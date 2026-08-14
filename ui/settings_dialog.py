# 设置面板（A13.4）：拟真度档位 + 自动翻面读写 user_config.json，保存后发变更通知

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from config.settings import AppConfig, load_config, save_config
from ui.effects.registry import available_levels


class SettingsDialog(QDialog):
    # 设置对话框：拟真度档位下拉 + 自动翻面勾选；保存（save_config + 变更通知，重启保持）

    def __init__(self, parent=None) -> None:
        # 初始化：档位下拉（三档，回显已存配置）+ 自动翻面勾选
        super().__init__(parent)
        self.setWindowTitle("设置")
        cfg = load_config()
        self.level_combo = QComboBox()
        self.level_combo.addItems(available_levels())
        if cfg.realism_level in available_levels():
            self.level_combo.setCurrentText(cfg.realism_level)
        self.auto_flip_check = QCheckBox("自动翻面（A 面播完后自动切 B 面）")
        self.auto_flip_check.setChecked(cfg.auto_flip)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("拟真度档位："))
        layout.addWidget(self.level_combo)
        layout.addWidget(self.auto_flip_check)
        layout.addWidget(buttons)

    def _on_save(self) -> None:
        # 保存：写入 user_config.json（持久化）→ 触发变更通知（监听器运行时应用）→ accept
        save_config(
            AppConfig(
                realism_level=self.level_combo.currentText(),
                auto_flip=self.auto_flip_check.isChecked(),
            )
        )
        self.accept()


# ===== ui/settings_dialog.py 类/函数说明 =====
# SettingsDialog(QDialog): 设置面板
#   __init__: 档位下拉（available_levels）+ 自动翻面勾选，回显 load_config()
#   _on_save: save_config（持久化 + 变更通知）→ accept
#   设计理由：读写统一走 config.settings（A1.7），重启保持由 user_config.json 保证
#   关联配置：config/user_config.json、effects.json（档位列表）
