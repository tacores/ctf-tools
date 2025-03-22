# ctf-tools
Catch The Flag 用に作った、あったら便利なツール群

## デコード

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

### HEX→ASCII変換（hex2str.py）

16進数値の文字列を、2桁ずつASCII文字と解釈してASCII文字列に変換する。

```shell
$ python ./hex2str.py 414243
ABC
```

### Vigenere暗号のキー検索

暗号化文字列と元の文字列が分かっている場合に、キーを割り出すスクリプト。  
文字数が1対1であり、アルファベット文字のみ暗号化されるため、元の文字列を部分的に推測しやすい。  
文字列とワードファイルをスクリプト内の変数で指定する。

```shell
python ./vigenere_findkey.py
```

## 攻撃スクリプト

### One Time Password 攻撃（otp_attack.py）
多要素認証の4桁のワンタイムパスワードを攻撃するスクリプト。  
サイトの仕様に合わせてコードをカスタマイズする必要がある。
```shell
python ./otp_attack.py
```

### ポートノッキング

ポート番号のリストを与えたら、全順番の組み合わせでポートノッキングする。  
IPアドレスとポート番号のリストを、シェルファイル内で設定する。  
ポートの順番が分かっている場合は、knockコマンドをそのまま使うべき。

```shell
./port_knock.sh
```
