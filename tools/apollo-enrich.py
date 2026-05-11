#!/usr/bin/env python3
"""
Apollo API enrichment tool — find emails for GTM contacts.

Important: Apollo's /people/match and /people/search BOTH silently ignore
the `organization_domain(s)` parameter. They only correctly scope to a
company when given an `organization_id`, so every operation in this tool
first resolves domain -> Apollo org_id via /organizations/enrich (free).

Recommended (highest hit rate):

  Find — search + reveal email by title at a domain:
    python tools/apollo-enrich.py find --domain playtika.com
    python tools/apollo-enrich.py find --domain roblox.com \\
        --titles "Chief Safety Officer,Head of Trust and Safety"

  Find without spending credits (search only, last names obfuscated):
    python tools/apollo-enrich.py find --domain playtika.com --no-enrich

Other modes:

  Search (free, no credits, last names obfuscated):
    python tools/apollo-enrich.py search --domain cyera.io --title "CISO"

  Enrich a known person by name (1 credit; resolves org_id automatically):
    python tools/apollo-enrich.py enrich --domain cyera.io --name "Nathan Smolenski"
    python tools/apollo-enrich.py enrich --domain cyera.io --name "Nathan Smolenski" \\
        --linkedin https://linkedin.com/in/nathan-smolenski   # strongest match

  Debug any single call (prints raw Apollo response + headers):
    python tools/apollo-enrich.py enrich --domain x.com --name "..." --debug
    python tools/apollo-enrich.py find --domain x.com --debug

  Batch (reads target-accounts.md, enriches named contacts without emails):
    python tools/apollo-enrich.py batch --file output/target-accounts.md
    python tools/apollo-enrich.py batch --file output/target-accounts.md --update
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "email-config.json"

APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
APOLLO_ENRICH_URL = "https://api.apollo.io/api/v1/people/match"
APOLLO_ORG_ENRICH_URL = "https://api.apollo.io/api/v1/organizations/enrich"

PROJECT_ROOT = SCRIPT_DIR.parent

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def normalize_domain(raw: str) -> str:
    """Take first hostname from 'a.com / b.com' or 'a.com extra text'."""
    s = raw.strip().strip("*").strip()
    if "/" in s:
        s = s.split("/")[0].strip()
    s = s.split()[0] if s else ""
    return s

def load_api_key() -> str:
    if not CONFIG_PATH.exists():
        print("Error: Config file not found at", CONFIG_PATH, file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    key = config.get("apollo_api_key", "")
    if not key or key.startswith("YOUR"):
        print("Error: apollo_api_key not set in", CONFIG_PATH, file=sys.stderr)
        sys.exit(1)
    return key


def headers(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
    }

# ---------------------------------------------------------------------------
# Organization resolution (free)
# ---------------------------------------------------------------------------

# Cache org-id lookups within a single CLI run to avoid repeat calls.
_ORG_CACHE: dict[str, dict] = {}


def resolve_organization(api_key: str, domain: str) -> dict | None:
    """Resolve a domain to Apollo's internal organization record.

    Critical: Apollo's /people/match and /people/search BOTH ignore the
    `organization_domain(s)` parameter. They only correctly scope to a
    company when you pass `organization_id`. So every lookup must start
    here.

    Returns None if Apollo doesn't know the company.
    """
    domain = normalize_domain(domain).lower()
    if not domain:
        return None
    if domain in _ORG_CACHE:
        return _ORG_CACHE[domain]
    resp = requests.get(
        APOLLO_ORG_ENRICH_URL,
        headers=headers(api_key),
        params={"domain": domain},
        timeout=30,
    )
    if DEBUG_ENRICH:
        print(f"\n--- DEBUG: /organizations/enrich domain={domain} status={resp.status_code} ---")
        try:
            print(json.dumps(resp.json(), indent=2)[:2000])
        except Exception:
            print(resp.text[:1000])
        print("--- /DEBUG ---\n")
    resp.raise_for_status()
    org = (resp.json() or {}).get("organization") or None
    if org and not org.get("id"):
        org = None
    _ORG_CACHE[domain] = org
    return org


# ---------------------------------------------------------------------------
# Search (free)
# ---------------------------------------------------------------------------

def search_people(
    api_key: str,
    domain: str,
    title: str | None = None,
    titles: list[str] | None = None,
    seniority: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Search Apollo for people at a company. Free — no credits consumed.

    Resolves the domain → Apollo organization_id first. The search endpoint
    silently ignores `organization_domains` — without an org_id we get
    global title matches, not people at the company.

    Note: search responses obfuscate last names ("Ra***i"). Call
    enrich_person_by_id() to reveal the full name + email (1 credit).
    """
    org = resolve_organization(api_key, domain)
    if not org:
        return []

    title_list = [t for t in (titles or []) if t]
    if title and title not in title_list:
        title_list.append(title)

    payload: dict = {
        "organization_ids": [org["id"]],
        "page": 1,
        "per_page": min(limit, 25),
    }
    if title_list:
        payload["person_titles"] = title_list
    if seniority:
        payload["person_seniorities"] = seniority

    resp = requests.post(APOLLO_SEARCH_URL, headers=headers(api_key), json=payload, timeout=30)
    if DEBUG_ENRICH:
        print(f"\n--- DEBUG: /mixed_people/api_search status={resp.status_code} ---")
        try:
            print(json.dumps(resp.json(), indent=2)[:3000])
        except Exception:
            print(resp.text[:1000])
        print("--- /DEBUG ---\n")
    resp.raise_for_status()
    data = resp.json()

    results = []
    for person in data.get("people", []):
        # Apollo returns last_name_obfuscated like "Ra***i" until enriched.
        last_disp = person.get("last_name") or person.get("last_name_obfuscated") or ""
        first = person.get("first_name") or ""
        results.append({
            "id": person.get("id"),
            "name": (first + " " + last_disp).strip(),
            "first_name": first,
            "last_name": person.get("last_name", ""),
            "last_name_display": last_disp,
            "title": person.get("title", ""),
            "linkedin": person.get("linkedin_url", ""),
            "city": person.get("city", ""),
            "country": person.get("country", ""),
            "organization_name": (person.get("organization") or {}).get("name", org.get("name", "")),
        })
    return results


def print_search_results(results: list[dict], domain: str, title: str | None):
    query = f"{title} @ {domain}" if title else domain
    if not results:
        print(f"No results for: {query}  (verify domain is in Apollo's database)")
        return
    print(f"\n{'='*70}")
    print(f"  Search: {query}  ({len(results)} results, 0 credits used)")
    print(f"  Note: last names obfuscated until enriched. Use 'find' to unmask.")
    print(f"{'='*70}\n")
    for i, p in enumerate(results, 1):
        print(f"  {i}. {p['name']}    [id={p.get('id','?')}]")
        print(f"     Title:    {p['title']}")
        if p.get("organization_name"):
            print(f"     Org:      {p['organization_name']}")
        if p["linkedin"]:
            print(f"     LinkedIn: {p['linkedin']}")
        loc = ", ".join(filter(None, [p.get("city"), p.get("country")]))
        if loc:
            print(f"     Location: {loc}")
        print()

# ---------------------------------------------------------------------------
# Enrich (1 credit)
# ---------------------------------------------------------------------------

def _is_real_email(s: str) -> bool:
    """Filter Apollo's masked / unlocked-placeholder values."""
    if not s:
        return False
    s = s.strip().lower()
    if "@" not in s:
        return False
    bad_markers = (
        "email_not_unlocked",
        "domain.com",  # Apollo placeholder
        "not_unlocked",
        "email_hidden",
    )
    return not any(m in s for m in bad_markers)


def extract_work_email_from_person(person: dict) -> str:
    """Pull the best work email from Apollo's response.

    Apollo's /people/match response can surface emails in several shapes:
      - person.email (string, often blank or 'email_not_unlocked@...')
      - person.contact_emails[] (list of {email, type, ...})
      - person.personal_emails[] (list of strings — only populated if
        reveal_personal_emails=true)
      - person.organization_email_format (gives a synthesizable pattern,
        not used here; kept as a fallback only)

    Returns the first real, non-masked email found, prioritizing work.
    """
    if not person:
        return ""

    direct = (person.get("email") or "").strip()
    if _is_real_email(direct):
        return direct

    for ce in person.get("contact_emails") or []:
        if isinstance(ce, dict):
            e = (ce.get("email") or "").strip()
            if _is_real_email(e):
                return e

    for pe in person.get("personal_emails") or []:
        if isinstance(pe, str) and _is_real_email(pe):
            return pe
        if isinstance(pe, dict):
            e = (pe.get("email") or "").strip()
            if _is_real_email(e):
                return e

    return ""


def normalize_linkedin_url(raw: str) -> str | None:
    s = raw.strip()
    if not s or "needs" in s.lower() or "lookup" in s.lower() or "manual" in s.lower():
        return None
    if "linkedin.com" not in s.lower():
        return None
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return "https://" + s.lstrip("/")


DEBUG_ENRICH = False  # set via --debug CLI flag

def enrich_person(
    api_key: str,
    domain: str,
    first_name: str,
    last_name: str,
    linkedin_url: str | None = None,
    reveal_personal: bool = True,
) -> dict | None:
    """Enrich a person by name + domain. Costs 1 credit.

    Apollo's /people/match endpoint silently IGNORES the
    `organization_domain` filter when matching by name — it returns the
    closest global name match instead, with org data stripped out. This
    is why every previous enrichment came back as "(not found)".

    The fix: resolve the domain to an Apollo organization_id first via
    /organizations/enrich (free), then pass that id to /people/match. If
    the name doesn't appear in Apollo at that org, fall back to a
    title-search and use the closest match's id (also handled by
    find_people()).
    """
    # Strong path 1: caller already knows the LinkedIn URL.
    if linkedin_url:
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "linkedin_url": linkedin_url,
            "reveal_personal_emails": bool(reveal_personal),
            "reveal_phone_number": False,
        }
        return _post_match(api_key, payload)

    # Strong path 2: resolve org_id, then match by name within that org.
    org = resolve_organization(api_key, domain)
    if org and org.get("id"):
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "organization_id": org["id"],
            "reveal_personal_emails": bool(reveal_personal),
            "reveal_phone_number": False,
        }
        result = _post_match(api_key, payload)
        # If by-name match against the org returned a stub (no title),
        # search the org for any close-name candidates and enrich by id.
        if result and not result.get("title"):
            candidate = _find_candidate_by_name(api_key, org["id"], first_name, last_name)
            if candidate and candidate.get("id"):
                by_id = enrich_person_by_id(api_key, candidate["id"], reveal_personal)
                if by_id:
                    return by_id
        if result:
            return result

    # Last-ditch fallback: original name+domain call (often returns stubs).
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "organization_domain": domain,
        "reveal_personal_emails": bool(reveal_personal),
        "reveal_phone_number": False,
    }
    return _post_match(api_key, payload)


def _post_match(api_key: str, payload: dict) -> dict | None:
    resp = requests.post(APOLLO_ENRICH_URL, headers=headers(api_key), json=payload, timeout=30)
    if DEBUG_ENRICH:
        print(f"\n--- DEBUG: /people/match status={resp.status_code} payload={json.dumps({k:v for k,v in payload.items() if k!='reveal_personal_emails'})} ---")
        for h in ("x-rate-limit-minute", "x-rate-limit-hourly", "x-rate-limit-daily",
                  "x-24-hour-usage", "x-minute-usage", "x-hourly-usage"):
            if h in resp.headers:
                print(f"  {h}: {resp.headers[h]}")
        try:
            print(json.dumps(resp.json(), indent=2)[:3000])
        except Exception:
            print(resp.text[:1500])
        print("--- /DEBUG ---\n")
    resp.raise_for_status()
    person = (resp.json() or {}).get("person") or None
    if not person:
        return None
    return {
        "name": person.get("name", ""),
        "first_name": person.get("first_name", ""),
        "last_name": person.get("last_name", ""),
        "title": person.get("title", ""),
        "email": extract_work_email_from_person(person),
        "email_status": person.get("email_status", ""),
        "linkedin": person.get("linkedin_url", ""),
        "company": (person.get("organization") or {}).get("name", ""),
    }


def _find_candidate_by_name(api_key: str, org_id: str, first_name: str, last_name: str) -> dict | None:
    """Search the org's people for the best candidate matching the given name.

    Apollo obfuscates last names in search ("Ra***i"), so we match on
    first_name exact + last_name first-letter when available.
    """
    payload = {"organization_ids": [org_id], "page": 1, "per_page": 25, "q_keywords": first_name}
    try:
        resp = requests.post(APOLLO_SEARCH_URL, headers=headers(api_key), json=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    candidates = (resp.json() or {}).get("people") or []
    last_initial = (last_name or "")[:1].lower()
    best = None
    for p in candidates:
        if (p.get("first_name") or "").strip().lower() != first_name.strip().lower():
            continue
        obf = (p.get("last_name_obfuscated") or "").lower()
        if last_initial and obf.startswith(last_initial):
            return p  # strong match
        best = best or p  # weak fallback
    return best


def enrich_person_by_id(api_key: str, person_id: str, reveal_personal: bool = True) -> dict | None:
    """Enrich an Apollo person record by its internal id. Costs 1 credit.

    This is the highest-confidence enrichment path — Apollo will return the
    full record (real last name, verified email, title, LinkedIn) for the
    exact person you found via search.
    """
    payload = {
        "id": person_id,
        "reveal_personal_emails": bool(reveal_personal),
        "reveal_phone_number": False,
    }
    resp = requests.post(APOLLO_ENRICH_URL, headers=headers(api_key), json=payload, timeout=30)
    if DEBUG_ENRICH:
        print(f"\n--- DEBUG: /people/match by id={person_id} status={resp.status_code} ---")
        try:
            print(json.dumps(resp.json(), indent=2)[:3000])
        except Exception:
            print(resp.text[:1000])
        print("--- /DEBUG ---\n")
    resp.raise_for_status()
    person = (resp.json() or {}).get("person") or None
    if not person:
        return None
    return {
        "name": person.get("name", ""),
        "first_name": person.get("first_name", ""),
        "last_name": person.get("last_name", ""),
        "title": person.get("title", ""),
        "email": extract_work_email_from_person(person),
        "email_status": person.get("email_status", ""),
        "linkedin": person.get("linkedin_url", ""),
        "company": (person.get("organization") or {}).get("name", ""),
    }


def find_people(
    api_key: str,
    domain: str,
    titles: list[str] | None = None,
    seniority: list[str] | None = None,
    limit: int = 10,
    enrich: bool = True,
) -> list[dict]:
    """Search by domain+title, then optionally enrich top matches.

    This is the function callers should use — it implements the only
    Apollo flow that actually returns verified work emails:
        domain  ->  /organizations/enrich  ->  org_id
        org_id  ->  /mixed_people/api_search  ->  person_ids
        person_id  ->  /people/match  ->  email

    enrich=False returns search-only previews (0 credits).
    enrich=True spends 1 credit per result returned (up to `limit`).
    """
    matches = search_people(api_key, domain, titles=titles, seniority=seniority, limit=limit)
    if not enrich:
        return matches
    enriched: list[dict] = []
    for m in matches:
        pid = m.get("id")
        if not pid:
            continue
        try:
            r = enrich_person_by_id(api_key, pid)
            if r:
                r["search_title"] = m.get("title", "")
                enriched.append(r)
            time.sleep(0.4)
        except requests.RequestException as exc:
            print(f"  ! enrich {pid} failed: {exc}", file=sys.stderr)
    return enriched


def print_enrich_result(result: dict | None, name: str, domain: str):
    if not result:
        print(f"No match found for: {name} @ {domain}")
        return
    print(f"\n{'='*70}")
    print(f"  Enrichment: {result['name']}  (credits used)")
    print(f"{'='*70}\n")
    print(f"  Name:     {result['name']}")
    print(f"  Title:    {result['title'] or '(none)'}")
    email_line = result['email'] or '(not found)'
    if result.get('email_status'):
        email_line = f"{email_line}  [{result['email_status']}]"
    print(f"  Email:    {email_line}")
    print(f"  LinkedIn: {result['linkedin'] or '(not found)'}")
    print(f"  Company:  {result['company']}")
    print()

# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

# Use [^\n]+ for line fields — (.+) with DOTALL matches newlines and can swallow the whole file.
ACCOUNT_BLOCK_RE = re.compile(
    r"ACCOUNT NAME:\s*([^\n]+)\n"
    r"Domain:\s*([^\n]+)\n"
    r".*?"
    r"Primary contact:\s*([^\n]+)\n"
    r"Secondary contacts?:\s*([^\n]+)",
    re.DOTALL,
)

def parse_contact_name(contact_line: str) -> tuple[str | None, str | None, str | None]:
    """Extract (first_name, last_name, raw_name) from a contact line.
    Returns (None, None, None) if the contact needs manual lookup or has no name."""
    line = contact_line.strip()
    if "needs manual lookup" in line.lower() or "needs lookup" in line.lower():
        if "—" in line:
            role_hint = line.split("—")[0].strip()
            if any(c.isalpha() for c in role_hint):
                names = role_hint.split(",")[0].strip().split()
                if len(names) >= 2 and not any(w.lower() in ("needs", "ciso", "vp", "head", "director", "senior", "svp") for w in names):
                    return names[0], " ".join(names[1:]), role_hint
        return None, None, None

    clean = re.sub(r"\*\*", "", line)
    clean = re.split(r"\s*[—\-,]\s*", clean)[0].strip()
    clean = re.sub(r"\s*\(.*?\)\s*", "", clean)

    names = clean.split()
    if len(names) < 2:
        return None, None, None

    title_words = {"ciso", "vp", "svp", "head", "director", "senior", "chief", "manager",
                   "officer", "president", "lead", "principal", "global", "regional"}
    if names[0].lower() in title_words:
        return None, None, None

    return names[0], " ".join(names[1:]), clean


def run_batch(api_key: str, filepath: str, update: bool = False):
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")
    blocks = ACCOUNT_BLOCK_RE.findall(content)

    if not blocks:
        print("No account blocks found in", filepath)
        return

    enrichments: list[dict] = []
    credits_used = 0

    print(f"\nFound {len(blocks)} account blocks. Scanning for contacts to enrich...\n")

    for account_name, domain, primary, secondary in blocks:
        account_name = account_name.strip()
        domain = normalize_domain(domain)

        for label, contact_line in [("Primary", primary), ("Secondary", secondary)]:
            first, last, raw = parse_contact_name(contact_line)
            if not first or not last:
                continue
            if "connection established" in contact_line.lower():
                continue

            print(f"  Enriching: {raw} @ {domain} ({label} for {account_name})...", end=" ", flush=True)
            try:
                result = enrich_person(api_key, domain, first, last)
                credits_used += 1
                if result and result.get("email"):
                    print(f"-> {result['email']}")
                    enrichments.append({
                        "account": account_name,
                        "domain": domain,
                        "role": label,
                        "name": result["name"],
                        "title": result["title"],
                        "email": result["email"],
                        "linkedin": result.get("linkedin", ""),
                    })
                else:
                    print("-> (no email found)")
                time.sleep(0.5)
            except requests.RequestException as e:
                print(f"-> ERROR: {e}")

    print(f"\n{'='*70}")
    print(f"  Batch complete: {len(enrichments)} emails found, {credits_used} credits used")
    print(f"{'='*70}\n")

    if enrichments:
        print(f"{'Name':<30} {'Title':<35} {'Email':<35} {'LinkedIn'}")
        print("-" * 140)
        for e in enrichments:
            print(f"{e['name']:<30} {e['title']:<35} {e['email']:<35} {e.get('linkedin', '')}")
        print()

    if update and enrichments:
        updated = content
        for e in enrichments:
            old_patterns = [
                f"{e['name']}.*needs LinkedIn lookup",
                f"{e['name']}.*needs lookup",
                f"{e['name']}.*Needs LinkedIn lookup",
                f"{e['name']}.*Needs lookup",
            ]
            for pat in old_patterns:
                match = re.search(pat, updated, re.IGNORECASE)
                if match:
                    old_line = match.group(0)
                    new_line = f"{e['name']}, {e['title']} — {e['email']}"
                    updated = updated.replace(old_line, new_line, 1)
                    break
        if updated != content:
            path.write_text(updated, encoding="utf-8")
            print(f"Updated {filepath} with enriched contact data.\n")


# ---------------------------------------------------------------------------
# Research markdown (Key People tables)
# ---------------------------------------------------------------------------

def extract_domain_from_research(content: str) -> str | None:
    m = re.search(r"\*\*Domain:\*\*\s*([^\n]+)", content)
    if not m:
        m = re.search(r"(?m)^Domain:\s*([^\n]+)", content)
    if not m:
        m = re.search(r"\|\s*\*\*Domain\*\*\s*\|\s*([^|]+)\|", content)
    if not m:
        return None
    dom = normalize_domain(m.group(1))
    return dom or None


def parse_key_people_rows(content: str) -> list[dict]:
    """Parse ## Key People table rows: name, optional LinkedIn URL (column 5 when present)."""
    rows: list[dict] = []
    if "## Key People" not in content:
        return rows
    sec = content.split("## Key People", 1)[1]
    if "##" in sec:
        sec = sec.split("##", 1)[0]
    for line in sec.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:
            continue
        role = cells[1].lower()
        name = cells[2]
        if not name or name.lower() == "name":
            continue
        if "---" in role or "---" in name:
            continue
        name = re.sub(r"\*+", "", name)
        name = name.split(",")[0].strip()
        nl = name.lower()
        if "unknown" in nl or "needs manual" in nl or "needs lookup" in nl:
            continue
        bad = (
            "/", "team", "leadership", "procurement", "hiring", "managers",
            "finance", "cfo", "cpo",
        )
        if any(b in nl for b in bad):
            continue
        parts_n = name.split()
        if len(parts_n) < 2 or len(parts_n) > 5:
            continue
        linkedin_raw = cells[5].strip() if len(cells) > 5 else ""
        li = normalize_linkedin_url(linkedin_raw)
        rows.append({"name": name, "linkedin_url": li})
    return rows


def run_research_enrich(
    api_key: str,
    root: Path,
    log_path: Path | None,
    already_seen: set[tuple[str, str]] | None = None,
) -> tuple[list[dict], int]:
    seen: set[tuple[str, str]] = set(already_seen) if already_seen else set()
    results: list[dict] = []
    credits = 0
    print(f"\nScanning {root} for Key People tables...\n")
    for md in sorted(root.rglob("*.md")):
        if md.name.startswith(".") or md.name == ".gitkeep":
            continue
        try:
            content = md.read_text(encoding="utf-8")
        except OSError:
            continue
        domain = extract_domain_from_research(content)
        if not domain:
            print(f"  Skip (no Domain line): {md.name}")
            continue
        people_rows = parse_key_people_rows(content)
        if not people_rows:
            continue
        try:
            rel = md.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = md
        for row in people_rows:
            full_name = row["name"]
            li_url = row.get("linkedin_url")
            key = (full_name.lower(), domain.lower())
            if key in seen:
                continue
            seen.add(key)
            parts = full_name.split()
            first, last = parts[0], " ".join(parts[1:])
            li_note = f" +LI" if li_url else ""
            print(f"  {full_name} @ {domain} ({md.name}){li_note}...", end=" ", flush=True)
            try:
                r = enrich_person(api_key, domain, first, last, linkedin_url=li_url)
                credits += 1
                if r and r.get("email"):
                    print(r["email"])
                    results.append(
                        {
                            "name": r.get("name", full_name),
                            "email": r["email"],
                            "title": r.get("title", ""),
                            "domain": domain,
                            "file": str(rel),
                            "linkedin": r.get("linkedin", ""),
                        }
                    )
                else:
                    print("(no email)")
                time.sleep(0.45)
            except requests.RequestException as e:
                print(f"ERROR: {e}")

    if log_path and results:
        lines = [
            "# Apollo enrichment — research files",
            "",
            "| Name | Email | Title | Domain | Source |",
            "|------|-------|-------|--------|--------|",
        ]
        for row in results:
            title = (row["title"] or "").replace("|", "/")
            lines.append(
                f"| {row['name']} | {row['email']} | {title} | {row['domain']} | `{row['file']}` |"
            )
        lines.append("")
        lines.append(f"*(Enrichment calls: {credits}, rows with email: {len(results)})*")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nWrote {log_path}")

    print(f"\nResearch scan: {len(results)} emails resolved, {credits} enrich API calls.\n")
    return results, credits

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Apollo API enrichment — find emails for GTM contacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    sp_search = sub.add_parser("search", help="Search for people at a company (free, no credits)")
    sp_search.add_argument("--domain", required=True, help="Company domain (e.g. cyera.io)")
    sp_search.add_argument("--title", default=None, help="Job title to search for (e.g. CISO)")
    sp_search.add_argument("--seniority", default=None, help="Comma-separated seniority levels (e.g. vp,c_suite,director)")
    sp_search.add_argument("--limit", type=int, default=10, help="Max results (default 10)")

    # enrich
    sp_enrich = sub.add_parser("enrich", help="Enrich a person by name + domain (1 credit)")
    sp_enrich.add_argument("--domain", required=True, help="Company domain")
    sp_enrich.add_argument("--name", required=True, help='Full name (e.g. "Nathan Smolenski")')
    sp_enrich.add_argument("--linkedin", default=None, help="LinkedIn URL (improves match rate)")
    sp_enrich.add_argument(
        "--no-reveal", action="store_true",
        help="Do NOT pass reveal_personal_emails=true (cheaper, but Apollo will return name only).",
    )
    sp_enrich.add_argument("--debug", action="store_true", help="Print raw Apollo response for diagnosis")

    # find — the recommended high-quality flow
    sp_find = sub.add_parser(
        "find",
        help="Find + enrich the right people at a company by title (resolves org_id first)",
    )
    sp_find.add_argument("--domain", required=True, help="Company domain (e.g. playtika.com)")
    sp_find.add_argument(
        "--titles",
        default="CISO,Chief Information Security Officer,VP Security,Head of Security,Head of Trust and Safety,VP Trust and Safety,Chief Safety Officer",
        help="Comma-separated job titles to search for",
    )
    sp_find.add_argument("--seniority", default=None, help="Comma-separated Apollo seniorities (vp,c_suite,director,head)")
    sp_find.add_argument("--limit", type=int, default=5, help="Max people to enrich (each costs 1 credit)")
    sp_find.add_argument("--no-enrich", action="store_true", help="Search only; do not spend credits to reveal emails")
    sp_find.add_argument("--debug", action="store_true", help="Print raw Apollo responses")

    # batch
    sp_batch = sub.add_parser("batch", help="Batch enrich contacts from target-accounts.md")
    sp_batch.add_argument("--file", required=True, help="Path to target-accounts.md")
    sp_batch.add_argument("--update", action="store_true", help="Update the file in place with found emails")

    # research
    sp_res = sub.add_parser(
        "research",
        help="Enrich all named people in ## Key People tables under output/research/",
    )
    sp_res.add_argument("--root", default="output/research", help="Root folder to scan")
    sp_res.add_argument(
        "--log",
        default="output/apollo-enrichment-research.md",
        help="Write markdown summary here (set empty to skip)",
    )

    # all — full project
    sp_all = sub.add_parser(
        "all",
        help="Run batch --update on target-accounts.md, then research scan (deduped per file)",
    )
    sp_all.add_argument("--target", default="output/target-accounts.md")
    sp_all.add_argument("--research-root", default="output/research")
    sp_all.add_argument("--log-research", default="output/apollo-enrichment-research.md")

    args = parser.parse_args()
    api_key = load_api_key()

    if args.command == "search":
        seniority = [s.strip() for s in args.seniority.split(",")] if args.seniority else None
        results = search_people(api_key, args.domain, args.title, seniority, args.limit)
        print_search_results(results, args.domain, args.title)

    elif args.command == "enrich":
        parts = args.name.strip().split()
        if len(parts) < 2:
            print("Error: Provide a full name (first + last)", file=sys.stderr)
            sys.exit(1)
        first, last = parts[0], " ".join(parts[1:])
        global DEBUG_ENRICH
        DEBUG_ENRICH = bool(getattr(args, "debug", False))
        result = enrich_person(
            api_key,
            args.domain,
            first,
            last,
            linkedin_url=getattr(args, "linkedin", None),
            reveal_personal=not getattr(args, "no_reveal", False),
        )
        print_enrich_result(result, args.name, args.domain)

    elif args.command == "find":
        DEBUG_ENRICH = bool(getattr(args, "debug", False))
        titles = [t.strip() for t in args.titles.split(",") if t.strip()]
        seniority = [s.strip() for s in args.seniority.split(",")] if args.seniority else None
        results = find_people(
            api_key,
            args.domain,
            titles=titles,
            seniority=seniority,
            limit=args.limit,
            enrich=not args.no_enrich,
        )
        if not results:
            org = resolve_organization(api_key, args.domain)
            if not org:
                print(f"Apollo has no organization record for {args.domain}.")
            else:
                print(f"No matches in Apollo for {org.get('name')} ({args.domain}) with titles: {titles}")
            return
        print(f"\n{'='*70}")
        print(f"  Find: {args.domain} — {len(results)} record(s)")
        print(f"{'='*70}\n")
        for r in results:
            email = r.get("email") or "(not found)"
            status = f" [{r['email_status']}]" if r.get("email_status") else ""
            print(f"  - {r.get('name','(unknown)')}")
            print(f"      Title:    {r.get('title') or r.get('search_title','(none)')}")
            print(f"      Email:    {email}{status}")
            print(f"      LinkedIn: {r.get('linkedin') or '(none)'}")
            print()

    elif args.command == "batch":
        run_batch(api_key, args.file, update=args.update)

    elif args.command == "research":
        log = Path(args.log) if getattr(args, "log", None) else None
        if log and str(log).strip() == "":
            log = None
        run_research_enrich(api_key, Path(args.root), log)

    elif args.command == "all":
        print("=== Step 1: target-accounts.md ===\n")
        run_batch(api_key, args.target, update=True)
        print("\n=== Step 2: research Key People ===\n")
        lr = Path(args.log_research) if args.log_research else None
        run_research_enrich(api_key, Path(args.research_root), lr)


if __name__ == "__main__":
    main()
