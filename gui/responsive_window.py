"""响应式主窗口 - 基于屏幕尺寸的自适应布局"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QSize, QEvent, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
import sys

from data.storage import Storage
from core.task_manager import TaskManager
from core.pomodoro_timer import PomodoroTimer
from core.statistics import Statistics
from utils.logger import Logger
from config import Config
from gui.styles import Colors, Spacing
from gui.optimized_timer_panel import OptimizedTimerPanel
from gui.optimized_quadrants_view import OptimizedQuadrantsView
from gui.responsive_history_view import ResponsiveHistoryView


class ResponsiveWindow(QMainWindow):
    """响应式主窗口 - 基于屏幕尺寸自适应"""

    # 定义信号
    resized = pyqtSignal()

    def __init__(self):
        super().__init__()

        # 断点定义
        self.BREAKPOINT_WIDE = 1400  # 宽屏断点
        self.MIN_WIDTH = 1280  # 最小宽度
        self.MIN_HEIGHT = 800  # 最小高度

        # 初始化数据层
        self.storage = Storage()
        self.task_manager = TaskManager(self.storage)

        # 从配置获取番茄钟时长
        timer_duration = Config.get_timer_duration()
        self.timer = PomodoroTimer(duration_seconds=timer_duration)
        self.statistics = Statistics(self.storage)
        self.logger = Logger(self.storage)

        # 设置窗口
        self.init_ui()
        self.setup_menu()
        self.setup_shortcuts()

        # 更新Dashboard
        self.update_dashboard()

        # 监听窗口大小变化
        self.resized.connect(self.on_window_resized)

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("番茄钟效率工具")
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.resize(1440, 900)  # 默认尺寸

        # 全局样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Colors.BG_GLOBAL};
            }}

            QWidget {{
                background-color: transparent;
            }}
        """)

        # 中央部件
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {Colors.BG_GLOBAL};")
        self.setCentralWidget(central_widget)

        # 主布局 - 使用VBoxLayout而不是HBoxLayout，方便未来纵向布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建水平分割器（三栏布局）
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Colors.BORDER};
                width: 1px;
            }}

            QSplitter::handle:hover {{
                background-color: {Colors.TEXT_TERTIARY};
                width: 2px;
            }}
        """)

        # ============= 左侧栏：任务列表 =============
        # 使用QScrollArea包装，确保内容可滚动
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.quadrants_view = OptimizedQuadrantsView(self.task_manager, self.timer)
        # 设置最小宽度
        self.quadrants_view.setMinimumWidth(300)

        left_scroll.setWidget(self.quadrants_view)
        self.main_splitter.addWidget(left_scroll)

        # ============= 中央栏：番茄钟 + Dashboard =============
        # 中央区域使用垂直布局
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # 番茄钟面板（自适应页面高度）
        self.timer_panel = OptimizedTimerPanel(
            self.timer,
            self.task_manager,
            self.logger
        )
        # 注入statistics
        self.timer_panel.statistics = self.statistics

        # 直接添加到布局，不使用滚动区域
        center_layout.addWidget(self.timer_panel, stretch=1)

        # Dashboard（自适应页面高度）
        from gui.dashboard import TodayDashboard
        self.dashboard_wrapper = TodayDashboard()

        # 直接添加到布局，不使用滚动区域
        center_layout.addWidget(self.dashboard_wrapper, stretch=2)

        # 设置中央容器最小宽度
        center_container.setMinimumWidth(400)
        self.main_splitter.addWidget(center_container)

        # ============= 右侧栏：历史记录 =============
        # 第三优先级，可折叠
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.history_view = ResponsiveHistoryView(self.statistics, self.logger, self.storage)
        # 设置固定宽度，不允许动态调整（解决滚动截断问题）
        self.history_view.setMinimumWidth(320)
        self.history_view.setMaximumWidth(320)  # ✅ 固定最大宽度，防止拉伸

        right_scroll.setWidget(self.history_view)
        self.main_splitter.addWidget(right_scroll)

        # ============= 设置初始比例 =============
        # 左侧:中央:右侧 = 25:45:30 (给历史记录更多空间)
        self.main_splitter.setStretchFactor(0, 25)
        self.main_splitter.setStretchFactor(1, 45)
        self.main_splitter.setStretchFactor(2, 30)

        # 设置最小尺寸 (280:500:320)
        self.main_splitter.setSizes([280, 500, 320])  # 初始宽度分配

        # ✅ 关键修复：禁用右侧栏的可调整大小功能
        # 这样可以避免动态调整导致的内容高度计算问题
        self.main_splitter.setCollapsible(2, False)  # 禁用右侧栏折叠
        # 锁定分割器位置，防止动态调整
        self.main_splitter.handle(1).setEnabled(False)  # 禁用中央和右侧之间的分割线
        # self.main_splitter.handle(2).setEnabled(False)  # 可选：完全禁用所有分割线

        main_layout.addWidget(self.main_splitter)

        # 连接信号
        self.connect_signals()

        # 设置定时更新（每分钟更新Dashboard）
        from PyQt6.QtCore import QTimer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(60000)

        # 安装事件过滤器以监听窗口大小变化
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器 - 监听窗口大小变化"""
        if obj is self and event.type() == QEvent.Type.Resize:
            # 延迟处理，避免频繁触发
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.on_window_resized)
        return super().eventFilter(obj, event)

    def on_window_resized(self):
        """窗口大小变化时的响应式处理"""
        current_width = self.width()

        # 根据窗口宽度应用不同的布局策略
        if current_width >= self.BREAKPOINT_WIDE:
            # 宽屏模式：三栏全部显示
            self.apply_wide_layout()
        else:
            # 中屏模式：右侧历史记录可以折叠
            self.apply_medium_layout()

    def apply_wide_layout(self):
        """宽屏布局（≥1400px）"""
        # 确保所有列都可见
        for i in range(self.main_splitter.count()):
            self.main_splitter.handle(i).setEnabled(True)

        # 宽屏下右侧栏可以更宽一些
        sizes = self.main_splitter.sizes()
        if len(sizes) == 3:
            total = sum(sizes)
            # 调整比例为 25:45:30 (给历史记录更多空间)
            self.main_splitter.setSizes([
                int(total * 0.25),
                int(total * 0.45),
                int(total * 0.30)
            ])

    def apply_medium_layout(self):
        """中屏布局（<1400px）"""
        sizes = self.main_splitter.sizes()
        if len(sizes) == 3:
            total = sum(sizes)
            # 中屏下适当压缩，比例调整为 28:47:25
            self.main_splitter.setSizes([
                int(total * 0.28),
                int(total * 0.47),
                int(total * 0.25)
            ])

    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {Colors.BG_CARD};
                border-bottom: 1px solid {Colors.BORDER};
                padding: {Spacing.SM}px {Spacing.MD}px;
            }}

            QMenuBar::item {{
                background-color: transparent;
                color: {Colors.TEXT_PRIMARY};
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Spacing.RADIUS_SMALL}px;
            }}

            QMenuBar::item:selected {{
                background-color: {Colors.BG_HOVER};
            }}

            QMenu {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SMALL}px;
                padding: {Spacing.XS}px;
            }}

            QMenu::item {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                color: {Colors.TEXT_PRIMARY};
            }}

            QMenu::item:selected {{
                background-color: {Colors.BG_SELECTED};
            }}
        """)

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        export_action = QAction("导出数据", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")

        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut(QKeySequence("Ctrl+R"))
        refresh_action.triggered.connect(self.refresh_all)
        edit_menu.addAction(refresh_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_shortcuts(self):
        """设置快捷键"""
        pause_action = QAction("开始/暂停", self)
        pause_action.setShortcut(QKeySequence("Ctrl+P"))
        pause_action.triggered.connect(self.toggle_timer)
        self.addAction(pause_action)

        stop_action = QAction("停止", self)
        stop_action.setShortcut(QKeySequence("Ctrl+S"))
        stop_action.triggered.connect(self.stop_timer)
        self.addAction(stop_action)

    def connect_signals(self):
        """连接信号"""
        self.timer.set_state_change_callback(self.on_timer_state_changed)
        self.timer.set_complete_callback(self.on_timer_complete)

        self.quadrants_view.task_updated.connect(self.on_task_updated)
        self.quadrants_view.task_selected.connect(self.on_task_selected)

        self.timer_panel.log_added.connect(self.on_log_added)

    def on_timer_state_changed(self, state):
        """计时器状态变化"""
        self.quadrants_view.refresh()

    def on_timer_complete(self):
        """计时器完成"""
        # 先执行计时器面板的完成逻辑（结束会话、累计番茄钟）
        self.timer_panel.on_timer_complete()

        # 再更新界面
        self.update_dashboard()
        self.history_view.refresh()
        self.quadrants_view.refresh()

        # 显示通知
        self.show_notification("番茄钟完成", "恭喜！你完成了一个番茄钟。")

    def on_task_updated(self):
        """任务更新"""
        self.quadrants_view.refresh()
        self.update_dashboard()
        self.timer_panel.refresh_task_list()
        # 刷新历史记录（包括"已完成任务"和"日期详情"）
        self.history_view.refresh()
        # 如果当前显示今天，刷新详情面板
        self.history_view.refresh_today_if_needed()

    def on_task_selected(self, task_id: int):
        """任务选择"""
        self.timer_panel.select_task_by_id(task_id)

    def on_log_added(self):
        """日志添加"""
        self.history_view.refresh()
        # 如果历史视图当前显示的是今天，强制刷新详情面板
        self.history_view.refresh_today_if_needed()

    def update_dashboard(self):
        """更新Dashboard"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        daily_stats = self.statistics.get_daily_statistics(today)
        self.dashboard_wrapper.update_dashboard(daily_stats)

    def toggle_timer(self):
        """切换计时器"""
        if self.timer.is_running:
            self.timer.pause()
        else:
            if self.timer.is_paused:
                self.timer.resume()
            else:
                self.timer_panel.start_pomodoro()

    def stop_timer(self):
        """停止计时器"""
        reply = QMessageBox.question(
            self,
            "确认停止",
            "确定要停止当前番茄钟吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 结束当前会话（如果有）
            if self.timer_panel.current_session_id is not None:
                from datetime import datetime
                from data.storage import TimerStatus
                end_time = datetime.now().isoformat()
                self.task_manager.storage.end_pomodoro_session(
                    self.timer_panel.current_session_id,
                    end_time,
                    TimerStatus.ABANDONED
                )
                self.timer_panel.current_session_id = None
                self.timer_panel.current_session_start_time = None

            self.timer.stop(abandon=True)
            # 重置计时器，显示完整的番茄钟时长
            self.timer.reset()
            self.timer_panel.refresh()

    def refresh_all(self):
        """刷新所有视图"""
        self.quadrants_view.refresh()
        self.timer_panel.refresh()
        self.history_view.refresh()
        self.update_dashboard()

    def export_data(self):
        """导出数据"""
        from datetime import datetime
        from PyQt6.QtWidgets import QFileDialog

        default_filename = f"pomodoro_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出数据",
            default_filename,
            "JSON Files (*.json)"
        )

        if filename:
            if self.storage.export_to_json(filename):
                QMessageBox.information(self, "成功", "数据导出成功！")
            else:
                QMessageBox.critical(self, "错误", "数据导出失败！")

    def show_about(self):
        """显示关于"""
        QMessageBox.about(
            self,
            "关于 番茄钟效率工具",
            """
            <h2>番茄钟效率工具 (Pomodoro Focus Pro)</h2>
            <p>版本: 3.0.0 (响应式布局版)</p>
            <p>结合艾森豪威尔矩阵与番茄工作法的效率工具</p>
            <p>技术栈: Python + PyQt6 + SQLite</p>
            <hr>
            <p><b>快捷键:</b></p>
            <ul>
                <li><b>Ctrl+P</b>: 开始/暂停番茄钟</li>
                <li><b>Ctrl+S</b>: 停止当前番茄钟</li>
                <li><b>Ctrl+E</b>: 导出数据</li>
                <li><b>Ctrl+R</b>: 刷新界面</li>
            </ul>
            <p><b>响应式设计:</b></p>
            <ul>
                <li>✨ 宽屏模式（≥1400px）：三栏并列布局</li>
                <li>✨ 中屏模式（<1400px）：智能压缩布局</li>
                <li>✨ 自适应滚动：所有模块可独立滚动</li>
                <li>✨ 最小支持1280×800分辨率</li>
            </ul>
            """
        )

    def show_notification(self, title: str, message: str):
        """显示系统通知"""
        try:
            import subprocess
            subprocess.run([
                'osascript',
                '-e', f'display notification "{message}" with title "{title}"'
            ])
        except Exception:
            pass

    def closeEvent(self, event):
        """关闭事件"""
        if self.timer.is_running or self.timer.is_paused:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "计时器正在运行，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        self.storage.close()
        event.accept()
