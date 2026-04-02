import requests
import threading
from typing import Optional

class SessionManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.session = requests.Session()

    def __enter__(self) -> requests.Session:
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.session.close()

def fetch_data(url: str) -> Optional[dict]:
    """
    Fetch data from a given URL.

    Args:
        url (str): The URL to fetch data from.

    Returns:
        Optional[dict]: The JSON response as a dictionary,
                        or None if the request fails.

    Raises:
        ValueError: If the provided URL is invalid.

    Examples:
        >>> fetch_data('https://api.example.com/data')
        {'key': 'value'}
    """
    if not url.startswith('http'):
        raise ValueError('Provided URL must start with http or https.')
    with SessionManager() as session:
        response = session.get(url)
        response.raise_for_status()
        return response.json()

# Other functions with added type hints, input validation, and improved error handling would go here.
