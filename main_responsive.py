#!/usr/bin/env python3
"""番茄钟效率工具 - 响应式布局版启动器"""

import sys
import os

def setup_qt_plugin_path():
    """设置Qt插件路径（macOS）"""
    if sys.platform == 'darwin':
        from pathlib import Path
        anaconda_plugins = Path('/opt/homebrew/anaconda3/lib/python3.11/site-packages/PyQt6/Qt6/plugins')
        if anaconda_plugins.exists():
            os.environ['QT_PLUGIN_PATH'] = str(anaconda_plugins)
            print("✅ PyQt6 插件路径已设置")

def check_screen_resolution():
    """检查并显示屏幕分辨率信息"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QScreen

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        screen = app.primaryScreen()
        size = screen.size()
        available_size = screen.availableSize()

        print(f"\n📺 屏幕信息:")
        print(f"   完整分辨率: {size.width()}×{size.height()}")
        print(f"   可用分辨率: {available_size.width()}×{available_size.height()}")
        print(f"   建议窗口尺寸: 1440×900 (最小: 1280×800)")

        return size.width(), size.height()
    except Exception as e:
        print(f"⚠️  无法获取屏幕信息: {e}")
        return 1920, 1080  # 默认值

def main():
    """主函数"""
    print("=" * 50)
    print("   番茄钟效率工具 (Pomodoro Focus Pro)")
    print("   响应式布局版 v3.0")
    print("=" * 50)

    # 设置Qt插件路径
    setup_qt_plugin_path()

    # 检查屏幕分辨率
    screen_w, screen_h = check_screen_resolution()

    # 验证最小分辨率要求
    if screen_w < 1280 or screen_h < 800:
        print("\n⚠️  警告: 您的屏幕分辨率低于推荐值 (1280×800)")
        print(f"   当前分辨率: {screen_w}×{screen_h}")
        response = input("   是否仍然尝试启动？(y/n): ")
        if response.lower() != 'y':
            print("   已取消启动")
            return

    print("\n🚀 启动应用...")
    print()

    # 导入Qt模块
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from gui.responsive_window import ResponsiveWindow

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("番茄钟效率工具")
    app.setOrganizationName("PomodoroFocusPro")

    # 设置高DPI支持
    app.setStyleSheet("""
        * {
            font-family: "Helvetica Neue", Arial, sans-serif;
        }
    """)

    # 创建并显示主窗口
    window = ResponsiveWindow()
    window.show()

    # 根据屏幕尺寸智能调整窗口大小
    if screen_w >= 1920 and screen_h >= 1080:
        # 全高清或更高：最大化窗口
        window.showMaximized()
    elif screen_w >= 1440 and screen_h >= 900:
        # 优秀分辨率：使用默认尺寸 (1440×900)
        pass
    else:
        # 较小分辨率：调整到合适的尺寸
        window.resize(max(1280, screen_w - 50), max(800, screen_h - 100))

    print("\n✅ 应用已启动！")
    print(f"   窗口尺寸: {window.width()}×{window.height()}")
    print(f"   布局模式: {'宽屏 (≥1400px)' if window.width() >= 1400 else '中屏 (<1400px)'}")
    print()
    print("💡 提示:")
    print("   - 按 Ctrl+P 开始/暂停番茄钟")
    print("   - 按 Ctrl+S 停止当前番茄钟")
    print("   - 按 Ctrl+R 刷新界面")
    print("   - 拖动分割线可调整各栏宽度")
    print("   - 所有内容区域支持独立滚动")
    print()

    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
