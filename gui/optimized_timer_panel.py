"""优化后的计时器面板 - 移除笔记，添加Dashboard"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional
from datetime import datetime
from core.task_manager import TaskManager
from core.pomodoro_timer import PomodoroTimer, TimerState
from core.statistics import Statistics
from data.storage import Storage, TimerStatus
from utils.logger import Logger
from gui.styles import (
    Colors, Fonts, Spacing,
    apply_primary_button_style, apply_secondary_button_style,
    apply_combo_box_style
)

# 番茄钟主卡片专用样式（视觉锚点）
TIMER_CARD_STYLE = f"""
    QFrame {{
        background-color: {Colors.BG_TIMER};
        border-radius: {Spacing.RADIUS_TIMER_CARD}px;
        border: 1px solid {Colors.BORDER};
    }}
"""

# 番茄钟容器阴影效果
TIMER_SHADOW_STYLE = """
    QFrame {
        background-color: transparent;
    }
    QFrame > QFrame {
        background-color: %s;
        border-radius: %dpx;
    }
"""


class OptimizedTimerPanel(QWidget):
    """优化后的计时器面板"""

    log_added = pyqtSignal()

    def __init__(self, timer: PomodoroTimer, task_manager: TaskManager,
                 logger: Logger, parent=None):
        super().__init__(parent)
        self.timer = timer
        self.task_manager = task_manager
        self.logger = logger
        self.storage = task_manager.storage
        self.statistics = Statistics(self.storage)

        self.current_session_id: Optional[int] = None
        self.current_session_start_time: Optional[str] = None  # 记录会话开始时间

        self.init_ui()
        self.connect_signals()
        self.refresh_task_list()
        self.update_ui_state()

    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(Spacing.XXXXL)  # 增加卡片间距

        # ===== 计时器卡片（视觉锚点）=====
        timer_card = QFrame()
        # 使用专属淡蓝背景 + 更大圆角 + 轻微阴影
        timer_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_TIMER};
                border-radius: {Spacing.RADIUS_TIMER_CARD}px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        timer_layout = QVBoxLayout(timer_card)
        timer_layout.setContentsMargins(Spacing.XXXXL, Spacing.XXXXL, Spacing.XXXXL, Spacing.XXXXL)
        timer_layout.setSpacing(Spacing.XXL)  # 增加内部间距

        # 当前任务显示
        self.current_task_label = QLabel("未选择任务")
        self.current_task_label.setFont(Fonts.caption())
        self.current_task_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self.current_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.current_task_label)

        # 计时器数字（绝对主视觉）
        self.time_label = QLabel(self.timer.get_formatted_time())
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(Fonts.timer_extra_bold(88))  # 增大10% + 超粗字重
        self.time_label.setStyleSheet(f"color: {Colors.TIMER_DISPLAY};")  # 深蓝近黑
        timer_layout.addWidget(self.time_label)

        # 状态标签（降级为辅助信息）
        self.status_label = QLabel("就绪")
        self.status_label.setFont(Fonts.body(14))  # 缩小字体
        self.status_label.setStyleSheet(f"color: {Colors.TIMER_STATUS};")  # 灰蓝色
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.status_label)

        # 控制按钮（主次分明）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.XL)  # 增加按钮间距，避免挤在一起
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_btn = QPushButton("开始")
        self.start_btn.setFixedHeight(56)
        self.start_btn.setMinimumWidth(140)
        apply_primary_button_style(self.start_btn)  # 实心、品牌色 - 主按钮
        # 使用一个统一的槽函数处理开始/继续
        self.start_btn.clicked.connect(self.on_start_or_resume_clicked)
        button_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setFixedHeight(56)
        self.pause_btn.setMinimumWidth(120)  # 略窄于开始按钮
        apply_secondary_button_style(self.pause_btn)  # 描边按钮 - 次级
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_pomodoro)
        button_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedHeight(56)
        self.stop_btn.setMinimumWidth(120)  # 略窄于开始按钮
        apply_secondary_button_style(self.stop_btn)  # 描边按钮 - 次级
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_pomodoro)
        button_layout.addWidget(self.stop_btn)

        timer_layout.addLayout(button_layout)

        # 任务选择区域
        task_selector_layout = QHBoxLayout()
        task_selector_layout.setSpacing(Spacing.LG)

        task_label = QLabel("当前任务:")
        task_label.setFont(Fonts.body())
        task_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        task_selector_layout.addWidget(task_label)

        self.task_combo = QComboBox()
        self.task_combo.setMinimumHeight(44)
        self.task_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_combo_box_style(self.task_combo)
        self.task_combo.currentIndexChanged.connect(self.on_task_changed)
        task_selector_layout.addWidget(self.task_combo)

        timer_layout.addLayout(task_selector_layout)

        main_layout.addWidget(timer_card)

    def connect_signals(self):
        """连接信号和槽"""
        self.timer.set_tick_callback(self.on_timer_tick)
        self.timer.set_state_change_callback(self.on_timer_state_changed)
        # 注意：complete_callback 由 ResponsiveWindow 统一管理，避免被覆盖

    def refresh(self):
        """刷新界面"""
        self.refresh_task_list()
        self.update_ui_state()

    def refresh_task_list(self):
        """刷新任务列表"""
        current_task_id = self.get_selected_task_id()

        self.task_combo.clear()
        self.task_combo.addItem("(无任务)", None)

        for quadrant in range(4):
            tasks = self.task_manager.get_tasks_by_quadrant(
                quadrant,
                include_completed=False
            )

            if tasks:
                quadrant_name = TaskManager.get_quadrant_name(quadrant)
                self.task_combo.addItem(f"── {quadrant_name} ──", None)
                self.task_combo.model().item(self.task_combo.count() - 1).setEnabled(False)

                for task in tasks:
                    self.task_combo.addItem(task.description, task.id)

        if current_task_id:
            self.select_task_by_id(current_task_id)

    def get_selected_task_id(self) -> Optional[int]:
        """获取当前选择的任务ID"""
        return self.task_combo.currentData()

    def select_task_by_id(self, task_id: int):
        """通过ID选择任务"""
        for i in range(self.task_combo.count()):
            if self.task_combo.itemData(i) == task_id:
                self.task_combo.setCurrentIndex(i)
                break

    def on_task_changed(self, index: int):
        """任务选择变化"""
        task_id = self.get_selected_task_id()
        self.timer.set_task(task_id)

        # 更新当前任务显示
        if task_id:
            task = self.task_manager.get_task(task_id)
            if task:
                self.current_task_label.setText(task.description)
        else:
            self.current_task_label.setText("未选择任务")

    def on_timer_tick(self, remaining: int, total: int):
        """计时器tick回调"""
        self.time_label.setText(self.timer.get_formatted_time())

        # 保持主视觉统一：始终使用深色，仅在状态标签上显示颜色
        # 不再改变倒计时数字颜色，保持视觉稳定性
        pass

    def on_timer_state_changed(self, state: TimerState):
        """计时器状态变化回调"""
        self.update_ui_state()

        # 更新状态标签 - 使用更温和的颜色系统
        state_colors = {
            TimerState.READY: Colors.TIMER_STATUS,      # 灰蓝
            TimerState.RUNNING: Colors.SUCCESS,         # 绿色（运行中）
            TimerState.PAUSED: Colors.WARNING,          # 橙色（暂停）
            TimerState.COMPLETED: Colors.PRIMARY,       # 蓝色（完成）
            TimerState.ABANDONED: Colors.TEXT_TERTIARY  # 浅灰（废弃）
        }

        color = state_colors.get(state, Colors.TIMER_STATUS)
        self.status_label.setText(state.value)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 500;")  # 减轻字重

    def on_timer_complete(self):
        """计时器完成回调 - 由 ResponsiveWindow 统一调用"""
        completed_task_id = None
        session_start_time = self.current_session_start_time

        if self.current_session_id is not None:
            end_time = datetime.now().isoformat()
            self.storage.end_pomodoro_session(
                self.current_session_id,
                end_time,
                TimerStatus.COMPLETED
            )

            task_id = self.timer.current_task_id
            if task_id:
                completed_task_id = task_id
                self.task_manager.increment_task_pomodoros(task_id)

        # 自动添加日志
        if completed_task_id and session_start_time:
            self._add_completion_log(completed_task_id, session_start_time)

        self.current_session_id = None
        self.current_session_start_time = None

        # 重置计时器为 READY 状态，方便立即开始下一个番茄钟
        self.timer.reset()
        self.time_label.setText(self.timer.get_formatted_time())
        self.update_ui_state()

    def _add_completion_log(self, task_id: int, start_time: str):
        """
        添加番茄钟完成日志

        Args:
            task_id: 任务ID
            start_time: 开始时间
        """
        try:
            task = self.task_manager.get_task(task_id)
            if not task:
                return

            # 获取任务类型（象限）
            quadrant_name = TaskManager.get_quadrant_name(task.quadrant)

            # 格式化开始时间
            start_dt = datetime.fromisoformat(start_time)
            start_time_str = start_dt.strftime("%H:%M")

            # 构建日志内容
            log_content = f"✅ 完成番茄钟 - [{quadrant_name}] {task.description} (开始时间: {start_time_str})"

            self.logger.create_log(log_content, task_id=task_id)

            # 发送信号通知主窗口刷新历史视图
            self.log_added.emit()

        except Exception as e:
            pass  # 静默失败，不影响主流程

    def on_start_or_resume_clicked(self):
        """处理开始/继续按钮点击"""
        state = self.timer.state

        if state == TimerState.PAUSED:
            # 从暂停恢复
            self.resume_pomodoro()
        else:
            # 开始新的番茄钟
            self.start_pomodoro()

    def start_pomodoro(self):
        """开始新的番茄钟"""
        try:
            start_time = datetime.now().isoformat()
            task_id = self.get_selected_task_id()

            session_id = self.storage.create_pomodoro_session(task_id, start_time)

            if self.timer.start():
                self.current_session_id = session_id
                self.current_session_start_time = start_time  # 保存开始时间
                self.update_ui_state()
            else:
                end_time = datetime.now().isoformat()
                self.storage.end_pomodoro_session(session_id, end_time, TimerStatus.ABANDONED)
                QMessageBox.warning(self, "警告", "计时器启动失败")
                self.current_session_id = None
                self.current_session_start_time = None
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法开始番茄钟: {str(e)}")
            self.current_session_id = None
            self.current_session_start_time = None

    def resume_pomodoro(self):
        """恢复暂停的番茄钟"""
        if self.current_session_id is None:
            QMessageBox.warning(self, "警告", "没有可以恢复的番茄钟")
            return

        # 只恢复计时，不创建新会话
        if self.timer.resume():
            self.update_ui_state()
        else:
            QMessageBox.warning(self, "警告", "无法恢复番茄钟")

    def pause_pomodoro(self):
        """暂停番茄钟"""
        if self.timer.pause():
            self.update_ui_state()

    def stop_pomodoro(self):
        """停止/废弃番茄钟"""
        reply = QMessageBox.question(
            self,
            "确认停止",
            "确定要停止当前番茄钟吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.current_session_id is not None:
                end_time = datetime.now().isoformat()
                self.storage.end_pomodoro_session(
                    self.current_session_id,
                    end_time,
                    TimerStatus.ABANDONED
                )
                self.current_session_id = None
                self.current_session_start_time = None

            self.timer.stop(abandon=True)
            # 重置计时器，显示完整的番茄钟时长
            self.timer.reset()
            self.time_label.setText(self.timer.get_formatted_time())
            self.update_ui_state()

    def force_complete_pomodoro(self):
        """强制完成番茄钟"""
        reply = QMessageBox.question(
            self,
            "确认强制完成",
            "确定要强制完成当前番茄钟吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.current_session_id is not None:
                end_time = datetime.now().isoformat()
                self.storage.end_pomodoro_session(
                    self.current_session_id,
                    end_time,
                    TimerStatus.FORCE_COMPLETED
                )

                task_id = self.timer.current_task_id
                if task_id:
                    self.task_manager.increment_task_pomodoros(task_id)
                    # 也添加日志
                    if self.current_session_start_time:
                        self._add_completion_log(task_id, self.current_session_start_time)

                self.current_session_id = None
                self.current_session_start_time = None

            self.timer.force_complete()

    def update_ui_state(self):
        """更新UI状态"""
        state = self.timer.state

        # 更新按钮状态和样式
        if state == TimerState.READY:
            self.start_btn.setText("开始")
            self.start_btn.setEnabled(True)
            apply_primary_button_style(self.start_btn)

            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.task_combo.setEnabled(True)

            self.status_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")

        elif state == TimerState.RUNNING:
            self.start_btn.setEnabled(False)

            self.pause_btn.setText("暂停")
            self.pause_btn.setEnabled(True)
            apply_primary_button_style(self.pause_btn)

            self.stop_btn.setEnabled(True)
            self.task_combo.setEnabled(False)

            self.status_label.setStyleSheet(f"color: {Colors.SUCCESS};")

        elif state == TimerState.PAUSED:
            self.start_btn.setText("继续")
            self.start_btn.setEnabled(True)
            apply_primary_button_style(self.start_btn)

            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.task_combo.setEnabled(False)

            self.status_label.setStyleSheet(f"color: {Colors.WARNING};")

        elif state == TimerState.COMPLETED:
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.task_combo.setEnabled(True)

            self.status_label.setStyleSheet(f"color: {Colors.PRIMARY};")

        elif state == TimerState.ABANDONED:
            self.start_btn.setText("开始")
            self.start_btn.setEnabled(True)
            apply_primary_button_style(self.start_btn)

            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.task_combo.setEnabled(True)

            self.status_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY};")

    def focus_log_input(self):
        """聚焦到日志输入框（已移除，保留接口兼容）"""
        pass
