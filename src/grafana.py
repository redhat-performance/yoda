import os
import requests
import logging
import multiprocessing as mp
from urllib.parse import urlencode
from utils.utils import create_grafana_session

logger = logging.getLogger(__name__)

def recurse_panels(panels: dict, panel_id_to_names: dict, panel_name_to_ids: dict) -> None:
    """
    Recursively extracts panel IDs and names from nested panel data.

    Args:
        panels (dict): List of upper level panels from dashboard json
        panel_id_to_names (dict): A dictionary passed by reference to store all the panel id to names
        panel_name_to_ids (dict): A dictionary passed by reference to store all the panel name to ids

    Returns:
        None
    """
    for panel in panels:
        # Check if the panel is of type "row" and skip it
        if panel.get("type") == "row":
            # Recursively check nested panels within a row
            if "panels" in panel:
                recurse_panels(panel["panels"], panel_id_to_names, panel_name_to_ids)
        else:
            # Add the panel ID and name to the map
            panel_id = panel.get("id")
            panel_title = panel.get("title", "")
            if panel_id is not None:
                panel_id_to_names[panel_id] = panel_title
                panel_name_to_ids[panel_title] = panel_id
            # Recursively check nested panels
            if "panels" in panel:
                recurse_panels(panel["panels"], panel_id_to_names, panel_name_to_ids)

def extract_panels(panels: list, panel_id_to_names: dict, panel_name_to_ids: dict) -> list[dict]:
    """
    Extract only panels specified in the config.

    Args:
        panels (list): A list of panel information to extract for insights
        panel_id_to_names (dict): A dictionary that has all the panel id to names
        panel_name_to_ids (dict): A dictionary that has all the panel name to ids

    Returns:
        extracted_panels (dict): A dictionary to extract only required panels
    """
    extracted_panels = []
    for panel in panels:
        panel_alias = panel.get("alias", "")
        panel_id = panel.get("id", -1)
        panel_name = panel.get("name", "")
        panel_context = panel.get("context", "")

        if panel_id not in panel_id_to_names and panel_name not in panel_name_to_ids:
            logger.info(f"Panel with id:{panel_id} or name:{panel_name} not found. Hence skipping it")
            continue
        if panel_id not in panel_id_to_names and panel_name in panel_name_to_ids:
            panel_id = panel_name_to_ids[panel_name]
        if panel_alias == "":
            panel_alias = panel_name
        extracted_panels.append({
            "panel_id": panel_id,
            "panel_title": panel_alias,
            "panel_context": panel_context,
        })

    return extracted_panels

def parallel_process(each_panel: str, g_url: str, d_uid: str, g_username: str, g_password: str, d_output: str, d_query_params: dict, return_dict: dict) -> None:
    """
    Function to process each panel at the lowest atomic level.

    Args:
        each_panel (str): Each single panel
        g_url (str): Grafana url
        d_uid (str): dashboard uid
        g_username (str): grafana username
        g_password (str): grafana password
        d_output (str): dashboard output path
        d_query_params (dict): dashboard query parameters
        return_dict (dict): shared dictionary across the threads

    Returns:
        None
    """
    try:
        # Create new session for each thread.
        d_session = create_grafana_session(g_username, g_password)

        # Start with fixed parameters as a list of tuples
        render_query_params = [
            ("panelId", each_panel["panel_id"]),
            ("orgId", d_query_params.get("orgId", ["1"])[0]),
            ("width", "1280"),
            ("height", "720"),
            ("tz", "UTC")
        ]

        # Add additional parameters as tuples, allowing redundant keys
        additional_params = [(k, v) for k, vals in d_query_params.items() for v in vals]
        render_query_params.extend(additional_params)
        
        # render url of the panel
        render_url = f"{g_url}/render/d-solo/{d_uid}?{urlencode(render_query_params, doseq=True)}"

        # Download the image
        image_response = d_session.get(render_url, stream=True)
        image_response.raise_for_status()

        # Save the image
        panel_name = f"panel_{each_panel["panel_id"]}" if each_panel["panel_title"] == "" else f"panel_{each_panel["panel_id"]}_{each_panel["panel_title"]}"
        image_path = os.path.join(d_output, f"{panel_name}.jpeg")
        each_panel["image_path"] = image_path
        with open(image_path, "wb") as image_file:
            for chunk in image_response.iter_content(1024):
                image_file.write(chunk)

        logger.info(f"Exported {panel_name} to {image_path}")
        return_dict[each_panel['panel_id']] = each_panel
    except requests.RequestException as e:
        logger.error(f"Error exporting panel {each_panel['panel_id']}: {e}")


def multi_process(panels_chunk: list, g_url: str, d_uid: str, g_username: str, g_password: str, d_output: str, d_query_params: dict) -> None:
    """
    Function to process each chunk parallely.

    Args:
        panels_chunk (list): A chunk of extracted panels
        g_url (str): Grafana url
        d_uid (str): dashboard uid
        g_username (str): grafana username
        g_password (str): grafana password
        d_output (str): dashboard output path
        d_query_params (dict): dashboard query parameters

    Returns:
        None
    """
    manager = mp.Manager()
    return_dict = manager.dict()
    jobs = []
    for each_panel in panels_chunk:
        process = mp.Process(target=parallel_process, args=(each_panel, g_url, d_uid, g_username, g_password, d_output, d_query_params, return_dict))
        jobs.append(process)
        process.start()

    for proc in jobs:
        proc.join()
    return [return_dict[panel_id] for panel_id in return_dict]

def export_panels(extracted_panels: list, g_url: str, d_uid: str, g_username: str, g_password: str, d_output: str, d_query_params: dict) -> None:
    """
    Export all the extracted panels to the configured output directory.

    Args:
        extracted_panels (list): Full list of extracted panels
        g_url (str): Grafana url
        d_uid (str): dashboard uid
        g_username (str): grafana username
        g_password (str): grafana password
        d_output (str): dashboard output path
        d_query_params (dict): dashboard query parameters

    Returns:
        None
    """
    logger.debug(extracted_panels)
    os.makedirs(d_output, exist_ok=True)


    chunk_size = (75 * mp.cpu_count())//100
    updated_panels = []
    for i in range(0, len(extracted_panels), chunk_size):
        panels_chunk = extracted_panels[i:i + chunk_size]
        updated_panels.extend(multi_process(panels_chunk, g_url, d_uid, g_username, g_password, d_output, d_query_params))
    
    # At this point, `updated_panels` should contain all the panels with the 'image_path' key included
    logger.debug(updated_panels)
    return updated_panels
