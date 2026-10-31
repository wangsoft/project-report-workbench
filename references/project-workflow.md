# 项目配置、执行与持续积累

[English](project-workflow.en.md) | 简体中文

## 三项工程结构

1. **配置与通用代码分离**：每个项目一份 `project.yaml`，绑定业务契约、脚本和模板。通用入口不硬编码客户、列数、品牌分类或输出 Sheet。
2. **薄调度层与脚本执行层**：本 skill 选择项目、解释变化和综合判断；稳定计算及排版调用已存在的 Python 脚本，不每期重写。
3. **可检查的阶段产物与续跑**：阶段声明文件输出，运行保存参数、指纹、日志和状态；非零退出或缺失输出不会被标为完成。

## 选择与初始化

以下命令从本 skill 根目录执行，使用已装依赖的 Python：

```bash
.venv/bin/python scripts/project_manager.py list
.venv/bin/python scripts/project_manager.py init monthly-sales
.venv/bin/python scripts/project_manager.py validate --project projects/monthly-sales/project.yaml
```

初始化仅创建候选 YAML，不生成子 skill 或虚构业务实现。已有同名目录拒绝覆盖。用户表达有歧义时先查看项目配置中的业务契约，再确认影响口径的选择，不能根据客户名相似就混用。

### 可执行快速入口

对单表“期间×对象”粒度的可加指标，用 `config/periodic-brief.example.json` 的结构编写真实 brief，再执行：

```bash
.venv/bin/python scripts/onboard_project.py --brief /path/to/brief.json
.venv/bin/python scripts/project_manager.py run --project projects/<project-id>/project.yaml --inputs /path/to/inputs.json --cache-dir workspace/cache
```

输入 JSON 只需 `data` 文件路径和 `period`。brief 明确有序 `periods`、完整 `entities`、字段映射、指标单位/方向及必答问题。支持 CSV 或指定 sheet 的 XLSX/XLSM，单行表头；每个期间/对象一行。脚本生成实际三阶段流水线、固定版本的执行代码和项目 brief，输出 HTML、Markdown、问题答案、行级来源和 `delivery.json`。无需另写计算脚本。`init` 仍保留给需要自定义适配器的项目。

目前快速入口支持总量/增速、全部对象贡献分解、逆势对象及总量不变时的内部对冲；只支持显式 `sum` 聚合。公式单元格、重复粒度、选中期间缺对象、非有限值、未知对象和不支持的问题类型会失败，不自动填零。基期非正时不计算增长率。其他期间的行不参与本次计算，并记录排除行数。

`ready_within_scope` 仅表示 brief 所声明的描述性问题和产物绑定检查通过；不代表因果、预测或任意业务分析已获认证。若原任务要求这些内容，智能体必须扩展对应项目适配器和证据输入，不能将问题改成描述性后宣称任务完成。HTML 结构校验不替代实际视觉复核。新项目初始化拒绝覆盖，后续升级显式迁移版本。

## 配置协议 v1

下面是格式示例，脚本与模板必须真实存在后才能校验和运行；示例本身不是已实现的业务流水线。

```yaml
schema_version: 1
project_id: monthly-sales
version: "0.1.0"
status: candidate
inputs:
  data: file
  period: string
  template: file
resources:
  - references/data-contract.md
  - references/analysis-rules.md
  - references/visual-spec.md
pipeline:
  - id: compute
    script: scripts/compute.py
    args: ["--data", "{input:data}", "--period", "{input:period}", "--out", "{run_dir}/evidence.json"]
    outputs: [evidence.json]
    checkpoint: true
    timeout_seconds: 600
  - id: render
    script: scripts/render.py
    args: ["--evidence", "{run_dir}/evidence.json", "--narrative", "{run_dir}/narrative-draft.json", "--template", "{input:template}", "--out", "{run_dir}/report.pptx"]
    outputs: [report.pptx, narrative.json]
```

上例由宿主在检查点写入 `narrative-draft.json`，`render` 先校验草稿，再自行产生最终 `narrative.json`。不能预先写入一个阶段声明的输出。叙事校验须检查 claim ID、数字、限制与反证；声明文件存在仅是工程检查，不是语义验收。

输入仅支持 `file`（记录内容哈希）和 `string`（保存完整值）；JSON 输入键必须与配置一致。输入文件的相对路径相对于输入 JSON 所在目录。`resources` 必须逐文件列出影响结果的规则、模板、导入的项目模块等依赖，不能只列目录。项目阶段脚本自动纳入指纹，通用脚本与依赖清单也纳入；系统字体、第三方包、外部 API 等仍须由项目记录环境和版本，管理器不提供完整环境封装。

脚本和资源路径相对于项目目录，不允许越界；输出路径相对于本次运行目录，不允许重叠或占用管理器状态/日志路径。参数支持 `{input:名字}`、`{run_dir}`、`{project_dir}` 和 `{project_config}`。脚本使用当前 Python 解释器、参数数组和独立工作目录执行，不经 shell。配置中的脚本应是经过检查的本地代码；该入口不是执行不可信代码的沙箱。

## 周期运行与续跑

将当期输入保存为 JSON，例如 `{"data":"sales.xlsx","period":"2026-10","template":"report.pptx"}`，然后执行：

```bash
.venv/bin/python scripts/project_manager.py run --project projects/monthly-sales/project.yaml --inputs /path/to/inputs.json
.venv/bin/python scripts/project_manager.py resume --run-dir /path/to/run --acknowledge compute
```

`run` 输出真实运行目录，包含 UTC 时间与随机 ID，同日多次运行不会合并覆盖。完成后查看 `run_state.json` 和项目验收产物，不能仅凭退出码称报告已通过视觉/业务验收。候选配置可做试跑，状态不会因此自动升级。

只有配置明确设置 `checkpoint: true` 才暂停，普通阶段连续执行。宿主可在检查点读取证据、写叙事草稿，再明确确认对应阶段继续；确认不代表业务质量自动通过。原始日期、模板、数据参数从状态文件恢复，不重新填默认值。已经完成的文件不可修改；补充草稿应使用新的文件名并在后续阶段校验、冻结为声明输出。

续跑核验原始文件、项目配置、代码、声明资源、解释器和已完成输出的指纹。变化时拒绝沿用本次运行，应创建新运行。无半成品的失败阶段可重试；存在未验证输出则要求新运行，不删除用户文件或冒险把半成品当缓存。每个运行有排他锁；进程被强杀后只在确认无进程仍在写入时手动清理 `.lock`。运行中不要修改依赖；外部副作用与脚本自行启动的后台进程不由此入口事务管理。

同一运行内采用保守续跑；跨运行通过 --cache-dir 启用显式依赖缓存，质量阶段不可缓存。协议见 [版本、反馈与缓存](project-lifecycle.md)，真实项目测量见 [性能规程](execution-performance.md)。

## 如何不断积累

- 当期事实、失败原因、人工修改和新假设留在运行目录。未验证建议不直接进入下期规则。
- 将重复且有证据的改进写入对应项目规则、配置、脚本或模板；提升项目版本，记录来源运行、适用范围和回归结果。新一期正常运行不自动升级规则。
- 旧运行保留配置快照、指纹和结果；快照不是完整代码备份。需要历史可重跑时，保留版本控制提交或独立项目版本归档及环境清单，不能仅凭哈希恢复旧代码。
- 只有跨项目成立且经过回归的通用改进才提升到本 skill 的共享工具/规程；客户字段、阈值和风格继续留在项目。不同项目不相互读取私有资产。
- 入口只维护通用流程，先列出项目、再按需加载选中配置与相关规则；不要将所有运行历史或客户报告不断追加进 `SKILL.md`。
