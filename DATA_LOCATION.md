# 📂 数据存储位置说明

## 主数据库文件

```
/Users/lihua/Downloads/temp/番茄钟_claude/pomodoro.db
```

- **文件类型**: SQLite 数据库
- **文件大小**: 约 20KB
- **位置**: 项目根目录

---

## 数据库结构

### 1. **待办事项** → `tasks` 表

| 字段 | 说明 |
|------|------|
| id | 任务ID |
| description | 任务描述 |
| quadrant | 象限（0=重要紧急，1=重要不紧急，2=紧急不重要，3=不紧急不重要）|
| is_completed | 是否完成（0=待办，1=完成）|
| actual_pomodoros | 实际完成的番茄钟数 |

**查询示例**：
```sql
-- 查看所有待办任务
SELECT * FROM tasks WHERE is_completed = 0;

-- 查看已完成的任务
SELECT * FROM tasks WHERE is_completed = 1;
```

---

### 2. **历史数据** → `pomodoro_sessions` 表

| 字段 | 说明 |
|------|------|
| id | 会话ID |
| task_id | 关联的任务ID |
| date | 日期（YYYY-MM-DD）|
| start_time | 开始时间 |
| end_time | 结束时间 |
| status | 状态（completed/abandoned/force_completed）|

**查询示例**：
```sql
-- 查看某天的番茄钟记录
SELECT * FROM pomodoro_sessions WHERE date = '2026-01-26';

-- 统计每天的番茄钟数量
SELECT date, COUNT(*) as count
FROM pomodoro_sessions
WHERE status = 'completed'
GROUP BY date
ORDER BY date DESC;
```

---

### 3. **日志记录** → `logs` 表

| 字段 | 说明 |
|------|------|
| id | 日志ID |
| content | 日志内容 |
| timestamp | 时间戳 |
| date | 日期 |

---

## 🛠️ 查看数据的方法

### 方法1：使用查看工具（推荐）
```bash
python3 inspect_db.py
```

### 方法2：使用 SQLite 命令行
```bash
# 进入数据库
sqlite3 pomodoro.db

# 查看所有表
.tables

# 查看任务数据
SELECT * FROM tasks;

# 退出
.quit
```

### 方法3：使用脚本
```bash
./view_data.sh
```

---

## 💾 备份与恢复

### 备份数据
```bash
# 复制数据库文件
cp pomodoro.db pomodoro.db.backup_$(date +%Y%m%d)

# 或使用应用导出功能
python3 main.py
# 然后选择：文件 -> 导出数据
```

### 恢复数据
```bash
# 停止应用，然后恢复备份
cp pomodoro.db.backup pomodoro.db
```

### 重置数据
```bash
# 删除数据库，重新生成测试数据
rm pomodoro.db
python3 generate_test_data.py
```

---

## 📊 数据统计

使用以下命令查看数据统计：

```bash
python3 verify_app.py
```

输出示例：
```
📋 任务列表:
  总任务: 11
  已完成: 6
  待完成: 5

🍅 番茄钟统计:
  2026-01-29: 3个
  2026-01-28: 5个
  ...

📝 日志统计:
  总日志数: 16条
```

---

## 🔍 数据关系

```
tasks (任务)
  ↓ (1:N)
pomodoro_sessions (番茄钟会话)
  ↓
统计数据 (每天/每月/每年)

logs (日志)
  ↓
历史记录 (按日期查看)
```

---

## 💡 提示

1. **所有数据都存储在 `pomodoro.db` 文件中**
2. **SQLite 数据库不需要额外服务器**
3. **可以直接复制文件进行备份**
4. **应用启动时会自动创建数据库**
5. **删除数据库文件会丢失所有数据**
