# 主题模块（A11.1）：全局 QSS 由 ui.json 装配（颜色/字体），apply_theme 应用

from typing import Any

from config.static.static_config import get_static_config

# 静态配置一次解包（运行时零 IO）
_SC = get_static_config()


def apply_theme(app: Any) -> None:
    # 应用全局 QSS（背景/按钮/列表/分组框/状态栏样式全部来自 ui.json colors/font_family，B2.7 全外置）；
    # PL001.2 补齐容器覆盖（Tab 页/滚动区/分组框/输入件）消除默认白块割裂
    ui = _SC.ui
    colors = ui.get("colors", {}) if isinstance(ui, dict) else {}
    c = {
        "primary": str(colors.get("primary", "#8B6F47")),
        "secondary": str(colors.get("secondary", "#2C2C2C")),
        "hover": str(colors.get("hover", "#9C7F55")),
        "pressed": str(colors.get("pressed", "#6B5533")),
        "border": str(colors.get("border", "#3A3A3A")),
        "background": str(colors.get("background", "#232323")),
        "text": str(colors.get("text", "#EAE6DF")),
        "text_on_primary": str(colors.get("text_on_primary", "#FFFFFF")),
        "surface": str(colors.get("surface", "#35302A")),
        "panel": str(colors.get("panel", "#3A342C")),
    }
    font_family = str(ui.get("font_family", "Microsoft YaHei"))
    qss = f"""
    QMainWindow, QDialog {{ background-color: {c["secondary"]}; color: {c["text"]}; }}
    QLabel {{ color: {c["text"]}; background: transparent; }}
    QPushButton {{ background-color: {c["primary"]}; color: {c["text_on_primary"]}; border: 1px solid {c["pressed"]};
        border-radius: 4px; padding: 4px 12px; }}
    QPushButton:hover {{ background-color: {c["hover"]}; }}
    QPushButton:pressed {{ background-color: {c["pressed"]}; }}
    QAbstractItemView {{ background-color: {c["background"]}; alternate-background-color: {c["surface"]};
        selection-background-color: {c["primary"]}; selection-color: {c["text_on_primary"]}; }}
    QListWidget {{ border: 1px solid {c["border"]}; }}
    QTabWidget::pane {{ background-color: {c["background"]}; border: 1px solid {c["border"]}; }}
    QTabBar::tab {{ background-color: {c["surface"]}; color: {c["text"]}; padding: 5px 16px;
        border: 1px solid {c["border"]}; border-bottom: none; }}
    QTabBar::tab:selected {{ background-color: {c["background"]}; color: {c["primary"]}; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QGroupBox {{ background-color: {c["surface"]}; border: 1px solid {c["border"]}; border-radius: 6px;
        margin-top: 10px; padding: 10px 8px 8px 8px; color: {c["text"]}; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; color: {c["primary"]}; }}
    QLineEdit, QComboBox {{ background-color: {c["panel"]}; color: {c["text"]}; border: 1px solid {c["border"]};
        border-radius: 4px; padding: 3px 6px; }}
    QLineEdit:focus, QComboBox:focus {{ border: 1px solid {c["primary"]}; }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox QAbstractItemView {{ background-color: {c["panel"]}; color: {c["text"]};
        selection-background-color: {c["primary"]}; }}
    QMenu {{ background-color: {c["panel"]}; color: {c["text"]}; border: 1px solid {c["border"]}; }}
    QMenu::item:selected {{ background-color: {c["primary"]}; }}
    QStatusBar {{ background-color: {c["background"]}; color: {c["text"]}; }}
    QMenuBar {{ background-color: {c["background"]}; color: {c["text"]}; }}
    QMenuBar::item:selected {{ background-color: {c["primary"]}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {c["border"]}; }}
    QSlider::handle:horizontal {{ width: 12px; background: {c["primary"]}; margin: -4px 0; }}
    QScrollBar:vertical {{ background: {c["background"]}; width: 10px; }}
    QScrollBar:horizontal {{ background: {c["background"]}; height: 10px; }}
    QScrollBar::handle {{ background: {c["primary"]}; border-radius: 3px; }}
    QScrollBar::handle:hover {{ background: {c["hover"]}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    * {{ font-family: "{font_family}"; }}
    """
    app.setStyleSheet(qss)


# ===== ui/themes.py 函数/常量说明 =====
# _SC: 静态配置单例（一次解包，运行时零 IO）
# apply_theme(app) -> None: 设置全局 QSS
#   逻辑：ui.json colors/font_family 取色 → QSS 模板格式化 → app.setStyleSheet
#   异常：无（ui.json 缺字段回退默认色，宽容）
#   覆盖面（PL001.2 补全）：窗体/按钮/列表(QAbstractItemView)/Tab 页与页签/滚动区/分组框(surface 底)/
#     输入件(QLineEdit/QComboBox panel 底 + 聚焦描边)/菜单/状态栏/滑杆——消除默认白块与深色窗的割裂
#   设计理由：可调参数一律走配置（AGENTS.md）；QSS 集中在主题层便于换肤
#   关联配置：config/static/ui.json（colors 含 surface/panel 分层色、font_family）
