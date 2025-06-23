import os
import json
from ckan import get_latest_resource_url, stream_resource_data
from transform import transform_event, normalize_text
import hashlib

OUTPUT_DIR = "docs/daily_jsonl"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def hash_event_content(event):
    """Generate a hash of the event content for change detection."""
    normalized = json.dumps(event, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def generate_event_key(event):
    """Create a unique key using organizer, start date, and location."""
    organizer_name = normalize_text(event.get("organizer", {}).get("name"))
    start_date = event.get("startDate", "")
    location_name = normalize_text(event.get("location", {}).get("name"))
    primary_url = event.get("url", "")
    key_source = f"{organizer_name}|{start_date}|{location_name}|{primary_url}"
    return hashlib.sha1(key_source.encode("utf-8")).hexdigest()


def write_event_jsonl(event):
    date_str = event.get("startDate", "")[:10]
    if not date_str:
        return

    output_path = os.path.join(OUTPUT_DIR, f"{date_str}.jsonl")
    event_key = generate_event_key(event)
    event_hash = hash_event_content(event)

    existing_records = {}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    existing_event = json.loads(line)
                    key = generate_event_key(existing_event)
                    existing_records[key] = (
                        existing_event,
                        hash_event_content(existing_event),
                    )
                except json.JSONDecodeError:
                    continue

    # Check for insert or update
    if (event_key not in existing_records) or (
        existing_records[event_key][1] != event_hash
    ):
        existing_records[event_key] = (event, event_hash)

        # Overwrite the file with updated records
        with open(output_path, "w", encoding="utf-8") as f:
            for e, _ in existing_records.values():
                f.write(json.dumps(e, ensure_ascii=False) + "\n")


def main():
    print("🚀 Starting JSON-LD generation")
    resource_url = get_latest_resource_url()
    print(f"📡 Resource URL: {resource_url}")

    count = 0
    for item in stream_resource_data(resource_url):
        try:
            jsonld_event = transform_event(item)
            if jsonld_event:
                write_event_jsonl(jsonld_event)
                count += 1
                if count % 500 == 0:
                    print(f"✍️ Processed {count} events...")
        except Exception as e:
            print(f"⚠️ Failed to process event: {e}")

    print(f"✅ Finished. Wrote {count} events to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
