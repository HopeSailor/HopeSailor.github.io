"""SerpApi-powered Google Scholar citation updater for AcadHomepage."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

AUTHOR_ID = "wtcf_r4AAAAJ"


def read_existing(directory: Path) -> dict:
    path = directory / "gs_data.json"
    if not path.is_file():
        raise ValueError("Missing existing gs_data.json in the statistics branch")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("scholar_id") != AUTHOR_ID:
        raise ValueError("Existing statistics belong to a different Scholar profile")
    return data


def fetch_serpapi(author_id: str, key: str) -> dict:
    url = "https://serpapi.com/search.json?" + urlencode({
        "engine": "google_scholar_author",
        "author_id": author_id,
        "hl": "en",
        "num": 100,
        "api_key": key,
    })
    # Do not print exception URLs, which contain the API key.
    try:
        with urlopen(url, timeout=70) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"SerpApi request failed (HTTP {exc.code})") from None
    except URLError:
        raise RuntimeError("SerpApi connection failed") from None
    if not isinstance(payload, dict) or payload.get("error"):
        raise ValueError("SerpApi returned an error")
    if payload.get("search_metadata", {}).get("status") != "Success":
        raise ValueError("SerpApi did not report a successful search")
    return payload


def transform(payload: dict, previous: dict, author_id: str) -> dict:
    params = payload.get("search_parameters") or {}
    if params.get("author_id") != author_id:
        raise ValueError("Unexpected Scholar author ID")
    author = payload.get("author") or {}
    if not isinstance(author.get("name"), str) or not author["name"].strip():
        raise ValueError("Missing Scholar author name")
    rows = (payload.get("cited_by") or {}).get("table") or []
    if not isinstance(rows, list):
        raise ValueError("Invalid citation metrics")
    cited_row = next((r["citations"] for r in rows
                      if isinstance(r, dict) and "citations" in r), None)
    if not isinstance(cited_row, dict) or cited_row.get("all") is None:
        raise ValueError("Missing total citations")
    total = int(cited_row["all"])
    if total < 0 or total < int(previous["citedby"]):
        raise ValueError("Invalid/decreasing citation total; preserving old data")
    if not previous.get("publications"):
        raise ValueError("No existing publications to preserve")

    result = dict(previous)
    result.update({
        "citedby": total,
        "name": author["name"],
        "source": "SERPAPI_GOOGLE_SCHOLAR_AUTHOR",
        "updated": datetime.now(timezone.utc).isoformat(),
    })
    pub = dict(previous["publications"])
    for article in payload.get("articles") or []:
        if not isinstance(article, dict):
            continue
        pid = article.get("citation_id")
        if pid in pub:
            n = (article.get("cited_by") or {}).get("value")
            if n is not None:
                row = dict(pub[pid])
                row["num_citations"] = int(n)
                pub[pid] = row
    result["publications"] = pub

    for source, target, recent in (
        ("citations", "citedby", "citedby5y"),
        ("h_index", "hindex", "hindex5y"),
        ("i10_index", "i10index", "i10index5y"),
    ):
        row = next((r[source] for r in rows
                    if isinstance(r, dict) and source in r), None)
        if isinstance(row, dict):
            if row.get("all") is not None:
                result[target] = int(row["all"])
            recent_values = [v for k, v in row.items() if k.startswith("since_")]
            if recent_values:
                result[recent] = int(recent_values[0])
    graph = (payload.get("cited_by") or {}).get("graph")
    if isinstance(graph, list) and graph:
        result["cites_per_year"] = {
            str(row["year"]): int(row["citations"])
            for row in graph if "year" in row and "citations" in row
        }
    return result


def write_files(directory: Path, result: dict) -> None:
    previous = read_existing(directory)
    total = result.get("citedby")
    if type(total) is not int or total < int(previous["citedby"]):
        raise ValueError("Invalid or decreasing total: files not changed")
    if not result.get("publications"):
        raise ValueError("Missing publications: files not changed")
    badge = {"schemaVersion": 1, "label": "citations", "message": str(total)}
    (directory / "gs_data.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (directory / "gs_data_shieldsio.json").write_text(
        json.dumps(badge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Google Scholar citations verified: {previous['citedby']} -> {total}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    author_id = os.environ.get("GOOGLE_SCHOLAR_ID", AUTHOR_ID).strip()
    if not key:
        parser.error("Configure SERPAPI_API_KEY in GitHub Actions Secrets")
    if author_id != AUTHOR_ID:
        parser.error("Unexpected Google Scholar author ID")
    old = read_existing(args.output_dir)
    updated = transform(fetch_serpapi(author_id, key), old, author_id)
    write_files(args.output_dir, updated)


if __name__ == "__main__":
    main()
