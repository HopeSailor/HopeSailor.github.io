import json
import os
from datetime import datetime, timezone
from pathlib import Path

from scholarly import scholarly


RESULTS_DIR = Path(__file__).resolve().parent / "results"
SECTIONS = ["basics", "indices", "counts", "publications"]


def fetch_author(scholar_id: str) -> dict:
    """Fetch and validate one Google Scholar author profile."""
    author = scholarly.search_author_id(scholar_id)
    if not author:
        raise RuntimeError(f"No Google Scholar profile found for ID {scholar_id!r}.")

    author = scholarly.fill(author, sections=SECTIONS)
    if "citedby" not in author:
        raise RuntimeError("Google Scholar returned a profile without a citation count.")

    publications = author.get("publications", [])
    author["publications"] = {
        publication["author_pub_id"]: publication
        for publication in publications
        if publication.get("author_pub_id")
    }
    author["updated"] = datetime.now(timezone.utc).isoformat()
    return author


def write_json(path: Path, payload: dict) -> None:
    """Write UTF-8 JSON with stable, human-readable formatting."""
    with path.open("w", encoding="utf-8") as outfile:
        json.dump(payload, outfile, ensure_ascii=False, indent=2)
        outfile.write("\n")


def main() -> None:
    scholar_id = os.environ.get("GOOGLE_SCHOLAR_ID", "").strip()
    if not scholar_id:
        raise SystemExit(
            "GOOGLE_SCHOLAR_ID is empty. Add it as a GitHub Actions repository secret."
        )

    author = fetch_author(scholar_id)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    write_json(RESULTS_DIR / "gs_data.json", author)
    write_json(
        RESULTS_DIR / "gs_data_shieldsio.json",
        {
            "schemaVersion": 1,
            "label": "citations",
            "message": str(author["citedby"]),
        },
    )

    print(
        f"Fetched {author.get('name', scholar_id)}: "
        f"{author['citedby']} citations and {len(author['publications'])} publications."
    )


if __name__ == "__main__":
    main()
