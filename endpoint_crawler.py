#!/usr/bin/env python3

import argparse
import re
import threading
import time
import random
from queue import Queue, Empty
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

try:
    import cloudscraper
    HAS_CF = True
except:
    HAS_CF = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except:
    HAS_PLAYWRIGHT = False


# =====================
# CONFIG
# =====================

DEFAULT_THREADS = 10
DEFAULT_TIMEOUT = 12
DEFAULT_DEPTH = 4
DEFAULT_PREFIX = "crawl"

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


# =====================
# CLEAN + OSINT HELPERS
# =====================

def clean_url(u: str) -> str:
    if not u:
        return ""
    u = u.replace("\\", "")  # remove backslashes
    u = u.replace('"', "").replace("'", "")
    if "http" in u:
        u = u[u.find("http"):]
    return u.strip()


def extract_osint_urls(raw: str):
    urls = set()
    pattern = re.compile(r"https?://[^\s'\"<>()]+")
    for u in pattern.findall(raw or ""):
        urls.add(clean_url(u))
    return urls


def normalize_url(url: str) -> str:
    p = urlparse(url)
    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urlunparse((p.scheme, p.netloc, path, p.params, p.query, ""))


def same_domain(url: str, domain: str) -> bool:
    return urlparse(url).netloc == domain


def looks_js(url: str) -> bool:
    return url.lower().split("?", 1)[0].endswith(".js")


def looks_endpoint(path: str) -> bool:
    markers = ["/api/", "/rest/", "/v1/", "/v2/", "/graphql", "/admin", "/auth"]
    if any(m in path.lower() for m in markers):
        return True
    return "?" in path


def extract_js_urls(js_text: str, base: str):
    urls = set()
    regexes = [
        re.compile(r"""['"]((?:https?://[^\s"'<>]+|/[A-Za-z0-9_\-./?&=#%+]+))['"]"""),
        re.compile(r"""fetch\s*\(\s*['"]([^'"]+)['"]"""),
        re.compile(r"""\.open\s*\(\s*['"][A-Z]+['"]\s*,\s*['"]([^'"]+)['"]"""),
    ]

    for r in regexes:
        for u in r.findall(js_text or ""):
            u = clean_url(u)
            urls.add(urljoin(base, u))
    return urls


def http_code_valid(code: int) -> bool:
    return 200 <= code <= 599


# ======================================================
# CRAWLER CLASS
# ======================================================

class EndpointCrawler:
    def __init__(self, start, threads, timeout, depth, burp, prefix, mode):
        self.start_url = start
        self.root = urlparse(start).netloc
        self.threads = threads
        self.timeout = timeout
        self.depth = depth
        self.prefix = prefix
        self.burp = burp          # FIXED — must be declared before HTTP engine
        self.mode = mode          # "auto" / "requests" / "cloudscraper" / "browser"

        # engine selection logic
        if mode == "auto":
            self.engine = "requests"
        else:
            self.engine = mode

        # dynamic engine object (session)
        self.session = None

        # Playwright state
        self.playwright = None
        self.browser = None

        self._init_http_engine()

        # Threading
        self.queue = Queue()
        self.lock = threading.Lock()

        # visited
        self.visited_html = set()
        self.visited_js = set()
        self.queued_html = set()
        self.queued_js = set()

        # OUTPUT STORAGE
        self.alive = {}
        self.params = set()
        self.endpoints = set()
        self.api_endpoints = set()
        self.js_files = set()
        self.osint_strings = set()

	    # ====================
    # LOG
    # ====================
    def log(self, *msg):
        with self.lock:
            print(*msg)

    # ====================
    # ENGINE INIT
    # ====================
    def _init_http_engine(self):
        """
        Initialize HTTP engine based on current self.engine.
        """
        if self.engine == "cloudscraper":
            if not HAS_CF:
                self.log("[!] cloudscraper not installed, falling back to requests.")
                self.engine = "requests"

        if self.engine in ("requests", "cloudscraper"):
            if self.engine == "cloudscraper":
                self.session = cloudscraper.create_scraper()
            else:
                self.session = requests.Session()

            self.session.headers.update(BASE_HEADERS)
            if self.burp:
                self.session.proxies.update({
                    "http": "http://127.0.0.1:8080",
                    "https": "http://127.0.0.1:8080",
                })
                self.session.verify = False

    # ====================
    # WAF-ish Detection
    # ====================
    def is_waf_like(self, status, headers, body_snippet):
        """
        Simple WAF-ish detection: used ONLY to decide engine switching.
        We are NOT bypassing anything – just behaving smarter.
        """
        if status in (403, 406, 409, 429, 503):
            return True

        headers = headers or {}
        h_lower = {k.lower(): v for k, v in headers.items()}
        b = (body_snippet or "").lower()

        waf_header_markers = [
            "cf-ray", "cf-cache-status", "cf-chl-bypass",
            "x-sucuri-id", "x-sucuri-block",
            "x-amzn-waf-id", "x-amz-cf-id",
            "x-iinfo", "incapsula", "x-cdn",
            "akamai", "x-akamai", "x-akamai-transformed",
            "x-waf", "x-firewall",
        ]
        for key in waf_header_markers:
            for hk in h_lower.keys():
                if key in hk:
                    return True

        waf_body_markers = [
            "checking your browser",       # cloudflare
            "just a moment",               # cloudflare
            "ddos protection by",
            "web application firewall",
            "access denied",
            "you are being rate limited",
            "/cdn-cgi/l/chk_jschl",
            "waf",
        ]
        for m in waf_body_markers:
            if m in b:
                return True

        return False

    # ====================
    # FETCH HELPERS
    # ====================
    def _fetch_requests(self, url):
        """
        Use self.session (requests / cloudscraper) to fetch.
        """
        if self.session is None:
            self._init_http_engine()

        try:
            r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            return r.status_code, r.text, r.url, r.headers
        except Exception:
            return None, None, url, {}

    def _fetch_browser(self, url):
        """
        Use Playwright for a single-page fetch.
        (We keep it stateless for safety with threads.)
        """
        if not HAS_PLAYWRIGHT:
            self.log("[!] Playwright not installed, cannot use browser mode.")
            return None, None, url

        try:
            with sync_playwright() as p:
                for name in ["chromium", "firefox", "webkit"]:
                    try:
                        browser_type = getattr(p, name)
                        browser = browser_type.launch(headless=True)
                        page = browser.new_page()
                        page.set_default_timeout(self.timeout * 1000)
                        page.goto(url, wait_until="networkidle")
                        html = page.content()
                        final_url = page.url
                        # some engines let you inspect response; we approximate with 200 if no error
                        browser.close()
                        self.log(f"[!] Browser mode used ({name}) for {url}")
                        return 200, html, final_url
                    except Exception:
                        continue
        except Exception as e:
            self.log(f"[!] Playwright error for {url}: {e}")

        return None, None, url

    # ====================
    # FETCH (ENGINE + AUTO)
    # ====================
    def fetch(self, url):
        """
        Fetch URL depending on mode / engine.
        Returns: (status, body, final_url)
        """
        # Hard modes
        if self.mode == "requests":
            self.engine = "requests"
            status, text, final_url, _ = self._fetch_requests(url)
            return status, text, final_url

        if self.mode == "cloudscraper":
            self.engine = "cloudscraper"
            status, text, final_url, _ = self._fetch_requests(url)
            return status, text, final_url

        if self.mode == "browser":
            self.engine = "browser"
            status, text, final_url = self._fetch_browser(url)
            return status, text, final_url

        # AUTO MODE
        # Step 1: try requests
        if self.engine not in ("requests", "cloudscraper", "browser"):
            self.engine = "requests"

        if self.engine in ("requests", "cloudscraper"):
            # ensure HTTP engine is ready
            if self.session is None:
                self._init_http_engine()

            status, text, final_url, headers = self._fetch_requests(url)
            if status is None:
                return None, None, final_url

            body_snip = (text or "")[:2048]
            if self.is_waf_like(status, headers, body_snip):
                # Try cloudscraper if not already
                if HAS_CF and self.engine != "cloudscraper":
                    self.log("[!] WAF-ish response, switching to Cloudscraper...")
                    self.engine = "cloudscraper"
                    self.session = None  # force re-init
                    status2, text2, final_url2, headers2 = self._fetch_requests(url)
                    if status2 is not None and not self.is_waf_like(status2, headers2, (text2 or "")[:2048]):
                        return status2, text2, final_url2
                    status, text, final_url = status2, text2, final_url2

                # If still WAFish and Playwright available → browser
                if HAS_PLAYWRIGHT:
                    self.log("[!] Strong protection / JS challenge, using browser mode...")
                    self.engine = "browser"
                    status3, text3, final_url3 = self._fetch_browser(url)
                    if status3 is not None:
                        return status3, text3, final_url3

            return status, text, final_url

        if self.engine == "browser":
            status, text, final_url = self._fetch_browser(url)
            return status, text, final_url

        # fallback
        status, text, final_url, _ = self._fetch_requests(url)
        return status, text, final_url

    # ====================
    # HTML HANDLER
    # ====================
    def handle_html(self, url, html, depth):
        soup = BeautifulSoup(html, "html.parser")

        # Inline JS OSINT
        for s in soup.find_all("script"):
            if not s.get("src"):
                self.osint_strings.update(extract_osint_urls(s.string or ""))

        # Links
        for a in soup.find_all("a", href=True):
            nxt = clean_url(urljoin(url, a["href"]))
            nxt = normalize_url(nxt)

            # external → OSINT
            if not same_domain(nxt, self.root):
                self.osint_strings.add(nxt)
                continue

            # depth control
            if depth + 1 > self.depth:
                continue

            with self.lock:
                if nxt in self.queued_html or nxt in self.visited_html:
                    continue
                self.queued_html.add(nxt)

            self.log(f"[HTML][{depth+1}] {nxt}")
            self.queue.put((nxt, depth + 1, "html"))

        # Script files
        for s in soup.find_all("script", src=True):
            js = clean_url(urljoin(url, s["src"]))
            js = normalize_url(js)

            if not same_domain(js, self.root):
                self.osint_strings.add(js)
                continue

            if depth + 1 > self.depth:
                continue

            with self.lock:
                if js in self.queued_js or js in self.visited_js:
                    continue
                self.queued_js.add(js)

            self.log(f"[JS][{depth+1}] {js}")
            self.queue.put((js, depth + 1, "js"))

    # ====================
    # JS HANDLER
    # ====================
    def handle_js(self, url, js_body, depth):
        # OSINT from JS itself
        self.osint_strings.update(extract_osint_urls(js_body))

        for found in extract_js_urls(js_body, url):
            found = clean_url(found)

            if not same_domain(found, self.root):
                self.osint_strings.add(found)
                continue

            found = normalize_url(found)

            if depth + 1 > self.depth:
                continue

            kind = "js" if looks_js(found) else "html"
            visited = self.visited_js if kind == "js" else self.visited_html
            queued = self.queued_js if kind == "js" else self.queued_html

            with self.lock:
                if found in visited or found in queued:
                    continue
                queued.add(found)

            self.log(f"[FOUND][{kind.upper()}] {found}")
            self.queue.put((found, depth + 1, kind))

    # ====================
    # WORKER
    # ====================
    def worker(self):
        while True:
            try:
                url, depth, kind = self.queue.get(timeout=2)
            except Empty:
                return

            try:
                if kind == "html":
                    with self.lock:
                        if url in self.visited_html:
                            continue
                        self.visited_html.add(url)
                else:
                    with self.lock:
                        if url in self.visited_js:
                            continue
                        self.visited_js.add(url)

                # For HTTP engines, set random UA
                if self.engine in ("requests", "cloudscraper") and self.session is not None:
                    self.session.headers["User-Agent"] = random.choice(UA_LIST)

                status, body, final_url = self.fetch(url)
                if status is None or body is None:
                    continue

                if not http_code_valid(status):
                    continue

                clean = clean_url(final_url or url)
                self.alive[clean] = status

                # params
                if "?" in clean:
                    self.params.add(clean)
                    self.log("[PARAM]", clean)

                parsed = urlparse(clean)
                full = parsed.path + ("?" + parsed.query if parsed.query else "")

                if looks_endpoint(full):
                    self.endpoints.add(clean)
                    self.log("[ENDPOINT]", clean)
                    if "/api/" in full or "/rest/" in full or "graphql" in full:
                        self.api_endpoints.add(clean)
                        self.log("[API]", clean)

                if looks_js(clean):
                    self.js_files.add(clean)

                if 200 <= status < 300:
                    if kind == "html":
                        self.handle_html(clean, body, depth)
                    else:
                        self.handle_js(clean, body, depth)

            finally:
                self.queue.task_done()

    # ====================
    # SAVE OUTPUT
    # ====================
    def save(self):
        base = self.prefix

        def write(name, data, alive=False):
            with open(name, "w") as f:
                if alive:
                    for u in sorted(data):
                        f.write(f"{data[u]}\t{u}\n")
                else:
                    for u in sorted(data):
                        f.write(u + "\n")

        write(f"{base}_alive_urls.txt", self.alive, alive=True)
        write(f"{base}_params.txt", self.params)
        write(f"{base}_endpoints.txt", self.endpoints)
        write(f"{base}_api_endpoints.txt", self.api_endpoints)
        write(f"{base}_js_files.txt", self.js_files)
        write(f"{base}_osint_strings.txt", self.osint_strings)

        self.log("[✓] Output saved!")

    # ====================
    # RUN
    # ====================
    def run(self):
        start = normalize_url(clean_url(self.start_url))

        with self.lock:
            self.queued_html.add(start)

        self.queue.put((start, 0, "html"))

        t0 = time.time()
        self.log(f"[+] Starting crawl: {start}")

        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker, daemon=True)
            threads.append(t)
            t.start()

        # Wait for threads
        self.queue.join()

        # Save output
        self.save()

        elapsed = time.time() - t0
        self.log(f"[✓] Crawl finished in {elapsed:.2f}s")
        self.log(f"[✓] Alive URLs: {len(self.alive)}")
        self.log(f"[✓] Params: {len(self.params)}")
        self.log(f"[✓] Endpoints: {len(self.endpoints)}")
        self.log(f"[✓] API Endpoints: {len(self.api_endpoints)}")
        self.log(f"[✓] JS files: {len(self.js_files)}")
        self.log(f"[✓] OSINT URLs: {len(self.osint_strings)}")


# =======================
# MAIN
# =======================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-t", "--threads", type=int, default=DEFAULT_THREADS)
    parser.add_argument("-d", "--depth", type=int, default=DEFAULT_DEPTH)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--burp", action="store_true",
                        help="Send traffic through Burp at 127.0.0.1:8080")
    parser.add_argument("-o", "--prefix", default=DEFAULT_PREFIX)
    parser.add_argument(
        "--mode",
        choices=["auto", "requests", "cloudscraper", "browser"],
        default="auto",
        help="Engine: auto / requests / cloudscraper / browser (Playwright)"
    )
    args = parser.parse_args()

    crawler = EndpointCrawler(
        args.url,
        args.threads,
        args.timeout,
        args.depth,
        args.burp,
        args.prefix,
        args.mode
    )
    crawler.run()


if __name__ == "__main__":
    main()
