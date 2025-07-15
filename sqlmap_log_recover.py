import re
from collections import defaultdict

# sqlmap の bool ベースのリクエストログから、流出した情報を復元するスクリプト。

# 前提
# pcapをもとに、tsvとして入力ファイルを用意。
# 6列目がデータ長。初期実装では、262をfalse、425をtrueとしている。
# 7列目は Stream Index。これにより要求と応答を１対１に対応させる。WireSharkではデフォルトで表示されていないので、列追加する。
# 8列目がリクエストで、URLデコード済とする。

# TSV例
# 51236	981.505736564	172.16.175.128	10.10.195.62	HTTP	440	6237	GET /search_app/search.php?query=1 AND ORD(MID((SELECT IFNULL(CAST(`name` AS NCHAR),0x20) FROM profile_db.`profiles` ORDER BY id LIMIT 6,1),2,1))>96 HTTP/1.1 
# 51239	981.506562579	172.16.175.128	10.10.195.62	HTTP	440	6236	GET /search_app/search.php?query=1 AND ORD(MID((SELECT IFNULL(CAST(`name` AS NCHAR),0x20) FROM profile_db.`profiles` ORDER BY id LIMIT 6,1),3,1))>96 HTTP/1.1 
# 51241	981.506693414	172.16.175.128	10.10.195.62	HTTP	440	6239	GET /search_app/search.php?query=1 AND ORD(MID((SELECT IFNULL(CAST(`name` AS NCHAR),0x20) FROM profile_db.`profiles` ORDER BY id LIMIT 6,1),5,1))>96 HTTP/1.1 
# 51244	981.508200149	172.16.175.128	10.10.195.62	HTTP	440	6238	GET /search_app/search.php?query=1 AND ORD(MID((SELECT IFNULL(CAST(`name` AS NCHAR),0x20) FROM profile_db.`profiles` ORDER BY id LIMIT 6,1),1,1))>96 HTTP/1.1 
# 51246	981.509149541	172.16.175.128	10.10.195.62	HTTP	441	6240	GET /search_app/search.php?query=1 AND ORD(MID((SELECT IFNULL(CAST(`name` AS NCHAR),0x20) FROM profile_db.`profiles` ORDER BY id LIMIT 6,1),4,1))>112 HTTP/1.1 
# 51249	981.843375832	10.10.195.62	172.16.175.128	HTTP	425	6237	HTTP/1.1 200 OK  (text/html)
# 51253	981.845382993	10.10.195.62	172.16.175.128	HTTP	425	6239	HTTP/1.1 200 OK  (text/html)
# 51255	981.845662581	10.10.195.62	172.16.175.128	HTTP	425	6236	HTTP/1.1 200 OK  (text/html)
# 51261	981.847989163	10.10.195.62	172.16.175.128	HTTP	262	6240	HTTP/1.1 200 OK  (text/html)
# 51264	981.848220209	10.10.195.62	172.16.175.128	HTTP	425	6238	HTTP/1.1 200 OK  (text/html)

# 応答長からの判定基準
TRUE_LENGTH = 425
FALSE_LENGTH = 262

# 入力ファイル
input_file = 'sqlmap_bool_log.tsv'

# リクエスト/レスポンスマップ
requests = {}
responses = {}

# レコード -> カラム -> 文字位置 -> 比較結果の格納
# 例: data[6]['name'][1] = [(96, True), (112, False)]
data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

# --- データ読み込み ---
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        cols = line.strip().split('\t')
        if len(cols) < 8:
            continue
        length = int(cols[5])
        stream = cols[6]
        content = cols[7]

        if content.startswith("GET"):
            requests[stream] = content
        else:
            responses[stream] = (length == TRUE_LENGTH)

# --- リクエストとレスポンスを結合して解析 ---
pattern = re.compile(
    r"CAST\(`(?P<column>\w+)` AS NCHAR\).*?LIMIT (?P<row>\d+),1\),\s*"
    r"(?P<pos>\d+),\s*1\)\)\s*>\s*(?P<threshold>\d+)"
)

for stream, request in requests.items():
    if stream not in responses:
        continue

    m = pattern.search(request)
    if not m:
        continue

    column = m.group("column")
    row = int(m.group("row"))
    pos = int(m.group("pos"))
    threshold = int(m.group("threshold"))
    result = responses[stream]

    data[row][column][pos].append((threshold, result))

# --- ASCII復元 ---
def infer_ascii(thresholds):
    min_val = 0
    max_val = 127
    for t, res in thresholds:
        if res:
            min_val = max(min_val, t + 1)
        else:
            max_val = min(max_val, t)
    return chr(min_val) if min_val <= max_val else '?'

# --- レコードごとに出力 ---
for row in sorted(data.keys()):
    print(f"\n[Row {row}]")
    for column in sorted(data[row].keys()):
        chars = []
        for pos in sorted(data[row][column].keys()):
            thresholds = data[row][column][pos]
            char = infer_ascii(thresholds)
            chars.append(char)
        value = ''.join(chars).rstrip()
        print(f"  {column}: {value}")
