import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "download_eas_script.py"
SPEC = importlib.util.spec_from_file_location("download_eas_script", MODULE_PATH)
DOWNLOADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOWNLOADER)


class QueryChunkingTest(unittest.TestCase):
    def test_chunk_product_ids_preserves_order_and_size(self):
        chunks = list(DOWNLOADER.chunk_product_ids(["one", "two", "three", "four", "five"], 2))

        self.assertEqual(chunks, [["one", "two"], ["three", "four"], ["five"]])

    def test_chunk_query_keeps_original_filters_and_adds_id_filter(self):
        query = DOWNLOADER.build_chunk_query("Header.DataSetRelease=Q1", ["one", "two"])

        self.assertEqual(
            query,
            "Header.DataSetRelease=Q1&Header.ProductId.LimitedString=includes(one,two)",
        )

    def test_lookup_query_requests_only_product_ids(self):
        query = DOWNLOADER.build_eas_query(
            "https://example.invalid/REST?class_name=",
            "DpdMerFinalCatalog",
            "Header.DataSetRelease=Q1",
            "EUCLID",
            fields=DOWNLOADER.PRODUCT_ID_FIELD,
        )

        self.assertIn("fields=Header.ProductId.LimitedString", query)
        self.assertNotIn("file_format=TGZ", query)

    def test_empty_query_matches_all_without_empty_filter(self):
        query = DOWNLOADER.build_eas_query(
            "https://example.invalid/REST?class_name=",
            "DpdVisCalibratedQuadFrame",
            "",
            "EUCLID",
            fields=DOWNLOADER.PRODUCT_ID_FIELD,
        )

        self.assertIn("class_name=DpdVisCalibratedQuadFrame", query)
        self.assertIn("make_asy=True", query)
        self.assertIn('Header.ProductId.LimitedString!=""', query)
        self.assertNotIn("&&", query)


if __name__ == "__main__":
    unittest.main()
