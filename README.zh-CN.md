# Project Report Workbench · 项目分析报告工作台

[English](README.detailed.en.md) | 简体中文 | [简明首页 / Quick start](readme.md)

> `workspace/` 中的原始材料和运行产物不随仓库分发；复跑下述示例前需准备对应输入文件。

在同一个 skill 中积累不同项目的分析口径、方法、模板和脚本，以替代分析师完成约定范围内的报告交付为目标，持续生成有证据支撑的周期报告。

首次建设时，结合历史 Excel/CSV、同期分析师 PDF/PPTX 与适用方法论，沉淀项目配置和可复用流水线。后续期间复用脚本完成数据处理、计算和报告制作，由模型处理综合判断与例外，再通过校验和反馈改进项目能力。

**当前形态是智能体执行规程、项目管理器与可执行报告组件。** 周期可加指标表可以通过 brief 直接创建运行流水线；复杂业务由智能体补充适配器、解释证据和模板。默认由系统分析、写作、核验与处理异常，不要求分析师逐期改稿。当前实现尚不能宣称全行业分析师替代已经验证。

## 快速构建项目

智能体根据用户资料填写 brief，结构见 [配置示例](config/periodic-brief.example.json)，再运行 `scripts/onboard_project.py --brief <brief.json>`。支持 CSV/XLSX 的明确期间、对象与可加指标，自动产出变化、贡献和逆势分析；重复记录、缺对象、非法数字及未支持的问题会阻断。HTML/Markdown、答案与来源一起保存。复杂因果、预测和多表口径须增加项目适配器，不能靠删减问题通过验收。

真实数据的快速入口已验证，可直接复跑：

```bash
.venv/bin/python scripts/project_manager.py run --project projects/electricity-quickstart/project.yaml --inputs workspace/onboarding-validation/inputs.json --cache-dir workspace/cache
```

流程与字段要求见 [项目配置与积累](references/project-workflow.md)。普通 `project_manager.py init` 仍只生成空配置，适用于自定义项目。

## 已跑通的示范项目

[英国区域电力项目](projects/uk-electricity/references/project-spec.md) 使用 DESNZ 两期官方 Excel/PDF，生成中文周期报告：0.2.0 为四页事实版，0.3.0 为十五页全主题候选版。原始材料与来源清单位于 workspace/public-fixtures/uk-electricity。

```bash
.venv/bin/python -m pip install -r projects/uk-electricity/requirements.txt
.venv/bin/python scripts/project_manager.py run --project projects/uk-electricity/project.yaml --inputs workspace/public-fixtures/uk-electricity/2023-release/inputs-v0.5.json --cache-dir workspace/cache
```

学习期标准化数据已保存为基线；迁移机器时需一并迁移原始材料并按项目 SOP 重建基线。0.3.0 三次重复测量中位数：无缓存 1.164 秒、热缓存 0.468 秒，约 2.48 倍。仅适用于本十五页模板，外部背景与地图已作为输入准备好；未调用模型，不含检索、证据整理、建设及人工评审时间。缓存与全量重算的证据和 PDF 字节一致，历史修订与仅修改样式场景也已验证。

[版本与反馈操作](references/project-lifecycle.md) 支持冻结、切换、回退和经回归后关闭反馈。当前激活 0.3.0（主题覆盖候选版；源表差异及业务评审待解决）；候选配置运行默认不使用发布指针，需增加 --active。

工作目录当前为 0.5.0 候选版：Chart 2 使用扣除厂用电后的净供给，Chart 3 使用可再生占比曲线；绘图数据与指标定义联动校验，摘要突出区域核电分化，运营和天气解释进入相应正文。另输出十页业务正文与五页审计附件。2022 与 2024 年回归已执行；2024 年源表差异仍阻断完整交付。原 0.4.0 冻结稿和 25/33 项目标报告对照记录保持不变，不能把本轮修复算作新盲测。

0.5.0 电力全流程三次测量中位数：无缓存 **1.38 秒**、热缓存 **0.73 秒**。快速入口小样本为 **0.34 / 0.23 秒**。仅测准备好数据、配置和背景后的执行，不含首次项目建设、检索或视觉检查。详见 [本轮验证记录](projects/uk-electricity/evals/regression-0.5.0.json)。运行激活的 0.3.0 仍使用 `--active` 和原 `2025-release/full-inputs.json`。

## 核心能力

| 能力 | 工作方式 |
| --- | --- |
| 项目积累 | 每个项目独立保存配置、指标口径、分析规则、SOP、模板与测试，不生成新的子 skill |
| 历史报告学习 | 建立“结论 → 指标 → 计算 → 数据位置”的证据链，区分事实、惯例、假设和外部背景 |
| 视觉体系沉淀 | 同时考虑 PDF/PPTX 的配色、字体、网格、页面类型、图表语义和内容容量 |
| 脚本优先 | 复用稳定的数据读取、清洗、计算、对账、制图和模板填充代码 |
| 模型综合 | 基于包含反证与限制的精简证据包生成叙事，必要时下钻数据 |
| 可检查与续跑 | 保存原始参数、配置快照、内容指纹、阶段输出、日志和耗时 |
| 持续验证 | 检查数字、证据、视觉效果与跨期表现，通过回归后更新项目版本 |

历史报告逆向、方法选择和视觉验收属于智能体执行规程，依赖宿主可用的文档工具及项目脚本；本项目没有内置覆盖所有 PDF/PPTX 的自动解析与渲染引擎。

## 工作流程

```text
历史数据 + 同期报告 + 业务问题 + 适用方法
                  ↓
       提炼口径、分析规则与视觉规范
                  ↓
       项目配置 + 脚本 + 模板 + 回归测试
                  ↓
新一期数据 → 校验与计算 → 证据包 → 叙事 → 报告 → 验收
                                                       ↓
                              记录反馈 → 验证改进 → 升级项目版本
```

不同项目的业务资产相互隔离。当期事实和新假设保存在运行记录中，经过验证的改进才进入长期规则；不会把每一期报告不断追加到 `SKILL.md`。

## 快速开始

### 1. 准备环境

需要 Python 3.10+。以下命令在仓库根目录执行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r config/requirements.txt
.venv/bin/python scripts/project_manager.py --help
```

基础依赖为 `openpyxl` 和 `PyYAML`。具体项目的 PDF/PPTX 处理、制图及导出工具按需求配置，基础依赖不包含全部报告制作能力。

### 2. 让智能体建立项目

将 [SKILL.md](SKILL.md) 作为执行入口，并提供业务目标、历史数据及对应报告。例如：

> 使用当前项目的 SKILL.md，为 monthly-sales 建立月度销售分析项目。根据提供的历史 Excel 和同期 PPTX，提炼指标口径、分析方法、配色与版式，构建可复用脚本与模板。先验证历史期间的计算，再用后续期间检查报告质量。保留未验证项，不生成新的 skill。

至少说明报告面向谁、支持什么决策、数据期间和截止日、所需输出格式。有多期材料时，应在读取参考结论前划分学习、调参与最终留出样本。没有历史报告也可以建立方法论驱动的候选项目；只有一期材料时不能声称已验证跨期泛化。

手动创建候选配置：

```bash
.venv/bin/python scripts/project_manager.py list
.venv/bin/python scripts/project_manager.py init monthly-sales
.venv/bin/python scripts/project_manager.py validate --project projects/monthly-sales/project.yaml
```

`init` 只创建 `project.yaml`，不会创建业务脚本或模板；空流水线可以通过配置检查，但不能运行。补齐实际规则、资源和阶段实现后再生成报告。配置字段、占位符与完整示例见 [项目配置与积累](references/project-workflow.md)。

### 3. 运行新一期数据

以下示例适用于项目已声明 `data`、`period`、`template` 三个输入且流水线已实现的情况。将输入保存为 `inputs.json`：

```json
{
  "data": "sales-2026-10.xlsx",
  "period": "2026-10",
  "template": "report-template.pptx"
}
```

文件相对路径以 `inputs.json` 所在目录为基准；输入键必须与项目配置一致。

```bash
.venv/bin/python scripts/project_manager.py run \
  --project projects/monthly-sales/project.yaml \
  --inputs /path/to/inputs.json
```

命令输出本次运行目录，默认位于 `workspace/<project-id>/<run-id>/`。每次使用独立 ID，避免同日运行覆盖。可以用 `--workspace /path/to/workspace` 指定产物目录。

### 4. 检查产物与续跑

查看运行目录中的 `run_state.json`、`logs/` 和配置声明的输出文件。只有设置了 `checkpoint: true` 的阶段才会暂停；例如配置中的 `compute` 阶段需要宿主读取证据、完成叙事草稿后继续：

```bash
.venv/bin/python scripts/project_manager.py resume \
  --run-dir /path/to/run \
  --acknowledge compute
```

`compute` 应替换为实际等待确认的阶段 ID。续跑保留原始日期、模板与数据参数，并核验依赖和已完成产物。输入、配置、代码或声明资源变化时应创建新运行。同一运行内采用保守续跑；跨运行可用 --cache-dir 启用显式依赖缓存，质量阶段始终重跑。

阶段执行成功仅代表工程检查通过；报告还需项目定义的数字、证据和视觉验收。

## 目录结构

`projects/` 和 `workspace/` 随实际初始化和运行创建，项目内部文件按需要建设。

```text
project-report-workbench/
├── SKILL.md                   # 智能体执行入口
├── agents/openai.yaml         # 技能展示与调用信息
├── config/requirements.txt    # 基础 Python 依赖
├── scripts/                   # 项目管理、数据探查、计算与计时工具
├── references/                # 分析、视觉、配置和验证规程
├── tests/                     # 通用工具与运行器的合成测试
├── evals/validation.json       # 已执行检查与未验证范围
├── projects/<project-id>/
│   ├── project.yaml           # 身份、版本、输入、依赖资源与阶段
│   ├── references/            # 项目口径、规则、报告规范与 SOP
│   ├── scripts/               # 项目计算、校验和渲染实现
│   ├── templates/             # 清理后的模板与授权素材
│   ├── tests/                 # 业务回归
│   └── evals/                 # 项目版本验证记录
└── workspace/<project-id>/<run-id>/
    ├── run_state.json         # 参数、快照、指纹、阶段状态与耗时
    ├── logs/                  # 阶段执行日志
    └── ...                    # 指标、证据、叙事、报告及验收产物
```

原始数据与参考报告保存在用户授权的数据目录或运行目录。分享通用 skill 时不包含客户项目、原始数据及运行产物；项目资产按授权单独分享。

## 已提供的工具

| 工具 | 用途与边界 |
| --- | --- |
| `scripts/project_manager.py` | `init`、`list`、`validate`、`run`、`resume`；调度项目 Python 阶段，不实现具体业务算法 |
| `scripts/project_versions.py` | 冻结发布、激活与回退、证据关联反馈及回归闭环 |
| `scripts/stage_cache.py` | 显式依赖阶段缓存；整条流水线成功后才发布缓存 |
| `scripts/profile_table.py` | 有界探查 `.xlsx`、`.xlsm`、`.csv`；不清洗、不重算公式，不支持旧 `.xls` |
| `scripts/metric_math.py` | Decimal 比率、增长与可加指标贡献分解；口径可比性由项目判断 |
| `scripts/benchmark_command.py` | 测量已有命令的墙钟耗时、失败和重复运行统计；不测 token、费用或峰值内存 |

数据探查示例：

```bash
.venv/bin/python scripts/profile_table.py /path/to/input.xlsx --out /path/to/profile.json
```

生成速度主要通过复用代码和模板、减少重复数据解析、集中模型综合来优化。构建耗时与周期运行耗时分开记录；实际提速幅度需要在同等数据和质量门槛下测量。

## 验证与当前范围

运行已有测试：

```bash
.venv/bin/python -m unittest discover -s tests -v
```

已有 77 项通用测试与 42 项真实样本项目测试，本次均通过；本轮另通过 5 项利润率边界检查。0.3.0 完成十五页 PDF、743 项计算/来源检查与逐页视觉复核；63 项官方数值对照中 61 项一致，2 项差异保留。两期四页版的历史验证单独保留。详见 [验证记录](evals/validation.json)、[示范结果](projects/uk-electricity/evals/pilot-results.json) 和上述 0.4.0 跨期实测记录。

本次是跨期重放，非严格盲测。新版覆盖官方各主题，计算部分之外的天气、政策与运营解释来自独立外部证据；并非所有细节和因果断言均已复现。人工业务评审、完整分析师式因果研究、PPTX 与大型数据性能尚未验证，不能据此承诺达到或超越分析师水平。

## 进一步阅读

全部现行说明均提供中英文版本，见[双语文档索引](readme.md#documentation)。`releases/` 中已冻结的历史归档保持原样；JSON 验证记录和配置字段保留原始值。

- [项目配置、运行与持续积累](references/project-workflow.md)
- [数据处理规程](references/data-processing.md)
- [指标、证据与假设契约](references/contracts.md)
- [方法选择](references/methods.md)与[多视角分析及叙事](references/analysis-synthesis.md)
- [报告逆向与生成](references/report-workflow.md)、[视觉逆向与模板](references/visual-reverse-engineering.md)
- [脚本执行与性能](references/execution-performance.md)
- [项目交付结构](references/deliverables.md)与[评测规程](references/evaluation.md)
- [来源与借鉴说明](references/sources.md)

## 自动诊断、调优与升版

已实现快速入口项目的有界闭环：发现缺失必答问题，生成隔离候选，三期验收通过后自动归档、切换版本，再复跑选中的归档；失败保留旧版或回退。

```bash
.venv/bin/python scripts/auto_tune.py --project projects/<quickstart-project>/project.yaml --suite /path/to/suite.json
.venv/bin/python scripts/project_manager.py run --project projects/retail-monthly/project.yaml --active --inputs workspace/business-tuning-case/april-inputs.json
```

合成零售月报已从 0.1.0 自动升级至 0.1.1，补齐收入、利润、订单的八个缺失问题，三期数值与问题覆盖验收均通过。重复调用已满足要求的项目不应重复升版。周期分析与报告生成使用脚本，不必每次让模型重新计算。

当前自动修复限于已支持的变化、贡献、异常问题配置；新指标口径、任意新算法、因果推断与视觉模板仍需构建对应适配器。商业案例是工程验证，尚非真实分析师报告对比。完整机制与中断恢复见 [项目生命周期](references/project-lifecycle.md)。

本轮自动调优验证记录见 [auto-tuning-validation.json](evals/auto-tuning-validation.json)。

## 从历史报告积累经验

已吸收 skill-training 的重建比较、差异归因、规则检索与更新机制。现在除固定问题补齐外，当前智能体还能依据历史报告提出经验、修改隔离候选脚本或模板，由工作台执行跨期验收、归档与自动切换。没有额外启动多 agent 或模型服务。

- `experience_loop.py prepare`：冻结验收与参考，重建基线，生成学习包。
- `recall`：先找适用规则，再显式打开；保存学习读取记录，区别于生产应用记录。
- `learn`：验证差异引文、归因与经验操作，支持新增、纠正、强化和合并。
- `finish`：候选全期通过且存在已改善的基线缺口才采用；仅写规则不改变报告会被拒绝。

零售示范已从 0.1.1 升至 0.1.2：根据两期合成参考提炼规模与利润率综合规则，将它实现为可重算脚本，在第三期呈现“收入下降而利润增长、利润率提升 2.50 个百分点”。生产输出 experience-applied.json，记录实际应用的规则及哈希。经验与实现一同归档，不另建新 skill。

详见 [学习协议、输入格式与命令](references/project-lifecycle.md)。当前执行适配器覆盖周期描述性项目；合成案例并非真实商业报告质量证明。正文断言不等于完整语义或视觉评分，仍需要针对目标业务的真实样本与专项验收。

零售项目当前采用经验学习后的定制引擎，继续迭代使用 experience_loop；auto_tune 仅用于原始快速入口引擎，不会覆盖定制实现。本轮证据见 [经验学习验证](evals/experience-learning-validation.json)。

## CI 与版本发布

GitHub Actions 在 PR 和 main 推送时运行 Python 3.10、3.12、3.14 的通用测试。main 测试全部通过后，读取根目录 `VERSION`，为尚未发布的版本创建 GitHub Release，并上传源码 ZIP、tar.gz 和 SHA-256 校验文件。已发布版本不会被覆盖。

发布新版时，更新 `VERSION` 并新增 `release-notes/v<版本号>.md`，合并到 main 即触发发布。中断后可在原 Actions 运行中选择 Re-run failed jobs，对同一提交重试；也可在 main 上通过 Run workflow 手动触发验证与发布。流程使用内置 `GITHUB_TOKEN`，无需配置个人令牌。仓库版本与示范项目自身版本相互独立。原始输入和运行产物不包含在发布包中。
