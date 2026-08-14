# MrSirMusic 第一版开发任务清单（A 系列）

- 任务清单定稿：2026-08-14
- 依据：z.plan.md（MrSirMusic 项目方案 v1.0）
- 编号：A 系列（新项目首轮），组号 = 开发阶段，组内条目 `A{组}.{序号}`
- 约定：全部验证命令在项目根目录、`.venv` 解释器下执行；GUI 验证用 `QT_QPA_PLATFORM=offscreen` 免弹窗；正式文件注释禁止 `.reference/` 标注

---

## A0. 项目骨架与基础设施

- [x] A0.1 初始化 git 仓库与 .gitignore —— 创建 `git init`；.gitignore 含：`.venv/`、`.reference/`、`.temp/`、`.opencode/`、`__pycache__/`、`*.py[cod]`、`.ruff_cache/`、`data/cache/`、以及**关键规则** `music/*` + `!music/.gitkeep`（忽略内容保留目录）；验证：`git status` 显示 music/.gitkeep 被跟踪、其余忽略（✅ 2026-08-14 完成：git init main 分支 + local config + remote；git status 验证 music/.gitkeep 跟踪、.reference/.opencode 忽略）
- [x] A0.2 创建目录骨架 —— 按 z.plan.md 目录结构建全：config/static、utils、modules/items、modules/rules、modules/generator、modules/library、modules/tagging、modules/cover、modules/playback/decoders、ui/views、ui/widgets、ui/effects、ui/bridge、music/covers、data/textures、docs、.temp；各包放 `__init__.py`；验证：目录树与 z.plan.md 逐一比对（✅ 2026-08-14 完成：探针 .temp/probe_a02_dirs.py 断言 17 目录 + 17 包 PASS）
- [x] A0.3 建立 .venv 与 requirements.txt —— `py -3.14 -m venv .venv`；requirements.txt 起步：PySide6、mutagen（pytest 可选后加）；验证：`.\.venv\Scripts\python.exe -c "import PySide6, mutagen"`（✅ 2026-08-14 完成：PySide6 6.11.1 + mutagen 1.48.1；另装 python-lsp-server 供 opencode pylsp，不进 requirements）
- [x] A0.4 编写 main.py 入口 —— argparse（--version/-V + 默认 GUI）；版本号从 `config/static/base.json` 读取（先建最小 base.json）；PySide6 与 ui.main_window 延迟导入；函数下 `#` 注释 + 文件尾 `# =====` 说明区；验证：`python main.py --version` 输出正确；`python -c "import main"` 冒烟通过（✅ 2026-08-14 完成：--version 输出 0.1.0.0、import main 冒烟 OK、GUI 缺 ui 时友好提示退出不崩溃）
- [x] A0.5 编写 AGENTS.md（项目规范）—— 抄录 z.plan.md 第七节架构约束 + MrAutoDJ 系代码规范（函数注释规则/代码约定/Git 注意/Commit 规范/操作注意）；验证：人工审核与 z.plan.md 一致（✅ 2026-08-14 完成：项目初始提交时已有，含四段版本规则、无条件编码设置、Commit 主题分组细则）
- [x] A0.6 编写 README.md —— 项目定位、第一版功能、运行方式（`python main.py`）、目录说明；验证：人工审核（✅ 2026-08-14 完成：初始提交时创建）

## A1. 配置体系

- [x] A1.1 static_config.py 加载器 —— json 读取 + 模块级缓存（`get_static_config()` 单例）+ 坏 JSON 容错（返回空 dict + 日志告警，不崩溃）；函数注释 + 文件尾说明区；验证：.temp 探针脚本加载全部 json 并打印结构（✅ 2026-08-14 完成：四分类聚合 dataclass + 懒加载单例；坏 JSON/缺映射键 → 空 dict + logging 告警）
- [x] A1.2 base.json —— 字段：version（"0.1.0.0"，四段式 X.Y.Z.P 初始值）、app_name（"MrSirMusic"）、sample_rate（44100）、channels（2）、music_dir（"music"）、data_dir（"data"）；验证：探针读取断言（✅ 2026-08-14 完成：A0.4 时已建，本轮探针断言六字段 + version 值通过）
- [x] A1.3 config.json 引导映射表 —— 结构：`{"base": "base.json", "item_types": "item_types.json", "effects": "effects.json", "ui": "ui.json"}`；验证：static_config 按映射逐个加载成功（✅ 2026-08-14 完成：探针四分类非空断言通过）
- [x] A1.4 ui.json —— 字段起步：窗口尺寸、主色/辅色、动画时长（转盘转速、唱针落下时长）、列表列宽等；验证：探针读取断言（✅ 2026-08-14 完成：window 尺寸/colors.primary+secondary/animation.record_spin_ms+tonearm_drop_ms/library_column_widths 断言通过）
- [x] A1.5 item_types.json —— 按 z.plan.md 第六节样例：vinyl/cassette/cd（name/side/minutes_per_side/shape）；验证：探针校验三条记录字段完整、side 均为合法面集合（✅ 2026-08-14 完成：三载体四字段齐全，side ∈ {A,B} 断言通过）
- [x] A1.6 effects.json —— 三档（concise/refined/realistic）：每档声明 `animations: bool`、`wear: bool`、`weathering: bool`、强度值；验证：探针断言三档齐全、默认档位存在（✅ 2026-08-14 完成：三档 bool 字段类型断言 + default_level=refined 存在 + 强度值字段通过）
- [x] A1.7 settings.py（用户配置）—— AppConfig dataclass（`realism_level`、`auto_flip`）+ 读写 `config/user_config.json`（缺省回退默认值，坏 JSON 不崩溃）+ 变更通知回调接口；验证：探针写→读→比对回环；删文件后回退默认（✅ 2026-08-14 完成：写读回环一致 + 回调触发 + 坏 JSON 回退默认 + 探针清理用户文件）

## A2. 工具层（utils/，零业务依赖）

- [x] A2.1 logger.py —— 控制台 + 文件（logs/mrsirmusic.log）双输出，中文 UTF-8，模块名级别；验证：探针调用产生日志文件（✅ 2026-08-14 完成：双 handler + UTF-8 文件 handler + 模块名 logger；探针断言日志文件含消息/模块名/级别）
- [x] A2.2 file_utils.py —— pathlib 封装：`is_audio_file(path)`（按扩展名集合）、`ensure_dir(path)`、`safe_copy(src, dst)`、`file_exists(path)`；验证：断言各函数行为（✅ 2026-08-14 完成：扩展名白名单大小写兼容、safe_copy 成功/失败/内容断言）
- [x] A2.3 retry.py —— `retry(times, delay)` 装饰器，指数退避，捕获指定异常，最终失败重抛；验证：mock 函数先失败后成功 → 重试次数断言（✅ 2026-08-14 完成：指数退避 + exceptions 参数；3 次成功/指定异常外不重试/最终重抛断言通过）
- [x] A2.4 convert.py —— `format_duration(seconds)`（mm:ss）、`seconds_from_ms(ms)`、`to_float32(audio)`（占位，为后续音频处理预留）；验证：断言边界值（0、61、3599）（✅ 2026-08-14 完成：格式 mm:ss 分钟自然位数秒补零（1:01 风格）、毫秒转秒、float32 占位原样返回；边界 0/61/3599 断言通过）

## A3. 领域模型（modules/items/）

- [x] A3.1 ItemType —— 枚举或 dataclass：`vinyl/cassette/cd`，字段 name/sides（tuple）/minutes_per_side/shape；提供 `from_config(json)` 工厂（读 item_types.json）；验证：断言三个类型实例化 + 容量字段正确（✅ 2026-08-14 完成：frozen dataclass + from_config(key, data) 宽容解析；三载体 22/30/80 分钟断言通过）
- [x] A3.2 Track —— dataclass：path/title/artist/album/duration_seconds/format；`from_tagging(TagData)` 工厂 + `is_missing()`（路径失效检测）；验证：断言构造与工厂（✅ 2026-08-14 完成：from_tagging duck typing（A4.1 TagData 建成后兼容）+ is_missing 存在/缺失断言）
- [x] A3.3 Side —— dataclass：`label`（"A"/"B"）、`tracks: list[Track]`；方法 `total_seconds()`、`add_track(track)`、`remove_track(track_id)`、`is_full(max_seconds)`；验证：断言容量边界（恰好满/超出）（✅ 2026-08-14 完成：按 path 移除、is_full >= 语义恰好满/超 1 秒/未满三态断言）
- [x] A3.4 Item —— dataclass：id（uuid）/name/type（ItemType）/cover_source/cover_path/tag/created_at/play_count/sides（dict[str, Side]）；方法 `all_tracks()`、`total_seconds()`、`side_for(label)`、`bump_play_count()`；验证：断言构造与聚合方法（✅ 2026-08-14 完成：uuid 唯一性 + 展平/时长/side_for/播放次数断言）
- [x] A3.5 items 工厂函数 —— `create_item(name, type, tag)`、`add_track_to_side(item, side_label, track)`（内部调用容量校验，返回成功/失败原因）、`remove_track(item, side_label, index)`；验证：断言全流程（含超容量拒绝）（✅ 2026-08-14 完成：面初始化 + 容量内成功/超容量拒绝中文原因/按序号移除；容量校验内联，A5.1 后生成流程统一走规则引擎）

## A4. 标签解析（modules/tagging/）

- [x] A4.1 TagData 统一结构 —— dataclass：title/artist/album/duration_seconds/format/embedded_cover(可选 bytes)；验证：断言构造（✅ 2026-08-14 完成：六字段 dataclass；embedded_cover 预留 None，A7 需要时提取）
- [x] A4.2 read_tags(path) —— mutagen 封装：按扩展名分派（ID3/MP4/FLAC/WAVE），提取字段；时长优先取 mutagen 信息（无则用文件名兜底）；返回 TagData；验证：.temp 造真实样本（mp3/flac/wav/m4a 各一）断言字段（✅ 2026-08-14 完成：四格式真实样本（手写 1s PCM WAV + 手写最小 FLAC/MP4 + mutagen 写标签）断言 title/artist/album/format + wav 时长 1.0s；mp3 无帧文件走 ID3 纯标签降级）
- [x] A4.3 容错降级 —— 损坏文件/未知格式 → 返回 `empty_record()`（title=文件名，其余空，format=扩展名），不抛异常；验证：损坏样本（截断的 mp3）断言不崩溃（✅ 2026-08-14 完成：截断 mp3 与 .xyz 未知格式均降级 title=stem；mutagen.File 对纯标签无帧文件抛 HeaderNotFoundError 已捕获处理）
- [x] A4.4 read_tags_batch(paths) —— 批量解析，单曲失败降级继续，返回 `list[TagData]`；验证：混合样本（含损坏）断言数量与降级项（✅ 2026-08-14 完成：5 路径混合（4 正常 + 损坏 + 未知）数量 5、降级 2 断言通过）

## A5. 规则引擎（modules/rules/）

- [x] A5.1 capacity.py —— `remaining_seconds(side, item_type)`、`fits(side, track, item_type) -> (bool, 原因)`；单曲超过单面容量 → 拒绝并说明；验证：断言边界（恰好/超出 1 秒/长曲）（✅ 2026-08-14 完成：剩余容量计算 + fits 边界（恰好通过/超 1 秒拒绝/长曲拒绝，原因含曲名与时长））
- [x] A5.2 side_allocator.py —— AB 面分配：第一版**顺序填充**（按添加顺序填 A 面，满后填 B 面）；预留策略参数（`ALLOC_STRATEGY` 常量，后续可加"平分/手动"）；验证：断言 8 首歌 3/5 分配结果（✅ 2026-08-14 完成：8 首 3/5 分配 + CD 单面超容跳过；修复长曲跳过后索引不重置导致后续曲目错失 A 面的 bug，每首从 A 面重试）
- [x] A5.3 validate.py —— 选歌校验：重复曲目（同一 path 不入两面）、超容量、路径失效（missing）；返回校验结果列表（每条含原因）；验证：断言三类拒绝场景（✅ 2026-08-14 完成：SelectionIssue(path, reason) 列表；重复/缺失/超容三类断言；探针相对路径误判 missing 已改用绝对路径样本）
- [x] A5.4 generate_check.py —— 生成前完整性校验：物品非空（至少一首）、各面不超载、封面可解析；验证：断言空物品拒绝、超载拒绝（✅ 2026-08-14 完成：空物品/面超载/local 无封面路径拒绝、placeholder 免路径通过）

## A6. 物品库持久化（modules/library/）

- [x] A6.1 schema.py —— SQLite 建表：`items`（id/name/type/cover_source/cover_path/tag/created_at/play_count）、`tracks`（id/item_id/side_label/position/path/title/artist/album/duration/format）；外键 + 索引（item_id、side_label）；schema_version 表；库文件 `music/items.db`（路径来自 base.json）；验证：探针建库后 `sqlite3` 查表结构（✅ 2026-08-14 完成：幂等建表 + 外键级联 + 双索引 + 版本表；DB_PATH 由 base.json music_dir 装配；探针 PRAGMA 表/列/索引断言通过）
- [x] A6.2 repository.py CRUD —— `save_item(item)`（事务插入/更新）、`load_all()`、`load_item(id)`、`delete_item(id)`（级联删 tracks）、`update_item(item)`；验证：探针 保存→加载→比对 回环 + 删除后查无（✅ 2026-08-14 完成：save 完整持久化（upsert+tracks 重建）/update 只改行不动 tracks/delete 级联；AB 面曲目与顺序回环断言）
- [x] A6.3 migration.py —— `schema_version` 读取 + 迁移函数注册表（dict: version → 函数）；第一版仅 v1 建库；验证：探针断言版本号与后续迁移点存在（✅ 2026-08-14 完成：MIGRATIONS={1: 建库} + get_schema_version（无表→0 容错）+ migrate 幂等；repository 连接自动迁移）
- [x] A6.4 path_check.py —— 加载时批量检测 `Track.is_missing()`，结果写入内存标记（Item 上 `missing_tracks` 集合），不阻塞加载；验证：探针移动一个文件后加载 → 断言 missing 标记（✅ 2026-08-14 完成：mark_missing 写 Item.missing_tracks（model.py 新增 set 字段，内存标记不落库）；移动文件后标记断言通过）

## A7. 封面服务（modules/cover/）

- [x] A7.1 providers.py —— `CoverProvider` 基类（`get_cover(item) -> str|None` 返回本地路径）+ 注册表（dict: 名称→类，从配置装配）；network 注册位留空注释说明；验证：断言注册表结构（✅ 2026-08-14 完成：ABC 基类 + 懒装配注册表（local/placeholder）+ resolve_cover 按 cover_source 解析 + network 预留注释；COVERS_DIR 由 base.json music_dir 装配）
- [x] A7.2 local_provider.py —— 用户选封面文件 → 复制到 `music/covers/`（UUID 命名）→ 写回 item.cover_path；验证：探针复制 + 文件存在断言（✅ 2026-08-14 完成：import_cover_file（uuid4().hex 命名保留扩展名 + 写回）+ LocalProvider.get_cover（路径有效才返回）；源缺失返回 None）
- [x] A7.3 placeholder_provider.py —— 无封面时返回 `data/placeholder.png` 路径；验证：断言返回路径存在（✅ 2026-08-14 完成：PlaceholderProvider 返回 data/placeholder.png（已生成 1×1 合法 PNG 69 字节随包入库）；文件缺失返回 None）

## A8. 生成编排（modules/generator/）

- [x] A8.1 generator.py 主流程 —— `generate(files, item_type, name, tag)`：read_tags_batch → 校验（A5.3）→ 顺序分配（A5.2）→ 封面解析（A7）→ create_item → save_item；返回 Item；验证：端到端探针生成一件真实物品并入库（✅ 2026-08-14 完成：端到端 5 首真实 wav 生成入库回环（名称/tag/曲目数/总时长 500s）；校验失败抛 GenerateError（分类业务异常）；封面参数 cover_source/cover_file 支持 local）
- [x] A8.2 regenerate.py 重新刻录 —— `regenerate(item, strategy=None)`：复用原歌池（原 path 列表）按新策略重新分配，生成**新 id** 物品；验证：断言新旧 id 不同、曲目集合相同（✅ 2026-08-14 完成：新 id + 原歌池重分配 + 继承封面；未知策略抛 GenerateError；入库回环断言）
- [x] A8.3 edit.py 编辑 —— `add_track(item, side_label, track)`（实时容量校验）、`remove_track`、`rename_item`、`change_tag`；验证：断言编辑后持久化正确（✅ 2026-08-14 完成：add 容量内成功/超容量拒绝中文原因、remove 按序号、rename/change_tag 走 update_item 不动 tracks；全部持久化回环断言）
- [x] A8.4 delete.py 删除 —— `delete(item)`：库删除 + 封面文件删除（仅当无其他 item 引用）；验证：探针删除后库/文件均消失（✅ 2026-08-14 完成：级联删库 + 封面引用检查（同 cover_path 其他物品存在时保留文件）；共享引用场景与无引用场景断言通过）

## A9. 播放核心（modules/playback/）

- [x] A9.1 events.py 事件契约 —— 事件名常量（PLAYBACK_STATE/TRACK_CHANGED/PROGRESS/SIDE_FLIPPED/ERROR）+ payload dataclass（各事件一个）；零 Qt 依赖；验证：断言构造与字段（✅ 2026-08-14 完成：5 事件名 + 5 payload dataclass，纯数据零 Qt）
- [x] A9.2 event_bus.py —— 极简订阅/发布（`subscribe(event, callback) -> unsubscribe`、`emit(event, payload)`）；验证：断言订阅回调与退订（✅ 2026-08-14 完成：subscribe 返回退订闭包 + 回调快照遍历 + 异常隔离（单回调出错不影响其他））
- [x] A9.3 engine.py 播放引擎 —— 封装 QMediaPlayer：`load_item(item)`（建立面内播放序列）、`play/pause/stop/seek(seconds)`、`current_track` 查询；**对外类型全部为项目模型，不暴露 QMediaPlayer 类型**；位置/状态变化经 event_bus 发事件；验证：offscreen 下 `QMediaPlayer` 无头初始化 + load 不崩溃（不出声）（✅ 2026-08-14 完成：内部延迟导入 QtMultimedia（offscreen 无头 OK）、对外 Track/Item 模型、play/pause/stop/seek/play_next、自然结束发 PLAYBACK_STATE(ended)、翻面发 SIDE_FLIPPED；auto_flip 读 settings）
- [x] A9.4 decoders/registry.py —— 解码器注册表：`register(exts, probe_fn, decoder)`、`resolve(path)`（扩展名 → 探测链 → 返回解码器）；验证：断言注册与 resolve 命中（✅ 2026-08-14 完成：DecoderEntry + 懒装配内置四格式 + resolve 魔数探测（未注册/探测失败 None））
- [x] A9.5 decoders/mp3.py、flac.py、wav.py、m4a.py —— 各模块声明 `EXTENSIONS` 与 `probe(path)`（基于 mutagen 或文件头魔数）；第一版解码实际走 QtMultimedia，模块为注册表占位与格式声明；验证：断言四种格式 resolve 正确（✅ 2026-08-14 完成：四格式魔数探测（ID3/0xFFE0、fLaC、RIFF+WAVE、ftyp）真实样本命中、.ogg 未注册不命中）
- [x] A9.6 queue.py 播放队列 —— 由 Item 生成：`[SideA.tracks..., SideB.tracks...]` + 当前索引 + 翻面标记；`next()/prev()` 边界处理（A 面末 → 自动翻面或停止，取决于 settings.auto_flip）；验证：状态机断言（含翻面路径）（✅ 2026-08-14 完成：build_queue 面内展平 + boundary；探针抓到 next() 普通推进分支覆盖翻面点的 bug，翻面判定前置后状态机 3/2 auto_flip 路径全对）
- [x] A9.7 progress.py 进度上报 —— 定时器（1s）读引擎位置 → emit PROGRESS；播放结束 → emit TRACK_CHANGED + 自动 next/stop；验证：探针监听事件流（✅ 2026-08-14 完成：QTimer 1s + _report 发 PROGRESS（位置/时长）+ 订阅 ended → play_next（失败 stop）；shutdown 退订防悬挂）

## A10. 事件桥接（ui/bridge/）

- [x] A10.1 event_bridge.py —— 订阅 core 事件 → 转 Qt 信号（stateChanged/trackChanged/progress/sideFlipped/error），桥内持有 QObject 载体；验证：offscreen 下 Qt 信号收发断言（✅ 2026-08-14 完成：_SignalCarrier(QObject) 五信号 + 五事件订阅转发（payload 安全读取）；五类信号收发断言通过）
- [x] A10.2 生命周期管理 —— 桥销毁时自动退订全部 core 事件（防悬挂回调）；验证：探针析构后 emit 无回调触发（✅ 2026-08-14 完成：shutdown() 退订全部（幂等）；退订后 emit 零回调 + 新桥不受影响（桥间隔离）断言通过）

## A11. UI 基础

- [x] A11.1 themes.py —— 全局 QSS（颜色/字体/控件样式来自 ui.json），`apply_theme(app)`；验证：offscreen 初始化 QApplication + apply_theme 不崩溃（✅ 2026-08-14 完成：QSS 模板由 ui.json colors/font_family 装配（ui.json 补 font_family 字段）；样式表生效断言）
- [x] A11.2 main_window.py —— 主窗：三视图容器（QSplitter/Stacked：物品库/置物架/唱机）+ 菜单栏骨架（文件→导入/生成、视图、设置）+ 状态栏（版本/播放状态）；验证：offscreen 初始化 + 控件存在性断言（✅ 2026-08-14 完成：TabWidget 左（物品库/置物架）+ 唱机右 QSplitter；菜单栏/状态栏/三视图 findChild 断言；GUI init OK）
- [x] A11.3 library_view.py 物品库视图 —— 网格/列表展示物品（缩略封面/名称/类型/Tag/播放次数）；选中 → 详情面板；右键菜单：播放/编辑/重新刻录/删除；验证：offscreen + 注入假 Item 渲染（✅ 2026-08-14 完成：列表（封面缩略 + 元信息）+ 详情面板 + 右键四菜单；注入渲染/选中详情/菜单结构断言）
- [x] A11.4 shelf_view.py 置物架视图 —— 按 Tag 分组（QGroupBox/分隔），组内物品卡片；点击卡片 → 播放信号（交 main_window 路由到 Deck）；验证：offscreen + 假数据分组渲染（✅ 2026-08-14 完成：tag 分组 QGroupBox + 卡片按钮 item_clicked 信号；分组渲染断言）
- [x] A11.5 deck_view.py 唱机视图 —— 封面大图 + 播放/暂停/上下曲按钮 + 进度条 + 翻面按钮（随 ItemType 显示 A/B）；绑定桥信号更新；验证：offscreen + 假状态更新断言（✅ 2026-08-14 完成：封面/控制/进度/翻面 + 桥信号绑定（state→按钮文本、progress→百分比、side→翻面、track→曲名）；事件驱动更新断言）
- [x] A11.6 导入对话框 —— "生成物品"流程 UI：文件多选（QFileDialog，过滤音频扩展名）→ 类型选择（下拉）→ 名称/Tag 输入 → 封面来源选择（local 文件 / 占位图）→ 调用 generator；验证：offscreen 手动走查对话框流程（不真正播放）（✅ 2026-08-14 完成：文件/类型/名称/Tag/封面来源收集 + GenerateError 提示 + 成功 accept；走查真实 wav 生成 2 曲入库（独立测试库）断言）

## A12. 拟物绘制（ui/widgets/）

- [x] A12.1 record_widget.py —— 按 ItemType.shape 绘制物品形态（circle：黑胶同心圆+封面中心；rect：磁带盒造型）；基础质感（渐变/阴影）；无动画；验证：offscreen 渲染 → 保存截图 → 人工核对（✅ 2026-08-14 完成：record_circle.png 核对通过（黑胶渐变圆盘+槽纹+中心封面圆）；record_rect.png 核对通过（磁带盒渐变壳+上窗+底部标签）；placeholder 红色符合预期）
- [x] A12.2 deck_widget.py 唱机 —— 转盘旋转（QTimer + QPainter 旋转，角度随播放状态）、唱针落下/抬起（插值动画）、播放中视觉反馈；动画时长读 ui.json；验证：offscreen 动画帧推进断言（角度变化）（✅ 2026-08-14 完成：deck_playing.png 核对通过（转盘圆盘+唱针播放态落下姿态）；角度推进/唱针插值断言通过）
- [x] A12.3 progress_widget.py —— 进度条 + 时间（mm:ss）；来自 PROGRESS 事件驱动；验证：offscreen 注入进度断言显示（✅ 2026-08-14 完成：on_progress(3000,10000) → bar=30%/时间 "0:03 / 0:10"；边界值断言）
- [x] A12.4 拖放 —— 置物架/物品库拖物品卡片到唱机区域 → 触发播放；验证：Qt 拖放事件模拟断言（✅ 2026-08-14 完成：ui/dnd 契约（encode/decode/is_item_drag 回环）；DraggableCardButton（shelf_view）+ _ItemList（library_view 拖出 mime 带 id）；deck_view dropEvent → item_dropped 信号断言）

## A13. 拟真度效果（ui/effects/）

- [x] A13.1 registry.py —— 按 effects.json 装配：读档位 → 生成效果器实例列表（wear/weathering/动画开关）；`apply(item_widget, level)` 接口；验证：断言三档装配结果与配置一致（✅ 2026-08-14 完成：effects.json 驱动（三档+强度+动画开关）；build_effects/apply/animations_enabled 全断言通过）
- [x] A13.2 wear.py —— 磨损/风化贴图：data/textures/ 下预置 PNG（噪点/划痕/泛黄），绘制时按强度叠加（QPainter drawImage + opacity）；验证：offscreen 截图人工核对（✅ 2026-08-14 完成：record_realistic.png 核对通过（磨损噪点+风化泛黄清晰可见）；record_refined.png 核对通过（轻磨损无泛黄）；两档差异清晰）
- [x] A13.3 动画联动 —— deck 动画启停随档位（concise 关、refined 转盘、realistic 全部）；验证：档位切换断言动画 timer 启停（✅ 2026-08-14 完成：set_animations_enabled(False) → timer 不启动/角度不推进/唱针瞬时落位；启用后 timer 启动/角度推进；修复 _tick 角度推进未检查动画开关 bug）
- [x] A13.4 settings 联动 —— 拟真度档位/自动翻面从 settings 读写（user_config.json），设置面板 UI；重启保持；验证：改档位 → 重启 → 断言持久化（✅ 2026-08-14 完成：SettingsDialog（档位下拉+自动翻面勾选）→ save_config 持久化 + 变更通知 + load_config 回显断言；main_window 设置菜单接线）

## A14. 集成与验收

- [x] A14.1 端到端走查 —— 导入 10+ 真实音频 → 生成 2 件物品（不同类型）→ 置物架陈列 → 唱机播放（进度/切歌/翻面/停止）→ 删除一件；验证：全程 offscreen 脚本 + 日志核对（✅ 2026-08-14 完成：12 个真实 wav → 黑胶 8 首 + CD 4 首 → 陈列分组 → 播放路由（按钮点击驱动）→ 切歌/翻面/暂停 → 删除；main_window 补播放路由/启动加载/closeEvent 清理）
- [x] A14.2 重启恢复 —— 退出后重启：物品库完整（数量/曲目/封面）、置物架 Tag 分组复原、拟真度档位保持；验证：两次启动状态比对断言（✅ 2026-08-14 完成：新窗口模拟重启 → 2 件物品/8 曲回环 + realistic/auto_flip 档位保持断言）
- [x] A14.3 缺失文件提示 —— 删除某曲目实体文件后播放 → ERROR 事件 → UI 提示"文件缺失"且不崩溃；验证：模拟场景断言（✅ 2026-08-14 完成：engine.play 增 is_missing 检查 → ERROR(file_missing) + 状态栏提示；当前曲目缺失拒绝播放不崩溃断言）
- [x] A14.4 日志验证 —— 生成/播放/错误全链路日志完整（logger 双输出）；验证：检查日志文件内容（✅ 2026-08-14 完成：generator/playback.engine 加 logger；生成成功/切歌/翻面/缺失 WARNING 全链路入 logs/mrsirmusic.log 断言）
- [x] A14.5 文档收尾 —— README 补全使用说明；z.plan.md 第八节验收清单逐项勾选；AGENTS.md 补运行/验证命令；验证：人工审核（✅ 2026-08-14 完成：README 补生成物品/播放/设置小节；z.plan 第八节 6 项全勾；AGENTS.md 补全量探针回归命令；A0-A14 全部完成）

---

## 执行说明

1. **顺序**：A0 → A4 等无 UI 依赖模块先行（可独立验证），A10 起 UI 在其后；A9 播放核心与 A10 起可并行开发（依赖事件契约）
2. **验证纪律**：每个任务完成后立即按"验证"方式执行，失败不进入下一任务
3. **依赖**：A1.2 是 main.py 前置；A6 依赖 A3/A4；A8 依赖 A3/A4/A5/A6/A7；A9 依赖 A3/A5 事件契约；A10 起 UI 依赖 A6/A9 + 事件契约
4. **命名约定**：正式文件注释禁 `.reference/` 标注；模块内 `#` 注释 + 文件尾 `# =====` 说明区
