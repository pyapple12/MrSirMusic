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
