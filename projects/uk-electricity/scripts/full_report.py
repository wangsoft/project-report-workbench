"""Render all reference topics with recomputed facts and separately labelled external context."""
import argparse
import json
import re
from pathlib import Path
from report_canvas import Report,NAMES,COLORS
from report_semantics import build as build_semantics
from pypdf import PdfReader, PdfWriter

FUEL_NAMES={'coal':'煤','oil':'油','gas':'天然气','nuclear':'核能','renewables':'可再生',
            'fossil':'化石燃料','wind':'风电','solar':'光伏','bioenergy':'生物能源',
            'hydro':'天然水电','tidal':'波浪潮汐','other':'其他燃料','pumped':'抽蓄','battery':'电池储能'}


def fmt(value: float, digits: int=2, signed: bool=False) -> str:
    if value is None:return '不适用'
    if round(value,digits)==0:value=0
    return f'{value:+.{digits}f}' if signed else f'{value:.{digits}f}'


def render(e:dict,style:dict,out:Path,map_path:Path,coverage:dict) -> None:
    if coverage['reference_year']!=e['year']:raise ValueError('Coverage contract year mismatch; review new-period scope')
    r=Report(out,e['year'],style);year=e['year'];years=list(range(year-4,year+1))
    regions=['England','Scotland','Wales','Northern Ireland'];uk=e['metrics'][0]
    fuels={(v['year'],v['region']):v['values'] for v in e['fuel_detail']}
    fm={(v['region'],v['fuel']):v for v in e['fuel_metrics']}
    sm={v['region']:v for v in e['supply_metrics']}
    semantics=build_semantics(e)
    context=e['context'];context_by_id={item['id']:item for item in context['items']};delayed=context.get('evaluation_mode')=='target_reference_delayed_reveal'
    def heading(title,source):
        if delayed:
            source=re.sub(r'（官方[^）]*）|对应官方第[^。·]*[。·]?','',source).replace('全主题覆盖重建','预设主题回测')
            source=source.replace('重建 Chart','预设 Chart')
        r.start(title,source)
    def trade_label(value):return ('净进口' if value>=0 else '净出口')+f' {abs(value)/1000:.2f} TWh'
    def drivers_text():
        names={'fossil':'化石燃料','nuclear':'核能','renewables':'可再生','residual':'其他及储能'}
        ranks=sorted(e['drivers'],key=lambda d:abs(d['delta_gwh']),reverse=True)
        a,b=ranks[:2]
        return f"变化贡献：{names[a['key']]} {a['delta_gwh']/1000:+.2f} TWh（对总发电同比贡献 {a['growth_contribution_pp']:+.2f} pp），{names[b['key']]} {b['delta_gwh']/1000:+.2f} TWh。这是可加的统计分解，不是因果归因。"
    def broad(v):return [v['fossil']/1000,v['nuclear']/1000,v['renewables']/1000,(v['total']-v['fossil']-v['nuclear']-v['renewables'])/1000]
    def detailed(v):return [v['coal']/1000,v['gas']/1000,v['nuclear']/1000,v['renewables']/1000,(v['total']-v['coal']-v['gas']-v['nuclear']-v['renewables'])/1000]
    heading(f'{year} 年英国区域电力分析','摘要 · 全主题覆盖重建；对应官方第 1 页。数据：区域电力 Excel，同一发布版本计算同比。')
    r.para(f"英国发电 {uk['current_gwh']['total']/1000:.2f} TWh，同比 {uk['growth_pct']['total']:+.2f}%；低碳占比 {uk['shares_pct']['low_carbon']:.2f}%，可再生占比 {uk['shares_pct']['renewables']:.2f}%。",15)
    r.para(f"对欧洲{trade_label(sm['UK Total']['net_imports'])}；英国公布的终端消费 {sm['UK Total']['values']['consumption']/1000:.2f} TWh，同比 {sm['UK Total']['consumption_growth']:+.2f}%。需求、消费和国内发电不是同一口径。")
    r.table(['地区','发电 TWh','同比 %','低碳 %'],[[NAMES[m['region']],fmt(m['current_gwh']['total']/1000),fmt(m['growth_pct']['total'],signed=True),fmt(m['shares_pct']['low_carbon'])] for m in e['metrics']])
    r.para(drivers_text())
    r.para(semantics['answers']['renewable_record']+' '+semantics['answers']['regional_nuclear'],11)
    r.para(f"贸易由上年的{trade_label(e['previous_net_imports'])}变为本期{trade_label(sm['UK Total']['net_imports'])}。"+context['items'][1]['text'],10)
    r.para(f"源表核对记录 {len(e['source_issues'])} 项差异，详见审计附件。数据、解释和结论边界分别保留。",9,'#526275')
    r.para('阅读顺序：区域趋势 → 供需与贸易 → 燃料和低碳 → 地区结构 → 可再生技术 → 外部背景 → 修订与来源。电站地图为外部图件，有独立日期，不由汇总 Excel 推算。',10)
    heading('区域发电：五年趋势','重建 Chart 1（官方第 2 页）· 所有发电企业；TWh。灰色为总量减三大类后的余项；若为负值，按红色源表差额表示，不能解释成储能产出。')
    r.stacked([(NAMES[g]+' '+str(y),broad(fuels[y,g])) for g in regions for y in years],['化石燃料','核能','可再生','其他储能'],[COLORS[1],COLORS[0],COLORS[2],COLORS[5]],20)
    r.table(['地区','英国份额 %','较上年变化 pp'],[[NAMES[g],fmt(fuels[year,g]['total']/fuels[year,'UK Total']['total']*100),fmt((fuels[year,g]['total']/fuels[year,'UK Total']['total']-fuels[year-1,g]['total']/fuels[year-1,'UK Total']['total'])*100,signed=True)] for g in regions],size=9)
    heading('供给与消费：地区角色','Chart 2 / 供给定义为发电减厂用及抽蓄用电，尚未扣跨境输电和输配损失；与发电总量区分。')
    r.table(['地区','供给 TWh','消费 TWh','供给占比 %','消费占比 %'],[[NAMES[g],fmt(semantics['charts']['supply_share']['net_gwh'][g]/1000),fmt(sm[g]['values']['consumption']/1000),fmt(semantics['charts']['supply_share']['values'][g]),fmt(sm[g]['consumption_share'])] for g in regions],size=9)
    share_sum=sum(sm[g]['consumption_share'] for g in regions)
    r.para(f'消费占比均按公布的英国消费总量为分母，合计为 {share_sum:.2f}%。未对原始份额做额外归一化；是否配平以原始数值核对为准。',11,'#9B4D20')
    r.table(['年份','英国消费 TWh','区域合计 TWh','差额 TWh'],[[str(y),fmt(next(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']=='UK Total')/1000),fmt(sum(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']!='UK Total')/1000),fmt(sum(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']!='UK Total')/1000-next(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']=='UK Total')/1000,signed=True)] for y in years])
    surplus=[NAMES[g] for g in regions if semantics['charts']['supply_share']['net_gwh'][g]>sm[g]['values']['consumption']]
    r.para('本地净供给高于所列消费的地区：'+'、'.join(surplus)+'。净供给与消费的差额仍包含输配损失，不能直接替代跨境输电。')
    r.para(context['items'][0]['text']+f" [X01，DUKES PDF 第 {context['items'][0]['page']} 页]")
    heading('跨境贸易与区域电力流向','重建国际贸易主题与 Appendix A（官方第 3、10 页）· 净流量 GWh / TWh；线路归属不等于完整物理潮流。')
    edges=[('苏格兰 → 英格兰',sm['Scotland']['values']['to_england']),('苏格兰 → 北爱尔兰',sm['Scotland']['values']['to_ni']),('英格兰 → 威尔士',-sm['Wales']['values']['to_england']),('欧洲 → 英格兰',-sm['England']['values']['to_europe']),('威尔士 → 欧洲',sm['Wales']['values']['to_europe']),('北爱尔兰 → 欧洲',sm['Northern Ireland']['values']['to_europe'])]
    r.table(['净流向（负值代表反向）','TWh'],[[a,fmt(v/1000)] for a,v in edges],[360,155])
    r.para('以下用流量台账重建桑基图的数量关系；存在平衡差额时不绘制暗示守恒的闭合宽带图。平衡消费 = 发电 − 厂用/储能用电 − 国内净输出 − 欧洲净输出 − 输配损失。',10)
    r.table(['地区','按流量推算消费','公布消费','残差 TWh'],[[NAMES[g],fmt(sm[g]['balance_consumption']/1000),fmt(sm[g]['values']['consumption']/1000),fmt(sm[g]['balance_residual']/1000,signed=True)] for g in ['UK Total']+regions],size=9)
    r.para(f"英国对欧洲{trade_label(sm['UK Total']['net_imports'])}；贸易符号已经统一为进口正、出口负。净额不能反推出总进口和总出口，后者引用独立 DUKES 资料。",10)
    heading('燃料转换与长期记录','对应官方第 2–4 页 · 煤、油、气、核能与可再生。历史记录只在燃料表 2004 年起的公布序列内比较。')
    keys=['coal','oil','gas','nuclear','renewables','fossil']
    r.table(['类别','TWh','同比 %','五年变化 %','占比变化 pp'],[[FUEL_NAMES[k],fmt(fm['UK Total',k]['gwh']/1000),fmt(fm['UK Total',k]['growth'],signed=True),fmt(fm['UK Total',k]['five_year_growth'],signed=True),fmt(fm['UK Total',k]['share_pp'],signed=True)] for k in keys],size=9)
    r.para('五年变化比较窗口首年与末年，不是五个完整年度的复合增长率。同比基期始终取本版数据。')
    r.table(['指标','公布序列最低','公布序列最高'],[[FUEL_NAMES.get(k,'总发电'), '是' if v['minimum'] else '否','是' if v['maximum'] else '否'] for k,v in e['records_summary'].items() if isinstance(v,dict)])
    r.para('早期“发电与供给表”和“燃料表”的总量存在差异。此处不跨表拼接历史序列；极值结论仅对燃料表成立，不扩展为英国全部历史记录。',10,'#9B4D20')
    v=fuels[year,'UK Total'];old=fuels[year-4,'UK Total']
    r.para(f"可再生与化石燃料占比差从 {((old['renewables']-old['fossil'])/old['total']*100):.2f} pp 变为 {((v['renewables']-v['fossil'])/v['total']*100):.2f} pp。煤电与核电运营背景见审计附件，政策作用不由这些趋势单独证明。",10)
    r.para(context_by_id['X03']['text']+' [X03]',10)
    heading('可再生占比趋势与低碳结构','Chart 3 / 图示为五年可再生发电占比；低碳指标另列表，不能互相替代。')
    r.para('可再生占比 = 可再生发电 / 总发电。低碳 = 核能 + 可再生；图中不把核电计入可再生。',10)
    r.lines({NAMES[g]:values for g,values in semantics['charts']['renewable_share']['series'].items()},years,200,metric_id='renewable_generation_share')
    r.table(['地区','低碳 TWh','低碳 %','低碳变化 pp','可再生 %'],[[NAMES[g],fmt((fuels[year,g]['nuclear']+fuels[year,g]['renewables'])/1000),fmt((fuels[year,g]['nuclear']+fuels[year,g]['renewables'])/fuels[year,g]['total']*100),fmt(sum(fm[g,k]['share_pp'] for k in ['nuclear','renewables']),signed=True),fmt(fm[g,'renewables']['share'])] for g in ['UK Total']+regions],size=8.5)
    r.para(f"本期核电量同比 {fm['UK Total','nuclear']['growth']:+.2f}%，总发电同比 {uk['growth_pct']['total']:+.2f}%，核电份额变化 {fm['UK Total','nuclear']['share_pp']:+.2f} pp。绝对量与份额方向可能不同，应分别判断分子和分母变化。")
    for group in [['Scotland','Wales'],['Northern Ireland','England']]:
        heading('地区燃料结构：'+'、'.join(NAMES[g] for g in group),'重建 Chart 4（官方第 5–6 页）· 每个地区独立刻度；TWh。小类别占比放入表格，避免重叠标签。')
        for g in group:
            r.para(NAMES[g],13)
            r.stacked([(str(y),detailed(fuels[y,g])) for y in years],['煤','天然气','核能','可再生','油/其他/储能'],['#333333',style['fossil'],style['nuclear'],style['renewables'],style['residual']],row_height=21)
            r.table(['本期占比 %','煤','天然气','核能','可再生'],[[NAMES[g]]+[fmt(fm[g,k]['share']) for k in ['coal','gas','nuclear','renewables']]],size=9)
            r.para(f"发电 {fuels[year,g]['total']/1000:.2f} TWh；天然气同比 {fmt(fm[g,'gas']['growth'],signed=True)}%，可再生同比 {fmt(fm[g,'renewables']['growth'],signed=True)}%。",9)
    heading('可再生技术：地区五年趋势','重建 Chart 5（官方第 7 页）· TWh；天然水电不含抽蓄，波浪潮汐单列以补全可再生总量。')
    r.stacked([(NAMES[g]+' '+str(y),[fuels[y,g][k]/1000 for k in ['wind','solar','bioenergy','hydro','tidal']]) for g in regions for y in years],['风电','光伏','生物能源','天然水电','波浪潮汐'],[style['fossil'],'#969DDD',style['nuclear'],'#BED7E8',style['residual']],row_height=20)
    r.para('不同地区规模差异较大；统一刻度便于看绝对量，下一页同时给出同比与集中度，避免只凭柱长判断增长。',10)
    heading('可再生技术：增长与集中度','对应官方第 7–8 页 · 重算风电、生物能源、光伏、水电；外部解释与计算结果分别标明。')
    r.table(['技术','英国 TWh','同比 %','五年变化 %','占发电 %'],[[FUEL_NAMES[k],fmt(fm['UK Total',k]['gwh']/1000),fmt(fm['UK Total',k]['growth'],signed=True),fmt(fm['UK Total',k]['five_year_growth'],signed=True),fmt(fm['UK Total',k]['share'])] for k in ['wind','bioenergy','solar','hydro','tidal']],size=9)
    r.table(['地区','风电同比 %','光伏同比 %','生物同比 %','水电同比 %'],[[NAMES[g]]+[fmt(fm[g,k]['growth'],signed=True) for k in ['wind','solar','bioenergy','hydro']] for g in regions],size=9)
    r.para(f"风电占苏格兰总发电 {fm['Scotland','wind']['share']:.2f}%；英格兰贡献英国生物能源发电 {fuels[year,'England']['bioenergy']/fuels[year,'UK Total']['bioenergy']*100:.2f}%；苏格兰贡献英国天然水电 {fuels[year,'Scotland']['hydro']/fuels[year,'UK Total']['hydro']*100:.2f}%。")
    r.para('装机增长不保证同幅度的发电增长：天气、检修、限电、投运日期与利用率都可能改变产出。具体来源见审计附件；这些因素各自的因果贡献尚未由模型识别。')
    r.para(context_by_id['X05']['text']+' [X05]',10)
    r.para(context_by_id['X06']['text']+' [X06]',10)
    heading('外部证据：需求、运营与天气',f"独立来源：{context['source_title']}，资料版本 {context['as_of']}。以下为文献解释，非汇总表自动推导的因果结论。")
    for item in e['context']['items']:
        r.para(item['id']+' '+item['topic']+' [DUKES PDF 第 '+str(item['page'])+' 页]',11)
        r.para(item['text'],10)
    heading('修订、差异与可验收边界','对应官方第 9 页，并补充源数据核对。差额披露不等于问题已经解决；不能据此批准未经复核的供需守恒模型。')
    r.table(['地区','旧版 TWh','本版 TWh','修订差额'],[[NAMES[v['region']],fmt(v['old_gwh']/1000,3),fmt(v['revised_gwh']/1000,3),fmt(v['gap_gwh']/1000,3,True)] for v in e['revisions']],size=9)
    r.para('同比采用本版基期，修订采用跨版本同年差异，两者不能混用。历史冲突保存在 normalized.json；源表缺失电池储能值保持缺失，不转为零。',10)
    r.table(['源表核对项','地区','残差 TWh'],[[{'balance_residual':'流量平衡减公布消费','public_auto_residual':'公共+自发消费减总计','consumption_region_sum':'区域消费合计减英国','fossil_components':'化石合计减煤油气','cross_sheet_generation':'发电总量跨表绝对差'}[x['kind']],str(x['year'])+' '+NAMES.get(x.get('region','UK Total')),fmt(x['gap_gwh']/1000,6,True)] for x in e['source_issues']],[230,150,135],size=8)
    r.para('系统分别检查计算与来源、指标定义、必答问题和页面呈现。未解决的来源差异保留证据与影响范围；候选状态不等同完整分析任务已经验收。',10,'#9B4D20')
    heading('主要发电商电站分布',f"Appendix B / 引用 {context['source_title']} PDF 第 {context['map_source_page']} 页；地图时点 {context['map_as_of']}，独立于数据年末。")
    r.c.drawImage(str(map_path),65,105,width=465,height=590,preserveAspectRatio=True,anchor='c')
    r.y=91;r.para(context['license']+'。背景图件须保留原时点与署名。',8)
    heading('政策与电站历史背景','补充官方报告的政策与站点背景；采用政府或运营商来源。事件属于历史事实，政策效果不由年度汇总表直接识别。')
    for item in e['context']['historical_context']:
        r.para(item['id']+' '+item['topic'],12)
        r.para(item['text'],10)
        r.link('来源：'+item['source'],item['url'])
        if 'additional_url' in item:r.link('补充来源：EPUKi Lynemouth',item['additional_url'])
    heading('覆盖清单与证据索引','本版是揭示参考后的修复回归。下表列主题与页码；指标定义和必答结论另做可执行检查。' if delayed else '覆盖主题与输出页码；不宣称逐句复刻或独立验证每一个官方因果断言。')
    r.table(['官方主题 / 页码','本报告页','实现方式'],[[v['topic'],v['report_page'],v['mode']] for v in coverage['items']],[280,65,170],size=8)
    r.para('Excel 单元格及哈希见 evidence.json；质量检查见 quality.json；覆盖映射见 coverage.json。外部背景、历史事件与地图绑定本期输入；来源标题可点击。原始参考 PDF 只用于覆盖与对照，不作为生成阶段输入。',9)
    r.para(f"来源：DESNZ 区域电力统计 Excel（截至 {year} 年）；{context['source_title']}。原文件哈希及日期见 context.json 和运行记录。",9)
    r.para('评测边界：本版属于目标报告揭示后的改进回归，不能再作为留出测试。原始冻结稿及揭示记录另存；外部背景仍取自同期 DUKES 文献。' if delayed else '重放评测，目标报告已读，非盲测；外部解释不等于独立因果验证。',9)
    r.link('独立年报：'+context['source_title'],context['source_url'])
    r.save()
    (out/'semantics.json').write_text(json.dumps(semantics,ensure_ascii=False,indent=2))
    pages=PdfReader(out/'report.pdf').pages
    for name,indices in [('business-report.pdf',range(10)),('audit-appendix.pdf',range(10,15))]:
        writer=PdfWriter()
        for index in indices:writer.add_page(pages[index])
        with (out/name).open('wb') as stream:writer.write(stream)
    (out/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['evidence','style','out-dir','map','coverage']:p.add_argument('--'+name,required=True)
    a=p.parse_args();load=lambda x:json.loads(Path(x).read_text())
    render(load(a.evidence),load(a.style),Path(a.out_dir),Path(a.map),load(a.coverage))
