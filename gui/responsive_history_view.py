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
        # 创建一个容器 widget 来包裹 scroll area
        tasks_scroll_container = QWidget()
        tasks_scroll_layout = QVBoxLayout(tasks_scroll_container)
        tasks_scroll_layout.setContentsMargins(0, 0, 0, 0)
        tasks_scroll_layout.setSpacing(0)

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
        self.tasks_list_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.tasks_scroll.setWidget(self.tasks_list_widget)

        tasks_scroll_layout.addWidget(self.tasks_scroll)

        # 在 scroll area 外层添加底部间距
        tasks_scroll_layout.addSpacing(Spacing.LG)  # 24px 底部留白

        main_layout.addWidget(tasks_scroll_container)

    def refresh(self):
        """刷新已完成任务列表 - 按日期分组显示"""
        completed_tasks = self.storage.get_completed_tasks()

        if not completed_tasks:
            self.tasks_list_widget.setText("暂无已完成的任务")
            self.tasks_list_widget.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: {Spacing.MD}px;")
            return

        # 按完成日期分组
        from collections import defaultdict
        tasks_by_date = defaultdict(list)
        for task in completed_tasks:
            completed_date = task.get('completed_date')
            if completed_date:
                # 只取日期部分（YYYY-MM-DD）
                date_only = completed_date.split('T')[0] if 'T' in completed_date else completed_date
                tasks_by_date[date_only].append(task)

        # 按日期排序（最新的在前）
        sorted_dates = sorted(tasks_by_date.keys(), reverse=True)

        quadrant_names = ["重要紧急", "重要不紧急", "紧急不重要", "不紧急不重要"]
        quadrant_colors = [Colors.QUADRANT_0, Colors.QUADRANT_1, Colors.QUADRANT_2, Colors.QUADRANT_3]

        # 构建HTML：日期分组 + 任务卡片
        html = "<div style='display: flex; flex-direction: column; gap: 16px;'>"

        for date_str in sorted_dates:
            tasks = tasks_by_date[date_str]

            # 解析日期
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]

            # 计算当日总番茄钟数
            daily_total = sum(task['actual_pomodoros'] for task in tasks)

            # 日期标题 - 使用清晰的蓝色背景
            html += f"""
            <div style='margin-bottom: 4px;'>
                <div style='
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 14px;
                    background-color: {Colors.PRIMARY};
                    border-radius: 8px;
                    margin-bottom: 8px;
                '>
                    <span style='color: white; font-size: 14px; font-weight: 600;'>
                        {date_obj.strftime('%Y年%m月%d日')} {weekday}
                    </span>
                    <span style='color: white; font-size: 14px; font-weight: 600;'>
                        {daily_total} 🍅
                    </span>
                </div>
            """

            # 任务列表
            html += "<div style='display: flex; flex-direction: column; gap: 10px;'>"

            for task in tasks:
                quadrant_name = quadrant_names[task['quadrant']]
                quadrant_color = quadrant_colors[task['quadrant']]

                # 计算各种时间信息
                created_date = datetime.fromisoformat(task['created_date'])
                completed_date = datetime.fromisoformat(task['completed_date']) if task['completed_date'] else datetime.now()

                # 创建时间
                created_str = created_date.strftime("%m-%d %H:%M")

                # 完成时间 - 尝试从会话中获取精确时间
                completed_time = ""
                if task['completed_date']:
                    sessions = self.storage.get_pomodoro_sessions_by_task(task['id'])
                    if sessions:
                        last_session = None
                        for session in sessions:
                            if session['status'] == 'completed':
                                if not last_session or session['end_time'] > last_session['end_time']:
                                    last_session = session
                        if last_session and last_session['end_time']:
                            try:
                                time_obj = datetime.fromisoformat(last_session['end_time'])
                                completed_time = time_obj.strftime("%m-%d %H:%M")
                            except:
                                completed_time = completed_date.strftime("%m-%d") + " --:--"
                    else:
                        completed_time = completed_date.strftime("%m-%d") + " --:--"

                # 消耗时间（天数）
                duration_days = max(1, (completed_date - created_date).days + 1)
                duration_str = f"{duration_days}天"

                # 预期和实际番茄钟数
                estimated = task['estimated_pomodoros']
                actual = task['actual_pomodoros']

                html += f"""
                <div style='
                    background-color: #FFFFFF;
                    border-radius: 8px;
                    padding: 12px 14px;
                    border-left: 4px solid {quadrant_color};
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
                '>
                    <!-- 第一行：象限标签 + 任务名称 -->
                    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                        <div style='
                            background-color: {quadrant_color};
                            color: #FFFFFF;
                            padding: 3px 8px;
                            border-radius: 4px;
                            font-size: 11px;
                            font-weight: 600;
                            white-space: nowrap;
                            flex-shrink: 0;
                        '>
                            {quadrant_name}
                        </div>
                        <div style='
                            color: {Colors.TEXT_PRIMARY};
                            font-size: 14px;
                            font-weight: 500;
                            flex: 1;
                        '>
                            {task['description']}
                        </div>
                    </div>

                    <!-- 第二行：所有时间信息在一行 -->
                    <div style='display: flex; align-items: center; gap: 16px; padding-left: 4px;'>
                        <div style='display: flex; align-items: center; gap: 4px;'>
                            <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px; white-space: nowrap;'>创建:</span>
                            <span style='color: {Colors.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;'>{created_str}</span>
                        </div>
                        <div style='display: flex; align-items: center; gap: 4px;'>
                            <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px; white-space: nowrap;'>完成:</span>
                            <span style='color: {Colors.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;'>{completed_time}</span>
                        </div>
                        <div style='display: flex; align-items: center; gap: 4px;'>
                            <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px; white-space: nowrap;'>耗时:</span>
                            <span style='color: {Colors.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;'>{duration_str}</span>
                        </div>
                        <div style='display: flex; align-items: center; gap: 4px;'>
                            <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px; white-space: nowrap;'>预期:</span>
                            <span style='color: {Colors.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;'>{estimated}🍅</span>
                        </div>
                        <div style='display: flex; align-items: center; gap: 4px;'>
                            <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px; white-space: nowrap;'>实际:</span>
                            <span style='color: {Colors.PRIMARY}; font-size: 13px; font-weight: 600;'>{actual}🍅</span>
                        </div>
                    </div>
                </div>
                """

            html += "</div></div>"

        html += "</div>"

        self.tasks_list_widget.setText(html)
        self.tasks_list_widget.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                padding: {Spacing.SM}px;
                padding-bottom: 40px;
            }}
        """)



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

        # 日志区域 - 任务完成卡片流
        log_section = QVBoxLayout()
        log_section.setSpacing(Spacing.MD)

        log_title = QLabel("完成记录")
        log_title.setFont(Fonts.body())
        log_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600;")
        log_section.addWidget(log_title)

        # 创建一个容器 widget 来包裹 scroll area
        log_scroll_container = QWidget()
        log_scroll_layout = QVBoxLayout(log_scroll_container)
        log_scroll_layout.setContentsMargins(0, 0, 0, 0)
        log_scroll_layout.setSpacing(0)

        self.log_scroll = QScrollArea()
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setMinimumHeight(150)
        self.log_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        self.log_list_widget = QLabel("暂无完成记录")
        self.log_list_widget.setFont(Fonts.body())
        self.log_list_widget.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                background-color: transparent;
                padding: {Spacing.SM}px;
                padding-bottom: 40px;
            }}
        """)
        self.log_list_widget.setWordWrap(True)
        # 移除 AlignTop 和 AlignLeft，让 QLabel 自然扩展
        self.log_scroll.setWidget(self.log_list_widget)

        log_scroll_layout.addWidget(self.log_scroll)

        # 在 scroll area 外层添加底部间距
        log_scroll_layout.addSpacing(Spacing.LG)  # 24px 底部留白

        log_section.addWidget(log_scroll_container)
        log_container = QWidget()
        log_container.setLayout(log_section)
        splitter.addWidget(log_container)

        # 心得感悟区域
        reflection_section = QVBoxLayout()
        reflection_section.setSpacing(Spacing.MD)

        reflection_title = QLabel("今日心得")
        reflection_title.setFont(Fonts.body())
        reflection_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-weight: 600;")
        reflection_section.addWidget(reflection_title)

        self.reflection_input = QTextEdit()
        self.reflection_input.setPlaceholderText("今天有什么收获和感悟...")
        self.reflection_input.setMinimumHeight(80)  # ✅ 降低最小高度
        self.reflection_input.setMaximumHeight(120)  # ✅ 限制最大高度，避免占据太多空间
        self.reflection_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # ✅ 固定高度策略
        self.reflection_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_CARD}px;
                padding: {Spacing.MD}px;
                font-size: 13px;
                line-height: 1.6;
                color: {Colors.TEXT_PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.BG_GLOBAL};
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

        # ✅ 调整比例：任务:日志:心得 = 2:7:0
        # 心得区域设为 0 表示使用固定大小（由 setMinimumHeight/MaximumHeight 决定）
        # 这样"完成记录"可以获得更多滚动空间
        splitter.setStretchFactor(0, 2)  # 完成的任务：约占 22%
        splitter.setStretchFactor(1, 7)  # 完成记录：约占 78%
        splitter.setStretchFactor(2, 0)  # 今日心得：固定大小（不参与伸缩）

        # ✅ 关键修复：禁用垂直分割线的调整功能，防止心得区域被压缩
        splitter.handle(0).setEnabled(False)  # 禁用任务和日志之间的分割线
        splitter.handle(1).setEnabled(False)  # 禁用日志和心得之间的分割线

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

        # 更新日志列表 - 任务完成卡片流
        if stats.logs:
            # 卡片流样式：每个完成记录是一个独立的卡片
            log_html = f"<div style='display: flex; flex-direction: column; gap: 12px; padding-bottom: 32px;'>"

            for log in stats.logs:
                timestamp = log['timestamp'][11:16]  # 只取 HH:MM
                content = log['content']

                # 解析日志内容，提取关键信息
                # 格式: "✅ 完成番茄钟 - [象限] 任务名称 (开始时间: HH:MM)"
                is_completion = "完成番茄钟" in content

                if is_completion:
                    # 任务完成卡片
                    log_html += f"""
                    <div style='
                        background: linear-gradient(135deg, {Colors.BG_CARD} 0%, rgba(82, 196, 26, 0.08) 100%);
                        border-radius: 12px;
                        padding: 14px 16px;
                        border-left: 3px solid {Colors.SUCCESS};
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
                    '>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                            <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px; font-weight: 500;'>{timestamp}</span>
                            <span style='color: {Colors.SUCCESS}; font-size: 16px;'>✅</span>
                        </div>
                        <div style='color: {Colors.TEXT_PRIMARY}; font-size: 14px; line-height: 1.5;'>
                            {self._format_log_content(content)}
                        </div>
                    </div>
                    """
                else:
                    # 普通日志卡片
                    log_html += f"""
                    <div style='
                        background-color: {Colors.BG_CARD};
                        border-radius: 12px;
                        padding: 12px 16px;
                        border-left: 3px solid {Colors.TEXT_TERTIARY};
                    '>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'>
                            <span style='color: {Colors.TEXT_TERTIARY}; font-size: 12px; font-weight: 500;'>{timestamp}</span>
                        </div>
                        <div style='color: {Colors.TEXT_PRIMARY}; font-size: 13px; line-height: 1.5;'>
                            {content}
                        </div>
                    </div>
                    """

            log_html += "</div>"
            self.log_list_widget.setText(log_html)
            self.log_list_widget.setStyleSheet(f"""
                QLabel {{
                    background-color: transparent;
                    padding: {Spacing.SM}px;
                    padding-bottom: 40px;
                }}
            """)
        else:
            self.log_list_widget.setText("暂无完成记录")
            self.log_list_widget.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; padding: {Spacing.MD}px; font-size: 13px;")

    def _format_log_content(self, content: str) -> str:
        """
        格式化日志内容，突出显示关键信息

        Args:
            content: 原始日志内容

        Returns:
            格式化后的HTML
        """
        # 提取象限标签和任务名称
        # 格式: "✅ 完成番茄钟 - [重要紧急] 任务名称 (开始时间: HH:MM)"
        import re

        # 匹配象限标签
        quadrant_match = re.search(r'\[([^\]]+)\]', content)
        if quadrant_match:
            quadrant_name = quadrant_match.group(1)
            quadrant_colors = {
                "重要紧急": Colors.QUADRANT_0,
                "重要不紧急": Colors.QUADRANT_1,
                "紧急不重要": Colors.QUADRANT_2,
                "不紧急不重要": Colors.QUADRANT_3
            }
            quadrant_color = quadrant_colors.get(quadrant_name, Colors.TEXT_SECONDARY)

            # 替换象限标签为带颜色的标签
            content = re.sub(
                r'\[([^\]]+)\]',
                f"<span style='color: {quadrant_color}; font-weight: 600; font-size: 12px;'>[\\1]</span>",
                content
            )

        # 移除时间戳部分（已经在顶部显示）
        content = re.sub(r'\(开始时间:\s*\d{2}:\d{2}\)', '', content)

        # 移除 "✅ 完成番茄钟 - " 前缀
        content = content.replace("✅ 完成番茄钟 - ", "")

        return content.strip()

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
        # init_ui 中设置了日历为今天，会触发 on_date_selected
        # 但需要确保所有组件都已创建，所以手动触发一次
        self.on_date_selected()
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

        # 默认选中今天
        self.calendar.setSelectedDate(QDate.currentDate())

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
        # 刷新详情面板（如果当前有选中日期）
        if self.detail_panel.current_date:
            self.refresh_detail_panel(self.detail_panel.current_date)

    def refresh_detail_panel(self, date_str: str):
        """
        刷新详情面板

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)
        """
        daily_stats = self.statistics.get_daily_statistics(date_str)
        self.detail_panel.update_detail(daily_stats, date_str)

    def refresh_today_if_needed(self):
        """如果当前显示的是今天，则刷新（用于新日志添加后）"""
        today = datetime.now().strftime("%Y-%m-%d")
        current = self.detail_panel.current_date

        if current == today:
            self.refresh_detail_panel(today)
        elif current is None:
            # 如果还没有选中任何日期，默认显示今天
            self.calendar.setSelectedDate(QDate.currentDate())
        else:
            # 仍然重新标记日历，因为今天有了新的番茄钟
            self.mark_calendar_dates()

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
        # 确保 detail_panel 已创建
        if not hasattr(self, 'detail_panel') or self.detail_panel is None:
            return

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
