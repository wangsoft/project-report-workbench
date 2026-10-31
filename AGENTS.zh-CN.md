# 仓库贡献指南

[English](AGENTS.md) | 简体中文

## 项目结构与模块组织

本工作台基于 Python 3.10+，生成有证据支撑的周期报告。共享流水线、缓存、初始化和评测工具位于 `scripts/`，通用测试位于 `tests/`。每个 `projects/<project-id>/` 包含 `project.yaml` 以及项目专属脚本、规程、模板、测试和验证记录。通用规程在 `references/`，依赖在 `config/requirements.txt`，智能体执行入口为 `SKILL.md`。`workspace/` 保存输入和运行产物，`releases/` 保存冻结版本。业务专属逻辑应留在对应项目内。

## 构建、测试与开发命令

在仓库根目录执行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r config/requirements.txt
.venv/bin/python scripts/project_manager.py --help
.venv/bin/python -m unittest discover -s tests -v
```

前两条准备环境，后两条查看 CLI 操作和运行通用测试；项目无需单独编译。

验证配置：

```bash
.venv/bin/python scripts/project_manager.py validate --project projects/electricity-quickstart/project.yaml
```

准备好本地示例输入后运行：

```bash
.venv/bin/python scripts/project_manager.py run --project projects/electricity-quickstart/project.yaml --inputs workspace/onboarding-validation/inputs.json --cache-dir workspace/cache
```

运行项目报告或测试前，先安装其专属依赖。

## 代码风格与命名

Python 使用四空格缩进，函数和模块使用 `snake_case`，名称应说明用途。遵循相邻代码风格；当前没有仓库统一的格式化或 lint 配置。项目和阶段 ID 必须匹配 `[a-z][a-z0-9_-]*`。在 `project.yaml` 显式声明流水线产物和缓存依赖。配置路径保持相对形式，保留输入指纹和来源证据。

## 测试要求

使用标准库 `unittest`，文件命名为 `test_*.py`，方法命名为 `test_*`。修复前复现并定位根因。为变化行为增加回归检查，运行器测试使用临时目录隔离。项目测试使用 `-m unittest discover -s projects/<project-id>/tests -v`。没有设定数值覆盖率门槛。报告变更还需数值、证据和视觉验证；命令成功不等于报告质量通过。只有新鲜验证证据才能支持成功声明。

## 提交与 Pull Request

使用简洁的祈使式提交主题；当前历史使用 `docs:` 和 `ci:` 等前缀。PR 说明应包含问题、受影响项目、验证命令与结果及剩余限制。关联相关 issue，报告布局变化附渲染示例。

## 数据与配置安全

共享分发包排除客户数据和运行产物。保留冻结版本，修改候选项目资产并验证后再升版。访问 `ess-repos01.wisers.com:9980` 或 `gitlab.wisers.com` 永远不要使用代理。
