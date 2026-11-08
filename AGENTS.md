# MrSirMusic 项目说明

拟物音乐播放器（Python + PySide6）：不使用文件夹/播放列表，而是通过**拟物物品**（黑胶/磁带/CD）承载音乐。物品由用户手动选歌**生成**（硬容量约束），持久保存在**物品库**（`music/`），可陈列于**置物架**（按 Tag 分类），点选放入**拟物唱机**播放。第一版范围：拟物 + 播放 + 生成 + 基础 UI，无联网依赖。方案全文见同目录 `z.plan.md`，任务清单见 `x.progress.md`。

## 运行与验证

- 入口 `main.py`：`python main.py`（GUI 默认）；`python main.py --version` 打印版本；版本常量 `VERSION` 单一来源在 `config/static/base.json` 的 `version` 字段，其他模块用 `get_static_config().base["version"]` 引用
- 没有测试/lint 命令。改动后验证：`.\.venv\Scripts\python.exe -c "import main, modules.items, modules.rules, modules.generator, modules.library, modules.tagging, modules.cover, modules.playback.engine, modules.playback.events, config.settings, config.static.static_config, ui.main_window, ui.bridge.event_bridge, ui.themes, utils.logger, utils.file_utils, utils.retry, utils.convert"`。不要直接跑 GUI 验证（会弹窗阻塞）
- 全量探针回归（.temp/probe_*.py，offscreen）：`$env:QT_QPA_PLATFORM="offscreen"; foreach ($p in @('probe_a1_config','probe_a2_utils','probe_a3_items','probe_a4_tagging','probe_a5_rules','probe_a6_library','probe_a7_cover','probe_a8_generator','probe_a9_playback','probe_a10_bridge','probe_a11_ui','probe_a12_widgets','probe_a13_effects','probe_a14_integration','probe_a15_sidecar')) { .\.venv\Scripts\python.exe .temp\$p.py | Select-Object -Last 1 }`——每轮改动后跑全量回归（a15 为子进程协议探针，非 offscreen 依赖，随批回归）
- GUI 无头初始化验证（不弹窗）：`$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; from ui.main_window import MainWindow; app = QApplication([]); w = MainWindow(); print('GUI init OK')"`
- 依赖（`requirements.txt`）：PySide6、mutagen 等，按需添加（见 z.plan.md）

## 环境陷阱

- `.venv` 是机器绑定的：`pyvenv.cfg` 的 `home` 指向创建时机器的 Python 路径。换机器/换用户后解释器损坏，症状是 VSCode Python 扩展报 `write EPIPE / Shutting down server`（Jedi 语言服务器无法启动）。重建：`Remove-Item -Recurse -Force .venv; py -3.14 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt`，然后在 VSCode 重选解释器
- opencode 的 pylsp 配置在 `.opencode/opencode.json`，路径硬编码为项目 `.venv` 路径——换机器需同步修改
- Qt 平台：无头验证必须 `QT_QPA_PLATFORM=offscreen`；Windows 原生运行 GUI
- **offscreen 无中文字体**：截图探针中文字全部呈 □ 占位——文字排版类评审/核对（字体层级、行高）必须真机截图，offscreen 截图只用于布局/色彩/控件判断（2026-11-05 UI 评审实测）
- **假音频文件无法真解码**：手写 RIFF 头的空文件会被 FFmpeg 后端拒（`errorOccurred → ERROR → stopped`）——播放链探针必须用 `wave` 模块生成真实 PCM 音频，否则播放态/唱针联动等断言连锁失真（2026-11-05 实测）
- **QMediaPlayer 持媒体文件句柄**（Windows 文件锁）：播放/加载后立即 rename/删除音频文件会 `PermissionError`——探针先 `setSource(QUrl())` 清空源释放句柄 + rename 加重试（probe_a14 实测）
- **stdio 协议流纪律**（sidecar，2026-11-08 实测）：JSON Lines 管道有缓冲——写信封必须**逐行 flush**，否则父进程读不到（a15 红灯证据）；stdout 是协议专用流，任何日志/第三方诊断不得写入（logging StreamHandler 默认 stderr、FFmpeg 诊断也在 stderr——天然不污染，spawn 侧 `stderr=DEVNULL` 即可）

## 验证与门禁（硬性工作流）

> 对齐 CapsulePulse"自动格式化与静态检查"纪律：**改完必须跑，不通过不得宣称完成**；环境缺工具时先报告用户，不得静默跳过。

- **编辑任何 `.py`（main/modules/ui/utils/config）后**：跑冒烟 import 命令（见"运行与验证"），全过才算完成
- **行为改动后**：跑全量 14 探针回归（offscreen）+ 受影响模块对应探针逐项核对
- **UI/视觉改动后**：跑 `.temp/ui_review_shots.py` 重拍截图 + 多模态读图核对（读图规则见"操作注意"）
- **提交前全量门禁**：冒烟 import + 全量探针 + `python main.py --version` 输出与 `base.json` 一致
- **静态检查工具现状**：Python 侧无 formatter/linter 挂载（ruff 未入 `.venv`）——引入时须先在本节登记并单独一次全量格式化提交（避免格式 diff 混入功能提交）；引入前排版以"代码约定"空格/行长条款为准

## 结构与约定

- 包结构按依赖单向分层：`utils/`（通用工具，零业务依赖）→ `config/`（配置）→ `modules/`（业务核心，零 GUI 依赖）→ `ui/`（界面）与 `sidecar/`（侧车进程，PL006）——**允许 import PySide6 的仅 ui/ 与 sidecar/app.py 两处**（sidecar 仅 QtCore 无 GUI：QCoreApplication/QObject/Signal 进程骨架特许）
- `sidecar/` 侧车进程（PL006 定案）：stdio JSON Lines 协议对外暴露 modules/ 业务（信封定案见 z.plan 附录 PL006）；**modules/ 零改动纯委托**；协议编解码/常量单源 `sidecar/protocol.py`；命令表与错误分类单源 `sidecar/commands.py`；优雅退出 = stdin EOF（engine.stop 先行）；测试钩子 `--db/--config`（对称 set_db_path_for_tests 惯例，探针隔离不污染真实数据）；stdout 协议流零污染（日志走 stderr + 文件）
- `modules/` 是**唯一可被未来复用的层**（Web / Godot 后续计划只换 ui/ 层）；模块按单一职责细拆：items（领域模型）、rules（规则引擎）、generator（生成编排）、library（物品库持久化）、tagging（标签解析）、cover（封面服务）、playback（播放核心 + decoders 子包）
- `modules/` 零 UI 依赖：禁止 import PySide6/Qt 任何类型；领域事件契约独立于 Qt（`modules/playback/events.py` 仅事件名 + 数据结构），`ui/bridge/` 是唯一翻译层（core 事件 → Qt 信号）
- `config/` 配置分两类：
  - **静态配置**（`config/static/`，只读，json 驱动）：`static_config.py` 加载器 + `config.json` 引导映射表 + `base.json`（版本等应用参数）+ `item_types.json`（载体类型注册：容量预算/AB面语义/形态）+ `effects.json`（拟真度效果注册表）+ `ui.json`（UI 参数）；模块顶层 `_SC = get_static_config()` 一次性解包，运行时零 IO
  - **用户配置**（`config/settings.py`，可读写）：AppConfig dataclass（拟真度档位/自动翻面），存 `config/user_config.json`
- 三个注册表机制：载体类型（item_types.json）、解码器（`modules/playback/decoders/`，新格式=加一个模块）、封面 providers（`modules/cover/`，network 留接口未实现）
- `music/` 是**用户核心数据目录**（非缓存）：`items.db`（物品库 SQLite）+ `covers/`（封面实体文件）；gitignore 忽略内容但保留目录（`music/*` + `!music/.gitkeep`）；删除前需确认（不同于可随手清理的缓存）
- **参数约定**：可调参数一律走 `config/static/*.json`，禁止代码硬编码
- **版本双轨**（2026-11-05 采纳 CapsulePulse 范本，替代原四段 X.Y.Z.P 口径）：机器版本唯一来源 = `config/static/base.json` 的 `version` 字段（**三段式 `X.Y.Z`**：`X.Y` 版本主线，第一版 `0.1`；`Z` 内容版本，新增内容/重构/小版本更新时 `+1`）；对外正式文本**分两类**——README 徽章用三段式（值 = `base.json` 即时推进，链接指向 Releases 页），**commit 标题用四段式 `VX.Y.Z.R`**（前三段与 `base.json` 一致，第四段 R 为修订号，只随提交历史记录、不入任何配置文件；递增规则见 Commit 提交规范）。历史四段版本（V0.1.0.0–V0.1.1.0）为既有记录保留；当前机器版本以 `base.json` 即时值为准（FIX006.15：删时点性快照，防漂移）
- `main.py` 收编入口分发（argparse + GUI）；模块间顶层 import，不要使用函数内延迟 import（PySide6 等重依赖除外，可在函数内导入）
- `.reference/` 目录是外部项目的 git clone（浅克隆），**不纳入本仓库版本控制**；需要更新时重新 clone
- 项目级 skill 统一在 `.agents/skills/`（19 个 = 自建 5 + skillforge + 外部收录 13）：自建为 `audit-project` / `audit-report` / `plan-task` / `progress-task` / `prune-docs`；`skillforge` 为技能创建/审计（自 `.opencode/skills/` 合并迁入，旧副本目录已删除）；外部收录 13 个（gamedev 3 + Blender 7 + taste-skill / diagram-design / ai-image-prompts-skill）源自 F:\Collection 技能库，均 MIT，来源/用途/维护约定见 `.agents/skills/README.md`；**修订一律以 `.agents/` 为准**
- `.agents/skills/` 整目录不入库（2026-11-07 起 gitignore，与 `.reference/` 同性质的机器本地资源；ai-image-prompts 提示词库可用 `scripts/setup.js --check` 重建）；来源/用途/维护约定见 `.agents/skills/README.md`
- 四文件职责：方案与审计归档 `z.plan.md` / 源码研读报告 `w.study.md` / 任务清单 `x.progress.md` / 问题与远期备忘 `y.problem.md`（详见各文件头部职责块与"任务清单纪律"节）

## 任务清单纪律（x.progress.md / z.plan.md，2026-11-05 切换三线编号轨道）

> 对齐 CapsulePulse 范本。**历史字母系列（A–H）与审计附录 A001–A005 为既有记录全量保留、编号不改**，仅作完成勾选依据；自此之后的计划一律按三线轨道记录，不再沿用字母系列。

- **编号轨道三线**：`PL{NNN}` 功能里程碑（立项方案见 z.plan.md 附录）/ `FIX{N}` 审计修复（由 audit-report 归档生成，与审计附录 `A{NNN}` **恒同号**，取号 = 下一可用 FIX 号 max+1）/ `PATCH{NNN}` 小修小改（用户日常小功能/小调整，不源自审计、不走审计轮）——方案入 z.plan.md 附录，执行条目入 x.progress.md 对应任务组，做法/验证标准三线同规
- **条目做法必须写到文件/函数级**：`—— 做法` 部分指明改哪个文件、哪个函数/方法、新增什么、怎么改（细到可照做）；禁止一句话概括只留验证方式
- **验证方式必须可执行、可断言**：写明探针名/断言值/截图核对点；TDD 类任务先写红灯用例再实现
- **两区结构**：`## 已完成 ✅` 区在前、`## 未完成` 区在后；任务完成整组移入已完成区；两区内部从上到下 = 从旧到新，新组追加在区末尾；已完成组全量保留、只增不删
- **勾选注记**：条目完成时改 `[x]`，句尾追加 `（YYYY-MM-DD 已验证：{一句话结论}）`——结论如实，不达标不降级宣布
- 立项方案（z.plan.md 附录 PL{NNN}）的实现措施与任务条目同标准：一律拆到文件/函数级

## 工程原则（设计哲学，所有项目通用）

> 设计哲学总纲（18 条 / 5 大类，与用户级 instructions.md 同源）；下文"代码规范"为项目细则，两者冲突时以本项目边界为准。

### 核心思想

- 以第一性原理思考问题：理解需求背后的真实目标，而非直接套用已有模式或技术方案。
- 优先解决本质问题，避免为假设中的未来需求提前设计复杂系统。
- 在保证长期可维护性的前提下，选择当前最简单、可靠、清晰的实现方案。

### 简洁与设计

- 遵循 KISS：优先选择简单直接的实现，避免不必要的复杂度。
- 遵循 DRY：避免重复逻辑，但不要为了消除少量重复而创建过度抽象。
- 遵循 SOLID 思想：职责清晰、降低模块耦合，提高可维护性和扩展能力。

### 架构

- 不长期保留废弃方案：优先删除过时代码，而不是增加兼容层、fallback 或临时迁移逻辑。
- 不进行未经验证的架构设计：避免提前引入抽象、配置和间接层。
- 从最小可工作的版本开始逐步演进，每次修改建立在已有可运行系统之上。
- 永远不要用未来可能需要的复杂性，牺牲当前产品的可用性。

### 代码质量

- 保持模块职责明确，避免一个模块承担过多职责。
- 优先使用成熟、稳定、维护良好的第三方库，而不是重复造轮子。
- 使用项目已有依赖解决问题之前，不要随意新增依赖。
- 在引入新方案前，先检查已有代码、依赖、文档和能力。
- 避免为了"看起来更优雅"而增加实际复杂度。

### 工程决策

- 优先选择长期可维护的方案，而不是只能临时运行的解决方案。
- 代码应该服务于业务目标，而不是为了展示技术复杂度。
- 如果简单方案已经满足需求，不要主动升级为复杂方案。

### 本项目边界（消解原则与项目规范的表面张力）

- **参数外置 vs 避免过度配置化**：以参数外置定案为准——业务逻辑常量（SQL/正则/维度枚举）不抽，只抽"可调参数"；原则"避免提前引入配置和间接层"不覆盖既有外置体系
- **审计整改机制 vs 不升级复杂度**：原则约束编码决策；项目审计/文档/验证流程为用户既定工作流，不受"简单方案不升级"覆盖

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

### 容错登记制（2026-11-05 采纳 CapsulePulse 范本）

> fail-soft 主线不变；**新增任何降级/容错点必须先在此登记**，写明场景、降级行为与理由三要素，杜绝无主静默兜底（审计维度同步检查"未登记的静默兜底"）。初始登记（存量降级点盘点）：

- **标签解析失败降级空记录**（A4 存量）：场景——音频文件损坏/格式未知；降级行为——返回 `empty_record()`（title=文件名，其余空），单曲失败不影响物品生成；理由——坏文件不得拖垮整批生成（AGENTS 降级不中断条款的具体化）
- **封面获取失败回退占位图**（A7 存量）：场景——封面文件缺失/图片损坏；降级行为——占位图 provider 兜底不显示空白；理由——缓存兜底策略
- **静态配置坏 JSON 容错空 dict**（A1 存量）：场景——配置文件损坏/缺失；降级行为——告警 + 空分类，消费点回退默认值；理由——配置层不得阻断启动
- **音效初始化失败整体禁用**（V0.1.1.0 H3 登记）：场景——无声卡/QtMultimedia 后端不可用；降级行为——SoundKit fail-soft 禁用并日志一次，播放主链路不受影响；理由——音效为装饰层，不得反噬业务
- **引擎空态静默忽略**（A9 存量）：场景——未载入曲目时调用 seek/position/duration；降级行为——忽略或返回 0；理由——播放控制对空态无业务意义
- **播放器错误降级停止态**（C0.2/D0.5 存量）：场景——解码失败/格式不支持/IO 错误；降级行为——ERROR 事件 + 状态同步 stopped，不崩溃；理由——常驻应用错误必须可提示可自愈
- **删除时封面引用查询失败保守保留**（A8.4 存量 / FIX006.7 登记）：场景——删物品查封面引用时库故障（连接/查询异常）；降级行为——视为有引用保留封面文件 + 告警一次；理由——宁留勿错删（方向保守），残留文件无害
- **删除时封面文件 unlink 失败静默保留**（A8.4 存量 / FIX006.7 登记）：场景——删封面文件遇 PermissionError 等文件系统故障；降级行为——告警一次后照常完成删除主流程；理由——残留文件无害，不得阻断物品删除
- **迁移版本读取失败归 0**（A6.3 存量 / FIX006.7 登记）：场景——schema_version 表缺失/损坏；降级行为——视为 0 走 v1 幂等重建；理由——建库幂等，重建安全不丢数据
- **面内时长缺失降级 payload None**（H1 引入 / FIX006.7 登记）：场景——曲目 duration 缺失或非正（标签解析降级产物）；降级行为——TRACK_CHANGED 附 side_offset/side_total = None，UI 退化为单曲内映射；理由——唱针面内映射为装饰层，缺失不破坏播放
- **面内寻曲时长缺失降级单曲比例**（H1 引入 / FIX006.7 登记）：场景——同上；降级行为——seek_side 按当前曲目内比例跳转；理由——寻曲可用性优先，比例语义在单曲内仍成立
- **未知载体形态回退黑胶绘制**（PL002 引入 / FIX006.7 登记）：场景——item_types 配置 shape 非法或类型键未知；降级行为——按黑胶/circle 绘制 + 告警一次；理由——拟物绘制为装饰层，不得阻断载入与播放
- **贴图加载失败回退矢量绘制**（PL005 引入 / 2026-11-07 登记）：场景——data/textures 贴图缺失或损坏（精简分发漏带资产/路径错误）；降级行为——每键告警一次并按现有矢量渐变绘制，播放与拟物交互不受影响；理由——贴图为装饰层，与噪点叠加同性质的画质增强，不得阻断拟物绘制与播放
- **侧车单命令异常收敛信封**（PL006 引入 / 2026-11-08 登记）：场景——任一命令处理抛未分类异常（命令层 bug/依赖环境突变）；降级行为——记日志（含栈）+ 返回 internal 错误信封，进程与事件循环不退出；理由——单命令失败不得杀死整个后端进程（前端还有重启策略兜底，PL007.3），错误信封保证前端可提示可重试

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
- **文件修改必须用 edit 工具**：修改任何既有文件（.py 代码、.md 文档、json 配置等）一律使用 edit 的精确 oldString/newString 替换，禁止用 Python 脚本（python -c / .temp/impl_*.py）或 PowerShell 命令执行内容替换（易踩引号/缩进/控制字符坑）；新建 .temp 探针/verify 脚本不受限（write 创建），但后续修改仍走 edit
- 音频数组约定：引擎统一 `(N, 2) float32 [-1, 1] @ 44100Hz`（为后续效果器预留）

## Git 注意

- `.gitignore` 忽略 `.venv/`、`.reference/`、`.temp/`、`.opencode/`、`.agents/skills/`、`.mimosa/`、`.zcode/`、`.archived/`、`__pycache__/`、`*.py[cod]`、`.ruff_cache/`、`.vscode/`、`.idea/`、`config/user_config.json`、日志目录；**关键规则**：`music/*` + `!music/.gitkeep`（物品库数据忽略内容但保留目录）；对这些文件的修改不会出现在 `git status` 中；`AGENTS.md`、`README.md`、`z.plan.md`、`x.progress.md`、`w.study.md`、`y.problem.md` 纳入版本控制
- 严禁将 API key、authCookie、workspaceId 等凭据提交到仓库
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作

### Commit 提交规范

- **标题行**：`<type>: V<版本>，<摘要>`——版本为四段式 `VX.Y.Z.R`（如 `V0.1.1.1`）：前三段与 `base.json` 的 `version` 一致，第四段 R 为修订号（**只随提交历史记录、不入任何配置文件**，见"版本双轨"）；摘要一句话概括核心（可用括号列重点）
- **版本递增**：`feat` / `fix` / `refactor` / `perf` 提交前先 bump 第四段 R（R+1）；前三段在 `base.json` 推进时 R 回到 1；`docs` / `test` / `style` / `chore` 不强制
- **type 全集**（conventional 风格）：
  - `feat` 新功能 / `fix` 修复 / `refactor` 重构（行为不变）/ `perf` 性能
  - `docs` 文档 / `test` 测试 / `style` 格式 / `build` 构建依赖 / `ci` CI / `chore` 杂项 / `revert` 回滚
- **正文**（默认必写，仅 docs/style 微调可省）：`- ` 列表逐条"具体做了什么"，每条一个功能块、一行自然中文、≤ 100 字符；体例 = `主题：内容（细节；细节）`，同主题多细节用 `；` 分隔
- **禁止项**：内部编号（PL001.1/FIX001.2 等任务编号）、验证/回归数字（如"全量回归 506 项通过"）、英文混排描述
- **提交范围**：一个版本的所有连带改动一次提交（源码 + 配置 + 文档同步）
- **流程**：由 AI 根据 `git status`/`git diff`（含 `--stat`）核对清单并草拟 commit 内容（git add 清单 + 标题 + 正文）→ 用户审阅后自行执行 `git add`/`git commit`/`git push`；**用户明确要求提交/推送时 AI 可按其指示执行**（执行前仍须核对改动范围）

## 操作注意

- 执行命令前先检测当前 shell（Windows 下为 pwsh）：使用 PowerShell 兼容命令（`Select-String` 替代 `grep`，`Get-ChildItem` 替代 `ls` 等），避免 Linux-only 工具
- pwsh 会话带 `-NoProfile` 不加载 `$PROFILE`；**每次执行命令无条件前置**编码设置：`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;`——不做输出内容预判，一律先设再执行，杜绝 GBK 解码乱码
- 未经用户明确要求，不得擅自执行 `git add`、`git commit` 或任何其他 Git 写操作
- **多模态模型约定**：拟物 UI 的视觉核对（截图/封面/磨损效果）需要读图；当前默认模型若无视觉能力（读图工具返回 `Cannot read: this model does not support image input`），需要读图的任务（UI 截图核对、效果图分析等）**必须先通知用户切换多模态模型**再执行；**未实际读到图时严禁声称"能读到"或编造图片内容**——图读失败如实报告
- **验证禁止更改电脑系统设置**：live 验证一律以系统当前态进行；禁止为验证去切换系统主题、缩放（DPI）、动画效果等系统设置——替代手段 = 代码走查确认规则在位 + 用户日常使用复核（2026-11-05 采纳 CapsulePulse 范本）
