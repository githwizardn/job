"""საერთო HTTP session retry/backoff-ით."""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import USER_AGENT, HTTP_RETRIES, HTTP_BACKOFF


def build_session(user_agent: str = USER_AGENT) -> requests.Session:
    """აბრუნებს Session-ს ავტომატური retry-ით transient შეცდომებზე."""
    retry = Retry(
        total=HTTP_RETRIES,
        backoff_factor=HTTP_BACKOFF,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
