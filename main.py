import requests
import sys
import click
import logging
import warnings
from urllib.parse import urlparse, parse_qs
from src.grafana import recurse_panels, export_panels, extract_panels
from src.deplot import google_deplot
from tabulate import tabulate
from utils.logging import configure_logging
from utils.yaml_parser import load_config


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
def generate(**kwargs):
    """insight generator is the cli tool to auto generate readouts.

    Args:
        config (str): path to the config file
        debug (bool): lets you log debug mode
    """

    level = logging.DEBUG if kwargs["debug"] else logging.INFO
    configure_logging(level)
    global logger
    logger = logging.getLogger(__name__)
    config_data = load_config(kwargs["config"])
    logger.debug(config_data)

    # TODO: Add support for other data sources as well
    process_grafana_config(config_data['grafana'])

def process_grafana_config(grafana_data: list):
    for each_grafana in grafana_data:
        g_alias = each_grafana['alias']
        g_url = each_grafana['url']
        g_username = each_grafana['username']
        g_password = each_grafana['password']

        for each_dashboard in each_grafana['dashboards']:
            d_alias = each_dashboard['alias']
            d_raw_url = each_dashboard['raw_url']
            d_output = each_dashboard['output']

            parsed_d_raw_url = urlparse(d_raw_url)
            d_uid = parsed_d_raw_url.path.split('/')[2]
            d_query_params = parse_qs(parsed_d_raw_url.query)

            d_session = requests.Session()
            d_session.verify = False
            d_session.auth = (g_username, g_password)

            d_url = f"{g_url}/api/dashboards/uid/{d_uid}"
            response = d_session.get(d_url)
            response.raise_for_status()

            dashboard_data = response.json()
            dashboard_title = dashboard_data["dashboard"]["title"]
            logger.info(f"Scanning dashboard: {dashboard_title}")
            
            
            panels = dashboard_data["dashboard"]["panels"]
            panel_id_to_names, panel_name_to_ids = dict(), dict()
            recurse_panels(panels, panel_id_to_names, panel_name_to_ids)

            data = [["Panel ID", "Panel Name"]]
            for panel_id, panel_name in panel_id_to_names.items():
                data.append([panel_id, panel_name])
            table = tabulate(data, headers="firstrow", tablefmt="grid")
            for line in table.split('\n'):
                logger.info(line)

            extracted_panels = extract_panels(each_dashboard['panels'], panel_id_to_names, panel_name_to_ids)
            export_panels(extracted_panels, g_url, d_uid, d_session, d_output, d_query_params)
            logger.debug(extracted_panels)
            for each_panel in extracted_panels:
                google_deplot([each_panel['image_path']], "Generate underlying data table of the figure below. Also make sure you capture the headings and relevant values accurately")

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        cli.main(['--help'])
    else:
        print(len(sys.argv))
        cli.add_command(generate)
        cli()
