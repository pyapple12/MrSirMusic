# MrSirMusic 项目方案 v1.0

- 方案定稿：2026-08-14
- 状态：📌 待开发（任务清单见 x.progress.md）
- 前置研读：同目录 `w.study.md`（webamp / audacious / RetroMusicPlayer / kelp-player / SpotAmp 五仓库深度报告，本方案沿用其架构模式）

---

## 一、项目定位

**拟物音乐播放器**：不使用文件夹/播放列表，而是通过**拟物物品**（黑胶/磁带/CD）承载音乐。

- 物品由用户手动选歌**生成**（硬容量约束），持久保存在**物品库**（`music/`）
- 物品可陈列于**置物架**（按需求 Tag 分类），点选放入**拟物唱机**播放
- 播放器能力 = 播放音乐 + 按需求生成播放物品

**与常规播放器的本质区别**：播放集合实体化为"可拥有、有容量约束、有正反面、可修正、可收藏"的拟物对象。

## 二、第一版范围

| 能力   | 范围                                                               |
| ------ | ------------------------------------------------------------------ |
| 播放   | mp3 / flac / wav / m4a；播放/暂停/上下曲/进度/翻面（随拟真度）     |
| 生成   | 用户选文件 → 选载体类型 → 容量硬校验 → AB 面分配 → 封面 → 入库     |
| 修正   | 重新刻录变体 / 手动换歌编辑 / 删除物品                             |
| 收藏   | 物品库（SQLite）+ 置物架按 Tag 分类陈列                            |
| 封面   | local（用户提供）+ placeholder（占位图）；network 留接口**不实现** |
| 拟真度 | 三档（简洁/精致/真实），由 effects.json 驱动，ui/effects 实现      |
| 不做   | LLM 选曲、网络封面、Web/Godot UI、置物架更换（均留扩展位）         |

## 三、决策总表

| 项       | 结论                                                                             |
| -------- | -------------------------------------------------------------------------------- |
| 载体容量 | **硬约束**（按载体单面时长装歌，装不下放弃/换歌）                                |
| 生成方式 | **用户选定生成**（手动选歌），非自动、非 LLM                                     |
| 收藏     | 生成的物品**持久收藏**，结果固定                                                 |
| 正反面   | 随物品类型（黑胶/磁带 AB 面，CD 单面）                                           |
| 翻面     | 受拟真度与设置控制（可自动翻面）                                                 |
| 置物架   | 按 Tag 分类陈列；暂不设容量，作为**可替换物件**预留（未来更换置物架 = 容量增减） |
| 物品库   | 独立于置物架的**全局存储**（`music/items.db`），所有物品的家                     |
| 封面来源 | 网络查找 / 用户提供 / 占位图（第一版仅后两者）                                   |
| 曲库     | 无素材库概念——用户从文件管理器选文件，**只记录路径**；生成时打包进物品           |
| 修正手段 | 需要：重新刻录变体 / 手动换歌 / 删除                                             |
| 技术栈   | **第一版 PySide6**（单进程，严格分层）；Web / Godot 为后续计划                   |
| 格式     | mp3 / flac / wav / m4a 起步（解码器插件注册表，可扩展）                          |
| 事件通道 | core 零 Qt 依赖，事件契约独立；ui/bridge 唯一翻译层                              |

## 四、命名体系

| 中文     | 代码标识   | 含义                                                     |
| -------- | ---------- | -------------------------------------------------------- |
| 物品     | `Item`     | 所有生成物的统称（黑胶/磁带/CD 的实例）                  |
| 物品类型 | `ItemType` | vinyl / cassette / cd——决定容量预算、AB 面语义、拟物形态 |
| 面       | `Side`     | A / B（CD 只有 A）                                       |
| 物品库   | `library`  | 全局存储，所有物品的持久化容器（`music/items.db`）       |
| 置物架   | `Shelf`    | 陈列视图（按 Tag 分类），未来可替换物件                  |
| 播放器   | `Deck`     | 唱机本体                                                 |
| 需求标签 | `Tag`      | 生成物品时用户赋予的分类（如"深夜"），置物架按此分类     |

## 五、目录结构规范

```
MrSirMusic/
├── main.py                        # 入口（argparse + GUI 分发，版本单一来源 base.json）
├── config/
│   ├── static/                    # 静态配置（json 驱动，只读）
│   │   ├── static_config.py       # 加载器
│   │   ├── config.json            # 引导映射表
│   │   ├── base.json              # 应用参数（版本等）
│   │   ├── item_types.json        # 载体类型注册（容量预算/AB面语义/形态）
│   │   ├── effects.json           # 拟真度效果注册表（档位/效果项/强度）
│   │   └── ui.json                # UI 参数
│   └── settings.py                # 用户配置（可读写：拟真度档位、自动翻面等）
├── utils/                         # 通用工具（零业务依赖）
│   ├── logger.py / file_utils.py / retry.py / convert.py
├── modules/                       # 业务核心（零 GUI 依赖，唯一可被未来复用的层）
│   ├── items/                     # 领域模型（Item/ItemType/Side/Track/Tag，纯数据）
│   ├── rules/                     # 规则引擎（硬容量算法、AB面分配、选歌校验）
│   ├── generator/                 # 生成编排（选歌→分配→封面→入库；未来 LLM 只动这里）
│   ├── library/                   # 物品库持久化（music/items.db）
│   ├── tagging/                   # 标签解析（mutagen 读 ID3/FLAC）
│   ├── cover/                     # 封面服务（providers 注册表：local/placeholder，network 留接口）
│   └── playback/                  # 播放核心
│       ├── engine.py              # 播放引擎封装（内部 QMediaPlayer，对外零 Qt 类型）
│       ├── decoders/              # 解码器插件注册表（mp3/flac/wav/m4a 各一模块）
│       └── events.py              # 领域事件契约（事件名 + 数据结构，零 Qt 依赖）
├── ui/                            # 界面层（唯一允许 import PySide6 的层）
│   ├── main_window.py             # 主窗（三视图容器）
│   ├── views/
│   │   ├── library_view.py        # 物品库视图
│   │   ├── shelf_view.py          # 置物架视图（按 Tag 分类陈列）
│   │   └── deck_view.py           # 唱机视图
│   ├── widgets/
│   │   ├── record_widget.py       # 物品拟物绘制（黑胶/磁带/CD 形态）
│   │   ├── deck_widget.py         # 唱机（转盘/唱针/翻面动效）
│   │   └── progress_widget.py     # 进度/状态条
│   ├── effects/                   # 拟真度效果层（贴图叠加，由 effects.json 装配）
│   │   ├── registry.py
│   │   └── wear.py                # 磨损/风化/指纹
│   ├── bridge/                    # 事件适配器（core events → Qt 信号，唯一翻译层）
│   └── themes.py                  # QSS 主题
├── music/                         # 物品库数据（gitignore 内容，保留目录）
│   ├── .gitkeep
│   ├── items.db                   # 物品库 SQLite（用户核心数据）
│   └── covers/                    # 封面实体文件
├── data/                          # 静态资源（入库）
│   ├── placeholder.png
│   └── textures/                  # 磨损/风化纹理贴图
├── docs/                          # 设计文档
├── .reference/                    # 参考仓库（gitignore，浅克隆）
├── .temp/                         # 临时脚本（gitignore）
├── .opencode/                     # opencode 配置（gitignore）
├── AGENTS.md / README.md / requirements.txt
├── w.study.md / x.progress.md / z.plan.md
```

**gitignore 关键规则**：

```
# 物品库数据：忽略内容，保留目录
music/*
!music/.gitkeep
```

## 六、核心机制设计

### 1. 载体类型注册（config/static/item_types.json）

新载体 = 加一条 JSON + 一个拟物绘制分支，核心与 UI 均按注册表驱动：

```json
{
  "vinyl": {
    "name": "黑胶",
    "side": ["A", "B"],
    "minutes_per_side": 22,
    "shape": "circle"
  },
  "cassette": {
    "name": "磁带",
    "side": ["A", "B"],
    "minutes_per_side": 30,
    "shape": "rect"
  },
  "cd": {
    "name": "CD",
    "side": ["A"],
    "minutes_per_side": 80,
    "shape": "circle"
  }
}
```

### 2. 解码器插件注册表（modules/playback/decoders/）

新格式 = 加一个模块，主程序按"扩展名 → 探测链"选择（audacious InputPlugin 模式）：

- 每个模块声明：`EXTENSIONS`、`probe(path) -> bool`、`decode(path) -> stream`
- 第一版基于 QtMultimedia 支持格式；注册表结构为未来独立解码进程预留

### 3. 事件契约（modules/playback/events.py）

纯数据结构，零 Qt 依赖；`ui/bridge/` 是唯一翻译层（core events → Qt 信号）：

| 事件名           | 触发时机           | 主要 payload        |
| ---------------- | ------------------ | ------------------- |
| `PLAYBACK_STATE` | 播放/暂停/停止切换 | state               |
| `TRACK_CHANGED`  | 切歌               | track 摘要          |
| `PROGRESS`       | 播放进度更新       | position / duration |
| `SIDE_FLIPPED`   | 翻面               | side                |
| `ERROR`          | 播放/文件错误      | 错误分类 + 消息     |

### 4. 拟真度（effects.json + ui/effects/）

- 档位：简洁 / 精致 / 真实；每档声明启用的效果项与强度
- 效果项：wear（磨损贴图）、weathering（风化）、动画开关、声效开关
- ui/effects/registry 按配置装配，核心不感知（第一版无声效）

### 5. 数据模型

```
Item:  id / name / type(vinyl|cassette|cd) / cover_source(local|placeholder) / cover_path
       / tag / created_at / play_count / sides{A: [Track...], B: [Track...]}
Track: path / title / artist / album / duration(秒) / format
```

物品的"家"是物品库；置物架只是陈列视图。未来"更换置物架"只改变陈列规则与容量上限，不动物品库数据。

## 七、架构约束（写死进 AGENTS.md）

1. `modules/` 零 UI 依赖（禁止 import PySide6）；唯一可被未来 Web/Godot 复用的层
2. 事件契约独立于 Qt；`ui/bridge/` 是唯一翻译层
3. 可调参数一律走 `config/static/*.json`，禁止代码硬编码
4. 版本号单一来源：base.json `version` 字段；四段式 `X.Y.Z.P`：`X.Y` 版本主线、`Z` 内容版本（新增/重构/小版本更新 `+1`）、`P` 审计轮次（审计修复 `+1`，`Z` 递增时归零）
5. 正式文件注释禁止 `.reference/` 标注；参考信息只允许在 `.temp/` 或文档中
6. 音频数组约定：统一 `(N, 2) float32 [-1, 1] @ 44100Hz`（为后续效果器预留）
7. 错误策略（沿用 MrAutoDJ 系）：不崩溃、不阻塞、有提示、能自愈

## 八、第一版验收清单

- [x] `--version` 输出版本（base.json 单一来源）——✅ A0.4 完成（输出 0.1.0.0）
- [x] 文件多选导入 → 读标签 → 生成物品（容量校验 + AB 面分配）——✅ A8.1/A11.6/A14.1 完成（端到端 10+ 音频生成 2 件不同类型）
- [x] 物品库浏览 / 置物架按 Tag 陈列 / 唱机播放（进度/翻面）——✅ A11/A14.1 完成（三视图 + 播放路由 + 翻面/进度）
- [x] 修正手段（重新刻录/换歌编辑/删除）——✅ A8.2/A8.3/A8.4 完成
- [x] 拟真度三档切换生效（重启保持）——✅ A13 完成（档位装配 + 设置面板持久化）
- [x] 退出重启后物品库完整恢复——✅ A14.2 完成（两次启动状态比对）

## 九、后续路线（扩展位，第一版不做）

1. **Web / Godot UI**：modules/ 复用不变，只换 ui/ 层；core API 需暴露为 HTTP/WebSocket 时在 modules 外加 server.py 适配层
2. **LLM 选曲**：只动 modules/generator（"需求 → 自动选曲"入口），领域层不动
3. **网络封面**：modules/cover 增加 network provider（已留接口）
4. **置物架更换**：Shelf 实体化（容量/形态），物品库不动
5. **独立解码进程**：decoders 注册表已预留，可演进为进程隔离（SpotAmp 管道模式）

## 观察项豁免定案清单（历轮汇总，2026-08-15 分级定稿）

> 分级规则（参照 MrBoard 机制，2026-08-15 定稿）：历轮（A001-A005）参考级观察项经复核，按确定性分三级——
> ①**永久豁免**：外部约束/设计定案/数据常量/性能可接受/并发理论/外观——后续轮次**不再报告、不再讨论**（除非外部依赖本身变更，如音频格式集合、Qt 行为）
> ②**条件豁免**：需验证/理论不可达/数据语义——触发条件变化时重新评估（每项标注触发条件）
> ③**价值权衡**：可修但收益 < 成本——未来批次按需排期
> 历史归档：历轮附录"二、参考级观察项"为审计记录保留；本清单为豁免唯一权威源，已定案项后续轮次不再重复报告

### ① 永久豁免（不再讨论）

- **分层约束**：三处格式清单（file_utils.AUDIO_EXTENSIONS / decoders 注册表 / tagging._READERS——utils 零业务依赖结构性约束，registry 交叉校验告警兜底）
- **外观**：绘制色硬编码（record/deck/wear 约 12 处，视觉常量）；themes QProgressBar 无 QSS 规则；空物品文案覆盖；菜单注释残留
- **并发理论**：static_config 单例懒加载非线程安全（import 期单线程）；档位监听器累积无退订（GUI 单实例）
- **性能可接受**：reporter 常驻 1s 定时器（1/s 事件量）；side_allocator O(n²)（曲目量级小）；repository load_all 秒级排序不稳；schema DB_PATH import 期计算
- **设计定案**：PlaybackEngine 无 shutdown（进程级生命周期）；closeEvent 未停 deck timer/engine（QTimer 父销毁自停）；delete.py/record_widget 函数内延迟 import（循环结构/AGENTS.md 例外）；迁移单迁移非原子；decoders 占位模块零消费；providers 循环延迟 import；COVERS_DIR 独立派生（模块解耦）；registry 单向告警（四格式一致）；settings_dialog 非法档位自愈；logger handler 预配场景；message_label 无清除时机（下次错误覆盖）；logger 文件 handler 静默失败（自愈）；effects.levels 内部记录未校验（isinstance 守卫兜底）；sample_rate/channels 预留键；retry 不可达分支；format_duration(inf)；回调重入递归；missing_tracks 无消费方（播放链实时 is_missing 正确路径）；play() missing 不重置 state（ERROR 已提示）；A 面 Side 缺失 boundary 误算（正常链路不可达）；消费点回退字面量（项目惯例）；`logging._nameToLevel` 私有 API（CPython 多年稳定）

### ② 条件豁免（触发条件变化时重新评估）

- 纯 ID3 无帧 probe 误判（mp3.py:14）——触发：decoders resolve 被 UI 实际消费（第一版占位）
- 封面导入非原子写改造后仍需关注孤儿临时文件——触发：封面写入原子性需求提升（已入 G 系列原子写，见③关联）
- engine ended 后重播行为——触发：Qt 运行时行为变化（需验证）
- queue.flipped 从 B 回 A 不复位——触发：side 推导逻辑变更

### ③ 价值权衡（未来批次按需排期，决策记录）

- （原 3 项已全部编入 G 系列任务清单，2026-08-15 移出）：
  - migrate 异常连接泄漏 → G3.1（加 finally close，成本约 3 行）
  - 三处格式清单双向告警 → G2.1（白名单多出格式时提示）
  - `message_label` 加清除时机 → G3.2（load_item 时清）

### 已升级转出（观察项 → P 级修复，用户复核 2026-08-15 定案）

- **0 时长曲目**（A004/A005 观察项）→ G0.1 完成 ✅（validate 增加 duration<=0 拦截）
- **生成丢弃曲目无提示**（A003/A005 观察项）→ G0.2 完成 ✅（分配差异抛 GenerateError，A 方案）
- **封面导入非原子写**（A003/A004/A005 观察项）→ G0.3 完成 ✅（临时文件 + os.replace 原子改名）

### 已修复记账（历史记录防重复报告）

- 翻面按钮态漂移（E0.4/F0.4 修复）；spin_tick_ms/drag_threshold 0 值（F3.2）；missing 展示错位（F0.2）；flip 回滚 _track（F0.3）；空 A 面 side 推导（F3.1）；card_size 长度契约（E0.2）；animation 0 值除零（E0.3）；item_types side 校验（F0.5）；默认档位回退链（F0.6）；监听器同实例去重（C1.3）

## 附录 A001：全量代码审计报告（第1轮，2026-08-14）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json（user_config.json 运行时生成不审）
> 方式：三路并行（utils+config / modules / ui）逐文件全文阅读 + 交叉验证（grep 调用点、venv 实测 mutagen/Path 语义）
> 状态：✅ 已完成（B 系列修复 2026-08-15 全部落地：B0-B4 共 49 项；全量回归 18 探针 PASS + 冒烟 OK + --version 0.1.0.0）
> 结论：P0 1 项、P1 15 项、P2 29 项 + 观察项 14 条（5 条经用户复核提升为 P 级，已并入 B 系列）

## 零、上轮修复复核清单

无上轮（首轮审计）。

## 一、P0-P3 修复清单

### P0（高：确定性缺陷 + 真实可达）

| #    | 文件:行号                                                      | 类型              | 描述                                                                                                | 建议                                                                    | 性质 | 影响面 |
| ---- | -------------------------------------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ---- | ------ |
| P0-1 | modules/playback/engine.py:120-167（play_next/play_prev/flip） | 13 错误策略一致性 | play() 有 is_missing 检查，但下一首/上一首/翻面三处无缺失检查——用户删除文件后按"下一首"静默卡死无声 | 三处统一：is_missing → emit ERROR(file_missing) + 日志 + 尝试跳过下一首 | 新增 | 播放   |

### P1（中）

| #     | 文件:行号                                                                      | 类型           | 描述                                                                                                                                         | 建议                                                                         | 影响面   |
| ----- | ------------------------------------------------------------------------------ | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------- |
| P1-1  | schema.py:9-13 / repository.py:8,18 / migration.py:6 / delete.py:6,14          | 10/12 可测试性 | DB_PATH 四模块各自 from...import 值绑定副本——探针覆盖不完整会静默操作真实用户库                                                              | 收敛为单一 get_db_path()/set_db_path_for_tests()                             | 跨模块   |
| P1-2  | generator.py:33-49 + generate_check.py:13-26                                   | 1 正确性       | check_item() 零调用；generate([]) 空列表校验通过 → 生成 0 曲目空物品入库                                                                     | 入库前调 check_item；空文件列表抛 GenerateError                              | 生成     |
| P1-3  | settings.py:62-64 + ui/effects/registry.py + ui/widgets/* + main_window.py:134 | 11+5 未接线    | 拟真度档位链路断线：add_change_listener 零注册、apply/animations_enabled/set_effects/set_animations_enabled 零调用——设置保存后无任何行为变化 | main_window 注册监听器：档位 → registry.apply + 动画开关；拟物控件接入主界面 | UI 交互  |
| P1-4  | ui/themes.py:11-36                                                             | 5 未接线       | apply_theme(app) 正式代码零调用——全局主题从未生效                                                                                            | main.py run_gui 一行接入                                                     | 显示层   |
| P1-5  | ui/views/library_view.py:118-123 + main_window.py:99                           | 1 正确性       | 右键菜单"编辑/重新刻录/删除"三信号零接收者——可见可点但静默无效                                                                               | main_window 接入三信号 → edit/regenerate/delete → refresh_library            | UI 交互  |
| P1-6  | ui/widgets/deck_widget.py:53-63                                                | 1 正确性       | 停止后 set_playing(False) 只停 timer，_tonearm_pos 保持 1.0——唱针不抬起，注释失实                                                            | 停止分支补 _tonearm_pos=0.0; update()                                        | 显示层   |
| P1-7  | ui/views/deck_view.py:78-84                                                    | 1 正确性       | 换物品时 cover 加载失败不更新 → 旧封面残留                                                                                                   | 封面无效分支 cover_label.clear()/setText                                     | 显示层   |
| P1-8  | engine.py:35-44                                                                | 2 防御         | QMediaPlayer.errorOccurred 未连接——损坏/不支持格式播放静默无提示                                                                             | 连接 → emit ERROR(playback_error) + 日志                                     | 播放     |
| P1-9  | ui/import_dialog.py:137-148                                                    | 2 防御         | 仅捕获 GenerateError，生成链路底层异常无兜底——槽内异常炸出                                                                                   | except Exception → QMessageBox 提示                                          | UI 交互  |
| P1-10 | modules/generator/delete.py:23-35                                              | 2 防御         | _cover_referenced 任何异常返回 False → 误删共享封面文件                                                                                      | 异常保守返回 True（不删）或记日志跳过                                        | 数据     |
| P1-11 | decoders/mp3.py:12、flac.py:12、wav.py:12、m4a.py:12                           | 9 性能         | 四格式 probe 全用 read_bytes()（整文件读入内存再切片）——大文件每次探测全量读盘                                                               | with open() as f: f.read(12)                                                 | 播放     |
| P1-12 | placeholder_provider.py:9-11 + ui/effects/wear.py:10                           | 3 配置化       | base.json data_dir 键零消费——两处硬编码 "data"                                                                                               | 均改 base["data_dir"]                                                        | 配置体系 |
| P1-13 | utils/logger.py:7-8,18                                                         | 3 配置化       | 日志目录/级别硬编码（注释自认可外置）                                                                                                        | 外置 base.json（logs_dir/log_level）                                         | 日志     |
| P1-14 | utils/file_utils.py:7                                                          | 3 配置化       | AUDIO_EXTENSIONS 与 decoders 注册表双处维护易漂移                                                                                            | 由 decoders 注册表导出或外置配置                                             | 跨模块   |
| P1-15 | static_config.py:25-34 + 消费点                                                | 2 防御         | _read_json 只校验顶层 dict，字段类型不校验——任一键被误写字符串/数组即 ValueError（GUI 起不来）                                               | 加载后类型校验或消费点宽容转换                                               | 配置体系 |

### P2（低）

| #     | 文件:行号                                                                                                | 类型               | 描述                                                                                                                                                                                                          |
| ----- | -------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P2-1  | main.py:9,15                                                                                             | 4 重复             | _STATIC_DIR 双处定义；json.loads 直读绕单例 → 版本双通道                                                                                                                                                      |
| P2-2  | main.py/logger.py/schema.py/static_config.py                                                             | 4 重复             | 项目根派生逻辑 4 处独立实现                                                                                                                                                                                   |
| P2-3  | 多处                                                                                                     | 5 死代码           | retry、file_utils 三函数、seconds_from_ms、to_float32、add_track_to_side、is_full、edit 四函数、regenerate、delete、ProgressWidget/RecordWidget/DeckWidget 未接入、result_item、空"视图"菜单、engine._url_cls |
| P2-4  | convert.py:26 / static_config.py:12 / record_widget.py:106 / deck_widget.py:53                           | 6 注释失实         | 字符串数字弹性转换不符；A2.1 后可统一未做；磁带盒"封面或色块"只画色块；"唱针抬起"未实现                                                                                                                       |
| P2-5  | utils/retry.py:26-30                                                                                     | 2 防御（实机验证） | delay<0 → sleep ValueError；times<=0、exceptions=() 未校验                                                                                                                                                    |
| P2-6  | config/settings.py:34-54                                                                                 | 2+13               | 档位无枚举校验（非法档位静默空效果）；save_config 写失败完全静默                                                                                                                                              |
| P2-7  | base.json:5-7 / ui.json:13                                                                               | 12 死键            | sample_rate/channels/data_dir/library_column_widths 零引用                                                                                                                                                    |
| P2-8  | effects.json:2 + settings.py:17 + registry.py:20 / 各配置回退默认                                        | 12 漂移            | 默认档位"refined"三处维护；配置缺键回退默认值与 json 值双处维护                                                                                                                                               |
| P2-9  | delete.py:11,6                                                                                           | 6 规范             | 函数内 import sqlite3；load_item 未使用导入                                                                                                                                                                   |
| P2-10 | delete.py:33                                                                                             | 7 安全（需验证）   | unlink 任意 DB 路径，未校验在 COVERS_DIR 内                                                                                                                                                                   |
| P2-11 | migration.py:33-46                                                                                       | 9 性能             | 每次连接跑 migrate（多一次 SELECT+commit）                                                                                                                                                                    |
| P2-12 | repository.py:118-125                                                                                    | 9 冗余             | load_all 已排序，_row_to_item 内再 sorted                                                                                                                                                                     |
| P2-13 | local_provider.py:13-18                                                                                  | 9+4+2              | 全量读内存（可 safe_copy 复用）；非原子写；扩展名不校验                                                                                                                                                       |
| P2-14 | event_bus.py:22-28,9-12                                                                                  | 10+6               | 回调异常完全静默；subscribe 无去重（注释"幂等安全"歧义）                                                                                                                                                      |
| P2-15 | cover/providers.py:30-47                                                                                 | 8                  | 懒装配竞态（单线程 GUI 无实际风险）                                                                                                                                                                           |
| P2-16 | repository.py:58-60                                                                                      | 12                 | 未知 type 键 → 0 容量幽灵物品无日志                                                                                                                                                                           |
| P2-17 | generator.py:47-48                                                                                       | 10                 | import_cover_file 失败静默无日志                                                                                                                                                                              |
| P2-18 | queue.py:45-56                                                                                           | 1（需验证接线）    | A 空 B 有曲：boundary 错设为 B 面数 → 永不翻面                                                                                                                                                                |
| P2-19 | edit.py:9-19                                                                                             | 13                 | 加曲不防重复 path（生成时防、编辑时不防）                                                                                                                                                                     |
| P2-20 | engine.py:72                                                                                             | 9                  | load_item 每次全量读 user_config.json                                                                                                                                                                         |
| P2-21 | progress.py:39-47                                                                                        | 13                 | duration 用标签值而非 player.duration()                                                                                                                                                                       |
| P2-22 | decoders/registry.py:46-58                                                                               | 10                 | resolve None 无法区分"未注册/探测失败"                                                                                                                                                                        |
| P2-23 | themes.py:19-32                                                                                          | 3                  | QSS 8 处颜色硬编码未进 ui.json                                                                                                                                                                                |
| P2-24 | library_view.py:69 / shelf_view.py:92,39 / deck_view.py:39,83 / deck_widget.py:29 / import_dialog.py:100 | 3                  | 缩略图/卡片/封面/帧间隔/图片过滤串硬编码                                                                                                                                                                      |
| P2-25 | progress_widget.py:26-34 vs deck_view.py:108-113                                                         | 4 重复             | 百分比换算双处独立实现                                                                                                                                                                                        |
| P2-26 | wear.py:20-27                                                                                            | 9                  | 贴图缺失时每帧重复 IO（失败未缓存）                                                                                                                                                                           |
| P2-27 | registry.py:38-40 / settings_dialog.py:26                                                                | 2                  | intensity float(None) TypeError；effects.json 空时下拉空保存 ""                                                                                                                                               |
| P2-28 | event_bridge.py:24-36                                                                                    | 2                  | 无 **del** 兜底退订（当前正常路径已覆盖）                                                                                                                                                                     |
| P2-29 | deck_view.py:120-130                                                                                     | 1（需验证）        | dragMoveEvent 未实现                                                                                                                                                                                          |

### 观察项提升（用户复核 2026-08-14 提升为 P 级）

| #   | 位置                                   | 提升为 | 描述                                                         |
| --- | -------------------------------------- | ------ | ------------------------------------------------------------ |
| O-1 | deck_view.py:89-94                     | P1     | 播放/暂停按按钮文本分发（脆弱）→ 改显式状态字段              |
| O-2 | shelf_view.py:73-85                    | P1     | _empty_label deleteLater 后重建 RuntimeError（空→有→空时序） |
| O-3 | capacity.py:15 vs side_allocator.py:17 | P1     | float 边界先减后比 vs 先加后比 → 统一比较方式                |
| O-4 | progress.py:13                         | P2     | timer_interval_ms=1000 硬编码 → 外置配置                     |
| O-5 | main.py:16                             | P2     | version 非字符串输出畸形 → 加类型校验                        |

## 二、参考级观察项（记录不修）

| 位置                                                        | 描述                           | 回落理由                                    |
| ----------------------------------------------------------- | ------------------------------ | ------------------------------------------- |
| engine.py:80-91                                             | ended 后重播行为依赖 Qt 运行时 | 需验证，非代码可证明                        |
| decoders 全模块                                             | 注册表/decoder 占位零消费      | 有注释依据的预留契约（第一版 QtMultimedia） |
| providers.py:32-33 / engine.py:35-44 / record_widget.py:135 | 函数内延迟导入                 | AGENTS.md 豁免（重依赖/循环依赖结构性）     |
| migration.py:38-46                                          | 多步迁移非原子                 | 第一版仅单条迁移，无部分迁移风险            |
| reader.py:83-88                                             | 三处格式清单各自维护           | 当前完全一致无失配                          |
| main_window.py:148-152                                      | closeEvent 未停 engine         | 关窗即退进程，无泄漏                        |
| 绘制颜色/几何参数（record/deck/wear 12 处）                 | 渐变/槽纹色硬编码              | 外观绘制细节参数豁免                        |
| static_config.py:50-58                                      | 单例懒加载非线程安全           | 模块导入期单线程调用                        |
| logger.py:17                                                | 外部预配 handler 场景          | 当前无调用方，纯理论                        |
| settings_dialog.py:26-27                                    | 非法档位回退自愈               | UI 层已自愈                                 |

## 三、亮点

- 分层架构合规：modules 零 UI 依赖（engine 特许例外对外零 Qt 类型）；事件契约零 Qt + bridge 唯一翻译层且 shutdown 幂等
- 容错降级链路完整：empty_record / placeholder 兜底 / 宽容解析 / 探针隔离测试库
- TDD 全覆盖：14 个探针全量回归
- 三路交叉验证一致：mutagen 帧 str() 行为已实测排除；read_bytes 全读语义已实测确认

## 附录 A002：全量代码审计报告（第2轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json
> 方式：三路并行（utils+config / modules / ui）逐文件全文阅读 + git show 0485b8a 修复 diff 核对 + 实测验证
> 状态：✅ 已完成（C 系列修复 2026-08-15 全部落地：C0-C4 共 17 项；全量回归 22 探针 PASS + 冒烟 OK + --version 0.1.0.2）
> 结论：P0 1 项、P1 8 项、P2 7 项 + 观察项 16 条；**B 系列归档缺口：P1-8/P1-9 无对应条目、P1-7 修复不完整**

## 零、上轮修复复核清单（A001 / B 系列 49 项）

| 复核项                                                                                                       | 现状                                                                                                   | 证据                           |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ | ------------------------------ |
| 关键修复 11 项抽查（缺失检查/DB_PATH 单点/档位接线/主题/右键路由/控件接入/paths/类型校验/总线/缓存/**del**） | ✅ 仍在                                                                                                | 各组逐行核对（commit 0485b8a） |
| B 系列覆盖完整性                                                                                             | ⚠️ 缺口 3 项：P1-7（封面残留修复不完整）、P1-8（errorOccurred）与 P1-9（import_dialog 兜底）无对应条目 | B0-B4 清单 vs A001 条目比对    |
| migration DB_PATH 值绑定（P1-1）                                                                             | ⚠️ 未完全收敛（migration.py:6,20-21 仍绑定 schema.DB_PATH）                                            | modules 组                     |
| event_bus 去重（B3.8）                                                                                       | ⚠️ 部分（对 bound method 无效）                                                                        | modules 组                     |
| main.py 说明区 / settings 路径派生 / effects 回退字面量                                                      | ⚠️ 漏改（B1.1/B1.2/P2-8 残留）                                                                         | config 组                      |
| 引入回归                                                                                                     | ❌ 0 处（但 B0.4 接线暴露新缺陷 P0-1）                                                                 | 各组                           |

## 一、P0-P3 修复清单

### P0（高：确定性错值 + 真实可达）

| #    | 文件:行号                       | 类型     | 描述                                                                                                     | 建议                                        | 性质                  | 影响面 |
| ---- | ------------------------------- | -------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------- | --------------------- | ------ |
| P0-1 | ui/widgets/deck_widget.py:34-41 | 1 正确性 | set_animations_enabled(True) 只更新标志不重启 timer——播放中改档位"简洁→精细"后转盘永久冻结（确定性复现） | enabled=True 且 _playing 时补 timer.start() | 新增（B0.4 接线引入） | 显示层 |

### P1（中）

| #    | 文件:行号                                            | 类型        | 描述                                                                                                                                              | 建议                                               | 性质                |
| ---- | ---------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ------------------- |
| P1-1 | engine.py:35-44                                      | 2 防御      | QMediaPlayer.errorOccurred 仍未连接——损坏/不支持格式播放静默（A001 P1-8 遗留）                                                                    | 连接 → emit ERROR(playback_error) + 日志           | 遗留                |
| P1-2 | decoders/mp3.py:12、flac.py:12、wav.py:12、m4a.py:12 | 9 性能      | 四格式 probe 仍整文件 read_bytes（A001 P1-11 遗留）                                                                                               | with open() as f: f.read(12)                       | 遗留                |
| P1-3 | config/static/static_config.py:15-25 + 消费点        | 2 防御      | B2.4 白名单覆盖不完整（实测）：log_level 非法值 → setLevel ValueError 导入即崩；music_dir/data_dir 非字符串 → schema.py import 即崩；容器键不校验 | 白名单扩到字符串/容器键（移除+告警）               | 新增（B2.4 不完整） |
| P1-4 | ui/import_dialog.py:138-149                          | 2 防御      | generate 底层异常无兜底——槽内炸出（A001 P1-9 遗留）                                                                                               | except Exception → QMessageBox 提示                | 遗留                |
| P1-5 | ui/widgets/record_widget.py:41-49                    | 1 正确性    | set_item 封面加载失败不清 _cover——local 封面文件被删后旧封面残留（A001 P1-7 不完整）                                                              | 失败分支补 self._cover = None                      | 遗留                |
| P1-6 | modules/generator/generator.py:51-58                 | 13 错误策略 | 封面导入失败日志称"降级占位图"实际中止生成（语义矛盾，B0.2 引入）                                                                                 | 失败降级 cover_source="placeholder" 或日志改"中止" | 新增                |
| P1-7 | modules/library/repository.py:37-41                  | 2 防御      | _connect 不 ensure_dir——music/ 被删后首连崩溃                                                                                                     | 连接前 mkdir(parents=True, exist_ok=True)          | 新增                |
| P1-8 | modules/library/migration.py:6,20-21                 | 12 配置卫生 | _connect 值绑定 schema.DB_PATH——无参 migrate() 绕过测试库覆盖（潜伏）                                                                             | 改走 repository.get_db_path()                      | 遗留（P1-1 未收敛） |

### P2（低）

| #    | 文件:行号                                           | 类型   | 描述                                                                                    |
| ---- | --------------------------------------------------- | ------ | --------------------------------------------------------------------------------------- |
| P2-1 | utils/convert.py:22                                 | 2+6    | progress_percent 不钳制（position>duration → >100，实测）且注释失实                     |
| P2-2 | main.py:44-47                                       | 6      | 说明区失实（_STATIC_DIR 已删，B1.1 漏改）                                               |
| P2-3 | config/settings.py:11-13,83,88-92                   | 4+6+10 | USER_CONFIG_PATH 未收敛 project_root；函数内延迟 import get_logger；回调异常静默/无去重 |
| P2-4 | utils/retry.py:19,21                                | 2      | times=True 通过校验（bool 是 int 子类，实测）；delay="0.1" 抛 TypeError                 |
| P2-5 | modules/playback/event_bus.py:14-19                 | 1/2    | 去重对 bound method 无效（注释"幂等安全"失实）                                          |
| P2-6 | main.py:22                                          | 6      | 文案"ui 层尚未开发完成"过时                                                             |
| P2-7 | effects.json:2 + settings.py:21,70 + registry.py:20 | 12     | 回退字面量 "refined" 三处残留（主值已单源）                                             |

## 二、参考级观察项（记录不修）

| 位置                                                        | 描述                                                       | 回落理由                           |
| ----------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------- |
| ui/main_window.py:71 + settings 监听器                      | 档位监听器模块级累积无退订（多窗口残留）                   | 当前 GUI 单实例，正常路径不可达    |
| engine.py:161-172                                           | flip() B 面首缺失时队列已推进与返回值不一致                | 可自愈；UI 不消费返回值            |
| queue.py:14-15                                              | flipped 从 B 回 A 不复位                                   | side 推导已兜底                    |
| engine.py:66-76                                             | 空物品 load_item 不 setSource（旧媒体续播）                | 空物品被 check_item 拦截不可达     |
| main_window.py:50-51                                        | reporter 常驻 1s 定时器（未播放也发 PROGRESS）             | 事件量 1/s 可忽略                  |
| regenerate.py:13 / capacity.py:16-19 / generate_check.py:18 | 硬编码策略字符串/超载信息失真/重复计算                     | 有注释依据/DB 篡改才可达/微优化    |
| delete.py:37-38                                             | unlink 失败静默                                            | 保守策略正确                       |
| providers.py:11-15                                          | COVERS_DIR 独立派生项目根（第 4 处）                       | 结果一致，模块解耦可接受           |
| file_utils vs registry vs reader                            | 三处格式清单（B2.3 半单源）                                | utils 零业务依赖分层约束，告警兜底 |
| repository.py:43-45                                         | _migrated_path 单槽（同路径删库重建不重迁移）              | 探针惯例新路径，生产无此场景       |
| deck_view.py:57,83 / 97-103 / 128                           | CD 翻面按钮态漂移 / 空物品文案覆盖 / QInputDialog 探针挂起 | 显示态偏差/探针未触发              |
| main_window.py:196-200                                      | closeEvent 未停 deck_widget timer/engine                   | QTimer 父销毁自动停，关窗即退进程  |
| themes.py:26-43                                             | QProgressBar 无 QSS 规则                                   | 外观缺省，豁免范围                 |
| main_window.py:76                                           | 菜单注释残留"视图"                                         | 纯注释                             |
| main_window.py:121-151                                      | _edit_item 等三处函数内延迟 import（非重依赖）             | 轻微规范偏差                       |

## 三、亮点

- B 系列 46/49 项完整在位，回归 0 处；模块层零 PySide6 顶层导入，分层合规
- 重点核查结论：settings 缓存/失效一致性、migrate 路径缓存、progress 时长兜底、delete 路径消毒均实现正确
- 探针体系稳定：18 探针全量回归支撑审计前状态验证

## 附录 A003：全量代码审计报告（第3轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json
> 方式：三路并行（utils+config / modules / ui）逐文件全文阅读 + git show c8844d2 修复 diff 核对 + 实测验证
> 状态：✅ 已完成（D 系列修复 2026-08-15 全部落地：D0-D4 共 12 项；全量回归 24 探针 PASS + 冒烟 OK + --version 0.1.0.3）
> 结论：P2 7 项（无 P0/P1）；其中 4 项为 C 系列"修复不完整"（C0.5 覆盖面/值域、C2.3 下界、C1.1 残留）、3 项新增；问题密度收敛（45→16→7）

## 零、上轮修复复核清单（A002 / C 系列 17 项）

| 复核项             | 现状                                                                                                   | 证据                                     |
| ------------------ | ------------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| C 系列 17 项在位性 | ✅ 全部在位（commit c8844d2）                                                                          | 主会话 grep 15 项 + 各组补查             |
| 引入回归           | ❌ 0 处                                                                                                | 各组实测 import 冒烟 + --version 0.1.0.2 |
| C0.5 白名单覆盖面  | ⚠️ 不完整（effects/item_types 无校验、容器键 dict/list 混收、容器内部值无白名单、drag_threshold 漏项） | config/ui 组实测                         |
| C2.3 percent 钳制  | ⚠️ 只修上界（下界 -50 实测）                                                                           | config 组实测                            |
| C0.5 log_level     | ⚠️ 类型堵了值域残留（小写级别 → setLevel 崩）                                                          | config 组实测                            |
| C1.1 migration     | ⚠️ DB_PATH 死 import 残留                                                                              | modules 组                               |

## 一、P0-P3 修复清单

### P2（低-中，全部需配置误写或特定场景触发）

| #    | 文件:行号                                                                                                 | 类型   | 描述                                                                                                                                                                                                                                                                          | 建议                                                                              | 性质                |
| ---- | --------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------- |
| P2-1 | static_config.py:106-121 + settings.py:34 + deck_widget.py:26-28 / themes.py:14-16 / shelf_view.py:99-100 | 2 防御 | C0.5 校验覆盖面缺口（3 暴露面合并）：effects/item_types 分类未应用校验（effects.levels 非 dict → settings 导入即崩，实测）；容器键 dict/list 混收（animation/colors 应为 dict、card_size 应为 list）；容器内部数值键（record_spin_ms/tonearm_drop_ms/card_size 元素）无白名单 | _sanitize_types 扩展 effects/item_types；容器键按类型区分；容器内部数值键递归校验 | 新增（C0.5 不完整） |
| P2-2 | settings.py:13 + logger setLevel 消费                                                                     | 2 防御 | log_level 值域未校验：小写/非法级别名穿透白名单 → setLevel ValueError 导入即崩（实测）；json null 也穿过                                                                                                                                                                      | 值域用 logging._nameToLevel 键集合校验；null 移除                                 | 新增（C0.5 不完整） |
| P2-3 | utils/convert.py:18-22                                                                                    | 2+6    | progress_percent 下界未钳：position 负值返回负百分比（实测 -50），注释"钳制 0-100"失实                                                                                                                                                                                        | 补 max(0, ...) 下界 + 注释/说明区同步                                             | 新增（C2.3 不完整） |
| P2-4 | engine.py:78-79 + queue.py:29                                                                             | 1+13   | SIDE_FLIPPED 在 B 面内每切一首都重复发射（flipped 置位后不复位）——事件契约污染（当前消费端 _on_side 幂等，未来翻面动画会重复触发）                                                                                                                                            | 翻面仅发射一次（发射后对 flipped 置位动作去重）                                   | 新增                |
| P2-5 | engine.py:45-57                                                                                           | 13+1   | ERROR 后 engine.state 不同步（C0.2 引入）：播放器失败但 state 停留 "playing"，状态栏漂移且 ended 联动链不触发（有提示可自愈）                                                                                                                                                 | _on_player_error 非 NoError 时同步 _emit_state("stopped")                         | 新增（C0.2 引入）   |
| P2-6 | migration.py:7                                                                                            | 12+6   | DB_PATH 死 import 残留（C1.1 改走 get_db_path 后正文零使用）                                                                                                                                                                                                                  | 从 import 移除 DB_PATH                                                            | 新增（C1.1 残留）   |
| P2-7 | utils/logger.py:46                                                                                        | 6      | 说明区"可调参数后续可外置 base.json"失实（logs_dir/log_level 已于 B2.2 外置）                                                                                                                                                                                                 | 说明区更新                                                                        | 新增（B 系列残留）  |

## 二、参考级观察项（记录不修）

| 位置                                   | 描述                                         | 回落理由                         |
| -------------------------------------- | -------------------------------------------- | -------------------------------- |
| settings.py:98-101 / main_window.py:71 | 档位监听器跨实例累积无退订                   | GUI 单实例，正常路径不可达       |
| settings.py:91-95                      | save_config 回调内重入 → 无限递归            | 回调契约为"应用不保存"，理论缺口 |
| repository.py:45-47                    | migrate 异常时连接泄漏                       | 开发期缺陷 + GC 回收             |
| side_allocator.py + generator.py       | 分配丢弃曲目无提示                           | 注释声明 + 边界罕见              |
| delete.py:31                           | 函数内延迟 import COVERS_DIR                 | 轻微规范偏差                     |
| local_provider.py:18-20                | 非原子写/扩展名不校验（A001 P2-13 归档遗漏） | 失败场景罕见 + UI 兜底           |
| mp3.py:14                              | 纯 ID3 无帧文件 probe 误判                   | 占位消费 + Qt errorOccurred 兜底 |
| repository.py:41                       | mkdir 每次调用                               | μs 级开销可忽略                  |
| settings.py:34                         | effects.levels null 值穿过校验               | 需手动写 null 才触发             |
| file_utils vs decoders vs reader       | 三处格式清单                                 | utils 零业务依赖分层约束         |
| static_config.py:127-135               | 单例懒加载非线程安全                         | 模块导入期单线程                 |
| deck_view.py:57,83 / 97-103            | CD 翻面按钮态漂移 / 空物品文案覆盖           | 显示态偏差                       |
| main_window.py:76                      | 菜单注释残留"视图"                           | 纯注释                           |
| themes.py:26-43                        | QProgressBar 无 QSS 规则                     | 外观缺省豁免                     |

## 三、亮点

- C 系列 17 项全部在位且零回归；三组交叉验证一致
- C0.1 动画时序穷举（播放/暂停 × 动画开关 × 切换顺序）无冻结无泄漏
- 版本/README/commit 三方一致（0.1.0.2，c8844d2）

## 附录 A004：全量代码审计报告（第4轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json
> 方式：三路并行（utils+config / modules / ui）逐文件全文阅读 + git show 176373c 修复 diff 核对 + 实测验证
> 状态：✅ 已完成（E 系列修复 2026-08-15 全部落地：E0-E4 共 15 项；全量回归 26 探针 PASS + 冒烟 OK + --version 0.1.0.4）
> 结论：P2 7 项 + P3 7 项（无 P0/P1）；D 系列修复自身引入 4 处新缺口（card_size 长度/0 值除零/按钮态暴露/错误提示覆盖）+ 3 处遗留；问题密度 45→16→7→14（修复迭代期波动）

## 零、上轮修复复核清单（A003 / D 系列 12 项）

| 复核项             | 现状                                                                                                                                        | 证据                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| D 系列 12 项在位性 | ✅ 全部在位（commit 176373c）                                                                                                               | 主会话 grep 7 项 + 各组补查 |
| 引入回归           | ❌ 0 处（但 D 系列暴露 4 处新缺口）                                                                                                         | 各组实测                    |
| D0.1 白名单        | ⚠️ 3 处不完整：drag_threshold 漏项（A003 点名仍未入，实测 null 崩）；card_size 过滤后长度契约破坏（实测解包崩）；animation 0 值除零（实测） | config+ui 组                |
| D0.3 percent       | ⚠️ 说明区未同步（双界仅改代码注释）                                                                                                         | config 组                   |
| D0.4 翻面单次      | ⚠️ 暴露 deck_view 按钮态漂移                                                                                                                | modules+ui 组               |
| D0.5 错误同步      | ⚠️ 引入"错误提示被'已停止'覆盖"                                                                                                             | ui 组                       |
| D1.1 migration     | ⚠️ 说明区 DB_PATH 残留（import 已清）                                                                                                       | modules 组                  |

## 一、P0-P3 修复清单

### P2（低-中）

| #    | 文件:行号                                        | 类型        | 描述                                                                                                              | 建议                                                            | 性质              |
| ---- | ------------------------------------------------ | ----------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------- |
| P2-1 | static_config.py:20-28 + shelf_view.py:43        | 2 防御      | drag_threshold 仍未入 _NUMERIC_UI_KEYS（A003 点名漏项；实测 null → int(None) TypeError）                          | 加入白名单                                                      | 遗留              |
| P2-2 | static_config.py:111-121 + shelf_view.py:99-100  | 2 防御      | card_size 元素过滤不保长度契约（部分非法→[110]、全非法→[]，消费点双变量解包 ValueError → set_items 崩）           | 过滤后长度≠2 整键移除回退默认                                   | 新增（D0.1 缺口） |
| P2-3 | static_config.py:46-49 + deck_widget.py:27,72    | 2 防御      | animation 值域未覆盖：record_spin_ms=0 穿过校验 → _tick 除零（drop_ms 有 max(1,) 防护而 spin_ms 无）              | 嵌套数值加 >0 下界或消费端 max(1, _spin_ms)                     | 新增（D0.1 缺口） |
| P2-4 | deck_view.py:57,83,130-133 + engine.py:185-197   | 1 正确性    | 翻面按钮态漂移（D0.4 暴露扩大）：B 面内切歌不再恢复 checked、prev 回 A 按钮仍显"B 面"、flip 单向且 B 面点击无反馈 | _on_track 按 payload.side 同步按钮态；B 面时 flip 禁用/文本区分 | 新增（D0.4 暴露） |
| P2-5 | main_window.py:172-174/162-170 + engine.py:47-61 | 13 错误策略 | D0.5 引入：ERROR 提示被随后的 PLAYBACK_STATE(stopped) 覆盖——错误详情用户不可见（确定性复现）                      | 状态栏拆"状态+消息"两 label，或 _on_error 提示不被状态覆盖      | 新增（D0.5 引入） |
| P2-6 | items/model.py:28                                | 2 防御      | item_types 记录内 minutes_per_side 无白名单：误写 "abc" → int() ValueError → load 崩                              | 记录内数值键校验（与 _NESTED_NUMERIC 同机制）                   | 新增（D0.1 缺口） |
| P2-7 | static_config.py:167-170 + settings.py:70-76     | 12 配置卫生 | default_level 无"∈ levels 键"值域校验：不一致时档位失效且 save 回退链自引用写无效档位                             | 校验 default_level ∈ levels.keys()                              | 新增              |

### P3（低）

| #    | 文件:行号                                                 | 类型       | 描述                                                                                    |
| ---- | --------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------- |
| P3-1 | engine.py:193-195                                         | 1 时序     | flip() 失败（B 面首曲 missing）时 _just_flipped 悬挂                                    |
| P3-2 | engine.py:86-97                                           | 1 状态同步 | load_item 不重置 state（load 后 play 因 missing 短路时 UI 按钮态残留）                  |
| P3-3 | engine.py:145-168                                         | 13         | play_next/flip 到 missing 曲目 index 不回滚                                             |
| P3-4 | migration.py:62                                           | 6          | 说明区仍写"DB_PATH（schema.py 同源）"（D1.1 未同步）                                    |
| P3-5 | progress.py:75                                            | 6          | 说明区"后续可外置 ui.json/base.json"失实（已外置）                                      |
| P3-6 | main_window.py:126,138,148                                | 6          | 三处函数内延迟 import generator.*（非重依赖）                                           |
| P3-7 | static_config.py:194-202 + convert.py:34-35 + retry.py:53 | 6          | 说明区残留组：_CONTAINER_UI_KEYS 旧名/旧签名、convert 双界未同步、retry"后续可外置"失实 |

## 二、参考级观察项（记录不修）

| 位置                                     | 描述                                        | 回落理由                |
| ---------------------------------------- | ------------------------------------------- | ----------------------- |
| deck_view.py:57,83                       | 翻面按钮态（纯显示态部分）                  | 引擎状态正确            |
| themes.py:14-24                          | colors 内部值无白名单                       | 需手写误改 + Qt 容错    |
| record_widget.py:70-134                  | 绘制色硬编码 8 处                           | 视觉常量豁免            |
| registry.py:57-61                        | effects.levels 内部记录未校验 dict          | isinstance 守卫兜底     |
| settings.py:91-95 / main_window.py:71    | 监听器累积/回调重入                         | GUI 单实例              |
| static_config.py:16                      | logging._nameToLevel 私有 API               | CPython 多年稳定        |
| engine.py:101-107                        | play() missing 不重置 state                 | ERROR 已提示，UI 可自愈 |
| queue.py:50-57                           | A 面 Side 缺失 boundary 误算                | 正常链路不可达          |
| generator.py:44-49                       | 0 时长曲目不占容量                          | 宽容解析设计妥协        |
| schema.py:9-11                           | DB_PATH import 期计算                       | 进程内一次              |
| local_provider/mp3/delete/side_allocator | 非原子写/纯 ID3 误判/延迟 import/丢弃无提示 | 均同前轮回落理由        |

## 三、亮点

- D 系列核心实现正确、零回归；D0.2（log_level 值域）与 D2.1（logger 说明区）修复完整
- 版本/README/commit 三方一致（0.1.0.3，176373c）
- 各组实测验证充分（null/长度/0 值/小写级别均实测）

## 附录 A005：全量代码审计报告（第5轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json
> 方式：三路并行（utils+config / modules / ui）逐文件全文阅读 + git show 30f5348 修复 diff 核对 + 实测验证
> 状态：✅ 已完成（F 系列修复 2026-08-15 全部落地：F0-F4 共 15 项；全量回归 28 探针 PASS + 冒烟 OK + --version 0.1.0.5；cover 模块已补入库）
> 结论：P1 1 项（cover 模块未入库——仓库完整性）+ P2 5 项 + P3 7 项；最大发现为仓库级问题（历轮盲区）；问题密度 45→16→7→14→13

## 零、上轮修复复核清单（A004 / E 系列 15 项）

| 复核项             | 现状                                                                                   | 证据                         |
| ------------------ | -------------------------------------------------------------------------------------- | ---------------------------- |
| E 系列 15 项在位性 | ✅ 全部在位（commit 30f5348）                                                          | 主会话 grep 11 项 + 各组补查 |
| 引入回归           | ⚠️ E 系列暴露 4 处新缺口（E0.4 自冲突/E1.1 不完整/E2.1 未达成/E0.6 假安全感）          | 各组实测                     |
| 仓库完整性         | ❌ modules/cover/ 4 文件从未入库（.gitignore:52 裸 cover/ 误伤）——clone 后应用无法启动 | modules 组 git 核查          |

## 一、P0-P3 修复清单

### P1（高：仓库完整性）

| #    | 文件:行号                  | 类型 | 描述                                                                                                                                                                               | 建议                                                                           | 性质               |
| ---- | -------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------ |
| P1-1 | .gitignore:52（裸 cover/） | 12/9 | Python 模板"coverage"段的 cover/（无前导斜杠）匹配任意层级 → modules/cover/ 4 文件从未被 git 跟踪；换机器 clone 后 generator.py:5 顶层 import → ModuleNotFoundError → 应用无法启动 | 该行改为 /coverage/ 或删除；git add -f modules/cover/ 补入库（需用户确认执行） | 新增（仓库级遗留） |

### P2（中）

| #    | 文件:行号                                    | 类型 | 描述                                                                                                                            | 建议                                      | 性质                |
| ---- | -------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------- |
| P2-1 | engine.py:153-164                            | 4/3  | missing 分支不发 TRACK_CHANGED：引擎 _track 更新但 UI 展示不刷新；auto_flip 自然翻面遇 missing → 自动播放链中断                 | missing 分支补发 TRACK_CHANGED            | 新增（E2.1 未达成） |
| P2-2 | engine.py:195-202                            | 3/4  | flip 失败回滚不滚 _track（已被置为 B 面 missing 曲目）：回滚后 index 与 _track 错位                                             | 回滚时同步 self._track = 当前队列曲目     | 新增（E1.1 不完整） |
| P2-3 | deck_view.py:128-132 + 97-99                 | 1    | E0.4 自冲突：_on_track side=="A" 无条件 setEnabled(True) 覆盖 load_item 单面禁用——CD 播放必触发，翻面按钮对 CD 可用但点击无反馈 | setEnabled(side=="A" and len(sides)>1)    | 新增（E0.4 自冲突） |
| P2-4 | static_config.py:195-210 + model.py:22-23    | 2    | item_types side 字段未校验（E0.6 只覆盖 minutes_per_side）：误写 int → for s in 123 TypeError 确定性崩溃                        | E0.6 同机制覆盖 side（list + A/B 白名单） | 新增（E0.6 缺口）   |
| P2-5 | static_config.py:183-194 + settings.py:70-76 | 12   | E0.7 回退链自引用（两路径实测）：DEFAULT_REALISM_LEVEL 不在 levels 时 save 写无效档位 → 档位永久失效                            | 字面量 ∈ levels 校验/动态化               | 新增（E0.7 不完整） |

### P3（低）

| #    | 文件:行号                                       | 类型 | 描述                                                                                           |
| ---- | ----------------------------------------------- | ---- | ---------------------------------------------------------------------------------------------- |
| P3-1 | static_config.py:112-131 + shelf_view.py:99-100 | 2    | card_size 元素无 >0 下界（[0,90] → 按钮不可见）                                                |
| P3-2 | static_config.py:198-210                        | 2    | minutes_per_side 无 >0 下界（0 → 容量 0 → 生成静默失效）                                       |
| P3-3 | engine.py:177-179 + 82-84                       | 3    | _just_flipped 复位不完整（自动翻面遇 missing 残留 → SIDE_FLIPPED 延迟；play_prev 回 A 不复位） |
| P3-4 | edit.py:24-29 + regenerate.py                   | 1/13 | edit.remove_track 全删后直接 save_item 无 check_item——可制造空物品入库（与生成路径不一致）     |
| P3-5 | engine.py:80 + deck_view.py:128-136             | 1    | 空 A 面物品 side 误推导 "B"（boundary=0 时 index>=0 恒真）                                     |
| P3-6 | settings.py:104-115                             | 6    | 说明区缺 _load_from_disk/_config_cache/_VALID_LEVELS（四轮遗漏）                               |
| P3-7 | static_config.py:28 / deck_widget.py:31         | 2    | drag_threshold/spin_tick_ms 0 值无下界（点击即拖/QTimer 忙等）                                 |

## 二、参考级观察项（记录不修）

| 位置                                                                      | 描述                                   | 回落理由                       |
| ------------------------------------------------------------------------- | -------------------------------------- | ------------------------------ |
| main_window.py:94,171-173                                                 | message_label 无清除时机               | 不阻塞不崩溃，下次错误覆盖     |
| model.py:97 + path_check.py                                               | Item.missing_tracks 无消费方           | 播放链实时 is_missing 正确路径 |
| queue.py:37-42                                                            | prev 回 A 后 flipped 不复位            | side 由 index 推导             |
| engine.py:37-45                                                           | PlaybackEngine 无 shutdown             | GUI 单实例进程级生命周期       |
| retry.py:39 / convert.py:8 / logger.py:29-35                              | 不可达分支/inf 溢出/文件 handler 静默  | 均不可达或自愈                 |
| delete.py:31 / local_provider.py:17-22 / mp3.py:14 / side_allocator.py:16 | 延迟 import/非原子写/纯 ID3 误判/O(n²) | 同前轮回落理由                 |
| registry.py:37-40 / generator.py:44-49 / repository.py:150                | 单向告警/0 时长不占容量/秒级排序       | 同前轮回落理由                 |

## 三、亮点

- E 系列核心修复在位、零崩溃级回归；版本/README/commit 三方一致（0.1.0.4，30f5348）
- 各组实测验证充分（side=123/回退链两路径/CD 播放路径）
