"""Original mathematical equivalence check, not a hardware timing test.
SPDX-License-Identifier: 0BSD
Copyright (C) 2026 by I.C.KaZe
"""
P=(1<<17)-1

def fibonacci(s):
    return (s>>1)|(((s^(s>>3))&1)<<16)

def galois(s):
    return (s>>1)^(0x12000 if s&1 else 0)

def apply(columns,s):
    result=0
    for k,c in enumerate(columns):
        if (s>>k)&1: result^=c
    return result

def power_step(s,n):
    columns=[fibonacci(1<<i) for i in range(17)]
    while n:
        if n&1:s=apply(columns,s)
        columns=[apply(columns,c) for c in columns]
        n>>=1
    return s

def main():
    f=1;g=0x4001;x=P^1;history=[1]+[0]*16;bits=[]
    for n in range(P):
        bit=f&1
        assert bit==(g&1)==(1-(x&1))==history[n%17],n
        bits.append(bit)
        history[n%17]=history[n%17]^history[(n+3)%17]
        f=fibonacci(f);g=galois(g)
        x=(x>>1)|((1^((x^(x>>3))&1))<<16)
    assert (f,g,x)==(1,0x4001,P^1)
    # Reconstruct the Fibonacci state from future output bits of Galois form.
    for seed in [1,8,0x12345,0x1ffff]:
        g=seed;s=0
        for i in range(17):s|=(g&1)<<i;g=galois(g)
        g=seed
        for i in range(1000):
            assert (s&1)==(g&1)
            s=fibonacci(s);g=galois(g)
    for n in [0,1,16,256,65536,P,P+17,1000000]:
        expected=1
        for _ in range(n%P):expected=fibonacci(expected)
        assert power_step(1,n)==expected
    assert len(bits)==P and sum(bits)==65536
    print('PASS: 131071 output bits: Fibonacci, Galois, complemented XNOR, ring recurrence; matrix jumps; mapped seeds')
if __name__=='__main__':main()
