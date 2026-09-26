import struct


class R:
    def __init__(s, b):
        s.b = b
        s.i = 0

    def u1(s):
        v = s.b[s.i]
        s.i += 1
        return v

    def u2(s):
        v = struct.unpack_from('>H', s.b, s.i)[0]
        s.i += 2
        return v

    def u4(s):
        v = struct.unpack_from('>I', s.b, s.i)[0]
        s.i += 4
        return v

    def raw(s, n):
        v = s.b[s.i:s.i + n]
        s.i += n
        return v


def _parse(data):
    r = R(data)
    if r.u4() != 0xCAFEBABE:
        raise ValueError('not a class file')
    r.u2()
    r.u2()
    n = r.u2()
    utf = {}
    i = 1
    while i < n:
        t = r.u1()
        if t == 1:
            l = r.u2()
            utf[i] = r.raw(l).decode('utf-8', 'replace')
        elif t in (7, 8, 16, 19, 20):
            r.u2()
        elif t == 15:
            r.u1()
            r.u2()
        elif t in (3, 4, 9, 10, 11, 12, 17, 18):
            r.u4()
        elif t in (5, 6):
            r.u4()
            r.u4()
            i += 1
        else:
            raise ValueError('bad cp tag %d' % t)
        i += 1
    r.u2()
    r.u2()
    r.u2()
    for _ in range(r.u2()):
        r.u2()
    for _ in range(r.u2()):
        r.u2()
        r.u2()
        r.u2()
        for _ in range(r.u2()):
            r.u2()
            ln = r.u4()
            r.raw(ln)
    out = []
    for _ in range(r.u2()):
        r.u2()
        ni = r.u2()
        di = r.u2()
        for _ in range(r.u2()):
            r.u2()
            ln = r.u4()
            r.raw(ln)
        out.append((utf.get(ni), utf.get(di)))
    return out


def methods_from_bytes(data):
    return _parse(data)


def methods(path):
    with open(path, 'rb') as f:
        return _parse(f.read())
