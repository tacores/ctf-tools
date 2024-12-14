# ctf-tools
Catch The Flag 用に作った、あったら便利なツール群

### モールス信号 (morse.py)
モールス信号を復号する
```shell
$ echo "... --- ..." | python morse.py
SOS
```

### 文字列オフセット (offset_word.py)
ASCII文字列の各文字をオフセットする。  
オフセット後に印字不可能文字が含まれる場合は出力しない。
```shell
# スペースはオフセットしない（デフォルト）
$ echo 'abc def' | python offset-word.py 1 3
bcd efg
cde fgh
def ghi

# スペースもオフセットする
$ echo 'abc def' | python offset-word.py 1 3 -s
bcd!efg
cdefgh
def#ghi
```
