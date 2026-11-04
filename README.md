# MrSirMusic —— 拟物音乐播放器

[![Version](https://img.shields.io/badge/Version-0.1.1.0-blue.svg)](config/static/base.json)
[![Python](https://img.shields.io/badge/Python-3.14+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 项目简介

Windows 拟物音乐播放器（Python + PySide6）：不使用文件夹/播放列表，而是通过**拟物物品**（黑胶/磁带/CD）承载音乐。物品由用户手动选歌**生成**（硬容量约束），持久保存在**物品库**（`music/`），可陈列于**置物架**（按 Tag 分类），点选放入**拟物唱机**播放。第一版范围：拟物 + 播放 + 生成 + 基础 UI，无联网依赖。

## 目录

- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [项目结构](#项目结构)
- [许可证](#许可证)

## 快速开始

### 环境要求

- Windows 10/11
- Python 3.14 或更高版本
- pip（Python 包管理器）

### 安装

```bash
git clone git@github.com:pyapple12/MrSirMusic.git
cd MrSirMusic

# 创建虚拟环境并安装依赖
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 使用说明

### 图形界面（默认）

```bash
.\.venv\Scripts\python.exe main.py

# 查看版本
.\.venv\Scripts\python.exe main.py --version
```

> 注意：`.venv` 是机器绑定的，换机器后需按上面流程重建虚拟环境。

### 生成物品

1. 菜单 **文件 → 导入/生成物品…**
2. 选择音频文件（mp3/flac/wav/m4a，支持多选）
3. 选择载体类型（黑胶 22 分钟/面、磁带 30 分钟/面、CD 80 分钟/面）
4. 填写名称与 Tag（Tag 用于置物架分组陈列）
5. 选择封面来源（占位图 / 本地图片）→ 确认生成

物品自动做容量校验与 AB 面顺序分配，生成后出现在物品库与置物架。

### 播放

- 双击置物架卡片 / 物品库右键"播放" / 拖动物品卡片到唱机区域
- 唱机提供播放/暂停、上下曲、翻面按钮与进度滑条（可直接拖动寻曲）
- **拖拽唱针寻曲**：抓住唱机右侧唱针尖端拖到任意位置松手，即按面内比例跳转（跨曲自动换曲；按住 Shift 可精调）
- 面内播放结束自动切下一首（A 面末自动翻面取决于"自动翻面"设置）
- 拟真音效（随档位）：黑胶播放时有爆裂/嘶声底噪与落针刮擦声、翻面落针声；磁带换曲有机械咔哒声；简洁档静音

### 设置（拟真度）

菜单 **设置 → 设置…**：拟真度档位（简洁/精致/真实——磨损贴图、转盘动画与拟真音效强度）与自动翻面，保存后重启保持。

## 项目结构

```
MrSirMusic/
├── main.py                    # 主入口：GUI 分发，版本号 VERSION 单一来源（base.json version 字段）
├── modules/                   # 业务核心层（无 GUI 依赖，可独立复用）
│   ├── items/                 # 领域模型（黑胶/磁带/CD 物品）
│   ├── rules/                 # 规则引擎（容量预算/AB面语义）
│   ├── generator/             # 生成编排（选歌 → 物品）
│   ├── library/               # 物品库持久化（music/items.db）
│   ├── tagging/               # 标签解析（置物架分类）
│   ├── cover/                 # 封面服务（占位图兜底）
│   └── playback/              # 播放核心（引擎 + decoders 子包）
├── config/                    # 配置（静态 json 驱动 + 用户配置）
├── ui/                        # 界面层（唯一允许 import PySide6 的层）
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
