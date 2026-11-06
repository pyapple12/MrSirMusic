# 进度控件（H5 拟物升级）：可拖动滑条 + 时间（mm:ss），PROGRESS 事件驱动，支持 scrub 寻曲
# 拖动中挂起外部回写（防 1s PROGRESS 覆盖拖动位），松手发 scrub_released 交路由方 seek

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget

from utils.convert import format_duration, progress_percent

# 滑条精度：0-1000（千分位，拖动寻曲足够平滑）
_SLIDER_MAX = 1000


class ProgressWidget(QWidget):
    # 进度控件：可拖动进度滑条 + "mm:ss / mm:ss" 时间标签；PROGRESS 事件驱动 + scrub 交互

    scrub_started = Signal()  # 按下滑条（路由方挂起进度回写 + 磁带 wind 视觉启动）
    scrub_moved = Signal(int)  # 拖动中（滑条原始值 0-1000；预览 + wind 方向判定）
    scrub_released = Signal(int)  # 松手（滑条原始值 0-1000；路由方换算秒数后 seek）

    def __init__(self, parent: QWidget | None = None) -> None:
        # 初始化：滑条（0-1000）+ 时间标签；scrub 期间外部 on_progress 回写被挂起
        super().__init__(parent)
        self._scrubbing = False
        self._duration_seconds = 0.0  # 最近一次上报的总时长（拖动预览换算用）
        self.bar = QSlider(Qt.Orientation.Horizontal)
        self.bar.setRange(0, _SLIDER_MAX)
        # scrub 三态：按下挂起回写 / 拖动预览 + wind / 松手 seek（信号在滑条实例上）
        self.bar.sliderPressed.connect(self._on_pressed)
        self.bar.sliderMoved.connect(self._on_moved)
        self.bar.sliderReleased.connect(self._on_released)
        self._time = QLabel("0:00 / 0:00")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.bar, 1)
        layout.addWidget(self._time)

    def time_text(self) -> str:
        # 当前时间文本（验证断言用）
        return self._time.text()

    def is_scrubbing(self) -> bool:
        # 是否拖动中（路由方挂起 PROGRESS 回写判断用）
        return self._scrubbing

    def _on_pressed(self) -> None:
        # 按下滑条：进入 scrub 态（回写挂起）
        self._scrubbing = True
        self.scrub_started.emit()

    def _on_moved(self, value: int) -> None:
        # 拖动中：时间文本按滑条比例实时预览（总时长未知时不预览）
        if self._duration_seconds > 0:
            position = self._duration_seconds * value / _SLIDER_MAX
            total_text = format_duration(self._duration_seconds)
            self._time.setText(f"{format_duration(position)} / {total_text}")
        self.scrub_moved.emit(value)

    def _on_released(self) -> None:
        # 松手：退出 scrub 态并发最终值（路由方 seek；随后 PROGRESS 事件恢复回写）
        self._scrubbing = False
        self.scrub_released.emit(self.bar.value())

    def on_progress(self, position_ms: int, duration_ms: int) -> None:
        # PROGRESS 驱动：更新滑条值与时间文本；scrub 中两者均挂起——滑条位与时间文本
        # 由拖动预览独占（FIX006.6：否则文本每秒在预览值/真实值间跳变）；
        # 总时长仍记录（预览换算源）；百分比 0-100 缩放到滑条 0-1000 值域
        if duration_ms > 0:
            self._duration_seconds = duration_ms / 1000.0
        if not self._scrubbing:
            self.bar.setValue(
                progress_percent(position_ms, duration_ms) * (_SLIDER_MAX // 100)
            )
            self._time.setText(
                f"{format_duration(position_ms / 1000)} / {format_duration(duration_ms / 1000)}"
            )


# ===== ui/widgets/progress_widget.py 类/函数说明 =====
# ProgressWidget(QWidget): 进度显示（可拖动滑条 + mm:ss 时间，H5 由 QProgressBar 升级 QSlider）
#   scrub_started/scrub_moved(int)/scrub_released(int): scrub 交互信号（值域 0-1000）
#   is_scrubbing(): 拖动中状态（路由方挂起回写判断）
#   on_progress(position_ms, duration_ms): 滑条值 + 时间（format_duration 毫秒→秒；scrub 中滑条与时间均挂起）；
#     同时记录总时长供拖动预览换算
#   time_text(): 时间文本只读（验证用）
#   设计理由：时间格式复用 utils.convert（单一实现）；seek 换算经信号外抛（控件零业务依赖）；
#     scrub 挂起回写防 1s PROGRESS 覆盖拖动位（B 系列节流语义的交互互补）
#   关联配置：无（事件来源为桥 progress 信号，由调用方 connect）
