"""Small bounded PDF drawing primitives for the electricity report."""
from html import escape
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import json

def safe_text(value: str) -> str:
    return str(value).replace('·',' / ').replace('−','-').replace('–','-').replace('©','(c)')


COLORS=['#082653','#6466D9','#B6BDE5','#3C82AD','#21958D','#9DA3AE','#AC748B']
NAMES={'UK Total':'英国合计','England':'英格兰','Scotland':'苏格兰','Wales':'威尔士','Northern Ireland':'北爱尔兰'}


class Report:
    def __init__(self, out: Path, year: int, style: dict):
        self.out=out;self.year=year;self.style=style;self.page=0;self.y=0;self.objects=[];self.notes=[]
        self.width,self.height=A4;self.font=style['font']
        pdfmetrics.registerFont(UnicodeCIDFont(self.font))
        self.c=canvas.Canvas(str(out/'report.pdf'),pagesize=A4,invariant=1)
        self.c.setTitle(f'{year} 英国区域电力：全主题对照候选报告')

    def text(self,x:float,y:float,text:str,size:float=10,color:str='#14233B') -> None:
        text=safe_text(text);w=pdfmetrics.stringWidth(text,self.font,size)
        if x<30 or x+w>self.width-29 or y<25 or y+size>self.height-20:raise ValueError('Text exceeds page bounds: '+text)
        self.c.setFillColor(HexColor(color));self.c.setFont(self.font,size);self.c.drawString(x,y,text)
        self.objects.append(dict(page=self.page,kind='text',text=text,bbox=[x,y,max(w,.1),size]))

    def start(self,title:str,source:str) -> None:
        if self.page:self.c.showPage()
        self.page+=1
        self.text(40,805,'PROJECT REPORT WORKBENCH / UK ELECTRICITY',8,self.style['accent'])
        self.text(40,768,title,21);self.y=735
        self.text(40,31,f'{self.year} 年度 · 全主题对照候选稿 · 非官方发布',8)
        self.text(525,31,str(self.page),9)
        self.c.setStrokeColor(HexColor('#CBD1E7'));self.c.line(40,48,555,48)
        self.notes.append('\n## '+title)
        self.para(source,9,'#53637B')

    def para(self,text:str,size:float=10.5,color:str='#14233B') -> None:
        text=safe_text(text)
        obj=Paragraph(escape(text),ParagraphStyle('body',fontName=self.font,fontSize=size,leading=size*1.65,textColor=HexColor(color),wordWrap='CJK'))
        w,h=obj.wrap(515,700)
        if self.y-h<65:raise ValueError('Paragraph overflow page '+str(self.page))
        obj.drawOn(self.c,40,self.y-h)
        self.objects.append(dict(page=self.page,kind='paragraph',text=text,bbox=[40,self.y-h,w,h]))
        self.notes.append(text);self.y-=h+12

    def table(self,headers:list,rows:list,widths:list=None,size:float=9) -> None:
        widths=widths or [515/len(headers)]*len(headers)
        self.c.setFillColor(HexColor('#EDF0F9'));self.c.rect(40,self.y-20,515,24,fill=1,stroke=0)
        for n,row in enumerate([headers]+rows):
            x=40
            for value,w in zip(row,widths):
                if pdfmetrics.stringWidth(str(value),self.font,size)>w-8:raise ValueError('Table cell exceeds capacity '+str(value))
                self.text(x+4,self.y-12,str(value),size);x+=w
            self.notes.append(' | '.join(map(str,row)))
            self.y-=25
        self.y-=12

    def stacked(self,rows:list,labels:list,colors:list=None,row_height:float=22) -> None:
        colors=colors or COLORS
        maximum=max(sum(max(0,v) for v in vals) for _,vals in rows)
        if maximum<=0:raise ValueError('Chart maximum must be positive')
        for label,vals in rows:
            self.text(40,self.y-12,label,8);x=150
            for i,v in enumerate(vals):
                if v<0:
                    if i!=len(vals)-1:raise ValueError('Negative physical generation')
                    self.c.setFillColor(HexColor('#B74436'));self.c.rect(150+v/maximum*340,self.y-16,-v/maximum*340,13,fill=1,stroke=0)
                    continue
                w=v/maximum*340
                self.c.setFillColor(HexColor(colors[i]));self.c.rect(x,self.y-16,w,13,fill=1,stroke=0);x+=w
            self.text(499,self.y-12,f'{sum(vals):.1f}',8)
            self.y-=row_height
        self.c.setStrokeColor(HexColor('#A9AFBC'));self.c.line(150,self.y,490,self.y)
        for f in [0,.25,.5,.75,1]:self.text(150+340*f,self.y-13,f'{maximum*f:.0f}',8)
        self.y-=35
        x=40
        for i,label in enumerate(labels):
            if x>490:x=40;self.y-=20
            self.c.setFillColor(HexColor(colors[i]));self.c.rect(x,self.y,8,8,fill=1,stroke=0)
            self.text(x+12,self.y,label,8);x+=86
        self.y-=28

    def lines(self,series:dict,years:list,height:float=190,metric_id:str='unspecified') -> None:
        top=self.y;bottom=top-height
        self.objects.append(dict(page=self.page,kind="line_chart",metric_id=metric_id,series=series,years=years,bbox=[65,bottom,405,height]))
        for tick in [0,25,50,75,100]:
            yy=bottom+height*tick/100;self.text(40,yy-3,str(tick),8)
            self.c.setStrokeColor(HexColor('#E3E7EE'));self.c.line(65,yy,470,yy)
        for j,(name,vals) in enumerate(series.items()):
            self.c.setStrokeColor(HexColor(COLORS[j]));self.c.setLineWidth(1.6)
            coords=[(65+i*100,bottom+height*v/100) for i,v in enumerate(vals)]
            for a,b in zip(coords,coords[1:]):self.c.line(*a,*b)
            for x,y in coords:self.c.circle(x,y,2,fill=0,stroke=1)
        for i,y in enumerate(years):self.text(57+i*100,bottom-16,str(y),8)
        self.y=bottom-38
        for i,name in enumerate(series):self.text(40+i*102,self.y,name,8,COLORS[i])
        self.y-=27;self.c.setLineWidth(1)

    def link(self,label:str,url:str) -> None:
        self.text(40,self.y-8,label,8,'#315CB0')
        self.c.linkURL(url,(40,self.y-12,550,self.y+4),relative=0)
        self.y-=24

    def save(self) -> None:
        self.c.save()
        (self.out/'layout.json').write_text(json.dumps(dict(pages=self.page,width=self.width,height=self.height,objects=self.objects),ensure_ascii=False,indent=2))
        (self.out/'report.md').write_text('\n\n'.join(self.notes))
