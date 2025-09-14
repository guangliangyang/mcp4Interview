"""
反检测工具
实现人工操作模拟和反爬虫检测
"""

import asyncio
import random
import time
from typing import List, Tuple, Dict
from playwright.async_api import Page
import logging

from src.utils.logger import get_logger

logger = get_logger(__name__)

class AntiDetection:
    """反检测工具类"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.request_history: List[float] = []
        self.max_requests_per_hour = self.config.get('max_requests_per_hour', 100)

    async def random_delay(self, min_delay: float = 1.0, max_delay: float = 5.0):
        """随机延迟

        Args:
            min_delay: 最小延迟时间（秒）
            max_delay: 最大延迟时间（秒）
        """
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"随机延迟 {delay:.2f} 秒")
        await asyncio.sleep(delay)

    async def human_like_mouse_movement(self, page: Page, target_x: int, target_y: int):
        """人工鼠标移动模拟

        Args:
            page: 页面实例
            target_x: 目标X坐标
            target_y: 目标Y坐标
        """
        try:
            # 获取当前鼠标位置（模拟）
            current_x, current_y = random.randint(100, 800), random.randint(100, 600)

            # 计算移动路径
            steps = random.randint(5, 15)
            step_x = (target_x - current_x) / steps
            step_y = (target_y - current_y) / steps

            # 模拟鼠标轨迹
            for i in range(steps):
                # 添加随机偏移
                offset_x = random.uniform(-2, 2)
                offset_y = random.uniform(-2, 2)

                x = current_x + (step_x * i) + offset_x
                y = current_y + (step_y * i) + offset_y

                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.01, 0.05))

            # 最终移动到准确位置
            await page.mouse.move(target_x, target_y)

        except Exception as e:
            logger.warning(f"鼠标移动模拟失败: {e}")

    async def human_like_typing(self, page: Page, element_selector: str, text: str):
        """人工输入模拟

        Args:
            page: 页面实例
            element_selector: 元素选择器
            text: 要输入的文本
        """
        try:
            element = await page.query_selector(element_selector)
            if not element:
                logger.warning(f"未找到元素: {element_selector}")
                return

            # 点击元素获得焦点
            await element.click()
            await self.random_delay(0.2, 0.5)

            # 清空现有内容
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Delete')
            await self.random_delay(0.1, 0.3)

            # 逐字符输入
            for char in text:
                await page.keyboard.type(char)

                # 随机输入延迟
                if random.random() < 0.1:  # 10%概率出现较长停顿
                    await self.random_delay(0.5, 1.5)
                else:
                    await asyncio.sleep(random.uniform(0.05, 0.2))

                # 模拟输入错误和修正
                if random.random() < 0.02:  # 2%概率输入错误
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    await page.keyboard.type(wrong_char)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await page.keyboard.press('Backspace')
                    await asyncio.sleep(random.uniform(0.1, 0.2))

        except Exception as e:
            logger.error(f"人工输入模拟失败: {e}")

    async def scroll_with_pauses(self, page: Page, total_distance: int = 1000,
                                direction: str = 'down'):
        """带停顿的滚动

        Args:
            page: 页面实例
            total_distance: 总滚动距离
            direction: 滚动方向 ('up', 'down')
        """
        try:
            scrolled = 0
            while scrolled < total_distance:
                # 随机滚动距离
                scroll_step = random.randint(100, 300)
                if scrolled + scroll_step > total_distance:
                    scroll_step = total_distance - scrolled

                # 执行滚动
                if direction == 'down':
                    await page.evaluate(f'window.scrollBy(0, {scroll_step})')
                else:
                    await page.evaluate(f'window.scrollBy(0, -{scroll_step})')

                scrolled += scroll_step

                # 随机停顿
                await self.random_delay(0.5, 2.0)

                # 随机概率回滚一点（模拟人工浏览行为）
                if random.random() < 0.1:
                    back_scroll = random.randint(50, 150)
                    if direction == 'down':
                        await page.evaluate(f'window.scrollBy(0, -{back_scroll})')
                    else:
                        await page.evaluate(f'window.scrollBy(0, {back_scroll})')
                    await self.random_delay(0.3, 1.0)

        except Exception as e:
            logger.error(f"滚动模拟失败: {e}")

    async def simulate_reading_time(self, content_length: int, wpm: int = 200):
        """模拟阅读时间

        Args:
            content_length: 内容长度（字符数）
            wpm: 每分钟阅读词数
        """
        # 估算词数（假设平均每个词5个字符）
        estimated_words = content_length / 5

        # 计算阅读时间（分钟）
        reading_time_minutes = estimated_words / wpm

        # 转换为秒并添加随机变化
        reading_time_seconds = reading_time_minutes * 60
        actual_time = random.uniform(reading_time_seconds * 0.5, reading_time_seconds * 1.5)

        # 最小阅读时间3秒，最大5分钟
        actual_time = max(3, min(300, actual_time))

        logger.debug(f"模拟阅读时间: {actual_time:.2f} 秒")
        await asyncio.sleep(actual_time)

    def check_rate_limit(self) -> bool:
        """检查请求频率限制

        Returns:
            是否可以发送请求
        """
        current_time = time.time()

        # 清理1小时前的记录
        hour_ago = current_time - 3600
        self.request_history = [t for t in self.request_history if t > hour_ago]

        # 检查是否超过限制
        if len(self.request_history) >= self.max_requests_per_hour:
            logger.warning("请求频率超限，需要等待")
            return False

        # 记录当前请求
        self.request_history.append(current_time)
        return True

    async def wait_for_rate_limit(self):
        """等待到可以发送请求"""
        while not self.check_rate_limit():
            wait_time = random.uniform(300, 900)  # 5-15分钟
            logger.info(f"请求频率限制，等待 {wait_time/60:.1f} 分钟")
            await asyncio.sleep(wait_time)

    async def add_noise_to_behavior(self, page: Page):
        """添加行为噪音（模拟人工浏览）

        Args:
            page: 页面实例
        """
        try:
            noise_actions = [
                self._random_mouse_movements,
                self._random_scrolling,
                self._pause_and_resume,
                self._simulate_tab_switching
            ]

            # 随机选择1-2个噪音动作
            selected_actions = random.sample(noise_actions, random.randint(1, 2))

            for action in selected_actions:
                try:
                    await action(page)
                except Exception as e:
                    logger.debug(f"噪音动作失败: {e}")

        except Exception as e:
            logger.warning(f"添加行为噪音失败: {e}")

    async def _random_mouse_movements(self, page: Page):
        """随机鼠标移动"""
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1200)
            y = random.randint(100, 800)
            await self.human_like_mouse_movement(page, x, y)
            await self.random_delay(0.5, 1.5)

    async def _random_scrolling(self, page: Page):
        """随机滚动"""
        # 随机滚动方向和距离
        direction = random.choice(['up', 'down'])
        distance = random.randint(200, 600)
        await self.scroll_with_pauses(page, distance, direction)

    async def _pause_and_resume(self, page: Page):
        """暂停和恢复（模拟思考）"""
        pause_time = random.uniform(2, 8)
        logger.debug(f"模拟思考暂停: {pause_time:.2f} 秒")
        await asyncio.sleep(pause_time)

    async def _simulate_tab_switching(self, page: Page):
        """模拟标签页切换"""
        try:
            # 模拟失去焦点
            await page.evaluate('window.blur()')
            await self.random_delay(1, 5)

            # 模拟重新获得焦点
            await page.evaluate('window.focus()')
            await self.random_delay(0.5, 2)

        except Exception as e:
            logger.debug(f"模拟标签页切换失败: {e}")

    async def bypass_common_detections(self, page: Page):
        """绕过常见检测机制

        Args:
            page: 页面实例
        """
        try:
            # 注入反检测脚本
            await page.add_init_script("""
                // 隐藏webdriver属性
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 重写navigator.permissions.query
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );

                // 伪装chrome对象
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };

                // 重写插件数组
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // 重写语言设置
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });

                // 伪装屏幕信息
                Object.defineProperty(screen, 'colorDepth', {
                    get: () => 24,
                });

                // 移除自动化标识
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """)

            logger.debug("反检测脚本注入成功")

        except Exception as e:
            logger.warning(f"反检测脚本注入失败: {e}")

    def get_random_viewport(self) -> Tuple[int, int]:
        """获取随机视口大小

        Returns:
            (宽度, 高度)
        """
        viewports = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720)
        ]

        return random.choice(viewports)

    def get_random_user_agent(self) -> str:
        """获取随机User-Agent

        Returns:
            User-Agent字符串
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]

        return random.choice(user_agents)

    async def simulate_human_session(self, page: Page, duration_minutes: int = 5):
        """模拟人工会话

        Args:
            page: 页面实例
            duration_minutes: 会话持续时间（分钟）
        """
        try:
            end_time = time.time() + (duration_minutes * 60)

            while time.time() < end_time:
                # 随机选择行为
                behaviors = [
                    lambda: self._random_scrolling(page),
                    lambda: self._random_mouse_movements(page),
                    lambda: self._pause_and_resume(page),
                    lambda: self.simulate_reading_time(random.randint(100, 500))
                ]

                behavior = random.choice(behaviors)
                await behavior()

                # 随机间隔
                await self.random_delay(5, 30)

            logger.info(f"完成 {duration_minutes} 分钟的人工会话模拟")

        except Exception as e:
            logger.error(f"人工会话模拟失败: {e}")

if __name__ == "__main__":
    async def test_anti_detection():
        """测试反检测工具"""
        from playwright.async_api import async_playwright

        config = {
            'max_requests_per_hour': 50
        }

        anti_detect = AntiDetection(config)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport=anti_detect.get_random_viewport(),
                user_agent=anti_detect.get_random_user_agent()
            )

            page = await context.new_page()
            await anti_detect.bypass_common_detections(page)

            await page.goto('https://example.com')

            # 测试各种反检测功能
            await anti_detect.add_noise_to_behavior(page)
            await anti_detect.human_like_typing(page, 'input', 'test input')
            await anti_detect.scroll_with_pauses(page, 500)

            await browser.close()

        print("反检测工具测试完成")

    # asyncio.run(test_anti_detection())