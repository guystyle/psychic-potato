from PIL import ImageFont
FONT=ImageFont.truetype("fonts/BlackHanSans-Regular.ttf",136)
SIZE,SX=136,68
CY="&HFFE500&"   # cyan (BGR) = #00E5FF
def width(t): return FONT.getlength(t)*SX/100
def wrap2(words,maxw=800):
    """1 line if it fits, else the most balanced 2-line split that fits; None if 3 lines would be needed"""
    full=" ".join(words)
    if width(full)<=maxw: return [full]
    best=None
    for k in range(1,len(words)):
        a=" ".join(words[:k]); b=" ".join(words[k:])
        m=max(width(a),width(b))
        if m<=maxw and (best is None or m<best[0]): best=(m,[a,b])
    return best[1] if best else None
def shape(x1,y1,x2,y2): return f"m {x1:.0f} {y1:.0f} l {x2:.0f} {y1:.0f} {x2:.0f} {y2:.0f} {x1:.0f} {y2:.0f}"
def box_events(st,en,lines,hl,cx=540,bottom=1450,padx=34,pady=26,accent=CY):
    """returns ASS Dialogue lines: translucent fill + cyan selection border + corner handles + text"""
    n=len(lines); w=max(width(l) for l in lines)+2*padx; h=n*SIZE*1.0+2*pady
    x1,x2=cx-w/2,cx+w/2; y2=bottom; y1=bottom-h
    a=lambda s,e,txt,l=1:f"Dialogue: {l},{s},{e},Cap,,0,0,0,,{txt}"
    ev=[]
    ev.append(a(st,en,"{\\an7\\pos(0,0)\\fscx100\\fscy100\\p1\\1c&H000000&\\1a&H8C&\\3c"+accent+"\\3a&H00&\\bord4\\shad0}"+shape(x1,y1,x2,y2)+"{\\p0}",1))
    for hx,hy in ((x1,y1),(x2,y1),(x2,y2),(x1,y2)):
        ev.append(a(st,en,"{\\an7\\pos(0,0)\\fscx100\\fscy100\\p1\\1c&HFFFFFF&\\1a&H00&\\3c"+accent+"\\bord3\\shad0}"+shape(hx-11,hy-11,hx+11,hy+11)+"{\\p0}",2))
    ty=y1+h/2+14
    ev.append(a(st,en,"{\\an5\\pos(%d,%d)}"%(cx,ty)+"\\N".join(hl(l) for l in lines),3))
    return ev
def plain_events(st,en,lines,hl,cx=540,bottom=1450):
    n=len(lines); h=n*SIZE
    return [f"Dialogue: 3,{st},{en},Cap,,0,0,0,,{{\\an5\\pos({cx},{bottom-h/2-10:.0f})}}"+"\\N".join(hl(l) for l in lines)]

def title_events(st,en,lines,mode="solid",cx=540,top=240,padx=40,pady=22,fade="\\fad(150,200)"):
    """unified title block. mode: 'solid' = one cyan rectangle + dark text; 'select' = cyan selection box + white text"""
    n=len(lines); w=max(width(l) for l in lines)+2*padx; h=n*SIZE+2*pady
    x1,x2=cx-w/2,cx+w/2; y1=top; y2=top+h
    D="{\\an7\\pos(0,0)\\fscx100\\fscy100"+fade+"\\p1"
    a=lambda txt,l:f"Dialogue: {l},{st},{en},Cap,,0,0,0,,{txt}"
    ev=[]
    ty=y1+h/2+14
    if mode=="solid":
        ev.append(a(D+"\\1c"+CY+"\\1a&H00&\\bord0\\shad0}"+shape(x1,y1,x2,y2)+"{\\p0}",1))
        ev.append(a("{\\an5\\pos(%d,%d)%s\\1c&H101010&\\bord0\\shad0}"%(cx,ty,fade)+"\\N".join(lines),3))
    else:
        ev.append(a(D+"\\1c&H000000&\\1a&H8C&\\3c"+CY+"\\3a&H00&\\bord4\\shad0}"+shape(x1,y1,x2,y2)+"{\\p0}",1))
        for hx,hy in ((x1,y1),(x2,y1),(x2,y2),(x1,y2)):
            ev.append(a(D+"\\1c&HFFFFFF&\\1a&H00&\\3c"+CY+"\\bord3\\shad0}"+shape(hx-11,hy-11,hx+11,hy+11)+"{\\p0}",2))
        ev.append(a("{\\an5\\pos(%d,%d)%s}"%(cx,ty,fade)+"\\N".join(lines),3))
    return ev
