import sys
import click
import csv
import logging
import warnings
import multiprocessing as mp
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from src.grafana import export_panels, extract_panels, preview_grafana_dashboard
from src.inference import image_inference
from src.slides import authenticate_google_slides, get_slide_info, replace_images_and_text
from utils.logging import configure_logging
from utils.yaml_parser import load_config
from utils.utils import multi_process, flatten_list

warnings.filterwarnings("ignore", message="Unverified HTTPS request.*")

logger = None
@click.group()
def cli(max_content_width=120):
    """
    yoda is the cli tool to auto generate readouts.
    """

@cli.command(name="generate")
@click.option("--config", default="config/grafana_config.yaml", help="Path to the configuration file")
@click.option("--debug", is_flag=True, help="log level")
@click.option("--concurrency", is_flag=True, help="To enable concurrent operations")
@click.option("--inference", is_flag=True, help="Flag for inference")
@click.option("--inference-endpoint", default="", help="Inference endpoint")
@click.option("--inference-api-key", default="", help="Api key to access inference endpoint")
@click.option("--inference-model", default="", help="Hosted model at the inference endpoint")
@click.option("--inference-model-type", default="", help="Hosted model type for inference. Valid options are [vllm, ollama, llama.cpp]")
@click.option("--csv", default="panel_inference.csv", help=".csv file path to output")
@click.option("--presentation", default="", help="Presentation id to parse")
@click.option("--credentials", default="credentials.json", help="Google oauth credentials path")
@click.option("--slidemapping", default="config/slide_content_mapping.yaml", help="Slide content mapping file")
def generate(**kwargs):
    """
    sub-command to generate a grafana panels and infer them. Optionally executes the default worklfow to publish those results to a presentation.
    """
    level = logging.DEBUG if kwargs["debug"] else logging.INFO
    need_inference = True if kwargs["inference"] else False
    concurrency = (75 * mp.cpu_count())//100 if kwargs["concurrency"] else 1
    configure_logging(level)
    global logger
    logger = logging.getLogger(__name__)
    config_data = load_config(kwargs["config"])
    logger.debug(config_data)

    # TODO: Add support for other data sources as well
    process_grafana_config(config_data['grafana'], concurrency, need_inference, kwargs)

@cli.command(name="preview-dashboard")
@click.option("--url", default="", help="Grafana dashboard url to preview")
@click.option("--username", default="", help="username of the dashboard")
@click.option("--password", default="", help="password of the dashboard")
@click.option("--csv", default="", help=".csv file path to output")
def preview_dashboard(**kwargs):
    """
    sub-command to preview a grafana dashboard.
    """
    configure_logging(logging.INFO)
    global logger
    logger = logging.getLogger(__name__)
    try:
        parsed_d_raw_url = urlparse(kwargs["url"])
        g_url = parsed_d_raw_url.scheme + "://" + parsed_d_raw_url.netloc
        d_uid = parsed_d_raw_url.path.split('/')[2]
        d_url = f"{g_url}/api/dashboards/uid/{d_uid}"
        preview_grafana_dashboard(d_url, kwargs["username"], kwargs["password"], True, kwargs["csv"])
    except Exception as e:
        logger.error(f"Please make sure the provided credentials are correct. Error: {e}")

@cli.command(name="preview-presentation")
@click.option("--id", default="", help="Presentation id to preview")
@click.option("--credentials", default="credentials.json", help="Google oauth credentials path")
@click.option("--csv", default="", help=".csv file path to output")
def preview_presentation(**kwargs):
    """
    sub-command to preview a presentation. More details here: https://developers.google.com/slides/api/quickstart/python
    """
    configure_logging(logging.INFO)
    global logger
    logger = logging.getLogger(__name__)
    try:
        creds = authenticate_google_slides(kwargs["credentials"])
        service = build('slides', 'v1', credentials=creds)
        get_slide_info(service, kwargs["id"], True, kwargs["csv"])
    except Exception as e:
        logger.error(f"Please make sure the provided credentials are correct. Error: {e}")

@cli.command(name="update-presentation")
@click.option("--id", default="", help="Presentation id to preview")
@click.option("--credentials", default="credentials.json", help="Google oauth credentials path")
@click.option("--slidemapping", default="config/slide_content_mapping.yaml", help="Slide content mapping file")
def update_presentation(**kwargs):
    """
    sub-command to update a presentation. More details here: https://developers.google.com/slides/api/quickstart/python
    """
    configure_logging(logging.INFO)
    global logger
    logger = logging.getLogger(__name__)
    try:
        creds = authenticate_google_slides(kwargs["credentials"])
        service = build('slides', 'v1', credentials=creds)
        slide_info = get_slide_info(service, kwargs["id"], False)
        logger.info(f"Applying slide mapping: {kwargs["slidemapping"]}")
        slide_content_mapping = load_config(kwargs["slidemapping"])
        response = replace_images_and_text(service, kwargs["id"], slide_info, slide_content_mapping)
        logger.debug(response)
        logger.info(f"Presentation: {kwargs["id"]} has been updated successfully")
    except Exception as e:
        logger.error(f"Please make sure the provided credentials are correct. Error: {e}")

def process_grafana_config(grafana_data: list, concurrency: int, need_inference: bool, kwargs: dict[str, any]) -> None:
    """
    Function to process the grafana config.

    Args:
        grafana_data (list): grafana configuration list
        concurrency (int): concurrency to implement parallelism
        need_inference (bool): flag to regulate inference
        kwargs (dict[str, any]): Additional application arguments

    Returns:
        None
    """
    for each_grafana in grafana_data:
        g_alias = each_grafana['alias']
        g_url = each_grafana['url']
        g_username = each_grafana['username']
        g_password = each_grafana['password']

        logger.info(f"Scraping grafana: {g_alias}")
        if 'dashboards' not in each_grafana or not each_grafana['dashboards']:
            logger.info("No dashboards specified in configuration for extraction. Hence skipping this grafana")
            continue
        all_dashboards = each_grafana['dashboards']

        all_panels = []
        for i in range(0, len(all_dashboards), concurrency):
            dashboard_chunk = all_dashboards[i:i + concurrency]
            all_panels.extend(multi_process(dashboard_chunk, process_dashboard, (g_url, g_username, g_password, concurrency)))
        updated_panels = flatten_list(all_panels)

        if need_inference:
            processed_panels = []
            for i in range(0, len(updated_panels), concurrency):
                panel_chunk = updated_panels[i: i + concurrency]
                processed_panels.extend(multi_process(panel_chunk, 
                                                      image_inference, 
                                                      ("Can you summarize this image?", 
                                                       kwargs["inference_endpoint"], 
                                                       kwargs["inference_api_key"], 
                                                       kwargs["inference_model"],
                                                       kwargs["inference_model_type"])
                                                    )
                                                )
            processed_panels = flatten_list(processed_panels)
            updated_panels = processed_panels
        
        logger.debug("Full list of exported panels")
        logger.debug(updated_panels)

        data = [["Panel Image", "Panel Text"]]
        for panel in updated_panels:
            panel_text = panel["panel_text"] if "panel_text" in panel else ""
            data.append([panel["panel_image"], panel_text])
        with open(kwargs["csv"], mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        logger.info(f"Panels summary exported to file: {kwargs["csv"]}")

        if kwargs["presentation"] != "" and kwargs["slidemapping"] != "":
            logger.info(f"Presentation ID specified. Trying to apply default slide mapping at {kwargs["slidemapping"]}")
            creds = authenticate_google_slides(kwargs["credentials"])
            service = build('slides', 'v1', credentials=creds)
            slide_info = get_slide_info(service, kwargs["presentation"], False)
            slide_content_mapping = load_config(kwargs["slidemapping"])
            response = replace_images_and_text(service, kwargs["presentation"], slide_info, slide_content_mapping)
            logger.debug(response)
            logger.info(f"Presentation: {kwargs["presentation"]} has been updated successfully")

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
    d_url = f"{g_url}/api/dashboards/uid/{d_uid}"
    panel_id_to_names, panel_name_to_ids = preview_grafana_dashboard(d_url, g_username, g_password, False, "", d_alias)

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
        cli.add_command(preview_dashboard)
        cli.add_command(preview_presentation)
        cli.add_command(update_presentation)
        cli()
