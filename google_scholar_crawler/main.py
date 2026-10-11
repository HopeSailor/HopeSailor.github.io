"""Fetch public Google Scholar author statistics for the AcadHomepage badge.

Run via GitHub Actions. No Google Scholar API key is required, but Google
Scholar may block automated requests; in that case the workflow exits without
overwriting the last known good citation data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any


def normalize_author(author: dict[str, Any]) -> dict[str, Any]:
    """Validate the essential fields and keep AcadHomepage's data schema."""
    if not isinstance(author, dict):
        raise ValueError("Google Scholar returned an invalid author payload")
    name = author.get("name")
    citedby = author.get("citedby")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Missing author name (possibly blocked by Google Scholar)")
    if isinstance(citedby, bool) or citedby is None:
        raise ValueError("Missing total citation count")
    try:
        citation_total = int(citedby)
    except (TypeError, ValueError) as exc:
        raise ValueError("Citation count is not an integer") from exc
    if citation_total < 0:
        raise ValueError("Citation count cannot be negative")

    publications = author.get("publications")
    if not isinstance(publications, (list, dict)) or not publications:
        raise ValueError("Missing publications; refusing to publish partial data")
    if isinstance(publications, list):
        indexed = {}
        for item in publications:
            if not isinstance(item, dict) or not item.get("author_pub_id"):
                raise ValueError("Publication missing author_pub_id")
            indexed[item["author_pub_id"]] = item
    else:
        indexed = publications

    normalized = dict(author)
    normalized["citedby"] = citation_total
    normalized["publications"] = indexed
    normalized["updated"] = datetime.now(timezone.utc).isoformat()
    return normalized


def existing_count(directory: Path) -> int | None:
    previous = directory / "gs_data.json"
    if not previous.exists():
        return None
    data = json.loads(previous.read_text(encoding="utf-8"))
    return int(data["citedby"])


def write_stats(directory: Path, author: dict[str, Any]) -> None:
    """Write compatible payloads only after validating all safety conditions."""
    result = normalize_author(author)
    prior = existing_count(directory)
    if prior is not None and result["citedby"] < prior:
        raise ValueError(
            f"Google Scholar count {result['citedby']} is less than previously "
            f"published {prior}; keeping existing data. Verify before lowering it."
        )
    directory.mkdir(parents=True, exist_ok=True)
    badge = {"schemaVersion": 1, "label": "citations", "message": str(result["citedby"])}
    (directory / "gs_data.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (directory / "gs_data_shieldsio.json").write_text(
        json.dumps(badge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Validated Google Scholar citations: {prior} -> {result['citedby']}")


def fetch_author(author_id: str, scholar_client: Any) -> dict[str, Any]:
    author = scholar_client.search_author_id(author_id)
    if not author:
        raise ValueError("Google Scholar returned no author")
    scholar_client.fill(author, sections=["basics", "indices", "counts", "publications"])
    return author


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    author_id = os.environ.get("GOOGLE_SCHOLAR_ID", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", author_id):
        parser.error("GOOGLE_SCHOLAR_ID is missing or invalid")

    from scholarly import scholarly  # Imported at runtime to keep offline tests independent.

    author = fetch_author(author_id, scholarly)
    write_stats(args.output_dir, author)


if __name__ == "__main__":
    main()
