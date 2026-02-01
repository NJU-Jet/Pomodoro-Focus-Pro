"""番茄钟计时器单元测试。"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pomodoro_timer import PomodoroTimer, TimerState


class TestPomodoroTimer:
    """番茄钟计时器测试类"""

    def test_initial_state(self):
        """测试初始状态"""
        timer = PomodoroTimer()

        assert timer.state == TimerState.READY
        assert timer.remaining_seconds == PomodoroTimer.DEFAULT_DURATION
        assert timer.duration == PomodoroTimer.DEFAULT_DURATION
        assert timer.current_task_id is None
        assert not timer.is_running
        assert not timer.is_paused

    def test_set_duration(self):
        """测试设置时长"""
        timer = PomodoroTimer()
        timer.set_duration(600)  # 10分钟

        assert timer.duration == 600
        assert timer.remaining_seconds == 600

    def test_set_task(self):
        """测试设置任务"""
        timer = PomodoroTimer()
        timer.set_task(123)

        assert timer.current_task_id == 123

    def test_start_timer(self):
        """测试开始计时"""
        timer = PomodoroTimer()

        success = timer.start()

        assert success is True
        assert timer.state == TimerState.RUNNING
        assert timer.is_running

        timer.stop()

    def test_pause_and_resume(self):
        """测试暂停和恢复"""
        timer = PomodoroTimer()
        timer.start()

        # 暂停
        timer.pause()
        assert timer.state == TimerState.PAUSED
        assert timer.is_paused

        # 恢复
        timer.resume()
        assert timer.state == TimerState.RUNNING
        assert timer.is_running

        timer.stop()

    def test_stop_abandon(self):
        """测试停止（废弃）"""
        timer = PomodoroTimer()
        timer.start()

        timer.stop(abandon=True)

        assert timer.state == TimerState.ABANDONED
        assert not timer.is_running

    def test_stop_complete(self):
        """测试停止（完成）"""
        timer = PomodoroTimer()
        timer.start()

        completed_called = []

        def on_complete():
            completed_called.append(True)

        timer.set_complete_callback(on_complete)
        timer.stop(abandon=False)

        assert timer.state == TimerState.COMPLETED
        assert len(completed_called) == 1

    def test_force_complete(self):
        """测试强制完成"""
        timer = PomodoroTimer()
        timer.start()

        completed_called = []

        def on_complete():
            completed_called.append(True)

        timer.set_complete_callback(on_complete)
        timer.force_complete()

        assert timer.state == TimerState.COMPLETED
        assert timer.remaining_seconds == 0
        assert len(completed_called) == 1

    def test_reset(self):
        """测试重置"""
        timer = PomodoroTimer()
        timer.start()
        timer.pause()

        timer.reset()

        assert timer.state == TimerState.READY
        assert timer.remaining_seconds == timer.duration

    def test_formatted_time(self):
        """测试格式化时间"""
        timer = PomodoroTimer()
        timer.set_duration(3661)  # 61分1秒

        assert timer.get_formatted_time() == "61:01"

        timer._remaining_seconds = 125
        assert timer.get_formatted_time() == "02:05"

        timer._remaining_seconds = 5
        assert timer.get_formatted_time() == "00:05"

    def test_progress_percentage(self):
        """测试进度百分比"""
        timer = PomodoroTimer()
        timer.set_duration(100)

        timer._remaining_seconds = 100
        assert timer.get_progress_percentage() == 0.0

        timer._remaining_seconds = 50
        assert timer.get_progress_percentage() == 50.0

        timer._remaining_seconds = 0
        assert timer.get_progress_percentage() == 100.0

    def test_tick_callback(self):
        """测试tick回调"""
        timer = PomodoroTimer()

        tick_values = []

        def on_tick(remaining, total):
            tick_values.append((remaining, total))

        timer.set_tick_callback(on_tick)
        timer.set_duration(2)  # 2秒用于快速测试
        timer.start()

        time.sleep(2.5)  # 等待完成

        assert len(tick_values) > 0
        assert tick_values[0][1] == 2

    def test_state_change_callback(self):
        """测试状态变化回调"""
        timer = PomodoroTimer()

        states = []

        def on_state_change(state):
            states.append(state)

        timer.set_state_change_callback(on_state_change)
        timer.start()
        timer.pause()
        timer.stop()

        assert len(states) >= 3
        assert TimerState.RUNNING in states
        assert TimerState.PAUSED in states

    def test_timer_completion(self):
        """测试计时器自动完成"""
        timer = PomodoroTimer()

        completed_called = []

        def on_complete():
            completed_called.append(True)

        timer.set_complete_callback(on_complete)
        timer.set_duration(1)  # 1秒
        timer.start()

        time.sleep(2)

        assert timer.state == TimerState.COMPLETED
        assert len(completed_called) == 1
        assert timer.remaining_seconds == 0

    def test_double_start(self):
        """测试重复启动"""
        timer = PomodoroTimer()
        timer.start()

        # 再次启动应该失败
        success = timer.start()
        assert success is False

        timer.stop()

    def test_pause_when_not_running(self):
        """测试未运行时暂停"""
        timer = PomodoroTimer()

        success = timer.pause()
        assert success is False

    def test_change_task_while_running(self):
        """测试运行时更换任务"""
        timer = PomodoroTimer()
        timer.start()

        with pytest.raises(RuntimeError):
            timer.set_task(456)

        timer.stop()

    def test_change_duration_while_running(self):
        """测试运行时修改时长"""
        timer = PomodoroTimer()
        timer.start()

        with pytest.raises(RuntimeError):
            timer.set_duration(600)

        timer.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
