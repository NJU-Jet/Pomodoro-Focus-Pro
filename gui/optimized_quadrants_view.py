"""优化后的四象限视图 - 使用产品级对话框"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QListWidget, QListWidgetItem, QPushButton, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from typing import Optional
from core.task_manager import TaskManager, Task
from core.pomodoro_timer import PomodoroTimer
from gui.styles import Colors, Fonts, Spacing
from gui.create_task_dialog import CreateTaskDialog
from gui.edit_task_dialog import EditTaskDialog


class OptimizedQuadrantCard(QFrame):
    """优化的象限卡片"""

    task_selected = pyqtSignal(int)
    task_updated = pyqtSignal()

    def __init__(self, quadrant: int, task_manager: TaskManager,
                 timer: PomodoroTimer, parent=None):
        super().__init__(parent)
        self.quadrant = quadrant
        self.task_manager = task_manager
        self.timer = timer

        self.quadrant_name = TaskManager.get_quadrant_name(quadrant)
        self.quadrant_color = self._get_quadrant_color(quadrant)

        self.init_ui()
        self.refresh()

    def _get_quadrant_color(self, quadrant: int) -> str:
        """获取象限颜色"""
        colors = {
            0: Colors.QUADRANT_0,
            1: Colors.QUADRANT_1,
            2: Colors.QUADRANT_2,
            3: Colors.QUADRANT_3
        }
        return colors.get(quadrant, Colors.TEXT_TERTIARY)

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 卡片容器
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border-radius: {Spacing.RADIUS_CARD}px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        card_layout.setSpacing(Spacing.MD)

        # 标题栏
        title_bar = QHBoxLayout()
        title_bar.setSpacing(Spacing.MD)

        # 色条
        color_bar = QLabel()
        color_bar.setFixedWidth(4)
        color_bar.setFixedHeight(20)
        color_bar.setStyleSheet(f"background-color: {self.quadrant_color}; border-radius: 2px;")
        title_bar.addWidget(color_bar)

        # 标题
        title_label = QLabel(self.quadrant_name)
        title_label.setFont(Fonts.title())
        title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        title_bar.addWidget(title_label)

        title_bar.addStretch()

        # 任务数量
        self.count_label = QLabel("0")
        self.count_label.setFont(Fonts.caption())
        self.count_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        title_bar.addWidget(self.count_label)

        card_layout.addLayout(title_bar)

        # 任务列表
        self.task_list = QListWidget()
        self.task_list.setMinimumHeight(180)
        self.task_list.setAlternatingRowColors(True)
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)
        self.task_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.task_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}

            QListWidget::item {{
                border-radius: {Spacing.RADIUS_SMALL}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
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
        """)
        card_layout.addWidget(self.task_list)

        # 添加按钮（使用产品级样式）
        add_btn = QPushButton("+ 创建任务")
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.PRIMARY};
                border: 1px dashed {Colors.PRIMARY};
                border-radius: {Spacing.RADIUS_BUTTON}px;
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: {Colors.BG_SELECTED};
                border-color: {Colors.PRIMARY_HOVER};
            }}
        """)
        add_btn.clicked.connect(self.create_task)
        card_layout.addWidget(add_btn)

        main_layout.addWidget(card)

    def refresh(self):
        """刷新任务列表"""
        self.task_list.clear()

        tasks = self.task_manager.get_tasks_by_quadrant(
            self.quadrant,
            include_completed=False
        )

        for task in tasks:
            # 解析创建时间
            from datetime import datetime
            from PyQt6.QtGui import QFontMetrics, QFont
            from PyQt6.QtCore import QSize
            try:
                created_date = datetime.fromisoformat(task.created_date)
                created_str = created_date.strftime("%m-%d %H:%M")
            except:
                created_str = "未知时间"

            # 构建显示文本 - 包含详细信息
            display_text = f"{task.description}\n"
            display_text += f"  📅 创建时间: {created_str}\n"
            display_text += f"  🍅 已用番茄钟: {task.actual_pomodoros} / 预计: {task.estimated_pomodoros}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, task.id)

            # 设置项目大小以适应多行文本（增加到4行以确保完整显示）
            font = self.task_list.font()
            fm = QFontMetrics(font)
            line_height = fm.lineSpacing()
            # 增加高度到5行，确保番茄钟信息完整显示
            item.setSizeHint(QSize(500, line_height * 5 + 15))

            # 当前任务高亮
            if self.timer.current_task_id == task.id and self.timer.is_running:
                item.setBackground(QBrush(QColor(Colors.BG_SELECTED)))

            self.task_list.addItem(item)

        # 更新任务数量
        self.count_label.setText(str(len(tasks)))

    def create_task(self):
        """创建新任务 - 使用产品级对话框"""
        dialog = CreateTaskDialog(quadrant=self.quadrant, parent=self)

        # 循环直到用户取消或输入有效
        while True:
            result = dialog.exec()

            if result != QDialog.DialogCode.Accepted:
                # 用户取消
                return

            # 验证输入
            valid, error_msg = dialog.validate()
            if not valid:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "输入验证失败", error_msg)
                # 重新显示同一个对话框，保留用户输入
                continue

            # 获取数据并创建任务
            task_data = dialog.get_task_data()
            try:
                self.task_manager.create_task(
                    task_data['description'],
                    task_data['quadrant'],
                    task_data['estimated_pomodoros']
                )
                # 刷新当前象限
                self.refresh()
                # 发送信号通知主窗口刷新所有视图
                self.task_updated.emit()
                return
            except ValueError as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "创建失败", str(e))
                # 出错后退出，避免无限循环
                return

    def edit_task(self, task_id: int):
        """编辑任务 - 使用编辑对话框"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return

        dialog = EditTaskDialog(task, parent=self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # 验证输入
            valid, error_msg = dialog.validate()
            if not valid:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "错误", error_msg)
                return

            # 获取数据并更新任务
            task_data = dialog.get_task_data()
            try:
                self.task_manager.update_task(
                    task_id,
                    description=task_data['description'],
                    estimated_pomodoros=task_data['estimated_pomodoros']
                )
                self.refresh()
                self.task_updated.emit()
            except ValueError as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "错误", str(e))

    def complete_task(self, task_id: int):
        """完成任务"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认完成",
            "确定要标记此任务为完成吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.task_manager.complete_task(task_id)
                self.refresh()
                self.task_updated.emit()
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))

    def delete_task(self, task_id: int):
        """删除任务"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除此任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.task_manager.delete_task(task_id)
                self.refresh()
                self.task_updated.emit()
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))

    def move_task_to_quadrant(self, task_id: int, new_quadrant: int):
        """移动任务到其他象限"""
        try:
            self.task_manager.move_task_to_quadrant(task_id, new_quadrant)
            self.refresh()
            self.task_updated.emit()
        except ValueError as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", str(e))

    def select_task_for_timer(self, task_id: int):
        """选择任务用于番茄钟"""
        self.task_selected.emit(task_id)

    def on_item_double_clicked(self, item: QListWidgetItem):
        """双击任务项"""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        self.select_task_for_timer(task_id)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.task_list.itemAt(position)
        if not item:
            return

        task_id = item.data(Qt.ItemDataRole.UserRole)

        from PyQt6.QtWidgets import QMenu

        menu = QMenu(self)
        menu.setStyleSheet(f"""
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

        select_action = menu.addAction("选择此任务")
        select_action.triggered.connect(lambda: self.select_task_for_timer(task_id))

        menu.addSeparator()

        edit_action = menu.addAction("编辑")
        edit_action.triggered.connect(lambda: self.edit_task(task_id))

        move_menu = menu.addMenu("移动到...")
        move_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SMALL}px;
            }}
        """)
        for q in range(4):
            if q != self.quadrant:
                action = move_menu.addAction(TaskManager.get_quadrant_name(q))
                action.triggered.connect(lambda checked, q=q: self.move_task_to_quadrant(task_id, q))

        menu.addSeparator()

        complete_action = menu.addAction("标记完成")
        complete_action.triggered.connect(lambda: self.complete_task(task_id))

        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.delete_task(task_id))

        menu.exec(self.task_list.mapToGlobal(position))


class OptimizedQuadrantsView(QWidget):
    """优化的四象限视图"""

    task_updated = pyqtSignal()
    task_selected = pyqtSignal(int)

    def __init__(self, task_manager: TaskManager, timer: PomodoroTimer):
        super().__init__()
        self.task_manager = task_manager
        self.timer = timer

        self.init_ui()
        self.refresh()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(Spacing.LG)

        # 标签页
        from PyQt6.QtWidgets import QTabWidget

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

        self.quadrant_cards = []
        for q in range(4):
            card = OptimizedQuadrantCard(q, self.task_manager, self.timer, self.tab_widget)
            card.task_selected.connect(self.on_task_selected)
            card.task_updated.connect(self.on_task_updated_inner)
            self.tab_widget.addTab(card, TaskManager.get_quadrant_name(q))
            self.quadrant_cards.append(card)

        main_layout.addWidget(self.tab_widget)

    def refresh(self):
        """刷新所有象限的任务"""
        for card in self.quadrant_cards:
            card.refresh()

    def on_task_selected(self, task_id: int):
        """处理任务选择信号"""
        self.task_selected.emit(task_id)

    def on_task_updated_inner(self):
        """处理内部任务更新信号"""
        self.task_updated.emit()
