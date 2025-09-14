"""
LinkedIn职位搜索和数据抓取模块
"""

import asyncio
import logging
import random
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from urllib.parse import urlencode, quote_plus
import re

from src.utils.logger import get_logger

logger = get_logger(__name__)

class LinkedInScraper:
    """LinkedIn职位抓取器"""

    def __init__(self, browser_config: Dict):
        self.config = browser_config
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False

    async def initialize(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                slow_mo=self.config.get('slow_mo', 500)
            )

            context = await self.browser.new_context(
                viewport={
                    'width': self.config.get('window_width', 1920),
                    'height': self.config.get('window_height', 1080)
                },
                user_agent=self.config.get('user_agent')
            )

            self.page = await context.new_page()

            # 设置超时
            self.page.set_default_timeout(self.config.get('page_timeout', 30000))

            logger.info("LinkedIn scraper initialized")

        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            raise

    async def search_jobs(self, keywords: str, location: str = "", limit: int = 10) -> List[Dict]:
        """搜索LinkedIn职位

        Args:
            keywords: 搜索关键词
            location: 工作地点
            limit: 返回结果数量限制

        Returns:
            职位信息列表
        """
        if not self.page:
            await self.initialize()

        try:
            # 构建搜索URL
            search_params = {
                'keywords': keywords,
                'location': location,
                'f_LF': 'f_AL',  # Easy Apply filter
                'sortBy': 'DD'   # Date posted (newest first)
            }

            # 过滤空参数
            search_params = {k: v for k, v in search_params.items() if v}
            search_url = f"https://www.linkedin.com/jobs/search/?{urlencode(search_params)}"

            logger.info(f"搜索LinkedIn职位: {search_url}")

            # 访问搜索页面
            await self.page.goto(search_url, wait_until='networkidle')

            # 等待职位列表加载
            try:
                await self.page.wait_for_selector('.job-search-card', timeout=10000)
            except Exception:
                logger.warning("未找到职位搜索结果")
                return []

            # 滚动页面加载更多职位
            await self._scroll_to_load_jobs()

            # 提取职位信息
            jobs = []
            job_cards = await self.page.query_selector_all('.job-search-card')

            for i, card in enumerate(job_cards[:limit]):
                if job_data := await self._extract_job_data(card):
                    job_data['platform'] = 'linkedin'
                    jobs.append(job_data)

                # 随机延迟避免被检测
                await asyncio.sleep(random.uniform(0.5, 1.5))

            logger.info(f"成功抓取 {len(jobs)} 个LinkedIn职位")
            return jobs

        except Exception as e:
            logger.error(f"LinkedIn职位搜索失败: {e}")
            return []

    async def _scroll_to_load_jobs(self):
        """滚动页面加载更多职位"""
        try:
            for _ in range(3):  # 滚动3次
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                # 检查是否有"显示更多"按钮并点击
                show_more_button = await self.page.query_selector('button[aria-label="显示更多职位"]')
                if show_more_button:
                    await show_more_button.click()
                    await asyncio.sleep(2)

        except Exception as e:
            logger.warning(f"滚动加载更多职位失败: {e}")

    async def _extract_job_data(self, card) -> Optional[Dict]:
        """从职位卡片中提取数据"""
        try:
            # 提取标题
            title_elem = await card.query_selector('.base-search-card__title')
            title = await title_elem.inner_text() if title_elem else "N/A"

            # 提取公司名称
            company_elem = await card.query_selector('.base-search-card__subtitle')
            company = await company_elem.inner_text() if company_elem else "N/A"

            # 提取地点
            location_elem = await card.query_selector('.job-search-card__location')
            location = await location_elem.inner_text() if location_elem else "N/A"

            # 提取职位链接
            link_elem = await card.query_selector('a[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
            url = await link_elem.get_attribute('href') if link_elem else ""

            # 确保URL是完整的
            if url and not url.startswith('http'):
                url = f"https://www.linkedin.com{url}"

            # 检查是否支持Easy Apply
            easy_apply = await self._check_easy_apply(card)

            # 提取薪资信息（如果有）
            salary_elem = await card.query_selector('.job-search-card__salary-info')
            salary_range = await salary_elem.inner_text() if salary_elem else ""

            # 提取发布时间
            time_elem = await card.query_selector('time')
            posted_date = await time_elem.get_attribute('datetime') if time_elem else ""

            return {
                "title": self._clean_text(title),
                "company": self._clean_text(company),
                "location": self._clean_text(location),
                "url": url,
                "salary_range": self._clean_text(salary_range),
                "posted_date": posted_date,
                "easy_apply": easy_apply,
                "scraped_at": asyncio.get_event_loop().time()
            }

        except Exception as e:
            logger.warning(f"提取职位数据失败: {e}")
            return None

    async def _check_easy_apply(self, card) -> bool:
        """检查是否支持Easy Apply"""
        try:
            # 检查Easy Apply标记
            easy_apply_elem = await card.query_selector('[data-tracking-control-name*="easy_apply"]')
            if easy_apply_elem:
                return True

            # 检查文本中是否包含"简单申请"或"Easy Apply"
            text_content = await card.inner_text()
            return "简单申请" in text_content or "Easy Apply" in text_content

        except Exception:
            return False

    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())

        # 移除特殊字符
        text = re.sub(r'[^\w\s\-.,()$€£¥]', '', text)

        return text

    async def get_job_details(self, job_url: str) -> Optional[Dict]:
        """获取职位详细信息"""
        if not self.page:
            await self.initialize()

        try:
            await self.page.goto(job_url, wait_until='networkidle')

            # 等待页面加载
            await self.page.wait_for_selector('.show-more-less-html__markup', timeout=10000)

            # 提取职位描述
            description_elem = await self.page.query_selector('.show-more-less-html__markup')
            description = await description_elem.inner_text() if description_elem else ""

            # 提取职位要求
            requirements = ""
            criteria_items = await self.page.query_selector_all('.description__job-criteria-item')
            for item in criteria_items:
                criteria_text = await item.inner_text()
                requirements += f"{criteria_text}\n"

            # 提取公司信息
            company_elem = await self.page.query_selector('.topcard__org-name-link')
            company = await company_elem.inner_text() if company_elem else ""

            return {
                "description": self._clean_text(description),
                "requirements": self._clean_text(requirements),
                "company": self._clean_text(company)
            }

        except Exception as e:
            logger.error(f"获取职位详情失败: {e}")
            return None

    async def check_easy_apply_available(self, job_url: str) -> bool:
        """检查职位是否支持Easy Apply"""
        if not self.page:
            await self.initialize()

        try:
            await self.page.goto(job_url, wait_until='networkidle')

            # 查找Easy Apply按钮
            easy_apply_button = await self.page.query_selector('button[data-tracking-control-name*="easy_apply"]')
            return easy_apply_button is not None

        except Exception as e:
            logger.error(f"检查Easy Apply状态失败: {e}")
            return False

    async def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("LinkedIn scraper closed")

        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

if __name__ == "__main__":
    async def test_linkedin_scraper():
        """测试LinkedIn抓取器"""
        config = {
            'headless': False,
            'slow_mo': 1000,
            'window_width': 1920,
            'window_height': 1080
        }

        async with LinkedInScraper(config) as scraper:
            jobs = await scraper.search_jobs("Python Developer", "San Francisco", 5)

            print(f"找到 {len(jobs)} 个职位:")
            for job in jobs:
                print(f"- {job['title']} at {job['company']}")
                print(f"  Location: {job['location']}")
                print(f"  Easy Apply: {job['easy_apply']}")
                print(f"  URL: {job['url']}")
                print()

    asyncio.run(test_linkedin_scraper())