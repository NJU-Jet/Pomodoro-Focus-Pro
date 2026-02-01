"""番茄钟计时器 - 倒计时逻辑和状态管理。"""

import time
import threading
from enum import Enum
from typing import Optional, Callable
from datetime import datetime


class TimerState(Enum):
    """计时器状态枚举"""
    READY = "就绪"
    RUNNING = "专注中"
    PAUSED = "已暂停"
    COMPLETED = "已完成"
    ABANDONED = "已废弃"


class PomodoroTimer:
    """番茄钟计时器"""

    DEFAULT_DURATION = 30 * 60  # 默认30分钟（秒）

    def __init__(self):
        """初始化计时器"""
        self._state = TimerState.READY
        self._duration = self.DEFAULT_DURATION
        self._remaining_seconds = self.DEFAULT_DURATION
        self._current_task_id: Optional[int] = None
        self._start_time: Optional[str] = None
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

        # 回调函数
        self._on_tick: Optional[Callable[[int, int], None]] = None  # (剩余秒数, 总秒数)
        self._on_complete: Optional[Callable[[], None]] = None
        self._on_state_change: Optional[Callable[[TimerState], None]] = None

    @property
    def state(self) -> TimerState:
        """获取当前状态"""
        return self._state

    @property
    def remaining_seconds(self) -> int:
        """获取剩余秒数"""
        return self._remaining_seconds

    @property
    def duration(self) -> int:
        """获取总时长"""
        return self._duration

    @property
    def current_task_id(self) -> Optional[int]:
        """获取当前任务ID"""
        return self._current_task_id

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._state == TimerState.RUNNING

    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._state == TimerState.PAUSED

    def set_duration(self, seconds: int):
        """
        设置计时器时长

        Args:
            seconds: 时长（秒）
        """
        if self._state == TimerState.RUNNING:
            raise RuntimeError("计时器运行时不能修改时长")

        self._duration = max(1, seconds)
        if self._state == TimerState.READY:
            self._remaining_seconds = self._duration

    def set_task(self, task_id: Optional[int]):
        """
        设置关联任务

        Args:
            task_id: 任务ID，None表示无关联任务
        """
        if self._state == TimerState.RUNNING:
            raise RuntimeError("计时器运行时不能更换任务")

        self._current_task_id = task_id

    def set_tick_callback(self, callback: Callable[[int, int], None]):
        """
        设置计时更新回调

        Args:
            callback: 回调函数，参数为(剩余秒数, 总秒数)
        """
        self._on_tick = callback

    def set_complete_callback(self, callback: Callable[[], None]):
        """
        设置完成回调

        Args:
            callback: 回调函数
        """
        self._on_complete = callback

    def set_state_change_callback(self, callback: Callable[[TimerState], None]):
        """
        设置状态变化回调

        Args:
            callback: 回调函数，参数为新状态
        """
        self._on_state_change = callback

    def start(self) -> bool:
        """
        开始计时

        Returns:
            是否成功启动
        """
        if self._state == TimerState.RUNNING:
            return False

        if self._state == TimerState.PAUSED:
            # 从暂停恢复
            self._set_state(TimerState.RUNNING)
            self._pause_event.clear()
            return True

        # 新的计时
        if self._state not in (TimerState.READY, TimerState.COMPLETED, TimerState.ABANDONED):
            return False

        self._remaining_seconds = self._duration
        self._start_time = datetime.now().isoformat()
        self._stop_event.clear()
        self._pause_event.clear()

        self._set_state(TimerState.RUNNING)

        # 启动计时线程
        self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self._timer_thread.start()

        return True

    def pause(self) -> bool:
        """
        暂停计时

        Returns:
            是否成功暂停
        """
        if self._state != TimerState.RUNNING:
            return False

        self._set_state(TimerState.PAUSED)
        self._pause_event.set()
        return True

    def resume(self) -> bool:
        """
        恢复计时

        Returns:
            是否成功恢复
        """
        return self.start()  # 复用start逻辑

    def stop(self, abandon: bool = True) -> bool:
        """
        停止计时

        Args:
            abandon: 是否废弃（True=废弃，False=正常完成）

        Returns:
            是否成功停止
        """
        if self._state not in (TimerState.RUNNING, TimerState.PAUSED):
            return False

        # 停止计时线程
        self._stop_event.set()
        self._pause_event.clear()

        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=1.0)

        if abandon:
            self._set_state(TimerState.ABANDONED)
        else:
            self._set_state(TimerState.COMPLETED)
            if self._on_complete:
                self._on_complete()

        return True

    def force_complete(self) -> bool:
        """
        强制完成（用于意外打断后手动确认）

        Returns:
            是否成功
        """
        if self._state not in (TimerState.RUNNING, TimerState.PAUSED):
            return False

        # 停止计时线程
        self._stop_event.set()
        self._pause_event.clear()

        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=1.0)

        self._remaining_seconds = 0
        self._set_state(TimerState.COMPLETED)

        if self._on_complete:
            self._on_complete()

        return True

    def reset(self):
        """重置计时器到初始状态"""
        if self._state == TimerState.RUNNING:
            self.stop(abandon=True)

        self._remaining_seconds = self._duration
        self._start_time = None
        self._set_state(TimerState.READY)

    def get_formatted_time(self) -> str:
        """
        获取格式化的剩余时间

        Returns:
            MM:SS 格式的时间字符串
        """
        minutes = self._remaining_seconds // 60
        seconds = self._remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_progress_percentage(self) -> float:
        """
        获取进度百分比

        Returns:
            0-100之间的浮点数
        """
        if self._duration == 0:
            return 0.0
        elapsed = self._duration - self._remaining_seconds
        return (elapsed / self._duration) * 100

    def _run_timer(self):
        """计时器线程执行函数"""
        while not self._stop_event.is_set():
            # 检查暂停
            if self._pause_event.is_set():
                self._pause_event.wait()
                continue

            if self._remaining_seconds <= 0:
                # 计时完成
                break

            # 触发tick回调
            if self._on_tick:
                self._on_tick(self._remaining_seconds, self._duration)

            # 等待1秒
            self._stop_event.wait(1.0)
            self._remaining_seconds -= 1

        # 检查是否自然完成（未中途停止）
        if not self._stop_event.is_set() and self._remaining_seconds <= 0:
            self._remaining_seconds = 0
            self._set_state(TimerState.COMPLETED)

            if self._on_tick:
                self._on_tick(0, self._duration)

            if self._on_complete:
                self._on_complete()

    def _set_state(self, new_state: TimerState):
        """
        设置状态并触发回调

        Args:
            new_state: 新状态
        """
        if self._state != new_state:
            self._state = new_state
            if self._on_state_change:
                self._on_state_change(new_state)
