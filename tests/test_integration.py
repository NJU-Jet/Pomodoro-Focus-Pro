"""集成测试 - 测试完整的工作流程。"""

import pytest
import os
import tempfile
import time
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.storage import Storage, TimerStatus
from core.task_manager import TaskManager
from core.pomodoro_timer import PomodoroTimer
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


class TestIntegration:
    """集成测试类"""

    def test_complete_workflow(self, temp_db):
        """测试完整工作流程：创建任务 -> 番茄钟 -> 完成 -> 统计"""
        # 初始化
        task_manager = TaskManager(temp_db)
        timer = PomodoroTimer()
        statistics = Statistics(temp_db)
        logger = Logger(temp_db)

        # 1. 创建任务
        task = task_manager.create_task(
            description="完成项目文档",
            quadrant=0,  # 重要紧急
            estimated_pomodoros=3
        )

        assert task.id > 0
        assert task.quadrant == 0

        # 2. 选择任务并开始番茄钟
        timer.set_task(task.id)
        timer.set_duration(1)  # 1秒用于快速测试

        start_time = datetime.now().isoformat()
        session_id = temp_db.create_pomodoro_session(task.id, start_time)

        timer.start()
        assert timer.is_running

        # 3. 等待完成
        time.sleep(2)

        # 4. 完成会话
        end_time = datetime.now().isoformat()
        temp_db.end_pomodoro_session(session_id, end_time, TimerStatus.COMPLETED)

        # 5. 增加任务番茄钟计数
        task_manager.increment_task_pomodoros(task.id)

        # 6. 添加日志
        logger.create_log("完成了第一个番茄钟，进度不错", task.id)

        # 7. 验证统计
        today = datetime.now().strftime("%Y-%m-%d")
        daily_stats = statistics.get_daily_statistics(today)

        assert daily_stats.total_pomodoros == 1
        assert len(daily_stats.completed_tasks) == 1
        assert daily_stats.completed_tasks[0]['id'] == task.id
        assert len(daily_stats.logs) == 1

        # 8. 完成任务
        task_manager.complete_task(task.id)

        completed_tasks = task_manager.get_completed_tasks()
        assert len(completed_tasks) == 1
        assert completed_tasks[0].id == task.id

        # 9. 验证任务统计
        task_stats = statistics.get_task_statistics(task.id)
        assert task_stats['actual_pomodoros'] == 1
        assert task_stats['is_completed'] is True

    def test_multiple_pomodoros_same_task(self, temp_db):
        """测试同一任务多个番茄钟"""
        task_manager = TaskManager(temp_db)
        timer = PomodoroTimer()

        task = task_manager.create_task("多番茄钟任务", quadrant=1)

        # 完成3个番茄钟
        for i in range(3):
            timer.set_task(task.id)
            timer.set_duration(1)

            start_time = datetime.now().isoformat()
            session_id = temp_db.create_pomodoro_session(task.id, start_time)

            timer.start()
            time.sleep(2)

            end_time = datetime.now().isoformat()
            temp_db.end_pomodoro_session(session_id, end_time, TimerStatus.COMPLETED)
            task_manager.increment_task_pomodoros(task.id)
            timer.reset()

        # 验证
        updated_task = task_manager.get_task(task.id)
        assert updated_task.actual_pomodoros == 3

    def test_abandoned_pomodoro_not_counted(self, temp_db):
        """测试废弃的番茄钟不被计数"""
        task_manager = TaskManager(temp_db)
        timer = PomodoroTimer()

        task = task_manager.create_task("测试任务", quadrant=0)

        # 启动但废弃
        timer.set_task(task.id)
        timer.set_duration(1)

        start_time = datetime.now().isoformat()
        session_id = temp_db.create_pomodoro_session(task.id, start_time)

        timer.start()
        timer.stop(abandon=True)

        end_time = datetime.now().isoformat()
        temp_db.end_pomodoro_session(session_id, end_time, TimerStatus.ABANDONED)

        # 验证不被计数
        today = datetime.now().strftime("%Y-%m-%d")
        daily_count = temp_db.get_daily_pomodoro_count(today)

        assert daily_count == 0

    def test_task_quadrant_management(self, temp_db):
        """测试象限管理流程"""
        task_manager = TaskManager(temp_db)

        # 创建各象限任务
        q1_task = task_manager.create_task("Q1任务", quadrant=0)
        q2_task = task_manager.create_task("Q2任务", quadrant=1)
        q3_task = task_manager.create_task("Q3任务", quadrant=2)
        q4_task = task_manager.create_task("Q4任务", quadrant=3)

        # 移动任务
        task_manager.move_task_to_quadrant(q4_task.id, new_quadrant=1)

        moved_task = task_manager.get_task(q4_task.id)
        assert moved_task.quadrant == 1

        # 完成任务
        task_manager.complete_task(q1_task.id)
        task_manager.complete_task(q2_task.id)

        # 验证统计
        summary = task_manager.get_quadrant_summary()

        assert summary[0]['completed'] == 1
        assert summary[1]['completed'] == 1
        assert summary[2]['pending'] == 1
        assert summary[3]['pending'] == 0

    def test_log_with_and_without_task(self, temp_db):
        """测试带任务和不带任务的日志"""
        logger = Logger(temp_db)
        task_manager = TaskManager(temp_db)

        task = task_manager.create_task("有日志的任务", quadrant=0)

        # 关联任务的日志
        log1 = logger.create_log("关联任务的日志", task.id)
        assert log1.task_id == task.id

        # 不关联任务的日志
        log2 = logger.create_log("独立日志")
        assert log2.task_id is None

        # 验证检索
        task_logs = logger.get_logs_by_task(task.id)
        assert len(task_logs) == 1
        assert task_logs[0].content == "关联任务的日志"

    def test_quadrant_distribution_statistics(self, temp_db):
        """测试象限分布统计"""
        task_manager = TaskManager(temp_db)
        statistics = Statistics(temp_db)

        # 创建任务
        for i in range(5):
            task_manager.create_task(f"Q1任务{i}", quadrant=0)

        for i in range(3):
            task = task_manager.create_task(f"Q2任务{i}", quadrant=1)
            if i < 2:
                task_manager.complete_task(task.id)

        distribution = statistics.get_quadrant_distribution()

        assert distribution[0]['total'] == 5
        assert distribution[0]['completed'] == 0
        assert distribution[1]['total'] == 3
        assert distribution[1]['completed'] == 2

    def test_calendar_history_view(self, temp_db):
        """测试日历历史数据"""
        task_manager = TaskManager(temp_db)
        statistics = Statistics(temp_db)

        task = task_manager.create_task("历史测试", quadrant=0)

        # 创建历史记录
        date = datetime.now().strftime("%Y-%m-%d")
        date_obj = datetime.strptime(date, "%Y-%m-%d")

        # 为过去3天创建记录
        for i in range(3):
            past_date = (date_obj - timedelta(days=i)).strftime("%Y-%m-%d")
            start_time = datetime.now().isoformat()

            for j in range(2):  # 每天2个番茄钟
                session_id = temp_db.create_pomodoro_session(task.id, start_time)
                # 同时更新date和status
                temp_db.conn.execute("""
                    UPDATE pomodoro_sessions
                    SET date = ?, status = ?
                    WHERE id = ?
                """, (past_date, TimerStatus.COMPLETED.value, session_id))
                temp_db.conn.commit()

        # 验证月度统计
        today = datetime.now()
        monthly = statistics.get_monthly_statistics(today.year, today.month)

        assert monthly.total_pomodoros >= 6
        assert monthly.days_with_pomodoros >= 1

    def test_export_and_import(self, temp_db):
        """测试数据导出"""
        task_manager = TaskManager(temp_db)
        logger = Logger(temp_db)

        # 创建测试数据
        task = task_manager.create_task("导出测试", quadrant=0)
        logger.create_log("测试日志", task.id)

        # 导出
        export_path = tempfile.mktemp(suffix='.json')
        success = temp_db.export_to_json(export_path)

        assert success is True
        assert os.path.exists(export_path)

        # 验证JSON内容
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'tasks' in data
        assert 'logs' in data
        assert len(data['tasks']) == 1
        assert len(data['logs']) == 1

        # 清理
        os.unlink(export_path)


# 导入timedelta
from datetime import timedelta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
