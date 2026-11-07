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

## 十、UI 壳层升级计划（2026-11-05 评审定案，附录轨道）

> UI 壳层升级方案（原"第十节 PL1-PL3"展开版）已按新规范移至文末附录 PL001/PL002/PL003——方案记录方式自 2026-11-05 起对齐 CapsulePulse 附录轨道（见 AGENTS「任务清单纪律」）；评审素材 `.temp/ui_review_shots.py`（贴皮渲染 9 图，改代码后重跑即得 before/after 对比）。

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

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json（user_config.json 运行时生成不审）；三路并行逐文件全文阅读 + 交叉验证（grep 调用点、venv 实测 mutagen/Path 语义）
> 结果：**P 级 45 条（P0 1 / P1 15 / P2 29）/ 参考级观察项 14 条（5 条用户复核提升 P 级）**
> 状态：✅ 已修复（2026-08-15：B 系列 B0-B4 共 49 项全部落地；探针 18 全量回归 PASS + 冒烟 OK + --version 0.1.0.1；任务清单见 x.progress.md B 系列）

- **上轮复核**：无上轮（首轮审计）
- **P0-P3（45 条）**：P0-1 播放三路径（下一首/上一首/翻面）缺缺失检查静默卡死；P1 15 条——DB_PATH 四模块值绑定、generate 空列表生成空物品、档位链路断线零接线、主题零调用、右键三信号零接收、停止唱针不抬起、换物品封面残留、errorOccurred 未连接、生成槽异常炸出、误删共享封面、probe 全量读盘、data_dir 硬编码、日志硬编码、格式清单双处维护、配置类型不校验；P2 29 条——死代码 13 处、注释失实 4 处、防御缺口（retry 参数/档位枚举/静默失败）、配置死键 3 处、默认档位三处漂移、性能（migrate 每连必跑/双排序/全量读配置）、安全（unlink 路径未消毒）、事件总线静默+无去重、resolve 无法区分原因、wear 每帧 IO、0 容量幽灵物品、加曲防重缺失、进度时长用标签值、色硬编码 8 处、intensity TypeError、dragMoveEvent 未实现
- **参考级观察项 14 条**（5 条提升 P 级，9 条维持豁免）：重播依赖 Qt 运行时需验证/注册表占位契约/migration 非原子单条无风险/格式清单一致/closeEvent 进程级生命周期/绘制参数豁免/单例懒加载导入期/logger 纯理论/非法档位 UI 自愈/延迟导入豁免
- **亮点**：分层架构合规（modules 零 UI 依赖）；容错降级链路完整；TDD 全覆盖 14 探针；三路交叉验证一致

## 附录 A002：全量代码审计报告（第2轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json；三路并行逐文件全文阅读 + git show 0485b8a 修复 diff 核对 + 实测验证
> 结果：**P 级 16 条（P0 1 / P1 8 / P2 7）/ 参考级观察项 16 条（用户复核全部维持豁免）**
> 状态：✅ 已修复（2026-08-15：C 系列 C0-C4 共 17 项全部落地；探针 22 全量回归 PASS + 冒烟 OK + --version 0.1.0.2；任务清单见 x.progress.md C 系列）

- **上轮复核（B 系列 49 项）**：关键修复 11 项抽查全部在位；⚠️ 归档缺口 3 项（P1-7 修复不完整、P1-8/P1-9 无对应条目）、P1-1 migration 未完全收敛、event_bus 去重部分、漏改 3 处；引入回归 0（B0.4 接线暴露新缺陷 P0-1）
- **P0-P3（16 条）**：P0-1 档位切换动画冻结（set_animations_enabled(True) 不重启 timer，B0.4 引入）；P1 8 条——errorOccurred 未连接遗留、probe 全量读盘遗留、白名单覆盖不完整（log_level/music_dir 导入即崩实测）、import_dialog 兜底遗留、封面残留不完整、封面失败语义矛盾（B0.2 引入）、_connect 不 ensure_dir、migration 值绑定遗留；P2 7 条——progress_percent 不钳制、说明区失实、settings 路径/回调/延迟导入、retry 类型边界（times=True/delay 字符串实测）、event_bus 去重对 bound method 无效、文案过时、回退字面量三处残留
- **参考级观察项 16 条**（全部维持豁免）：监听器累积无退订/flip 返回值不一致/flipped 不复位/空物品 load/1s 定时器/硬编码策略/delete 静默/COVERS_DIR 派生/三处格式清单/单槽迁移/翻面按钮态/closeEvent/进度条无 QSS/菜单注释残留/延迟 import
- **亮点**：B 系列 46/49 在位零回归；settings 缓存/迁移路径缓存/进度时长兜底/delete 路径消毒核查正确；探针体系稳定

## 附录 A003：全量代码审计报告（第3轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json；三路并行逐文件全文阅读 + git show c8844d2 修复 diff 核对 + 实测验证
> 结果：**P 级 7 条（P2 7，无 P0/P1）/ 参考级观察项 14 条（用户复核全部维持豁免）**
> 状态：✅ 已修复（2026-08-15：D 系列 D0-D4 共 12 项全部落地；探针 24 全量回归 PASS + 冒烟 OK + --version 0.1.0.3；任务清单见 x.progress.md D 系列）

- **上轮复核（C 系列 17 项）**：全部在位（commit c8844d2）；引入回归 0；⚠️ C0.5 白名单覆盖面不完整（effects/item_types 无校验、容器键混收）、C2.3 percent 只修上界、C0.5 log_level 值域残留、C1.1 migration 死 import 残留
- **P0-P3（7 条，全 P2）**：白名单覆盖面缺口（effects.levels 非 dict 导入即崩实测）；log_level 值域未校验（小写穿透白名单 setLevel 崩）；progress_percent 下界未钳（-50 实测）；SIDE_FLIPPED B 面内重复发射（flipped 不复位）；ERROR 后 state 不同步（C0.2 引入）；migration DB_PATH 死 import 残留；logger 说明区失实（B 系列残留）
- **参考级观察项 14 条**（全部维持豁免）：监听器累积/回调重入/migrate 异常连接泄漏/分配丢弃无提示/延迟 import/非原子写/纯 ID3 误判/mkdir 每次调用/null 穿过/三处格式清单/单例懒加载/翻面按钮态/菜单注释残留/进度条无 QSS
- **亮点**：C 系列 17 项零回归；C0.1 动画时序穷举无冻结无泄漏；版本/README/commit 三方一致（0.1.0.2）

## 附录 A004：全量代码审计报告（第4轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json；三路并行逐文件全文阅读 + git show 176373c 修复 diff 核对 + 实测验证
> 结果：**P 级 14 条（P2 7 / P3 7，无 P0/P1）/ 参考级观察项 13 条（用户复核全部维持豁免）**
> 状态：✅ 已修复（2026-08-15：E 系列 E0-E4 共 15 项全部落地；探针 26 全量回归 PASS + 冒烟 OK + --version 0.1.0.4；任务清单见 x.progress.md E 系列）

- **上轮复核（D 系列 12 项）**：全部在位（commit 176373c）；引入回归 0；⚠️ D 系列暴露 4 处新缺口（drag_threshold 漏项实测 null 崩、card_size 过滤后长度契约破坏实测解包崩、animation 0 值除零、D0.4 暴露按钮态漂移）+ D0.5 引入"错误提示被'已停止'覆盖" + 3 处说明区残留
- **P0-P3（14 条）**：P2 7——drag_threshold 白名单漏项（A003 点名仍未入）；card_size 长度契约（过滤后长度≠2 双变量解包崩）；animation 0 值除零（record_spin_ms 无下界）；翻面按钮态漂移（B 面内切歌/prev 回 A/flip 单向）；错误提示被状态覆盖（D0.5 引入，确定性复现）；minutes_per_side 无白名单（"abc" 导入崩）；default_level 无值域校验（回退链自引用）；P3 7——flip 失败 _just_flipped 悬挂；load_item 不重置 state；missing 曲目 index 不回滚；migration 说明区 DB_PATH 残留；progress 说明区失实；三处函数内延迟 import；static_config/convert/retry 说明区残留组
- **参考级观察项 13 条**（全部维持豁免）：翻面按钮纯显示态/colors 内部值无白名单/绘制色硬编码 8 处/effects.levels 内部未校验/监听器累积/私有 API/play missing 不重置 state/A 面 boundary 误算/0 时长不占容量/DB_PATH import 期计算/非原子写等历轮同因
- **亮点**：D 系列核心实现正确零回归；D0.2 log_level 值域与 D2.1 logger 说明区修复完整；实测验证充分（null/长度/0 值/小写级别）

## 附录 A005：全量代码审计报告（第5轮，2026-08-15）

> 范围：main.py + config/、modules/、ui/、utils/ 全部 .py + 5 个 json；三路并行逐文件全文阅读 + git show 30f5348 修复 diff 核对 + 实测验证
> 结果：**P 级 13 条（P1 1 / P2 5 / P3 7）/ 参考级观察项 14 条（用户复核全部维持豁免）**
> 状态：✅ 已修复（2026-08-15：F 系列 F0-F4 共 15 项全部落地；探针 28 全量回归 PASS + 冒烟 OK + --version 0.1.0.5；cover 模块已补入库；任务清单见 x.progress.md F 系列）

- **上轮复核（E 系列 15 项）**：全部在位（commit 30f5348）；⚠️ E 系列暴露 4 处新缺口（E0.4 自冲突/E1.1 不完整/E2.1 未达成/E0.6 假安全感）；❌ 仓库完整性：modules/cover/ 4 文件从未入库（.gitignore 裸 cover/ 误伤）——clone 后应用无法启动（历轮盲区）
- **P0-P3（13 条）**：P1-1 仓库完整性——cover 模块未入库（.gitignore:52 裸 cover/ 匹配任意层级，git add -f 补入库）；P2 5——missing 分支不发 TRACK_CHANGED（UI 展示不刷新/自动翻面链中断）；flip 失败回滚不滚 _track（index 与 _track 错位）；CD 单面按钮 E0.4 自冲突（setEnabled 无条件覆盖禁用）；item_types side 字段未校验（误写 int 确定性崩）；回退链自引用两路径实测；P3 7——card_size/minutes_per_side 无 >0 下界；_just_flipped 复位不完整；edit 全删后无 check_item 可造空物品；空 A 面 side 误推导 "B"；settings 说明区缺三项；drag_threshold/spin_tick_ms 0 值无下界
- **参考级观察项 14 条**（全部维持豁免）：message_label 无清除时机/missing_tracks 无消费方/flipped 不复位/无 shutdown/不可达分支与静默/延迟 import 与非原子写同因/单向告警与 0 时长同因
- **亮点**：E 系列核心修复在位零崩溃级回归；版本/README/commit 三方一致（0.1.0.4）；实测充分（side=123/回退链两路径/CD 播放路径）

## 附录 PL001：布局修缮与占位图重绘（2026-11-05 立项）

> 状态：✅ 已完成（2026-11-05 收口，全量 14 探针 PASS + 三档截图终审读图通过；任务组见 x.progress.md「PL001」）。**依据**：V0.1.1.0 贴皮截图评审（素材 `.temp/ui_review_shots.py`，方法 = F:\Collection taste-skill critique 十四遍观察法 + app-screens + game-ui-ux/game-feel），评审总评 ≈5.8/10，差距在壳层不在拟物控件。

**定案口径**

- 三大观感硬伤定案：① 占位图 = 1×1 纯红像素（#ff0000）拉伸成唱片中心标签，刺眼；② 唱机区垂直节奏崩坏（曲目标签→按钮、按钮→滑条两段 ~130-180px 偶然空洞；1440 宽按钮拉伸成巨条；900 窄窗挤压出横向滚动条）；③ QSS 覆盖不全（物品库详情区/置物架滚动区/组框白块与深色窗割裂）
- 占位图定案：程序化生成 128×128（深胶木底 + 同心纹 + 音符刻痕），延续拟物质感，不走"找图"路线
- 布局定案：按钮固定宽 ≤96px 居中成排（不再全宽拉伸）；滑条区最大宽 420px；垂直间距用 addSpacing 有意化（呼吸留白 ≠ 偶然空洞）
- 置物架定案：card_size [128,128] + 封面缩略图标 + 两行文本（名称 / 形态·曲数）；组框 margins 修卡片溢出
- 最小窗口定案：setMinimumSize(980, 640)
- 版本定案：收口推进 `base.json` → `0.1.2`（三段式，commit 标题 V0.1.2.1 起）

**明确不做**：本 PL 不改任何行为（拖放/右键/选中/播放语义零变更）；唱机形态分化 → PL002；主题色板分层 → PL003。

**实施与证据**：逐条做法与验证见 x.progress.md「PL001」组；评审素材重跑 `.temp/ui_review_shots.py` 即得 before/after。

## 附录 PL002：唱机形态分化与库列表行重设计（2026-11-05 立项）

> 状态：✅ 已完成（2026-11-05 收口，全量 14 探针 PASS + 三形态截图终审读图通过；任务组见 x.progress.md「PL002」）。

**定案口径**

- 语义冲突定案：现版唱机区恒为黑胶转盘 + 唱针——播磁带时左侧磁带卡与右侧黑胶唱机并存、CD 也显示唱针（CD 无唱针），属拟物语义冲突，必须随 `item.type.key` 分形态
- 三形态定案：vinyl = 现状转盘 + 唱针（拖拽寻曲仅黑胶）；cassette = 带仓壳 + 观察窗双卷轴（复用共享绘制）+ 双飞轮；cd = 银灰碟面 + OddEven 真镂空中心孔 + 封面环带 + 夹持爪（无唱针）
- DRY 定案：卷轴绘制从 record_widget 迁出为共享 `ui/widgets/parts.py`（record_widget 与 deck_widget 共用），不复制两份
- 交互定案：非黑胶时唱针命中测试直接失败（needle_dropped / needle_drag_started 零发射）；进度滑条 scrub 三态全类型可用
- 库列表定案：条目文本两行化（名称主行 / 形态·Tag·时长次行），缩略图标保留
- 版本定案：收口推进 `0.1.2`（与 PL001 合并为同一内容版本，用户定案；commit 标题 V0.1.2.1 起）

**明确不做**：磁带/CD 的专属音效（磁带机械声已存在、CD 数字静音为拟物正确）；3D 视图（Spun 参考结论：2D 已覆盖全部交互语义）。

**实施与证据**：逐条做法与验证见 x.progress.md「PL002」组。

## 附录 PL003：主题精修与交互补充（2026-11-05 立项）

> 状态：✅ 已完成（2026-11-05 收口，全量 14 探针 PASS + 全套截图终审读图通过；任务组见 x.progress.md「PL003」）。

**定案口径**

- 方向定案：ui.json 暖棕深色主题贴皮评审成立且气质正确，**不换方向**，做"精修补全"——评审误判修正记录（原 P7"换主题"不成立）
- 色彩分层定案：colors 增 `surface`（面板）/ `panel`（输入面）/ `muted`（弱文本）/ `disabled`（禁用面）四级，全部外置 ui.json（colors 整 dict 校验语义免白名单改动）
- QSS 精修定案：QGroupBox / QLineEdit / QComboBox / QMenu / QToolTip / disabled 态 / 下拉列表 / indicator 全组件覆盖，取色走 themes.py c 字典
- 对话框定案：导入按流程四分组（①音频文件 ②载体类型 ③命名与归类 ④封面来源），字段与校验零变更；设置加档位说明文案（代码内常量——UI 文案非业务参数不入 json）
- 快捷键定案：空格 = 播放/暂停、←/→ = 上下曲、F = 翻面（WindowShortcut 级）；播放控制按钮 setFocusPolicy(NoFocus) 防聚焦按钮空格双触发；Ctrl+F 搜索第一版无搜索框不做
- 版本定案：收口推进 `0.1.4`（commit 标题 V0.1.4.1 起）

**明确不做**：深浅色双主题跟随（Windows 桌面常驻场景单一深色已够，双主题进 y.problem 备忘）；自定义皮肤体系。

**实施与证据**：逐条做法与验证见 x.progress.md「PL003」组；收口时真机核对三项（中文排版层级 / 高 DPI 清晰度 / 拖拽视觉反馈）交用户。

## 附录 A006：全量代码审计报告（第6轮，2026-11-05）

> 范围：main.py + config/modules/ui/utils 全部 .py + 5 个静态 json；三路并行只读代理（modules 核心 / playback / UI+入口+配置）+ 交叉汇总去重；P 级证据经主会话抽查坐实；探针体系（14/14 PASS）为行为事实源
> 方式：逐文件全文阅读 + 回归复核（A005/F 系列 15 项 + G/H/PL 批次抽查，git show 双核对）+ 13 维度对照
> 结果：**P 级 16 条（P2 4 / P3 12，无 P0/P1）/ 参考级观察项 30 条（全部维持豁免，其中需产品定案 2、需 Qt 行为验证 3）**
> 状态：✅ 已修复（2026-11-05：FIX006 共 17 条全部落地——16 条 P 级 + 验证收尾；全量 14 探针 PASS + --version 0.1.4；反向验收逐条对照原问题；任务清单见 x.progress.md FIX006）
> 编号备注：本轮起启用 FIX 三位轨道，历史无 FIX 组——默认 max+1 应为 FIX001，用户裁决对齐轮次取 A006/FIX006（记录该次例外）

- **零、上轮修复复核**：A005/F 系列 15 项全部 ✅ 在位（三路 grep + `git show 5ab69ca`/`30f5348` 双核对）；G/H/PL 批次抽查（G0.1-G0.3/G2.1/G3.1-G3.2、H0.1-H0.6/H1、PL001-003 关键修复）全部 ✅；零回退零漏改；勘误——30f5348 实为 E 系列（第 4 轮），F 系列 = 5ab69ca
- **一、P0-P3（16 条）**：
  - **P2 4**——① regenerate 缺 G0.2/F2.1 等价保护（0 容量类型物品重新刻录 → 空物品入库；minutes_per_side 调小 → 静默丢歌无提示）；② engine `_pending_seek` 错误链残留（errorOccurred 不清 pending → 旧偏移应用在后续错误曲目上）；③ 手动切缺失曲发声错位（missing 分支不 stop 旧媒体不发状态，UI 展示切曲但扬声器继续放旧曲；自动链无此问题）；④ 播放中切拟真档位底噪不恢复（sounds.set_level 仅 >0 时调音量不重启底噪，concise→refined 静音至下次态迁移）
  - **P3 12**——① 拖针收尾定时器永久空转（30ms 空重绘，常见路径）；② scrub 拖动中时间文本预览/真实跳变 + 注释失实；③ 容错登记制补登记 6 处（delete 封面查询静默 True 与 unlink 静默 pass、migration 版本读取归 0、H1 面内时长缺失降级 ×2、未知形态回退 vinyl/circle ×2、progress 函数内 QTimer 特许例外）；④ item_types 缺 shape ∈ {circle,rect} 校验（坏 shape 静默按黑胶绘制）；⑤ 磁带物理常量三处漂移（基准速度双份 + deck 侧半径界值内联，PL002 DRY 执行不彻底）；⑥ 置物架缩略图 56×56 硬编码未走 ui.json（thumbnail_size 契约旁置）；⑦ load_item 首曲缺失走 Qt 泛化英文错误（play 路径为 file_missing 中文——分类漂移）；⑧ 秒→毫秒 `int(x*1000)` 三处散布（convert 已有反向函数）；⑨ 死代码组（Side.remove_track/factory.remove_track（F2.1 连带）/remaining_seconds/repository.load_item/DEFAULT_REALISM_LEVEL 死 import×2/**bump_play_count 全链零写入点（播放计数恒 0——接线或移除需拍板）**）；⑩ import 纪律（delete 函数内延迟 import 无依据 + cover 包循环依赖无例外说明）；⑪ 文档一致性组（AGENTS"当前机器版本 0.1.1"过期 / main.py 仍写四段式 / H 系列编号代码注释与 x.progress 错位）；⑫ 快捷键跨类调用 `deck_view._on_play_clicked()` 私有方法
  - **需产品定案（观察项内，不占编号）**：空 A 面 + B 有曲物品可生成（generate_check 不拦，F3.1 语义边界）；播放计数是否属第一版承诺功能（与⑨联动）
- **二、参考级观察项 30 条**（全部维持豁免；摘要分类）：需 Qt 行为验证 3（seek_side(1.0) 曲末 EndOfMedia、LoadedMedia 回调内 setPosition、键盘操作滑条残留 wind）；设计使然/已文档化 8（EndOfMedia 回调链 setSource+日志、auto_flip 载入快照、空闲期每秒 PROGRESS(0)、容量双实现刻意同口径、queue.prev 不复位 flipped（A005 遗留）、created_at 同秒排序、embedded_cover 预留、decoder 占位零消费）；性能可接受 6（repository 每操作建连、paintEvent 每帧渐变、mark_missing 逐曲 stat、库列表重读封面、_ensure_player 幂等、rogue Side 已告警）；纯理论/轻微 13（mid-session 删库缓存、edit 回滚无日志、event_bus id() 碰撞、registry 误命中、probe 误判（A005 已登记）、空态拖针文案、载入后进度残留、dnd 损坏 mime、save_config 回调未净化、_round_rect_path 内层 import、新载体键需同步 deck_widget 分支（契约提示）、registry.default_level 仅探针消费、deck_widget 空态事件防护（需桥空态发事件才可达））
- **三、亮点**：A005 全部修复 + G/H/PL 三大批次关键修复零回退零漏改（三路独立 git show 双核对）；容错登记制首次存量盘点即产出（P3 制度生效证据）；三路交叉勘误上轮提交号（30f5348=E 系列 vs F=5ab69ca）；playback 主链走查无确定性缺陷；版本三方一致（0.1.4）

## 附录 A007：全量代码审计报告（第7轮，2026-11-06）

> 范围：main.py + config/modules/ui/utils 全部 .py + 5 个静态 json；三路并行只读代理 + 交叉汇总去重；基线 commit 1289729（FIX006，V0.1.4.2）
> 方式：FIX006 修复在位性回归复核（git show 1289729 全 diff 逐项）+ 修复自身新缺陷定向排查 + 13 维度对照；P 级证据经主会话抽查坐实
> 结果：**P 级 6 条（P2 1 / P3 5，无 P0/P1）/ 新增观察项 14 条（维持豁免）；A006 已定案 30 条观察项不重报（相关代码未变化）**
> 状态：✅ 已修复（2026-11-05：FIX007 共 7 条全部落地——1 条 P2 + 5 条 P3 + 验证收尾；全量 14 探针 PASS + --version 0.1.4；反向验收 playbackState StoppedState 断言覆盖；任务清单见 x.progress.md FIX007）
> 编号备注：A007/FIX007 同号绑定对齐轮次（本轮恰为 max+1，无例外）；A006 观察项未提升（float 截断 1 条维持"需定案"标记）

- **零、FIX006 回归复核（21 项核查）**：全部 ✅ 在位零回退——modules 6（regenerate 防护口径确等/delete 告警/shape 校验提取/死代码删除彻底/播放计数写链移除 schema 未动/cover 断环 re-export 无破坏）、playback 5（error 清 pending/missing 停声/首曲预检/ms 收敛/H 编号）、UI+配置 10（regenerate 捕获/set_level 恢复/收敛自停互斥排查/on_progress 挂起/_sanitize_item_types 行为等价/REEL 单源/缩略图配置/死 import/文档一致/toggle_play）；版本三方一致 0.1.4 ✅
- **一、P0-P3（6 条）**：
  - **P2 1**——FIX006.11 自身引入回归：播放中载入"首曲缺失"物品 → 发 stopped（UI 冻结停止态）但不 stop 旧媒体 → 扬声器继续放旧曲（原 setSource 虽错误但带停声副作用，预检跳过 setSource 后副作用丢失；engine.py:160-172 缺失 elif 分支）；修法 = 缺失分支补 player.stop()（一行）
  - **P3 5**——① _pending_seek 跨 setSource 竞态窗口（play_next/play_prev/flip/seek 入口不清，遗留 H1；修法 = 三换源入口进入时清，stop 是否清并入统一决策）；② cover/providers 断环不彻底（_build_registry 函数内延迟 import 环消后无必要 + COVERS_DIR re-export 零消费死重量，FIX006.14 自留）；③ deck_view.py:193-195 秒→毫秒第 4 处散布（FIX006.12 漏检 UI 层，"唯一入口"声明被打破）；④ FIX006 执行残留文档组 5 处（model.py 说明区已删方法残留/factory.py 头注失实/edit.py 幽灵符号/repository.py 尾注矛盾/progress_widget.py 说明区与新行为矛盾）；⑤ static_config.py:179-180 不可达防御分支（双保险语义未标注）
- **二、参考级观察项 14 条**（维持豁免）：需产品定案 1（item_types 放行 float 被 from_config int() 静默截断——现 json 全 int 纯理论）；需验证 2（拖针收敛窗口切档唱针冻结半程、stop() 后 LoadedMedia 应用 pending 续播语义）；设计使然/幂等冗余 5（自动链缺失曲双 stopped 双 stop、_ensure_player 先于预检、auto_flip flipped 不对称 E2.1/E1.1 语义分立、regenerate 不复跑 validate_selection、progress duration 兜底未入登记制——下轮盘点补录）；轻微 6（import_cover_file 外层静默（调用链有告警）、_row_to_item 未知类型 0 容量降级（有告警）、spin 缺省 2000 同文件三处、re-export noqa 待 FIX007 处置、说明区未覆盖新增逻辑、shelf_view"防除零"注释措辞）
- **三、亮点**：FIX006 全部 17 条修复零回退（三路 git show 1289729 逐项核对）；修复自身缺陷被紧随审计当场抓住（审计-修复闭环证据）；收敛自停与惯性/快捷键互斥、set_level 与 set_active 互斥、_sanitize_item_types 行为等价性三项重点排查全过；上轮收尾全量回归曾红灯一次（setattr 缩进），探针当场抓住修复——验证链完整

## 附录 PL004：game-ui-ux 对照审查与补强（2026-11-07 立项）

> 状态：✅ 已完成（2026-11-07 收口，全量 14 探针 PASS + 十图终审读图通过；任务组见 x.progress.md「PL004」）。

**定案口径**

- 方向定案：以 `.agents/skills/game-ui-ux`（引擎中立游戏 UI 架构，2026-11-07 收录）为审查基线，对照 ui/ 层逐维审查 + 热点当场修——审查维度：焦点体系（QShortcut WindowShortcut 与按钮 NoFocus 组合下的派发一致性、Tab 序、初始焦点确定性、卡片聚焦可见性）、缩放安全区（980×640 最小窗下 deck 居中构图挤压行为、shelf 分组流式换行、library 行省略策略）、事件驱动纪律（UI 状态更新零轮询残留）
- 产出形态定案：审查发现逐点注记于任务条目勾选注记；可修热点当场修（文件/函数级）；需产品决策项转 y.problem.md 备忘（不占编号）
- 版本定案：收口推进 `0.1.5`（commit 标题 V0.1.5.1 起）

**明确不做**：手柄/控制器导航（桌面鼠标键盘场景）；UI 屏幕状态栈重构（主窗 + 两对话框已够）；多断点响应式布局；深浅色双主题（PL003 已定案进 y.problem 备忘）。

**实施与证据**：逐条做法与验证见 x.progress.md「PL004」组。

## 附录 PL005：Blender 拟物贴图管线（2026-11-07 立项）

> 状态：📌 待实施（任务组见 x.progress.md「PL005」；硬依赖环境门禁 PL005.1——Blender + blender-mcp 探活不过则全组挂起等环境，不降级实施）。

**定案口径**

- 方向定案：拟物视觉升级走「Blender 预渲染烘焙贴图 + QPainter 分层合成」——运行时仍纯 QPainter、零新 Python 依赖，贴图为静态资产；产物 PNG 入 `data/textures/`（纳入版本控制），.blend 源文件不入库（留 `.temp/blender_src/`）
- 贴图清单定案（四类）：`vinyl_disc`（盘面沟槽+高光）/ `cassette_shell`（塑料壳+观察窗质感）/ `cd_disc`（薄膜干涉彩虹反射）/ `walnut_panel`（胡桃木面板，无缝平铺）；统一规格 512×512、key light 左上统一光照
- 档位接线定案：concise=纯矢量绘制（现状不变）/ refined=贴图底+简化高光 / realistic=贴图全量+动态层全开；`effects.json` 各档加 `texture` 开关（bool），deck_widget/record_widget 经 `set_realism(level)` 切换绘制路径
- 容错定案：贴图文件缺失/加载失败 → 回退现有矢量绘制 + 告警一次（AGENTS 容错登记制随 PL005.4 补登记）
- 技能路由定案：制作走 `.agents/skills/blender-director` 入口 + materials / texture-workflow / lighting / rendering 子技能 + qa-review 截图门禁（技能已收录本项目 `.agents/skills/`，见其 README）
- 版本定案：收口推进 `0.1.6`（commit 标题 V0.1.6.1 起）

**明确不做**：3D 实时渲染/视差；新 Python 依赖（贴图消费只用 QPixmap）；modules 层改动（贴图为 ui 层装饰资产）；4K 级贴图（512 档覆盖 96-128px 显示目标）；AI 生图替代 Blender 烘焙（光照不可控）。

**实施与证据**：逐条做法与验证见 x.progress.md「PL005」组。
