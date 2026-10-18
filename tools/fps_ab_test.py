"""Two builds, the same play, frame by frame: are the screens the same?
For checking that an optimisation changes nothing that can be seen.
  python fps_ab_test.py <reference fps.bin> [<new fps.bin>]
If <reference>.vars (the same name, .vars for .bin) is there - the
fps_vars.inc of that build - it is used for the reference's variables."""
import os
import sys
ref = sys.argv[1]
new = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'fps.bin')
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H, fps_testlib as T
def load_vars(path):
    v={}
    for l in open(path):
        if l.startswith('v_'):
            n,_,x=l.split(); v[n[2:]]=int(x.rstrip('h'),16)
    return v
VNEW=dict(T.V)
_rv=os.path.splitext(ref)[0]+'.vars'
VREF=load_vars(_rv) if os.path.exists(_rv) else VNEW
SCRIPT=([0]*6+[H.K_SPACE,0]*3+[0]*4+[H.K_RIGHT]*5+[H.K_UP]*8+[H.K_LEFT]*3+[H.K_SHIFT,0]+[H.K_SPACE,0]*4+[H.K_UP]*10+[0]*6)
def run(binpath, enemies, vv):
    global V, E
    T.V.clear(); T.V.update(vv); V=T.V; E=V['enemies']
    p6=H.P6(open(binpath,'rb').read()); m=p6.mem
    H.fps_start(p6)
    g=T.Game.__new__(T.Game); g.p6=p6; g.m=m
    g.frame(0,3); m[V['god']]=1
    cells,_,_=T.level(0); ox,oy=T.find_open(cells,5,3)
    f0=len(p6.flips)+1; orig=p6.inp; done=[False]
    def setup():
        g.setw('px',(ox+0.5)*256); g.setw('py',(oy+1.5)*256); m[V['pa']]=0
        if enemies:
            for i in range(24): m[E+i*16]=0
            for i,(ty,d,hp) in enumerate(((1,3.5,3),(2,4.4,4),(7,2.0,0))):
                x,y=int((ox+0.5+d)*256),int((oy+1.5+0.6*i)*256); b=E+i*16
                m[b],m[b+1],m[b+2],m[b+3],m[b+4],m[b+5],m[b+6]=ty,x&255,x>>8,y&255,y>>8,hp,(1 if ty<6 else 0)
    def inp(port):
        if port&0xFF==0x90 and not p6.keyq_active:
            i=len(p6.flips)-f0
            if i==0 and not done[0]: done[0]=True; setup()    # at a fixed point: frame 0's keys
            return SCRIPT[i] if 0<=i<len(SCRIPT) else 0
        return orig(port)
    p6.m.set_input_callback(inp)
    g.frame(0)
    shots=[]
    for k in SCRIPT:
        g.frame(k); shots.append(bytes(m[0x8000:0x10000]))
    return shots
ok=True
for en in (False,True):
    a=run(ref,en,VREF); b=run(new,en,VNEW)
    d=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    ok&=not d
    print(('OK   ' if not d else 'FAIL ')+('enemies ahead' if en else 'walking about'), '(%d frames; different: %s)'%(len(a),d[:5]))
print('ALL OK' if ok else 'SOME FAILED')
