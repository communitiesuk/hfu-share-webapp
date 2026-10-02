import os
from urllib.parse import urlparse


def browser_test_url_is_local() -> bool:
    return urlparse(os.environ["BROWSER_TEST_URL"]).hostname in (
        "localhost",
        "127.0.0.1",
    )
