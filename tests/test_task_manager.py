"""任务管理器单元测试。"""

import pytest
import os
import tempfile
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.storage import Storage
from core.task_manager import TaskManager, Task


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
def task_manager(temp_db):
    """创建任务管理器"""
    return TaskManager(temp_db)


class TestTaskManager:
    """任务管理器测试类"""

    def test_create_task(self, task_manager):
        """测试创建任务"""
        task = task_manager.create_task(
            description="测试任务",
            quadrant=0,
            estimated_pomodoros=3
        )

        assert task is not None
        assert task.id > 0
        assert task.description == "测试任务"
        assert task.quadrant == 0
        assert task.estimated_pomodoros == 3
        assert task.actual_pomodoros == 0
        assert not task.is_completed

    def test_create_task_invalid_quadrant(self, task_manager):
        """测试无效象限"""
        with pytest.raises(ValueError):
            task_manager.create_task("测试", quadrant=5)

    def test_create_task_empty_description(self, task_manager):
        """测试空描述"""
        with pytest.raises(ValueError):
            task_manager.create_task("", quadrant=0)

        with pytest.raises(ValueError):
            task_manager.create_task("   ", quadrant=0)

    def test_get_task(self, task_manager):
        """测试获取任务"""
        created = task_manager.create_task("获取测试", quadrant=1)
        retrieved = task_manager.get_task(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.description == "获取测试"

    def test_get_nonexistent_task(self, task_manager):
        """测试获取不存在的任务"""
        task = task_manager.get_task(99999)
        assert task is None

    def test_get_tasks_by_quadrant(self, task_manager):
        """测试按象限获取任务"""
        task_manager.create_task("重要紧急", quadrant=0)
        task_manager.create_task("重要不紧急", quadrant=1)
        task_manager.create_task("紧急不重要", quadrant=2)
        task_manager.create_task("不重要不紧急", quadrant=3)

        q0_tasks = task_manager.get_tasks_by_quadrant(0)
        q1_tasks = task_manager.get_tasks_by_quadrant(1)

        assert len(q0_tasks) == 1
        assert q0_tasks[0].description == "重要紧急"
        assert len(q1_tasks) == 1
        assert q1_tasks[0].description == "重要不紧急"

    def test_update_task(self, task_manager):
        """测试更新任务"""
        task = task_manager.create_task("原描述", quadrant=0, estimated_pomodoros=2)

        success = task_manager.update_task(
            task.id,
            description="新描述",
            estimated_pomodoros=5
        )

        assert success is True

        updated = task_manager.get_task(task.id)
        assert updated.description == "新描述"
        assert updated.estimated_pomodoros == 5

    def test_update_completed_task(self, task_manager):
        """测试更新已完成的任务"""
        task = task_manager.create_task("测试", quadrant=0)
        task_manager.complete_task(task.id)

        with pytest.raises(ValueError):
            task_manager.update_task(task.id, description="新描述")

    def test_move_task_to_quadrant(self, task_manager):
        """测试移动任务到其他象限"""
        task = task_manager.create_task("移动测试", quadrant=0)

        success = task_manager.move_task_to_quadrant(task.id, new_quadrant=2)

        assert success is True

        moved = task_manager.get_task(task.id)
        assert moved.quadrant == 2

    def test_complete_task(self, task_manager):
        """测试完成任务"""
        task = task_manager.create_task("完成测试", quadrant=1)

        success = task_manager.complete_task(task.id)

        assert success is True

        completed = task_manager.get_task(task.id)
        assert completed.is_completed is True
        assert completed.completed_date is not None

    def test_get_completed_tasks(self, task_manager):
        """测试获取已完成任务"""
        t1 = task_manager.create_task("任务1", quadrant=0)
        t2 = task_manager.create_task("任务2", quadrant=1)

        task_manager.complete_task(t1.id)

        completed = task_manager.get_completed_tasks()

        assert len(completed) == 1
        assert completed[0].id == t1.id

    def test_delete_task(self, task_manager):
        """测试删除任务"""
        task = task_manager.create_task("删除测试", quadrant=0)

        success = task_manager.delete_task(task.id)

        assert success is True

        deleted = task_manager.get_task(task.id)
        assert deleted is None

    def test_increment_task_pomodoros(self, task_manager):
        """测试增加番茄钟计数"""
        task = task_manager.create_task("番茄钟测试", quadrant=0)

        task_manager.increment_task_pomodoros(task.id)
        task_manager.increment_task_pomodoros(task.id)

        updated = task_manager.get_task(task.id)
        assert updated.actual_pomodoros == 2

    def test_get_task_duration_days(self, task_manager):
        """测试计算任务持续天数"""
        task = task_manager.create_task("持续测试", quadrant=0)

        # 未完成的任务
        duration = task_manager.get_task_duration_days(task.id)
        assert duration is None

        # 完成的任务
        task_manager.complete_task(task.id)
        duration = task_manager.get_task_duration_days(task.id)
        assert duration == 0  # 同一天完成

    def test_get_quadrant_summary(self, task_manager):
        """测试获取象限摘要"""
        task_manager.create_task("Q1任务1", quadrant=0)
        task_manager.create_task("Q1任务2", quadrant=0)
        t3 = task_manager.create_task("Q1任务3", quadrant=0)
        task_manager.complete_task(t3.id)

        summary = task_manager.get_quadrant_summary()

        assert summary[0]['pending'] == 2
        assert summary[0]['completed'] == 1
        assert summary[0]['total'] == 3

    def test_get_quadrant_name(self):
        """测试获取象限名称"""
        assert TaskManager.get_quadrant_name(0) == "重要紧急"
        assert TaskManager.get_quadrant_name(1) == "重要不紧急"
        assert TaskManager.get_quadrant_name(2) == "紧急不重要"
        assert TaskManager.get_quadrant_name(3) == "不紧急不重要"

    def test_get_quadrant_color(self):
        """测试获取象限颜色"""
        assert TaskManager.get_quadrant_color(0) == "#FF6B6B"
        assert TaskManager.get_quadrant_color(1) == "#FFD93D"
        assert TaskManager.get_quadrant_color(2) == "#4D96FF"
        assert TaskManager.get_quadrant_color(3) == "#A0A0A0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
