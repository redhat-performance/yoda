import requests
import sys
import click
import logging
import warnings
import multiprocessing as mp
from urllib.parse import urlparse, parse_qs
from src.grafana import recurse_panels, export_panels, extract_panels
from src.deplot import google_deplot
from tabulate import tabulate
from utils.logging import configure_logging
from utils.yaml_parser import load_config
from utils.utils import create_grafana_session, multi_process, flatten_list


warnings.filterwarnings("ignore", message="Unverified HTTPS request.*")

logger = None
@click.group()
def cli(max_content_width=120):
    """
    cli function to group commands
    """

@click.command()
@click.option("--config", default="config.yaml", help="Path to the configuration file")
@click.option("--debug", is_flag=True, help="log level ")
@click.option("--concurrency", default=75, type=int, help="Number of concurrent processes")
def generate(**kwargs):
    """insight generator is the cli tool to auto generate readouts.

    Args:
        config (str): path to the config file
        debug (bool): lets you log debug mode
        concurrency (int): concurrency to implement parallelism
    """
    level = logging.DEBUG if kwargs["debug"] else logging.INFO
    configure_logging(level)
    global logger
    logger = logging.getLogger(__name__)
    config_data = load_config(kwargs["config"])
    logger.debug(config_data)

    # TODO: Add support for other data sources as well
    process_grafana_config(config_data['grafana'], kwargs["concurrency"])

def process_grafana_config(grafana_data: list, concurrency: int) -> None:
    """
    Function to process the grafana config.

    Args:
        grafana_data (list): grafana configuration list
        concurrency (int): concurrency to implement parallelism

    Returns:
        None
    """
    for each_grafana in grafana_data:
        g_alias = each_grafana['alias']
        g_url = each_grafana['url']
        g_username = each_grafana['username']
        g_password = each_grafana['password']

        logger.info(f"Scraping grafana: {g_alias}")
        parallelism = (concurrency * mp.cpu_count())//100
        if 'dashboards' not in each_grafana or not each_grafana['dashboards']:
            logger.info("No dashboards specified in configuration for extraction. Hence skipping this grafana")
            continue
        all_dashboards = each_grafana['dashboards']

        all_panels = []
        for i in range(0, len(all_dashboards), parallelism):
            dashboard_chunk = all_dashboards[i:i + parallelism]
            all_panels.extend(multi_process(dashboard_chunk, process_dashboard, (g_url, g_username, g_password, concurrency)))
        updated_panels = flatten_list(all_panels)
        logger.debug("Full list of exported panels")
        logger.debug(updated_panels)

        for each_panel in updated_panels:
            google_deplot([each_panel['image_path']], "Generate underlying data table of the figure below:")

def process_dashboard(each_dashboard: dict, args: tuple, return_dict: dict, idx: int) -> None:
    """
    Process grafana dashboard.

    Args:
        each_dashboard (dict): each dashboard to process
        args (tuple): full list of arguments to process
        return_dict (dict): shared dictionary across the threads
        idx (int): unique index to store thread data

    Returns:
        None
    """
    g_url, g_username, g_password, concurrency = args
    d_alias = each_dashboard['alias']
    d_raw_url = each_dashboard['raw_url']
    d_output = each_dashboard['output']

    parsed_d_raw_url = urlparse(d_raw_url)
    d_uid = parsed_d_raw_url.path.split('/')[2]
    d_query_params = parse_qs(parsed_d_raw_url.query)

    d_session = create_grafana_session(g_username, g_password)
    d_url = f"{g_url}/api/dashboards/uid/{d_uid}"
    response = d_session.get(d_url)
    response.raise_for_status()

    dashboard_data = response.json()
    dashboard_title = dashboard_data["dashboard"]["title"]
    d_title = d_alias if d_alias else dashboard_title

    logger.info(f"Scanning dashboard: {d_title}")
    panels = dashboard_data["dashboard"]["panels"]
    panel_id_to_names, panel_name_to_ids = dict(), dict()
    recurse_panels(panels, panel_id_to_names, panel_name_to_ids)

    logger.info("Full list of dashboard panels")
    data = [["Panel ID", "Panel Name"]]
    for panel_id, panel_name in panel_id_to_names.items():
        data.append([panel_id, panel_name])
    table = tabulate(data, headers="firstrow", tablefmt="grid")
    logger.info("\n" + table)

    if 'panels' not in each_dashboard or not each_dashboard['panels']:
        logger.info("No panels specified in configuration for extraction. Hence skipping this dashboard")
        return []

    extracted_panels = extract_panels(each_dashboard['panels'], panel_id_to_names, panel_name_to_ids)
    return_dict[idx] = export_panels(extracted_panels, g_url, d_uid, g_username, g_password, d_output, d_query_params, concurrency)

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        cli.main(['--help'])
    else:
        print(len(sys.argv))
        cli.add_command(generate)
        cli()
