from pathlib import Path
import re
import unittest


INDEX_HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text()


class QueryAndDownloadUiTest(unittest.TestCase):
    def test_page_has_dark_first_branded_header_and_footer(self):
        self.assertIn('<html lang="en" data-theme="dark">', INDEX_HTML)
        self.assertIn('<title>EAS Downloader</title>', INDEX_HTML)
        self.assertIn('<header class="site-header">', INDEX_HTML)
        self.assertIn('<h1 class="brand-name">EAS Downloader</h1>', INDEX_HTML)
        self.assertIn('src="./images/University%20of%20Edinburgh%20Logo.png"', INDEX_HTML)
        self.assertIn('src="./images/Euclid_consortium_logo.png"', INDEX_HTML)
        self.assertIn('<footer class="site-footer">', INDEX_HTML)

    def test_footer_includes_requested_reference_and_github_links(self):
        self.assertIn('href="https://eas-dps-cus-ops.esac.esa.int/"', INDEX_HTML)
        self.assertIn('href="http://st-dm.pages.euclid-sgs.uk/ST_DataModel/10.0.2/"', INDEX_HTML)
        self.assertIn('href="http://st-dm.pages.euclid-sgs.uk/data-product-doc/dm10/"', INDEX_HTML)
        self.assertIn('href="https://github.com/cylammarco/EAS-Downloader"', INDEX_HTML)
        self.assertIn('class="github-button"', INDEX_HTML)
        self.assertIn('class="github-star-control"', INDEX_HTML)
        self.assertIn('src="./images/GitHub-Mark.png"', INDEX_HTML)
        self.assertIn('data-icon="octicon-star-fill"', INDEX_HTML)
        self.assertIn('data-show-count="true"', INDEX_HTML)
        self.assertIn('src="https://buttons.github.io/buttons.js"', INDEX_HTML)

    def test_footer_is_centered_and_visual_layout_uses_wider_dark_plain_background(self):
        self.assertIn("justify-content: center;", INDEX_HTML)
        self.assertIn("width: min(1176px, calc(100% - 2.4rem));", INDEX_HTML)
        self.assertIn("background: var(--page);", INDEX_HTML)
        self.assertIn(':root[data-theme="light"] body {', INDEX_HTML)
        self.assertNotIn(".github-link {", INDEX_HTML)
        self.assertNotIn("border-right: 1px solid var(--line-subtle);", INDEX_HTML)
        self.assertIn("@media (max-width: 980px)", INDEX_HTML)
        self.assertIn("@media (max-width: 760px)", INDEX_HTML)

    def test_theme_toggle_defaults_to_dark_on_every_page_load(self):
        self.assertIn('id="themeToggle"', INDEX_HTML)
        self.assertIn('function applyTheme(theme)', INDEX_HTML)
        self.assertIn('function toggleTheme()', INDEX_HTML)
        self.assertNotIn('localStorage.getItem("eas-downloader-theme")', INDEX_HTML)
        self.assertNotIn('localStorage.setItem(THEME_STORAGE_KEY, nextTheme);', INDEX_HTML)
        self.assertIn('applyTheme("dark");', INDEX_HTML)
        self.assertIn('themeToggleBtn.addEventListener("click", toggleTheme);', INDEX_HTML)

    def test_query_and_download_are_separate_actions(self):
        self.assertIn('id="submitBtn" class="primary-btn" type="submit">Run Query</button>', INDEX_HTML)
        self.assertIn('id="stopQueryBtn" class="ghost-btn" type="button" disabled>Stop Query</button>', INDEX_HTML)
        self.assertIn('id="downloadSelectedBtn" class="primary-btn" type="button" disabled>Download Selected</button>', INDEX_HTML)
        self.assertIn('id="downloadSelectedXmlBtn" class="ghost-btn" type="button" disabled>Download Matching XML</button>', INDEX_HTML)

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
        self.assertIn("getMatchingXmlProducts()", INDEX_HTML)
        self.assertIn("buildObjectXmlExportUrl(querySession.dataProduct, product.objectId, querySession.project)", INDEX_HTML)
        self.assertIn('output: `data/${makeUniqueZipEntryName(file.fileName, index, usedDataNames)}`', INDEX_HTML)
        self.assertIn('output: `xml/${makeUniqueZipEntryName(`${product.productId || product.objectId}.xml`, index, usedXmlNames)}`', INDEX_HTML)
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

    def test_query_uses_two_server_limited_dbview_requests(self):
        self.assertNotIn('id="queryChunkSize"', INDEX_HTML)
        self.assertIn("function buildDbViewRequestUrl", INDEX_HTML)
        self.assertIn('targetUrl.searchParams.set("mainpref_numrows", String(maximumFiles));', INDEX_HTML)
        self.assertIn('targetUrl.searchParams.set("Exportselect", "NoDownload");', INDEX_HTML)
        self.assertIn('`${dataProduct}.Header#GenericHeader`,', INDEX_HTML)
        self.assertLess(
            INDEX_HTML.index('`${dataProduct}.Header#GenericHeader`,'),
            INDEX_HTML.index('`${dataProduct}.Header.ProductId#ObjectId`,'),
        )
        self.assertIn("function buildDbViewFileExportUrl", INDEX_HTML)
        self.assertIn('targetUrl.searchParams.set("Exportselect", "FITS");', INDEX_HTML)
        self.assertIn("function extractDbViewProducts", INDEX_HTML)
        self.assertIn("function extractDbViewFileLinks", INDEX_HTML)
        self.assertIn("const products = extractDbViewProducts(dbViewHtml);", INDEX_HTML)
        self.assertIn("const files = extractDbViewFileLinks(fileListText);", INDEX_HTML)
        self.assertIn("requestCount: 1", INDEX_HTML)
        self.assertIn("querySession.requestCount = 2;", INDEX_HTML)

    def test_query_does_not_poll_or_export_xml_per_product(self):
        query_flow = INDEX_HTML.split('form.addEventListener("submit"', 1)[1]

        self.assertNotIn("runAsyncEasRequest(", query_flow)
        self.assertNotIn("fetchObjectXmlChunk(", query_flow)
        self.assertNotIn("for (let chunkIndex", query_flow)
        self.assertNotIn("Promise.all", query_flow)

    def test_query_has_one_five_minute_deadline_and_keeps_intermediate_summary(self):
        self.assertIn("let queryInProgress = false;", INDEX_HTML)
        self.assertIn("const QUERY_TIMEOUT_MS = 5 * 60 * 1000;", INDEX_HTML)
        self.assertIn("function fetchTextBeforeDeadline", INDEX_HTML)
        self.assertIn("const queryDeadline = queryStartedAt + QUERY_TIMEOUT_MS;", INDEX_HTML)
        self.assertEqual(INDEX_HTML.count("queryDeadline,\n"), 2)
        self.assertIn("function renderDownloadResults(session, queryComplete = true)", INDEX_HTML)
        self.assertIn("renderDownloadResults(querySession, false);", INDEX_HTML)
        self.assertIn("Retrieving file links with optimized DbView export (request 2/2)", INDEX_HTML)
        self.assertIn("Query exceeded five-minute limit", INDEX_HTML)

    def test_large_result_list_is_added_with_one_document_fragment(self):
        self.assertIn("const resultFragment = document.createDocumentFragment();", INDEX_HTML)
        self.assertIn("resultFragment.appendChild(item);", INDEX_HTML)
        self.assertIn("downloadList.appendChild(resultFragment);", INDEX_HTML)

    def test_proxy_error_identifies_stale_deployed_worker(self):
        self.assertIn("Deployed proxy Worker blocked", INDEX_HTML)
        self.assertIn("Deploy proxy-worker.js containing that host allowlist", INDEX_HTML)

    def test_html_proxy_errors_are_reduced_to_useful_eas_exception_text(self):
        self.assertIn("function summarizeProxyErrorResponse(responseText, fallbackText)", INDEX_HTML)
        self.assertIn("/^Exception\\s*:/i.test(item)", INDEX_HTML)
        self.assertIn("summarizeProxyErrorResponse(text, response.statusText)", INDEX_HTML)

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

    def test_matching_xml_download_uses_one_cus_export_per_matching_product(self):
        self.assertIn("function buildObjectXmlExportUrl(dataProduct, objectId, project)", INDEX_HTML)
        self.assertIn("async function downloadMatchingXmlFiles()", INDEX_HTML)
        self.assertIn("const matchingProducts = getMatchingXmlProducts();", INDEX_HTML)
        self.assertIn("buildObjectXmlExportUrl(querySession.dataProduct, product.objectId, querySession.project)", INDEX_HTML)
        self.assertIn("const outputName = `${safeDataProduct}-${timestamp}-xml.zip`;", INDEX_HTML)

    def test_matching_xml_download_is_sequential(self):
        self.assertIn("for (const [index, product] of matchingProducts.entries())", INDEX_HTML)
        self.assertNotIn("XML_DOWNLOAD_CONCURRENCY", INDEX_HTML)
        self.assertNotIn("async function mapWithConcurrency", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
