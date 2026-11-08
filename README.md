# MrSirMusic —— 拟物音乐播放器

[![Version](https://img.shields.io/badge/Version-0.2.6-blue.svg)](../../releases)

> 版本口径：徽章 = 代码版本（三段式 `X.Y.Z`，与 `config/static/base.json` 即时同步）；发布版本以 GitHub Releases 为准；commit 标题用四段式 `VX.Y.Z.R`（修订号只进提交历史，口径见 `AGENTS.md`"版本双轨"）。
[![Python](https://img.shields.io/badge/Python-3.14+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 项目简介

Windows 拟物音乐播放器（Python sidecar + Tauri/Web 前端）：不使用文件夹/播放列表，而是通过**拟物物品**（黑胶/磁带/CD）承载音乐。物品由用户手动选歌**生成**（硬容量约束），持久保存在**物品库**（`music/`），可陈列于**置物架**（按 Tag 分类），点选放入**拟物唱机**播放。业务与播放核心在 Python（`modules/` + `sidecar/` 进程），界面为 Web 前端（`tauri/`），无联网依赖。

## 目录

- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [技术架构](#技术架构)
- [项目结构](#项目结构)
- [许可证](#许可证)

## 快速开始

### 环境要求

- Windows 10/11
- Python 3.14 或更高版本
- Rust toolchain（[rustup](https://rustup.rs) 安装）与 Node.js 22+（Tauri 壳与前端构建所需）

### 安装

```bash
git clone git@github.com:pyapple12/MrSirMusic.git
cd MrSirMusic

# 创建虚拟环境并安装依赖
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 使用说明

### 图形界面（Web 版，唯一前端）

```bash
cd tauri
npm install
npm run app        # 一键起 Tauri 窗口 + Python sidecar
```

> 注意：`.venv` 是机器绑定的，换机器后需按上面流程重建虚拟环境。

### 生成物品

1. 点击顶部 **导入/生成…** 按钮
2. 选择音频文件（mp3/flac/wav/m4a，支持多选）
3. 选择载体类型（黑胶 22 分钟/面、磁带 30 分钟/面、CD 80 分钟/面）
4. 填写名称与 Tag（Tag 用于置物架分组陈列）
5. 选择封面来源（占位图 / 本地图片）→ 确认生成

物品自动做容量校验与 AB 面顺序分配，生成后出现在物品库与置物架。

### 播放

- 单击置物架卡片 / 物品库右键"播放" / 拖动物品卡片到唱机区域
- 唱机随载体切换拟物形态：黑胶 → 转盘唱针（可拖拽寻曲）、磁带 → 磁带仓（观察窗卷轴）、CD → 碟舱
- 播放/暂停、上下曲、翻面按钮与进度滑条（可直接拖动寻曲）
- 键盘快捷键：`空格` 播放/暂停、`←`/`→` 上一首/下一首、`F` 翻面
- **拖拽唱针寻曲**：抓住唱机右侧唱针尖端拖到任意位置松手，即按面内比例跳转（跨曲自动换曲；按住 Shift 可精调）
- 面内播放结束自动切下一首（A 面末自动翻面取决于"自动翻面"设置）
- 拟真音效（随档位）：黑胶播放时有爆裂/嘶声底噪与落针刮擦声、翻面落针声；磁带换曲有机械咔哒声；简洁档静音
- **拟物贴图（精致/真实档）**：黑胶盘面、CD 碟面（含彩虹反射与中心孔）、磁带壳、置物架卡片木纹底为 Blender 烘焙纹理（`data/textures/`）；贴图缺失自动回退矢量绘制

### 设置（拟真度）

点击顶部 **设置…** 按钮：拟真度档位（简洁/精致/真实——磨损贴图、转盘动画与拟真音效强度）与自动翻面，保存后重启保持。

## 技术架构

Tauri 2 桌面壳（Rust + WebView2）+ Vue 3/TypeScript 前端（`tauri/src/`）+ Python sidecar 后端进程（`sidecar/`，stdio JSON Lines 协议）。业务与播放核心在 `modules/`（零 UI 依赖），由 sidecar 进程承载、Rust IPC 桥转发，前端为可替换层；主题经 `config/static/ui.json` → CSS 变量单源注入；侧车崩溃自动重启（指数退避）。离线优先，无联网依赖；打包/安装器未做（后续发布线，见 `y.problem.md`）。

## 项目结构

```
MrSirMusic/
├── modules/                   # 业务核心层（无 GUI 依赖，sidecar/Web 共享复用）
│   ├── items/                 # 领域模型（黑胶/磁带/CD 物品）
│   ├── rules/                 # 规则引擎（容量预算/AB面语义）
│   ├── generator/             # 生成编排（选歌 → 物品）
│   ├── library/               # 物品库持久化（music/items.db）
│   ├── tagging/               # 标签解析（置物架分类）
│   ├── cover/                 # 封面服务（占位图兜底）
│   └── playback/              # 播放核心（引擎 + decoders 子包）
├── sidecar/                   # 侧车进程（stdio JSON Lines 协议暴露业务 + 播放引擎，Web 版后端）
├── config/                    # 配置（静态 json 驱动 + 用户配置）
├── tauri/                     # Web 前端（Vite+Vue3+TS）+ Rust 壳（src-tauri/，IPC 桥）
├── data/                      # 静态资源（Blender 烘焙贴图 textures/ + 合成音效 sounds/ + 占位图）
├── utils/                     # 通用工具（零业务依赖）
├── music/                     # 物品库用户核心数据（items.db + covers/，gitignore 内容）
├── requirements.txt           # Python 依赖列表
├── LICENSE                    # MIT 许可证
└── README.md                  # 本文件
```

## 维护者

- 作者：[pyapple12](https://github.com/pyapple12)
- 邮箱：takechance_bao@188.com

## 许可证

本项目基于 [MIT 许可证](./LICENSE) 开源。
