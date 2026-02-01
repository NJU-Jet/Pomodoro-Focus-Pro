"""响应式历史记录视图 - 自适应布局"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCalendarWidget, QFrame, QScrollArea, QSplitter,
    QSizePolicy, QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QTextCharFormat, QBrush, QFont
from datetime import datetime
from typing import Dict, Optional
from core.statistics import DailyStatistics
from core.statistics import Statistics
from utils.logger import Logger
from gui.styles import (
    Colors, Fonts, Spacing
)


# 日历样式 - 温和回顾风格
CALENDAR_CARD_STYLE = """
    QFrame {{
        background-color: {bg_card};
        border-radius: {radius}px;
        border: 1px solid {border};
    }}
"""

CALENDAR_WIDGET_STYLE = """
    QCalendarWidget {{
        background-color: transparent;
        border: none;
    }}

    QCalendarWidget QTableView {{
        background-color: {bg_calendar};
        border: none;
        selection-background-color: {bg_selected};
        selection-color: {text_primary};
        alternate-background-color: transparent;
        gridline-color: {grid_color};
    }}

    QCalendarWidget QToolButton {{
        background-color: transparent;
        border: none;
        color: {text_primary};
        font-size: 14px;
        font-weight: 600;
        padding: 4px;
    }}

    QCalendarWidget QToolButton:hover {{
        background-color: {bg_hover};
        border-radius: 8px;
    }}
"""


class CompletedTasksPanel(QFrame):
    """已完成任务列表面板"""

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.init_ui()
        self.refresh()

    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border-radius: {Spacing.RADIUS_CARD}px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.MD)

        # 标题和刷新按钮
        header_layout = QHBoxLayout()

        title = QLabel("已完成任务")
        title.setFont(Fonts.title(16))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
                border-radius: {Spacing.RADIUS_SMALL}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_SELECTED};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # 任务列表区域
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tasks_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        self.tasks_list_widget = QLabel("加载中...")
        self.tasks_list_widget.setFont(Fonts.body())
        self.tasks_list_widget.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                background-color: transparent;
                padding: {Spacing.SM}px;
            }}
        """)
        self.tasks_list_widget.setWordWrap(True)
        self.tasks_list_widget.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tasks_scroll.setWidget(self.tasks_list_widget)

        main_layout.addWidget(self.tasks_scroll)

    def refresh(self):
        """刷新已完成任务列表"""
        completed_tasks = self.storage.get_completed_tasks()

        if not completed_tasks:
            self.tasks_list_widget.setText("暂无已完成的任务")
            self.tasks_list_widget.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Spacing.SM}px;")
            return

        # 构建HTML显示
        quadrant_names = ["重要紧急", "重要不紧急", "紧急不重要", "不紧急不重要"]
        quadrant_colors = [Colors.QUADRANT_0, Colors.QUADRANT_1, Colors.QUADRANT_2, Colors.QUADRANT_3]

        html = f"<div style='font-size: 13px;'>"

        for task in completed_tasks:
            quadrant_name = quadrant_names[task['quadrant']]
            quadrant_color = quadrant_colors[task['quadrant']]

            # 计算持续时间（从创建到完成的天数）
            created_date = datetime.fromisoformat(task['created_date'])
            completed_date = datetime.fromisoformat(task['completed_date']) if task['completed_date'] else datetime.now()
            duration_days = (completed_date - created_date).days + 1

            # 格式化日期
            completed_str = completed_date.strftime("%Y-%m-%d") if task['completed_date'] else "未完成"

            html += f"""
            <div style='padding: {Spacing.MD}px; margin-bottom: {Spacing.SM}px;
                 background-color: {Colors.BG_HOVER}; border-radius: {Spacing.RADIUS_SMALL}px;
                 border-left: 3px solid {quadrant_color};'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='color: {quadrant_color}; font-weight: 600; font-size: 12px;'>[{quadrant_name}]</span>
                    <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px;'>{completed_str}</span>
                </div>
                <div style='color: {Colors.TEXT_PRIMARY}; margin-top: {Spacing.XS}px; font-weight: 500;'>
                    {task['description']}
                </div>
                <div style='margin-top: {Spacing.SM}px; display: flex; gap: {Spacing.MD}px;'>
                    <span style='color: {Colors.PRIMARY}; font-size: 12px;'>
                        🍅 {task['actual_pomodoros']} 个番茄钟
                    </span>
                    <span style='color: {Colors.TEXT_SECONDARY}; font-size: 12px;'>
                        ⏱️ 持续 {duration_days} 天
                    </span>
                </div>
            </div>
            """

        html += "</div>"
        self.tasks_list_widget.setText(html)
        self.tasks_list_widget.setStyleSheet("")



class DateDetailPanel(QFrame):
    """日期详情面板 - 响应式设计"""

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.current_date: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border-radius: {Spacing.RADIUS_CARD}px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.MD)

        # 标题区
        title_layout = QHBoxLayout()
        title_layout.setSpacing(Spacing.SM)

        self.date_label = QLabel("选择日期")
        self.date_label.setFont(Fonts.title())
        self.date_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        title_layout.addWidget(self.date_label)

        title_layout.addStretch()

        # 统计标签
        self.stats_label = QLabel("0🍅")
        self.stats_label.setFont(Fonts.body(14))
        self.stats_label.setStyleSheet(f"color: {Colors.PRIMARY}; font-weight: 600;")
        title_layout.addWidget(self.stats_label)

        main_layout.addLayout(title_layout)

        # 内容区 - 使用Splitter确保任务、日志和心得都可以独立滚动
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Colors.BORDER};
                height: 1px;
            }}
        """)

        # 任务区域
        task_section = QVBoxLayout()
        task_section.setSpacing(Spacing.SM)

        task_title = QLabel("完成的任务")
        task_title.setFont(Fonts.body())
        task_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600;")
        task_section.addWidget(task_title)

        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)
        self.task_scroll.setMinimumHeight(100)
        self.task_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.task_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        self.task_list_widget = QLabel("选择日期查看详情")
        self.task_list_widget.setFont(Fonts.body())
        self.task_list_widget.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                background-color: transparent;
                padding: {Spacing.SM}px;
            }}
        """)
        self.task_list_widget.setWordWrap(True)
        self.task_list_widget.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_scroll.setWidget(self.task_list_widget)

        task_section.addWidget(self.task_scroll)
        task_container = QWidget()
        task_container.setLayout(task_section)
        splitter.addWidget(task_container)

        # 日志区域
        log_section = QVBoxLayout()
        log_section.setSpacing(Spacing.SM)

        log_title = QLabel("日志记录")
        log_title.setFont(Fonts.body())
        log_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600;")
        log_section.addWidget(log_title)

        self.log_scroll = QScrollArea()
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setMinimumHeight(100)
        self.log_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        self.log_list_widget = QLabel("暂无日志")
        self.log_list_widget.setFont(Fonts.body())
        self.log_list_widget.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                background-color: transparent;
                padding: {Spacing.SM}px;
            }}
        """)
        self.log_list_widget.setWordWrap(True)
        self.log_list_widget.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_scroll.setWidget(self.log_list_widget)

        log_section.addWidget(self.log_scroll)
        log_container = QWidget()
        log_container.setLayout(log_section)
        splitter.addWidget(log_container)

        # 心得感悟区域
        reflection_section = QVBoxLayout()
        reflection_section.setSpacing(Spacing.SM)

        reflection_title = QLabel("心得感悟")
        reflection_title.setFont(Fonts.body())
        reflection_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600;")
        reflection_section.addWidget(reflection_title)

        self.reflection_input = QTextEdit()
        self.reflection_input.setPlaceholderText("记录今天的心得和感悟...")
        self.reflection_input.setMinimumHeight(80)
        self.reflection_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_GLOBAL};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SMALL}px;
                padding: {Spacing.SM}px;
                font-size: 13px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """)
        reflection_section.addWidget(self.reflection_input)

        # 保存按钮
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()

        self.save_reflection_btn = QPushButton("保存心得")
        self.save_reflection_btn.setFixedHeight(32)
        self.save_reflection_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_WHITE};
                border: none;
                border-radius: {Spacing.RADIUS_SMALL}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)
        self.save_reflection_btn.clicked.connect(self.save_reflection)
        save_btn_layout.addWidget(self.save_reflection_btn)

        reflection_section.addLayout(save_btn_layout)
        reflection_container = QWidget()
        reflection_container.setLayout(reflection_section)
        splitter.addWidget(reflection_container)

        # 设置初始比例（任务:日志:心得 = 4:3:3）
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 3)

        main_layout.addWidget(splitter)

    def update_detail(self, stats: DailyStatistics, date_str: str):
        """更新详情"""
        # 保存当前日期
        self.current_date = date_str

        # 解析日期
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
        formatted_date = date_obj.strftime("%Y年%m月%d日")

        # 更新标题
        self.date_label.setText(f"{formatted_date} {weekday}")
        self.stats_label.setText(f"{stats.total_pomodoros}🍅")

        # 更新任务列表
        if stats.completed_tasks:
            task_html = f"<div style='font-size: 13px;'>"
            quadrant_names = ["重要紧急", "重要不紧急", "紧急不重要", "不紧急不重要"]
            quadrant_colors = [Colors.QUADRANT_0, Colors.QUADRANT_1, Colors.QUADRANT_2, Colors.QUADRANT_3]

            for task in stats.completed_tasks:
                quadrant_name = quadrant_names[task['quadrant']]
                quadrant_color = quadrant_colors[task['quadrant']]
                task_html += f"""
                <div style='padding: {Spacing.SM}px; margin-bottom: {Spacing.SM}px;
                     background-color: {Colors.BG_HOVER}; border-radius: {Spacing.RADIUS_SMALL}px;'>
                    <span style='color: {quadrant_color}; font-weight: 600;'>[{quadrant_name}]</span>
                    <span style='color: {Colors.TEXT_PRIMARY};'> {task['description']}</span>
                    <span style='color: {Colors.TEXT_SECONDARY}; float: right;'>{task['pomodoros']}🍅</span>
                </div>
                """
            task_html += "</div>"
            self.task_list_widget.setText(task_html)
            self.task_list_widget.setStyleSheet("")
        else:
            self.task_list_widget.setText("当日无完成任务")
            self.task_list_widget.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Spacing.SM}px;")

        # 更新日志列表
        if stats.logs:
            log_html = f"<div style='font-size: 13px;'>"
            for log in stats.logs:
                timestamp = log['timestamp'][:16]
                log_html += f"""
                <div style='padding: {Spacing.SM}px; margin-bottom: {Spacing.SM}px;
                     background-color: {Colors.BG_HOVER}; border-radius: {Spacing.RADIUS_SMALL}px;'>
                    <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px;'>{timestamp}</span>
                    <span style='color: {Colors.TEXT_PRIMARY};'> {log['content']}</span>
                </div>
                """
            log_html += "</div>"
            self.log_list_widget.setText(log_html)
            self.log_list_widget.setStyleSheet("")
        else:
            self.log_list_widget.setText("当日无日志记录")
            self.log_list_widget.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Spacing.SM}px;")

        # 加载心得感悟（使用stats.reflection）
        if stats.reflection and stats.reflection.get('content'):
            self.reflection_input.setPlainText(stats.reflection['content'])
        else:
            self.reflection_input.clear()

    def save_reflection(self):
        """保存心得感悟"""
        if not self.current_date:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请先选择一个日期")
            return

        content = self.reflection_input.toPlainText().strip()

        # 保存到数据库
        success = self.storage.save_daily_reflection(self.current_date, content)

        if success:
            # 重新加载心得数据以确保显示正确
            reflection = self.storage.get_daily_reflection(self.current_date)

            # 验证数据是否正确保存
            if reflection and reflection.get('content') == content:
                # 显示保存成功提示
                self.save_reflection_btn.setText("✓ 已保存")
                self.save_reflection_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.SUCCESS};
                        color: {Colors.TEXT_WHITE};
                        border: none;
                        border-radius: {Spacing.RADIUS_SMALL}px;
                        padding: {Spacing.SM}px {Spacing.MD}px;
                        font-size: 13px;
                        font-weight: 500;
                    }}
                """)

                # 2秒后恢复按钮文本
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, self._reset_save_button)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "警告", "保存后验证失败，请检查是否正确保存")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "保存失败，请重试")

    def _reset_save_button(self):
        """重置保存按钮"""
        self.save_reflection_btn.setText("保存心得")
        self.save_reflection_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_WHITE};
                border: none;
                border-radius: {Spacing.RADIUS_SMALL}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)


class ResponsiveHistoryView(QWidget):
    """响应式历史记录视图"""

    def __init__(self, statistics: Statistics, logger: Logger, storage, parent=None):
        super().__init__(parent)
        self.statistics = statistics
        self.logger = logger
        self.storage = storage

        self.init_ui()
        self.refresh()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(Spacing.LG)

        # 标题
        title = QLabel("历史记录")
        title.setFont(Fonts.title(16))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        main_layout.addWidget(title)

        # 使用标签页在日历和已完成任务之间切换
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}

            QTabBar::tab {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                padding: {Spacing.MD}px {Spacing.LG}px;
                margin-right: {Spacing.SM}px;
                border: none;
                font-size: 13px;
                font-weight: 500;
            }}

            QTabBar::tab:hover {{
                color: {Colors.TEXT_PRIMARY};
            }}

            QTabBar::tab:selected {{
                color: {Colors.PRIMARY};
            }}
        """)

        # === 标签页1: 日历视图 ===
        calendar_tab = QWidget()
        calendar_tab_layout = QVBoxLayout(calendar_tab)
        calendar_tab_layout.setContentsMargins(0, 0, 0, 0)
        calendar_tab_layout.setSpacing(0)

        # 日历和详情的分割器（纵向布局）
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Colors.BORDER};
                height: 1px;
            }}
        """)

        # 日历区
        calendar_container = QFrame()
        calendar_container.setStyleSheet(CALENDAR_CARD_STYLE.format(
            bg_card=Colors.CALENDAR_BG,  # 浅灰背景
            radius=Spacing.RADIUS_CARD,
            border=Colors.BORDER
        ))

        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        calendar_layout.setSpacing(Spacing.MD)

        # 日历导航
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(Spacing.MD)

        self.calendar = QCalendarWidget()
        self.calendar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.calendar.setMinimumHeight(180)
        self.calendar.setGridVisible(True)
        # 使用温和的日历样式
        self.calendar.setStyleSheet(CALENDAR_WIDGET_STYLE.format(
            bg_calendar=Colors.BG_CARD,
            bg_selected=Colors.CALENDAR_TODAY,  # 蓝色描边而非填充
            text_primary=Colors.TEXT_PRIMARY,
            grid_color=Colors.CALENDAR_GRID,  # 极浅灰网格线
            bg_hover=Colors.BG_HOVER
        ))
        self.calendar.selectionChanged.connect(self.on_date_selected)
        calendar_layout.addWidget(self.calendar)

        # 导航按钮
        today_btn = QPushButton("今天")
        today_btn.setFixedHeight(32)
        today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
                border-radius: {Spacing.RADIUS_BUTTON}px;
                font-size: 13px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: {Colors.BG_SELECTED};
            }}
        """)
        today_btn.clicked.connect(self.go_to_today)
        calendar_layout.addWidget(today_btn)

        splitter.addWidget(calendar_container)

        # 日期详情面板
        self.detail_panel = DateDetailPanel(self.storage)
        self.detail_panel.setMinimumHeight(280)
        splitter.addWidget(self.detail_panel)

        # 设置比例（日历:详情 = 3:7）
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        calendar_tab_layout.addWidget(splitter)
        self.tab_widget.addTab(calendar_tab, "日历")

        # === 标签页2: 已完成任务 ===
        self.completed_panel = CompletedTasksPanel(self.storage)
        self.tab_widget.addTab(self.completed_panel, "已完成任务")

        main_layout.addWidget(self.tab_widget)

    def refresh(self):
        """刷新视图"""
        self.mark_calendar_dates()
        self.completed_panel.refresh()

    def mark_calendar_dates(self):
        """标记有番茄钟的日期 - 温和回顾风格"""
        today = datetime.now()
        year = today.year
        month = today.month

        monthly_stats = self.statistics.get_monthly_statistics(year, month)

        # 为有番茄钟的日期设置格式（使用标记而非填充）
        for day, count in monthly_stats.days_with_data.items():
            if count > 0:
                date = QDate(year, month, int(day))

                # 根据番茄钟数量设置浅色标记（温和回顾）
                if count >= 8:
                    bg_color = Colors.CALENDAR_HAS_DATA_HIGH  # 深蓝标记
                    text_color = Colors.TEXT_WHITE
                elif count >= 5:
                    bg_color = Colors.CALENDAR_HAS_DATA  # 浅蓝标记
                    text_color = Colors.TEXT_PRIMARY
                else:
                    # 使用浅色背景 + 蓝色文字的标记方式
                    bg_color = "#DBEAFE"  # 非常浅的蓝
                    text_color = Colors.PRIMARY

                fmt = QTextCharFormat()
                fmt.setBackground(QBrush(QColor(bg_color)))
                fmt.setForeground(QBrush(QColor(text_color)))

                self.calendar.setDateTextFormat(date, fmt)

    def on_date_selected(self):
        """日期选择变化"""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("yyyy-MM-dd")

        stats = self.statistics.get_daily_statistics(date_str)
        self.detail_panel.update_detail(stats, date_str)

    def go_to_today(self):
        """跳转到今天"""
        self.calendar.setSelectedDate(QDate.currentDate())

    def update_today_summary(self, stats: DailyStatistics):
        """更新今日概况（外部调用接口）"""
        pass
