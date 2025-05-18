#!/usr/bin/python3
from gmpy2 import isqrt
from math import lcm
from Crypto.PublicKey import RSA
import gmpy2

# id_rsa.pub から id_rsa を生成する。
# 通常は時間がかかりすぎて使えるものではないが、p と q が非常に近く、
# ユークリッドアルゴリズムで高速に素因数分解できる場合に限り使える。

def factorize(n):
    if (n & 1) == 0:
        return (n/2, 2)

    a = isqrt(n)

    if a * a == n:
        return a, a

    while True:
        a = a + 1
        bsq = a * a - n
        b = isqrt(bsq)
        if b * b == bsq:
            break

    return a + b, a - b


encoded_key = open("id_rsa.pub", "rb").read()
rsakey = RSA.import_key(encoded_key)

n = rsakey.n
e = rsakey.e

(p, q) = factorize(n)

phi = (p - 1) * (q - 1)
d = gmpy2.invert(e, phi)

private_key = RSA.construct((int(n), int(e), int(d), int(p), int(q)))

with open("id_rsa", "wb") as f:
    f.write(private_key.export_key('PEM'))
