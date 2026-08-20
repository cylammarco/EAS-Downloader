# EAS Downloader

Single-page static web app [https://cylammarco.github.io/EAS-Downloader/](https://cylammarco.github.io/EAS-Downloader/)

## What it does

- Lets users enter `username`, `password`, and an optional `query` (empty matches all products)
- Uses a two-step Data Product selector:
  - first level: type (`LE1`, `SIM`, `VIS`, `NIR`, `SIR`, `EXT`, `MER`, `PHZ`, `SPE`, `SHE`, `LE3`, `DQC`, `SOC`, `Missing`)
  - second level: corresponding PascalCase Data Product names from documentation cards (or `Missing` entries when docs lack a name)
- Uses a project dropdown with: `TEST`, `EUCLID`, `ALL`
- Calls EAS through the configured Cloudflare Worker proxy before running queries
- Requests at most the configured number of matching products from DbView
- Converts REST-style query expressions (including `>=`, `<=`, and `!=`) to DbView's class-qualified field and operator parameters
- Retrieves all matching file links with DbView's bulk `FITS` link export
- Uses two EAS calls for a non-empty result: one product-list call and one file-link export
- Enforces one five-minute deadline across both query calls
- Stops at the server-selected product limit (default: 1000); it does not first retrieve every matching product
- Shows returned-row count, downloadable-file count, project, and server-limit status
- Renders each result as an actual DSS download URL: `https://euclidsoc.esac.esa.int/<FileName>`
- Lets users select matching DSS files, then packages selected files in one zip
- Generates Python or shell download commands for selected DSS files

## Large queries

EAS can time out while assembling deeply nested REST field queries. **Run Query** instead uses two bounded DbView calls.
First call returns matching rows plus product/object IDs, limited by `mainpref_numrows=Maximum Number of Files`. Second
call uses DbView's `Exportselect=FITS` output to retrieve all associated DSS links at once. Search does not fetch one XML
document per product and does not start or poll asynchronous REST jobs. One five-minute client deadline covers both
calls; narrow filters or lower maximum when EAS cannot finish within it.
Set **Maximum Number of Files** to control the server-side DbView row request; default: `1000`.
Leave **Query String** empty to match all products of selected data-product class, akin to SQL `SELECT *`. The launcher
adds EAS filter `Header.ProductId.LimitedString!=""`, required because EAS rejects an empty search statement.

Result links are DSS file URLs. **Download Selected** fetches selected DSS files through the configured proxy and creates
one zip. **Download Matching XML** fetches EAS `/XML` exports one at a time for every matching product and creates a
separate XML zip. File selection affects data downloads only because bulk DbView output does not map files to products.
The deployed proxy must allow `euclidsoc.esac.esa.int` and forward `Pragma: DSSGET` for DSS requests.
It must also allow `eas-dps-cus-ops.esac.esa.int` for server-limited DbView and XML-export queries. **Stop Query**
aborts browser requests. XML export does not submit background EAS jobs.

## Proxy Worker

This repository includes [proxy-worker.js](proxy-worker.js) and [wrangler.jsonc](wrangler.jsonc). The Worker allows only
the EAS REST hosts, `eas-dps-cus-ops.esac.esa.int`, and `euclidsoc.esac.esa.int`. Query flow uses its generic streaming
proxy for two DbView requests; legacy XML batching remains available but is not used during search. Worker forwards
`Pragma: DSSGET` only to the DSS host. It accepts browser origins from GitHub Pages plus `http://localhost`, `http://127.0.0.1`, and IPv6
loopback for local development. Deploy it in the Cloudflare account that owns `eas-downloader-proxy.cylammarco.workers.dev`:

```bash
npx wrangler deploy
```

If deployment uses another Worker URL, change `PROXY_ENDPOINT` in `index.html` to that URL.

For local use, serve this directory over HTTP; do not open `index.html` as a `file://` URL:

```bash
python3 -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000). Deploy the Worker after changing it; an already-deployed
Worker keeps its previous host and origin allowlists.

After query results appear, every file is selected by default. The **Selected-file download command** panel has visible
**Format** (Python or shell) and **Download** (Data, XML, or Both) controls. XML commands use all matching products'
EAS `/XML` exports; data commands use selected DSS URLs with `Pragma: DSSGET`. Both require `EAS_USERNAME` and `EAS_PASSWORD`.
The command updates whenever selection or either control changes.
Use **Copy Script** to copy the generated Python script or shell command. Python output is a standalone script (no shell
heredoc wrapper), and the script panel has a fixed maximum height with its own scrollbar. Stopping a query preserves any
partial results and generated script already shown.

The command-line Python tool selects output with `--download`:

```bash
python3 download_eas_script.py --username USER --data_product DpdVisCalibratedQuadFrame --download xml
```

Choose `xml` for metadata XML only, `data` for DSS data files only, or `both` for both. XML output defaults to
`eas-xml`; data output defaults to `eas-data`. Override them with `--xml_output_dir DIRECTORY` and
`--data_output_dir DIRECTORY`.

## Publish on GitHub Pages

1. Create a new GitHub repository and upload this folder contents (`index.html`, `data-product-options.js`, and this `README.md`) to the repository root.
2. In repository settings, open **Pages**.
3. Set source to **Deploy from a branch**.
4. Select branch `main` and folder `/ (root)`.
5. Save. GitHub will publish the page URL.

## Important note

Direct browser calls to EAS are blocked by CORS. This page is implemented to call EAS through a backend proxy endpoint (for example a Cloudflare Worker URL).
