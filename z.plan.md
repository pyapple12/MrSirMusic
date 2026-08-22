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
