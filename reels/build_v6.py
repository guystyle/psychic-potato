import json,subprocess,re
WJ={"7469":[(a,b,w.strip()) for s in json.load(open("IMG_7469_d.json")) for a,b,w in s["w"]],
    "7470":[(a,b,w.strip()) for s in json.load(open("IMG_7470_m.json")) for a,b,w in s["w"]]}
SEG=[("7469",1.46,5.10),("7469",9.71,10.65),("7469",12.05,14.13),("7469",14.57,18.50),("7469",19.23,27.30),("7469",28.72,35.30),
     ("7469",48.32,71.66),("7469",74.64,78.02),
     ("7470",11.70,29.40),("7470",41.20,59.70),
     ("7470",59.76,64.70),("7470",81.50,85.00),("7470",86.50,89.20),("7469",97.30,106.40),("7470",94.16,95.96),("7470",99.80,106.14),("7469",116.52,118.04)]

import sys
PARTS=[(0,6,"EDC 2026 스태프\\N2일차 출근길 (1/4)","2편에서 계속"),
       (6,8,"EDC 가는 길에 본\\N영종도 아침 풍경 (2/4)","3편에서 계속"),
       (8,10,"길도 잃고 연락도\\N못 받은 출근길 (3/4)","4편에서 계속"),
       (10,17,"받는 돈에 비해\\N기름값을 너무 썼다 (4/4)",None)]
PADI,PADO=0.04,0.16
REP=[("유료비","유류비"),("푸드티","후드티"),("보여드리셨으면","보여드렸으면"),("하늘도","하늘도시"),("수축은","쪽은"),("심도시가","신도시가"),("활차다는","활기차다는")]
HI=("EDC","1일차","하늘도시","촬영","스태프","영종도","10km","5천원","20km","기름값","유류비","돌이킬","훨씬","검은")
def ts(x):
    h=int(x//3600);m=int(x%3600//60);sc=x%60
    return f"{h}:{m:02d}:{sc:05.2f}"
def txt(g):
    out=[]
    for _,_,w in g:
        w2=w.rstrip(".,?")
        out.append("{\\c&H00D7FF&}"+w2+"{\\c&HFFFFFF&}" if any(h in w for h in HI) else w2)
    return " ".join(out)
HDR=open("reel2.ass").read().split("[Events]")[0]+"[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:p=bt709,format=yuv420p"
GR="eq=saturation=0.9:contrast=1.1:brightness=-0.02,colorbalance=rs=-0.06:bs=0.06:rm=-0.04:bm=0.04,curves=preset=medium_contrast"

import re as _re
_t=open("ys.txt").read()
YS=[(float(a),float(b)) for a,b in _re.findall(r"pts_time:([\d.]+).*?\n.*?YAVG=([\d.]+)",_t,flags=_re.S)]
def lift_filters(src_start,dur):
    """returns (pre, darks): pre = lifts for dim parts (before crop); darks = [(a,b)] near-black parts (t local to segment)."""
    pts=[(a-src_start,b) for a,b in YS if src_start-0.3<=a<=src_start+dur+0.3]
    cls=[(t,"dark" if v<15 else "dim" if v<90 else "ok") for t,v in pts]
    runs=[]
    for i,(t,c) in enumerate(cls):
        e=cls[i+1][0] if i+1<len(cls) else dur
        if runs and runs[-1][2]==c: runs[-1][1]=e
        else: runs.append([t,e,c])
    pre=[];darks=[]
    for a,b,c in runs:
        a=max(a,0);b=min(b,dur)
        if b<=a or c=="ok": continue
        if c=="dark": darks.append((a,b))
        else: pre.append(f"eq=gamma=1.5:contrast=1.05:enable='between(t,{a:.2f},{b:.2f})'")
    return ("hqdn3d=4:3:5:4," if pre else "")+(",".join(pre)+"," if pre else ""), darks
def dark_chain(darks):
    if not darks: return "",GR
    inn="+".join(f"between(t,{a:.2f},{b:.2f})" for a,b in darks)
    en=f"enable='{inn}'"; nen=f"enable='not({inn})'"
    gr=("eq=saturation=0.9:contrast=1.1:brightness=-0.02:%s,colorbalance=rs=-0.06:bs=0.06:rm=-0.04:bm=0.04:%s,curves=preset=medium_contrast:%s")%(nen,nen,nen)
    dk=(",hqdn3d=6:5:8:6:%s,curves=all='0/0 0.015/0.22 0.05/0.42 0.18/0.70 0.5/0.90 1/1':%s,"
        "eq=saturation=0.55:contrast=1.08:%s,colorbalance=rs=-0.15:rm=-0.15:rh=-0.06:bs=0.05:bm=0.05:%s")%(en,en,en,en)
    return dk,gr

cmds=[]
for pi,(a,b,title,teaser) in enumerate(PARTS,1):
    seg=SEG[a:b]; offs=[];t=0
    for k,S,E in seg:
        d=E-S+PADO+PADI; offs.append((t,S-PADI,d)); t+=d
    TOTAL=t; caps=[]
    for (k,S,E),(o,st0,d) in zip(seg,offs):
        ws=[]
        for x,y,w in WJ[k]:
            if S-0.05<=x<E-0.03 and w:
                for p,q in REP: w=w.replace(p,q)
                ws.append((x,y,w))
        grp=[];cur=[]
        for w in ws:
            if cur and len(" ".join(z[2] for z in cur+[w]))>13: grp.append(cur);cur=[]
            cur.append(w)
            n=len(" ".join(z[2] for z in cur))
            if re.search(r"[.,?]$",w[2]) and n>=4: grp.append(cur);cur=[]
        if S==99.8: cur=[];grp=[ws[:2],ws[2:7],ws[7:]]
        if cur:
            if grp and len(" ".join(z[2] for z in cur))<=3: grp[-1]+=cur
            else: grp.append(cur)
        for i,g in enumerate(grp):
            st=o+(max(g[0][0],S)-st0)
            nxt=grp[i+1][0][0] if i+1<len(grp) else E+0.1
            en=o+(min(nxt,E+0.1)-st0)
            en=max(en,st+0.5); en=min(en,o+d)
            if S==99.8 and i==len(grp)-1: en=o+d
            caps.append((st,en,g))
    ev=[f"Dialogue: 1,{ts(0.0)},{ts(3.4)},Hook,,0,0,0,,{{\\fad(150,200)}}{title}"]
    if teaser: ev.append(f"Dialogue: 1,{ts(TOTAL-1.9)},{ts(TOTAL)},Hook,,0,0,0,,{{\\fad(150,0)}}{teaser}")
    for st,en,g in caps:
        ev.append(f"Dialogue: 0,{ts(st)},{ts(en)},Cap,,0,0,0,,{{\\fad(40,0)\\fscx88\\fscy88\\t(0,110,\\fscx100\\fscy100)}}{txt(g)}")
    open(f"p{pi}.ass","w").write(HDR+"\n".join(ev)+"\n")
    print("part",pi,"len",round(TOTAL,1))
    for st,en,g in caps: print(f"  {st:5.1f}-{en:5.1f}"," ".join(z[2] for z in g))
    inp=[];fc=[];lab=""
    for i,((k,S,E),(o,st0,d)) in enumerate(zip(seg,offs)):
        inp+=["-ss",f"{st0:.3f}","-t",f"{d:.3f}","-i",f"IMG_{k}.MOV","-ss",f"{st0:.3f}","-t",f"{d:.3f}","-i",f"d_{k}.wav"]
        z=1.0 if i%2==0 else 1.08
        cw=int(2160/z)//2*2; ch=int(3840/z)//2*2
        LF,DK_=lift_filters(st0,d) if k=="7469" else ("",[])
        DKC,GRx=dark_chain(DK_)
        fc.append(f"[{2*i}:v]{TM},{LF}crop={cw}:{ch},scale=1080:1920:flags=lanczos,{GRx}{DKC},fps=30,setpts=PTS-STARTPTS[v{i}]")
        fc.append(f"[{2*i+1}:a]aresample=48000,afade=t=in:d=0.03,afade=t=out:st={d-0.05:.3f}:d=0.05,asetpts=PTS-STARTPTS[a{i}]")
        lab+=f"[v{i}][a{i}]"
    fc.append(f"{lab}concat=n={len(seg)}:v=1:a=1[vc][ac]")
    fc.append(f"[vc]ass=p{pi}.ass:fontsdir=fonts[vo]")
    fc.append("[ac]equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=9,aformat=channel_layouts=stereo[ao]")
    cmds.append(["ffmpeg","-y","-v","error","-stats"]+inp+["-filter_complex",";".join(fc),"-map","[vo]","-map","[ao]","-c:v","libx264","-crf","21","-preset","medium","-maxrate","8M","-bufsize","16M","-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709","-c:a","aac","-b:a","160k","-movflags","+faststart",f"reel_v6_part{pi}.mp4"])
json.dump(cmds,open("cmd6.json","w"))
