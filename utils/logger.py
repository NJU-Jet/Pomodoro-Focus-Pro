"""日志工具 - 记录和检索日志。"""

from typing import List, Dict, Optional
from datetime import datetime
from data.storage import Storage


class LogEntry:
    """日志条目类"""

    def __init__(self, log_id: int, content: str, timestamp: str,
                 task_id: Optional[int] = None, date: str = None):
        """
        初始化日志条目

        Args:
            log_id: 日志ID
            content: 日志内容
            timestamp: 时间戳
            task_id: 关联任务ID（可选）
            date: 日期 (YYYY-MM-DD)
        """
        self.id = log_id
        self.content = content
        self.timestamp = timestamp
        self.task_id = task_id
        self.date = date or datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")

    @classmethod
    def from_dict(cls, data: Dict) -> 'LogEntry':
        """从字典创建LogEntry对象"""
        return cls(
            log_id=data['id'],
            content=data['content'],
            timestamp=data['timestamp'],
            task_id=data.get('task_id'),
            date=data.get('date')
        )

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp,
            'task_id': self.task_id,
            'date': self.date
        }

    def get_formatted_time(self) -> str:
        """获取格式化的时间"""
        dt = datetime.fromisoformat(self.timestamp)
        return dt.strftime("%H:%M")


class Logger:
    """日志管理器"""

    def __init__(self, storage: Storage):
        """
        初始化日志管理器

        Args:
            storage: 数据存储对象
        """
        self.storage = storage

    def create_log(self, content: str, task_id: Optional[int] = None) -> LogEntry:
        """
        创建新日志

        Args:
            content: 日志内容
            task_id: 关联任务ID（可选）

        Returns:
            创建的日志对象

        Raises:
            ValueError: 如果内容为空
        """
        if not content or not content.strip():
            raise ValueError("日志内容不能为空")

        log_id = self.storage.create_log(content.strip(), task_id)
        log_data = self.storage.get_logs_by_date(
            datetime.now().strftime("%Y-%m-%d")
        )
        log_entry = next((l for l in log_data if l['id'] == log_id), None)

        if log_entry:
            return LogEntry.from_dict(log_entry)

        # 回退：直接从数据库获取
        cursor = self.storage.conn.cursor()
        cursor.execute("SELECT * FROM logs WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        if row:
            return LogEntry.from_dict(dict(row))
        else:
            raise ValueError(f"无法找到日志记录: {log_id}")

    def get_logs_by_date(self, date: str) -> List[LogEntry]:
        """
        获取指定日期的日志

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            日志列表
        """
        logs_data = self.storage.get_logs_by_date(date)
        return [LogEntry.from_dict(log) for log in logs_data]

    def get_logs_by_task(self, task_id: int) -> List[LogEntry]:
        """
        获取指定任务的日志

        Args:
            task_id: 任务ID

        Returns:
            日志列表
        """
        logs_data = self.storage.get_logs_by_task(task_id)
        return [LogEntry.from_dict(log) for log in logs_data]

    def get_recent_logs(self, limit: int = 10) -> List[LogEntry]:
        """
        获取最近的日志

        Args:
            limit: 返回数量

        Returns:
            日志列表
        """
        cursor = self.storage.conn.cursor()
        cursor.execute("""
            SELECT * FROM logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        return [LogEntry.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_today_logs(self) -> List[LogEntry]:
        """
        获取今天的日志

        Returns:
            日志列表
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_logs_by_date(today)

    def search_logs(self, keyword: str, date: Optional[str] = None) -> List[LogEntry]:
        """
        搜索日志

        Args:
            keyword: 搜索关键词
            date: 限定日期（可选）

        Returns:
            匹配的日志列表
        """
        cursor = self.storage.conn.cursor()

        if date:
            cursor.execute("""
                SELECT * FROM logs
                WHERE date = ? AND content LIKE ?
                ORDER BY timestamp DESC
            """, (date, f"%{keyword}%"))
        else:
            cursor.execute("""
                SELECT * FROM logs
                WHERE content LIKE ?
                ORDER BY timestamp DESC
            """, (f"%{keyword}%",))

        return [LogEntry.from_dict(dict(row)) for row in cursor.fetchall()]
