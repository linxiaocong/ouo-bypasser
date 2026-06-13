# Ouo Bypasser

A simple Python CLI tool to resolve short URLs from **ouo.io** and **ouo.press** to their final destination URLs.

## Features
- Resolve single URLs or a list of URLs from a file.
- Handles nested redirection chains (up to 5 levels).
- Increases request timeout to 60 seconds to avoid timed‑out errors.
- Automatic retry with a 180‑second back‑off when any error occurs (up to 3 attempts).
- Uses `curl_cffi` with a Safari 15.5 fingerprint to bypass Cloudflare Turnstile.
- Outputs results to the console or writes them to a file in a tabular format.

## Installation
```bash
# Clone the repository (if you have it locally, skip this step)
git clone https://github.com/yourusername/ouo-bypasser.git
cd ouo-bypasser

# Install dependencies (recommended inside a virtual environment)
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
### Resolve a single URL
```bash
python bypass_ouo.py https://ouo.io/2skcYS1
```

### Resolve multiple URLs from a file
Create a plain‑text file (e.g., `urls.txt`) with one URL per line:
```
https://ouo.io/e31WsK
https://ouo.press/abc123
```
Run the script specifying the input file and output file:
```bash
python bypass_ouo.py -f urls.txt -o resolved.txt
```
The tool will read all URLs from `urls.txt`, resolve them, and write a table to `resolved.txt`.

## Options
- **-f, --file** – Path to the input file containing a list of URLs (one per line).
- **-o, --output** – Path to the output file to write the results to. If omitted, results are printed to stdout.
- **Positional Arguments** – One or more direct URLs to process.
- **Timeout** – Internally set to 60 seconds per request.
- **Retry** – Up to 3 attempts with a 180‑second delay between attempts on any failure.

## Example Output
```
============================================================
Short URL                      | Status   | Destination
============================================================
https://ouo.io/2skcYS1         | success  | https://ouo.io/JIXyN8
============================================================
```

## License
This project is licensed under the GPLv3 License.
