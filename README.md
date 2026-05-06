# EAS Query Page

Single-page static web app version of `download_eas_script.py`.

## What it does

- Lets users enter `username`, `password`, and `query`
- Uses a two-step Data Product selector:
  - first level: type (`LE1`, `SIM`, `VIS`, `NIR`, `SIR`, `EXT`, `MER`, `PHZ`, `SPE`, `SHE`, `LE3`, `DQC`, `SOC`, `Missing`)
  - second level: corresponding PascalCase Data Product names from documentation cards (or `Missing` entries when docs lack a name)
- Uses a project dropdown with: `TEST`, `EUCLID`, `ALL`
- Requires a `Proxy Endpoint (Cloudflare Worker)` URL in the form before running queries
- Submits the async EAS request and polls until completion
- Extracts XML metadata files from the returned TGZ archive
- Downloads XML files as a zip and also downloads the original TGZ archive
- Generates the equivalent Python command for terminal use

## Publish on GitHub Pages

1. Create a new GitHub repository and upload this folder contents (`index.html`, `data-product-options.js`, and this `README.md`) to the repository root.
2. In repository settings, open **Pages**.
3. Set source to **Deploy from a branch**.
4. Select branch `main` and folder `/ (root)`.
5. Save. GitHub will publish the page URL.

## Important note

Direct browser calls to EAS are blocked by CORS. This page is implemented to call EAS through a backend proxy endpoint (for example a Cloudflare Worker URL).
