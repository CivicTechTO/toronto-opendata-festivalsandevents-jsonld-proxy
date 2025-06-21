from urllib.parse import urljoin
from html import unescape
from ftfy import fix_text
import re

# Used to prepend image URLs if they are relative
TORONTO_IMAGE_BASE = "https://secure.toronto.ca"
LOCALITIES = ["Toronto", "North York", "Scarborough", "Etobicoke", "East York", "York"]


def transform_event(cal_event):
    """
    Convert a single raw event record to schema.org/Event JSON-LD format.
    """
    evt = cal_event["calEvent"]
    location = evt.get("locations", [{}])[0]
    address = location.get("address", "")
    reservation = evt.get("reservation", {})

    # Get first datetime range for the event
    start_dt = evt.get("dates", [{}])[0].get("startDateTime")
    end_dt = evt.get("dates", [{}])[0].get("endDateTime")

    # Clean up relative image URLs
    image_url = evt.get("image", {}).get("url")
    if image_url and not image_url.startswith("http"):
        image_url = urljoin(TORONTO_IMAGE_BASE, image_url)

    # Choose the most relevant URL: reservation site preferred
    primary_url = reservation.get("website") or evt.get("eventWebsite")

    # Convert category string to a list of keywords
    raw_keywords = evt.get("categoryString", "")
    keywords = [unescape(k.strip()) for k in raw_keywords.split(",") if k.strip()]

    # Build core schema.org Event structure
    event = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": fix_text(unescape(evt.get("eventName", ""))),
        "startDate": start_dt,
        "endDate": end_dt,
        "location": {
            "@type": "Place",
            "name": fix_text(unescape(location.get("locationName", "Toronto"))),
            "address": parse_address(address),  # Use utility to parse addres
            "geo": extract_geo(location),  # Optional but added if available
        },
        "description": fix_text(unescape(evt.get("description", ""))),
        "url": primary_url,
        "image": image_url,
        "organizer": {
            "@type": "Organization",
            "name": fix_text(unescape(evt.get("orgName", ""))),
            "email": evt.get("orgEmail"),
            "telephone": evt.get("orgPhone"),
        },
        "isAccessibleForFree": evt.get("freeEvent", "").strip().lower() == "yes",
        "keywords": keywords,
    }

    # Optionally add offer block (e.g. cost + ticket URL)
    offer = build_offer(evt)
    if offer:
        event["offers"] = offer

    return event


def build_offer(evt):
    """
    Optionally build an Offer block for pricing and ticketing.
    """
    cost = evt.get("cost", {})
    reservation_url = evt.get("reservation", {}).get("website")
    offer = {}

    if isinstance(cost, dict):
        # Handle different cost formats
        if "from" in cost or "to" in cost:
            offer["price"] = cost.get("from") or cost.get("to")
        elif "ga" in cost:
            offer["price"] = cost["ga"]

        if "price" in offer:
            offer["priceCurrency"] = "CAD"

    if reservation_url:
        offer["url"] = reservation_url

    return {"@type": "Offer", **offer} if offer else None


def transform_all(raw_events):
    """
    Transform all raw records into JSON-LD Event objects.
    """
    return [transform_event(evt) for evt in raw_events]


def parse_address(full_address):
    """
    Parse a Toronto address into street, locality, region, and postal code.
    Uses known localities to split out address components.
    """
    if not full_address:
        return {}

    # Normalize whitespace
    full_address = full_address.strip()

    # Extract postal code
    postal_match = re.search(r"\b([A-Z]\d[A-Z])\s?(\d[A-Z]\d)\b", full_address)
    postal_code = (
        f"{postal_match.group(1)} {postal_match.group(2)}" if postal_match else None
    )

    # Try to identify the locality
    locality = "Toronto"
    for candidate in LOCALITIES:
        pattern = r",\s*(" + re.escape(candidate) + r")\b"
        match = re.search(pattern, full_address)
        if match:
            locality = match.group(1)
            break

    # Extract everything before the matched locality (if possible)
    if locality and locality in full_address:
        split_pattern = r"\s*,\s*" + re.escape(locality)
        parts = re.split(split_pattern, full_address, maxsplit=1)
        street_address = parts[0].strip() if parts else full_address
    else:
        street_address = full_address  # fallback

    return {
        "@type": "PostalAddress",
        "streetAddress": street_address,
        "addressLocality": locality,
        "addressRegion": "ON",
        "postalCode": postal_code,
        "addressCountry": "CA",
    }


def extract_geo(location):
    """
    Extract latitude and longitude as a schema.org GeoCoordinates object.

    Args:
        location (dict): A location object from the raw event data.

    Returns:
        dict or None: A schema.org-compatible GeoCoordinates block, or None if missing.
    """
    coords = location.get("coords")

    # Handle if coords is a list of dicts
    if isinstance(coords, list) and coords:
        coords = coords[0]

    # Handle if coords is a single dict
    if isinstance(coords, dict):
        return {
            "@type": "GeoCoordinates",
            "latitude": coords.get("lat"),
            "longitude": coords.get("lng"),
        }

    # Fallback if coords is missing or unrecognized format
    return None
