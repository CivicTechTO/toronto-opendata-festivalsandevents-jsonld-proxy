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
- Transform each event into schema.org/Event JSON-LD format.
- Write events to files in docs/daily_jsonl/YYYY-MM-DD.jsonl, one file per event day.

You can run this manually for initial population, or on a schedule for daily updates.

**Generate the JSON-LD**

To generate the full dataset of JSON-LD as indexes of all and upcoming:

```zsh
python build_indexes.py
```

### Usage


**Add**

Go to [https://www.toronto.ca/explore-enjoy/festivals-events/festivals-events-calendar/](https://www.toronto.ca/explore-enjoy/festivals-events/festivals-events-calendar/) to add events.

**Consume**

For each day:

- All output data is stored under [docs/daily_jsonl/](docs/daily_jsonl/), split by event date.
- Each .jsonl file contains one event per line in JSON-LD format.
- You can serve these files directly via GitHub Pages as a static API, or use them as a backend for a lightweight frontend or Flask app.

For upcoming:
see [docs/upcoming.jsonld](docs/upcoming.jsonld)

For all:
see [docs/all.jsonld](docs/all.jsonld)

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
