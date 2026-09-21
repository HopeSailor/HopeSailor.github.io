import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from scholarly import scholarly


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

RESULTS_DIR = Path(__file__).resolve().parent / "results"

# Only fetch the sections actually used by the website.
SECTIONS = [
    "basics",
    "indices",
    "counts",
    "publications",
]

# Keep individual HTTP requests reasonably short.
SCHOLAR_TIMEOUT_SECONDS = 10

# Reduce normal retries inside scholarly.
# The GitHub Actions workflow provides the final hard timeout.
SCHOLAR_RETRIES = 2


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

def configure_logging() -> None:
    """Configure console logging for GitHub Actions."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    # Enable scholarly's own logging.
    scholarly.set_logger(True)

    # Limit individual network request duration.
    scholarly.set_timeout(SCHOLAR_TIMEOUT_SECONDS)

    # Limit ordinary retry attempts.
    scholarly.set_retries(SCHOLAR_RETRIES)


# ---------------------------------------------------------------------
# Google Scholar
# ---------------------------------------------------------------------

def fetch_author(scholar_id: str) -> dict:
    """Fetch and validate one Google Scholar author profile."""

    print("=" * 70, flush=True)
    print("[Scholar] Starting Google Scholar request", flush=True)
    print(f"[Scholar] Scholar ID: {scholar_id}", flush=True)
    print("=" * 70, flush=True)

    # -----------------------------------------------------------------
    # Step 1: Find author
    # -----------------------------------------------------------------

    print(
        "[1/2] Requesting basic Google Scholar author profile...",
        flush=True,
    )

    author = scholarly.search_author_id(scholar_id)

    if not author:
        raise RuntimeError(
            f"No Google Scholar profile found for ID {scholar_id!r}."
        )

    author_name = author.get("name", scholar_id)

    print(
        f"[1/2] Profile found: {author_name}",
        flush=True,
    )

    # -----------------------------------------------------------------
    # Step 2: Fill citation data and publications
    # -----------------------------------------------------------------

    print(
        "[2/2] Fetching citation indices, yearly counts, "
        "and publications...",
        flush=True,
    )

    author = scholarly.fill(
        author,
        sections=SECTIONS,
    )

    print(
        "[2/2] Google Scholar data received.",
        flush=True,
    )

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    if "citedby" not in author:
        raise RuntimeError(
            "Google Scholar returned a profile without a citation count."
        )

    publications = author.get("publications", [])

    # Convert publication list into a dictionary indexed by author_pub_id.
    # This preserves the structure expected by the existing website.
    author["publications"] = {
        publication["author_pub_id"]: publication
        for publication in publications
        if publication.get("author_pub_id")
    }

    author["updated"] = datetime.now(timezone.utc).isoformat()

    print(
        f"[Scholar] Successfully fetched {author_name}: "
        f"{author['citedby']} citations, "
        f"{len(author['publications'])} publications.",
        flush=True,
    )

    return author


# ---------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------

def write_json(path: Path, payload: dict) -> None:
    """Write UTF-8 JSON with stable, human-readable formatting."""

    print(
        f"[Output] Writing {path.name}...",
        flush=True,
    )

    with path.open("w", encoding="utf-8") as outfile:
        json.dump(
            payload,
            outfile,
            ensure_ascii=False,
            indent=2,
        )
        outfile.write("\n")

    print(
        f"[Output] Written successfully: {path}",
        flush=True,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    configure_logging()

    print(
        "[Crawler] Google Scholar crawler started.",
        flush=True,
    )

    scholar_id = os.environ.get(
        "GOOGLE_SCHOLAR_ID",
        "",
    ).strip()

    if not scholar_id:
        raise RuntimeError(
            "GOOGLE_SCHOLAR_ID is empty. "
            "Add it as a GitHub Actions repository secret."
        )

    # Fetch Scholar data.
    author = fetch_author(scholar_id)

    # Ensure output directory exists.
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "[Output] Preparing citation JSON files...",
        flush=True,
    )

    # Complete Google Scholar data.
    write_json(
        RESULTS_DIR / "gs_data.json",
        author,
    )

    # Shields.io citation badge data.
    write_json(
        RESULTS_DIR / "gs_data_shieldsio.json",
        {
            "schemaVersion": 1,
            "label": "citations",
            "message": str(author["citedby"]),
        },
    )

    print("=" * 70, flush=True)
    print(
        f"[Crawler] Finished successfully.",
        flush=True,
    )
    print(
        f"[Crawler] Author: "
        f"{author.get('name', scholar_id)}",
        flush=True,
    )
    print(
        f"[Crawler] Citations: {author['citedby']}",
        flush=True,
    )
    print(
        f"[Crawler] Publications: "
        f"{len(author['publications'])}",
        flush=True,
    )
    print("=" * 70, flush=True)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print(
            "[ERROR] Crawler was interrupted.",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(130)

    except Exception:
        logging.exception(
            "[ERROR] Google Scholar crawler failed."
        )
        sys.exit(1)
