"""Render a four-page, source-linked factual report with native vector charts."""
import argparse
from html import escape
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

NAMES={'UK Total':'英国合计','England':'英格兰','Scotland':'苏格兰','Wales':'威尔士','Northern Ireland':'北爱尔兰'}


def render(evidence, style, out):
    pdfmetrics.registerFont(UnicodeCIDFont(style['font']))
    font=style['font']; width,height=A4
    c=canvas.Canvas(str(out/'report.pdf'),pagesize=A4,invariant=1)
    c.setTitle(f"英国区域电力分析 {evidence['year']}")
    audit=[]; page=0; notes=[]
    def text(x,y,value,size=10,color='ink'):
        value=str(value); w=pdfmetrics.stringWidth(value,font,size)
        if x<30 or x+w>width-29 or y<28 or y+size>height-25:
            raise ValueError(f'Text exceeds page bounds: {value}')
        c.setFillColor(HexColor(style[color]));c.setFont(font,size);c.drawString(x,y,value)
        audit.append(dict(page=page,kind='text',text=value,bbox=[x,y,w,size]))
    def para(y,value,size=11):
        obj=Paragraph(escape(value),ParagraphStyle('body',fontName=font,fontSize=size,leading=size*1.65,
                      textColor=HexColor(style['ink']),wordWrap='CJK'))
        w,h=obj.wrap(width-88,650)
        if y-h<58:raise ValueError('Paragraph overflow')
        obj.drawOn(c,44,y-h)
        audit.append(dict(page=page,kind='paragraph',text=value,bbox=[44,y-h,w,h]))
        notes.append(value)
        return y-h-14
    def start(title,subtitle):
        nonlocal page
        if page:c.showPage()
        page+=1
        text(44,height-38,'PROJECT REPORT WORKBENCH  /  UK ELECTRICITY',8,'accent')
        text(44,height-80,title,23)
        para(height-100,subtitle,10)
        c.setStrokeColor(HexColor(style['renewables']));c.line(44,45,width-44,45)
        text(44,31,f"DESNZ 官方数据 | {evidence['year']} 年度 | 事实模板试运行稿",8)
        text(width-62,31,str(page),9)
    def table(y,headers,rows,widths):
        x=44
        c.setFillColor(HexColor(style['background']));c.rect(x,y-8,sum(widths),26,fill=1,stroke=0)
        for label,w in zip(headers,widths):text(x+5,y,label,9);x+=w
        y-=33
        for row in rows:
            x=44
            for value,w in zip(row,widths):
                if pdfmetrics.stringWidth(str(value),font,10)>w-10:
                    raise ValueError('Table cell exceeds column capacity')
                text(x+5,y,value,10);x+=w
            c.setStrokeColor(HexColor(style['background']));c.line(44,y-10,width-44,y-10)
            y-=32
        return y-8
    def bars(rows,y,mode):
        colors=['fossil','nuclear','renewables','residual']
        maxval=max(sum(v) for _,v in rows) if mode=='TWh' else 100
        for label,values in rows:
            text(44,y+4,label,10)
            x=117
            for key,value in zip(colors,values):
                w=value/maxval*350
                c.setFillColor(HexColor(style[key]));c.rect(x,y,w,18,stroke=0,fill=1);x+=w
            text(478,y+4,f'{sum(values):.1f}',9)
            y-=42
        c.setStrokeColor(HexColor(style['residual']));c.line(117,y+23,467,y+23)
        for fraction in [0,0.25,0.5,0.75,1]:
            text(117+350*fraction,y+10,f'{maxval*fraction:.0f}',8)
        y-=15
        x=44
        for key,label in zip(colors,['化石燃料','核能','可再生','其他及储能']):
            c.setFillColor(HexColor(style[key]));c.rect(x,y,9,9,stroke=0,fill=1)
            text(x+14,y,label,9);x+=122
        return y-30
    metrics=evidence['metrics'];uk=metrics[0];year=evidence['year']
    start(f'{year} 年英国区域电力分析','同一发布版本计算同比；历史版本修订单列。单位：TWh（1 TWh = 1,000 GWh）。')
    text(44,675,f"{uk['current_gwh']['total']/1000:.2f} TWh",30)
    text(330,681,f"同比 {uk['growth_pct']['total']:+.2f}%",19)
    y=para(641,f"低碳发电占比为 {uk['shares_pct']['low_carbon']:.2f}%，其中可再生能源占 {uk['shares_pct']['renewables']:.2f}%。占比由本期发电量重新计算，不直接拼接跨版本百分比。")
    rows=[[NAMES[r['region']],f"{r['current_gwh']['total']/1000:.2f}",f"{r['growth_pct']['total']:+.2f}%",f"{r['shares_pct']['low_carbon']:.2f}%"] for r in metrics]
    y=table(y-15,['地区','发电量 TWh','同比','低碳占比'],rows,[133,115,115,144])
    changes=sorted(metrics[1:],key=lambda r:r['delta_gwh'])
    y=para(y,f"区域变化：{NAMES[changes[0]['region']]}的发电量变动为 {changes[0]['delta_gwh']/1000:+.2f} TWh；{NAMES[changes[-1]['region']]}为 {changes[-1]['delta_gwh']/1000:+.2f} TWh。地区按绝对变动排序，不将占比变化等同于发电量增长。")
    para(y,'阅读范围：发电量、能源结构与地区差异。电力贸易、消费、排放和政策原因不在本次生成范围内；不将相关变化表述为因果关系。')
    start('趋势与能源结构','沿用参考报告的蓝色分类体系；补充“其他及储能”，避免堆叠图漏掉剩余发电量。')
    rows=[]
    for r in evidence['trend']:
        v=r['values'];rows.append((str(r['year']),[v['fossil']/1000,v['nuclear']/1000,v['renewables']/1000,
                                                  (v['total']-v['fossil']-v['nuclear']-v['renewables'])/1000]))
    text(44,682,'英国近五年发电量（TWh）',13)
    y=bars(rows,640,'TWh')
    y=para(y,f"本期化石燃料发电同比 {uk['growth_pct']['fossil']:+.2f}%，核能同比 {uk['growth_pct']['nuclear']:+.2f}%，可再生能源同比 {uk['growth_pct']['renewables']:+.2f}%。这些是统计变化，不包含价格、天气或设备运行原因的推断。")
    rows=[[name,f"{uk['current_gwh'][key]/1000:.2f}",f"{uk['shares_pct'][key]:.2f}%"] for key,name in [('fossil','化石燃料'),('nuclear','核能'),('renewables','可再生能源')]]
    rows.append(['其他及储能',f"{uk['residual_gwh']/1000:.2f}",f"{uk['residual_gwh']/uk['current_gwh']['total']*100:.2f}%"])
    table(y-12,['英国能源类别','发电量 TWh','占总发电量'],rows,[190,150,167])
    start('区域结构与历史修订','地区之间按相同口径比较；同一年在两次发布中的不同数值作为修订差异展示。')
    rows=[]
    for r in metrics[1:]:
        shares=r['shares_pct'];rows.append((NAMES[r['region']],[shares[k] for k in ['fossil','nuclear','renewables']]+[100-sum(shares[k] for k in ['fossil','nuclear','renewables'])]))
    text(44,682,'本期地区能源结构（%）',13)
    y=bars(rows,640,'%')
    rev=evidence['revisions']; yr=rev[0]['year']
    y=para(y,f'{yr} 年发电量的版本修订核对（TWh）；新一期同比统一采用新版基期，不能用旧报告中的数值直接相减。')
    rows=[[NAMES[r['region']],f"{r['old_gwh']/1000:.3f}",f"{r['revised_gwh']/1000:.3f}",f"{r['gap_gwh']/1000:+.3f}"] for r in rev]
    y=table(y-8,['地区','旧版','本版重述','修订差额'],rows,[133,115,115,144])
    para(y,'建议核查动作：优先核对修订幅度较大的地区及口径变化。在取得设备、价格或天气证据之前，保留对变化原因的判断。',10)
    start('证据与适用边界','本报告由版本化脚本和事实模板生成。表格、正文与图表引用同一份计算结果。')
    y=680
    y=para(y,'数据来源：英国能源安全与净零部门（DESNZ），Energy Trends 区域电力统计配套 Excel。原始单位 GWh；结果按展示精度四舍五入。',11)
    y=para(y,'证据账本随报告交付：evidence.json 保存当前与基期数值、Excel 单元格、指标定义及结论 ID；quality.json 保存计算检查，acceptance.json 保存文件检查。',11)
    for claim in evidence['claims']:
        r=next(r for r in metrics if r['region']==claim['metric_region'])
        y=para(y,f"{claim['claim_id']}  {NAMES[r['region']]}：发电量 {r['current_gwh']['total']/1000:.2f} TWh；来源 {r['source_cells']['total']}；基期 {r['previous_cells']['total']}。",9)
    for limitation in ['低碳 = 核能 + 可再生能源；储能和其他燃料不自动归入低碳。','原材料是汇总表；早期跨表冲突排除出五年分析范围，详见质量记录。', '使用期内跨表差异超过 0.001 GWh 会披露；本案例仅容许不超过 0.01 GWh 的小额差异。','事实模板未调用模型，不包含完整分析师式因果研究或预测。','搜索阶段已见两期部分摘要，本次属于跨期重放，不是严格盲测。','自动检查通过不能替代逐页视觉复核；人工业务评审仍待完成。']:
        y=para(y,limitation,10)
    c.save()
    (out/'layout.json').write_text(json.dumps(dict(pages=page,width=width,height=height,objects=audit),ensure_ascii=False,indent=2))
    (out/'report.md').write_text(f'# {year} 年英国区域电力分析\n\n'+'\n\n'.join(notes)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',required=True);p.add_argument('--style',required=True);p.add_argument('--out-dir',required=True)
    a=p.parse_args();render(json.loads(Path(a.evidence).read_text()),json.loads(Path(a.style).read_text()),Path(a.out_dir))
