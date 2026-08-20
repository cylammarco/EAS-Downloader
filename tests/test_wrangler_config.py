import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "wrangler.jsonc").read_text())


class WranglerConfigTest(unittest.TestCase):
    def test_cloudflare_build_deploys_proxy_worker_entrypoint(self):
        self.assertEqual(CONFIG["name"], "eas-downloader-proxy")
        self.assertEqual(CONFIG["main"], "proxy-worker.js")

    def test_proxy_build_does_not_replace_worker_with_static_assets(self):
        self.assertNotIn("assets", CONFIG)
        self.assertFalse((ROOT / "wrangler.toml").exists())


if __name__ == "__main__":
    unittest.main()
