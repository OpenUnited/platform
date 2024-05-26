import sys
import time
from urllib.parse import urlparse

text_field_class_names = (
    "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
    " placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
)


def placeholder(name):
    return f"Enter {name.capitalize()}..."


def fancy_out(message):
    output = ("\r....." + message).ljust(80, ".")
    sys.stdout.write(output)
    sys.stdout.flush()
    time.sleep(0.5)


def get_path_from_url(url_string, strip=False):
    if not url_string:
        return ""
    parsed = urlparse(url_string)
    if strip:
        return parsed.path.strip("/")

    return parsed.path


def serialize_other_type_tree(node):
    """Serializer for the tree."""
    return {
        "id": node.pk,
        "name": node.name,
        "children": [serialize_other_type_tree(child) for child in node.get_children],
    }
