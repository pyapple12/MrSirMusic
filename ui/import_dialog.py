# 导入对话框（A11.6）："生成物品"流程 UI——文件多选/类型/名称/Tag/封面来源 → generator

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from config.static.static_config import get_static_config
from modules.generator.generator import GenerateError, generate
from modules.items.model import Item, ItemType
from utils.file_utils import AUDIO_EXTENSIONS, is_audio_file

# 静态配置一次解包
_SC = get_static_config()


class ImportDialog(QDialog):
    # 生成物品对话框：多选文件 → 类型下拉 → 名称/Tag → 封面来源（占位图/local）→ generate

    def __init__(self, parent: Any | None = None) -> None:
        # 初始化：字段布局 + 类型下拉（item_types.json 装配）+ 文件选择
        super().__init__(parent)
        self.setWindowTitle("生成物品")
        self._selected_files: list[str] = []
        self._result_item: Item | None = None

        self.files_label = QLabel("未选择文件")
        self.pick_button = QPushButton("选择音频文件…")
        self.pick_button.clicked.connect(self._pick_files)

        self.type_combo = QComboBox()
        for key, rec in _SC.item_types.items():
            if isinstance(rec, dict):
                self.type_combo.addItem(str(rec.get("name", key)), key)

        self.name_edit = QLineEdit()
        self.tag_edit = QLineEdit()

        self.placeholder_radio = QRadioButton("占位图")
        self.placeholder_radio.setChecked(True)
        self.local_radio = QRadioButton("本地图片…")
        self.cover_path_edit = QLineEdit()
        self.cover_path_edit.setEnabled(False)
        self.cover_pick_button = QPushButton("浏览…")
        self.cover_pick_button.setEnabled(False)
        self.cover_pick_button.clicked.connect(self._pick_cover)
        self.local_radio.toggled.connect(self.cover_path_edit.setEnabled)
        self.local_radio.toggled.connect(self.cover_pick_button.setEnabled)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("音频文件："))
        layout.addWidget(self.files_label)
        layout.addWidget(self.pick_button)
        layout.addWidget(QLabel("载体类型："))
        layout.addWidget(self.type_combo)
        layout.addWidget(QLabel("名称："))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Tag："))
        layout.addWidget(self.tag_edit)
        layout.addWidget(QLabel("封面来源："))
        cover_row = QHBoxLayout()
        cover_row.addWidget(self.placeholder_radio)
        cover_row.addWidget(self.local_radio)
        cover_row.addWidget(self.cover_path_edit)
        cover_row.addWidget(self.cover_pick_button)
        layout.addLayout(cover_row)
        layout.addWidget(buttons)

    def _pick_files(self) -> None:
        # 文件多选：QFileDialog 过滤音频扩展名；选择后更新标签
        exts = " ".join(f"*{e}" for e in sorted(AUDIO_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "", f"音频文件 ({exts})"
        )
        if files:
            self._selected_files = list(files)
            self.files_label.setText(f"已选 {len(files)} 个文件")

    def _pick_cover(self) -> None:
        # 本地封面选择（QFileDialog 单文件，图片过滤串走 ui.json，B2.8）
        image_filter = str(_SC.ui.get("cover_image_filter", "*.png *.jpg *.jpeg *.bmp"))
        path, _ = QFileDialog.getOpenFileName(
            self, "选择封面图片", "", f"图片文件 ({image_filter})"
        )
        if path:
            self.cover_path_edit.setText(path)

    def _item_type(self) -> ItemType | None:
        # 当前下拉的 ItemType（按注册表键装配）
        key = self.type_combo.currentData()
        rec = _SC.item_types.get(key)
        if isinstance(rec, dict):
            return ItemType.from_config(str(key), rec)
        return None

    def _on_ok(self) -> None:
        # 确认：收集参数 → generator.generate（失败 QMessageBox 提示）；成功 accept + 保存结果
        files = [f for f in self._selected_files if is_audio_file(f)]
        item_type = self._item_type()
        name = self.name_edit.text().strip()
        tag = self.tag_edit.text().strip()
        if not files:
            QMessageBox.warning(self, "生成物品", "请选择音频文件")
            return
        if not name:
            QMessageBox.warning(self, "生成物品", "请填写名称")
            return
        if item_type is None:
            QMessageBox.warning(self, "生成物品", "载体类型无效")
            return
        cover_source = "local" if self.local_radio.isChecked() else "placeholder"
        cover_file = (
            self.cover_path_edit.text().strip() if cover_source == "local" else None
        )
        if cover_source == "local" and (
            not cover_file or not Path(cover_file).is_file()
        ):
            QMessageBox.warning(self, "生成物品", "请选择有效的封面图片")
            return
        try:
            self._result_item = generate(
                files,
                item_type,
                name,
                tag,
                cover_source=cover_source,
                cover_file=cover_file,
            )
        except GenerateError as exc:
            QMessageBox.warning(self, "生成物品", str(exc))
            return
        except Exception as exc:
            # C2.2：底层异常（磁盘/库损坏等）兜底提示，不炸出 Qt 槽
            QMessageBox.warning(self, "生成物品", f"生成失败：{exc}")
            return
        self.accept()

    def result_item(self) -> Item | None:
        # 生成结果（accept 后由调用方取）；预留：当前刷新走重新读库，本接口供探针/后续直接取用
        return self._result_item


# ===== ui/import_dialog.py 类/函数说明 =====
# _SC: 静态配置单例（item_types 装配类型下拉）
# ImportDialog(QDialog): 生成物品对话框
#   _pick_files/_pick_cover: 文件多选/封面单选（QFileDialog，音频/图片过滤）
#   _item_type: 下拉 → ItemType（item_types.json 装配）
#   _on_ok: 参数收集 + 前置校验（文件/名称/类型/封面）→ generate → 成功 accept/失败 QMessageBox
#   result_item: 生成结果（供调用方取走后刷新视图）
#   设计理由：UI 只做参数收集与错误提示，业务全部走 generator（错误分类 GenerateError）
#   关联配置：item_types.json（类型下拉）、AUDIO_EXTENSIONS（文件过滤）、generator
