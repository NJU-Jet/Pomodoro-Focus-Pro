"""Data persistence layer using SQLite."""

import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class Quadrant(Enum):
    """任务象限枚举"""
    URGENT_IMPORTANT = 0  # 重要紧急
    IMPORTANT_NOT_URGENT = 1  # 重要不紧急
    URGENT_NOT_IMPORTANT = 2  # 紧急不重要
    NOT_URGENT_NOT_IMPORTANT = 3  # 不紧急不重要


class TimerStatus(Enum):
    """番茄钟状态枚举"""
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FORCE_COMPLETED = "force_completed"


class Storage:
    """SQLite数据存储管理器"""

    def __init__(self, db_path: str = "pomodoro.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self._lock = threading.Lock()  # 线程锁，保护数据库操作
        self._connect()
        self._create_tables()

    def _connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _execute_sql(self, query: tuple, fetch_all: bool = False):
        """
        线程安全的SQL执行方法

        Args:
            query: (sql, params) 元组
            fetch_all: 是否获取所有结果

        Returns:
            执行结果
        """
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(*query)
            self.conn.commit()

            if fetch_all:
                return [dict(row) for row in cursor.fetchall()]
            else:
                row = cursor.fetchone()
                return dict(row) if row else None

    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()

        # 任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                created_date TEXT NOT NULL,
                estimated_pomodoros INTEGER DEFAULT 0,
                quadrant INTEGER NOT NULL,
                completed_date TEXT,
                actual_pomodoros INTEGER DEFAULT 0,
                is_completed BOOLEAN DEFAULT 0
            )
        """)

        # 番茄钟会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration INTEGER DEFAULT 30,
                status TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)

        # 日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                task_id INTEGER,
                date TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)

        # 每日心得感悟表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                content TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.conn.commit()

    # ==================== 任务操作 ====================

    def create_task(self, description: str, quadrant: int,
                    estimated_pomodoros: int = 0) -> int:
        """
        创建新任务

        Args:
            description: 任务描述
            quadrant: 所属象限 (0-3)
            estimated_pomodoros: 预计番茄钟数

        Returns:
            任务ID
        """
        with self._lock:  # 线程安全保护
            cursor = self.conn.cursor()
            created_date = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO tasks (description, created_date, quadrant, estimated_pomodoros)
                VALUES (?, ?, ?, ?)
            """, (description, created_date, quadrant, estimated_pomodoros))

            self.conn.commit()
            return cursor.lastrowid

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个任务

        Args:
            task_id: 任务ID

        Returns:
            任务字典，不存在则返回None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_all_tasks(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有任务

        Args:
            include_completed: 是否包含已完成的任务

        Returns:
            任务列表
        """
        cursor = self.conn.cursor()

        if include_completed:
            cursor.execute("SELECT * FROM tasks ORDER BY created_date DESC")
        else:
            cursor.execute("SELECT * FROM tasks WHERE is_completed = 0 ORDER BY created_date DESC")

        return [dict(row) for row in cursor.fetchall()]

    def get_tasks_by_quadrant(self, quadrant: int,
                              include_completed: bool = False) -> List[Dict[str, Any]]:
        """
        获取指定象限的任务

        Args:
            quadrant: 象限编号 (0-3)
            include_completed: 是否包含已完成的任务

        Returns:
            任务列表
        """
        cursor = self.conn.cursor()

        if include_completed:
            cursor.execute(
                "SELECT * FROM tasks WHERE quadrant = ? ORDER BY created_date DESC",
                (quadrant,)
            )
        else:
            cursor.execute(
                "SELECT * FROM tasks WHERE quadrant = ? AND is_completed = 0 ORDER BY created_date DESC",
                (quadrant,)
            )

        return [dict(row) for row in cursor.fetchall()]

    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有已完成的任务

        Returns:
            已完成任务列表
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE is_completed = 1 ORDER BY completed_date DESC")
        return [dict(row) for row in cursor.fetchall()]

    def update_task(self, task_id: int, **kwargs) -> bool:
        """
        更新任务信息

        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段

        Returns:
            是否成功
        """
        allowed_fields = {'description', 'estimated_pomodoros', 'quadrant'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        query = "UPDATE tasks SET " + ", ".join(f"{k} = ?" for k in updates.keys()) + " WHERE id = ?"
        values = list(updates.values()) + [task_id]

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()

        return cursor.rowcount > 0

    def complete_task(self, task_id: int) -> bool:
        """
        标记任务为完成

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()
        completed_date = datetime.now().isoformat()

        cursor.execute("""
            UPDATE tasks
            SET is_completed = 1, completed_date = ?
            WHERE id = ?
        """, (completed_date, task_id))

        self.conn.commit()
        return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def increment_task_pomodoros(self, task_id: int) -> bool:
        """
        增加任务的番茄钟计数

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        with self._lock:  # 线程安全保护
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET actual_pomodoros = actual_pomodoros + 1
                WHERE id = ?
            """, (task_id,))
            self.conn.commit()
            return cursor.rowcount > 0

    # ==================== 番茄钟会话操作 ====================

    def create_pomodoro_session(self, task_id: Optional[int],
                                start_time: str) -> int:
        """
        创建番茄钟会话

        Args:
            task_id: 关联任务ID（可为空）
            start_time: 开始时间

        Returns:
            会话ID
        """
        with self._lock:  # 线程安全保护
            cursor = self.conn.cursor()
            date = datetime.fromisoformat(start_time).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO pomodoro_sessions (task_id, start_time, date, status)
                VALUES (?, ?, ?, ?)
            """, (task_id, start_time, date, "running"))

            self.conn.commit()
            return cursor.lastrowid

    def end_pomodoro_session(self, session_id: int, end_time: str,
                             status: TimerStatus) -> bool:
        """
        结束番茄钟会话

        Args:
            session_id: 会话ID
            end_time: 结束时间
            status: 结束状态

        Returns:
            是否成功
        """
        with self._lock:  # 线程安全保护
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE pomodoro_sessions
                SET end_time = ?, status = ?
                WHERE id = ?
            """, (end_time, status.value, session_id))

            self.conn.commit()
            return cursor.rowcount > 0

    def get_pomodoro_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        获取指定番茄钟会话

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典，不存在则返回None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM pomodoro_sessions
            WHERE id = ?
        """, (session_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_pomodoro_sessions_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        获取指定日期的番茄钟会话

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            会话列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM pomodoro_sessions
            WHERE date = ? AND status = ?
            ORDER BY start_time
        """, (date, TimerStatus.COMPLETED.value))

        return [dict(row) for row in cursor.fetchall()]

    def get_daily_pomodoro_count(self, date: str) -> int:
        """
        获取指定日期的番茄钟总数

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            番茄钟数量
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM pomodoro_sessions
            WHERE date = ? AND status = ?
        """, (date, TimerStatus.COMPLETED.value))

        row = cursor.fetchone()
        return row['count'] if row else 0

    def get_pomodoro_sessions_by_task(self, task_id: int) -> List[Dict[str, Any]]:
        """
        获取指定任务的所有番茄钟会话

        Args:
            task_id: 任务ID

        Returns:
            会话列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM pomodoro_sessions
            WHERE task_id = ? AND status = ?
            ORDER BY start_time
        """, (task_id, TimerStatus.COMPLETED.value))

        return [dict(row) for row in cursor.fetchall()]

    def get_task_pomodoro_count(self, task_id: int) -> int:
        """
        获取指定任务的番茄钟总数

        Args:
            task_id: 任务ID

        Returns:
            番茄钟数量
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM pomodoro_sessions
            WHERE task_id = ? AND status = ?
        """, (task_id, TimerStatus.COMPLETED.value))

        row = cursor.fetchone()
        return row['count'] if row else 0

    # ==================== 日志操作 ====================

    def create_log(self, content: str, task_id: Optional[int] = None) -> int:
        """
        创建日志

        Args:
            content: 日志内容
            task_id: 关联任务ID（可选）

        Returns:
            日志ID
        """
        with self._lock:  # 线程安全保护
            cursor = self.conn.cursor()
            timestamp = datetime.now().isoformat()
            date = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO logs (content, timestamp, task_id, date)
                VALUES (?, ?, ?, ?)
            """, (content, timestamp, task_id, date))

            self.conn.commit()
            return cursor.lastrowid

    def get_logs_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        获取指定日期的日志

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            日志列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM logs
            WHERE date = ?
            ORDER BY timestamp
        """, (date,))

        return [dict(row) for row in cursor.fetchall()]

    def get_logs_by_task(self, task_id: int) -> List[Dict[str, Any]]:
        """
        获取指定任务的日志

        Args:
            task_id: 任务ID

        Returns:
            日志列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM logs
            WHERE task_id = ?
            ORDER BY timestamp
        """, (task_id,))

        return [dict(row) for row in cursor.fetchall()]

    # ==================== 每日心得感悟操作 ====================

    def save_daily_reflection(self, date: str, content: str) -> bool:
        """
        保存或更新每日心得感悟

        Args:
            date: 日期 (YYYY-MM-DD)
            content: 感悟内容

        Returns:
            是否成功
        """
        with self._lock:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()

            # 检查是否已存在
            cursor.execute("SELECT id FROM daily_reflections WHERE date = ?", (date,))
            exists = cursor.fetchone()

            if exists:
                # 更新
                cursor.execute("""
                    UPDATE daily_reflections
                    SET content = ?, updated_at = ?
                    WHERE date = ?
                """, (content, now, date))
            else:
                # 插入
                cursor.execute("""
                    INSERT INTO daily_reflections (date, content, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (date, content, now, now))

            self.conn.commit()
            return True

    def get_daily_reflection(self, date: str) -> Optional[Dict[str, Any]]:
        """
        获取指定日期的心得感悟

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            感悟字典，不存在则返回None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM daily_reflections WHERE date = ?", (date,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_all_reflections(self) -> List[Dict[str, Any]]:
        """
        获取所有心得感悟

        Returns:
            感悟列表，按日期降序
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM daily_reflections ORDER BY date DESC")
        return [dict(row) for row in cursor.fetchall()]

    # ==================== 统计操作 ====================

    def get_pending_task_counts_by_quadrant(self, date: str = None) -> Dict[int, int]:
        """
        获取各象限未完成任务数量（指定日期时的快照）

        Args:
            date: 日期 (YYYY-MM-DD)，None表示当前

        Returns:
            {象限: 任务数量}
        """
        cursor = self.conn.cursor()

        if date is None:
            # 当前状态
            cursor.execute("""
                SELECT quadrant, COUNT(*) as count
                FROM tasks
                WHERE is_completed = 0
                GROUP BY quadrant
            """)
        else:
            # 历史快照：获取在指定日期之前创建且在指定日期时仍未完成的任务
            # 这里简化处理，返回历史数据
            cursor.execute("""
                SELECT quadrant, COUNT(*) as count
                FROM tasks
                WHERE is_completed = 0
                  AND created_date <= ?
                  AND (completed_date IS NULL OR completed_date > ?)
                GROUP BY quadrant
            """, (date + "T23:59:59", date + "T00:00:00"))

        result = {0: 0, 1: 0, 2: 0, 3: 0}
        for row in cursor.fetchall():
            result[row['quadrant']] = row['count']

        return result

    def get_monthly_pomodoro_counts(self, year: int, month: int) -> Dict[str, int]:
        """
        获取指定月份每天的番茄钟数量

        Args:
            year: 年份
            month: 月份 (1-12)

        Returns:
            {日期(DD): 番茄钟数量}
        """
        cursor = self.conn.cursor()
        month_str = f"{year}-{month:02d}"

        cursor.execute("""
            SELECT substr(date, 9) as day, COUNT(*) as count
            FROM pomodoro_sessions
            WHERE date LIKE ? AND status = ?
            GROUP BY date
            ORDER BY date
        """, (f"{month_str}%", TimerStatus.COMPLETED.value))

        return {row['day']: row['count'] for row in cursor.fetchall()}

    def export_to_json(self, file_path: str) -> bool:
        """
        导出数据到JSON文件

        Args:
            file_path: 导出文件路径

        Returns:
            是否成功
        """
        try:
            data = {
                'tasks': self.get_all_tasks(include_completed=True),
                'pomodoro_sessions': [],
                'logs': []
            }

            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM pomodoro_sessions ORDER BY start_time")
            data['pomodoro_sessions'] = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM logs ORDER BY timestamp")
            data['logs'] = [dict(row) for row in cursor.fetchall()]

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
