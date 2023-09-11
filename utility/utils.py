import sys
import time
from urllib.parse import urlparse


def fancy_out(message):
    output = ("\r....." + message).ljust(80, ".")
    sys.stdout.write(output)
    sys.stdout.flush()
    time.sleep(0.5)


def get_path_from_url(url_string):
    if not url_string:
        return ""
    parsed = urlparse(url_string)
    return parsed.path.strip("/")
