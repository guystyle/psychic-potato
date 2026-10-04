import json,subprocess,re
W=json.load(open("IMG_7470_m.json"))
words=[(a,b,w.strip()) for s in W for a,b,w in s["w"]]
# (src start, src end)
SEG=[(1.6,11.5),(11.7,29.4),(41.2,59.7),(74.7,79.9),(81.5,85.0),(94.16,95.96),(99.8,106.14)]
PADI,PADO=0.04,0.16
offs=[];t=0
for S,E in SEG:
    d=E-S+PADO+PADI; offs.append((t,S-PADI,d)); t+=d
TOTAL=t
FIX={"유료비":"유류비","푸드티":"후드티","프리스,":"프리스,"}
HI=("영종도","10km","5천원","20km","기름값","유류비","돌이킬","훨씬")
def map_t(x):
    for (o,s,d),(S,E) in zip(offs,SEG):
        if S-0.05<=x<=E+0.1: return o+(x-s)
    return None
caps=[]
for (o,s,d),(S,E) in zip(offs,SEG):
    ws=[(a,b,w.replace("유료비","유류비").replace("푸드티","후드티")) for a,b,w in words if S-0.05<=a<E-0.03 and w]
    grp=[];cur=[]
    for w in ws:
        if cur and len(" ".join(x[2] for x in cur+[w]))>12:
            grp.append(cur);cur=[]
        cur.append(w)
        n=len(" ".join(x[2] for x in cur))
        if re.search(r"[.,?]$",w[2]) and n>=4:
            grp.append(cur);cur=[]
    if S==99.8:
        cur=[];grp=[ws[:2],ws[2:7],ws[7:]]
    if cur:
        if grp and len(" ".join(x[2] for x in cur))<=3: grp[-1]+=cur
        else: grp.append(cur)
    for i,g in enumerate(grp):
        st=o+(max(g[0][0],S)-s)
        nxt=grp[i+1][0][0] if i+1<len(grp) else E+0.1
        en=o+(min(nxt,E+0.1)-s)
        en=max(en,st+0.5); en=min(en,o+d)
        if S==99.8 and i==len(grp)-1: en=TOTAL
        caps.append((st,en,g))
def ts(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60
    return f"{h}:{m:02d}:{s:05.2f}"
def txt(g):
    parts=[]
    for _,_,w in g:
        w2=w.rstrip(".,?")
        if any(h in w for h in HI): parts.append("{\\c&H00D7FF&}"+w2+"{\\c&HFFFFFF&}")
        else: parts.append(w2)
    return " ".join(parts)
hdr="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,WenQuanYi Zen Hei,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,2,2,60,60,520,1
Style: Hook,WenQuanYi Zen Hei,92,&H00101010,&H00101010,&H0000D7FF,&H0000D7FF,-1,0,0,0,100,100,0,0,3,14,0,8,60,60,300,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
ev=[f"Dialogue: 1,{ts(0.0)},{ts(3.2)},Hook,,0,0,0,,{{\\fad(150,200)}}영종도에서 길 한 번 잘못 들면?"]
for st,en,g in caps:
    ev.append(f"Dialogue: 0,{ts(st)},{ts(en)},Cap,,0,0,0,,{{\\fad(40,0)\\fscx88\\fscy88\\t(0,110,\\fscx100\\fscy100)}}{txt(g)}")
open("reel.ass","w").write(hdr+"\n".join(ev)+"\n")
print("total",round(TOTAL,1),"caps",len(caps))
for st,en,g in caps: print(f"{st:6.1f}-{en:6.1f}"," ".join(x[2] for x in g))
# ffmpeg
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:p=bt709,format=yuv420p"
GR="eq=saturation=0.9:contrast=1.1:brightness=-0.02,colorbalance=rs=-0.06:bs=0.06:rm=-0.04:bm=0.04,curves=preset=medium_contrast"
inp=[];fc=[];lab=""
for i,(o,s,d) in enumerate(offs):
    inp+=["-ss",f"{s:.3f}","-t",f"{d:.3f}","-i","IMG_7470.MOV"]
    z=1.0 if i%2==0 else 1.08
    cw=int(2160/z)//2*2; ch=int(3840/z)//2*2
    fc.append(f"[{i}:v]{TM},crop={cw}:{ch},scale=1080:1920:flags=lanczos,{GR},fps=30,setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[{i}:a]aresample=48000,highpass=f=90,afade=t=in:d=0.03,afade=t=out:st={d-0.05:.3f}:d=0.05,asetpts=PTS-STARTPTS[a{i}]")
    lab+=f"[v{i}][a{i}]"
fc.append(f"{lab}concat=n={len(offs)}:v=1:a=1[vc][ac]")
fc.append("[vc]ass=reel.ass[vo]")
fc.append("[ac]acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=9[ao]")
cmd=["ffmpeg","-y","-v","error","-stats"]+inp+["-filter_complex",";".join(fc),"-map","[vo]","-map","[ao]","-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709","-c:a","aac","-b:a","192k","-movflags","+faststart","reel_v1.mp4"]
open("cmd.json","w").write(json.dumps(cmd))
