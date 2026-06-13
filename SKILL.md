# Skill: Ouo Bypasser

**Name**: `ouo-bypasser`

**Description**: A command‑line Python utility that resolves short URLs from the `ouo.io` and `ouo.press` services to their final destination URLs. It supports batch processing via input files, handles nested redirects, incorporates extended timeouts, and retries failed requests after a back‑off period.

**Key Capabilities**
- **Single‑URL resolution** – Provide a URL directly as a command‑line argument.
- **Batch resolution** – Supply a text file containing one URL per line; the tool reads all URLs and resolves them sequentially.
- **Output options** – Results are printed to STDOUT or written to a specified output file as a formatted table.
- **Robust networking** – 60‑second request timeout and up to three retry attempts with a 180‑second delay on any error.
- **Cloudflare bypass** – Utilises `curl_cffi` with a Safari 15.5 fingerprint to evade Cloudflare Turnstile challenges that block simple `requests` calls.
- **Recursive un‑shortening** – Follows up to five redirection levels automatically to reach the ultimate destination URL.

**Typical Workflow**
1. Install dependencies via `pip install -r requirements.txt`.
2. Run the script:
   - Single URL: `python bypass_ouo.py https://ouo.io/abcd`
   - From file: `python bypass_ouo.py -f urls.txt -o resolved.txt`
3. Review the tabular output or the generated `resolved.txt` file.

**Limitations**
- Only supports URLs from `ouo.io` and `ouo.press` domains.
- Maximum redirection depth is limited to five levels to prevent infinite loops.
- Retries are fixed to three attempts; additional customization would require code changes.

**License**
- Distributed under the MIT License.
