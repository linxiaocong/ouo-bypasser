#!/usr/bin/env python3
import sys
import re
import json
import argparse
import urllib.parse
import requests as std_requests
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

# Retrieve the latest Google reCAPTCHA v3 version dynamically
def get_recaptcha_version():
    try:
        # Load the main api.js from Google reCAPTCHA
        res = std_requests.get('https://www.google.com/recaptcha/api.js?render=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x', timeout=60)
        # Find the release version (e.g. r202312040939 or similar)
        match = re.search(r'releases/([^/]+)/recaptcha__', res.text)
        if match:
            return match.group(1)
    except Exception:
        pass
    # Fallback default version if the dynamic fetch fails
    return 'pCoGBhjs9s8EhFOHJFe8cqis'

# Solve reCAPTCHA v3 and return the token response (rresp)
def solve_recaptcha_v3():
    v = get_recaptcha_version()
    anchor_url = f'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&hl=en&v={v}&size=invisible&cb=ahgyd1gkfkhe'
    
    rs = std_requests.Session()
    rs.headers.update({'content-type': 'application/x-www-form-urlencoded'})
    
    # Extract params from the anchor URL
    matches = re.findall(r'([api2|enterprise]+)\/anchor\?(.*)', anchor_url)[0]
    url_base = 'https://www.google.com/recaptcha/' + matches[0] + '/'
    params = matches[1]
    
    # Fetch anchor page to retrieve token
    res = rs.get(url_base + 'anchor', params=params, timeout=60)
    token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]
    
    # Reload to solve reCAPTCHA
    params_dict = dict(pair.split('=') for pair in params.split('&'))
    post_data = f"v={params_dict['v']}&reason=q&c={token}&k={params_dict['k']}&co={params_dict['co']}"
    res = rs.post(url_base + 'reload', params=f'k={params_dict["k"]}', data=post_data, timeout=60)
    
    # Return the solved token
    return re.findall(r'"rresp","(.*?)"', res.text)[0]

# Resolve a single layer of ouo.io / ouo.press redirection
def bypass_ouo_single(url: str):
    tempurl = url.replace("ouo.press", "ouo.io")
    p = urllib.parse.urlparse(tempurl)
    
    # Extract the ID from the short URL
    path_parts = p.path.strip('/').split('/')
    if not path_parts or path_parts[0] == '':
        raise ValueError("Invalid ouo URL structure: no path ID found.")
    url_id = path_parts[-1]
    
    # Setup impersonation client to avoid TLS fingerprint blocks (Cloudflare, etc.)
    client = curl_requests.Session(headers={
        'authority': 'ouo.io',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'referer': 'https://www.google.com/',
        'upgrade-insecure-requests': '1'
    })
    
    # Step 1: Initial GET
    res = client.get(tempurl, impersonate="safari15_5", timeout=60)
    next_url = f"{p.scheme}://{p.hostname}/go/{url_id}"
    
    # Multi-step POST (usually 2 loops)
    for _ in range(2):
        if res.headers.get('Location'):
            break
            
        soup = BeautifulSoup(res.content, 'html.parser')
        form = soup.form
        if not form:
            # Check if we landed directly or met a redirect
            if res.status_code in (301, 302, 307, 308) and res.headers.get('Location'):
                return res.headers.get('Location')
            raise RuntimeError("Could not find form elements on the page. You might have been blocked or the page structure changed.")
            
        inputs = form.findAll("input", {"name": re.compile(r"token$")})
        data = {inp.get('name'): inp.get('value') for inp in inputs}
        
        # Inject solved reCAPTCHA v3 token
        data['x-token'] = solve_recaptcha_v3()
        
        # Post the token & get response
        res = client.post(
            next_url,
            data=data,
            headers={'content-type': 'application/x-www-form-urlencoded'},
            allow_redirects=False,
            impersonate="safari15_5",
            timeout=60
        )
        
        # Update endpoint for step 2
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{url_id}"
        
    final_url = res.headers.get('Location')
    if not final_url:
        raise RuntimeError("Bypass failed. Did not receive redirect header from ouo.")
        
    return final_url

# Bypass ouo.io / ouo.press URL (supports recursive redirection chains)
def bypass_ouo(url: str, max_depth: int = 5):
    current_url = url
    for depth in range(max_depth):
        parsed = urllib.parse.urlparse(current_url)
        is_ouo = any(domain in parsed.netloc.lower() for domain in ("ouo.io", "ouo.press"))
        if not is_ouo:
            return current_url
        
        if depth > 0:
            print(f"\n  └─> Found nested link, resolving: {current_url} ... ", end="", flush=True)
            
        # Resolve one level
        current_url = bypass_ouo_single(current_url)
        
        if depth > 0:
            print("Done!", end="", flush=True)
            
    raise RuntimeError(f"Redirection chain exceeded max depth of {max_depth}")

def main():
    import os
    
    parser = argparse.ArgumentParser(description="Ouo Link Bypasser - Resolve the original destination URL from ouo.io/ouo.press short URLs.")
    parser.add_argument("inputs", nargs="*", help="List of direct ouo short URLs to bypass.")
    parser.add_argument("-f", "--file", help="Path to a text file containing ouo URLs (one per line).")
    parser.add_argument("-o", "--output", help="Path to save output results (supports txt or json format).")
    
    args = parser.parse_args()
    
    urls_to_process = []
    input_file = args.file
    output_file = args.output
    
    # 1. Parse positional inputs as direct URLs
    if args.inputs:
        urls_to_process.extend(args.inputs)
        
    # 3. Read URLs from input file if specified
    if input_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comment lines
                    if line and not line.startswith('#'):
                        urls_to_process.append(line)
            print(f"Loaded {len(urls_to_process)} URLs from file '{input_file}'")
        except Exception as e:
            print(f"Error reading file '{input_file}': {e}", file=sys.stderr)
            sys.exit(1)
            
    # 4. Interactive fallback if no URLs are supplied
    if not urls_to_process:
        print("No URLs specified via command-line arguments or file.")
        print("Enter ouo short URLs line-by-line (press Enter on an empty line to finish):")
        while True:
            try:
                line = input("> ").strip()
                if not line:
                    break
                urls_to_process.append(line)
            except (KeyboardInterrupt, EOFError):
                print()
                break
                
    if not urls_to_process:
        print("No URLs to process. Exiting.")
        sys.exit(0)
        
    print(f"\nProcessing {len(urls_to_process)} URLs...\n")
    
    results = []
    max_retries = 2  # Total 3 attempts (1 initial + 2 retries)
    for idx, url in enumerate(urls_to_process, 1):
        print(f"[{idx}/{len(urls_to_process)}] Resolving: {url} ... ", end="", flush=True)
        
        attempt = 0
        success = False
        original_url = None
        error_msg = ""
        
        while attempt <= max_retries:
            try:
                if not (url.startswith("http://") or url.startswith("https://")):
                    raise ValueError("URL must start with http:// or https://")
                
                # Run the bypass logic
                original_url = bypass_ouo(url)
                success = True
                break
            except Exception as e:
                attempt += 1
                error_msg = str(e)
                if attempt <= max_retries:
                    print(f"Failed! (Error: {e})")
                    print(f"  └─> Retrying in 180 seconds... (Attempt {attempt + 1}/{max_retries + 1})")
                    import time
                    # Sleep in increments of 10s to keep execution responsive/responsive logs
                    for _ in range(18):
                        time.sleep(10)
                    print(f"[{idx}/{len(urls_to_process)}] Resolving: {url} (Retry {attempt}) ... ", end="", flush=True)
                else:
                    break
        
        if success:
            print("Done!")
            print(f"  └─> {original_url}\n")
            results.append({
                "short_url": url,
                "original_url": original_url,
                "status": "success"
            })
        else:
            print("Failed!")
            print(f"  └─> Error: {error_msg}\n")
            results.append({
                "short_url": url,
                "error": error_msg,
                "status": "failed"
            })
            
    # Print Summary Table
    print("=" * 60)
    print(f"{'Short URL':<30} | {'Status':<8} | {'Destination'}")
    print("=" * 60)
    for r in results:
        dest = r.get("original_url") or r.get("error", "Unknown error")
        # Truncate for display if too long
        if len(dest) > 40:
            dest = dest[:37] + "..."
        print(f"{r['short_url'][:30]:<30} | {r['status']:<8} | {dest}")
    print("=" * 60)
    
    # Save output if requested
    if output_file:
        try:
            if output_file.lower().endswith(".json"):
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=4)
            else:
                # Text output: Write one original URL per line
                with open(output_file, 'w', encoding='utf-8') as f:
                    for r in results:
                        if r["status"] == "success":
                            f.write(f"{r['original_url']}\n")
                        else:
                            f.write(f"ERROR: {r['error']} (for {r['short_url']})\n")
            print(f"\nResults successfully exported to '{output_file}'")
        except Exception as e:
            print(f"Error saving output to '{output_file}': {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
