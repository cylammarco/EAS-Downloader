from pathlib import Path
import unittest


WORKER = (Path(__file__).resolve().parents[1] / "proxy-worker.js").read_text()


class ProxyWorkerTest(unittest.TestCase):
    def test_proxy_allows_public_page_and_loopback_http_origins(self):
        self.assertIn("function isAllowedOrigin(origin)", WORKER)
        self.assertIn('url.protocol === "http:"', WORKER)
        self.assertIn('"localhost"', WORKER)
        self.assertIn('"127.0.0.1"', WORKER)
        self.assertIn('"[::1]"', WORKER)

    def test_proxy_uses_origin_helper_for_cors_and_access_control(self):
        self.assertEqual(WORKER.count("isAllowedOrigin(origin)"), 3)

    def test_dbview_host_is_allowlisted(self):
        self.assertIn('"eas-dps-cus-ops.esac.esa.int"', WORKER)

    def test_worker_resolves_a_whole_object_chunk_in_one_browser_request(self):
        self.assertIn('payload.operation === "resolve-object-xml-chunk"', WORKER)
        self.assertIn("async function resolveObjectXmlChunk", WORKER)
        self.assertIn("const MAX_OBJECTS_PER_PROXY_CHUNK = 20;", WORKER)
        self.assertIn("const OBJECT_FETCH_CONCURRENCY = 5;", WORKER)
        self.assertIn('new URL(`https://${CUS_HOST}/XML`)', WORKER)
        self.assertIn('xmlTagValues(xmlText, "DataStorage")', WORKER)
        self.assertIn('files: fileNames.map((fileName) => ({ objectId, productId, fileName }))', WORKER)

    def test_dss_header_is_scoped_to_dss_host(self):
        self.assertIn('if (target.hostname === DSS_HOST && payload.requestHeaders?.Pragma === "DSSGET")', WORKER)
        self.assertIn('headers.set("Pragma", "DSSGET");', WORKER)

    def test_proxy_normalizes_legacy_base64_and_complete_basic_headers(self):
        self.assertIn("function normalizeBasicAuth(value)", WORKER)
        self.assertIn('rawValue.replace(/^Basic\\s+/i, "")', WORKER)
        self.assertIn("const authHeaderValue = normalizeBasicAuth(payload.authHeaderValue);", WORKER)

    def test_proxy_rejects_unapproved_target_hosts(self):
        self.assertIn("if (!isAllowedTarget(target))", WORKER)
        self.assertIn("Proxy target URL allowlist blocked", WORKER)


if __name__ == "__main__":
    unittest.main()
