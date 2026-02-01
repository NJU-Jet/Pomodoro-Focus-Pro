"""编辑任务对话框"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QFrame
)
from PyQt6.QtCore import Qt
from gui.styles import (
    Colors, Fonts, Spacing,
    apply_primary_button_style, apply_secondary_button_style,
    apply_input_style
)


class EditTaskDialog(QDialog):
    """编辑任务对话框"""

    def __init__(self, task, parent=None):
        """
        初始化编辑任务对话框

        Args:
            task: Task对象，包含 description, estimated_pomodoros 等属性
            parent: 父窗口
        """
        super().__init__(parent)
        self.task = task
        self.init_ui()
        self.load_task_data()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑任务")
        self.setMinimumSize(400, 300)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_GLOBAL};
            }}
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 内容卡片
        content_card = QFrame()
        content_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border-radius: {Spacing.RADIUS_CARD}px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(Spacing.XXL, Spacing.XXL, Spacing.XXL, Spacing.XXL)
        content_layout.setSpacing(Spacing.XL)

        # 标题区
        title_section = QVBoxLayout()
        title_section.setSpacing(Spacing.SM)

        title = QLabel("编辑任务")
        title.setFont(Fonts.title(18))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        title_section.addWidget(title)

        subtitle = QLabel("修改任务信息和预估时间")
        subtitle.setFont(Fonts.caption())
        subtitle.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        title_section.addWidget(subtitle)

        content_layout.addLayout(title_section)

        # 分割线
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {Colors.BORDER};")
        content_layout.addWidget(line)

        # 输入区
        input_section = QVBoxLayout()
        input_section.setSpacing(Spacing.LG)

        # 任务名称
        name_label = QLabel("任务名称")
        name_label.setFont(Fonts.body())
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: 600;")
        input_section.addWidget(name_label)

        self.task_name_input = QLineEdit()
        self.task_name_input.setPlaceholderText("输入任务名称")
        self.task_name_input.setMinimumHeight(44)
        apply_input_style(self.task_name_input)
        input_section.addWidget(self.task_name_input)

        # 预计番茄钟
        pomodoro_label = QLabel("预计番茄钟")
        pomodoro_label.setFont(Fonts.body())
        pomodoro_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: 600;")
        input_section.addWidget(pomodoro_label)

        pomodoro_input_layout = QHBoxLayout()
        pomodoro_input_layout.setSpacing(Spacing.SM)

        self.pomodoro_input = QSpinBox()
        self.pomodoro_input.setRange(0, 99)
        self.pomodoro_input.setValue(1)
        self.pomodoro_input.setMinimumHeight(44)
        self.pomodoro_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_BUTTON}px;
                padding: {Spacing.MD}px;
                font-size: 14px;
                color: {Colors.TEXT_PRIMARY};
            }}

            QSpinBox:focus {{
                border-color: {Colors.PRIMARY};
            }}

            QSpinBox::up-button, QSpinBox::down-button {{
                width: 32px;
                border: none;
                background-color: {Colors.BG_HOVER};
            }}

            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {Colors.BG_SELECTED};
            }}
        """)
        pomodoro_input_layout.addWidget(self.pomodoro_input)

        pomodoro_unit = QLabel("个")
        pomodoro_unit.setFont(Fonts.body())
        pomodoro_unit.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        pomodoro_input_layout.addWidget(pomodoro_unit)

        pomodoro_input_layout.addStretch()

        input_section.addLayout(pomodoro_input_layout)
        content_layout.addLayout(input_section)

        # 按钮区
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.MD)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(44)
        cancel_btn.setMinimumWidth(120)
        apply_secondary_button_style(cancel_btn)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.setFixedHeight(44)
        save_btn.setMinimumWidth(140)
        apply_primary_button_style(save_btn)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        content_layout.addLayout(button_layout)

        main_layout.addWidget(content_card)

        # 设置默认焦点
        self.task_name_input.setFocus()

    def load_task_data(self):
        """加载任务数据"""
        self.task_name_input.setText(self.task.description)
        self.pomodoro_input.setValue(self.task.estimated_pomodoros)

    def get_task_data(self):
        """获取编辑后的任务数据"""
        return {
            'description': self.task_name_input.text().strip(),
            'estimated_pomodoros': self.pomodoro_input.value()
        }

    def validate(self):
        """验证输入"""
        description = self.task_name_input.text().strip()

        if not description:
            self.task_name_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {Colors.BG_CARD};
                    border: 1px solid {Colors.DANGER};
                    border-radius: {Spacing.RADIUS_BUTTON}px;
                    padding: {Spacing.MD}px;
                    font-size: 14px;
                }}
            """)
            return False, "任务名称不能为空"

        return True, ""
