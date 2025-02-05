import os
import sys
import random

PROGRAMVERSION = "3.2.3"
PROGRAMDATE = "20241209"

def validfname(fn):
    ALLOWED_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
    newname = ''
    for k in fn:
        if k in ALLOWED_CHARACTERS:
            newname += k
        else:
            newname += '_'
    if newname in ('CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'):
        newname += '_'
    return newname

def list2str(l):
    s = ''
    for k in l:
        s += chr(k)
    return s

def list2string(l):
    s = ''
    for k in l:
        if k not in range(32, 128):
            k = 32
        s += chr(k)
    return s

def string2list(s):
    l = []
    for k in s:
        l.append(ord(k))
    return l

def range2list(s):
    l = []
    s = s.split(',')
    for k in s:
        if '-' in k:
            start = max(1, int(k.split('-')[0]))
            end = int(k.split('-')[1]) + 1
            l += range(start, end)
        else:
            l.append(max(1, int(k)))
    return l

def tl2out(tl):
    out = []
    for i in range(80):
        out.append(99-i)
    out += [20, 19, 18, 18, 17, 16, 15, 15, 14, 14,
            13, 13, 12, 12, 11, 11, 10, 10, 9, 9,
            8, 8, 7, 7, 6, 6, 5, 5, 5, 4,
            4, 4, 4, 3, 3, 3, 3, 2, 2, 2,
            2, 1, 1, 1, 1, 0, 0, 0]
    return out[tl]

def out2tl(out):
    tl = [127,122,118,114,110,107,104,102,100,98,96,94,92,90,88,86,85,84,82,81]
    for i in range(20, 100):
        tl.append(99-i)
    return tl[out]

def checksum(data):
    return (128-sum(data)&127)%128

def dxrandom(data, size=128):
    # thanks Renata Dokmanovic
    print ("Randomizing data")
    random.seed()
    n = len(data)//size
    newdata = []
    for v in range(n):
        for p in range(size):
            newdata.append(data[size * random.randrange(n) + p])
    return newdata

def file2names(infile, len=10):
    names = []
    with open(infile, 'r') as f:
        lines = f.readlines()
    for l in lines:
        if l.strip() != '':
            name = l.ljust(10)
            names += string2list(name)
    return names

def nr2note(nr, C3 = 60):
    scl = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
    n = (nr - C3) % 12
    i = (nr - C3) // 12 
    return scl[n] + str(i + 3) 

def closeto(value, table, expo=False):
    if value in table:
        return table.index(value)
    minval = min(table)
    if value < minval:
        return table.index(minval)
    maxval = max(table)
    if value > maxval:
        return table.index(maxval)
    srtable = sorted(table)
    for i in range(len(table) - 1):
        hi = srtable[i+1]
        lo = srtable[i]
        if lo < value < hi:
            if expo:
                center = (hi * lo) ** 0.5
            else:
                center = (hi + lo) / 2.
            if value <= center:
                return table.index(lo)
            elif value > center:
                return table.index(hi)
    return 0

