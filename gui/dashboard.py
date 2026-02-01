"""今日概况仪表盘 - 响应式布局版"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
from core.statistics import DailyStatistics
from gui.styles import (
    Colors, Fonts, Spacing
)


# 卡片样式（带阴影）
def get_card_style(bg_color: str, has_data: bool = False) -> str:
    """获取卡片样式"""
    border_color = Colors.PRIMARY if has_data else Colors.BORDER
    return f"""
        QFrame {{
            background-color: {bg_color};
            border-radius: 12px;
            border: 1px solid {border_color};
        }}
    """


# 进度条样式
PROGRESS_BAR_BG_STYLE = """
    QFrame {
        background-color: """ + Colors.BG_HOVER + """;
        border-radius: 4px;
    }
"""

PROGRESS_BAR_FILL_STYLE = """
    QFrame {
        background-color: """ + Colors.PRIMARY + """;
        border-radius: 4px;
    }
"""


class StatCard(QFrame):
    """统计卡片 - 响应式设计"""

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)

        self.title = title
        self.icon = icon
        self.value_label = None
        self.subtitle_label = None
        self.has_data = False  # 是否有数据

        self.init_ui()
        self.add_shadow()

    def init_ui(self):
        """初始化UI"""
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        self.layout().setSpacing(Spacing.SM)

        # 最小高度（避免太小）
        self.setMinimumHeight(100)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.setSpacing(Spacing.SM)

        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setFont(Fonts.body(16))
            title_layout.addWidget(icon_label)

        title_label = QLabel(self.title)
        title_label.setFont(Fonts.caption())
        title_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        title_layout.addWidget(title_label)

        title_layout.addStretch()
        self.layout().addLayout(title_layout)

        # 核心数值（自适应大小）
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setWordWrap(True)
        self.layout().addWidget(self.value_label)

        # 副标题（状态说明）
        self.subtitle_label = QLabel("")
        self.subtitle_label.setFont(Fonts.caption())
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.layout().addWidget(self.subtitle_label)

        self.layout().addStretch()

        # 初始样式（无数据状态）
        self.update_style()

    def add_shadow(self):
        """添加卡片阴影"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 10))
        self.setGraphicsEffect(shadow)

    def update_style(self):
        """更新卡片样式（根据是否有数据）"""
        bg_color = Colors.BG_CARD if not self.has_data else "#F0F9FF"
        self.setStyleSheet(get_card_style(bg_color, self.has_data))

    def update_font_size(self):
        """根据卡片宽度和高度动态调整字体大小"""
        if self.value_label:
            card_width = self.width() if self.width() > 0 else 150
            card_height = self.height() if self.height() > 0 else 100

            # 计算可用空间（考虑padding和间距）
            available_width = card_width - 32  # 减去左右padding
            available_height = card_height - 60  # 减去标题和副标题的高度

            # 根据宽度和高度计算合适的字体大小
            font_size_from_width = available_width * 0.35  # 宽度的35%
            font_size_from_height = available_height * 0.5  # 高度的50%

            # 取较小值，确保数字能完整显示
            font_size = min(font_size_from_width, font_size_from_height)

            # 限制字体大小范围（根据卡片大小动态调整）
            if card_width < 120:
                # 非常小的卡片
                font_size = min(font_size, 20)
                min_size = 14
            elif card_width < 150:
                # 小卡片
                font_size = min(font_size, 28)
                min_size = 18
            elif card_width < 200:
                # 中等卡片
                font_size = min(font_size, 36)
                min_size = 22
            else:
                # 大卡片
                font_size = min(font_size, 56)
                min_size = 28

            # 应用字体大小（确保不小于最小值）
            final_size = max(min_size, int(font_size))
            self.value_label.setFont(Fonts.timer_display(final_size))

    def resizeEvent(self, event):
        """窗口大小改变时更新字体大小"""
        super().resizeEvent(event)
        self.update_font_size()

    def set_data(self, value: str, subtitle: str = "", has_data: bool = None):
        """
        更新卡片数据

        Args:
            value: 显示的数值
            subtitle: 副标题/状态说明
            has_data: 是否有数据（决定颜色主题）
        """
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)

        if has_data is not None:
            self.has_data = has_data
            self.update_style()

            # 根据状态调整颜色
            if self.has_data:
                self.value_label.setStyleSheet(f"color: {Colors.PRIMARY}; font-weight: bold;")
            else:
                self.value_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY};")


class PomodoroCard(StatCard):
    """番茄钟卡片"""

    def __init__(self, parent=None):
        super().__init__("今日番茄钟", "🍅", parent)
        self.set_data("0", "还没开始，来一个番茄？", False)

    def update_data(self, count: int):
        """更新数据"""
        if count == 0:
            self.set_data("0", "还没开始，来一个番茄？", False)
        elif count < 4:
            self.set_data(str(count), "好的开始，继续保持！", True)
        elif count < 8:
            self.set_data(str(count), "专注力不错，加油！", True)
        else:
            self.set_data(str(count), "太棒了！今天效率超高！", True)


class FocusTimeCard(StatCard):
    """专注时长卡片"""

    def __init__(self, parent=None):
        super().__init__("专注时长", "⏱️", parent)
        self.set_data("0m", "开始你的专注之旅", False)

    def update_data(self, minutes: int):
        """更新数据"""
        if minutes == 0:
            self.set_data("0m", "开始你的专注之旅", False)
        else:
            hours = minutes // 60
            mins = minutes % 60

            if hours > 0:
                time_str = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
                subtitle = f"累计专注 {hours} 小时" if mins == 0 else f"专注 {hours} 小时 {mins} 分钟"
            else:
                time_str = f"{mins}m"
                subtitle = "专注进行中..."

            # 根据时长给出不同的鼓励
            if minutes >= 240:  # 4小时以上
                subtitle = "专注力爆表！"
            elif minutes >= 180:  # 3小时以上
                subtitle = "非常高效的一天！"
            elif minutes >= 120:  # 2小时以上
                subtitle = "表现不错，继续保持"
            elif minutes >= 60:  # 1小时以上
                subtitle = "好的开始"

            self.set_data(time_str, subtitle, True)


class CompletedTasksCard(StatCard):
    """完成任务卡片"""

    def __init__(self, parent=None):
        super().__init__("完成任务", "✅", parent)
        self.set_data("0", "等待任务完成", False)

    def update_data(self, count: int):
        """更新数据"""
        if count == 0:
            self.set_data("0", "还没有完成任务", False)
        elif count == 1:
            self.set_data("1", "完成第一个任务！", True)
        elif count < 5:
            self.set_data(str(count), f"已完成 {count} 个任务", True)
        else:
            self.set_data(str(count), "任务收割机！", True)


class CompletionRateCard(StatCard):
    """完成率卡片"""

    def __init__(self, parent=None):
        super().__init__("完成率", "📊", parent)
        self.rate = 0
        self.set_data("0%", "开始行动", False)

    def update_data(self, rate: float):
        """更新数据"""
        self.rate = rate

        if rate == 0:
            self.set_data("0%", "还没开始，来一个番茄？", False)
        elif rate < 25:
            self.set_data(f"{rate:.0f}%", "好的开始，继续保持！", True)
        elif rate < 50:
            self.set_data(f"{rate:.0f}%", "稳步推进中", True)
        elif rate < 75:
            self.set_data(f"{rate:.0f}%", "表现不错", True)
        elif rate < 100:
            self.set_data(f"{rate:.0f}%", "即将完成！", True)
        else:
            self.set_data("100%", "完美收官！", True)

        # 根据完成率调整颜色
        if rate >= 80:
            self.value_label.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold;")
        elif rate >= 50:
            self.value_label.setStyleSheet(f"color: {Colors.PRIMARY}; font-weight: bold;")
        elif rate > 0:
            self.value_label.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold;")


class TodayDashboard(QFrame):
    """今日概况仪表盘 - 完全响应式设计"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []  # 保存所有卡片引用
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        # 主容器样式
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border-radius: {Spacing.RADIUS_CARD}px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XXL, Spacing.XXL, Spacing.XXL, Spacing.XXL)
        main_layout.setSpacing(Spacing.XL)

        # 标题
        title = QLabel("今日概况")
        title.setFont(Fonts.title(18))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        main_layout.addWidget(title)

        # 主数据卡片（2x2网格，完全响应式）
        cards_layout = QGridLayout()
        cards_layout.setSpacing(Spacing.LG)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # 创建四个卡片
        self.pomodoro_card = PomodoroCard()
        self.focus_time_card = FocusTimeCard()
        self.completed_card = CompletedTasksCard()
        self.rate_card = CompletionRateCard()

        # 保存卡片引用
        self.cards = [
            self.pomodoro_card,
            self.focus_time_card,
            self.completed_card,
            self.rate_card
        ]

        # 添加到网格布局（2x2）
        cards_layout.addWidget(self.pomodoro_card, 0, 0)
        cards_layout.addWidget(self.focus_time_card, 0, 1)
        cards_layout.addWidget(self.completed_card, 1, 0)
        cards_layout.addWidget(self.rate_card, 1, 1)

        # 设置列的伸展因子（让两列等宽）
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)

        # 设置行的伸展因子（让两行等高）
        cards_layout.setRowStretch(0, 1)
        cards_layout.setRowStretch(1, 1)

        main_layout.addLayout(cards_layout)

        # 完成率进度条（可选增强）
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(Spacing.SM)

        # 进度条标签
        progress_header = QHBoxLayout()
        self.progress_label = QLabel("今日进度")
        self.progress_label.setFont(Fonts.body())
        self.progress_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        progress_header.addWidget(self.progress_label)

        self.progress_value_label = QLabel("0%")
        self.progress_value_label.setFont(Fonts.body())
        self.progress_value_label.setStyleSheet(f"color: {Colors.PRIMARY}; font-weight: 600;")
        progress_header.addStretch()
        progress_header.addWidget(self.progress_value_label)

        progress_layout.addLayout(progress_header)

        # 进度条背景
        self.progress_bar_bg = QFrame()
        self.progress_bar_bg.setFixedHeight(8)
        self.progress_bar_bg.setStyleSheet(PROGRESS_BAR_BG_STYLE)

        # 进度条填充
        self.progress_bar_fill = QFrame(self.progress_bar_bg)
        self.progress_bar_fill.setGeometry(0, 0, 0, 8)
        self.progress_bar_fill.setStyleSheet(PROGRESS_BAR_FILL_STYLE)

        progress_layout.addWidget(self.progress_bar_bg)

        main_layout.addWidget(progress_container)

        # 添加弹性空间（让布局更自然）
        main_layout.addStretch()

    def update_dashboard(self, stats: DailyStatistics):
        """更新仪表盘数据"""
        # 1. 更新番茄钟数
        self.pomodoro_card.update_data(stats.total_pomodoros)

        # 2. 更新专注时长
        focus_minutes = stats.total_pomodoros * 30
        self.focus_time_card.update_data(focus_minutes)

        # 3. 更新完成任务数
        self.completed_card.update_data(len(stats.completed_tasks))

        # 4. 更新完成率
        total_tasks = sum(stats.pending_counts.values()) + len(stats.completed_tasks)
        if total_tasks > 0:
            completion_rate = (len(stats.completed_tasks) / total_tasks) * 100
        else:
            completion_rate = 0

        self.rate_card.update_data(completion_rate)

        # 5. 更新进度条
        self.progress_value_label.setText(f"{completion_rate:.0f}%")

        # 延迟更新进度条宽度（确保组件已渲染）
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._update_progress_bar(completion_rate))
        # 同时更新卡片字体大小
        QTimer.singleShot(0, self._update_cards_font_size)

    def _update_progress_bar(self, rate: float):
        """更新进度条（内部方法）"""
        if self.progress_bar_bg.width() > 0:
            fill_width = int(self.progress_bar_bg.width() * rate / 100)
            self.progress_bar_fill.setFixedWidth(fill_width)

    def _update_cards_font_size(self):
        """更新所有卡片的字体大小"""
        for card in self.cards:
            card.update_font_size()

    def resizeEvent(self, event):
        """窗口大小改变时更新所有子元素"""
        super().resizeEvent(event)
        # 重新计算进度条宽度
        if hasattr(self, 'rate_card'):
            self._update_progress_bar(self.rate_card.rate)
        # 更新所有卡片字体大小
        if hasattr(self, 'cards'):
            self._update_cards_font_size()
