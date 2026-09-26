"""Locate a method's Code attribute and report its constant-pool references.

Self-contained: reads the class file once, keeps the pool, walks fields and
methods, and for the requested method prints every invoke/field/class reference
plus the branch instructions. Used to prove whether a method null-checks its
first argument before dereferencing it.
"""
import struct
import sys
import zipfile


class Reader:
    def __init__(self, b):
        self.b = b
        self.i = 0

    def u1(self):
        v = self.b[self.i]; self.i += 1; return v

    def u2(self):
        v = struct.unpack_from('>H', self.b, self.i)[0]; self.i += 2; return v

    def u4(self):
        v = struct.unpack_from('>I', self.b, self.i)[0]; self.i += 4; return v

    def raw(self, n):
        v = self.b[self.i:self.i + n]; self.i += n; return v

    def skip(self, n):
        self.i += n


def read_pool(r):
    r.u4(); r.u2(); r.u2()
    n = r.u2()
    utf = {}
    cls = {}
    ref = {}
    i = 1
    while i < n:
        t = r.u1()
        if t == 1:
            l = r.u2()
            utf[i] = r.raw(l).decode('utf-8', 'replace')
        elif t == 7:
            cls[i] = r.u2()
        elif t == 8:
            r.u2()
        elif t in (9, 10, 11):
            a = r.u2(); b = r.u2()
            ref[i] = (a, b)
        elif t == 12:
            r.u2(); r.u2()
        elif t == 3:
            r.u4()
        elif t == 4:
            r.u4()
        elif t == 5:
            r.u4(); r.u4(); i += 1
        elif t == 6:
            r.u4(); r.u4(); i += 1
        elif t == 15:
            r.u1(); r.u2()
        elif t == 16:
            r.u2()
        elif t in (17, 18):
            r.u2(); r.u2()
        elif t in (19, 20):
            r.u2()
        else:
            raise ValueError('bad constant pool tag %d at index %d (offset %d)' % (t, i, r.i - 1))
        i += 1
    return utf, cls, ref


def nat_name(utf, ref, idx):
    """resolve a Methodref/Fieldref/InterfaceMethodref entry to owner.name+desc"""
    if idx not in ref:
        return None
    owner_i, nat_i = ref[idx]
    # nat_i is a NameAndType; re-parse from the raw record is not possible here,
    # so callers use the parallel dict built below
    return None


def read_pool_full(r):
    r.u4(); r.u2(); r.u2()
    n = r.u2()
    utf, cls, ref, nat = {}, {}, {}, {}
    i = 1
    while i < n:
        t = r.u1()
        if t == 1:
            l = r.u2(); utf[i] = r.raw(l).decode('utf-8', 'replace')
        elif t == 7:
            cls[i] = r.u2()
        elif t == 8:
            r.u2()
        elif t in (9, 10, 11):
            ref[i] = (r.u2(), r.u2())
        elif t == 12:
            nat[i] = (r.u2(), r.u2())
        elif t in (3, 4):
            r.u4()
        elif t in (5, 6):
            r.u4(); r.u4(); i += 1
        elif t == 15:
            r.u1(); r.u2()
        elif t == 16:
            r.u2()
        elif t in (17, 18):
            r.u2(); r.u2()
        elif t in (19, 20):
            r.u2()
        else:
            raise ValueError('bad constant pool tag %d at index %d' % (t, i))
        i += 1
    return utf, cls, ref, nat


CP_REF_OPS = {
    0x12: 'ldc', 0x13: 'ldc_w', 0x14: 'ldc2_w',
    0xb2: 'getstatic', 0xb3: 'putstatic', 0xb4: 'getfield', 0xb5: 'putfield',
    0xb6: 'invokevirtual', 0xb7: 'invokespecial', 0xb8: 'invokestatic',
    0xb9: 'invokeinterface', 0xba: 'invokedynamic',
    0xbb: 'new', 0xbd: 'anewarray', 0xc0: 'checkcast', 0xc1: 'instanceof',
}
BRANCH_OPS = {0x99: 'ifeq', 0x9a: 'ifne', 0x9b: 'iflt', 0x9c: 'ifge', 0x9d: 'ifgt',
              0x9e: 'ifle', 0x9f: 'if_icmpeq', 0xa0: 'if_icmpne', 0xa1: 'if_icmplt',
              0xa2: 'if_icmpge', 0xa3: 'if_icmpgt', 0xa4: 'if_icmple', 0xa5: 'if_acmpeq',
              0xa6: 'if_acmpne', 0xa7: 'goto', 0xc6: 'ifnull', 0xc7: 'ifnonnull'}
U2_OPS = set(list(CP_REF_OPS) + list(BRANCH_OPS) + [0xa8, 0xa9, 0x84])
U1_OPS = {0x10, 0x15, 0x16, 0x17, 0x18, 0x19, 0x36, 0x37, 0x38, 0x39, 0x3a, 0xbc, 0xa9}


def analyse(code, pool):
    utf, cls, ref, nat = pool
    pc = 0
    refs = []
    branches = []
    n = len(code)
    while pc < n:
        op = code[pc]
        if op in (0xaa, 0xab):
            pad = 3 - (pc % 4)
            p = pc + 1 + pad
            if op == 0xaa:
                lo = struct.unpack_from('>i', code, p + 4)[0]
                hi = struct.unpack_from('>i', code, p + 8)[0]
                pc = p + 12 + 4 * (hi - lo + 1)
            else:
                npairs = struct.unpack_from('>i', code, p + 4)[0]
                pc = p + 8 + 8 * npairs
            continue
        if op in U2_OPS:
            arg = struct.unpack_from('>H', code, pc + 1)[0]
            if op in CP_REF_OPS:
                if arg in ref:
                    owner_i, nt_i = ref[arg]
                    name_i, desc_i = nat.get(nt_i, (None, None))
                    owner = utf.get(cls.get(owner_i, -1), '?')
                    refs.append((pc, CP_REF_OPS[op], '%s.%s%s' % (
                        owner.replace('/', '.'), utf.get(name_i, '?'), utf.get(desc_i, ''))))
                elif arg in cls:
                    refs.append((pc, CP_REF_OPS[op], utf.get(cls[arg], '?')))
            elif op in BRANCH_OPS:
                off = struct.unpack_from('>h', code, pc + 1)[0]
                branches.append((pc, BRANCH_OPS[op], pc + off))
            pc += 3
            continue
        if op in U1_OPS:
            pc += 2
            continue
        if op in (0xc5,):
            pc += 4
            continue
        if op == 0x11:
            pc += 3
            continue
        if op == 0xb9:
            pc += 5
            continue
        if op == 0xba:
            pc += 5
            continue
        if op == 0xc4:
            pc += 4
            continue
        pc += 1
    return refs, branches


def find_code(data, want_name, want_desc=None):
    r = Reader(data)
    pool = read_pool_full(r)
    utf = pool[0]
    r.u2(); r.u2(); r.u2()
    for _ in range(r.u2()):
        r.u2()
    for _ in range(r.u2()):                       # fields
        r.u2(); r.u2(); r.u2()
        for _ in range(r.u2()):
            r.u2(); r.skip(r.u4())
    out = []
    for _ in range(r.u2()):                       # methods
        r.u2()
        name = utf.get(r.u2())
        desc = utf.get(r.u2())
        code = None
        for _ in range(r.u2()):
            an = utf.get(r.u2())
            ln = r.u4()
            start = r.i
            if an == 'Code':
                r.u2(); r.u2()
                clen = r.u4()
                code = r.raw(clen)
            r.i = start + ln
        if name == want_name and (want_desc is None or desc == want_desc):
            out.append((desc, code, pool))
    return out


def main():
    src, cls, method = sys.argv[1], sys.argv[2], sys.argv[3]
    desc = sys.argv[4] if len(sys.argv) > 4 else None
    data = zipfile.ZipFile(src).read(cls) if src.endswith('.jar') else open(src, 'rb').read()
    hits = find_code(data, method, desc)
    print('== %s :: %s.%s%s' % (src.rsplit('\\', 1)[-1], cls, method, desc or ''))
    if not hits:
        print('   METHOD NOT FOUND')
        return 1
    for d, code, pool in hits:
        print('   descriptor: %s' % d)
        if not code:
            print('   no Code attribute')
            continue
        refs, branches = analyse(code, pool)
        print('   code length: %d bytes' % len(code))
        print('   constant-pool refs in execution order:')
        for pc, op, target in refs:
            print('     @%-4d %-15s %s' % (pc, op, target))
        print('   branches:')
        for pc, op, tgt in branches:
            print('     @%-4d %-12s -> %d' % (pc, op, tgt))
        nulls = [(pc, op) for pc, op, t in branches if op in ('ifnull', 'ifnonnull')]
        print('   >>> null-check branches: %s' % (nulls if nulls else 'NONE'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
