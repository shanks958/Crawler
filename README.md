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

