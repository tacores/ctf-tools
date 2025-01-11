def vigenere_decrypt(ciphertext, key):
    """Vigenère暗号を復号する"""
    decrypted = []
    key_length = len(key)
    
    for i, char in enumerate(ciphertext):
        if char.isalpha():  # アルファベットのみ処理
            shift = ord(key[i % key_length].lower()) - ord('a')
            if char.islower():
                decrypted.append(chr((ord(char) - shift - ord('a')) % 26 + ord('a')))
            else:
                decrypted.append(chr((ord(char) - shift - ord('A')) % 26 + ord('A')))
        else:
            decrypted.append(char)  # 非アルファベット文字はそのまま保持
    
    return ''.join(decrypted)

def find_matching_key_from_list(ciphertext, expected, key_list_file):
    """キーが羅列されたリストファイルを使用して一致するキーを探す"""
    try:
        with open(key_list_file, 'r', encoding='latin-1') as file:
            keys = file.read().splitlines()  # ファイル内の各行をキーとして扱う
            for key in keys:
                if not key.strip():
                    continue  # 空行をスキップ
                decrypted_text = vigenere_decrypt(ciphertext, key.strip())
                if decrypted_text == expected:
                    return key.strip()
    except Exception as e:
        print(f"Error reading key list file: {e}")
    return None

if __name__ == "__main__":
    # 暗号文、期待する文字列、キーが羅列されたリストファイル
    ciphertext = "MYKAHODTQ"
    expected_text = "TRYHACKME"
    key_list_file = "/usr/share/wordlists/rockyou.txt"  # キーリストが格納されたファイル

    # 復号処理
    matching_key = find_matching_key_from_list(ciphertext, expected_text, key_list_file)
    if matching_key:
        print(f"Match found!\nKey: {matching_key}")
    else:
        print("No matching key found.")
