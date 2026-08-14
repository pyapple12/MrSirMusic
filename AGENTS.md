# MrSirMusic 项目说明

拟物音乐播放器（Python + PySide6）：不使用文件夹/播放列表，而是通过**拟物物品**（黑胶/磁带/CD）承载音乐。物品由用户手动选歌**生成**（硬容量约束），持久保存在**物品库**（`music/`），可陈列于**置物架**（按 Tag 分类），点选放入**拟物唱机**播放。第一版范围：拟物 + 播放 + 生成 + 基础 UI，无联网依赖。方案全文见同目录 `z.plan.md`，任务清单见 `x.progress.md`。

## 运行与验证

- 入口 `main.py`：`python main.py`（GUI 默认）；`python main.py --version` 打印版本；版本常量 `VERSION` 单一来源在 `config/static/base.json` 的 `version` 字段，其他模块用 `get_static_config().base["version"]` 引用
- 没有测试/lint 命令。改动后验证：`.\.venv\Scripts\python.exe -c "import main, modules.items, modules.rules, modules.generator, modules.library, modules.tagging, modules.cover, modules.playback.engine, modules.playback.events, config.settings, config.static.static_config, ui.main_window, ui.bridge.event_bridge, ui.themes, utils.logger, utils.file_utils, utils.retry, utils.convert"`。不要直接跑 GUI 验证（会弹窗阻塞）
- 全量探针回归（.temp/probe_*.py，offscreen）：`$env:QT_QPA_PLATFORM="offscreen"; foreach ($p in @('probe_a1_config','probe_a2_utils','probe_a3_items','probe_a4_tagging','probe_a5_rules','probe_a6_library','probe_a7_cover','probe_a8_generator','probe_a9_playback','probe_a10_bridge','probe_a11_ui','probe_a12_widgets','probe_a13_effects','probe_a14_integration')) { .\.venv\Scripts\python.exe .temp\$p.py | Select-Object -Last 1 }`——每轮改动后跑全量回归
- GUI 无头初始化验证（不弹窗）：`$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; from ui.main_window import MainWindow; app = QApplication([]); w = MainWindow(); print('GUI init OK')"`
- 依赖（`requirements.txt`）：PySide6、mutagen 等，按需添加（见 z.plan.md）

## 环境陷阱

- `.venv` 是机器绑定的：`pyvenv.cfg` 的 `home` 指向创建时机器的 Python 路径。换机器/换用户后解释器损坏，症状是 VSCode Python 扩展报 `write EPIPE / Shutting down server`（Jedi 语言服务器无法启动）。重建：`Remove-Item -Recurse -Force .venv; py -3.14 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt`，然后在 VSCode 重选解释器
- opencode 的 pylsp 配置在 `.opencode/opencode.json`，路径硬编码为项目 `.venv` 路径——换机器需同步修改
- Qt 平台：无头验证必须 `QT_QPA_PLATFORM=offscreen`；Windows 原生运行 GUI

## 结构与约定

- 包结构按依赖单向分层：`utils/`（通用工具，零业务依赖）→ `config/`（配置）→ `modules/`（业务核心，零 GUI 依赖）→ `ui/`（界面，**唯一允许 import PySide6 的层**）
- `modules/` 是**唯一可被未来复用的层**（Web / Godot 后续计划只换 ui/ 层）；模块按单一职责细拆：items（领域模型）、rules（规则引擎）、generator（生成编排）、library（物品库持久化）、tagging（标签解析）、cover（封面服务）、playback（播放核心 + decoders 子包）
- `modules/` 零 UI 依赖：禁止 import PySide6/Qt 任何类型；领域事件契约独立于 Qt（`modules/playback/events.py` 仅事件名 + 数据结构），`ui/bridge/` 是唯一翻译层（core 事件 → Qt 信号）
- `config/` 配置分两类：
  - **静态配置**（`config/static/`，只读，json 驱动）：`static_config.py` 加载器 + `config.json` 引导映射表 + `base.json`（版本等应用参数）+ `item_types.json`（载体类型注册：容量预算/AB面语义/形态）+ `effects.json`（拟真度效果注册表）+ `ui.json`（UI 参数）；模块顶层 `_SC = get_static_config()` 一次性解包，运行时零 IO
  - **用户配置**（`config/settings.py`，可读写）：AppConfig dataclass（拟真度档位/自动翻面），存 `config/user_config.json`
- 三个注册表机制：载体类型（item_types.json）、解码器（`modules/playback/decoders/`，新格式=加一个模块）、封面 providers（`modules/cover/`，network 留接口未实现）
- `music/` 是**用户核心数据目录**（非缓存）：`items.db`（物品库 SQLite）+ `covers/`（封面实体文件）；gitignore 忽略内容但保留目录（`music/*` + `!music/.gitkeep`）；删除前需确认（不同于可随手清理的缓存）
- **参数约定**：可调参数一律走 `config/static/*.json`，禁止代码硬编码；版本号唯一来源为 `base.json` 的 `version` 字段，格式四段式 `X.Y.Z.P`：`X.Y` 版本主线（第一版 `0.1`）、`Z` 内容版本（新增内容/重构/小版本更新时 `+1`）、`P` 审计轮次（每次审计修复 `+1`）；`Z` 递增时 `P` 归零重新计数
- `main.py` 收编入口分发（argparse + GUI）；模块间顶层 import，不要使用函数内延迟 import（PySide6 等重依赖除外，可在函数内导入）
- `.reference/` 目录是外部项目的 git clone（浅克隆），**不纳入本仓库版本控制**；需要更新时重新 clone
- 项目规划与方案文档在 `z.plan.md`，源码研读报告在 `w.study.md`，任务清单在 `x.progress.md`

## 代码规范

### 错误策略

常驻桌面应用 + 音频播放的错误处理主线：**不崩溃、不阻塞、有提示、能自愈**。

- 统一错误类型：业务错误定义分类异常，携带中文消息；UI 只认分类不认细节
- 播放/解码回调纪律：回调内零 IO、零分配、锁内操作保持短；回调异常 fail-soft（静音降级），绝不抛出到 UI 线程
- 降级不中断：标签解析失败返回 `empty_record()`（title=文件名，其余空），单曲失败不影响物品生成
- 缓存兜底：封面/数据获取失败回退占位图（placeholder provider），不显示空白
- 宽容解析：外部数据（分析结果、配置）数字字段弹性转换，坏 JSON 返回空不崩溃，None 语义区分"未记录"与 0
- 节流 + 去重：非必要不频繁刷新（进度上报/列表刷新）；in-flight 去重，避免重复加载
- 保留旧数据：刷新失败保留旧视图，成功后视图才替换
- 路径失效：文件被移动 → Track 标记 missing，播放时提示，不崩溃
- 只读防误写：缓存类数据库（如未来分析/统计缓存）一律只读连接（mode=ro）；用户数据库（music/items.db）走事务写

### 函数注释规则

- 每个函数定义下方紧跟 `#` 注释，说明该函数的用途和核心逻辑（1-3 行）
- **禁止使用 docstring（三引号字符串）替代 `#` 注释**——函数/类/模块文档统一走 `#` 注释体系，docstring 不承担注释职责；单行 docstring 当注释用属于违规
- 每个 `.py` 文件末尾必须有完整的函数逻辑说明区，用 `# =====` 分隔，涵盖文件中所有函数/模块级常量：
  - 输入、输出、逻辑步骤
  - 设计理由（为什么这样做）
  - 异常处理说明
  - 关联的配置或外部依赖

### 代码约定

- 注释必须用 `#`，禁止 `//` 或其他语言注释符号；所有注释使用中文
- **正式程序文件（main.py 及 modules/、ui/、utils/、config/ 下的 .py）的注释中禁止出现任何与 `.reference/` 相关的参考标注**（如"参考：.reference/…"、"照抄自…"等）；参考来源信息只允许写在 `.temp/` 临时脚本或文档（w.study.md / x.progress.md / z.plan.md）中
- 命名风格：函数/变量用 `snake_case`，类用 `CamelCase`，常量用 `UPPER_CASE`
- `_` 前缀：函数名前加 `_` 表示模块内部私用，如 `_format_tokens()`，外部模块不应直接调用
- `def main()`：每个可独立运行的脚本都有 `main()` + `if __name__ == "__main__": main()`
- 类型注解：优先使用 Python 类型注解，包括 `typing` 模块和 `| None` 语法
- dataclass：配置聚合优先用 `@dataclass`
- import 顺序：标准库 → 第三方库 → 本地模块，每组之间空行分隔
- f-string：字符串格式化优先用 f-string，避免 `.format()` 或 `%`
- 推导式：优先用列表/字典推导式而非手写 for 循环构建集合
- 布尔值判断：用 `if x:` / `if not x:` 而非 `if x == True:` / `if x is False:`
- 空值判断：用 `if x is None:` / `if x is not None:` 而非 `if x == None:`
- 异常捕获：避免裸 `except:`，至少用 `except Exception:`，指定具体异常类型更好；捕获多个异常类型可用 `except (Exc1, Exc2):`
- 行长度：每行尽量不超过 100 字符（超过时在运算符或逗号后换行）
- 空格约定：逗号后加空格、冒号前不加空格（切片冒号两侧不加）、赋值/比较运算符两侧加空格、函数定义前后各空两行、类定义前后各空两行、方法之间空一行
- 字符串引号：普通字符串用双引号；f-string 内含大量双引号时允许外层使用单引号
- 路径处理：强制使用 `pathlib` 代替 `os.path`
- 临时文件：所有临时生成的脚本/文件必须写入项目根目录下的 `.temp/` 文件夹（已 gitignore）
- 音频数组约定：引擎统一 `(N, 2) float32 [-1, 1] @ 44100Hz`（为后续效果器预留）

## Git 注意

- `.gitignore` 忽略 `.venv/`、`.reference/`、`.temp/`、`.opencode/`、`__pycache__/`、`*.py[cod]`、`.ruff_cache/`、`.vscode/`、`.idea/`、`config/user_config.json`、日志目录；**关键规则**：`music/*` + `!music/.gitkeep`（物品库数据忽略内容但保留目录）；对这些文件的修改不会出现在 `git status` 中；`AGENTS.md`、`README.md`、`z.plan.md`、`x.progress.md`、`w.study.md` 纳入版本控制
- 严禁将 API key、authCookie、workspaceId 等凭据提交到仓库
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作

### Commit 提交规范

- **标题行**：`<type>: V<版本>，<摘要>`——版本号与 base.json `version` 字段一致（四段式 `X.Y.Z.P` 全写，如 `V0.1.0.1`）；摘要一句话概括核心（可用括号列重点）
- **type 全集**（conventional 风格）：
  - `feat` 新功能 / `fix` 修复 / `refactor` 重构（行为不变）/ `perf` 性能
  - `docs` 文档 / `test` 测试 / `style` 格式 / `build` 构建依赖 / `ci` CI / `chore` 杂项 / `revert` 回滚
- **正文**（改动大时可选）：`- ` 列表，按主题分组、分组下子条目缩进，每个功能块一行自然中文描述，每行 ≤ 100 字符
- **禁止项**：内部编号（A0.1/B2.3 等任务编号）、验证/回归数字（如"全量回归 506 项通过"）、英文混排描述
- **提交范围**：一个版本的所有连带改动一次提交（源码 + 配置 + 文档同步）
- **流程**：由 AI 根据 `git status`/`git diff` 核对清单并草拟 commit 内容（git add 清单 + message）→ 用户审阅后自行执行 `git add`/`git commit`/`git push`（AI 不执行 git 写操作）

## 操作注意

- 执行命令前先检测当前 shell（Windows 下为 pwsh）：使用 PowerShell 兼容命令（`Select-String` 替代 `grep`，`Get-ChildItem` 替代 `ls` 等），避免 Linux-only 工具
- pwsh 会话带 `-NoProfile` 不加载 `$PROFILE`；**每次执行命令无条件前置**编码设置：`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;`——不做输出内容预判，一律先设再执行，杜绝 GBK 解码乱码
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作
- **多模态模型约定**：拟物 UI 的视觉核对（截图/封面/磨损效果）需要读图；当前默认模型若无视觉能力（读图工具返回 `Cannot read: this model does not support image input`），需要读图的任务（UI 截图核对、效果图分析等）**必须先通知用户切换多模态模型**再执行；**未实际读到图时严禁声称"能读到"或编造图片内容**——图读失败如实报告
