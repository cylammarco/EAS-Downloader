from pathlib import Path
import re
import unittest


INDEX_HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text()


class QueryAndDownloadUiTest(unittest.TestCase):
    def test_query_and_download_are_separate_actions(self):
        self.assertIn('id="submitBtn" class="primary-btn" type="submit">Run Query</button>', INDEX_HTML)
        self.assertIn('id="stopQueryBtn" class="ghost-btn" type="button" disabled>Stop Query</button>', INDEX_HTML)
        self.assertIn('id="downloadSelectedBtn" class="primary-btn" type="button" disabled>Download Selected</button>', INDEX_HTML)
        self.assertIn('id="downloadSelectedXmlBtn" class="ghost-btn" type="button" disabled>Download Selected XML</button>', INDEX_HTML)

    def test_empty_query_is_allowed_as_match_all(self):
        self.assertIn('placeholder="Leave empty to match all files', INDEX_HTML)
        query_textarea = re.search(r'<textarea\s+id="query"[\s\S]*?</textarea>', INDEX_HTML)
        self.assertIsNotNone(query_textarea)
        self.assertNotIn("required", query_textarea.group(0))
        self.assertIn('if (!username || !password || !dataProduct) {', INDEX_HTML)
        self.assertIn('const MATCH_ALL_PRODUCT_ID_FILTER_KEY = `${PRODUCT_ID_FIELD}!`;', INDEX_HTML)
        self.assertIn('searchParams.append(MATCH_ALL_PRODUCT_ID_FILTER_KEY, MATCH_ALL_PRODUCT_ID_FILTER_VALUE);', INDEX_HTML)

    def test_browser_sends_a_complete_basic_authentication_header(self):
        self.assertIn('return `Basic ${btoa(binary)}`;', INDEX_HTML)

    def test_data_product_dropdowns_sort_alphabetically(self):
        self.assertIn("function sortSelectOptions(select)", INDEX_HTML)
        self.assertIn("ALPHABETICAL_COLLATOR.compare(left.textContent, right.textContent)", INDEX_HTML)
        self.assertIn("sortSelectOptions(dataProductTypeInput);", INDEX_HTML)
        self.assertIn("ALPHABETICAL_COLLATOR.compare(left.name, right.name)", INDEX_HTML)

    def test_query_result_panel_lists_direct_links(self):
        self.assertIn('id="downloadPanel"', INDEX_HTML)
        self.assertIn('const DATA_FILE_NAME_FIELD = "Data.DataStorage.DataContainer.FileName";', INDEX_HTML)
        self.assertIn("function buildDownloadableFileLookupUrl", INDEX_HTML)
        self.assertIn("function extractDownloadableFiles", INDEX_HTML)
        self.assertIn("function buildDssDownloadUrl", INDEX_HTML)
        self.assertIn("directLink.href = file.url;", INDEX_HTML)
        self.assertIn('directLink.textContent = "Download link";', INDEX_HTML)

    def test_dbview_query_uses_class_qualified_fields_and_separate_operators(self):
        self.assertIn("function parseUserQueryConditions(rawQuery)", INDEX_HTML)
        self.assertIn("const match = token.match(/^(.+?)(>=|<=|!=|=|>|<)(.*)$/);", INDEX_HTML)
        self.assertIn("function appendDbViewUserQuery(searchParams, dataProduct, rawQuery)", INDEX_HTML)
        self.assertIn('const qualifiedField = field.startsWith(`${dataProduct}.`) ? field : `${dataProduct}.${field}`;', INDEX_HTML)
        self.assertIn('searchParams.append(`${qualifiedField}.op`, operator);', INDEX_HTML)
        self.assertIn("appendDbViewUserQuery(targetUrl.searchParams, dataProduct, rawQuery);", INDEX_HTML)

    def test_query_panel_shows_returned_rows_and_other_summary_values(self):
        self.assertIn('id="queryReturnedRows"', INDEX_HTML)
        self.assertIn('id="queryDownloadableFiles"', INDEX_HTML)
        self.assertIn('id="queryProject"', INDEX_HTML)
        self.assertIn('id="queryLimitStatus"', INDEX_HTML)
        self.assertIn("function extractDbViewReturnedRowCount(htmlText)", INDEX_HTML)
        self.assertIn("queryReturnedRows.textContent = String(session.returnedRowCount);", INDEX_HTML)

    def test_selected_file_command_defaults_to_python_and_can_toggle_to_shell(self):
        self.assertIn('class="command-format-label">Format</span>', INDEX_HTML)
        self.assertIn('id="commandFormatPythonBtn"', INDEX_HTML)
        self.assertIn('id="commandFormatShellBtn"', INDEX_HTML)
        self.assertIn('id="commandDownloadDataBtn"', INDEX_HTML)
        self.assertIn('id="commandDownloadXmlBtn"', INDEX_HTML)
        self.assertIn('id="commandDownloadBothBtn"', INDEX_HTML)
        self.assertIn('let commandFormat = "python";', INDEX_HTML)
        self.assertIn('let commandDownloadMode = "data";', INDEX_HTML)
        self.assertIn("function updateCommandFormatControls()", INDEX_HTML)
        self.assertIn("function buildCommandDownloadEntries(selectedFiles)", INDEX_HTML)
        self.assertIn("function buildPythonDownloadScript(downloads)", INDEX_HTML)
        self.assertIn("function buildShellDownloadCommand(downloads)", INDEX_HTML)
        self.assertIn('headers["Pragma"] = "DSSGET"', INDEX_HTML)
        self.assertIn('EAS_USERNAME', INDEX_HTML)
        self.assertIn('EAS_PASSWORD', INDEX_HTML)
        self.assertIn('commandFormat = "python";', INDEX_HTML)
        self.assertIn('commandFormat = "shell";', INDEX_HTML)
        self.assertIn('commandDownloadMode = "data";', INDEX_HTML)
        self.assertIn('commandDownloadMode = "xml";', INDEX_HTML)
        self.assertIn('commandDownloadMode = "both";', INDEX_HTML)
        self.assertIn("getSelectedXmlProducts(selectedFiles)", INDEX_HTML)
        self.assertIn("buildObjectXmlExportUrl(querySession.dataProduct, file.objectId, querySession.project)", INDEX_HTML)
        self.assertIn('output: `data/${makeUniqueZipEntryName(file.fileName, index, usedDataNames)}`', INDEX_HTML)
        self.assertIn('output: `xml/${makeUniqueZipEntryName(`${file.productId || file.objectId}.xml`, index, usedXmlNames)}`', INDEX_HTML)
        self.assertIn("dssget: false", INDEX_HTML)
        self.assertIn('if download["dssget"]:', INDEX_HTML)
        self.assertIn("if (download.dssget)", INDEX_HTML)

    def test_script_has_copy_button_and_no_shell_heredoc_wrapper(self):
        self.assertIn('id="copyScriptBtn"', INDEX_HTML)
        self.assertIn('copyScriptBtn.addEventListener("click", copySelectedDownloadScript);', INDEX_HTML)
        self.assertIn("await writeClipboardText(copyableScript);", INDEX_HTML)
        self.assertIn('"#!/usr/bin/env python3"', INDEX_HTML)
        self.assertIn("dssget: download.dssget ? 1 : 0", INDEX_HTML)
        self.assertNotIn("python3 - <<'PY'", INDEX_HTML)
        self.assertRegex(INDEX_HTML, r"pre \{[\s\S]*?max-height: 360px;[\s\S]*?overflow: auto;")

    def test_results_start_selected_and_selection_populates_command(self):
        self.assertIn("checkbox.checked = true;", INDEX_HTML)
        self.assertIn("function updateSelectedDownloadCommand(selectedFiles = getSelectedFiles())", INDEX_HTML)
        self.assertIn("updateSelectedDownloadCommand();", INDEX_HTML)
        self.assertIn('commandOutput.textContent = "Select files to generate a download command.";', INDEX_HTML)

    def test_query_limits_products_server_side_then_chunks_file_lookup(self):
        self.assertRegex(INDEX_HTML, r'id="queryChunkSize"[\s\S]*?value="[1-9][0-9]*"')
        self.assertRegex(INDEX_HTML, r"const DEFAULT_QUERY_CHUNK_SIZE = [1-9][0-9]*;")
        self.assertIn("function buildDbViewRequestUrl", INDEX_HTML)
        self.assertIn('targetUrl.searchParams.set("mainpref_numrows", String(maximumFiles));', INDEX_HTML)
        self.assertIn("function extractDbViewObjectIds", INDEX_HTML)
        self.assertIn("matchAll(/object_id=([0-9A-F]+)/gi)", INDEX_HTML)
        self.assertIn("const MAX_OBJECTS_PER_PROXY_CHUNK = 48;", INDEX_HTML)
        self.assertIn("const objectIdChunks = chunkItems(objectIds, Math.min(queryChunkSize, MAX_OBJECTS_PER_PROXY_CHUNK));", INDEX_HTML)
        self.assertIn("const filesByUrl = new Map();", INDEX_HTML)
        self.assertIn("async function fetchObjectXmlChunk", INDEX_HTML)
        self.assertIn('operation: "resolve-object-xml-chunk"', INDEX_HTML)
        self.assertIn("const chunkResult = await fetchObjectXmlChunk(", INDEX_HTML)
        self.assertIn("chunkResult.files.forEach((file) => filesByUrl.set(file.url, file));", INDEX_HTML)

    def test_query_does_not_poll_one_rest_job_per_product(self):
        query_flow = INDEX_HTML.split("const objectIdChunks =", 1)[1].split("const files = Array.from", 1)[0]

        self.assertNotIn("runAsyncEasRequest(", query_flow)
        self.assertNotIn("objectIdChunk.map(", query_flow)
        self.assertIn("for (let chunkIndex = 0; chunkIndex < objectIdChunks.length; chunkIndex += 1)", query_flow)
        self.assertNotIn("Promise.all", query_flow)

    def test_query_renders_returned_files_after_each_sequential_batch(self):
        self.assertIn("let queryInProgress = false;", INDEX_HTML)
        self.assertIn("function renderDownloadResults(session, queryComplete = true)", INDEX_HTML)
        self.assertIn("querySession.files = Array.from(filesByUrl.values());", INDEX_HTML)
        self.assertIn("renderDownloadResults(querySession, false);", INDEX_HTML)
        self.assertIn("Resolving XML batches sequentially:", INDEX_HTML)

    def test_proxy_error_identifies_stale_deployed_worker(self):
        self.assertIn("Deployed proxy Worker blocked", INDEX_HTML)
        self.assertIn("Deploy proxy-worker.js containing that host allowlist", INDEX_HTML)

    def test_stop_query_aborts_browser_work(self):
        self.assertIn("let activeQueryAbortController = null;", INDEX_HTML)
        self.assertIn('stopQueryBtn.addEventListener("click"', INDEX_HTML)
        self.assertIn("activeQueryAbortController.abort();", INDEX_HTML)
        self.assertIn("signal,", INDEX_HTML)
        self.assertIn("if (isAbortError(error))", INDEX_HTML)
        abort_handler = INDEX_HTML.split("if (isAbortError(error))", 1)[1].split("console.error", 1)[0]
        self.assertNotIn("clearQueryResults();", abort_handler)
        self.assertIn("querySession.stopped = true;", abort_handler)
        self.assertIn("Partial results and generated script were kept.", abort_handler)

    def test_maximum_files_field_defaults_to_1000_and_limits_results(self):
        self.assertIn('<label for="maximumFiles">Maximum Number of Files</label>', INDEX_HTML)
        self.assertIn('id="maximumFiles"', INDEX_HTML)
        self.assertIn('value="1000"', INDEX_HTML)
        self.assertIn('const maximumFiles = parseMaximumFiles(maximumFilesInput.value || String(DEFAULT_MAXIMUM_FILES));', INDEX_HTML)
        self.assertIn('targetUrl.searchParams.set("mainpref_numrows", String(maximumFiles));', INDEX_HTML)

    def test_download_only_uses_checked_dss_files(self):
        self.assertIn("function getSelectedFiles()", INDEX_HTML)
        self.assertIn("const selectedFiles = getSelectedFiles();", INDEX_HTML)
        self.assertIn("async function downloadSelectedFiles()", INDEX_HTML)
        self.assertIn("const fileBlob = await fetchBlob(file.url, querySession.auth);", INDEX_HTML)

    def test_selected_xml_download_uses_one_cus_export_per_selected_product(self):
        self.assertIn("function buildObjectXmlExportUrl(dataProduct, objectId, project)", INDEX_HTML)
        self.assertIn("objectId: String(file?.objectId || \"\").trim()", INDEX_HTML)
        self.assertIn("async function downloadSelectedXmlFiles()", INDEX_HTML)
        self.assertIn("new Map(", INDEX_HTML)
        self.assertIn("buildObjectXmlExportUrl(querySession.dataProduct, file.objectId, querySession.project)", INDEX_HTML)
        self.assertIn("const outputName = `${safeDataProduct}-${timestamp}-xml.zip`;", INDEX_HTML)

    def test_selected_xml_download_is_sequential(self):
        self.assertIn("for (const [index, file] of selectedProducts.entries())", INDEX_HTML)
        self.assertNotIn("XML_DOWNLOAD_CONCURRENCY", INDEX_HTML)
        self.assertNotIn("async function mapWithConcurrency", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
