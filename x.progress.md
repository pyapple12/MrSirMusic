# MrSirMusic 第一版开发任务清单（A 系列）

- 任务清单定稿：2026-08-14
- 依据：z.plan.md（MrSirMusic 项目方案 v1.0）
- 编号：A 系列（新项目首轮），组号 = 开发阶段，组内条目 `A{组}.{序号}`
- 约定：全部验证命令在项目根目录、`.venv` 解释器下执行；GUI 验证用 `QT_QPA_PLATFORM=offscreen` 免弹窗；正式文件注释禁止 `.reference/` 标注

---

## A0. 项目骨架与基础设施

- [ ] A0.1 初始化 git 仓库与 .gitignore —— 创建 `git init`；.gitignore 含：`.venv/`、`.reference/`、`.temp/`、`.opencode/`、`__pycache__/`、`*.py[cod]`、`.ruff_cache/`、`data/cache/`、以及**关键规则** `music/*` + `!music/.gitkeep`（忽略内容保留目录）；验证：`git status` 显示 music/.gitkeep 被跟踪、其余忽略
- [ ] A0.2 创建目录骨架 —— 按 z.plan.md 目录结构建全：config/static、utils、modules/items、modules/rules、modules/generator、modules/library、modules/tagging、modules/cover、modules/playback/decoders、ui/views、ui/widgets、ui/effects、ui/bridge、music/covers、data/textures、docs、.temp；各包放 `__init__.py`；验证：目录树与 z.plan.md 逐一比对
- [ ] A0.3 建立 .venv 与 requirements.txt —— `py -3.14 -m venv .venv`；requirements.txt 起步：PySide6、mutagen（pytest 可选后加）；验证：`.\.venv\Scripts\python.exe -c "import PySide6, mutagen"`
- [ ] A0.4 编写 main.py 入口 —— argparse（--version/-V + 默认 GUI）；版本号从 `config/static/base.json` 读取（先建最小 base.json）；PySide6 与 ui.main_window 延迟导入；函数下 `#` 注释 + 文件尾 `# =====` 说明区；验证：`python main.py --version` 输出正确；`python -c "import main"` 冒烟通过
- [ ] A0.5 编写 AGENTS.md（项目规范）—— 抄录 z.plan.md 第七节架构约束 + MrAutoDJ 系代码规范（函数注释规则/代码约定/Git 注意/Commit 规范/操作注意）；验证：人工审核与 z.plan.md 一致
- [ ] A0.6 编写 README.md —— 项目定位、第一版功能、运行方式（`python main.py`）、目录说明；验证：人工审核

## A1. 配置体系

- [ ] A1.1 static_config.py 加载器 —— json 读取 + 模块级缓存（`get_static_config()` 单例）+ 坏 JSON 容错（返回空 dict + 日志告警，不崩溃）；函数注释 + 文件尾说明区；验证：.temp 探针脚本加载全部 json 并打印结构
- [ ] A1.2 base.json —— 字段：version（"0.1.0"）、app_name（"MrSirMusic"）、sample_rate（44100）、channels（2）、music_dir（"music"）、data_dir（"data"）；验证：探针读取断言
- [ ] A1.3 config.json 引导映射表 —— 结构：`{"base": "base.json", "item_types": "item_types.json", "effects": "effects.json", "ui": "ui.json"}`；验证：static_config 按映射逐个加载成功
- [ ] A1.4 ui.json —— 字段起步：窗口尺寸、主色/辅色、动画时长（转盘转速、唱针落下时长）、列表列宽等；验证：探针读取断言
- [ ] A1.5 item_types.json —— 按 z.plan.md 第六节样例：vinyl/cassette/cd（name/side/minutes_per_side/shape）；验证：探针校验三条记录字段完整、side 均为合法面集合
- [ ] A1.6 effects.json —— 三档（concise/refined/realistic）：每档声明 `animations: bool`、`wear: bool`、`weathering: bool`、强度值；验证：探针断言三档齐全、默认档位存在
- [ ] A1.7 settings.py（用户配置）—— AppConfig dataclass（`realism_level`、`auto_flip`）+ 读写 `config/user_config.json`（缺省回退默认值，坏 JSON 不崩溃）+ 变更通知回调接口；验证：探针写→读→比对回环；删文件后回退默认

## A2. 工具层（utils/，零业务依赖）

- [ ] A2.1 logger.py —— 控制台 + 文件（logs/mrsirmusic.log）双输出，中文 UTF-8，模块名级别；验证：探针调用产生日志文件
- [ ] A2.2 file_utils.py —— pathlib 封装：`is_audio_file(path)`（按扩展名集合）、`ensure_dir(path)`、`safe_copy(src, dst)`、`file_exists(path)`；验证：断言各函数行为
- [ ] A2.3 retry.py —— `retry(times, delay)` 装饰器，指数退避，捕获指定异常，最终失败重抛；验证：mock 函数先失败后成功 → 重试次数断言
- [ ] A2.4 convert.py —— `format_duration(seconds)`（mm:ss）、`seconds_from_ms(ms)`、`to_float32(audio)`（占位，为后续音频处理预留）；验证：断言边界值（0、61、3599）

## A3. 领域模型（modules/items/）

- [ ] A3.1 ItemType —— 枚举或 dataclass：`vinyl/cassette/cd`，字段 name/sides（tuple）/minutes_per_side/shape；提供 `from_config(json)` 工厂（读 item_types.json）；验证：断言三个类型实例化 + 容量字段正确
- [ ] A3.2 Track —— dataclass：path/title/artist/album/duration_seconds/format；`from_tagging(TagData)` 工厂 + `is_missing()`（路径失效检测）；验证：断言构造与工厂
- [ ] A3.3 Side —— dataclass：`label`（"A"/"B"）、`tracks: list[Track]`；方法 `total_seconds()`、`add_track(track)`、`remove_track(track_id)`、`is_full(max_seconds)`；验证：断言容量边界（恰好满/超出）
- [ ] A3.4 Item —— dataclass：id（uuid）/name/type（ItemType）/cover_source/cover_path/tag/created_at/play_count/sides（dict[str, Side]）；方法 `all_tracks()`、`total_seconds()`、`side_for(label)`、`bump_play_count()`；验证：断言构造与聚合方法
- [ ] A3.5 items 工厂函数 —— `create_item(name, type, tag)`、`add_track_to_side(item, side_label, track)`（内部调用容量校验，返回成功/失败原因）、`remove_track(item, side_label, index)`；验证：断言全流程（含超容量拒绝）

## A4. 标签解析（modules/tagging/）

- [ ] A4.1 TagData 统一结构 —— dataclass：title/artist/album/duration_seconds/format/embedded_cover(可选 bytes)；验证：断言构造
- [ ] A4.2 read_tags(path) —— mutagen 封装：按扩展名分派（ID3/MP4/FLAC/WAVE），提取字段；时长优先取 mutagen 信息（无则用文件名兜底）；返回 TagData；验证：.temp 造真实样本（mp3/flac/wav/m4a 各一）断言字段
- [ ] A4.3 容错降级 —— 损坏文件/未知格式 → 返回 `empty_record()`（title=文件名，其余空，format=扩展名），不抛异常；验证：损坏样本（截断的 mp3）断言不崩溃
- [ ] A4.4 read_tags_batch(paths) —— 批量解析，单曲失败降级继续，返回 `list[TagData]`；验证：混合样本（含损坏）断言数量与降级项

## A5. 规则引擎（modules/rules/）

- [ ] A5.1 capacity.py —— `remaining_seconds(side, item_type)`、`fits(side, track, item_type) -> (bool, 原因)`；单曲超过单面容量 → 拒绝并说明；验证：断言边界（恰好/超出 1 秒/长曲）
- [ ] A5.2 side_allocator.py —— AB 面分配：第一版**顺序填充**（按添加顺序填 A 面，满后填 B 面）；预留策略参数（`ALLOC_STRATEGY` 常量，后续可加"平分/手动"）；验证：断言 8 首歌 3/5 分配结果
- [ ] A5.3 validate.py —— 选歌校验：重复曲目（同一 path 不入两面）、超容量、路径失效（missing）；返回校验结果列表（每条含原因）；验证：断言三类拒绝场景
- [ ] A5.4 generate_check.py —— 生成前完整性校验：物品非空（至少一首）、各面不超载、封面可解析；验证：断言空物品拒绝、超载拒绝

## A6. 物品库持久化（modules/library/）

- [ ] A6.1 schema.py —— SQLite 建表：`items`（id/name/type/cover_source/cover_path/tag/created_at/play_count）、`tracks`（id/item_id/side_label/position/path/title/artist/album/duration/format）；外键 + 索引（item_id、side_label）；schema_version 表；库文件 `music/items.db`（路径来自 base.json）；验证：探针建库后 `sqlite3` 查表结构
- [ ] A6.2 repository.py CRUD —— `save_item(item)`（事务插入/更新）、`load_all()`、`load_item(id)`、`delete_item(id)`（级联删 tracks）、`update_item(item)`；验证：探针 保存→加载→比对 回环 + 删除后查无
- [ ] A6.3 migration.py —— `schema_version` 读取 + 迁移函数注册表（dict: version → 函数）；第一版仅 v1 建库；验证：探针断言版本号与后续迁移点存在
- [ ] A6.4 path_check.py —— 加载时批量检测 `Track.is_missing()`，结果写入内存标记（Item 上 `missing_tracks` 集合），不阻塞加载；验证：探针移动一个文件后加载 → 断言 missing 标记

## A7. 封面服务（modules/cover/）

- [ ] A7.1 providers.py —— `CoverProvider` 基类（`get_cover(item) -> str|None` 返回本地路径）+ 注册表（dict: 名称→类，从配置装配）；network 注册位留空注释说明；验证：断言注册表结构
- [ ] A7.2 local_provider.py —— 用户选封面文件 → 复制到 `music/covers/`（UUID 命名）→ 写回 item.cover_path；验证：探针复制 + 文件存在断言
- [ ] A7.3 placeholder_provider.py —— 无封面时返回 `data/placeholder.png` 路径；验证：断言返回路径存在

## A8. 生成编排（modules/generator/）

- [ ] A8.1 generator.py 主流程 —— `generate(files, item_type, name, tag)`：read_tags_batch → 校验（A5.3）→ 顺序分配（A5.2）→ 封面解析（A7）→ create_item → save_item；返回 Item；验证：端到端探针生成一件真实物品并入库
- [ ] A8.2 regenerate.py 重新刻录 —— `regenerate(item, strategy=None)`：复用原歌池（原 path 列表）按新策略重新分配，生成**新 id** 物品；验证：断言新旧 id 不同、曲目集合相同
- [ ] A8.3 edit.py 编辑 —— `add_track(item, side_label, track)`（实时容量校验）、`remove_track`、`rename_item`、`change_tag`；验证：断言编辑后持久化正确
- [ ] A8.4 delete.py 删除 —— `delete(item)`：库删除 + 封面文件删除（仅当无其他 item 引用）；验证：探针删除后库/文件均消失

## A9. 播放核心（modules/playback/）

- [ ] A9.1 events.py 事件契约 —— 事件名常量（PLAYBACK_STATE/TRACK_CHANGED/PROGRESS/SIDE_FLIPPED/ERROR）+ payload dataclass（各事件一个）；零 Qt 依赖；验证：断言构造与字段
- [ ] A9.2 event_bus.py —— 极简订阅/发布（`subscribe(event, callback) -> unsubscribe`、`emit(event, payload)`）；验证：断言订阅回调与退订
- [ ] A9.3 engine.py 播放引擎 —— 封装 QMediaPlayer：`load_item(item)`（建立面内播放序列）、`play/pause/stop/seek(seconds)`、`current_track` 查询；**对外类型全部为项目模型，不暴露 QMediaPlayer 类型**；位置/状态变化经 event_bus 发事件；验证：offscreen 下 `QMediaPlayer` 无头初始化 + load 不崩溃（不出声）
- [ ] A9.4 decoders/registry.py —— 解码器注册表：`register(exts, probe_fn, decoder)`、`resolve(path)`（扩展名 → 探测链 → 返回解码器）；验证：断言注册与 resolve 命中
- [ ] A9.5 decoders/mp3.py、flac.py、wav.py、m4a.py —— 各模块声明 `EXTENSIONS` 与 `probe(path)`（基于 mutagen 或文件头魔数）；第一版解码实际走 QtMultimedia，模块为注册表占位与格式声明；验证：断言四种格式 resolve 正确
- [ ] A9.6 queue.py 播放队列 —— 由 Item 生成：`[SideA.tracks..., SideB.tracks...]` + 当前索引 + 翻面标记；`next()/prev()` 边界处理（A 面末 → 自动翻面或停止，取决于 settings.auto_flip）；验证：状态机断言（含翻面路径）
- [ ] A9.7 progress.py 进度上报 —— 定时器（1s）读引擎位置 → emit PROGRESS；播放结束 → emit TRACK_CHANGED + 自动 next/stop；验证：探针监听事件流

## B0. 事件桥接（ui/bridge/）

- [ ] B0.1 event_bridge.py —— 订阅 core 事件 → 转 Qt 信号（stateChanged/trackChanged/progress/sideFlipped/error），桥内持有 QObject 载体；验证：offscreen 下 Qt 信号收发断言
- [ ] B0.2 生命周期管理 —— 桥销毁时自动退订全部 core 事件（防悬挂回调）；验证：探针析构后 emit 无回调触发

## B1. UI 基础

- [ ] B1.1 themes.py —— 全局 QSS（颜色/字体/控件样式来自 ui.json），`apply_theme(app)`；验证：offscreen 初始化 QApplication + apply_theme 不崩溃
- [ ] B1.2 main_window.py —— 主窗：三视图容器（QSplitter/Stacked：物品库/置物架/唱机）+ 菜单栏骨架（文件→导入/生成、视图、设置）+ 状态栏（版本/播放状态）；验证：offscreen 初始化 + 控件存在性断言
- [ ] B1.3 library_view.py 物品库视图 —— 网格/列表展示物品（缩略封面/名称/类型/Tag/播放次数）；选中 → 详情面板；右键菜单：播放/编辑/重新刻录/删除；验证：offscreen + 注入假 Item 渲染
- [ ] B1.4 shelf_view.py 置物架视图 —— 按 Tag 分组（QGroupBox/分隔），组内物品卡片；点击卡片 → 播放信号（交 main_window 路由到 Deck）；验证：offscreen + 假数据分组渲染
- [ ] B1.5 deck_view.py 唱机视图 —— 封面大图 + 播放/暂停/上下曲按钮 + 进度条 + 翻面按钮（随 ItemType 显示 A/B）；绑定桥信号更新；验证：offscreen + 假状态更新断言
- [ ] B1.6 导入对话框 —— "生成物品"流程 UI：文件多选（QFileDialog，过滤音频扩展名）→ 类型选择（下拉）→ 名称/Tag 输入 → 封面来源选择（local 文件 / 占位图）→ 调用 generator；验证：offscreen 手动走查对话框流程（不真正播放）

## B2. 拟物绘制（ui/widgets/）

- [ ] B2.1 record_widget.py —— 按 ItemType.shape 绘制物品形态（circle：黑胶同心圆+封面中心；rect：磁带盒造型）；基础质感（渐变/阴影）；无动画；验证：offscreen 渲染 → 保存截图 → 人工核对（需多模态模型读图，见 AGENTS.md）
- [ ] B2.2 deck_widget.py 唱机 —— 转盘旋转（QTimer + QPainter 旋转，角度随播放状态）、唱针落下/抬起（插值动画）、播放中视觉反馈；动画时长读 ui.json；验证：offscreen 动画帧推进断言（角度变化）
- [ ] B2.3 progress_widget.py —— 进度条 + 时间（mm:ss）；来自 PROGRESS 事件驱动；验证：offscreen 注入进度断言显示
- [ ] B2.4 拖放 —— 置物架/物品库拖物品卡片到唱机区域 → 触发播放；验证：Qt 拖放事件模拟断言

## B3. 拟真度效果（ui/effects/）

- [ ] B3.1 registry.py —— 按 effects.json 装配：读档位 → 生成效果器实例列表（wear/weathering/动画开关）；`apply(item_widget, level)` 接口；验证：断言三档装配结果与配置一致
- [ ] B3.2 wear.py —— 磨损/风化贴图：data/textures/ 下预置 PNG（噪点/划痕/泛黄），绘制时按强度叠加（QPainter drawImage + opacity）；验证：offscreen 截图人工核对（需多模态模型）
- [ ] B3.3 动画联动 —— deck 动画启停随档位（concise 关、refined 转盘、realistic 全部）；验证：档位切换断言动画 timer 启停
- [ ] B3.4 settings 联动 —— 拟真度档位/自动翻面从 settings 读写（user_config.json），设置面板 UI；重启保持；验证：改档位 → 重启 → 断言持久化

## B4. 集成与验收

- [ ] B4.1 端到端走查 —— 导入 10+ 真实音频 → 生成 2 件物品（不同类型）→ 置物架陈列 → 唱机播放（进度/切歌/翻面/停止）→ 删除一件；验证：全程 offscreen 脚本 + 日志核对
- [ ] B4.2 重启恢复 —— 退出后重启：物品库完整（数量/曲目/封面）、置物架 Tag 分组复原、拟真度档位保持；验证：两次启动状态比对断言
- [ ] B4.3 缺失文件提示 —— 删除某曲目实体文件后播放 → ERROR 事件 → UI 提示"文件缺失"且不崩溃；验证：模拟场景断言
- [ ] B4.4 日志验证 —— 生成/播放/错误全链路日志完整（logger 双输出）；验证：检查日志文件内容
- [ ] B4.5 文档收尾 —— README 补全使用说明；z.plan.md 第八节验收清单逐项勾选；AGENTS.md 补运行/验证命令；验证：人工审核

---

## 执行说明

1. **顺序**：A0 → A4 等无 UI 依赖模块先行（可独立验证），B 系列 UI 在其后；A9 播放核心与 B 系列可并行开发（依赖事件契约）
2. **验证纪律**：每个任务完成后立即按"验证"方式执行，失败不进入下一任务
3. **依赖**：A1.2 是 main.py 前置；A6 依赖 A3/A4；A8 依赖 A3/A4/A5/A6/A7；A9 依赖 A3/A5 事件契约；B 系列依赖 A6/A9 + 事件契约
4. **命名约定**：正式文件注释禁 `.reference/` 标注；模块内 `#` 注释 + 文件尾 `# =====` 说明区
