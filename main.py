# MrSirMusic 主入口（A0.4/B1.1）：argparse 分发，--version/-V 打印版本后退出，默认启动 GUI

import argparse
import sys

from config.static.static_config import get_static_config


def get_version() -> str:
    # 读取 base.json 的 version 字段（版本唯一来源，经 static_config 单例单通道）；非字符串/缺失回退 "unknown"
    value = get_static_config().base.get("version", "unknown")
    return value if isinstance(value, str) else "unknown"


def run_gui() -> None:
    # 启动 GUI：PySide6 与 ui.main_window 延迟导入（--version 路径零 GUI 开销；依赖缺失时友好提示退出）
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        from ui.themes import apply_theme
    except ImportError as exc:
        print(f"GUI 依赖缺失：{exc}（请检查 PySide6 安装）", file=sys.stderr)
        raise SystemExit(1)
    app = QApplication([])
    apply_theme(app)
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
# get_version() -> str: 读取 base.json version 字段（版本唯一来源）
#   逻辑：经 static_config 单例单通道读取 → isinstance(str) 校验；键缺失/非字符串返回 "unknown"
#   异常：配置缺失/损坏由 static_config 容错为空 dict，此处回退 "unknown"（--version 容错，不崩溃）
#   关联配置：config/static/base.json 的 version 字段（四段式 X.Y.Z.P）
# run_gui() -> None: GUI 启动
#   逻辑：延迟 import PySide6 与 ui.main_window → apply_theme → QApplication + MainWindow → 事件循环
#   异常：ImportError（PySide6 缺失等）→ stderr 提示 + SystemExit(1)，不崩溃
#   设计理由：PySide6 重依赖延迟导入，--version 路径不加载 GUI；主题在窗口创建前应用（B0.5）
# main() -> None: 入口分发
#   逻辑：argparse 解析（--version/-V 用 action="version" 自动打印并 SystemExit(0)）→ run_gui()
#   关联配置：config/static/base.json（版本号经 get_version 间接引用）
