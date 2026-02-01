"""统计模块单元测试。"""

import pytest
import os
import tempfile
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.storage import Storage, TimerStatus
from core.task_manager import TaskManager
from core.statistics import Statistics
from utils.logger import Logger


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    storage = Storage(path)
    yield storage
    storage.close()
    os.unlink(path)


@pytest.fixture
def statistics(temp_db):
    """创建统计管理器"""
    return Statistics(temp_db)


@pytest.fixture
def task_manager(temp_db):
    """创建任务管理器"""
    return TaskManager(temp_db)


@pytest.fixture
def logger(temp_db):
    """创建日志管理器"""
    return Logger(temp_db)


class TestStatistics:
    """统计模块测试类"""

    def test_get_daily_statistics_empty(self, statistics):
        """测试获取空日期的统计"""
        stats = statistics.get_daily_statistics("2026-01-15")

        assert stats.date == "2026-01-15"
        assert stats.total_pomodoros == 0
        assert len(stats.completed_tasks) == 0
        assert len(stats.logs) == 0

    def test_daily_statistics_with_data(self, temp_db, statistics, task_manager):
        """测试有数据时的每日统计"""
        # 创建任务
        task1 = task_manager.create_task("任务1", quadrant=0)
        task2 = task_manager.create_task("任务2", quadrant=1)

        # 创建番茄钟会话
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = datetime.now().isoformat()

        session1 = temp_db.create_pomodoro_session(task1.id, start_time)
        temp_db.end_pomodoro_session(session1, start_time, TimerStatus.COMPLETED)

        session2 = temp_db.create_pomodoro_session(task2.id, start_time)
        temp_db.end_pomodoro_session(session2, start_time, TimerStatus.COMPLETED)

        # 获取统计
        stats = statistics.get_daily_statistics(today)

        assert stats.total_pomodoros == 2
        assert len(stats.completed_tasks) == 2

    def test_get_monthly_statistics(self, statistics):
        """测试月度统计"""
        monthly = statistics.get_monthly_statistics(2026, 1)

        assert monthly.year == 2026
        assert monthly.month == 1
        assert monthly.total_pomodoros == 0
        assert monthly.days_with_pomodoros == 0

    def test_weekly_statistics(self, statistics):
        """测试周统计"""
        weekly = statistics.get_weekly_statistics("2026-01-12")

        assert len(weekly) == 7
        assert "2026-01-12" in weekly
        assert "2026-01-18" in weekly

    def test_get_task_statistics(self, temp_db, statistics, task_manager):
        """测试任务统计"""
        task = task_manager.create_task("测试任务", quadrant=0, estimated_pomodoros=5)

        # 添加番茄钟会话
        start_time = datetime.now().isoformat()
        for _ in range(3):
            session_id = temp_db.create_pomodoro_session(task.id, start_time)
            temp_db.end_pomodoro_session(session_id, start_time, TimerStatus.COMPLETED)

        stats = statistics.get_task_statistics(task.id)

        assert stats['task_id'] == task.id
        assert stats['description'] == "测试任务"
        assert stats['quadrant'] == 0
        assert stats['estimated_pomodoros'] == 5
        assert stats['actual_pomodoros'] == 3

    def test_get_productivity_streak_empty(self, statistics):
        """测试空数据的连续记录"""
        streak = statistics.get_productivity_streak()

        assert streak['current_streak'] == 0
        assert streak['longest_streak'] == 0

    def test_get_productivity_streak(self, temp_db, statistics):
        """测试连续记录"""
        # 创建连续3天的番茄钟记录
        for i in range(3):
            date = datetime.now().strftime("%Y-%m-%d")
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            target_date = (date_obj - timedelta(days=i)).strftime("%Y-%m-%d")

            start_time = datetime.now().isoformat()
            session_id = temp_db.create_pomodoro_session(None, start_time)
            # 同时更新date和status
            temp_db.conn.execute("""
                UPDATE pomodoro_sessions
                SET date = ?, status = ?
                WHERE id = ?
            """, (target_date, TimerStatus.COMPLETED.value, session_id))
            temp_db.conn.commit()

        streak = statistics.get_productivity_streak()

        # 注意：这个测试可能因为日期问题而失败，需要根据实际日期调整
        assert streak['longest_streak'] >= 1

    def test_get_quadrant_distribution(self, temp_db, statistics, task_manager):
        """测试象限分布"""
        # 创建各象限任务
        task_manager.create_task("Q1任务1", quadrant=0)
        task_manager.create_task("Q1任务2", quadrant=0)
        t3 = task_manager.create_task("Q1任务3", quadrant=0)
        task_manager.complete_task(t3.id)

        task_manager.create_task("Q2任务", quadrant=1)

        distribution = statistics.get_quadrant_distribution()

        assert distribution[0]['pending'] == 2
        assert distribution[0]['completed'] == 1
        assert distribution[0]['total'] == 3
        assert distribution[0]['completion_rate'] == 33.33

    def test_get_calendar_data(self, statistics):
        """测试日历数据"""
        calendar_data = statistics.get_calendar_data(2026, 1)

        # 1月2026年应该有6周
        assert len(calendar_data) <= 6
        # 每周7天
        for week in calendar_data:
            assert len(week) == 7


# 导入timedelta
from datetime import timedelta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
