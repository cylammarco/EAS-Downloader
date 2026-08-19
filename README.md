# EAS Query Page

Single-page static web app version of `download_eas_script.py`.

## What it does

- Lets users enter `username`, `password`, and an optional `query` (empty matches all products)
- Uses a two-step Data Product selector:
  - first level: type (`LE1`, `SIM`, `VIS`, `NIR`, `SIR`, `EXT`, `MER`, `PHZ`, `SPE`, `SHE`, `LE3`, `DQC`, `SOC`, `Missing`)
  - second level: corresponding PascalCase Data Product names from documentation cards (or `Missing` entries when docs lack a name)
- Uses a project dropdown with: `TEST`, `EUCLID`, `ALL`
- Calls EAS through the configured Cloudflare Worker proxy before running queries
- Requests at most the configured number of matching products from DbView before resolving file names
- Resolves `FileName` values from EAS XML exports in configurable proxy chunks (default: 100 products)
- Concatenates returned file links from every chunk
- Stops at the server-selected product limit (default: 1000); it does not first retrieve every matching product
- Renders each result as an actual DSS download URL: `https://euclidsoc.esac.esa.int/<FileName>`
- Lets users select matching DSS files, then packages selected files in one zip
- Generates Python or shell download commands for selected DSS files

## Large queries

EAS can time out while assembling one large product query. **Run Query** asks DbView for only the first matching product
rows, using `mainpref_numrows=Maximum Number of Files`. The Worker then resolves each selected product's EAS XML export
and concatenates `FileName` values in groups of **Query Chunk Size**. It does not issue an unbounded REST product-ID
query before applying the maximum, and it does not create a browser-to-Worker request for every EAS poll.
Set **Query Chunk Size** to control products per Worker batch; default: `100`. Batches are internally limited to `48`
products, leaving headroom below Cloudflare Free's 50-subrequest limit. The Worker resolves EAS XML exports one at a
time; browser batches are also serial. Returned DSS links appear in the page after every finished batch.
Set **Maximum Number of Files** to control the server-side DbView row request; default: `1000`.
Leave **Query String** empty to match all products of selected data-product class, akin to SQL `SELECT *`. The launcher
adds EAS filter `Header.ProductId.LimitedString!=""`, required because EAS rejects an empty search statement.

Result links are DSS file URLs. **Download Selected** fetches selected DSS files through the configured proxy and creates
one zip. **Download Selected XML** fetches EAS `/XML` exports one at a time for selected products and creates a separate
XML zip. The deployed proxy must allow `euclidsoc.esac.esa.int` and forward `Pragma: DSSGET` for DSS requests.
It must also allow `eas-dps-cus-ops.esac.esa.int` for server-limited DbView and XML-export queries. **Stop Query**
aborts browser requests. XML export does not submit background EAS jobs.

## Proxy Worker

This repository includes [proxy-worker.js](proxy-worker.js) and [wrangler.jsonc](wrangler.jsonc). The Worker allows only
the EAS REST hosts, `eas-dps-cus-ops.esac.esa.int`, and `euclidsoc.esac.esa.int`; it batches up to 48 EAS XML exports
inside one browser request and forwards `Pragma: DSSGET` only to
the DSS host. It accepts browser origins from GitHub Pages plus `http://localhost`, `http://127.0.0.1`, and IPv6
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
**Format** (Python or shell) and **Download** (Data, XML, or Both) controls. XML commands use the selected products'
EAS `/XML` exports; data commands use DSS URLs with `Pragma: DSSGET`. Both require `EAS_USERNAME` and `EAS_PASSWORD`.
The command updates whenever selection or either control changes.

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
