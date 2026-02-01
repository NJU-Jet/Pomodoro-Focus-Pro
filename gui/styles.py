"""全局样式系统 - macOS原生极简风格"""

from PyQt6.QtGui import QColor, QPalette, QFont, QBrush
from PyQt6.QtCore import Qt

# ==================== 颜色系统 ====================

class Colors:
    """配色方案"""

    # 背景色
    BG_GLOBAL = "#F5F6F8"          # 全局背景
    BG_CARD = "#FFFFFF"            # 卡片背景
    BG_HOVER = "#F9FAFB"           # 悬停背景
    BG_SELECTED = "#EFF6FF"        # 选中背景

    # 番茄钟核心区背景（视觉锚点）
    BG_TIMER = "#EAF2FF"           # 番茄钟专属淡蓝背景

    # 分割线
    BORDER = "#E5E7EB"             # 边框、分割线
    BORDER_LIGHT = "#F3F4F6"       # 浅色分割线

    # 文字色
    TEXT_PRIMARY = "#111827"       # 主文字
    TEXT_SECONDARY = "#6B7280"     # 次级文字
    TEXT_TERTIARY = "#9CA3AF"      # 辅助文字
    TEXT_WHITE = "#FFFFFF"         # 白色文字

    # 番茄钟专用色
    TIMER_DISPLAY = "#1F2A44"      # 倒计时数字（深蓝近黑）
    TIMER_STATUS = "#6B7A99"       # 状态文案（灰蓝）

    # 功能色
    PRIMARY = "#3B82F6"            # 主操作、选中态
    PRIMARY_HOVER = "#2563EB"      # 主色悬停
    SUCCESS = "#22C55E"            # 成功、进行中
    WARNING = "#F59E0B"            # 警告
    DANGER = "#EF4444"             # 危险、重要紧急

    # 象限色（细色条）
    QUADRANT_0 = DANGER            # 重要紧急
    QUADRANT_1 = WARNING           # 重要不紧急
    QUADRANT_2 = "#4B5563"         # 紧急不重要（深灰）
    QUADRANT_3 = "#9CA3AF"         # 不紧急不重要（浅灰）

    # 日历色（温和回顾风格）
    CALENDAR_BG = "#F7F8FA"        # 日历背景
    CALENDAR_GRID = "#E5E7EB"      # 日历网格线
    CALENDAR_TODAY = "#3B82F6"     # 今天的描边色
    CALENDAR_HAS_DATA = "#93C5FD"  # 有记录的浅蓝标记
    CALENDAR_HAS_DATA_HIGH = "#3B82F6"  # 有记录的深蓝标记

    # 状态色
    STATUS_READY = TEXT_SECONDARY
    STATUS_RUNNING = SUCCESS
    STATUS_PAUSED = WARNING
    STATUS_COMPLETED = PRIMARY

# ==================== 字体系统 ====================

class Fonts:
    """字体规范"""

    @staticmethod
    def title(size=18):
        """标题字体 Semi-Bold"""
        font = QFont()
        font.setFamily("Helvetica Neue")
        font.setPointSize(size)
        font.setWeight(QFont.Weight.DemiBold)
        return font

    @staticmethod
    def body(size=14):
        """正文字体 Regular"""
        font = QFont()
        font.setFamily("Helvetica Neue")
        font.setPointSize(size)
        font.setWeight(QFont.Weight.Normal)
        return font

    @staticmethod
    def caption(size=13):
        """辅助字体"""
        font = QFont()
        font.setFamily("Helvetica Neue")
        font.setPointSize(size)
        font.setWeight(QFont.Weight.Normal)
        return font

    @staticmethod
    def timer_display(size=80):
        """计时器数字（等宽）"""
        font = QFont()
        font.setFamily("Monaco")
        font.setPointSize(size)
        font.setWeight(QFont.Weight.Bold)
        return font

    @staticmethod
    def timer_extra_bold(size=88):
        """计时器主显示（超大+超粗）- 视觉锚点"""
        font = QFont()
        font.setFamily("Monaco")
        font.setPointSize(size)
        font.setWeight(QFont.Weight.ExtraBold)  # 800字重
        return font

# ==================== 尺寸规范 ====================

class Spacing:
    """间距规范（优化版 - 增加留白）"""

    UNIT = 4                     # 基础单位
    XS = UNIT * 1                # 4px
    SM = UNIT * 2                # 8px
    MD = UNIT * 3                # 12px
    LG = UNIT * 4                # 16px
    XL = UNIT * 5                # 20px
    XXL = UNIT * 6               # 24px
    XXXL = UNIT * 8              # 32px
    XXXXL = UNIT * 10            # 40px

    # 圆角（统一体系）
    RADIUS_TIMER_CARD = 20       # 番茄钟主卡片圆角（视觉锚点）
    RADIUS_CARD = 16             # 普通卡片圆角
    RADIUS_SUB_CARD = 12         # 次级信息卡片圆角
    RADIUS_BUTTON = 12           # 按钮圆角
    RADIUS_SMALL = 8             # 小圆角

# ==================== 样式字符串 ====================

class Stylesheets:
    """预定义样式表"""

    # ========== 卡片样式 ==========
    CARD = f"""
        QWidget {{
            background-color: {Colors.BG_CARD};
            border-radius: {Spacing.RADIUS_CARD}px;
            border: 1px solid {Colors.BORDER};
        }}
    """

    CARD_FLAT = f"""
        QWidget {{
            background-color: {Colors.BG_CARD};
            border-radius: {Spacing.RADIUS_CARD}px;
        }}
    """

    # ========== 主按钮（实心）==========
    BUTTON_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.PRIMARY};
            color: {Colors.TEXT_WHITE};
            border: none;
            border-radius: {Spacing.RADIUS_BUTTON}px;
            padding: {Spacing.MD}px {Spacing.XL}px;
            font-size: 14px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background-color: {Colors.PRIMARY_HOVER};
        }}

        QPushButton:pressed {{
            background-color: {Colors.PRIMARY_HOVER};
            padding: {Spacing.MD}px {Spacing.XL - 1}px;
        }}

        QPushButton:disabled {{
            background-color: {Colors.TEXT_TERTIARY};
            color: {Colors.BG_GLOBAL};
        }}
    """

    # ========== 次级按钮（描边）==========
    BUTTON_SECONDARY = f"""
        QPushButton {{
            background-color: transparent;
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_BUTTON}px;
            padding: {Spacing.MD}px {Spacing.XL}px;
            font-size: 14px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {Colors.BG_HOVER};
            border-color: {Colors.TEXT_TERTIARY};
        }}

        QPushButton:pressed {{
            background-color: {Colors.BG_SELECTED};
        }}

        QPushButton:disabled {{
            color: {Colors.TEXT_TERTIARY};
            border-color: {Colors.BORDER_LIGHT};
        }}
    """

    # ========== 文字按钮（无边框）==========
    BUTTON_TEXT = f"""
        QPushButton {{
            background-color: transparent;
            color: {Colors.PRIMARY};
            border: none;
            padding: {Spacing.SM}px {Spacing.MD}px;
            font-size: 13px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            color: {Colors.PRIMARY_HOVER};
            background-color: {Colors.BG_SELECTED};
            border-radius: {Spacing.RADIUS_SMALL}px;
        }}

        QPushButton:disabled {{
            color: {Colors.TEXT_TERTIARY};
        }}
    """

    # ========== 输入框 ==========
    INPUT = f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_BUTTON}px;
            padding: {Spacing.MD}px;
            font-size: 13px;
            color: {Colors.TEXT_PRIMARY};
            selection-background-color: {Colors.PRIMARY};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {Colors.PRIMARY};
        }}

        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {Colors.BG_HOVER};
            color: {Colors.TEXT_TERTIARY};
        }}
    """

    # ========== 下拉框 ==========
    COMBO_BOX = f"""
        QComboBox {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_BUTTON}px;
            padding: {Spacing.MD}px;
            font-size: 13px;
            color: {Colors.TEXT_PRIMARY};
        }}

        QComboBox:hover {{
            border-color: {Colors.TEXT_TERTIARY};
        }}

        QComboBox:focus {{
            border-color: {Colors.PRIMARY};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border: none;
        }}

        QComboBox QAbstractItemView {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SMALL}px;
            selection-background-color: {Colors.BG_SELECTED};
            selection-color: {Colors.TEXT_PRIMARY};
            padding: {Spacing.SM}px;
        }}
    """

    # ========== 列表项 ==========
    LIST_ITEM = f"""
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
        }}

        QListWidget::item {{
            border-radius: {Spacing.RADIUS_SMALL}px;
            padding: {Spacing.MD}px;
            margin-bottom: {Spacing.XS}px;
            color: {Colors.TEXT_PRIMARY};
        }}

        QListWidget::item:hover {{
            background-color: {Colors.BG_HOVER};
        }}

        QListWidget::item:selected {{
            background-color: {Colors.BG_SELECTED};
            color: {Colors.PRIMARY};
        }}
    """

    # ========== 标签页 ==========
    TAB_WIDGET = f"""
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
    """

    # ========== 滚动条 ==========
    SCROLL_BAR = f"""
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {Colors.TEXT_TERTIARY};
            border-radius: 4px;
            min-height: 32px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {Colors.TEXT_SECONDARY};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
        }}

        QScrollBar::handle:horizontal {{
            background: {Colors.TEXT_TERTIARY};
            border-radius: 4px;
            min-width: 32px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {Colors.TEXT_SECONDARY};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """

    # ========== 分组框 ==========
    GROUP_BOX = f"""
        QGroupBox {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_CARD}px;
            margin-top: {Spacing.LG}px;
            padding-top: {Spacing.MD}px;
            font-size: 14px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {Spacing.LG}px;
            padding: 0 {Spacing.SM}px;
        }}
    """

    # ========== 标签页容器 ==========
    TAB_CONTAINER = f"""
        QTabWidget {{
            background-color: transparent;
        }}

        QTabWidget::pane {{
            border: none;
            background-color: transparent;
        }}
    """

# ==================== 工具函数 ====================

def apply_card_style(widget):
    """应用卡片样式"""
    widget.setStyleSheet(Stylesheets.CARD)

def apply_primary_button_style(button):
    """应用主按钮样式"""
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setStyleSheet(Stylesheets.BUTTON_PRIMARY)

def apply_secondary_button_style(button):
    """应用次级按钮样式"""
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setStyleSheet(Stylesheets.BUTTON_SECONDARY)

def apply_text_button_style(button):
    """应用文字按钮样式"""
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setStyleSheet(Stylesheets.BUTTON_TEXT)

def apply_input_style(widget):
    """应用输入框样式"""
    widget.setStyleSheet(Stylesheets.INPUT)

def apply_combo_box_style(combo):
    """应用下拉框样式"""
    combo.setStyleSheet(Stylesheets.COMBO_BOX)

def apply_list_style(list_widget):
    """应用列表样式"""
    list_widget.setStyleSheet(Stylesheets.LIST_ITEM)

def apply_scroll_bar_style(widget):
    """应用滚动条样式"""
    widget.setStyleSheet(Stylesheets.SCROLL_BAR)
