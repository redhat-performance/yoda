import requests
import multiprocessing as mp

def create_grafana_session(g_username: str, g_password: str) -> requests.Session:
    """
    Create a new session for connecting to Grafana with the specified credentials/
    This is required for creating multiple sessions as the session object is thread safe.

    Args:
        g_username (str): Grafana username
        g_password (str): Grafana password

    Returns:
        requests.Session: Configured session for Grafana
    """
    session = requests.Session()
    session.verify = False
    session.auth = (g_username, g_password)
    return session

def multi_process(chunk: list, job: callable, args: tuple) -> None:
    """
    Function to process each chunk parallely.

    Args:
        chunk (list): chunk of work to process
        job (function): job to execute
        args (tuple): list of arguments for the job

    Returns:
        None
    """
    manager = mp.Manager()
    return_dict = manager.dict()
    jobs = []
    extended_list = []

    for idx, each_item in enumerate(chunk):
        process = mp.Process(target=job, args=(each_item, args, return_dict, idx))
        jobs.append(process)
        process.start()

    for proc in jobs:
        proc.join()

    extended_list = []
    for each_value in return_dict.values():
        extended_list.extend([each_value])
    return extended_list

def flatten_list(nested_list):
    """
    Flattens a nested list.

    Args:
        nested_list (list): A list that may contain other lists.

    Returns:
        list: A single flattened list.
    """
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list
