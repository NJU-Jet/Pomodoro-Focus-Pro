"""产品级任务创建对话框"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QButtonGroup,
    QRadioButton, QSpinBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.styles import (
    Colors, Fonts, Spacing,
    apply_primary_button_style, apply_secondary_button_style,
    apply_input_style
)


class CreateTaskDialog(QDialog):
    """产品级任务创建对话框"""

    def __init__(self, quadrant: int = 0, parent=None):
        super().__init__(parent)
        self.selected_quadrant = quadrant
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("创建新任务")
        self.setMinimumSize(480, 520)
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

        title = QLabel("创建新任务")
        title.setFont(Fonts.title(18))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        title_section.addWidget(title)

        subtitle = QLabel("明确任务目标，开始专注执行")
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
        self.task_name_input.setPlaceholderText("例如：完成项目报告")
        self.task_name_input.setMinimumHeight(44)
        apply_input_style(self.task_name_input)
        input_section.addWidget(self.task_name_input)

        # 象限选择
        quadrant_label = QLabel("优先级")
        quadrant_label.setFont(Fonts.body())
        quadrant_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: 600;")
        input_section.addWidget(quadrant_label)

        # 象限按钮组
        quadrant_buttons_layout = QHBoxLayout()
        quadrant_buttons_layout.setSpacing(Spacing.MD)

        self.quadrant_group = QButtonGroup()

        quadrants = [
            (0, "重要紧急", Colors.QUADRANT_0),
            (1, "重要不紧急", Colors.QUADRANT_1),
            (2, "紧急不重要", Colors.QUADRANT_2),
            (3, "不紧急不重要", Colors.QUADRANT_3),
        ]

        for idx, (q_id, q_name, q_color) in enumerate(quadrants):
            radio = QRadioButton(q_name)
            radio.setFont(Fonts.body())
            radio.setStyleSheet(f"""
                QRadioButton {{
                    color: {Colors.TEXT_PRIMARY};
                    spacing: {Spacing.SM}px;
                }}

                QRadioButton::indicator {{
                    width: 18px;
                    height: 18px;
                }}

                QRadioButton::indicator:checked {{
                    background-color: {q_color};
                    border: 2px solid {q_color};
                    border-radius: 9px;
                }}
            """)
            if q_id == self.selected_quadrant:
                radio.setChecked(True)

            self.quadrant_group.addButton(radio, q_id)
            quadrant_buttons_layout.addWidget(radio)

        input_section.addLayout(quadrant_buttons_layout)

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

        create_btn = QPushButton("创建任务")
        create_btn.setFixedHeight(44)
        create_btn.setMinimumWidth(140)
        apply_primary_button_style(create_btn)
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)

        content_layout.addLayout(button_layout)

        main_layout.addWidget(content_card)

        # 设置默认焦点
        self.task_name_input.setFocus()

    def get_task_data(self):
        """获取任务数据"""
        return {
            'description': self.task_name_input.text().strip(),
            'quadrant': self.quadrant_group.checkedId(),
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
