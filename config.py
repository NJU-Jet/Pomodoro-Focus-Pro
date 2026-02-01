"""番茄钟配置文件"""

import os


class Config:
    """应用配置"""

    @staticmethod
    def get_timer_duration() -> int:
        """
        获取番茄钟时长（秒）

        优先级：环境变量 > 配置文件 > 默认值

        Returns:
            时长（秒）

        环境变量:
            POMODORO_DURATION_SECONDS: 设置番茄钟时长（秒）
            POMODORO_TEST_MODE: 设置为 'true' 启用10秒测试模式
        """
        # 检查测试模式环境变量
        if os.getenv('POMODORO_TEST_MODE', '').lower() == 'true':
            print("⚠️  测试模式已启用：番茄钟时长 = 10秒")
            return 10

        # 检查自定义时长环境变量
        env_duration = os.getenv('POMODORO_DURATION_SECONDS')
        if env_duration:
            try:
                duration = int(env_duration)
                print(f"ℹ️  使用自定义番茄钟时长: {duration}秒")
                return duration
            except ValueError:
                print(f"⚠️  无效的 POMODORO_DURATION_SECONDS 值: {env_duration}")

        # 默认30分钟
        return 30 * 60

    @staticmethod
    def is_test_mode() -> bool:
        """是否为测试模式"""
        return os.getenv('POMODORO_TEST_MODE', '').lower() == 'true'
