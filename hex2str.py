import sys

def hex_to_ascii_string(ascii_str):
    # 入力文字列が2桁の倍数でなければエラー
    if len(ascii_str) % 2 != 0:
        raise ValueError("Input must have an even number of characters (e.g., 414243).")
    
    # 2桁ずつ分割してASCIIコードを文字に変換
    chars = [chr(int(ascii_str[i:i+2], 16)) for i in range(0, len(ascii_str), 2)]
    return ''.join(chars)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <hex_string>")
        sys.exit(1)

    ascii_string = sys.argv[1]
    try:
        result = hex_to_ascii_string(ascii_string)
        print(result)
    except ValueError as e:
        print(f"Error: {e}")
