#!/usr/bin/env python3
"""Backlink live-URL checker — deterministic gates for the backlink-live-validator skill.

stdlib-only (no pip installs). Fetches each live URL logged-out (no cookies, no
session), and reports: access verdict, target-URL presence + rel attribute,
and content signals for the agent to score.

Usage:
  python3 check_links.py input.json > output.json
  python3 check_links.py --selftest

Input JSON: [{"row": 2, "live_url": "...", "target_url": "...", "activity_type": "..."}, ...]
Output JSON: same rows + result fields (see check_row).
"""

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
TIMEOUT = 20
MAX_BODY = 2_000_000
MAX_WORKERS = 10


def normalize(url: str) -> str:
    """Lowercase, strip scheme/www/trailing slash — for URL comparison."""
    if not url:
        return ""
    u = url.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []  # (href, rel)
        self.title = ""
        self.images = 0
        self.password_inputs = 0
        self.text_parts = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.anchors.append((a.get("href", ""), (a.get("rel") or "").lower()))
        elif tag == "title":
            self._in_title = True
        elif tag == "img":
            self.images += 1
        elif tag == "input" and (a.get("type") or "").lower() == "password":
            self.password_inputs += 1
        elif tag in ("script", "style", "noscript"):
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in ("script", "style", "noscript") and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip_depth:
            d = data.strip()
            if d:
                self.text_parts.append(d)


LOGIN_RX = re.compile(r"\b(log ?in|sign ?in|sign ?up|register|create (an )?account)\b", re.I)


def fetch(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            body = r.read(MAX_BODY).decode("utf-8", "replace")
            return r.getcode(), r.geturl(), body, None
    except urllib.error.HTTPError as e:
        return e.code, url, "", "HTTP %d" % e.code
    except Exception as e:
        return None, url, "", "%s: %s" % (type(e).__name__, e)


def analyze_html(body, target_url):
    """Parse HTML and report link/content signals. Network-free (selftest uses this)."""
    p = PageParser()
    try:
        p.feed(body)
    except Exception:
        pass
    text = " ".join(p.text_parts)
    tn = normalize(target_url)
    found_link, linked_rel = False, ""
    for href, rel in p.anchors:
        if tn and tn in normalize(href):
            found_link, linked_rel = True, rel
            break
    text_flat = re.sub(r"https?://(www\.)?", "", text.lower())
    text_mention = bool(tn) and tn in text_flat
    if found_link:
        if "nofollow" in linked_rel:
            rel_out = "nofollow"
        elif "sponsored" in linked_rel or "ugc" in linked_rel:
            rel_out = linked_rel
        else:
            rel_out = "dofollow"
        link_verdict = "LINK_FOUND"
    elif text_mention:
        rel_out, link_verdict = "", "MENTION_ONLY"
    else:
        rel_out, link_verdict = "", "TARGET_URL_MISSING"
    words = len(text.split())
    return {
        "link_verdict": link_verdict,
        "rel": rel_out,
        "word_count": words,
        "images": p.images,
        "anchor_count": len(p.anchors),
        "title": p.title.strip()[:120],
        "password_inputs": p.password_inputs,
        "login_keyword_hits": len(LOGIN_RX.findall(text[:3000])),
        "snippet": text[:400],
        "js_render_suspect": words < 40 and len(p.anchors) < 3,
    }


def check_row(row):
    out = dict(row)
    live = (row.get("live_url") or "").strip()
    target = (row.get("target_url") or "").strip()
    if not re.match(r"^https?://\S+\.\S+", live):
        out.update(access="INVALID_URL", detail="URL malformed ya khali")
        return out

    code, final_url, body, err = fetch(live)
    out["status_code"] = code
    out["final_url"] = final_url
    out["redirected"] = normalize(final_url) != normalize(live)

    if code is None:
        out.update(access="INVALID_URL", detail=err)
        return out
    if code in (404, 410):
        out.update(access="404_NOT_FOUND", detail="HTTP %d" % code)
        return out
    if code in (401, 403):
        out.update(access="LOGIN_WALL", detail="HTTP %d (access blocked)" % code)
        return out
    if code >= 400:
        out.update(access="INVALID_URL", detail="HTTP %d" % code)
        return out

    sig = analyze_html(body, target)
    out.update(sig)

    if sig["password_inputs"] > 0 and sig["word_count"] < 300:
        out.update(access="LOGIN_WALL", detail="password field + thin page")
    elif sig["login_keyword_hits"] >= 2 and sig["word_count"] < 150:
        out.update(access="LOGIN_WALL_SUSPECT",
                   detail="login/signup keywords, content nahi — browser se verify karo")
    else:
        out["access"] = "OK"
    return out


# ── selftest ────────────────────────────────────────────────────────────────

SELFTEST_PAGES = {
    "dofollow": (
        "<html><head><title>Guest Post</title></head><body>"
        "<p>" + ("word " * 400) + "</p>"
        "<a href='https://www.fameninja.com/services/'>Fame Ninja</a>"
        "<img src='x.jpg'></body></html>",
        "https://fameninja.com/services",
        {"link_verdict": "LINK_FOUND", "rel": "dofollow"},
    ),
    "nofollow": (
        "<html><body><p>" + ("word " * 200) + "</p>"
        "<a rel='nofollow noopener' href='http://fameninja.com/services'>x</a></body></html>",
        "https://www.fameninja.com/services/",
        {"link_verdict": "LINK_FOUND", "rel": "nofollow"},
    ),
    "mention_only": (
        "<html><body><p>Visit fameninja.com/services today. " + ("word " * 100) + "</p></body></html>",
        "https://fameninja.com/services",
        {"link_verdict": "MENTION_ONLY"},
    ),
    "missing": (
        "<html><body><p>" + ("word " * 100) + "</p><a href='https://other.com/'>o</a></body></html>",
        "https://fameninja.com/services",
        {"link_verdict": "TARGET_URL_MISSING"},
    ),
    "login_wall": (
        "<html><body><form><input type='password'></form><p>Sign in to continue. Sign up free.</p></body></html>",
        "https://fameninja.com",
        {"password_inputs": 1},
    ),
}


def selftest():
    failures = 0
    for name, (html, target, expect) in SELFTEST_PAGES.items():
        got = analyze_html(html, target)
        for k, v in expect.items():
            if got.get(k) != v:
                print("FAIL %s: %s = %r (expected %r)" % (name, k, got.get(k), v))
                failures += 1
            else:
                print("PASS %s: %s = %r" % (name, k, v))
    assert normalize("HTTPS://WWW.FameNinja.com/x/") == "fameninja.com/x"
    print("PASS normalize")
    if failures:
        sys.exit(1)
    print("SELFTEST OK")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "--selftest":
        selftest()
        return
    with open(sys.argv[1]) as f:
        rows = json.load(f)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        results = list(ex.map(check_row, rows))
    json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
