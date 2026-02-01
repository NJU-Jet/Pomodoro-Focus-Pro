# CLAUDE.md

开发指南给 Claude Code (claude.ai/code) 和项目贡献者。

## 项目概述

**Pomodoro Focus Pro (PFE)** 是一款 macOS 效率工具，结合艾森豪威尔矩阵（四象限法则）与番茄工作法，帮助用户智能规划任务、专注执行并回顾生产力数据。

**技术栈:**
- Python 3.9+
- PyQt6 6.6.1 (GUI 框架，macOS 原生外观)
- SQLite (数据持久化)
- pytest 7.4.3 + pytest-qt 4.3.0 (测试框架)

**当前版本:** v3.0.0 (响应式布局版)

**项目状态:** 生产就绪，功能完整

---

## 开发命令

### 环境配置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS

# 安装依赖
pip install -r requirements.txt
```

### 依赖项

```
PyQt6==6.6.1
pytest==7.4.3
pytest-qt==4.3.0
```

### 运行应用

```bash
# 启动应用（推荐）
python main_responsive.py

# 或使用脚本
./run_responsive.sh
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_task_manager.py

# 运行测试并显示输出
pytest -v -s

# 查看测试覆盖率
pytest --cov=core --cov-report=html
open htmlcov/index.html
```

---

## 项目架构

### 模块分层

```
gui/           # 视图层 - PyQt6 界面组件
    ↓
core/          # 业务层 - 核心逻辑
    ↓
data/          # 数据层 - SQLite 持久化
```

### 模块详解

#### core/ - 核心业务逻辑

| 模块 | 功能 |
|------|------|
| `task_manager.py` | 任务 CRUD、象限逻辑、任务完成管理 |
| `pomodoro_timer.py` | 倒计时逻辑、状态管理、回调机制 |
| `statistics.py` | 日/月统计、历史数据聚合 |

#### data/ - 数据持久化

| 模块 | 功能 |
|------|------|
| `storage.py` | SQLite 操作（任务、会话、日志、心得） |

**线程安全**: 所有数据库操作使用 `threading.Lock` 保护

#### gui/ - 界面组件

| 模块 | 功能 |
|------|------|
| `responsive_window.py` | 主窗口，响应式布局协调 |
| `optimized_quadrants_view.py` | 四象限任务列表 |
| `optimized_timer_panel.py` | 番茄钟控制面板 |
| `responsive_history_view.py` | 历史日历 + 日期详情 |
| `dashboard.py` | 今日统计仪表板 |
| `create_task_dialog.py` | 创建任务对话框 |
| `edit_task_dialog.py` | 编辑任务对话框 |
| `styles.py` | 全局颜色、间距样式常量 |

#### utils/ - 工具模块

| 模块 | 功能 |
|------|------|
| `logger.py` | 日志条目创建与检索 |

---

## 数据模型

### Tasks 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| description | TEXT | 任务描述 |
| created_date | TEXT | 创建日期 (YYYY-MM-DD) |
| estimated_pomodoros | INTEGER | 预计番茄钟数 |
| quadrant | INTEGER | 象限 (0-3) |
| completed_date | TEXT | 完成日期 |
| actual_pomodoros | INTEGER | 实际番茄钟数 |
| is_completed | BOOLEAN | 是否完成 |

**象限定义**:
- `0` = 重要紧急
- `1` = 重要不紧急
- `2` = 紧急不重要
- `3` = 不紧急不重要

### Pomodoro Sessions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| task_id | INTEGER | 关联任务 ID |
| start_time | TEXT | 开始时间 |
| end_time | TEXT | 结束时间 |
| duration | INTEGER | 时长（分钟） |
| status | TEXT | 状态 (completed/abandoned/force_completed) |
| date | TEXT | 日期 (YYYY-MM-DD) |

### Logs 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| content | TEXT | 日志内容 |
| timestamp | TEXT | 时间戳 |
| date | TEXT | 日期 |

### Reflections 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| date | TEXT | 日期（唯一）|
| content | TEXT | 心得内容 |

---

## 关键实现细节

### 计时器逻辑

**状态机**:
```
READY → RUNNING → PAUSED → RUNNING → COMPLETED
                    ↓
                 ABANDONED
```

**关键点**:
- 计时器运行在独立线程 (`threading.Thread`)
- 使用 `threading.Event` 控制停止和暂停
- **只有正常完成的番茄钟** (status='completed') 才会计入统计
- 强制完成用于中断后手动确认

### 任务-计时器联动

1. 任务选择器仅显示未完成任务（按象限分组）
2. 选中任务在计时器运行时高亮显示
3. 番茄钟正常完成时：
   - `task.actual_pomodoros += 1`
   - `daily_total += 1`
   - 触发 UI 刷新信号

### 日历历史视图

**默认范围**: 2026-01-01 至今

**视觉编码**:
- 无番茄钟日：灰色格子
- 有番茄钟日：蓝色高亮 + 显示数量

**日期详情面板**:
- 当日总番茄钟数
- 当日完成的任务列表（含番茄钟明细）
- 截至该日结束时各象限待办数量快照
- 当日日志列表

### 响应式布局

**断点**:
- `BREAKPOINT_WIDE = 1400` px
- `MIN_WIDTH = 1280` px
- `MIN_HEIGHT = 800` px

**宽屏模式（≥1400px）**: 左:中:右 = 25:45:30
**中屏模式（<1400px）**: 左:中:右 = 28:47:25

**自适应策略**:
- 使用 `QSplitter` 实现可拖动分割线
- 各栏内容区域使用 `QScrollArea` 独立滚动
- 监听 `QEvent.Type.Resize` 动态调整布局

---

## 设计模式

### 1. 观察者模式
- **实现**: PyQt6 信号/槽机制
- **用途**: 计时器状态变化 → UI 更新
  ```python
  self.timer.set_state_change_callback(self.on_timer_state_changed)
  self.timer.set_complete_callback(self.on_timer_complete)
  ```

### 2. 仓储模式
- **实现**: `Storage` 类封装所有 SQLite 操作
- **好处**: 业务逻辑与数据库解耦，易于测试

### 3. MVC 变体
- **Model**: Core 模块（Task, PomodoroTimer, Statistics）
- **View**: GUI 模块（PyQt6 组件）
- **Controller**: GUI 事件处理 + Core 业务逻辑

---

## 快捷键

| 快捷键 | 功能 | 实现位置 |
|--------|------|----------|
| `Ctrl+P` | 开始/暂停番茄钟 | `ResponsiveWindow.setup_shortcuts()` |
| `Ctrl+S` | 停止/废弃当前番茄钟 | `ResponsiveWindow.setup_shortcuts()` |
| `Ctrl+E` | 导出数据 | 菜单栏 → 文件 |
| `Ctrl+R` | 刷新界面 | 菜单栏 → 编辑 |
| `Ctrl+Q` | 退出应用 | 菜单栏 → 文件 |

---

## 测试策略

### 单元测试

| 文件 | 覆盖内容 |
|------|----------|
| `test_task_manager.py` | 任务 CRUD、象限操作、完成逻辑 |
| `test_pomodoro_timer.py` | 状态转换、回调执行 |
| `test_statistics.py` | 日/月计算、任务聚合 |

### 集成测试

| 文件 | 覆盖场景 |
|------|----------|
| `test_integration.py` | 完整工作流：创建任务 → 启动番茄钟 → 完成 → 验证统计 |

### UI 测试

使用 `pytest-qt` 测试关键交互路径：
- 任务创建
- 计时器控制
- 日历导航

---

## 系统集成 (macOS)

### 桌面通知

使用 AppleScript 显示系统通知：
```python
subprocess.run([
    'osascript',
    '-e', f'display notification "{message}" with title "{title}"'
])
```

### 菜单栏应用（可选扩展）

建议使用 `pystray` 或 `rumps` 实现菜单栏图标

---

## 数据持久化

### 数据库位置

```
项目根目录/pomodoro.db
```

### 自动保存

- 应用退出时自动调用 `storage.close()`
- 所有数据库操作即时提交（auto-commit）

### 备份与恢复

**备份**:
```bash
cp pomodoro.db pomodoro.db.backup_$(date +%Y%m%d)
```

**应用内导出**: 文件 → 导出数据 (JSON)

**详情**: 参考 [DATA_LOCATION.md](DATA_LOCATION.md)

---

## 故障排查

### 常见问题

**Q: PyQt6 插件加载失败**
```python
# main_responsive.py 已包含修复
def setup_qt_plugin_path():
    if sys.platform == 'darwin':
        os.environ['QT_PLUGIN_PATH'] = '/opt/homebrew/anaconda3/lib/python3.11/site-packages/PyQt6/Qt6/plugins'
```

**Q: 计时器不准**
- 确保计时线程正常运行
- 检查 `time.sleep()` 是否被中断

**Q: 数据库锁定**
- 所有数据库操作已使用 `threading.Lock` 保护
- 避免在信号处理中直接执行耗时查询

---

## 未来扩展方向

1. **菜单栏应用**: 快速启动/暂停
2. **番茄钟统计图表**: 使用 `matplotlib` 或 `pyqtgraph`
3. **任务标签系统**: 支持多维度分类
4. **番茄钟休息提醒**: 长休息（15分钟）vs 短休息（5分钟）
5. **数据同步**: 云端备份支持
6. **多语言**: 英文/中文切换

---

## 贡献指南

1. 遵循现有代码风格
2. 为新功能添加单元测试
3. 更新相关文档
4. 提交前运行 `pytest` 确保测试通过

---

## 许可证

MIT License
