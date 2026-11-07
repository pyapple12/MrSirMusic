# 拟物共享绘制件（PL002.1）：磁带卷轴/带卷物理因子/拟物贴图加载等跨控件共用
# record_widget（置物架卡片磁带观察窗）与 deck_widget（磁带仓形态）共用，避免绘制逻辑双份漂移

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

from config.static.static_config import get_static_config
from utils.logger import get_logger

# 模块日志（PL005.4：贴图加载失败告警一次——容错登记制可观测）
_logger = get_logger("ui.parts")

# 带卷半径物理因子（恒线速模型的几何侧）：44² → 77² 线性内插（空卷 → 满卷）
REEL_RADIUS_MIN = 44.0
REEL_RADIUS_MAX = 77.0
# 播放基准角速度（度/秒）：恒线速模型的速度侧，实际角速度 = 本值 / reel_factor(fill)
# （FIX006.9 收敛单源——record_widget 卡片与 deck_widget 磁带仓共用，防调参单向漂移）
REEL_BASE_SPEED = 240.0

# 拟物贴图目录（PL005.3 产物：Blender 烘焙四贴图；仓库内固定相对路径）
TEXTURES_DIR = Path(__file__).resolve().parents[2] / "data" / "textures"

# 贴图惰性缓存（键 → QPixmap 或 None；None = 已知缺失/损坏，回退矢量绘制不再重试读盘）
_TEXTURE_CACHE: dict = {}
_TEXTURE_WARNED: set = set()


def reel_factor(fill: float) -> float:
    # 带卷半径因子：sqrt(44² + (77²-44²)×fill)——卷多因子大（角速度反比于它，恒线速）
    fill = min(1.0, max(0.0, fill))
    return math.sqrt(REEL_RADIUS_MIN**2 + (REEL_RADIUS_MAX**2 - REEL_RADIUS_MIN**2) * fill)


def texture_pixmap(key: str) -> QPixmap | None:
    # 拟物贴图惰性加载（PL005.4）：data/textures/<key>.png → QPixmap；缺失/损坏 → None
    # （回退矢量绘制；每键仅告警一次，容错登记制条目；结果进缓存不重试读盘）
    if key in _TEXTURE_CACHE:
        return _TEXTURE_CACHE[key]
    path = TEXTURES_DIR / f"{key}.png"
    pixmap: QPixmap | None = None
    if path.is_file():
        loaded = QPixmap(str(path))
        if not loaded.isNull():
            pixmap = loaded
    if pixmap is None and key not in _TEXTURE_WARNED:
        _logger.warning("贴图加载失败（回退矢量绘制）: %s", path.name)
        _TEXTURE_WARNED.add(key)
    _TEXTURE_CACHE[key] = pixmap
    return pixmap


def texture_enabled(level: str) -> bool:
    # 拟真度档位 → 贴图打底开关（effects.json levels[level].texture；缺档/缺键宽容 False）
    levels = get_static_config().effects.get("levels", {})
    record = levels.get(level) if isinstance(levels, dict) else None
    if isinstance(record, dict):
        return bool(record.get("texture", False))
    return False


def draw_reel(
    painter: QPainter,
    center: QPointF,
    radius: float,
    hub_radius: float,
    angle: float,
) -> None:
    # 绘制单个磁带卷轴：带卷体（深棕）+ 缠绕纹理内圈 + 花键 hub（浅色圆 + 3 齿随角度旋转）
    # 半径/hub 由调用方按窗口尺寸与 fill 计算（本函数只管画，零状态）
    # 带卷体
    painter.setPen(QPen(QColor("#5a4a3a"), 1))
    painter.setBrush(QColor("#2e2620"))
    painter.drawEllipse(center, radius, radius)
    # 缠绕纹理（内圈细线，透明度低做层叠感）
    painter.setPen(QPen(QColor(90, 74, 58, 110), 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(center, radius * 0.72, radius * 0.72)
    painter.drawEllipse(center, radius * 0.50, radius * 0.50)
    # hub（浅色花键盘）
    painter.setPen(QPen(QColor("#777777"), 1))
    painter.setBrush(QColor("#d8d8d8"))
    painter.drawEllipse(center, hub_radius, hub_radius)
    # 3 齿（120° 分布，随卷轴角度旋转）
    painter.save()
    painter.translate(center)
    painter.rotate(angle)
    painter.setBrush(QColor("#8a8a8a"))
    painter.setPen(QPen(QColor("#666666"), 1))
    tooth_length = hub_radius * 0.85
    for _ in range(3):
        painter.rotate(120.0)
        painter.drawRect(QRectF(-1.5, -hub_radius, 3.0, tooth_length))
    painter.restore()


# ===== ui/widgets/parts.py 函数/常量说明 =====
# REEL_RADIUS_MIN/REEL_RADIUS_MAX: 带卷半径因子上下界（44/77，与角速度公式同源量纲）
# reel_factor(fill) -> float: 带卷半径因子（恒线速模型的半径侧；调用方角速度 = 基准/因子）
# TEXTURES_DIR: 拟物贴图目录（data/textures；PL005.3 Blender 烘焙产物）
# texture_pixmap(key) -> QPixmap|None: 贴图惰性缓存加载（缺失/损坏 → None 回退矢量 + 每键告警一次）
# texture_enabled(level) -> bool: 档位贴图开关（effects.json levels[level].texture，宽容缺键）
# draw_reel(painter, center, radius, hub_radius, angle): 单卷轴绘制（带卷 + 缠绕纹 + hub 3 齿）
#   逻辑：带卷体 → 两圈内缠绕纹 → hub 圆 → save/translate/rotate 后画 3 齿（120° 分布）→ restore
#   设计理由：卷轴绘制原在 record_widget 私有（PL002.1 迁出共享），deck_widget 磁带仓形态复用；
#     本模块只管画（零状态、零动画），进度/角度推进留在各控件 _tick；
#     贴图加载收口本模块单源（deck_widget/record_widget/shelf_view 共用，防三份加载器漂移）
#   异常：无（纯绘制；半径/hub 非法值由调用方保证 >0；贴图读盘失败已捕获降级）
#   关联配置：effects.json levels[].texture（档位开关）；消费方 record_widget / deck_widget / shelf_view
