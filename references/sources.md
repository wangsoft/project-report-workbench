# 来源、借鉴与裁剪

[English](sources.en.md) | 简体中文

检查日期：2026-10-31。以下记录来源与设计取舍，不将第三方示例视为已验证业务规则。

## SenseNova

仓库 [OpenSenseNova/SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills)，检查版本 `95db9cf340f0efad2945c3b79f4fc7d7a5d474fd`。

已阅读：

- [sn-da-excel-workflow](https://github.com/OpenSenseNova/SenseNova-Skills/blob/95db9cf340f0efad2945c3b79f4fc7d7a5d474fd/skills/sn-da-excel-workflow/SKILL.md)
- [sn-da-large-file-analysis](https://github.com/OpenSenseNova/SenseNova-Skills/blob/95db9cf340f0efad2945c3b79f4fc7d7a5d474fd/skills/sn-da-large-file-analysis/SKILL.md)
- 同版本 workflow 的 `capability/excel-data-cleaning/numeric-format-normalization/SKILL.md` 与 `capability/excel-reading/single-sheet-reading/SKILL.md`。

| 借鉴点 | 本 skill 的调整 |
|---|---|
| 先探查、多 Sheet、按需加载 | 先有界采样，维度只是提示；必要时才全扫描，保留原行定位 |
| 大文件流式、Parquet 缓存 | 由列宽/内存/重复读取决定；显式 schema、内容哈希缓存和原子落盘 |
| 清洗后对照汇总值 | 加入隔离记录、关联基数、粒度及跨期口径核对 |
| 向量化与大文件写入 | 保留原则，不机械禁止合理迭代；输出遵守宿主与格式限制 |
| 图表与交付 | 从验证后的指标生成图文，实际确认字体和渲染 |

未采用：固定 10k/100k 的绝对阈值；全部转字符串作为分析类型；删掉非中文或非数字字符；金额默认 float32；只凭文件存在复用缓存；固定服务器字体与 `/mnt/data` 链接；复制大量依赖其他技能的子技能列表。

辅助脚本为本项目重新实现；来源项目为 MIT，保留声明于 [sense-nova-license.txt](sense-nova-license.txt)。

## Skill Training

参考本地 `skill-training` 的重建—比较—规则修订思路，检查提交 `5a72d0ec26ee4207f153935000e0b193137f6f53`，重点为 `prompts/backward.md`、`prompts/loss.md` 和 `skilltrain/workflows/s2_forward.py`。

此处以真实数据作为输入，增加确定性核算、证据链、跨期验证与方法论基线；未复制该仓库实现或提示词。没有把剧本实验结果外推为分析报告效果。

## data-analysis-skill 的定向借鉴

检查仓库 [dongzhang84/data-analysis-skill](https://github.com/dongzhang84/data-analysis-skill)，版本 `1c2d806bb282f343d9143e2766faaeb3381f1584`；阅读了 `.claude/skills/data-analysis/` 下的入口、`references/workflows.md`、`domain-knowledge.md`、样式/HTML 组件参考及三个辅助脚本。

吸收三个设计思路并重新编写为 [多视角分析与叙事](analysis-synthesis.md)：

- 多视角改为按问题选择、顺序执行，不固定专家数量、不冒用机构身份、不新增审批环节。
- 发现综合增加证据 ID、去重、反证、范围对齐与冲突状态；多视角意见不当独立证据。
- 叙事组件改为输出格式无关的内容契约，绑定已有视觉规范，不复制其 HTML/CSS 或代码。

未引入其领域公式/阈值、随机机构风格、强制多 agent、自动装依赖及整页截图式 PPTX 路线。未将其示例报告或宣传描述作为质量验证。该项目未成为运行依赖。

## data-analytics-skills 的定向借鉴

来源 [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills)。本次读取 `main` 原始文件，未取得可核实提交号，不声称固定版本。重点阅读 `02-documentation-knowledge/` 下的 semantic-model-builder、metric-reconciliation、analysis-assumptions-log，以及相关定义框架、核对参考和假设脚本；另检查根因、影响估算与上下文打包规程。

定向吸收指标语义定义、逐层差异定位、假设生命周期思路，重新编写并整合进 [contracts.md](contracts.md)，未复制上游代码或模板，也未添加运行依赖。补充了可聚合性、历史时点口径、残余核对、否定/需重验状态及下游影响传播。

未采用通用容差表、固定标准差停止调查条件、预设倍数冒充统计置信区间或隐式修改上游系统。上游 assumptions_tracker.py 和 drilldown_analyzer.py 在本次 `--help` 最小运行中输出演示而非帮助，因此不直接复用其 CLI。这里的实现是智能体执行规程，不是已完成自动语义平台或失效传播引擎。

## 原始技术与方法文档（原文参考）

- [openpyxl optimized modes](https://openpyxl.readthedocs.io/en/stable/optimized.html)：只读/只写模式与不可靠 worksheet dimensions。
- [NIST EDA](https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm)：探索数据结构、异常和假设。
- [NIST time series introduction](https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc4.htm)：趋势、季节性与自相关。

方法应用仍需满足输入条件；这些来源不构成对本 skill 业务效果的认证。

## skill-training 的定向吸收

来源为本地 `../skill-training` 的 README.zh-CN.md、prompts/backward.md、prompts/memory_policy.md、workflows/s2_forward.py、s4_backward.py 和 s5_train.py。吸收重建对比、结合读取轨迹归因、跨样本提炼、经验强化/纠正/新增/合并、快照与恢复的机制；以独立编写的 experience_memory.py 与 experience_loop.py 适配报告项目，没有复制上游源码或提示词，也不作为运行依赖。

上游标注 PolyForm Noncommercial 1.0.0；本次仅借鉴机制，不把上游代码作为可任意商用的依赖引入。上游的剧本训练结果不能作为本工作台的效果证明。其忽略排版的比较方式不适用于报告；本工作台继续保留视觉验收，并用独立数字/报告断言和回归门槛补足格式检查不能证明质量的问题。
