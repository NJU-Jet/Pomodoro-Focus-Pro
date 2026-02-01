"""任务管理器 - 处理任务的增删改查和象限逻辑。"""

from typing import List, Dict, Optional
from datetime import datetime
from data.storage import Storage, Quadrant


class Task:
    """任务数据类"""

    def __init__(self, task_id: int, description: str, created_date: str,
                 quadrant: int, estimated_pomodoros: int = 0,
                 completed_date: Optional[str] = None, actual_pomodoros: int = 0,
                 is_completed: bool = False):
        self.id = task_id
        self.description = description
        self.created_date = created_date
        self.quadrant = quadrant
        self.estimated_pomodoros = estimated_pomodoros
        self.completed_date = completed_date
        self.actual_pomodoros = actual_pomodoros
        self.is_completed = is_completed

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """从字典创建Task对象"""
        # 将SQLite返回的整数转换为布尔值
        is_completed = data.get('is_completed', False)
        if isinstance(is_completed, int):
            is_completed = bool(is_completed)

        return cls(
            task_id=data['id'],
            description=data['description'],
            created_date=data['created_date'],
            quadrant=data['quadrant'],
            estimated_pomodoros=data.get('estimated_pomodoros', 0),
            completed_date=data.get('completed_date'),
            actual_pomodoros=data.get('actual_pomodoros', 0),
            is_completed=is_completed
        )

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'description': self.description,
            'created_date': self.created_date,
            'quadrant': self.quadrant,
            'estimated_pomodoros': self.estimated_pomodoros,
            'completed_date': self.completed_date,
            'actual_pomodoros': self.actual_pomodoros,
            'is_completed': self.is_completed
        }


class TaskManager:
    """任务管理器"""

    # 象限名称映射
    QUADRANT_NAMES = {
        0: "重要紧急",
        1: "重要不紧急",
        2: "紧急不重要",
        3: "不紧急不重要"
    }

    # 象限颜色映射
    QUADRANT_COLORS = {
        0: "#FF6B6B",  # 红色
        1: "#FFD93D",  # 黄色
        2: "#4D96FF",  # 蓝色
        3: "#A0A0A0"   # 灰色
    }

    def __init__(self, storage: Storage):
        """
        初始化任务管理器

        Args:
            storage: 数据存储对象
        """
        self.storage = storage

    def create_task(self, description: str, quadrant: int,
                    estimated_pomodoros: int = 0) -> Task:
        """
        创建新任务

        Args:
            description: 任务描述
            quadrant: 所属象限 (0-3)
            estimated_pomodoros: 预计番茄钟数

        Returns:
            创建的任务对象

        Raises:
            ValueError: 如果象限编号无效
        """
        if not 0 <= quadrant <= 3:
            raise ValueError(f"无效的象限编号: {quadrant}，必须是0-3之间的整数")

        if not description or not description.strip():
            raise ValueError("任务描述不能为空")

        task_id = self.storage.create_task(
            description=description.strip(),
            quadrant=quadrant,
            estimated_pomodoros=estimated_pomodoros
        )

        task_data = self.storage.get_task(task_id)
        return Task.from_dict(task_data)

    def get_task(self, task_id: int) -> Optional[Task]:
        """
        获取指定任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，不存在则返回None
        """
        task_data = self.storage.get_task(task_id)
        if task_data:
            return Task.from_dict(task_data)
        return None

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """
        获取所有任务

        Args:
            include_completed: 是否包含已完成的任务

        Returns:
            任务列表
        """
        tasks_data = self.storage.get_all_tasks(include_completed=include_completed)
        return [Task.from_dict(t) for t in tasks_data]

    def get_tasks_by_quadrant(self, quadrant: int,
                              include_completed: bool = False) -> List[Task]:
        """
        获取指定象限的任务

        Args:
            quadrant: 象限编号 (0-3)
            include_completed: 是否包含已完成的任务

        Returns:
            任务列表

        Raises:
            ValueError: 如果象限编号无效
        """
        if not 0 <= quadrant <= 3:
            raise ValueError(f"无效的象限编号: {quadrant}")

        tasks_data = self.storage.get_tasks_by_quadrant(quadrant, include_completed)
        return [Task.from_dict(t) for t in tasks_data]

    def get_completed_tasks(self) -> List[Task]:
        """
        获取所有已完成的任务

        Returns:
            已完成任务列表
        """
        tasks_data = self.storage.get_completed_tasks()
        return [Task.from_dict(t) for t in tasks_data]

    def update_task(self, task_id: int, description: str = None,
                    estimated_pomodoros: int = None) -> bool:
        """
        更新任务信息

        Args:
            task_id: 任务ID
            description: 新的任务描述
            estimated_pomodoros: 新的预计番茄钟数

        Returns:
            是否成功

        Raises:
            ValueError: 如果任务不存在或参数无效
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.is_completed:
            raise ValueError("已完成的任务不能修改")

        updates = {}
        if description is not None:
            if not description.strip():
                raise ValueError("任务描述不能为空")
            updates['description'] = description.strip()

        if estimated_pomodoros is not None:
            if estimated_pomodoros < 0:
                raise ValueError("预计番茄钟数不能为负数")
            updates['estimated_pomodoros'] = estimated_pomodoros

        if not updates:
            return False

        return self.storage.update_task(task_id, **updates)

    def move_task_to_quadrant(self, task_id: int, new_quadrant: int) -> bool:
        """
        移动任务到不同象限

        Args:
            task_id: 任务ID
            new_quadrant: 新的象限编号 (0-3)

        Returns:
            是否成功

        Raises:
            ValueError: 如果任务不存在、已完成或象限编号无效
        """
        if not 0 <= new_quadrant <= 3:
            raise ValueError(f"无效的象限编号: {new_quadrant}")

        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.is_completed:
            raise ValueError("已完成的任务不能移动象限")

        if task.quadrant == new_quadrant:
            return False  # 已经在目标象限

        return self.storage.update_task(task_id, quadrant=new_quadrant)

    def complete_task(self, task_id: int) -> bool:
        """
        标记任务为完成

        Args:
            task_id: 任务ID

        Returns:
            是否成功

        Raises:
            ValueError: 如果任务不存在
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.is_completed:
            return False  # 已经完成

        return self.storage.complete_task(task_id)

    def delete_task(self, task_id: int) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功

        Raises:
            ValueError: 如果任务不存在
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        return self.storage.delete_task(task_id)

    def increment_task_pomodoros(self, task_id: int) -> bool:
        """
        增加任务的番茄钟计数

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        return self.storage.increment_task_pomodoros(task_id)

    def get_task_duration_days(self, task_id: int) -> Optional[int]:
        """
        计算任务从创建到完成的天数

        Args:
            task_id: 任务ID

        Returns:
            持续天数，未完成则返回None
        """
        task = self.get_task(task_id)
        if not task or not task.is_completed:
            return None

        created = datetime.fromisoformat(task.created_date)
        completed = datetime.fromisoformat(task.completed_date)
        return (completed - created).days

    def get_quadrant_summary(self) -> Dict[int, Dict[str, int]]:
        """
        获取各象限的任务统计摘要

        Returns:
            {
                象限: {
                    'pending': 未完成数量,
                    'completed': 完成数量,
                    'total': 总数量
                }
            }
        """
        summary = {}
        for q in range(4):
            pending = self.get_tasks_by_quadrant(q, include_completed=False)
            completed_list = self.get_tasks_by_quadrant(q, include_completed=True)
            completed = [t for t in completed_list if t.is_completed]

            summary[q] = {
                'pending': len(pending),
                'completed': len(completed),
                'total': len(pending) + len(completed)
            }

        return summary

    @staticmethod
    def get_quadrant_name(quadrant: int) -> str:
        """获取象限名称"""
        return TaskManager.QUADRANT_NAMES.get(quadrant, "未知")

    @staticmethod
    def get_quadrant_color(quadrant: int) -> str:
        """获取象限颜色"""
        return TaskManager.QUADRANT_COLORS.get(quadrant, "#808080")
