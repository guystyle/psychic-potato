import json,subprocess,re
WJ={k:[(a,b,w.strip()) for s in json.load(open(f"IMG_{k}_m.json")) for a,b,w in s["w"]] for k in ("7469","7470")}
# (source, start, end)
SEG=[("7469",3.76,5.30),("7469",9.70,10.75),("7469",11.90,14.13),("7469",14.59,18.50),
     ("7470",11.70,29.40),("7470",41.20,59.70),("7470",59.76,64.70),
     ("7470",81.50,85.00),("7470",86.50,89.20),
     ("7469",98.85,104.30),
     ("7470",94.16,95.96),("7470",99.80,106.14)]

import sys
PARTS=[(0,5,"EDC 2026 스태프\\N출근길에 생긴 일 (1/3)","2편에서 계속"),
       (5,7,"나만 못 받은\\N검은 옷 연락 (2/3)","3편에서 계속"),
       (7,12,"기름값이 더\\N걱정인 출근길 (3/3)",None)]
PADI,PADO=0.04,0.16
REP=[("유료비","유류비"),("푸드티","후드티"),("그분을","그 부분을")]
HI=("EDC","스태프","영종도","10km","5천원","20km","기름값","유류비","돌이킬","훨씬","검은")
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
            if S==99.8 and i==len(grp)-1: en=TOTAL
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
        fc.append(f"[{2*i}:v]{TM},crop={cw}:{ch},scale=1080:1920:flags=lanczos,{GR},fps=30,setpts=PTS-STARTPTS[v{i}]")
        fc.append(f"[{2*i+1}:a]aresample=48000,afade=t=in:d=0.03,afade=t=out:st={d-0.05:.3f}:d=0.05,asetpts=PTS-STARTPTS[a{i}]")
        lab+=f"[v{i}][a{i}]"
    fc.append(f"{lab}concat=n={len(seg)}:v=1:a=1[vc][ac]")
    fc.append(f"[vc]ass=p{pi}.ass:fontsdir=fonts[vo]")
    fc.append("[ac]equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=9,aformat=channel_layouts=stereo[ao]")
    cmds.append(["ffmpeg","-y","-v","error","-stats"]+inp+["-filter_complex",";".join(fc),"-map","[vo]","-map","[ao]","-c:v","libx264","-crf","21","-preset","medium","-maxrate","8M","-bufsize","16M","-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709","-c:a","aac","-b:a","160k","-movflags","+faststart",f"reel_v3_part{pi}.mp4"])
json.dump(cmds,open("cmd3.json","w"))
