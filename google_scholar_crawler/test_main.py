"""Offline integration tests: SerpApi JSON -> existing AcadHomepage files."""
import json
from pathlib import Path
import tempfile
import unittest
from main import AUTHOR_ID, transform, write_files, read_existing

def previous():
    return {
        "scholar_id": AUTHOR_ID, "name": "Xiaochen Wang", "citedby": 129,
        "publications": {
            AUTHOR_ID + ":abc": {"author_pub_id": AUTHOR_ID + ":abc", "num_citations": 3},
            AUTHOR_ID + ":def": {"author_pub_id": AUTHOR_ID + ":def", "num_citations": 1},
        },
        "hindex": 4,
    }

def fixture(cited=130):
    return {
        "search_metadata": {"status": "Success"},
        "search_parameters": {"engine": "google_scholar_author", "author_id": AUTHOR_ID},
        "author": {"name": "Xiaochen Wang"},
        "cited_by": {
            "table": [
                {"citations": {"all": cited, "since_2021": 119}},
                {"h_index": {"all": 4, "since_2021": 4}},
                {"i10_index": {"all": 3, "since_2021": 3}},
            ],
            "graph": [{"year": 2026, "citations": 75}],
        },
        "articles": [{"citation_id": AUTHOR_ID + ":abc", "cited_by": {"value": 4}}],
    }

class Tests(unittest.TestCase):
    def test_convert_metrics(self):
        updated = transform(fixture(), previous(), AUTHOR_ID)
        self.assertEqual(updated["citedby"], 130)
        self.assertEqual(updated["citedby5y"], 119)
        self.assertEqual(updated["hindex"], 4)
        self.assertEqual(updated["publications"][AUTHOR_ID + ":abc"]["num_citations"], 4)
        self.assertEqual(updated["publications"][AUTHOR_ID + ":def"]["num_citations"], 1)

    def test_does_not_lower_total(self):
        with self.assertRaises(ValueError):
            transform(fixture(127), previous(), AUTHOR_ID)

    def test_rejects_wrong_author(self):
        data = fixture()
        data["search_parameters"]["author_id"] = "other_author"
        with self.assertRaisesRegex(ValueError, "author"):
            transform(data, previous(), AUTHOR_ID)

    def test_rejects_missing_metrics(self):
        data = fixture()
        data["cited_by"]["table"] = []
        with self.assertRaisesRegex(ValueError, "Missing total"):
            transform(data, previous(), AUTHOR_ID)

    def test_writes_site_json_and_badge(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / "gs_data.json").write_text(json.dumps(previous()), encoding="utf-8")
            final = transform(fixture(), read_existing(directory), AUTHOR_ID)
            write_files(directory, final)
            self.assertEqual(json.loads((directory / "gs_data.json").read_text())["citedby"], 130)
            self.assertEqual(json.loads((directory / "gs_data_shieldsio.json").read_text())["message"], "130")

    def test_invalid_write_keeps_original(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            initial = json.dumps(previous())
            (directory / "gs_data.json").write_text(initial, encoding="utf-8")
            with self.assertRaises(ValueError):
                write_files(directory, {**previous(), "citedby": 127})
            self.assertEqual((directory / "gs_data.json").read_text(), initial)


if __name__ == "__main__":
    unittest.main()
