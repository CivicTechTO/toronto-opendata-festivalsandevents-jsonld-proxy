# Festival & Events JSON-LD Proxy

**A daily-refreshed JSON-LD proxy for Toronto’s Festivals & Events open data feed.**  
Built to help make Toronto the most programmable city in the world.

## Function

This project transforms the [City of Toronto’s Festivals and Events dataset](https://open.toronto.ca/dataset/festivals-events/) into structured, linked data using the [schema.org/Event](https://schema.org/Event) vocabulary.

The result is a free, publicly hosted JSON-LD feed that enables developers, search engines, and civic tools to discover and reuse Toronto's official event listings in a standardized, machine-readable format.

## Purpose

- Demonstrates how open data can power real-world tools with **minimal cost and friction**.
- Enables **events aggregators, civic apps, and open data projects** to work with a common standard and data ontology.
- Bridges the gap between _open datasets_ and _programmable cities_.

## Orientation

### Build

**Install dependencies**

```zsh
pip install -r requirements.txt
```

**Generate the JSON Lines**

To generate the full dataset of event records and write them to date-specific .jsonl files:

```zsh
python scripts/generate_jsonld.py
```

This will:

- Fetch the latest events feed from the City of Toronto’s CKAN resource.
- Transform each event into [schema.org/Event](https://schema.org/Event) JSON-LD format.
- Write events to files in `docs/daily_jsonl/YYYY-MM-DD.jsonl`, one file per event day.
- Use a content-based deduplication and update strategy to maintain and avoid duplicating events that have already been stored.

**Generate the JSON-LD**

To build JSON-LD aggregate indexes:

```zsh
python build_indexes.py
```

This produces:

- [`docs/all.jsonld`](docs/all.jsonld): a complete flat list of all event entries across all dates.
- [`docs/upcoming.jsonld`](docs/upcoming.jsonld): a list of only future events relative to the current date.

**Deduplication Strategy**

Each event is hashed using a combination of minimally mutable attributes. A stable identity key is created using:

- `startDate`: the event’s scheduled date
- `organizer.name`: who is running the event
- `location.name`: where the event is held
- `url`: the reservation URL for the event

If an event is new or has changed since the last run, it is written or updated accordingly.
The `.jsonl` file for the relevant date is rewritten to reflect the latest version of all known events on that date.

You can run this manually for initial population, or allow the system to maintain itself automatically via a scheduled GitHub Actions workflow.

### Automated Updates

This project includes a GitHub Actions workflow at [`.github/workflows/update.yml`](.github/workflows/update.yml) that:

- Runs daily on a schedule (via cron).
- Executes `generate_jsonld.py` and `build_indexes.py` to fetch and append new or changed events.
- Commits changes back to the repository if new data is found.
- This keeps the data in sync with the latest available event information.

### Usage

**Add**

To list your event in this feed, submit it through the official City of Toronto portal:

[https://www.toronto.ca/explore-enjoy/festivals-events/festivals-events-calendar/](https://www.toronto.ca/explore-enjoy/festivals-events/festivals-events-calendar/)

**Consume**

- All event data is stored under [`docs/daily_jsonl/`](docs/daily_jsonl), grouped by event date.
- Each `.jsonl` file contains one event per line in JSON-LD format.
- You can serve these files as a static API via GitHub Pages or query them from a custom frontend or backend service.

Convenient indexes:

- All events: [`docs/all.jsonld`](docs/all.jsonld)
- Upcoming events: [`docs/upcoming.jsonld`](docs/upcoming.jsonld)

## About

### Origin

This project was built as part of **PROGRAM: Toronto** — a hackathon to make Toronto the world’s most programmable city — in collaboration with the City of Toronto Open Data team.

### Acknowledgments

Built by [@jordyarms](https://github.com/jordyarms)  
Maintained by _(you?)_

Special thanks to:

- [City of Toronto Open Data](https://open.toronto.ca/)
- PROGRAM: Toronto

## License

- **Code** is licensed under the [MIT License](LICENSE).
- **Source event data** is licensed under the [Open Government Licence – Toronto](https://open.toronto.ca/open-data-licence/).  
  Please attribute as:
  > Contains information licensed under the Open Government Licence – Toronto.
