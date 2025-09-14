"""
SEEK职位搜索和数据抓取模块
澳洲求职平台专用
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

class SeekScraper:
    """SEEK职位抓取器"""

    def __init__(self, browser_config: Dict):
        self.config = browser_config
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

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
            self.page.set_default_timeout(self.config.get('page_timeout', 30000))

            logger.info("SEEK scraper initialized")

        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            raise

    async def search_jobs(self, keywords: str, location: str = "Australia", limit: int = 10) -> List[Dict]:
        """搜索SEEK职位

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
                'q': keywords,
                'where': location,
                'sortmode': 'ListedDate',  # 按发布日期排序
            }

            search_url = f"https://www.seek.com.au/jobs?{urlencode(search_params)}"

            logger.info(f"搜索SEEK职位: {search_url}")

            # 访问搜索页面
            await self.page.goto(search_url, wait_until='networkidle')

            # 等待职位列表加载
            try:
                await self.page.wait_for_selector('[data-automation="jobListing"]', timeout=10000)
            except Exception:
                logger.warning("未找到SEEK职位搜索结果")
                return []

            # 滚动页面加载更多职位
            await self._scroll_to_load_jobs()

            # 提取职位信息
            jobs = []
            job_cards = await self.page.query_selector_all('[data-automation="jobListing"]')

            for i, card in enumerate(job_cards[:limit]):
                if job_data := await self._extract_job_data(card):
                    job_data['platform'] = 'seek'
                    jobs.append(job_data)

                # 随机延迟避免被检测
                await asyncio.sleep(random.uniform(0.5, 1.5))

            logger.info(f"成功抓取 {len(jobs)} 个SEEK职位")
            return jobs

        except Exception as e:
            logger.error(f"SEEK职位搜索失败: {e}")
            return []

    async def _scroll_to_load_jobs(self):
        """滚动页面加载更多职位"""
        try:
            for _ in range(3):  # 滚动3次
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                # 检查是否有"Load more jobs"按钮并点击
                load_more_button = await self.page.query_selector('[data-automation="load-more-jobs"]')
                if load_more_button:
                    await load_more_button.click()
                    await asyncio.sleep(3)

        except Exception as e:
            logger.warning(f"滚动加载更多职位失败: {e}")

    async def _extract_job_data(self, card) -> Optional[Dict]:
        """从职位卡片中提取数据"""
        try:
            # 提取标题和链接
            title_elem = await card.query_selector('[data-automation="jobTitle"] a')
            title = await title_elem.inner_text() if title_elem else "N/A"
            url = await title_elem.get_attribute('href') if title_elem else ""

            # 确保URL是完整的
            if url and not url.startswith('http'):
                url = f"https://www.seek.com.au{url}"

            # 提取公司名称
            company_elem = await card.query_selector('[data-automation="jobCompany"]')
            company = await company_elem.inner_text() if company_elem else "N/A"

            # 提取地点
            location_elem = await card.query_selector('[data-automation="jobLocation"]')
            location = await location_elem.inner_text() if location_elem else "N/A"

            # 提取薪资信息
            salary_elem = await card.query_selector('[data-automation="jobSalary"]')
            salary_range = await salary_elem.inner_text() if salary_elem else ""

            # 提取职位类型（全职/兼职等）
            job_type_elem = await card.query_selector('[data-automation="jobClassification"]')
            job_type = await job_type_elem.inner_text() if job_type_elem else ""

            # 提取职位描述片段
            description_elem = await card.query_selector('[data-automation="jobShortDescription"]')
            description = await description_elem.inner_text() if description_elem else ""

            # 提取发布时间
            time_elem = await card.query_selector('[data-automation="jobListingDate"]')
            posted_date = await time_elem.inner_text() if time_elem else ""

            # SEEK通常没有Easy Apply，大多数都需要跳转
            easy_apply = False

            return {
                "title": self._clean_text(title),
                "company": self._clean_text(company),
                "location": self._clean_text(location),
                "url": url,
                "salary_range": self._clean_text(salary_range),
                "job_type": self._clean_text(job_type),
                "description": self._clean_text(description),
                "posted_date": self._parse_posted_date(posted_date),
                "easy_apply": easy_apply,
                "scraped_at": asyncio.get_event_loop().time()
            }

        except Exception as e:
            logger.warning(f"提取SEEK职位数据失败: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())

        # 移除特殊字符，保留货币符号
        text = re.sub(r'[^\w\s\-.,()$€£¥AUD]', '', text)

        return text

    def _parse_posted_date(self, date_text: str) -> str:
        """解析发布日期"""
        if not date_text:
            return ""

        # SEEK的日期格式通常是 "2d ago", "1w ago" 等
        date_text = date_text.lower().strip()

        if 'today' in date_text or 'just now' in date_text:
            return 'today'
        elif 'd ago' in date_text:
            days = re.findall(r'(\d+)d', date_text)
            return f"{days[0]} days ago" if days else date_text
        elif 'w ago' in date_text:
            weeks = re.findall(r'(\d+)w', date_text)
            return f"{weeks[0]} weeks ago" if weeks else date_text
        else:
            return date_text

    async def get_job_details(self, job_url: str) -> Optional[Dict]:
        """获取职位详细信息"""
        if not self.page:
            await self.initialize()

        try:
            await self.page.goto(job_url, wait_until='networkidle')

            # 等待页面加载
            await self.page.wait_for_selector('[data-automation="jobDescription"]', timeout=10000)

            # 提取完整职位描述
            description_elem = await self.page.query_selector('[data-automation="jobDescription"]')
            description = await description_elem.inner_text() if description_elem else ""

            # 提取公司信息
            company_elem = await self.page.query_selector('[data-automation="advertiser-name"]')
            company = await company_elem.inner_text() if company_elem else ""

            # 提取工作类型详情
            work_type_elements = await self.page.query_selector_all('[data-automation="job-detail-work-type"] span')
            work_types = []
            for elem in work_type_elements:
                work_type = await elem.inner_text()
                if work_type.strip():
                    work_types.append(work_type.strip())

            # 提取薪资范围
            salary_elem = await self.page.query_selector('[data-automation="job-detail-salary"]')
            salary_range = await salary_elem.inner_text() if salary_elem else ""

            # 提取公司规模
            company_size_elem = await self.page.query_selector('[data-automation="companySize"]')
            company_size = await company_size_elem.inner_text() if company_size_elem else ""

            return {
                "description": self._clean_text(description),
                "company": self._clean_text(company),
                "work_types": work_types,
                "salary_range": self._clean_text(salary_range),
                "company_size": self._clean_text(company_size)
            }

        except Exception as e:
            logger.error(f"获取SEEK职位详情失败: {e}")
            return None

    async def get_application_url(self, job_url: str) -> Optional[str]:
        """获取申请链接"""
        if not self.page:
            await self.initialize()

        try:
            await self.page.goto(job_url, wait_until='networkidle')

            # 查找申请按钮
            apply_button = await self.page.query_selector('[data-automation="job-apply"]')
            if apply_button:
                apply_url = await apply_button.get_attribute('href')
                if apply_url and not apply_url.startswith('http'):
                    apply_url = f"https://www.seek.com.au{apply_url}"
                return apply_url

            # 备选查找方式
            apply_link = await self.page.query_selector('a[href*="apply"]')
            if apply_link:
                apply_url = await apply_link.get_attribute('href')
                if apply_url and not apply_url.startswith('http'):
                    apply_url = f"https://www.seek.com.au{apply_url}"
                return apply_url

            return None

        except Exception as e:
            logger.error(f"获取申请链接失败: {e}")
            return None

    async def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("SEEK scraper closed")

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
    async def test_seek_scraper():
        """测试SEEK抓取器"""
        config = {
            'headless': False,
            'slow_mo': 1000,
            'window_width': 1920,
            'window_height': 1080
        }

        async with SeekScraper(config) as scraper:
            jobs = await scraper.search_jobs("Python Developer", "Sydney", 5)

            print(f"找到 {len(jobs)} 个SEEK职位:")
            for job in jobs:
                print(f"- {job['title']} at {job['company']}")
                print(f"  Location: {job['location']}")
                print(f"  Salary: {job['salary_range']}")
                print(f"  URL: {job['url']}")
                print()

    asyncio.run(test_seek_scraper())