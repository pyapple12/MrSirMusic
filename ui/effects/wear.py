# 磨损/风化效果器（A13.2/B2.1）：预置贴图按强度叠加（QPainter drawImage + opacity）

from pathlib import Path

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter

from config.static.static_config import get_static_config
from utils.paths import project_root

# 贴图路径（data/textures/ 随包发布；目录走 base.json data_dir）
_TEXTURES_DIR = (
    project_root() / get_static_config().base.get("data_dir", "data") / "textures"
)
WEAR_TEXTURE = _TEXTURES_DIR / "wear.png"
WEATHERING_TEXTURE = _TEXTURES_DIR / "weathering.png"


def _load_texture(path: Path) -> QImage | None:
    # 懒加载贴图（成功与失败均缓存，B3.15 防缺失时每帧重复 IO；缺失返回 None）
    if path not in _texture_cache:
        loaded: QImage | None = None
        if path.is_file():
            img = QImage(str(path))
            if not img.isNull():
                loaded = img
        _texture_cache[path] = loaded
    return _texture_cache.get(path)


_texture_cache: dict[Path, QImage | None] = {}


class Effect:
    # 效果器基类：按强度叠加绘制（0 强度不绘制）

    def __init__(self, intensity: float = 0.0) -> None:
        # 初始化强度（0-1，钳制）
        self.intensity = max(0.0, min(1.0, float(intensity)))

    def apply(self, painter: QPainter, rect: QRectF) -> None:
        # 叠加绘制（子类实现）
        raise NotImplementedError


class WearEffect(Effect):
    # 磨损效果器：噪点/划痕贴图按强度透明度叠加

    def apply(self, painter: QPainter, rect: QRectF) -> None:
        # 贴图存在且强度 > 0 才叠加（拉伸铺满目标区域）
        if self.intensity <= 0.0:
            return
        texture = _load_texture(WEAR_TEXTURE)
        if texture is None:
            return
        painter.save()
        painter.setOpacity(self.intensity)
        painter.drawImage(rect, texture)
        painter.restore()


class WeatheringEffect(Effect):
    # 风化效果器：泛黄/风化贴图按强度透明度叠加

    def apply(self, painter: QPainter, rect: QRectF) -> None:
        # 贴图存在且强度 > 0 才叠加（拉伸铺满目标区域）
        if self.intensity <= 0.0:
            return
        texture = _load_texture(WEATHERING_TEXTURE)
        if texture is None:
            return
        painter.save()
        painter.setOpacity(self.intensity)
        painter.drawImage(rect, texture)
        painter.restore()


# ===== ui/effects/wear.py 类/函数说明 =====
# WEAR_TEXTURE / WEATHERING_TEXTURE: 贴图路径（data/textures/，探针 .temp/make_textures.py 生成）
# _texture_cache: 贴图懒加载缓存（QImage，进程内一次加载）
# _load_texture(path) -> QImage | None: 懒加载（缺失返回 None，降级不崩溃）
# Effect(基类): intensity 0-1 钳制；apply 抽象
# WearEffect/WeatheringEffect: 贴图拉伸 + setOpacity(intensity) 叠加
#   设计理由：效果器实例由 registry 按档位装配；贴图缺失时静默跳过（缓存兜底策略）
#   关联配置：effects.json 的 wear_intensity/weathering_intensity（registry 装配时传入）
