# EndpointCrawler — Advanced Web Crawler for Recon, OSINT & API Discovery

EndpointCrawler is a **next-generation web crawler** built for bug bounty hunters, red teamers, and OSINT analysts.  
It intelligently extracts:

- Alive URLs with status codes  
- JS file endpoints  
- API/REST endpoints  
- Hidden parameters  
- OSINT-rich external URLs  
- Deep JS-discovered links  
- Browser-rendered dynamic URLs (anti-bot/WAF friendly)

Supports:

✔ Static crawling  
✔ JS parsing  
✔ Browser-mode crawling (Chromium)  
✔ WAF/Cloudflare-friendly behavior  
✔ Multi-threading  
✔ Depth-controlled recursion  

---

## 🚀 Features

### 🔍 **Smart HTML & JS Crawling**
- Extracts URLs from HTML, JS files, inline JS, fetch calls, XHR, open(), etc.
- Follows HTML `<a>`, `<script>`, and dynamic JS-based URLs.

### 🧠 **JS Analysis**
- Finds URLs hidden inside JavaScript code.
- Discovers API endpoints like `/api/*`, `/rest/*`, `/v1/`, `/graphql`, etc.

### 🌐 **Browser Mode (Anti-Bot Safe)**
Solves:
- JS-rendered pages  
- Bot-detection-heavy sites  
- Cloudflare “Browser Verification”  

By using **real Chromium** when needed.

### 🛡 **WAF-Aware Behavior**
Does:
- Randomized headers & user-agents
- Smart delays
- Browser fingerprint mimic
- Adaptive retry strategy

### 🗂 **Clean Output Files**
The tool generates multiple structured output files:
```
prefix_alive_urls.txt
prefix_params.txt
prefix_endpoints.txt
prefix_api_endpoints.txt
prefix_js_files.txt
prefix_osint_strings.txt
```

### ⚡ **Multi-threading**
Speed up your crawl with:
-t 20


### 🔎 **OSINT Collection**
Extracts all **external URLs** including:
- Social media
- CDNs
- API references
- GitHub links
- Documentation URLs
- External resources inside JS

---

# 📦 Installation

### Requirements
- Python 3.8+
- pip
- BeautifulSoup4
- Requests
- Playwright (optional, for browser mode)

Install deps:
```pip install -r requirements.txt```

If browser mode is used:
```playwright install chromium```

🛠 Usage
Basic Crawl
```python3 endpoint_crawler.py https://example.com```

Increase threads & depth
```python3 endpoint_crawler.py https://example.com -t 20 -d 6```

Custom output filename prefix
```python3 endpoint_crawler.py https://example.com -o target```

Auto Mode (HTTP → JS → Browser)
```python3 endpoint_crawler.py https://example.com --mode auto```

Force Browser Mode
```python3 endpoint_crawler.py https://example.com --mode browser```

Use Burp Proxy
```python3 endpoint_crawler.py https://example.com --burp```

---

📁 Output Files
1. prefix_alive_urls.txt
Format:
```<status_code> <url>```

2. prefix_params.txt
All URLs containing ?param=.

3. prefix_endpoints.txt
Backend-related endpoint patterns:
/api/
/rest/
/admin
/v1/
?param=

4. prefix_api_endpoints.txt
Filtered API-only endpoints.

5. prefix_js_files.txt
All JS files found.

6. prefix_osint_strings.txt
All external URLs:
GitHub links
Social media
External APIs
CDN URLs
(OSINT gold mine)

---

🧪 Example Output Summary
```
[✓] Alive URLs: 1048
[✓] Params: 27
[✓] Endpoints: 62
[✓] API Endpoints: 36
[✓] JS files: 20
[✓] OSINT URLs: 33
```

## ⚖ Legal Disclaimer

This tool is intended **ONLY** for:

- Security testing **with permission**
- **Educational** and research purposes
- **Bug bounty** programs

Using this tool on systems **without explicit authorization is illegal**.

The author **is not responsible** for any misuse, damage, or legal consequences resulting from the use of this tool.


❤️ Author
Created with passion for cybersecurity, automation, and recon.


