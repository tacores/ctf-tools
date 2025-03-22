#!/bin/bash

TARGET="10.10.10.10"
PORTS=(1111 2222 3333 4444)

# すべての順列を生成する関数
permute() {
    local items=("$@")
    local num=${#items[@]}
    
    if (( num == 1 )); then
        echo "${items[0]}"
    else
        for (( i=0; i<num; i++ )); do
            local head="${items[i]}"
            local rest=("${items[@]:0:i}" "${items[@]:i+1}")  # i番目を除いたリストを作る
            while read -r p; do
                echo "$head $p"
            done < <(permute "${rest[@]}")
        done
    fi
}

# すべての順列を試す
while read -r seq; do
    echo "Trying sequence: $seq"
    knock -d 100 "$TARGET" $seq
    sleep 0.2  # ノックの処理が完了するのを待つ
done < <(permute "${PORTS[@]}")
