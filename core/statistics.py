"""统计模块 - 数据统计和历史计算。"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from calendar import monthcalendar, monthrange
from data.storage import Storage


class DailyStatistics:
    """每日统计数据类"""

    def __init__(self, date: str, total_pomodoros: int,
                 completed_tasks: List[Dict],
                 pending_counts: Dict[int, int],
                 logs: List[Dict],
                 reflection: Optional[Dict] = None):
        """
        初始化每日统计

        Args:
            date: 日期 (YYYY-MM-DD)
            total_pomodoros: 番茄钟总数
            completed_tasks: 当日完成的任务列表
            pending_counts: 各象限未完成数量 {象限: 数量}
            logs: 当日日志列表
            reflection: 当日心得感悟
        """
        self.date = date
        self.total_pomodoros = total_pomodoros
        self.completed_tasks = completed_tasks
        self.pending_counts = pending_counts
        self.logs = logs
        self.reflection = reflection

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'date': self.date,
            'total_pomodoros': self.total_pomodoros,
            'completed_tasks': self.completed_tasks,
            'pending_counts': self.pending_counts,
            'logs': self.logs,
            'reflection': self.reflection
        }


class MonthlyStatistics:
    """月度统计数据类"""

    def __init__(self, year: int, month: int):
        """
        初始化月度统计

        Args:
            year: 年份
            month: 月份 (1-12)
        """
        self.year = year
        self.month = month
        self.days_with_data: Dict[str, int] = {}  # {日期: 番茄钟数}
        self.total_pomodoros = 0
        self.days_with_pomodoros = 0

    def add_day(self, day: str, pomodoro_count: int):
        """
        添加某天的数据

        Args:
            day: 日期 (DD)
            pomodoro_count: 番茄钟数量
        """
        self.days_with_data[day] = pomodoro_count
        self.total_pomodoros += pomodoro_count
        if pomodoro_count > 0:
            self.days_with_pomodoros += 1

    def get_average_daily(self) -> float:
        """
        获取平均每日番茄钟数

        Returns:
            平均值
        """
        if self.days_with_pomodoros == 0:
            return 0.0
        return self.total_pomodoros / self.days_with_pomodoros

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'year': self.year,
            'month': self.month,
            'days_with_data': self.days_with_data,
            'total_pomodoros': self.total_pomodoros,
            'days_with_pomodoros': self.days_with_pomodoros,
            'average_daily': self.get_average_daily()
        }


class Statistics:
    """统计管理器"""

    def __init__(self, storage: Storage):
        """
        初始化统计管理器

        Args:
            storage: 数据存储对象
        """
        self.storage = storage

    def get_daily_statistics(self, date: str) -> DailyStatistics:
        """
        获取指定日期的统计信息

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            每日统计对象
        """
        # 获取当日番茄钟总数
        total_pomodoros = self.storage.get_daily_pomodoro_count(date)

        # 获取当日番茄钟会话
        sessions = self.storage.get_pomodoro_sessions_by_date(date)

        # 获取当日番茄钟会话关联的任务及其番茄钟数
        task_pomodoros: Dict[int, int] = {}
        for session in sessions:
            task_id = session['task_id']
            if task_id:
                task_pomodoros[task_id] = task_pomodoros.get(task_id, 0) + 1

        # 获取真正已完成的任务（通过completed_date判断）
        all_tasks = self.storage.get_all_tasks(include_completed=True)
        completed_tasks = []

        for task in all_tasks:
            # 检查任务是否在当日完成
            if task.get('is_completed'):
                completed_date = task.get('completed_date', '')
                if completed_date and completed_date.startswith(date):
                    pomodoros = task_pomodoros.get(task['id'], 0)
                    completed_tasks.append({
                        'id': task['id'],
                        'description': task['description'],
                        'pomodoros': pomodoros,
                        'quadrant': task['quadrant']
                    })

        # 获取该日结束时各象限未完成任务数量
        pending_counts = self.storage.get_pending_task_counts_by_quadrant(date)

        # 获取当日日志
        logs = self.storage.get_logs_by_date(date)

        # 获取当日心得感悟
        reflection = self.storage.get_daily_reflection(date)

        return DailyStatistics(
            date=date,
            total_pomodoros=total_pomodoros,
            completed_tasks=completed_tasks,
            pending_counts=pending_counts,
            logs=logs,
            reflection=reflection
        )

    def get_monthly_statistics(self, year: int, month: int) -> MonthlyStatistics:
        """
        获取指定月份的统计信息

        Args:
            year: 年份
            month: 月份 (1-12)

        Returns:
            月度统计对象
        """
        monthly_stats = MonthlyStatistics(year, month)
        daily_counts = self.storage.get_monthly_pomodoro_counts(year, month)

        for day, count in daily_counts.items():
            monthly_stats.add_day(day, count)

        return monthly_stats

    def get_weekly_statistics(self, start_date: str) -> Dict[str, int]:
        """
        获取一周的统计信息

        Args:
            start_date: 开始日期 (YYYY-MM-DD)

        Returns:
            {日期: 番茄钟数}
        """
        weekly_data = {}
        start = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(7):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            count = self.storage.get_daily_pomodoro_count(date)
            weekly_data[date] = count

        return weekly_data

    def get_total_pomodoros(self, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> int:
        """
        获取时间范围内的番茄钟总数

        Args:
            start_date: 开始日期 (YYYY-MM-DD)，None表示不限
            end_date: 结束日期 (YYYY-MM-DD)，None表示不限

        Returns:
            番茄钟总数
        """
        # 这里简化实现，如果需要精确范围可以在storage层添加
        if not start_date and not end_date:
            # 获取所有数据的总和
            cursor = self.storage.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM pomodoro_sessions
                WHERE status = 'completed'
            """)
            row = cursor.fetchone()
            return row['count'] if row else 0

        # TODO: 实现日期范围查询
        return 0

    def get_task_statistics(self, task_id: int) -> Dict:
        """
        获取指定任务的统计信息

        Args:
            task_id: 任务ID

        Returns:
            任务统计字典
        """
        task = self.storage.get_task(task_id)
        if not task:
            return {}

        sessions = self.storage.get_pomodoro_sessions_by_task(task_id)

        # 将is_completed转换为布尔值
        is_completed = task.get('is_completed', False)
        if isinstance(is_completed, int):
            is_completed = bool(is_completed)

        return {
            'task_id': task_id,
            'description': task['description'],
            'quadrant': task['quadrant'],
            'estimated_pomodoros': task.get('estimated_pomodoros', 0),
            'actual_pomodoros': len(sessions),
            'is_completed': is_completed,
            'created_date': task['created_date'],
            'completed_date': task.get('completed_date'),
            'sessions': sessions
        }

    def get_productivity_streak(self) -> Dict[str, int]:
        """
        获取连续生产力记录

        Returns:
            {
                'current_streak': 当前连续天数,
                'longest_streak': 最长连续天数
            }
        """
        cursor = self.storage.conn.cursor()

        # 获取所有有番茄钟的日期
        cursor.execute("""
            SELECT date, COUNT(*) as count
            FROM pomodoro_sessions
            WHERE status = 'completed'
            GROUP BY date
            ORDER BY date DESC
        """)

        dates = [row['date'] for row in cursor.fetchall()]

        if not dates:
            return {'current_streak': 0, 'longest_streak': 0}

        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        today = datetime.now().date()

        # 计算当前连续天数（从今天开始向回检查）
        for i, date_str in enumerate(dates):
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            expected_date = today - timedelta(days=i)

            if date == expected_date:
                current_streak += 1
            else:
                break

        # 计算最长连续天数
        if len(dates) > 0:
            temp_streak = 1
            longest_streak = 1

            for i in range(1, len(dates)):
                curr_date = datetime.strptime(dates[i], "%Y-%m-%d").date()
                prev_date = datetime.strptime(dates[i - 1], "%Y-%m-%d").date()

                # 检查相邻日期是否连续（前一个日期 - 当前日期 = 1天）
                if (prev_date - curr_date).days == 1:
                    temp_streak += 1
                else:
                    temp_streak = 1

                if temp_streak > longest_streak:
                    longest_streak = temp_streak

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }

    def get_quadrant_distribution(self) -> Dict[int, Dict]:
        """
        获取各象限的任务分布

        Returns:
            {
                象限: {
                    'pending': 未完成数,
                    'completed': 完成数,
                    'completion_rate': 完成率
                }
            }
        """
        all_tasks = self.storage.get_all_tasks(include_completed=True)

        distribution = {}
        for q in range(4):
            quadrant_tasks = [t for t in all_tasks if t['quadrant'] == q]
            pending = len([t for t in quadrant_tasks if not bool(t.get('is_completed', False))])
            completed = len([t for t in quadrant_tasks if bool(t.get('is_completed', False))])
            total = pending + completed

            completion_rate = (completed / total * 100) if total > 0 else 0.0

            distribution[q] = {
                'pending': pending,
                'completed': completed,
                'total': total,
                'completion_rate': round(completion_rate, 2)
            }

        return distribution

    def get_calendar_data(self, year: int, month: int) -> List[List[Optional[int]]]:
        """
        获取日历视图数据

        Args:
            year: 年份
            month: 月份 (1-12)

        Returns:
            6x7的日历矩阵，每个元素为该日的番茄钟数（无数据为None）
        """
        # 获取月份日历布局
        cal = monthcalendar(year, month)

        # 获取该月的番茄钟数据
        daily_counts = self.storage.get_monthly_pomodoro_counts(year, month)

        # 构建日历矩阵
        calendar_data = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append(None)
                else:
                    day_key = f"{day:02d}"
                    week_data.append(daily_counts.get(day_key, 0))
            calendar_data.append(week_data)

        return calendar_data
