# MrSirMusic 主入口（A0.4）：argparse 分发，--version/-V 打印版本后退出，默认启动 GUI

import argparse
import json
import sys
from pathlib import Path

# 静态配置目录（__file__ 自定位，与 config/static/ 绑定）
_STATIC_DIR = Path(__file__).resolve().parent / "config" / "static"


def get_version() -> str:
    # 读取 base.json 的 version 字段（版本唯一来源）；缺失/损坏回退 "unknown"，不崩溃
    try:
        data = json.loads((_STATIC_DIR / "base.json").read_text(encoding="utf-8"))
        return str(data.get("version", "unknown"))
    except Exception:
        return "unknown"


def run_gui() -> None:
    # 启动 GUI：PySide6 与 ui.main_window 延迟导入（--version 路径零 GUI 开销；ui 未完成时友好提示退出）
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
    except ImportError as exc:
        print(f"GUI 依赖未就绪：{exc}（ui 层尚未开发完成）", file=sys.stderr)
        raise SystemExit(1)
    app = QApplication([])
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())


def main() -> None:
    # 入口分发：--version/-V 由 argparse 打印版本并退出，默认走 GUI 路径
    parser = argparse.ArgumentParser(description="MrSirMusic 拟物音乐播放器")
    parser.add_argument("--version", "-V", action="version", version=get_version())
    parser.parse_args()
    run_gui()


if __name__ == "__main__":
    main()


# ===== main.py 函数/常量说明 =====
# _STATIC_DIR: 静态配置目录（唯一路径来源），__file__ 自定位，读取 base.json 用
# get_version() -> str: 读取 base.json version 字段（版本唯一来源）
#   逻辑：json 读取 → 取 version 字段 → 转 str；键缺失返回 "unknown"
#   异常：任何读取/解析错误捕获后返回 "unknown"（--version 容错，不崩溃）
#   关联配置：config/static/base.json 的 version 字段（四段式 X.Y.Z.P）
# run_gui() -> None: GUI 启动
#   逻辑：延迟 import PySide6 与 ui.main_window → QApplication + MainWindow → 事件循环
#   异常：ImportError（ui 层未完成或依赖缺失）→ stderr 提示 + SystemExit(1)，不崩溃
#   设计理由：PySide6 重依赖延迟导入，--version 路径不加载 GUI；ui 未完成阶段可独立验证 CLI
# main() -> None: 入口分发
#   逻辑：argparse 解析（--version/-V 用 action="version" 自动打印并 SystemExit(0)）→ run_gui()
#   关联配置：config/static/base.json（版本号经 get_version 间接引用）
