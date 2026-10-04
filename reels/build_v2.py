import json,subprocess,re
WJ={k:[(a,b,w.strip()) for s in json.load(open(f"IMG_{k}_m.json")) for a,b,w in s["w"]] for k in ("7469","7470")}
# (source, start, end)
SEG=[("7469",3.76,5.30),("7469",9.70,10.75),("7469",11.90,14.13),("7469",14.59,18.50),
     ("7470",11.70,29.40),("7470",41.20,59.70),("7470",59.76,64.70),
     ("7470",81.50,85.00),("7470",86.50,89.20),
     ("7469",98.85,104.30),
     ("7470",94.16,95.96),("7470",99.80,106.14)]
PADI,PADO=0.04,0.16
offs=[];t=0
for k,S,E in SEG:
    d=E-S+PADO+PADI; offs.append((t,S-PADI,d)); t+=d
TOTAL=t
REP=[("유료비","유류비"),("푸드티","후드티"),("그분을","그 부분을"),("가이스타일이네요","가이스타일이네요")]
HI=("EDC","스태프","영종도","10km","5천원","20km","기름값","유류비","돌이킬","훨씬","검은")
caps=[]
for idx,((k,S,E),(o,s,d)) in enumerate(zip(SEG,offs)):
    ws=[]
    for a,b,w in WJ[k]:
        if S-0.05<=a<E-0.03 and w:
            for x,y in REP: w=w.replace(x,y)
            ws.append((a,b,w))
    grp=[];cur=[]
    for w in ws:
        if cur and len(" ".join(x[2] for x in cur+[w]))>13:
            grp.append(cur);cur=[]
        cur.append(w)
        n=len(" ".join(x[2] for x in cur))
        if re.search(r"[.,?]$",w[2]) and n>=4: grp.append(cur);cur=[]
    if S==99.8: cur=[];grp=[ws[:2],ws[2:7],ws[7:]]
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
    out=[]
    for _,_,w in g:
        w2=w.rstrip(".,?")
        out.append("{\\c&H00D7FF&}"+w2+"{\\c&HFFFFFF&}" if any(h in w for h in HI) else w2)
    return " ".join(out)
hdr="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,Black Han Sans,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,10,5,2,70,70,470,1
Style: Hook,Black Han Sans,100,&H00101010,&H00101010,&H0000D7FF,&H0000D7FF,0,0,0,0,100,100,0,0,3,18,0,8,70,70,260,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
ev=[f"Dialogue: 1,{ts(0.0)},{ts(3.6)},Hook,,0,0,0,,{{\\fad(150,200)}}EDC 2026 스태프\\N출근길에 생긴 일"]
for st,en,g in caps:
    ev.append(f"Dialogue: 0,{ts(st)},{ts(en)},Cap,,0,0,0,,{{\\fad(40,0)\\fscx88\\fscy88\\t(0,110,\\fscx100\\fscy100)}}{txt(g)}")
open("reel2.ass","w").write(hdr+"\n".join(ev)+"\n")
print("total",round(TOTAL,1),"caps",len(caps))
for st,en,g in caps: print(f"{st:6.1f}-{en:6.1f}"," ".join(x[2] for x in g))
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv:p=bt709,format=yuv420p"
GR="eq=saturation=0.9:contrast=1.1:brightness=-0.02,colorbalance=rs=-0.06:bs=0.06:rm=-0.04:bm=0.04,curves=preset=medium_contrast"
inp=[];fc=[];lab=""
for i,((k,S,E),(o,s,d)) in enumerate(zip(SEG,offs)):
    inp+=["-ss",f"{s:.3f}","-t",f"{d:.3f}","-i",f"IMG_{k}.MOV","-ss",f"{s:.3f}","-t",f"{d:.3f}","-i",f"d_{k}.wav"]
    z=1.0 if i%2==0 else 1.08
    cw=int(2160/z)//2*2; ch=int(3840/z)//2*2
    fc.append(f"[{2*i}:v]{TM},crop={cw}:{ch},scale=1080:1920:flags=lanczos,{GR},fps=30,setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[{2*i+1}:a]aresample=48000,afade=t=in:d=0.03,afade=t=out:st={d-0.05:.3f}:d=0.05,asetpts=PTS-STARTPTS[a{i}]")
    lab+=f"[v{i}][a{i}]"
fc.append(f"{lab}concat=n={len(SEG)}:v=1:a=1[vc][ac]")
fc.append("[vc]ass=reel2.ass:fontsdir=fonts[vo]")
fc.append("[ac]equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=9,aformat=channel_layouts=stereo[ao]")
cmd=["ffmpeg","-y","-v","error","-stats"]+inp+["-filter_complex",";".join(fc),"-map","[vo]","-map","[ao]","-c:v","libx264","-crf","20","-preset","medium","-maxrate","12M","-bufsize","24M","-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709","-c:a","aac","-b:a","192k","-movflags","+faststart","reel_v2.mp4"]
json.dump(cmd,open("cmd2.json","w"))
