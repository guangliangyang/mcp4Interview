"""
浏览器管理工具
统一管理浏览器实例和会话
"""

import asyncio
import logging
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import random

from src.utils.logger import get_logger

logger = get_logger(__name__)

class BrowserManager:
    """浏览器管理器"""

    def __init__(self, config: Dict):
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}

    async def initialize(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()

            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                slow_mo=self.config.get('slow_mo', 500),
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )

            logger.info("浏览器管理器初始化成功")

        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            raise

    async def create_context(self, context_name: str, **kwargs) -> BrowserContext:
        """创建浏览器上下文

        Args:
            context_name: 上下文名称
            **kwargs: 上下文配置

        Returns:
            浏览器上下文
        """
        if not self.browser:
            await self.initialize()

        try:
            # 默认配置
            default_config = {
                'viewport': {
                    'width': self.config.get('window_width', 1920),
                    'height': self.config.get('window_height', 1080)
                },
                'user_agent': self.config.get('user_agent', self._get_random_user_agent()),
                'locale': 'en-US',
                'timezone_id': 'America/New_York'
            }

            # 合并用户配置
            context_config = {**default_config, **kwargs}

            # 创建上下文
            context = await self.browser.new_context(**context_config)

            # 设置额外配置
            await self._setup_context(context)

            self.contexts[context_name] = context
            logger.info(f"创建浏览器上下文: {context_name}")

            return context

        except Exception as e:
            logger.error(f"创建浏览器上下文失败: {e}")
            raise

    async def _setup_context(self, context: BrowserContext):
        """设置上下文"""
        try:
            # 设置超时
            context.set_default_timeout(self.config.get('page_timeout', 30000))
            context.set_default_navigation_timeout(self.config.get('navigation_timeout', 30000))

            # 添加初始化脚本（反检测）
            await context.add_init_script("""
                // 隐藏webdriver属性
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 伪装chrome属性
                window.chrome = {
                    runtime: {},
                };

                // 伪装语言
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });

                // 伪装插件
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)

        except Exception as e:
            logger.warning(f"设置上下文失败: {e}")

    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)

    async def create_page(self, context_name: str, page_name: str) -> Page:
        """在指定上下文中创建页面

        Args:
            context_name: 上下文名称
            page_name: 页面名称

        Returns:
            页面实例
        """
        try:
            if context_name not in self.contexts:
                await self.create_context(context_name)

            context = self.contexts[context_name]
            page = await context.new_page()

            # 页面设置
            await self._setup_page(page)

            self.pages[page_name] = page
            logger.info(f"创建页面: {page_name} (上下文: {context_name})")

            return page

        except Exception as e:
            logger.error(f"创建页面失败: {e}")
            raise

    async def _setup_page(self, page: Page):
        """设置页面"""
        try:
            # 设置额外请求头
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            })

            # 阻止某些资源加载以提高速度
            await page.route('**/*.{png,jpg,jpeg,gif,svg,css}', lambda route: route.abort())

        except Exception as e:
            logger.warning(f"设置页面失败: {e}")

    async def get_page(self, page_name: str) -> Optional[Page]:
        """获取页面实例"""
        return self.pages.get(page_name)

    async def get_context(self, context_name: str) -> Optional[BrowserContext]:
        """获取上下文实例"""
        return self.contexts.get(context_name)

    async def close_page(self, page_name: str):
        """关闭指定页面"""
        try:
            if page_name in self.pages:
                await self.pages[page_name].close()
                del self.pages[page_name]
                logger.info(f"关闭页面: {page_name}")

        except Exception as e:
            logger.error(f"关闭页面失败: {e}")

    async def close_context(self, context_name: str):
        """关闭指定上下文"""
        try:
            if context_name in self.contexts:
                # 关闭该上下文的所有页面
                pages_to_close = [name for name, page in self.pages.items()
                                 if page.context == self.contexts[context_name]]

                for page_name in pages_to_close:
                    del self.pages[page_name]

                await self.contexts[context_name].close()
                del self.contexts[context_name]
                logger.info(f"关闭上下文: {context_name}")

        except Exception as e:
            logger.error(f"关闭上下文失败: {e}")

    async def close_all(self):
        """关闭所有浏览器资源"""
        try:
            # 关闭所有页面
            for page_name in list(self.pages.keys()):
                await self.close_page(page_name)

            # 关闭所有上下文
            for context_name in list(self.contexts.keys()):
                await self.close_context(context_name)

            # 关闭浏览器
            if self.browser:
                await self.browser.close()

            # 停止playwright
            if self.playwright:
                await self.playwright.stop()

            logger.info("浏览器管理器已关闭")

        except Exception as e:
            logger.error(f"关闭浏览器管理器失败: {e}")

    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """随机延迟（反检测）"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def human_like_typing(self, page: Page, selector: str, text: str, delay_range: tuple = (50, 150)):
        """人工输入模拟

        Args:
            page: 页面实例
            selector: 元素选择器
            text: 要输入的文本
            delay_range: 输入延迟范围（毫秒）
        """
        try:
            element = await page.query_selector(selector)
            if element:
                # 先清空现有内容
                await element.click()
                await page.keyboard.press('Control+A')

                # 逐字符输入
                for char in text:
                    await element.type(char)
                    delay = random.uniform(delay_range[0], delay_range[1])
                    await asyncio.sleep(delay / 1000)  # 转换为秒

        except Exception as e:
            logger.error(f"人工输入模拟失败: {e}")

    async def human_like_click(self, page: Page, selector: str, offset_range: int = 5):
        """人工点击模拟

        Args:
            page: 页面实例
            selector: 元素选择器
            offset_range: 点击位置偏移范围
        """
        try:
            element = await page.query_selector(selector)
            if element:
                # 获取元素边界
                box = await element.bounding_box()
                if box:
                    # 计算随机点击位置
                    x = box['x'] + box['width'] / 2 + random.uniform(-offset_range, offset_range)
                    y = box['y'] + box['height'] / 2 + random.uniform(-offset_range, offset_range)

                    # 模拟鼠标移动和点击
                    await page.mouse.move(x, y)
                    await self.random_delay(0.1, 0.3)
                    await page.mouse.click(x, y)

        except Exception as e:
            logger.error(f"人工点击模拟失败: {e}")

    async def scroll_page(self, page: Page, direction: str = 'down', distance: int = 500):
        """滚动页面

        Args:
            page: 页面实例
            direction: 滚动方向 ('up', 'down')
            distance: 滚动距离（像素）
        """
        try:
            if direction == 'down':
                await page.evaluate(f'window.scrollBy(0, {distance})')
            elif direction == 'up':
                await page.evaluate(f'window.scrollBy(0, -{distance})')

            await self.random_delay(0.5, 1.5)

        except Exception as e:
            logger.error(f"页面滚动失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_all()

if __name__ == "__main__":
    async def test_browser_manager():
        """测试浏览器管理器"""
        config = {
            'headless': False,
            'slow_mo': 500,
            'window_width': 1920,
            'window_height': 1080,
            'page_timeout': 30000
        }

        async with BrowserManager(config) as browser_manager:
            # 创建上下文和页面
            page = await browser_manager.create_page('test_context', 'test_page')

            # 访问测试页面
            await page.goto('https://example.com')

            # 模拟人工操作
            await browser_manager.random_delay()
            await browser_manager.scroll_page(page, 'down', 300)

            print("浏览器管理器测试完成")

    asyncio.run(test_browser_manager())