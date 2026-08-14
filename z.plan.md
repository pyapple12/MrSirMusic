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
4. 版本号单一来源：base.json `version` 字段
5. 正式文件注释禁止 `.reference/` 标注；参考信息只允许在 `.temp/` 或文档中
6. 音频数组约定：统一 `(N, 2) float32 [-1, 1] @ 44100Hz`（为后续效果器预留）
7. 错误策略（沿用 MrAutoDJ 系）：不崩溃、不阻塞、有提示、能自愈

## 八、第一版验收清单

- [ ] `--version` 输出版本（base.json 单一来源）
- [ ] 文件多选导入 → 读标签 → 生成物品（容量校验 + AB 面分配）
- [ ] 物品库浏览 / 置物架按 Tag 陈列 / 唱机播放（进度/翻面）
- [ ] 修正手段（重新刻录/换歌编辑/删除）
- [ ] 拟真度三档切换生效（重启保持）
- [ ] 退出重启后物品库完整恢复

## 九、后续路线（扩展位，第一版不做）

1. **Web / Godot UI**：modules/ 复用不变，只换 ui/ 层；core API 需暴露为 HTTP/WebSocket 时在 modules 外加 server.py 适配层
2. **LLM 选曲**：只动 modules/generator（"需求 → 自动选曲"入口），领域层不动
3. **网络封面**：modules/cover 增加 network provider（已留接口）
4. **置物架更换**：Shelf 实体化（容量/形态），物品库不动
5. **独立解码进程**：decoders 注册表已预留，可演进为进程隔离（SpotAmp 管道模式）
