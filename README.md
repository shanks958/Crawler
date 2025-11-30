# 🔥 EndpointCrawler v2  
### **Advanced Web Crawler for Recon, OSINT, API Discovery & JS Enumeration**

<p align="center">
  <b>A next-generation offensive security crawler built for bug bounty hunters, red teamers, and OSINT analysts.</b>
</p>

---

## 🚀 **What is EndpointCrawler?**

`EndpointCrawler` is a high-performance, multi-threaded web crawler designed to dig deep into a target website and extract everything useful for recon:

- 🔍 **Endpoints** (including hidden & JS-exposed)
- 🧩 **API + REST routes**
- 🌐 **Alive URLs with status codes**
- 🏷️ **Query parameters**
- 📜 **JavaScript files**
- 🕵️ **OSINT URLs**
- 🧠 **Smart WAF-aware engine switching**  
  Requests → Cloudscraper → Browser (Playwright)

No more blind crawling —  
this tool **parses both HTML & JS**, extracts hidden API calls, handles JS-rendered content, and avoids basic WAF blocks.

---

## ⚡ Features

- 🚀 Multi-threaded crawling  
- 🌲 Depth-controlled recursion  
- 🧩 Intelligent JS parsing  
- 🕸️ Detects: `/api/`, `/rest/`, `/v1/`, `/auth/`, GraphQL, etc.  
- 🛡️ Auto WAF handling (403/429/503 detection)  
- 🧠 Switches engine to Cloudscraper or Browser mode automatically  
- 🎯 Extracts URLs from:
  - HTML href/src  
  - Inline JS  
  - External JS files  
  - `fetch()`, `XHR`, and hidden string patterns  
- 📦 Detailed output files:
  - `*_alive_urls.txt`
  - `*_endpoints.txt`
  - `*_api_endpoints.txt`
  - `*_params.txt`
  - `*_js_files.txt`
  - `*_osint_strings.txt`

---

## 📦 Installation

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

Set custom timeout
```python3 endpoint_crawler.py https://example.com --timeout 20```

---

## 📁 Output Files
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

## 🧪 Example Output Summary
```
[✓] Alive URLs: 1048
[✓] Params: 27
[✓] Endpoints: 62
[✓] API Endpoints: 36
[✓] JS files: 20
[✓] OSINT URLs: 33
```
---

## ⚖ Legal Disclaimer

This tool is intended **ONLY** for:

- Security testing **with permission**
- **Educational** and research purposes
- **Bug bounty** programs

Using this tool on systems **without explicit authorization is illegal**.

The author **is not responsible** for any misuse, damage, or legal consequences resulting from the use of this tool.

---

## 👤 Author

shanks958  
GitHub: https://github.com/shanks958



