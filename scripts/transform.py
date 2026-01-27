from html import unescape
from ftfy import fix_text
import re
import json


def normalize_text(s):
    """Fix text encoding and clean up spacing/HTML entities."""
    return fix_text(unescape(s or "")).strip()


# Used to prepend image URLs if they are relative
TORONTO_IMAGE_BASE = "https://secure.toronto.ca"
IMAGE_CDN_BASE = "https://s3.ca-central-1.amazonaws.com/c3api-penguin-prod-toronto-storagestack-oc9o88-uploads/"
LOCALITIES = ["Toronto", "North York", "Scarborough", "Etobicoke", "East York", "York"]


def transform_event(evt):
    """
    Convert a single raw event record to schema.org/Event JSON-LD format.
    Updated for the new Toronto Open Data API schema (2025).
    """
    # Get first location if available
    locations = evt.get("event_locations", [])
    location = locations[0] if locations else {}

    # Get address
    address = location.get("location_address", "")

    # Get dates
    start_dt = evt.get("event_startdate")
    end_dt = evt.get("event_enddate")

    # Build image URL from new schema
    image_url = None
    images = evt.get("event_image", [])
    if images and isinstance(images, list) and len(images) > 0:
        img = images[0]
        if isinstance(img, dict) and img.get("bin_id"):
            image_url = f"{IMAGE_CDN_BASE}{img['bin_id']}"

    # Choose the most relevant URL
    primary_url = evt.get("ticket_website") or evt.get("event_website")

    # Convert category array to keywords
    categories = evt.get("event_category", [])
    if isinstance(categories, list):
        keywords = [normalize_text(k) for k in categories if k]
    else:
        keywords = []

    # Get organizer from partnerships or fallback
    organizer_name = ""
    partnerships = evt.get("partnerships", [])
    if partnerships and isinstance(partnerships, list):
        for p in partnerships:
            if isinstance(p, dict) and p.get("text"):
                organizer_name = p.get("text")
                break

    # Build core schema.org Event structure
    event = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": normalize_text(evt.get("event_name", "")),
        "startDate": start_dt,
        "endDate": end_dt,
        "location": {
            "@type": "Place",
            "name": normalize_text(location.get("location_name", "Toronto")),
            "address": parse_address(address),
            "geo": extract_geo(location),
        },
        "description": normalize_text(evt.get("event_description", "")),
        "url": primary_url,
        "image": image_url,
        "organizer": {
            "@type": "Organization",
            "name": normalize_text(organizer_name),
            "email": evt.get("event_email"),
            "telephone": evt.get("event_telephone"),
        },
        "isAccessibleForFree": str(evt.get("free_event", "")).strip().lower() == "yes",
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
    offer = {}

    # Check various price fields
    price = (
        evt.get("event_price") or
        evt.get("event_price_adult") or
        evt.get("event_price_low")
    )

    if price:
        offer["price"] = price
        offer["priceCurrency"] = "CAD"

    reservation_url = evt.get("ticket_website")
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
    The new schema stores GPS as a JSON string in location_gps field.
    """
    gps_str = location.get("location_gps")

    if gps_str and isinstance(gps_str, str):
        try:
            gps_data = json.loads(gps_str)
            if isinstance(gps_data, list) and gps_data:
                coords = gps_data[0]
                lat = coords.get("gps_lat")
                lng = coords.get("gps_lng")
                if lat and lng:
                    return {
                        "@type": "GeoCoordinates",
                        "latitude": lat,
                        "longitude": lng,
                    }
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

    # Fallback to direct fields if available
    lat = location.get("geo_lat")
    lng = location.get("geo_long")
    if lat and lng:
        return {
            "@type": "GeoCoordinates",
            "latitude": lat,
            "longitude": lng,
        }

    return None
