import json,re,subprocess,sys
sys.path.insert(0,".")
from boxcap import *
WJ={"7469":[(a,b,w.strip()) for s in json.load(open("IMG_7469_d.json")) for a,b,w in s["w"]],
    "7470":[(a,b,w.strip()) for s in json.load(open("IMG_7470_m.json")) for a,b,w in s["w"]]}
SEG=[("7469",12.05,14.13),("7469",14.57,18.50),
     ("7470",41.20,50.30),("7470",50.50,58.40),("7470",59.76,64.70),
     ("7470",81.50,85.00),
     ("7470",94.16,95.96),("7470",99.80,106.14),
     ("7469",116.52,118.04)]
PADI,PADO=0.04,0.16
REP=[("유료비","유류비"),("푸드티","후드티")]
HIK=("EDC","스태프","검은","다이소","5천원","20km","유류비","돌이킬","훨씬")
def ts(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60
    return f"{h}:{m:02d}:{s:05.2f}"
def hl(line):
    return " ".join(("{\\c"+CY+"}"+w+"{\\c&HFFFFFF&}") if any(k in w for k in HIK) else w for w in line.split(" "))
_t=open("ys.txt").read()
YS=[(float(a),float(b)) for a,b in re.findall(r"pts_time:([\d.]+).*?\n.*?YAVG=([\d.]+)",_t,flags=re.S)]
def runs_for(src_start,dur):
    pts=[(a-src_start,b) for a,b in YS if src_start-0.3<=a<=src_start+dur+0.3]
    cls=[(t,"dark" if v<15 else "dim" if v<90 else "ok") for t,v in pts]
    runs=[]
    for i,(t,c) in enumerate(cls):
        e=cls[i+1][0] if i+1<len(cls) else dur
        if runs and runs[-1][2]==c: runs[-1][1]=e
        else: runs.append([t,e,c])
    dim=[];dark=[]
    for a,b,c in runs:
        a=max(a,0);b=min(b,dur)
        if b>a and c=="dim": dim.append((a,b))
        if b>a and c=="dark": dark.append((a,b))
    return dim,dark
# timeline
offs=[];t=0
for k,S,E in SEG:
    d=E-S+PADO+PADI; offs.append((t,S-PADI,d)); t+=d
TOTAL=t
# captions
caps=[]
for (k,S,E),(o,s0,d) in zip(SEG,offs):
    ws=[]
    for a,b,w in WJ[k]:
        if S-0.05<=a<E-0.03 and w:
            for p,q in REP: w=w.replace(p,q)
            ws.append((a,b,w))
    grp=[];cur=[]
    for w in ws:
        trial=cur+[w]
        if cur and (wrap2([x[2] for x in trial]) is None or len(" ".join(x[2] for x in trial))>13):
            grp.append(cur);cur=[]
        cur.append(w)
        if re.search(r"[.,?]$",w[2]) and len(" ".join(x[2] for x in cur))>=4: grp.append(cur);cur=[]
    if S==99.8: cur=[];grp=[ws[:2],ws[2:7],ws[7:]]
    if cur:
        if grp and len(" ".join(x[2] for x in cur))<=3: grp[-1]+=cur
        else: grp.append(cur)
    for i,g in enumerate(grp):
        st=o+(max(g[0][0],S)-s0)
        nxt=grp[i+1][0][0] if i+1<len(grp) else E+0.1
        en=o+(min(nxt,E+0.1)-s0)
        en=max(en,st+0.5); en=min(en,o+d)
        lines=wrap2([x[2].rstrip(".,?") if False else x[2] for x in g])
        caps.append((st,en,[l.rstrip(".,?") for l in lines]))
hdr=open("ti_cyan.ass").read().split("[Events]")[0]+"[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
ev=[f"Dialogue: 1,{ts(0)},{ts(3.4)},Hook,,0,0,0,,{{\\fad(150,200)}}EDC 스태프 출근길\\N나만 못 받은 연락",
]
for st,en,lines in caps: ev+=box_events(ts(st),ts(en),lines,hl)
open("hero.ass","w").write(hdr+"\n".join(ev)+"\n")
print("total",round(TOTAL,1),"caps",len(caps))
for st,en,l in caps: print(f"{st:5.1f}-{en:5.1f}"," / ".join(l))
# video
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:p=bt709,format=yuv420p"
def teal(dark):
    nen="" if not dark else ":enable='not(%s)'"%"+".join(f"between(t,{a:.2f},{b:.2f})" for a,b in dark)
    g=("eq=saturation=1.08:contrast=1.14:brightness=-0.02%s,colorbalance=rs=-0.18:gs=0.06:bs=0.14:rm=-0.12:gm=0.05:bm=0.10:rh=0.03:gh=0.0:bh=-0.02%s,"
       "curves=all='0/0.02 0.25/0.19 0.5/0.48 0.78/0.78 1/0.94'%s,vignette=angle=PI/5:mode=backward")%(nen,nen,nen)
    if not dark: return g
    en="enable='%s'"%"+".join(f"between(t,{a:.2f},{b:.2f})" for a,b in dark)
    dk=(",hqdn3d=6:5:8:6:%s,curves=all='0/0 0.015/0.22 0.05/0.42 0.18/0.70 0.5/0.90 1/1':%s,eq=saturation=0.55:contrast=1.08:%s,"
        "colorbalance=rs=-0.15:rm=-0.15:rh=-0.06:bs=0.05:bm=0.05:%s")%(en,en,en,en)
    return g+dk
inp=[];fc=[];lab=""
for i,((k,S,E),(o,s0,d)) in enumerate(zip(SEG,offs)):
    inp+=["-ss",f"{s0:.3f}","-t",f"{d:.3f}","-i",f"IMG_{k}.MOV","-ss",f"{s0:.3f}","-t",f"{d:.3f}","-i",f"d_{k}.wav"]
    z=1.0 if i%2==0 else 1.08
    cw=int(2160/z)//2*2; ch=int(3840/z)//2*2
    dim,dark=(runs_for(s0,d) if k=="7469" else ([],[]))
    pre=("hqdn3d=4:3:5:4,"+",".join(f"eq=gamma=1.5:contrast=1.05:enable='between(t,{a:.2f},{b:.2f})'" for a,b in dim)+",") if dim else ""
    fc.append(f"[{2*i}:v]{TM},{pre}crop={cw}:{ch},scale=1080:1920:flags=lanczos,{teal(dark)},fps=30,setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[{2*i+1}:a]aresample=48000,afade=t=in:d=0.03,afade=t=out:st={d-0.05:.3f}:d=0.05,asetpts=PTS-STARTPTS[a{i}]")
    lab+=f"[v{i}][a{i}]"
fc.append(f"{lab}concat=n={len(SEG)}:v=1:a=1[vc][ac]")
fc.append("[vc]ass=hero.ass:fontsdir=fonts[vo]")
fc.append("[ac]equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=9,aformat=channel_layouts=stereo[ao]")
cmd=["ffmpeg","-y","-v","error","-stats"]+inp+["-filter_complex",";".join(fc),"-map","[vo]","-map","[ao]","-c:v","libx264","-crf","21","-preset","medium","-maxrate","8M","-bufsize","16M","-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709","-c:a","aac","-b:a","160k","-movflags","+faststart","reel_hero.mp4"]
json.dump(cmd,open("cmd_hero.json","w"))
