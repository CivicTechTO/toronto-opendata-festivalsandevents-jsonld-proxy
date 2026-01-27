import requests
from urllib.parse import urljoin, urlencode, urlparse, urlunparse, parse_qs

# Base configuration for Toronto Open Data CKAN API
BASE_CKAN_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PACKAGE_NAME = "festivals-events"


def get_latest_resource_url():
    """
    Fetch the latest downloadable (non-datastore) resource URL from CKAN.

    Returns:
        str: URL to the dataset resource file.
    Raises:
        RuntimeError: If no valid non-datastore resource is found.
    """
    package_url = urljoin(BASE_CKAN_URL, "/api/3/action/package_show")
    params = {"id": PACKAGE_NAME}

    print("🔍 Fetching CKAN package metadata...")
    response = requests.get(package_url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    for resource in data["result"]["resources"]:
        if not resource.get("datastore_active"):
            print(f"🔗 Using resource URL: {resource['url']}")
            return resource["url"]

    raise RuntimeError("❌ No suitable non-datastore resource found in CKAN package.")


def append_query_params(base_url, new_params):
    """
    Append or update query parameters to a base URL safely.

    Args:
        base_url (str): The original URL.
        new_params (dict): Key-value query parameters to add or update.

    Returns:
        str: URL with appended query parameters.
    """
    parsed = urlparse(base_url)
    existing = parse_qs(parsed.query)
    existing.update({k: [str(v)] for k, v in new_params.items()})
    encoded = urlencode(existing, doseq=True)
    return urlunparse(parsed._replace(query=encoded))


def stream_resource_data(resource_url):
    """
    Generator to stream event data from the resource.

    Args:
        resource_url (str): CKAN resource URL to the JSON file.

    Yields:
        dict: Each event record.
    """
    print(f"⬇️ Fetching event data from: {resource_url}")

    response = requests.get(resource_url, timeout=60)
    response.raise_for_status()
    data = response.json()

    # Handle wrapped response {"value": [...]} or plain array [...]
    if isinstance(data, dict) and "value" in data:
        events = data["value"]
    elif isinstance(data, list):
        events = data
    else:
        raise RuntimeError(f"Unexpected response format: {type(data)}")

    print(f"📦 Received {len(events)} events")

    for item in events:
        yield item

    print(f"📊 Total events streamed: {len(events)}")
