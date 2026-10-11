"""Offline tests for the Google Scholar data normalization and safety checks."""
import json
from pathlib import Path
import tempfile
import unittest

from main import fetch_author, normalize_author, write_stats


def mock_author(count=129):
    return {
        "name": "Xiaochen Wang",
        "citedby": count,
        "publications": [
            {
                "author_pub_id": "wtcf_r4AAAAJ:sample",
                "bib": {"title": "Example publication"},
                "num_citations": 5,
            }
        ],
    }


class DummyScholarly:
    def search_author_id(self, author_id):
        assert author_id == "wtcf_r4AAAAJ"
        return mock_author()

    def fill(self, author, sections):
        assert "publications" in sections
        return author


class ScholarDataTest(unittest.TestCase):
    def test_fetch_and_transform(self):
        data = fetch_author("wtcf_r4AAAAJ", DummyScholarly())
        normalized = normalize_author(data)
        self.assertEqual(normalized["citedby"], 129)
        self.assertIn("wtcf_r4AAAAJ:sample", normalized["publications"])

    def test_writes_site_compatible_json(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_stats(root, mock_author())
            badge = json.loads((root / "gs_data_shieldsio.json").read_text())
            source = json.loads((root / "gs_data.json").read_text())
            self.assertEqual(badge["message"], "129")
            self.assertEqual(source["citedby"], 129)

    def test_rejects_lower_count_and_preserves_data(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_stats(root, mock_author())
            prior = (root / "gs_data_shieldsio.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "previously published"):
                write_stats(root, mock_author(127))
            self.assertEqual(prior, (root / "gs_data_shieldsio.json").read_bytes())

    def test_rejects_missing_publications(self):
        bad = mock_author()
        bad["publications"] = []
        with self.assertRaisesRegex(ValueError, "Missing publications"):
            normalize_author(bad)


if __name__ == "__main__":
    unittest.main()
