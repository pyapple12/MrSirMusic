# MrSirMusic 开发任务清单

- 任务清单定稿：2026-08-14
- 依据：z.plan.md（MrSirMusic 项目方案 v1.0）
- 编号：A 系列（新项目首轮），组号 = 开发阶段，组内条目 `A{组}.{序号}`
- 约定：全部验证命令在项目根目录、`.venv` 解释器下执行；GUI 验证用 `QT_QPA_PLATFORM=offscreen` 免弹窗；正式文件注释禁止 `.reference/` 标注

---

## V0.1.0.0 开发任务清单 A系列

> 目标：50 项按 15 组（A0-A14 开发阶段）实施；验证：探针 A1-A14 全量 + 冒烟 + GUI init OK
> 依据：z.plan.md（MrSirMusic 项目方案 v1.0）；结果：A0-A14 全部完成（2026-08-14/15，版本 V0.1.0.0；全量 14 探针 PASS + 冒烟 OK + --version 0.1.0.0）

项目骨架（A0）：A0.1 git init + .gitignore（music/*+!music/.gitkeep 关键规则）；A0.2 目录骨架（17 目录 + 17 包断言）；A0.3 .venv（py-3.14）+ requirements（PySide6 6.11.1/mutagen 1.48.1）；A0.4 main.py 入口（argparse --version + 版本读 base.json + 延迟导入）；A0.5 AGENTS.md（架构约束 + 四段版本 + Commit 规范）；A0.6 README.md。

配置体系（A1）：A1.1 static_config 加载器（四分类 dataclass + 懒加载单例 + 坏 JSON 容错）；A1.2 base.json（六字段 + version 0.1.0.0）；A1.3 config.json 引导映射；A1.4 ui.json（窗口/颜色/动画/列宽）；A1.5 item_types.json（vinyl/cassette/cd 四字段）；A1.6 effects.json（三档 bool + 强度 + default_level）；A1.7 settings.py（AppConfig + user_config 读写回环 + 变更通知）。

工具层（A2）：A2.1 logger（双 handler UTF-8 文件）；A2.2 file_utils（扩展名白名单/safe_copy/ensure_dir）；A2.3 retry（指数退避 + exceptions 参数）；A2.4 convert（mm:ss 格式 + float32 占位）。

领域模型（A3）：A3.1 ItemType（frozen dataclass + from_config 宽容解析，22/30/80 分钟）；A3.2 Track（from_tagging 工厂 + is_missing）；A3.3 Side（total_seconds/add/remove/is_full 三态边界）；A3.4 Item（uuid/聚合方法/bump_play_count）；A3.5 工厂（create_item/add_track_to_side 容量校验/remove_track）。

标签解析（A4）：A4.1 TagData（六字段 + embedded_cover 预留）；A4.2 read_tags（四格式真实样本断言）；A4.3 容错降级（损坏/未知 → empty_record 不抛）；A4.4 read_tags_batch（混合样本 5 路径降级 2）。

规则引擎（A5）：A5.1 capacity（remaining/fits 边界三态）；A5.2 side_allocator（顺序填充 8 首 3/5 + 长曲跳过后索引重置 bug 修复）；A5.3 validate（重复/缺失/超容三类拒绝）；A5.4 generate_check（空/超载/封面解析拒绝）。

物品库（A6）：A6.1 schema（幂等建表 + 外键级联 + 双索引 + 版本表）；A6.2 repository CRUD（upsert 回环 + 级联删）；A6.3 migration（MIGRATIONS 注册表 + 幂等）；A6.4 path_check（mark_missing 内存标记不落库）。

封面服务（A7）：A7.1 providers（ABC + 懒装配注册表 + network 预留）；A7.2 local_provider（uuid 命名复制回写）；A7.3 placeholder_provider（占位图随包入库）。

生成编排（A8）：A8.1 generate 主流程（端到端 5 首 wav 入库回环 + GenerateError）；A8.2 regenerate（新 id + 原歌池重分配 + 继承封面）；A8.3 edit（add/remove/rename/change_tag 持久化）；A8.4 delete（级联删库 + 封面引用检查保留共享）。

播放核心（A9）：A9.1 事件契约（5 事件 + 5 payload 零 Qt）；A9.2 event_bus（退订闭包 + 异常隔离）；A9.3 engine（QMediaPlayer 封装对外零 Qt 类型 + offscreen 无头 + auto_flip）；A9.4 decoders/registry（懒装配 + 魔数探测）；A9.5 四格式解码器占位（ID3/fLaC/RIFF/ftyp 真实样本命中）；A9.6 queue（面内展平 + boundary + 翻面判定前置 bug 修复）；A9.7 progress（1s 定时器 + ended 自动 next + shutdown 退订）。

事件桥接（A10）：A10.1 event_bridge（QObject 载体五信号转发）；A10.2 生命周期（shutdown 幂等退订 + 桥间隔离）。

UI 基础（A11）：A11.1 themes（QSS 由 ui.json 装配）；A11.2 main_window（三视图 + 菜单栏/状态栏）；A11.3 library_view（列表 + 详情 + 右键四菜单）；A11.4 shelf_view（Tag 分组卡片 + item_clicked）；A11.5 deck_view（封面/控制/进度/翻面 + 桥绑定）；A11.6 导入对话框（文件/类型/名称/Tag/封面收集 + GenerateError 提示）。

拟物绘制（A12）：A12.1 record_widget（黑胶同心圆/磁带盒渐变，截图核对通过）；A12.2 deck_widget（转盘旋转 + 唱针插值，截图核对）；A12.3 progress_widget（on_progress 30%/时间文本）；A12.4 拖放（dnd 契约 + 卡片拖到唱机 item_dropped）。

拟真度效果（A13）：A13.1 registry（三档装配断言）；A13.2 wear（磨损噪点/风化泛黄截图核对两档差异）；A13.3 动画联动（档位启停 + _tick 检查动画开关 bug 修复）；A13.4 settings 联动（SettingsDialog 持久化 + 重启保持）。

集成验收（A14）：A14.1 端到端走查（12 wav → 黑胶 8 首 + CD 4 首 → 陈列 → 播放路由/切歌/翻面/删除）；A14.2 重启恢复（2 件/8 曲/档位保持）；A14.3 缺失文件提示（ERROR(file_missing) 不崩溃）；A14.4 日志验证（全链路入 logs）；A14.5 文档收尾（README/z.plan 第八节全勾/AGENTS.md 回归命令）。

---

## 执行说明

1. **顺序**：A0 → A4 等无 UI 依赖模块先行（可独立验证），A10 起 UI 在其后；A9 播放核心与 A10 起可并行开发（依赖事件契约）
2. **验证纪律**：每个任务完成后立即按"验证"方式执行，失败不进入下一任务
3. **依赖**：A1.2 是 main.py 前置；A6 依赖 A3/A4；A8 依赖 A3/A4/A5/A6/A7；A9 依赖 A3/A5 事件契约；A10 起 UI 依赖 A6/A9 + 事件契约
4. **命名约定**：正式文件注释禁 `.reference/` 标注；模块内 `#` 注释 + 文件尾 `# =====` 说明区

## 第 1 轮审计整改完成（B 系列，2026-08-14 审计，2026-08-15 已实施，版本 V0.1.0.1）

> 目标：49 条 P 级按分组整改；全量回归 18/18
> 依据：z.plan.md 附录 A001；结果：B0-B4 全部完成（探针 15 项行为验证 + 冒烟 51 模块）

正确性（B0）：B0.1 播放三路径缺失检查（统一 \_play_current 抽公共方法）；B0.2 生成空物品拦截（files 空校验 + check_item 入库前校验）；B0.3 DB_PATH 单点收敛（set/get_db_path + unlink 路径消毒）；B0.4 拟真度档位接线（监听器 + 启动应用）；B0.5 主题应用接线（run_gui 一行）；B0.6 右键三信号路由（edit/regenerate/delete + refresh）；B0.7 停止后唱针抬起（瞬时置 0）；B0.8 换物品旧封面残留（RecordWidget 全量重绘架构性解决）；B0.9 queue 空 A 面 boundary（first_side 标记修正）；B0.10 编辑加曲防重（全范围 path 查重）；B0.11 文本分发改状态字段（O-1）；B0.12 容量边界统一（O-3 先加后比）；B0.13 dragMoveEvent 补实现；B0.14 拟物控件接入 DeckView（RecordWidget/DeckWidget/ProgressWidget + 桥联动）。
去重（B1）：B1.1 main.py 版本单通道（单例 + isinstance 校验含 O-5）；B1.2 项目根派生收敛（utils/paths.py 新建三处收敛）；B1.3 local_provider 流式复制（copyfileobj）；B1.4 进度换算去重（convert.progress_percent 单点）。
配置化（B2）：B2.1 data_dir 键消费；B2.2 日志外置（logs_dir/log_level）；B2.3 扩展名单源（注册表导出 + 交叉告警）；B2.4 静态配置类型校验（白名单 + \_sanitize_types）；B2.5 配置死键处置（library_column_widths 删）；B2.6 默认档位单源（default_level）；B2.7 主题色外置（6 键）；B2.8 尺寸/阈值外置（7 处消费点）；B2.9 进度间隔外置（O-4）。
清理（B3）：B3.1 死代码处置（删除/标注预留）；B3.2 注释失实修正；B3.3 retry 参数校验（抛 ValueError）；B3.4 档位白名单校验 + 保存失败日志；B3.5 delete.py 清理（COVERS_DIR 校验）；B3.6 migrate 执行缓存（\_migrated_path 按库路径）；B3.7 双排序移除（assume_sorted）；B3.8 event_bus 可观测性 + 订阅去重；B3.9 懒装配竞态锁（双重检查）；B3.10 未知 type 日志；B3.11 封面导入失败日志；B3.12 load_item 配置缓存（\_config_cache）；B3.13 duration 用播放器（标签兜底）；B3.14 resolve 区分原因（not_registered/probe_failed/ok）；B3.15 wear 失败缓存（None 也缓存）；B3.16 intensity 宽容转换；B3.17 bridge **del** 兜底退订；B3.18 shelf 空标签重建（O-2）；B3.19 版本类型校验（O-5）。
验证收尾（B4）：B4.1 全量 18 探针 PASS + 冒烟 55 模块 + --version 0.1.0.1；B4.2 端到端复走（probe_a14_integration）；B4.3 文档同步（附录 A001 状态行更新）。

## 第 2 轮审计整改完成（C 系列，2026-08-15 审计，2026-08-15 已实施，版本 V0.1.0.2）

> 目标：17 条 P 级按分组整改；全量回归 22/22
> 依据：z.plan.md 附录 A002；结果：C0-C4 全部完成（探针 12 项行为验证 + 冒烟 55 模块）

正确性（C0）：C0.1 档位切换动画冻结修复（enabled 且 playing 补 timer.start）；C0.2 errorOccurred 连接（ERROR(playback_error) + 日志）；C0.3 封面残留补修（set_item 先清空再加载）；C0.4 封面失败语义统一（降级 placeholder 生成继续）；C0.5 白名单覆盖补全（字符串键 + 容器键类型校验）。
去重（C1）：C1.1 migration 路径单点（get_db_path 延迟 import 结构例外）；C1.2 retry 类型边界（times 排除 bool）；C1.3 settings 路径收敛 + 回调可观测。
配置化（C2）：C2.1 probe 流式读取（四格式 f.read 12 字节）；C2.2 import_dialog 底层兜底（except Exception → QMessageBox）；C2.3 progress_percent 钳制（min(100)）；C2.4 回退字面量收敛（DEFAULT_REALISM_LEVEL 单源）。
清理（C3）：C3.1 \_connect 目录确保（mkdir parents）；C3.2 event_bus bound method 去重（三元组判重键）；C3.3 注释/文案修正。
验证收尾（C4）：C4.1 全量 22 探针 PASS + 冒烟 + --version 0.1.0.2；C4.2 端到端复走；C4.3 文档同步（附录 A002 状态行 + 版本/README/探针断言同步）。

## 第 3 轮审计整改完成（D 系列，2026-08-15 审计，2026-08-15 已实施，版本 V0.1.0.3）

> 目标：12 条 P 级按分组整改；全量回归 24/24
> 依据：z.plan.md 附录 A003；结果：D0-D4 全部完成（探针 6 项行为验证 + 冒烟 55 模块）

正确性（D0）：D0.1 白名单覆盖面补全（\_sanitize_types 重构四分类：effects/item_types 容器/嵌套数值递归）；D0.2 log_level 值域校验（\_VALID_LOG_LEVELS + valid_values）；D0.3 progress_percent 下界钳制（max(0, min(100))）；D0.4 SIDE_FLIPPED 单次发射（\_just_flipped 标记）；D0.5 ERROR 后状态同步（非 NoError 同步 stopped）。
去重（D1）：D1.1 migration 死 import 清理（DB_PATH 移除）。
配置化（D2）：D2.1 logger 说明区修正（已外置描述）。
清理（D3）：本轮无 P3 项（观察项维持参考级）。
验证收尾（D4）：D4.1 全量 24 探针 PASS + 冒烟 + --version 0.1.0.3；D4.2 端到端复走；D4.3 文档同步（附录 A003 状态行 + 版本/README/探针断言同步）。

## 第 4 轮审计整改完成（E 系列，2026-08-15 审计，2026-08-15 已实施，版本 V0.1.0.4）

> 目标：15 条 P 级按分组整改；全量回归 26/26
> 依据：z.plan.md 附录 A004；结果：E0-E4 全部完成（探针 12 项行为验证 + 冒烟 55 模块）

正确性（E0）：E0.1 drag_threshold 白名单补全；E0.2 card_size 长度契约（过滤后长度≠2 整键移除）；E0.3 animation 值域下界（>0 + 消费端 max(1) 对称保护）；E0.4 翻面按钮态同步（\_on_track 按 side 同步 + 单面禁用）；E0.5 错误提示不被覆盖（message_label 独立于 state_label）；E0.6 item_types 记录内数值校验；E0.7 default_level 值域校验（∈ levels 键）。
去重（E1）：E1.1 flip 失败标记复位（回滚 A 面末 + 双复位）；E1.2 load_item 状态复位（字段复位不发事件）。
配置化（E2）：E2.1 missing 曲目跳过语义（回滚方案会卡死缺失曲目，改 \_track 保持一致 + index 推进可跳过）；E2.2 说明区同步组（migration/progress/static_config/convert/retry 5 文件）。
清理（E3）：E3.1 main_window 顶层 import（三处延迟导入改顶部）。
验证收尾（E4）：E4.1 全量 26 探针 PASS + 冒烟 + --version 0.1.0.4；E4.2 端到端复走；E4.3 文档同步（附录 A004 状态行 + 版本/README/探针断言同步）。

## 第 5 轮审计整改完成（F 系列，2026-08-15 审计，2026-08-15 已实施，版本 V0.1.0.5）

> 目标：15 条 P 级按分组整改；全量回归 28/28
> 依据：z.plan.md 附录 A005；结果：F0-F4 全部完成（探针 12 项行为验证 + 冒烟 55 模块；cover 模块补入库）

正确性（F0）：F0.1 cover 模块补入库（.gitignore 裸 cover/ 改 /coverage/ + git add -f）；F0.2 missing 分支发 TRACK_CHANGED（UI 展示同步）；F0.3 flip 回滚同步 \_track（+ \_emit_track 补发）；F0.4 CD 单面按钮禁用修复（side=="A" and len(sides)>1）；F0.5 side 字段校验（list + A/B 白名单）；F0.6 回退链自引用修复（\_fallback_level 动态回退 levels 首键）。
去重（F1）：F1.1 card_size/minutes_per_side >0 下界；F1.2 \_just_flipped 复位补全（play_next 失败对称）。
配置化（F2）：F2.1 编辑路径空物品拦截（remove_track 后 check_item + 回滚）；F2.2 settings 说明区补全（三项函数/常量）。
清理（F3）：F3.1 空 A 面 side 推导修正（boundary>0 守卫）；F3.2 顶层数值键 >0 下界（drag_threshold/spin_tick_ms）。
验证收尾（F4）：F4.1 全量 28 探针 PASS + 冒烟 + --version 0.1.0.5；F4.2 端到端复走；F4.3 文档同步（附录 A005 状态行 + 版本/README/探针断言同步）。

## 第 6 轮审计整改完成（G 系列，2026-08-15 审计，2026-08-15 已实施，版本 V0.1.0.6）

> 目标：9 条按分组整改（观察项升级 3 + 价值权衡 2 + 顺手修 1 + 验证收尾 3）；全量回归 30/30
> 依据：z.plan.md 观察项豁免定案清单"已升级转出"；结果：G0-G4 全部完成（探针 6 项行为验证 + 冒烟 55 模块）

正确性（G0）：G0.1 0 时长曲目拦截（validate 四类检查含 duration<=0）；G0.2 生成丢弃曲目中止提示（placed 对比抛 GenerateError）；G0.3 封面导入原子写（tmp + os.replace + 异常清理）。
配置化（G2）：G2.1 格式清单双向告警（registered 集合反向差集告警）。
清理（G3）：G3.1 migrate 连接泄漏 finally（异常 close + 上抛）；G3.2 message_label 清除时机（\_play_item 载入前 clear）。
验证收尾（G4）：G4.1 全量 30 探针 PASS + 冒烟 + --version 0.1.0.6；G4.2 端到端复走；G4.3 文档同步（z.plan 豁免清单"已升级转出"标注 + 版本/README/探针断言同步）

## 拟物升级 + 第 7 轮体检整改完成（H 系列，2026-11-05 体检 + 实施版本 V0.1.1.0）

> 目标：基于三个新参考项目（.reference/Spun、Vinyl-Vue、RecordPlayer，研读记录见 w.study.md 第 10 节）做拟物交互升级，并合并第 7 轮体检结果（mimosa 深度安全扫描 0 发现 / 24 依赖包无告警；代码审查 P0×1 + P1×1 + P2×2）；全量回归 14/14
> 体检来源：mimosa 深度扫描 + code-reviewer 聚焦审查（playback/拟物 UI/config 白名单）+ F:\Collection 知识技能（game-feel/audio-design）设计约束；结果：H0-H6 全部完成（探针 14 全量回归 PASS + 冒烟 + GUI 无头 init + 截图核对通过）

体检修复（H0）：H0.1 P0 播放静音（QMediaPlayer 从未挂 QAudioOutput——Qt6 不挂输出解码推进但全程无声，6 轮审计盲区；engine._ensure_player 补挂 + 持引用防 GC）；H0.2 P2 load_item 裸赋值不发事件（播放中换物品 UI 卡"播放中"，改走 _emit_state("stopped")）；H0.3 P2 closeEvent 未停引擎（首行补 engine.stop()）；H0.4 seek 在 ended 后补发 paused（媒体拉回 LoadedMedia 但按钮态卡死）；H0.5 P1 迁移循环陷阱（循环条件固定与初始版本比较，未来注册 v2 时新库必重复 ALTER 崩溃——每次迁移后重读版本；探针 a6 补模拟用例）
面内寻曲引擎链路（H1）：TrackChangedPayload 扩展 side_offset_seconds/side_total_seconds（可选默认 None，宽容降级）；engine._side_range/_side_durations（面内索引区间 + 时长表，全有效才启用面内映射）；engine.seek_side(fraction)（面内时间比例 → 定位曲目/曲内偏移：同曲 seek、跨曲换索引 + 挂起跳转待 LoadedMedia 应用；只在当前面内——唱针不跨面；时长缺失降级单曲内比例）
配置扩展（H2）：item_types.json 加 spin_ms_per_rev（vinyl 1800≈33⅓rpm / cassette 2500 / cd 4000）；ItemType 加可选字段 + from_config 宽容解析（非法回退 2000）；static_config item_types 记录内可选数值键校验（非法移除键保留记录）；effects.json 三档加 ambience_intensity（0/0.4/0.7）
音效资源与套件（H3）：.temp/make_sounds.py 纯标准库合成 data/sounds/*.wav（vinyl_crackle 9.6s 循环底噪 + 首尾交叉淡化 / needle_drop 0.3s / tape_mech 0.28s 三撞击——算法移植见 w.study 10.1）；ui/sounds.py SoundKit（QSoundEffect 封装，fail-soft 整体降级：无声卡/offscreen 自动禁用；底噪循环随播放态启停，载体门控 vinyl only；落针/机械声一次性；档位响度 ambience_intensity）；main_window 接线（set_level/set_media_kind/状态迁移沿落针音/SIDE_FLIPPED 落针音/播放中磁带换曲机械声）
唱针真实化 + 拖拽寻曲（H4）：deck_widget 重构——枢轴/臂杆/唱头/配重真实几何（硬阴影技法），唱针角 = 落针角 + 扫过角×面内进度；mousePress/Move/Release（尖端 27px 命中 → atan2 解卷拖拽 → Shift 精调 → 钳制 → 有效窗落针发 needle_dropped / 窗外静默取消）；拖针即暂停（提针停转拟物语义）；转盘启停惯性缓动（speed += (target-speed)×min(1, dt×2.2)）；set_progress/set_spin_ms 注入；deck_view 面内比例驱动唱针
进度滑条 scrub（H5）：progress_widget QProgressBar → QSlider（0-1000，themes QSlider QSS 现成）；scrub_started/moved/released 三态信号（scrub 中挂起 PROGRESS 回写防覆盖，松手发曲内秒数）；deck_view 换算 seek_requested；磁带 wind 视觉按拖动方向
磁带卷轴动画（H6）：record_widget 升级——观察窗内双卷带（半径按带卷物理因子胀缩）+ 缠绕纹理 + 花键 hub 3 齿随角度旋转 + 走带路径线；恒线速模型（角速度 = 基准/半径因子，卷多转慢）；set_playing/set_animations_enabled/set_reel_progress/set_wind；定时器仅唱机实例播放中启动（置物架卡片保持静态）；scrub 方向驱动 wind 快进/倒带视觉
验证收尾（H7）：H7.1 全量 14 探针 PASS + 冒烟 + GUI 无头 init + --version 0.1.1.0；H7.2 截图核对（唱针几何/磁带卷轴/落针到位渲染，多模态读图通过）；H7.3 探针适配与补强（a6 迁移防御、a9 音频输出/seek_side/状态同步、a11 滑条值域、a12 惯性/落针/卷轴/scrub、a13 音效资源与装配）；H7.4 文档同步（w.study 第 10 节参考研读 / README 播放与音效说明 / 版本三方一致）。
