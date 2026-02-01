#!/bin/bash
# 番茄钟效率工具 - 响应式布局版启动脚本

echo "=========================================="
echo "   番茄钟效率工具 (Pomodoro Focus Pro)"
echo "   响应式布局版 v3.0"
echo "=========================================="
echo ""

# 设置 PyQt6 插件路径
if [[ "$OSTYPE" == "darwin" ]]; then
    export QT_PLUGIN_PATH=/opt/homebrew/anaconda3/lib/python3.11/site-packages/PyQt6/Qt6/plugins
    echo "✅ PyQt6 插件路径已设置"
fi

echo ""
echo "🎨 响应式布局特性："
echo ""
echo "  ✓ 三层视觉结构："
echo "    - 第一优先级：番茄钟执行区（始终完整显示）"
echo "    - 第二优先级：今日概况（可滚动）"
echo "    - 第三优先级：历史记录（可折叠）"
echo ""
echo "  ✓ 响应式断点："
echo "    - 宽屏模式（≥1400px）：三栏并列，比例30:50:20"
echo "    - 中屏模式（<1400px）：压缩右侧，比例35:50:15"
echo ""
echo "  ✓ 自适应特性："
echo "    - 所有模块使用QScrollArea独立滚动"
echo "    - 窗口缩放时自动调整布局"
echo "    - 最小支持1280×800分辨率"
echo "    - 内容超出时显示滚动条，禁止裁切"
echo ""
echo "  ✓ 优雅布局："
echo "    - 使用留白区分模块，而非强边框"
echo "    - 拖动分割线可调整各栏宽度"
echo "    - 避免大面积空白+小块内容失衡"
echo ""
echo "🚀 启动应用..."
echo ""

# 启动应用
python3 main_responsive.py

echo ""
echo "=========================================="
echo "应用已退出"
echo "=========================================="
