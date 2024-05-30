import requests

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
