#! /usr/bin/python3

import sys
import argparse
import string

def is_ascii_printable(s):
    return all(char in string.printable for char in s)

def offset_string(text, offset, split=True):
    if split == True:
        # 1. スペースで分割して単語のリストを作る
        words = text.split()
    else:
        words = [text]

    # 2. リストでループして変換
    transformed_words = []
    for word in words:
        # 各文字にオフセットを適用して新しい単語を作る
        try:
            transformed_word = ''.join(chr(ord(char) + offset) for char in word)
        except ValueError:
            return ""
        transformed_words.append(transformed_word)

    # 3. 変換後の単語リストをスペース区切りで表示
    result = ' '.join(transformed_words)
    return result

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("### Spaces are not offset ###\n    echo 'string' | python test.py <start> <end>")
        print("### Spaces are also offset ###\n    echo 'string' | python test.py <start> <end> -s")
        print()
        print("Example:")
        print("echo 'abc def' | python offset-word.py 1 3")
        print("bcd efg\ncde fgh\ndef ghi")
        print()
        print("echo 'abc def' | python offset-word.py 1 3 -s")
        print("bcd!efg\ncdefgh\ndef#ghi")
        sys.exit(1)

    # 引数を解析
    parser = argparse.ArgumentParser(description="Process a string multiple times.")
    parser.add_argument("start", type=int, help="Start of the range")
    parser.add_argument("end", type=int, help="End of the range")
    parser.add_argument("-s", "--split", action="store_true", help="Enable split mode")
    args = parser.parse_args()
    
    # 標準入力を受け取る
    input_string = sys.stdin.read().strip()
    
    # 指定された回数処理を実行
    for offset in range(args.start, args.end+1):
        output = offset_string(input_string, offset, not args.split)
        # 印字不可能な時は出力しない
        if is_ascii_printable(output) and len(output) > 0:
            print(output)

if __name__ == "__main__":
    main()
