import sys,re,difflib,collections
def load(p):
    L=[l.strip() for l in open(p) if not l.startswith('constantPool') and not l.strip().startswith('constantPool')]
    return L
a=load(sys.argv[1]); b=load(sys.argv[2])
sk=lambda l: re.sub(r"'(?:[^'\\]|\\.)*'|\"[^\"]*\"",'S',l)
sm=difflib.SequenceMatcher(None,[sk(x) for x in a],[sk(x) for x in b],autojunk=False)
m=collections.defaultdict(collections.Counter)
tok=re.compile(r"'((?:[^'\\]|\\.)*)'|\"([^\"]*)\"")
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': continue
    for x,y in zip(a[i1:i2],b[j1:j2]):
        ta=[p or q for p,q in tok.findall(x)]; tb=[p or q for p,q in tok.findall(y)]
        for u,v in zip(ta,tb): m[u][v]+=1
for k in sorted(m): print(repr(k),'->',repr(m[k].most_common(1)[0][0]), '' if len(m[k])==1 else m[k])
