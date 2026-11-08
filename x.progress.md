# MrSirMusic 开发任务清单

- 任务清单定稿：2026-08-14
- 依据：z.plan.md（MrSirMusic 项目方案 v1.0）
- 编号：A 系列（新项目首轮），组号 = 开发阶段，组内条目 `A{组}.{序号}`
- 约定：全部验证命令在项目根目录、`.venv` 解释器下执行；GUI 验证用 `QT_QPA_PLATFORM=offscreen` 免弹窗；正式文件注释禁止 `.reference/` 标注

> 文件职责（2026-11-05 对齐 CapsulePulse 范本）：任务清单与进度追踪，与 `z.plan.md` 配套——方案在 z.plan 附录展开，执行拆条在本文件勾选。结构：**`## 已完成 ✅` 区在前、`## 未完成` 区在后**，两区内部从上到下 = 从旧到新，新组追加在区末尾；已完成组全量保留、只增不删。
> 格式速查：任务组 `### PL{NNN}: {标题} [来源引用]`（来源：[z.plan#附录 PL{NNN}] / [problems#N] / [audit#A{NNN}]）；子任务 `- [ ] PL{NNN}.{序号} {标题} —— {做法}；验证：{检验方式}`；审计修复组 `### FIX{NNN}` 与审计附录 `A{NNN}` **恒同号**（条目内 `[P{级别}]` 标注）；小修组 `### PATCH{NNN}`——编号轨道三线与 A/FIX 绑定细则见 AGENTS「任务清单纪律」。
> 勾选注记：条目完成时改 `[x]`，句尾追加 `（YYYY-MM-DD 已验证：{一句话结论}）`——结论如实，不达标不降级宣布。
> 轨道切换说明：下方字母系列（A–H）为 2026-08-14 至 2026-11-05 的既有记录，**编号全量保留、仅作完成勾选依据**；自 2026-11-05 起新计划一律用 PL/FIX/PATCH 三线轨道，不再沿用字母系列。
> 修复记录：2026-11-07 发现 346d796 误将本文件截断为 23 行（`## 已完成 ✅` 区标题与 A→FIX006 历史组丢失、职责块与 FIX007 标题粘连）——已自 1289729 版本恢复历史区并回插 FIX007 组，内容逐字核对无失。

---

## 已完成 ✅

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
验证收尾（H7）：H7.1 全量 14 探针 PASS + 冒烟 + GUI 无头 init + --version 0.1.1.0；H7.2 截图核对（唱针几何/磁带卷轴/落针到位渲染，多模态读图通过）；H7.3 探针适配与补强（a6 迁移防御、a9 音频输出/seek_side/状态同步、a11 滑条值域、a12 惯性/落针/卷轴/scrub、a13 音效资源与装配）；H7.4 文档同步（w.study 第 10 节参考研读 / README 播放与音效说明 / 版本三方一致）

### PL001: 布局修缮与占位图重绘 [z.plan#附录 PL001] ✅

> 结果：三大观感硬伤全消（红占位图 → 128×128 暗纹音符占位 / 唱机区居中构图 + 按钮 96px 成排 + 滑条限宽 / 白块割裂全消含 Tab 页·滚动区·组框·输入件）+ 最小窗口 980×640 + 窄窗横向滚动条消除；全量 14 探针 PASS。评审依据 z.plan.md 附录 PL001。

- [x] PL001.1 占位图重绘 —— 新建 `.temp/make_placeholder.py`（离屏 QPixmap 绘制）：128×128 深胶木底径向渐变 + 三圈同心纹 + 音符刻痕 + 外缘描边，覆盖 `data/placeholder.png`；验证：读图断言 128×128 且中心 #342f29 ≠ #ff0000；截图中心呈暗纹音符（2026-11-05 已验证：尺寸/像素断言过 + 贴皮截图读图非红）
- [x] PL001.2 白块割裂修复 —— 定案根因 = QTabWidget 页面默认白（非最初候选）+ QScrollArea/QGroupBox 默认浅底；`ui/themes.py` QSS 补 QTabWidget::pane / QTabBar::tab / QScrollArea 透明 / QGroupBox surface 底 + padding / QAbstractItemView / QMenu / QScrollBar 深色（收口追加）；`ui.json` colors 增 surface/panel 两键；验证：重拍 01/02/08 读图无白色异质区（2026-11-05 已验证：三视图 + 对话框全协调）
- [x] PL001.3 deck_view 布局重构 —— `ui/views/deck_view.py`：art_row 对称 stretch 居中 + 组间距 16；四按钮 setFixedWidth(96) + spacing 12 居中成排；progress_widget maxWidth(420) 行居中；track_label 水平居中；验证：a12 追加 play_button.width ≤96 / 滑条限宽 / 标签居中三断言过 + 三档截图无巨条无大空洞（2026-11-05 已验证：读图通过）
- [x] PL001.4 置物架组框与卡片重设计 —— `ui.json` card_size [128,128]；`ui/views/shelf_view.py` DraggableCardButton 改收 Item（封面缩略 setIcon 56×56 + 两行文本 `名称\n形态·N曲`）+ 组框 margins(12,20,12,12) 修溢出 + 组间距 10；验证：截图 02 卡片不越界含缩略图（读图）+ a12 拖放回归 + a11 分组断言过（2026-11-05 已验证）
- [x] PL001.5 最小窗口尺寸 —— `ui/main_window.py` setMinimumSize(980, 640)；配套 `library_view` 关横向滚动条（窄窗行文本裁切优于横滚）+ QScrollBar 深色样式；验证：a11 追加 minimumSize 断言过 + 980×640 截图无横向滚动条（2026-11-05 已验证）
- [x] PL001.6 PL001 收口 —— `base.json` → 0.1.2、README 徽章 0.1.2、a1 断言同步；全量 14 探针 PASS + 冒烟 + --version 0.1.2 + 三档截图终审（读图）；草拟 commit 交用户（2026-11-05 已验证：全量 14/14 PASS，版本三方一致 0.1.2）

### PL002: 唱机形态分化与库列表行重设计 [z.plan#附录 PL002] ✅

> 结果：唱机区随载体三分形态（黑胶转盘+唱针 / 磁带仓观察窗双卷轴+双飞轮 / CD 碟舱 OddEven 镂空+封面环带+夹持爪），"播磁带时右侧是黑胶唱机"语义冲突消除；库列表行两行化；全量 14 探针 PASS。

- [x] PL002.1 共享绘制模块 —— 新建 `ui/widgets/parts.py`（`REEL_RADIUS_MIN/MAX` + `reel_factor(fill)` + `draw_reel(painter, center, radius, hub_radius, angle)`），record_widget 卷轴绘制/角速度计算改引共享（行为零变更）；验证：a12 卷轴断言原样过 + 冒烟含 ui.widgets.parts（2026-11-05 已验证）
- [x] PL002.2 类型分派骨架 —— `deck_widget.py`：`set_item_type(key, cover)`（未知键回退 vinyl）+ `_item_type` 分派 paintEvent；非 vinyl 唱针 mousePress 直接失败（零信号）；验证：a12 追加三形态 grab 非空 + CD 模拟 press/release 零落针断言过（2026-11-05 已验证）
- [x] PL002.3 磁带仓形态 —— `_paint_cassette_deck`：仓壳径向渐变 + 观察窗（parts.draw_reel 双卷轴随 `_side_progress` 胀缩）+ 双飞轮（`_angle×1.8` 辐条旋转）+ 走带线 + 四角螺丝 + 铭牌条；DeckWidget 增 `_reel_angle_l/_r` 于 `_tick` 恒线速推进（修复一次引用缺失段错误）；验证：磁带播放截图读图（卷轴/飞轮/壳体成立）（2026-11-05 已验证）
- [x] PL002.4 CD 舱形态 —— `_paint_cd`：银灰径向渐变碟面 + QPainterPath OddEvenFill 中心孔（8% 真镂空透窗底）+ 封面环带（22%..55% 环裁，无封面素环）+ 3 夹持爪 + 两圈淡槽纹；验证：CD 播放截图读图（碟面/孔/爪成立）（2026-11-05 已验证）
- [x] PL002.5 deck_view 接线与库列表行 —— `deck_view.load_item` 取 resolve_cover pixmap 注入 `set_item_type(item.type.key, cover)`；`library_view.set_items` 文本两行化 `名称\n形态·Tag·时长`（format_duration）；验证：a11 回归过（详情断言不受影响）+ 三形态截图读图（2026-11-05 已验证）
- [x] PL002.6 PL002 收口 —— `base.json` → 0.1.2（与 PL001 合并为一个内容版本提交）、README 徽章 + 播放段补形态说明、a1 断言同步；全量 14 探针 PASS + 冒烟 + --version 0.1.2 + 三形态截图终审（读图）；草拟 commit 交用户（2026-11-05 已验证：全量 14/14 PASS，版本三方一致 0.1.2）

### PL003: 主题精修与交互补充 [z.plan#附录 PL003] ✅

> 结果：色板四级分层（surface/panel/muted/disabled）+ QSS 全容器覆盖精修（禁用态/工具提示/勾选件 indicator）+ 导入对话框四分组 + 设置对话框说明文案与即时回显 + 桌面快捷键三项（空格/←→/F）；全量 14 探针 PASS。

- [x] PL003.1 色板分层扩展 —— `config/static/ui.json` colors 增 `muted`（#9A938A 弱文本）/ `disabled`（#45403A 禁用面）两键（surface/panel 已随 PL001 入位）；验证：贴皮截图读图定色（2026-11-05 已验证：对话框禁用浏览按钮/弱文本呈分层灰暖调）
- [x] PL003.2 QSS 精修 —— `ui/themes.py` 补 QPushButton:disabled（disabled 底 + muted 字）、QToolTip（panel 底）、QCheckBox/QRadioButton indicator（panel 底 + 选中 primary + 圆角）；说明区同步；验证：a13 回归过 + 截图读图（indicator 选中态呈 primary 实心）（2026-11-05 已验证）
- [x] PL003.3 导入对话框分组 —— `ui/import_dialog.py` 布局重排四个 QGroupBox（①音频文件 ②载体类型 ③命名与归类 ④封面来源，Tag 标签补"置物架分组依据"提示）+ `setMinimumHeight(420)`；字段/校验/信号零变更；验证：a11 导入走查断言原样过 + 截图 08 读图分组清晰（2026-11-05 已验证）
- [x] PL003.4 设置对话框增强 —— `ui/settings_dialog.py`：`_LEVEL_HINTS` 三档说明常量 + `currentTextChanged` 即时回显 + 自动翻面说明行 + `setMinimumWidth(340)`；验证：a13 持久化回归原样过 + 截图 09 读图（2026-11-05 已验证）
- [x] PL003.5 快捷键 —— `ui/main_window.py` `_wire_shortcuts()`：三项 QShortcut（空格 → deck_view._on_play_clicked、← → play_prev、→ → play_next、F → flip，WindowShortcut）；`deck_view.py` 播放控制四按钮 setFocusPolicy(NoFocus)；验证：a11 追加真音频链路 QTest.keyClick 断言（空格 playing↔paused 翻转）+ NoFocus 断言过（2026-11-05 已验证；调试修一处窗口未激活导致快捷键不派发——探针补 show+activateWindow）
- [x] PL003.6 PL003 收口 —— `base.json` → 0.1.4、README 徽章 0.1.4 + 快捷键表、a1 断言同步；全量 14 探针 PASS + 冒烟 + --version 0.1.4 + 全套截图终审（读图）；草拟 commit 交用户；真机核对三项（中文排版层级 / 高 DPI 清晰度 / 拖拽视觉反馈）留待用户日常使用复核（2026-11-05 已验证：全量 14/14 PASS，版本三方一致 0.1.4）

### FIX006: 第 6 轮审计修复 [audit#A006] ✅

> 结果：16 条 P 级（P2×4 + P3×12）全部落地；全量 14 探针 PASS + --version 0.1.4；反向验收逐条对照原问题（0 容量重刻被拦 / pending 清理 / 缺失切换 stopped / 切档底噪恢复 / 定时器自停 / scrub 冻结均已断言）。来源 z.plan.md 附录 A006。**播放计数链按默认决策移除**（用户未另行拍板），决策备忘登记 y.problem.md P3。

- [x] FIX006.1 [P2] regenerate 空物品入库/静默丢歌 —— placed 计数检查 + check_item 拦截（与 generate 主流程同口径）+ `_regenerate_item` 捕获 GenerateError 提示（2026-11-05 已验证：a8 断言 0 容量/容量缩水重刻均 GenerateError 且库零新行）
- [x] FIX006.2 [P2] _pending_seek 错误链残留 —— `_on_player_error` 补清 pending（2026-11-05 已验证：a9 断言 error 后 pending 为 None）
- [x] FIX006.3 [P2] 手动切缺失曲发声错位 —— missing 分支补 player.stop() + _emit_state("stopped")（E2.1 语义保持）（2026-11-05 已验证：a9 真音频 playing 切缺失曲 → stopped）
- [x] FIX006.4 [P2] set_level 底噪不恢复 —— 补 elif intensity>0 and _active → _start_ambience()（2026-11-05 已验证：a13 断言 concise→realistic 播放中底噪恢复）
- [x] FIX006.5 [P3] 拖针定时器空转 —— _tick 收敛自停（2026-11-05 已验证：a12 取消松手归位后 isActive False）
- [x] FIX006.6 [P3] scrub 时间文本跳变 —— on_progress 全量挂起（滑条+文本）+ 注释如实化（2026-11-05 已验证：a12 scrub 中文本冻结断言）
- [x] FIX006.7 [P3] 容错登记制补登记 —— AGENTS 补 6 条三要素登记 + delete.py 两处告警 + deck_widget/record_widget 回退告警 + progress.py 说明区 QTimer 特许声明（2026-11-05 已验证：登记与代码一一对应 + 冒烟）
- [x] FIX006.8 [P3] item_types shape 校验 —— 记录级校验提取 `_sanitize_item_types()` 独立函数（探针可单测）+ shape ∈ {circle,rect} 非法移除记录（2026-11-05 已验证：a1 断言坏 shape 三形态移除、合法保留）
- [x] FIX006.9 [P3] 磁带常量漂移 —— REEL_BASE_SPEED 入 parts 单源 + deck 侧 44/77 内联改引 parts 常量（2026-11-05 已验证：a12 卷轴断言原样过）
- [x] FIX006.10 [P3] 置物架缩略图走配置 —— ui.json 增 shelf_thumbnail_size=56 + 白名单补键 + shelf_view 改读配置（2026-11-05 已验证：a11 回归过）
- [x] FIX006.11 [P3] load_item 首曲缺失预检 —— setSource 前 is_missing 预检发 file_missing 中文分类（2026-11-05 已验证：a9 断言 ERROR category == file_missing）
- [x] FIX006.12 [P3] 秒→毫秒收敛 —— convert 增 ms_from_seconds（负值钳 0）+ engine×2/progress 改引（2026-11-05 已验证：a2 四边界断言）
- [x] FIX006.13 [P3] 死代码清理 —— 删 Side.remove_track/factory.remove_track/capacity.remaining_seconds/repository.load_item（保留为仓储完备 API 并注明，a6 回环依赖）/DEFAULT_REALISM_LEVEL 死 import×2；播放计数链按默认决策移除写链（update_item 去 play_count 写回，列保留读兼容）+ 决策备忘 y.problem.md P3（2026-11-05 已验证：grep 零引用 + a3/a6/a8 回归）
- [x] FIX006.14 [P3] import 纪律 —— delete.py 延迟 import 提升 + cover 基座下沉 modules/cover/base.py 断环（providers re-export 兼容既有导入路径）（2026-11-05 已验证：a7/a8 回归 + 冒烟含 cover.base）
- [x] FIX006.15 [P3] 文档一致性 —— AGENTS 版本句删时点快照、main.py 改三段式口径、代码注释 H 编号对齐 x.progress（H0.3→H0.2/H0.6→H0.3）（2026-11-05 已验证：grep 无四段式残留 + 编号对齐）
- [x] FIX006.16 [P3] toggle_play 公开化 —— deck_view.toggle_play() + 快捷键改调（2026-11-05 已验证：a11 快捷键断言原样过）
- [x] FIX006.17 验证收尾 —— 全量 14 探针 PASS + 冒烟 + --version 0.1.4 + 反向验收逐条对照原问题（见各组注记）；探针回归曾红灯一次（static_config setattr 缩进回归致全分类空），修复后绿灯——红灯证据留存于会话（2026-11-05 已验证：全量 14/14 PASS，版本三方一致 0.1.4）

### FIX007: 第 7 轮审计修复 [audit#A007] ✅

> 结果：6 条 P 级全部落地；全量 14 探针 PASS + --version 0.1.4；反向验收（playbackState StoppedState 断言即原问题对照）。来源 z.plan.md 附录 A007。
> 编号备注：A007/FIX007 同号绑定对齐轮次（恰为 max+1，无例外）；A006 观察项未提升，float 截断维持"需定案"标记。

- [x] FIX007.1 [P2] load_item 缺失分支停声 —— `modules/playback/engine.py` `load_item` 缺失 elif 分支（file_missing 预检块内）补 `if self._player is not None: self._player.stop()`（与 FIX006.3 同构；player 已在 :157 ensure）；验证：a9 追加断言（真音频 playing → load_item 缺失首曲物品 → 旧媒体停声/stopped 保持，扬声器不再出声）（2026-11-05 已验证：缺失 elif 分支补 player.stop()（与 FIX006.3 同构）——a9 真音频 playing 载缺失物品 → stopped 且 playbackState StoppedState）
- [x] FIX007.2 [P3] pending_seek 跨换源竞态 —— `engine.py` `play_next`/`play_prev`/`flip` 三入口进入时补 `self._pending_seek = None`（勿在 `_play_current` 内清防误杀合法挂起）；`stop()` 维持不清并在 seek_side 说明区记录"续播点即用户意图"语义决策；验证：a9 追加断言（seek_side 跨曲挂起后立即 play_prev → pending 为 None）（2026-11-05 已验证：play_next/play_prev/flip 三入口补 _pending_seek = None（_play_current 内不清防误杀）——a9 置 pending 后 play_prev → None）
- [x] FIX007.3 [P3] cover/providers 断环残留清理 —— `_build_registry` 两条函数内 import 提升顶部（环已断无依据）；删 `COVERS_DIR` re-export（全仓零消费，CoverProvider 保留供注解）+ 说明区 :46 口径同步；a7 探针核查 re-export 断言（如有一并适配）；验证：冒烟 + a7/a8 回归 + grep 零消费（2026-11-05 已验证：_build_registry import 提升顶部 + 删 COVERS_DIR 零消费 re-export + 说明区口径同步；a7 探针改引 cover.base——a7/a8 回归过）
- [x] FIX007.4 [P3] deck_view 秒→毫秒收敛 —— `ui/views/deck_view.py:193-195` 改引 `utils.convert.ms_from_seconds`（删内联 int(...*1000)）；验证：a11 桥绑定回归 + 冒烟（2026-11-05 已验证：_on_track 改引 utils.convert.ms_from_seconds——a11 回归过）
- [x] FIX007.5 [P3] FIX006 残留文档组 —— ① `model.py:122` 说明区删 remove_track 条目；② `model.py:124` 删"bump"字样；③ `factory.py:1` 头注改"创建空物品"；④ `edit.py:53` 说明区改"内联移除 + check_item 拒绝回滚 + save_item"；⑤ `repository.py:227` 尾注去"播放次数"；⑥ `progress_widget.py:82` 说明区改"scrub 中滑条与时间均挂起"；验证：grep 五文件无残留 + 冒烟（2026-11-05 已验证：文档残留 5 处全部如实化（model×2/factory 头注/edit 幽灵符号/repository 尾注/progress_widget 说明区）——grep 无残留）
- [x] FIX007.6 [P3] 不可达分支清理 —— `static_config.py:179-180` 删非 dict continue 双保险分支（上游 values_must_be_dict 已保证）；验证：a1 shape 校验断言原样过 + 冒烟（2026-11-05 已验证：_sanitize_item_types 非 dict continue 删除——a1 shape 校验断言原样过）
- [x] FIX007.7 验证收尾 —— 全量 14 探针（offscreen）+ 冒烟 + `--version` 0.1.4 一致 + a9 重点核对（FIX007.1/2 断言）+ 反向验收（原问题"旧媒体不停声"→验收"缺失载入后停声"）；结论如实回写勾选注记（2026-11-05 已验证：全量 14 探针 PASS + 冒烟 + --version 0.1.4 + 反向验收（playbackState StoppedState 断言即原问题对照））

### PL004: game-ui-ux 对照审查与补强 [z.plan#附录 PL004] ✅

> 结果：焦点体系三处歧义全消（初始焦点落库列表 / 滑条与卡片退出焦点链 / QSS 聚焦描边可见）+ 置物架组内改流式布局（最小窗多卡折行，横向滚动条消除）；全量 14 探针 PASS + 十图终审读图通过。

- [x] PL004.1 焦点体系审查与修复 —— 读 `.agents/skills/game-ui-ux/SKILL.md` 焦点导航章节作基线；核查点：①`ui/main_window.py` `_wire_shortcuts()` 四个 QShortcut 均为 WindowShortcut 语境且与 deck_view 四按钮 NoFocus（PL003.5）组合下空格无双触发回归；②主窗口 show 后初始焦点落点确定性（应落库列表或 deck，不悬空）；③`ui/views/shelf_view.py` 卡片按钮 Tab 可聚焦性与可见焦点框（若可聚焦则 `ui/themes.py` QSS 补 `:focus` 轮廓，取色走 colors 字典）；发现即修并逐点注记，需产品决策项转 y.problem.md；验证：a11 追加断言（快捷键 context 枚举值 + 四按钮 focusPolicy == NoFocus）+ GUI 无头初始化 + 冒烟（2026-11-07 已验证：红灯 6 项坐实后修复——初始焦点显式落库列表（原 QTabBar 捕获）/进度滑条 NoFocus（箭头键已全局绑切曲）/卡片 NoFocus（空格被全局占用、回车非对话框不触发，无键盘激活路径）/QSS 补 QPushButton:focus + QAbstractItemView:focus；a11 断言全绿）
- [x] PL004.2 缩放安全区审查与修复 —— 以最小窗 980×640 为基准逐面板核查：①deck_view 居中构图宽度预算（按钮 4×96 + spacing 3×12 + progress maxWidth 420 + 页边距）不溢出不挤压；②shelf_view 分组流式布局窄窗换行不溢出（横向滚动条关闭态保持）；③library_view 行文本 ElideMode 省略策略窄窗生效；发现即修（margin/spacing/elide 参数——可调项走 ui.json，视觉常量留模块）；验证：offscreen `resize(980,640)` 后 ui_review_shots 复拍 + 读图核对（无溢出/无挤压/无横向滚动条）+ a11 布局断言回归（2026-11-07 已验证：shelf 组内 QHBoxLayout 不换行系真缺陷——新增 `_FlowLayout` 流式布局修最小窗 8 卡横向滚动条（断言 + 读图折行正常）；deck 最小宽 460≥420 预算守卫；ElideRight 系 QAbstractItemView 默认已生效补断言固化）
- [x] PL004.3 事件驱动纪律审查 —— grep ui/ 全部 QTimer 使用点（白名单：deck_widget 动效 tick；sounds 应无定时器）与轮询刷新点；确认 UI 状态更新全部经桥信号驱动（进度挂起/翻面/切曲/错误展示零轮询）；发现轮询残留改事件驱动或登记豁免理由；验证：grep 结果注记于本条勾选注记 + a10/a11 回归 + 冒烟（2026-11-07 已验证：grep 全 ui/ 仅 deck_widget 与 record_widget 两处 QTimer——均为播放态门控的动效驱动器（record_widget 系 H6 卷轴动画，与 deck_widget 同类白名单）非状态轮询；状态栏/标签/进度全部经桥信号；a10/a11 回归 + 冒烟过）
- [x] PL004.4 PL004 收口 —— `config/static/base.json` version → `0.1.5` + README 徽章同步 + a1 探针版本断言同步；全量 14 探针（offscreen）+ 冒烟 + `--version` 一致 + ui_review_shots 九图终审读图 + 草拟 commit（feat: V0.1.5.1）交用户；验证：全量回归 PASS + 版本三方一致 + 读图记录（2026-11-07 已验证：全量 14/14 PASS + 冒烟 + --version 0.1.5 三方一致 + 十图终审读图全过（新增 10_shelf_min_980 最小窗流式换行图）；红灯证据存 .temp/pl004_red.py；commit 草案已交用户）

### PL005: Blender 拟物贴图管线 [z.plan#附录 PL005] ✅

> 结果：四贴图 Blender 烘焙入库（data/textures/，木纹平铺无缝经像素比对实证）+ 三形态/卡片贴图打底随档位差异化叠加 + 贴图缺失回退矢量（容错登记）；全量 14 探针 PASS + 十三图终审读图通过。环境门禁经用户确认后落地（Steam Blender 5.2.3 LTS + blender-mcp）。

- [x] PL005.1 环境就绪门（挂起闸） —— 本机安装 Blender 4.x + blender-mcp 插件（ahujasid/blender-mcp，Blender 侧 Connect 后监听 localhost:9876）；写 `.temp/probe_blender_env.py` 探活（socket connect 9876 + 场景对象写入/读取回环一次）；探活不过 → 向用户报告安装指引并挂起本组后续条目；验证：探活脚本 PASS（连接 + 读写回环）（2026-11-07 已验证：用户 Steam Blender 5.2.3 LTS + blender-mcp main 分支插件装入用户目录并持久启用（headless enable + save_userpref，兼容 5.x 无碍）；用户 GUI 点 Connect 后探针 ping/场景读取/写入回环全过——PL005.2-6 解封；插件经用户逐项确认后安装，Blender 本体系用户既有 Steam 安装）
- [x] PL005.2 贴图规格定案与制作方案 —— 四类贴图规格表（尺寸/光照/透明底/命名 `data/textures/{vinyl_disc,cassette_shell,cd_disc,walnut_panel}.png`）补写 z.plan 附录 PL005 规格小节；用 blender-director 路由 + materials/texture-workflow 出程序化节点方案（vinyl 沟槽=同心波纹+noise 微扰；CD=薄膜干涉色渐变；木纹=wave+noise warping 可平铺）；验证：规格表四文件命名/尺寸/光照无歧义且在附录（2026-11-07 已验证：规格表入 z.plan 附录 PL005（统一 512×512/正交俯拍/透明底或平铺）；档位接线定案 concise=false、refined/realistic=true 且 refined 跳手绘纹理细节防与烘焙纹理打架）
- [x] PL005.3 渲染产出四贴图 —— 经 Blender MCP 执行方案：每类一场景（统一三点光 key 左上、正交相机、film_transparent 透明底）渲染 512×512 PNG → qa-review 门禁（构图/曝光/木纹平铺无缝检查，不过返工）→ 产物入 `data/textures/`，.blend 源留 `.temp/blender_src/` 不入库；验证：四 PNG 存在 + 尺寸 512 断言 + 读图核对（多模态约定：读图前通知用户切模型）（2026-11-07 已验证：驱动器 `.temp/blender_src/build_textures.py` 经 execute_code 渲染五图（四贴图 + walnut 2×2 查缝图）；读图门禁过——黑胶近黑沟槽盘面/CD 银碟彩虹涡+孔镂空/磁带壳暖灰细纹/木纹暖棕波纹；平铺无缝像素实证（边缘差 0.024 ≈ 降噪底噪 < 任意列差 0.086）；产物 512×512 断言过并晋升 data/textures/；过程要点：节点构建 R_CHAIN 先于材质创建的顺序修正、色带需 elements.new、渲染集合平移 (50,50) 远离用户场景默认立方体（零接触）、贴图类改远场均匀光 + 发射材质烘焙（光照标定不再影响平铺亮度）、场景设置先读快照后还原）
- [x] PL005.4 deck_widget 贴图合成 —— `ui/widgets/deck_widget.py` 新增 `_texture_pixmap(key)` 惰性缓存加载器（QPixmap；缺失/损坏回退矢量绘制 + 告警一次——AGENTS 容错登记制补登记该降级点）；`_paint_vinyl`/`_paint_cassette_deck`/`_paint_cd` 改分层：贴图底图（按档位开关）→ 现有动态层（唱针/卷轴/高光/夹持爪）叠加；新增槽 `set_realism(level)`；验证：a12 追加断言（set_realism 三档切换绘制路径标记 + 移走贴图文件后 grab 不崩走回退）+ 冒烟（2026-11-07 已验证：加载器收口 `ui/widgets/parts.py` 单源（texture_pixmap 惰性缓存 + 每键告警一次 / texture_enabled 档位开关），deck 三形态贴图分层落地；a12 断言三档传导/512 在位/缓存 None 回退三形态 grab 不崩全过；AGENTS 容错登记制补"贴图加载失败回退矢量绘制"条目）
- [x] PL005.5 record_widget/shelf 接线与档位分发 —— `ui/widgets/record_widget.py` 同构接 `_texture_pixmap`（盘面/壳体贴图底，56px 缩略平滑缩放）；`ui/views/shelf_view.py` 卡片缩略图合成贴图底；`config/static/effects.json` 三档加 `texture` bool 键；`ui/main_window.py` `_apply_realism` 增 `set_realism` 分发到 deck_widget/record_widget；验证：a13 追加断言（档位切换 texture 键读取与传导 + 无 texture 键宽容回退）+ a1 配置回归 + 冒烟（2026-11-07 已验证：record 同构 + main_window 三处分发（deck/record/shelf）+ a13/a1 texture 键断言过 + a11 分发传导断言过；卡片贴图底走 QSS background-image 原生路径——卡片自绘 paintEvent 在 QSS 按钮层级存在 C++ 崩溃面（faulthandler 抓 access violation、子类覆写同体复刻即消，机制未明留档 .temp/pl005_bisect*.py）；过程修正 record_widget 漏 import Qt（realistic 档 NameError → QPainter 开放 → access violation 同源，一行修复））
- [x] PL005.6 PL005 收口 —— `config/static/base.json` version → `0.1.6` + README 徽章同步 + 拟物段补贴图管线说明 + a1 版本断言同步；全量 14 探针 + 冒烟 + `--version` 一致 + ui_review_shots 复拍（三形态 × 档位组合）+ 多模态读图终审 + AGENTS 容错登记制补录核查 + 草拟 commit（feat: V0.1.6.1）交用户；验证：全量回归 PASS + 版本三方一致 + 读图记录 + 登记制核查（2026-11-07 已验证：全量 14/14 PASS + 冒烟 + --version 0.1.6 三方一致；十三图终审读图过——refined 档贴图生效清晰（烘焙沟槽 vs 矢量渐变对照）、QSS 木纹卡片成立；realistic 档暴露 A13 风化叠加方形硬边为既有观感（非本次回归，此前截图未在 realistic 档拍过），留档观察不占编号；登记制补录核查过；commit 草案已交用户）

### PL006: IPC 契约与 Python Sidecar [z.plan#附录 PL006] ✅

> 结果：`sidecar/` 四件落地（protocol 信封单源 / app 进程线程模型 / commands 18 命令表 / __main__ 测试钩子）+ a15 协议探针全链 PASS；全量 15/15 + --version 0.2.0。modules/ 零改动纯委托。TDD 红灯→绿灯证据：红灯 = sidecar 不存在 ready 超时（ModuleNotFoundError → stdout EOF）；过程红两处 = 探针事件游标捞到 load_item 历史 stopped 态（改游标顺序消费 + playing 态过滤）与空文件列表被误判 bad_request（改放行业务 GenerateError → generate 分类，与 Qt UI 同语义）；终绿后全程稳定。

- [x] PL006.1 协议与骨架 —— 新建 `sidecar/` 包四件：`sidecar/protocol.py`（信封编解码——请求 `{id,cmd,params}` / 响应 `{id,ok,result|error{category,message}}` / 事件 `{event,data}`；JSON Lines 线帧 encode/decode；命令名与事件名常量单源）；`sidecar/app.py` `Session` 类（QCoreApplication 无头事件循环；bootstrap=静态配置快照+`repository.load_all`；stdin 读取线程按行分发到命令表；stdout 单写锁+逐行 flush；event_bus 订阅→事件泵）；`sidecar/commands.py`（命令注册表 dict + `dispatch(cmd,params)`）；`sidecar/__main__.py`（`main()` 入口 + `--db <path>`/`--config <path>` 测试钩子参数 → `set_db_path_for_tests`/配置路径覆盖）；验证：冒烟 import 含 sidecar 四模块 + ping 单命令子进程回环手测（2026-11-08 已验证：四模块冒烟过；线程模型落地 = stdin 守护线程→Qt 信号排队、命令/响应/事件写全部主线程；config/settings.py 补 set_config_path_for_tests 测试钩子——config 层对称 repository 惯例）
- [x] PL006.2 传输命令面 —— `sidecar/commands.py`：`ping`/`load_item{item_id}`/`transport_play|pause|stop|next|prev|flip`/`seek{seconds}`/`seek_side{fraction}` 九命令委托 `modules.playback.engine.PlaybackEngine`（引擎事件经 PL006.4 泵推送）；错误映射（未知命令/参数缺失→bad_request、未捕获异常→internal）；验证：a15 传输断言段（spawn 子进程→真 wave PCM wav load_item→play→playback_state=playing 事件→seek→stop 全链）（2026-11-08 已验证：a15 传输段全过——playing 态事件到达、seek_side 返回 applied bool）
- [x] PL006.3 库与生成命令面 —— `sidecar/commands.py` 续：`list_items`（load_all 全量+封面路径）/`delete_item`/`rename_item`/`change_tag`/`regenerate`/`generate{files,type_key,name,tag,cover_source}`（`GenerateError`→error{category:"generate"}中文消息透传）；全部写命令成功后发 `library_changed`；验证：a15 库断言段（临时库 generate→list 计数→rename→delete 级联→generate 空文件拒绝且 category=="generate"）（2026-11-08 已验证：a15 库段全过——generate 返回 id、library_changed 到达、list_items 单件结构含 sides/tracks/is_missing=False；空文件列表经 GenerateError → generate 分类）
- [x] PL006.4 配置与事件泵 —— `sidecar/commands.py` `get_bootstrap`（base/ui/effects/item_types/user_config/items 六合快照=前端唯一配置源）/`set_config{realism_level?,auto_flip?}`（`config.settings.save_config` 变更监听链路复用）；`sidecar/app.py` 事件泵订阅 event_bus 五事件→protocol 事件（progress/playback_state/track_changed/side_flipped/error）+ `ready` 握手（bootstrap 完成首发，携版本与库统计）+ `config_changed`；验证：a15 事件流断言（ready 首发顺序/set_config 后 config_changed 收到/progress 事件在播放中出现）（2026-11-08 已验证：a15 事件段全过——ready 首发携 version/items_count=0、config_changed 携 realistic、--config 路径落盘核验）
- [x] PL006.5 探针与登记 —— 新建 `.temp/probe_a15_sidecar.py`（`sys.executable -m sidecar --db <临时库> --config <临时配置>` spawn；握手/传输/库/错误分类/优雅退出五段断言；真音频 wave 模块 PCM；stdin EOF→进程 exit 0）；AGENTS 登记：结构与约定节增 sidecar 层条款（独立进程零 GUI、Qt 仅 engine/app 事件循环特许、stdio JSON Lines 协议）、运行与验证节增 a15 命令、环境陷阱增"子进程管道缓冲需逐行 flush"条；验证：a15 全绿 + 既有 14 探针回归全绿（modules 未动证据）（2026-11-08 已验证：a15 五段全过含 stdin EOF→exit 0；AGENTS 五处落地——分层条款改"ui/ 与 sidecar/app.py 两处 Qt 特许"、sidecar 层定义条、a15 入回归命令、环境陷阱"stdio 协议流纪律"、容错登记"侧车单命令异常收敛信封"）
- [x] PL006.6 PL006 收口 —— `config/static/base.json` version → `0.2.0`（0.2 主线首版）+ README 徽章 + a1 版本断言同步；全量回归（14+a15）+ 冒烟 + `--version` 一致；草拟 commit（feat: V0.2.0.1）交用户；验证：全量回归 PASS + 版本三方一致（2026-11-08 已验证：全量 15/15 PASS + 冒烟 + --version 0.2.0 三方一致；commit 草案已交用户）

## 未完成

### PL007: Tauri 壳与置物架试点 [z.plan#附录 PL007]

> 目标：Tauri 窗口 + Rust IPC 桥 + 置物架视图端到端闭环（点卡片出声）。依赖：PL006；环境门禁 PL007.1 不过全组挂起（不阻塞已收官件）。

- [ ] PL007.1 环境门禁（挂起闸） —— 探活三件：`cargo --version`（rustup+MSVC）、`node --version`≥22、`npm --version`；写 `.temp/probe_tauri_env.py` 汇总结论；不过 → 安装指引报告并挂起 PL007.2-6；验证：探活 PASS（三命令输出在案）
- [ ] PL007.2 Tauri 工程脚手架 —— 新建 `tauri/`（npm 工程：package.json=vite+vue3+typescript、vite.config.ts、src/ 前端源码；src-tauri/=Cargo.toml、tauri.conf.json（devUrl localhost:1420 + beforeDevCommand）、src-tauri/src/main.rs+lib.rs）；`.gitignore` 增 `tauri/target/`、`tauri/node_modules/`、`tauri/dist/`；验证：`npm install` + `npm run tauri dev` 空窗口起（人工）+ `cargo check` 过
- [ ] PL007.3 Rust IPC 桥 —— 新建 `tauri/src-tauri/src/sidecar.rs`：plugin-shell dev spawn `.venv/Scripts/python.exe -m sidecar`（工作目录=项目根，不经 externalBin——打包壳切换属发布线 problems#4）；stdout 泵线程（JSON Lines 解析→emit `sidecar://event`）；invoke 命令 `sidecar_cmd{cmd,params}`（自增 id + `Mutex<HashMap<u64,mpsc::Sender>>` 关联应答；超时 60s→error + 告警）；sidecar 退出监听→指数退避重启×3→emit `sidecar://dead`；验证：dev 模式 invoke ping→pong 回环 + kill sidecar 进程→自动重启成功→第 4 次失败 dead 事件
- [ ] PL007.4 前端骨架与主题桥 —— `tauri/src/`：`lib/ipc.ts`（invoke 封装 + `onSidecarEvent` 订阅）；`lib/theme.ts`（get_bootstrap→ui.json colors→`:root` CSS custom properties 注入）；`App.vue` + `styles/base.css`（CSS 变量消费，深棕主题对齐）；验证：dev 窗口背景/主色与 ui.json 一致（读图）+ items 计数与库一致
- [ ] PL007.5 置物架视图与最小传输条 —— `tauri/src/views/ShelfView.vue`（tag 分组卡片流 flex-wrap；封面 `convertFileSrc(cover_path)`；点击→load_item+transport_play）+ `tauri/src/components/DeckBar.vue`（播放/暂停按钮按 playback_state 切换、只读进度条接 progress、曲目两行文本接 track_changed）；验证：dev 真机清单（点卡片出声/进度走动/切曲文本/暂停态）+ 读图
- [ ] PL007.6 PL007 收口 —— `base.json` → `0.2.1` + README 新增"Web 版（开发中）"运行段（前置+启动命令）+ a1 断言同步；全量回归（14+a15）+ `cargo check` + 前端 `npm run build` 过；dev 窗口截图读图；AGENTS 容错登记三条（IPC 超时 60s 降级/sidecar 崩溃重启×3/ready 超时）核查补录；草拟 commit（feat: V0.2.1.1）交用户；验证：全量回归 PASS + 版本三方一致 + 读图记录

### PL008: 管理面完备 [z.plan#附录 PL008]

> 目标：库视图+三对话框+拖放快捷键+库同步——Web 版管理能力对齐 Qt 版（parity 清单首核）。依赖：PL007。

- [ ] PL008.1 物品库视图 —— `tauri/src/views/LibraryView.vue`（两行列表 名称/形态·Tag·时长 + 详情面板 + `components/ContextMenu.vue` 播放/编辑/重刻/删除→四命令）；验证：dev 清单（列表渲染与 Qt 版信息架构一致/详情随选中/右键四项可用）
- [ ] PL008.2 导入对话框 —— `tauri/src/dialogs/ImportDialog.vue`（四分组对齐 PL003.3 语义：①音频文件 ②载体类型 ③命名与归类 ④封面来源）+ src-tauri 引入 tauri-plugin-dialog（多选 mp3/flac/wav/m4a 过滤）；generate 命令提交 + GenerateError 分类提示不炸；验证：dev 走查（真文件导入→库刷新→错误提示）
- [ ] PL008.3 设置对话框 —— `tauri/src/dialogs/SettingsDialog.vue`（三档 select + auto_flip checkbox + 档位说明文案）→ set_config → config_changed 回显；验证：dev 走查（切档即时生效：deck 动画/贴图/音效响应）
- [ ] PL008.4 拖放快捷键与库同步 —— 卡片 HTML5 DnD（dataTransfer item_id）→ DeckBar 放置区 load_item+play；window keydown 快捷键 Space/←/→/F→transport 命令（输入框焦点豁免）；library_changed→三视图重取（保留旧视图直到成功）；验证：dev 走查（拖放播放/快捷键/删除后列表更新不闪烁）
- [ ] PL008.5 PL008 收口与 parity 首核 —— z.plan 附录 PL008 parity 清单九项逐项核对注记；`base.json` → `0.2.2` + README 补 Web 版功能清单 + a1 同步；全量回归（14+a15）+ 读图 + 草拟 commit（feat: V0.2.2.1）交用户；验证：全量回归 PASS + parity 九项全过 + 版本三方一致

### PL009: 拟物唱机 Web 化 [z.plan#附录 PL009]

> 目标：三形态拟物绘制+拖针+scrub+音效——迁移主战场（deck_widget/record_widget/parts/sounds 的 TS 等价物）。依赖：PL008。

- [ ] PL009.1 绘制基座 —— `tauri/src/components/deck/DeckStage.vue`（形态分派容器接 track_changed/state）+ `lib/deckClock.ts`（rAF 帧循环 composable：spinSpeed 惯性缓动 `speed+=(target-speed)*min(1,dt*2.2)` 移植 + 收敛自停 + reel 角度恒线速推进——常量与公式逐条自 `ui/widgets/parts.py`/`deck_widget.py` 移植并 TS 注明同源：REEL_BASE_SPEED/reel_factor/wind 900）；验证：dev 断言（播放启动缓动/停止收敛 rAF 自停）
- [ ] PL009.2 黑胶形态 —— `deck/VinylDeck.vue`：vinyl_disc.png 贴图底旋转（convertFileSrc）+ 唱针 SVG（`_PIVOT_X/_PIVOT_Y/_ARM_LENGTH/_ANGLE_START/_ANGLE_RANGE/_ANGLE_REST` 常量逐条移植）+ 面内进度→落针角映射 + realistic 档槽纹圈叠加（SVG circle 半透明）；验证：读图（贴图旋转/唱针几何与 Qt 版对照）
- [ ] PL009.3 拖针寻曲 —— VinylDeck pointer 三事件：27px 命中→atan2 ±180° 解卷→[_DRAG_MIN,_DRAG_MAX] 钳制→Shift×0.1 精调→[_DROP_MIN,_DROP_MAX] 有效窗判定→seek_side(fraction) / 窗外回臂；拖拽即发 transport_pause（提针停转语义）；验证：dev 交互清单（跨曲落针/无效窗回臂/Shift 精调——对照 Qt 版手感，主观项留真机调参注记）
- [ ] PL009.4 磁带仓与 CD —— `deck/CassetteDeck.vue`（cassette_shell.png 壳体贴图 + 观察窗 canvas `draw_reel` 移植：带卷/缠绕纹/花键 3 齿随角 + 双飞轮 SVG 旋转 + 走带线）+ `deck/CdDeck.vue`（cd_disc.png 贴图旋转——孔已烘焙镂空 + 封面环带 + 3 夹持爪 SVG）；验证：读图（两形态与 Qt 版对照）
- [ ] PL009.5 scrub 三态与 wind —— `tauri/src/components/ProgressSlider.vue`（range 0-1000；scrub 中挂起 progress 回写+时间文本预览；松手换算秒数 seek）；wind：scrub 方向→CassetteDeck 卷轴加速（±900°/s 基准移植）；验证：dev 清单（拖动预览/松手跳转/磁带 wind 方向正确）
- [ ] PL009.6 Web Audio 音效 —— `tauri/src/lib/sounds.ts`：fetch data/sounds/*.wav→AudioContext `decodeAudioData`；crackle 循环（loop bufferSource，vinyl 门控随播放态启停）；needle_drop/tape_mech 一次性；档位 gain=ambience_intensity 映射；贴图/音效缺失降级（img onerror→矢量路径 + console.warn 一次——容错登记语义平移）；验证：代码走查档位映射 + dev 听感留真机
- [ ] PL009.7 磨损效果器 —— `tauri/src/components/EffectOverlay.vue`（wear/weathering.png overlay + mix-blend-mode，档位 opacity 映射 wear_intensity/weathering_intensity）；验证：三档读图对照
- [ ] PL009.8 PL009 收口 —— `base.json` → `0.2.3` + README 拟物段补 Web 版说明 + a1 同步；全量回归（14+a15）+ 三档×三形态截图读图终审 + 拟物交互清单（拖针/scrub/wind/档位）注记；草拟 commit（feat: V0.2.3.1）交用户；验证：全量回归 PASS + 读图记录 + 版本三方一致

### PL010: 迁移收官 [z.plan#附录 PL010]

> 目标：dev 模式固化+文档/探针/登记收口——0.2 迁移线完成（dev 可用、parity 达标；**不含打包发布**）。依赖：PL009。

- [ ] PL010.1 dev 启动路径固化 —— `tauri/package.json` scripts 收口（`npm run tauri dev` 一键起壳+sidecar）；AGENTS 运行与验证节补全（sidecar 单独跑/Tauri dev/14+a15 探针命令）；验证：按 README 从零步骤走查（人工）
- [ ] PL010.2 AGENTS 架构节改写 —— 结构与约定节分层重写（tauri 壳+web 前端 ↔ stdio JSON Lines ↔ sidecar/→modules/；sidecar 独立进程零 GUI、Qt 仅 engine/app 循环特许；ui/ 与 tauri/src 双前端并存期条款）；验证：AGENTS 全文走查无新旧口径冲突
- [ ] PL010.3 README 与 w.study —— README 结构段双前端说明 + 当前形态如实（dev 迁移完成/无安装包/打包属后续线 problems#4）；w.study 第 11 节（Tauri 进程模型/stdio 桥/Rust 侧并发/Vue3 组合式研读）；验证：文档走查
- [ ] PL010.4 y.problem 登记与容错核查 —— problems#4 打包发布线/#5 Qt 壳去留/#6 Web Audio 直驱 三条登记（本立项时已预登记，本条核对状态与内容仍准确）；AGENTS 容错登记制核查（PL007 三条 + PL009 降级语义平移条目补全齐备）；验证：登记齐全对照
- [ ] PL010.5 PL010 收口 —— `base.json` → `0.2.4` + a1 同步；全量回归（14+a15）+ parity 终验（z.plan PL008 清单九项复核）+ dev 真机走查（冷启动/重启恢复/中文输入）+ 草拟 commit（feat: V0.2.4.1）交用户；验证：全量回归 PASS + parity 全过 + 版本三方一致
