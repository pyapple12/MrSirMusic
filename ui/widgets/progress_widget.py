# 进度显示（A12.3）：进度条 + 时间（mm:ss），PROGRESS 事件驱动

from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from utils.convert import format_duration


class ProgressWidget(QWidget):
    # 进度控件：进度条 + "mm:ss / mm:ss" 时间标签；由 PROGRESS 事件驱动

    def __init__(self, parent: QWidget | None = None) -> None:
        # 初始化：进度条（0-100）+ 时间标签
        super().__init__(parent)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self._time = QLabel("0:00 / 0:00")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.bar, 1)
        layout.addWidget(self._time)

    def time_text(self) -> str:
        # 当前时间文本（验证断言用）
        return self._time.text()

    def on_progress(self, position_ms: int, duration_ms: int) -> None:
        # PROGRESS 驱动：更新进度条百分比与时间文本（duration 0 时归零）
        if duration_ms > 0:
            self.bar.setValue(int(position_ms * 100 / duration_ms))
        else:
            self.bar.setValue(0)
        self._time.setText(
            f"{format_duration(position_ms / 1000)} / {format_duration(duration_ms / 1000)}"
        )


# ===== ui/widgets/progress_widget.py 类/函数说明 =====
# ProgressWidget(QWidget): 进度显示（bar + mm:ss 时间）
#   on_progress(position_ms, duration_ms): 百分比 + 时间（format_duration 毫秒→秒）
#   time_text(): 时间文本只读（验证用）
#   设计理由：时间格式 mm:ss 复用 utils.convert（单一实现）；事件驱动与桥解耦
#   关联配置：无（事件来源为桥 progress 信号，由调用方 connect）
