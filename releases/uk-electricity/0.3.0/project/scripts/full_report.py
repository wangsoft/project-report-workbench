"""Render all reference topics with recomputed facts and separately labelled external context."""
import argparse
import json
from pathlib import Path
from report_canvas import Report,NAMES,COLORS

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
    def heading(title,source):r.start(title,source)
    def broad(v):return [v['fossil']/1000,v['nuclear']/1000,v['renewables']/1000,(v['total']-v['fossil']-v['nuclear']-v['renewables'])/1000]
    def detailed(v):return [v['coal']/1000,v['gas']/1000,v['nuclear']/1000,v['renewables']/1000,(v['total']-v['coal']-v['gas']-v['nuclear']-v['renewables'])/1000]
    heading(f'{year} 年英国区域电力分析','摘要 · 全主题覆盖重建；对应官方第 1 页。数据：区域电力 Excel，同一发布版本计算同比。')
    r.para(f"英国发电 {uk['current_gwh']['total']/1000:.2f} TWh，同比 {uk['growth_pct']['total']:+.2f}%；低碳占比 {uk['shares_pct']['low_carbon']:.2f}%，可再生占比 {uk['shares_pct']['renewables']:.2f}%。",15)
    r.para(f"对欧洲净进口 {sm['UK Total']['net_imports']/1000:.2f} TWh；英国公布的终端消费 {sm['UK Total']['values']['consumption']/1000:.2f} TWh，同比 {sm['UK Total']['consumption_growth']:+.2f}%。需求、消费和国内发电不是同一口径。")
    r.table(['地区','发电 TWh','同比 %','低碳 %'],[[NAMES[m['region']],fmt(m['current_gwh']['total']/1000),fmt(m['growth_pct']['total'],signed=True),fmt(m['shares_pct']['low_carbon'])] for m in e['metrics']])
    r.para(f"主要变化：化石燃料发电同比 {uk['growth_pct']['fossil']:+.2f}%，可再生发电同比 {uk['growth_pct']['renewables']:+.2f}%。后续页面分别核对能源结构、消费与贸易，再讨论外部背景，避免把占比提升直接视为产出增长。")
    r.para('验收提示：源表存在燃料分项与供需平衡差额，本报告保留原值并披露。覆盖主题不等于所有源数据已配平；人工业务评审仍待完成。',11,'#9B4D20')
    r.para('阅读顺序：区域趋势 → 供需与贸易 → 燃料和低碳 → 地区结构 → 可再生技术 → 外部背景 → 修订与来源。电站地图为外部图件，有独立日期，不由汇总 Excel 推算。',10)
    heading('区域发电：五年趋势','重建 Chart 1（官方第 2 页）· 所有发电企业；TWh。灰色为余项；2020 年北爱尔兰余项为 -0.000597 TWh，作为红色负差额记录，不能解释成储能产出。')
    r.stacked([(NAMES[g]+' '+str(y),broad(fuels[y,g])) for g in regions for y in years],['化石燃料','核能','可再生','其他储能'],[COLORS[1],COLORS[0],COLORS[2],COLORS[5]],20)
    r.table(['地区','英国份额 %','较上年变化 pp'],[[NAMES[g],fmt(fuels[year,g]['total']/fuels[year,'UK Total']['total']*100),fmt((fuels[year,g]['total']/fuels[year,'UK Total']['total']-fuels[year-1,g]['total']/fuels[year-1,'UK Total']['total'])*100,signed=True)] for g in regions],size=9)
    heading('发电与消费：地区角色','重建 Chart 2（官方第 2–3 页）· 用并列表比较发电与消费份额，同时保留每年总量核对。')
    r.table(['地区','发电 TWh','消费 TWh','发电占比 %','消费占比 %'],[[NAMES[g],fmt(fuels[year,g]['total']/1000),fmt(sm[g]['values']['consumption']/1000),fmt(fuels[year,g]['total']/fuels[year,'UK Total']['total']*100),fmt(sm[g]['consumption_share'])] for g in regions],size=9)
    share_sum=sum(sm[g]['consumption_share'] for g in regions)
    r.para(f'消费占比均按公布的英国消费总量为分母，合计为 {share_sum:.2f}%。未对原始份额做额外归一化；是否配平以原始数值核对为准。',11,'#9B4D20')
    r.table(['年份','英国消费 TWh','区域合计 TWh','差额 TWh'],[[str(y),fmt(next(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']=='UK Total')/1000),fmt(sum(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']!='UK Total')/1000),fmt(sum(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']!='UK Total')/1000-next(x['values']['consumption'] for x in e['supply'] if x['year']==y and x['region']=='UK Total')/1000,signed=True)] for y in years])
    r.para('苏格兰、威尔士的本地发电高于所列消费，英格兰相反。发电量并非扣除厂用电后的净供给，不能将发电减消费直接当作实际跨境输电。')
    r.para(e['context']['items'][0]['text']+' [X01，DUKES PDF 第 29 页]')
    heading('跨境贸易与区域电力流向','重建国际贸易主题与 Appendix A（官方第 3、10 页）· 净流量 GWh / TWh；线路归属不等于完整物理潮流。')
    edges=[('苏格兰 → 英格兰',sm['Scotland']['values']['to_england']),('苏格兰 → 北爱尔兰',sm['Scotland']['values']['to_ni']),('英格兰 → 威尔士',-sm['Wales']['values']['to_england']),('欧洲 → 英格兰',-sm['England']['values']['to_europe']),('威尔士 → 欧洲',sm['Wales']['values']['to_europe']),('北爱尔兰 → 欧洲',sm['Northern Ireland']['values']['to_europe'])]
    r.table(['净流向（负值代表反向）','TWh'],[[a,fmt(v/1000)] for a,v in edges],[360,155])
    r.para('以下用流量台账重建桑基图的数量关系；存在平衡差额时不绘制暗示守恒的闭合宽带图。平衡消费 = 发电 − 厂用/储能用电 − 国内净输出 − 欧洲净输出 − 输配损失。',10)
    r.table(['地区','按流量推算消费','公布消费','残差 TWh'],[[NAMES[g],fmt(sm[g]['balance_consumption']/1000),fmt(sm[g]['values']['consumption']/1000),fmt(sm[g]['balance_residual']/1000,signed=True)] for g in ['UK Total']+regions],size=9)
    r.para(f"英国对欧洲净进口 {sm['UK Total']['net_imports']/1000:.2f} TWh；贸易符号已经统一为进口正、出口负。净额不能反推出总进口和总出口，后者引用独立 DUKES 资料。",10)
    heading('燃料转换与长期记录','对应官方第 2–4 页 · 煤、油、气、核能与可再生。历史记录只在燃料表 2004 年起的公布序列内比较。')
    keys=['coal','oil','gas','nuclear','renewables','fossil']
    r.table(['类别','TWh','同比 %','五年变化 %','占比变化 pp'],[[FUEL_NAMES[k],fmt(fm['UK Total',k]['gwh']/1000),fmt(fm['UK Total',k]['growth'],signed=True),fmt(fm['UK Total',k]['five_year_growth'],signed=True),fmt(fm['UK Total',k]['share_pp'],signed=True)] for k in keys],size=9)
    r.para('五年变化比较窗口首年与末年，不是五个完整年度的复合增长率。同比基期始终取本版数据。')
    r.table(['指标','公布序列最低','公布序列最高'],[[FUEL_NAMES.get(k,'总发电'), '是' if v['minimum'] else '否','是' if v['maximum'] else '否'] for k,v in e['records_summary'].items() if isinstance(v,dict)])
    r.para('早期“发电与供给表”和“燃料表”的总量存在差异。此处不跨表拼接历史序列；极值结论仅对燃料表成立，不扩展为英国全部历史记录。',10,'#9B4D20')
    v=fuels[year,'UK Total'];old=fuels[year-4,'UK Total']
    r.para(f"可再生与化石燃料占比差从 {((old['renewables']-old['fossil'])/old['total']*100):.2f} pp 变为 {((v['renewables']-v['fossil'])/v['total']*100):.2f} pp。煤电收缩与核电运营背景见第 11 页，政策作用不由这些趋势单独证明。",10)
    heading('低碳与可再生：分清口径','重建 Chart 3（官方第 4 页）· 原文引导句写“可再生”，图题及数值实际为“低碳”；本报告同时呈现，避免继承歧义。')
    r.para('低碳 = 核能 + 可再生；储能与其他燃料不自动归入低碳。图中纵轴为 %，下表给出另一口径。',10)
    r.lines({NAMES[g]:[(fuels[y,g]['nuclear']+fuels[y,g]['renewables'])/fuels[y,g]['total']*100 for y in years] for g in ['UK Total']+regions},years,200)
    r.table(['地区','低碳 TWh','低碳 %','低碳变化 pp','可再生 %'],[[NAMES[g],fmt((fuels[year,g]['nuclear']+fuels[year,g]['renewables'])/1000),fmt((fuels[year,g]['nuclear']+fuels[year,g]['renewables'])/fuels[year,g]['total']*100),fmt(sum(fm[g,k]['share_pp'] for k in ['nuclear','renewables']),signed=True),fmt(fm[g,'renewables']['share'])] for g in ['UK Total']+regions],size=8.5)
    r.para('占比变化同时受到分子和分母影响。核电量变化不大时，国内总发电下降也会提高其占比；应同时读绝对量与百分点变化。')
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
    r.para('装机增长不保证同幅度的发电增长：天气、检修、限电、投运日期与利用率都可能改变产出。第 11 页列示已核实的外部解释；当前脚本不估计这些因素各自的因果贡献。')
    heading('外部证据：需求、运营与天气','独立来源：DESNZ DUKES 2025，2025-07-31 发布。以下是文献归因，不是区域汇总表自动推导的因果结论。')
    for item in e['context']['items']:
        r.para(item['id']+' '+item['topic']+' [DUKES PDF 第 '+str(item['page'])+' 页]',11)
        r.para(item['text'],10)
    heading('修订、差异与可验收边界','对应官方第 9 页，并补充源数据核对。差额披露不等于问题已经解决；不能据此批准未经复核的供需守恒模型。')
    r.table(['地区','旧版 TWh','本版 TWh','修订差额'],[[NAMES[v['region']],fmt(v['old_gwh']/1000,3),fmt(v['revised_gwh']/1000,3),fmt(v['gap_gwh']/1000,3,True)] for v in e['revisions']],size=9)
    r.para('同比采用本版基期，修订采用跨版本同年差异，两者不能混用。历史冲突保存在 normalized.json；源表缺失电池储能值保持缺失，不转为零。',10)
    r.table(['源表核对项','地区','残差 TWh'],[[{'balance_residual':'流量平衡减公布消费','public_auto_residual':'公共+自发消费减总计','consumption_region_sum':'区域消费合计减英国','fossil_components':'化石合计减煤油气'}[x['kind']],str(x['year'])+' '+NAMES.get(x.get('region','UK Total')),fmt(x['gap_gwh']/1000,3,True)] for x in e['source_issues']],[230,150,135],size=8)
    r.para('验收分层：算式、引用和文件可执行检查；完整主题覆盖检查；逐页视觉复核；人工业务评审。源数据差异与外部解释仍需业务人员复核，因此本报告保持候选状态。',10,'#9B4D20')
    heading('主要发电商电站分布','对应 Appendix B（官方第 11 页）· 独立引用 DUKES 2025 PDF 第 35 页图件，时点为 2025 年 5 月；不是 2024 年末快照。')
    r.c.drawImage(str(map_path),65,105,width=465,height=590,preserveAspectRatio=True,anchor='c')
    r.y=91;r.para('© Crown copyright 2025 / OGL v3.0。保留图内底图署名；仅为背景资产，下一期必须更换或明确保留旧时点。',8)
    heading('政策与电站历史背景','补充官方报告的政策与站点背景；采用政府或运营商来源。事件属于历史事实，政策效果不由年度汇总表直接识别。')
    for item in e['context']['historical_context']:
        r.para(item['id']+' '+item['topic'],12)
        r.para(item['text'],10)
        r.link('来源：'+item['source'],item['url'])
        if 'additional_url' in item:r.link('补充来源：EPUKi Lynemouth',item['additional_url'])
    heading('覆盖清单与证据索引','覆盖官方全部章节、Chart 1–5、附录 A/B 与修订/来源主题；不宣称逐句复刻或独立验证每一个官方因果断言。')
    r.table(['官方主题 / 页码','本报告页','实现方式'],[[v['topic'],v['report_page'],v['mode']] for v in coverage['items']],[280,65,170],size=8)
    r.para('Excel 单元格及哈希见 evidence.json；质量检查见 quality.json；覆盖映射见 coverage.json。外部来源 X01-X06、H01-H04 与地图绑定本期输入；来源标题可点击。原始参考 PDF 只用于覆盖与对照，不作为生成阶段输入。',9)
    r.para('来源：DESNZ 区域电力统计配套 Excel（2025 发布版）；DUKES 2025 Chapters 1–7（2025-07-31）。独立年报下载地址与 SHA-256 见 context.json；在线入口为 gov.uk 的 DUKES Electricity / Energy Trends。',9)
    r.para('方法限制：本次已读目标报告，属于重放与差距修复，非盲测。政策历史、具体站点事件及天气作用未逐条建立因果模型；以明确归属的外部背景和待补证据表示，不静默沿用上期解释。',9)
    r.link('独立年报：DESNZ DUKES 2025 Chapters 1-7',e['context']['source_url'])
    r.save()
    (out/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['evidence','style','out-dir','map','coverage']:p.add_argument('--'+name,required=True)
    a=p.parse_args();load=lambda x:json.loads(Path(x).read_text())
    render(load(a.evidence),load(a.style),Path(a.out_dir),Path(a.map),load(a.coverage))
