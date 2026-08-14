# 主题模块（A11.1）：全局 QSS 由 ui.json 装配（颜色/字体），apply_theme 应用

from typing import Any

from config.static.static_config import get_static_config

# 静态配置一次解包（运行时零 IO）
_SC = get_static_config()


def apply_theme(app: Any) -> None:
    # 应用全局 QSS（背景/按钮/列表/分组框/状态栏样式来自 ui.json colors/font_family）
    ui = _SC.ui
    colors = ui.get("colors", {}) if isinstance(ui, dict) else {}
    primary = str(colors.get("primary", "#8B6F47"))
    secondary = str(colors.get("secondary", "#2C2C2C"))
    font_family = str(ui.get("font_family", "Microsoft YaHei"))
    qss = f"""
    QMainWindow, QDialog {{ background-color: {secondary}; color: #EAE6DF; }}
    QLabel {{ color: #EAE6DF; }}
    QPushButton {{ background-color: {primary}; color: #FFFFFF; border: 1px solid #6B5533;
        border-radius: 4px; padding: 4px 12px; }}
    QPushButton:hover {{ background-color: #9C7F55; }}
    QPushButton:pressed {{ background-color: #6B5533; }}
    QListWidget {{ background-color: #232323; border: 1px solid #3A3A3A; }}
    QGroupBox {{ border: 1px solid #3A3A3A; border-radius: 6px; margin-top: 10px;
        color: {primary}; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; }}
    QStatusBar {{ background-color: #232323; color: #EAE6DF; }}
    QMenuBar {{ background-color: #232323; color: #EAE6DF; }}
    QMenuBar::item:selected {{ background-color: {primary}; }}
    QSlider::groove:horizontal {{ height: 4px; background: #3A3A3A; }}
    QSlider::handle:horizontal {{ width: 12px; background: {primary}; margin: -4px 0; }}
    * {{ font-family: "{font_family}"; }}
    """
    app.setStyleSheet(qss)


# ===== ui/themes.py 函数/常量说明 =====
# _SC: 静态配置单例（一次解包，运行时零 IO）
# apply_theme(app) -> None: 设置全局 QSS
#   逻辑：ui.json colors/font_family 取色 → QSS 模板格式化 → app.setStyleSheet
#   异常：无（ui.json 缺字段回退默认色，宽容）
#   设计理由：可调参数一律走配置（AGENTS.md）；QSS 集中在主题层便于换肤
#   关联配置：config/static/ui.json（colors/font_family）
