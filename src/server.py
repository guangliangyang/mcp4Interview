#!/usr/bin/env python3
"""
MCP 智能简历投递助手服务器
专为LinkedIn和SEEK平台设计的自动化求职工具
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import aiosqlite

from src.config.settings import Settings
from src.database.models import DatabaseManager
from src.utils.logger import setup_logger

# 配置日志
logger = setup_logger(__name__)

class JobApplierMCPServer:
    """MCP智能简历投递助手服务器"""

    def __init__(self):
        self.server = Server("job-applier")
        self.settings = Settings()
        self.db_manager = DatabaseManager(self.settings.database.path)

        # 注册MCP工具
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def _register_tools(self):
        """注册所有MCP工具函数"""

        # 职位搜索和筛选
        @self.server.tool("search_jobs")
        async def search_jobs(
            platform: str,
            keywords: str,
            location: str = "",
            salary_min: int = 0,
            job_type: str = "all",
            limit: int = 10
        ) -> List[TextContent]:
            """搜索职位信息

            Args:
                platform: 平台名称 (linkedin/seek)
                keywords: 搜索关键词
                location: 工作地点
                salary_min: 最低薪资要求
                job_type: 职位类型
                limit: 返回结果数量限制
            """
            try:
                from src.platforms.linkedin.scraper import LinkedInScraper
                from src.platforms.seek.scraper import SeekScraper

                if platform.lower() == "linkedin":
                    scraper = LinkedInScraper(self.settings.browser.dict())
                    results = await scraper.search_jobs(keywords, location, limit)
                elif platform.lower() == "seek":
                    scraper = SeekScraper(self.settings.browser.dict())
                    results = await scraper.search_jobs(keywords, location, limit)
                else:
                    return [TextContent(type="text", text=f"不支持的平台: {platform}")]

                # 保存职位信息到数据库
                for job in results:
                    await self.db_manager.save_job_listing(job)

                summary = f"在 {platform} 上找到 {len(results)} 个职位:\n\n"
                for i, job in enumerate(results, 1):
                    summary += f"{i}. **{job['title']}** at {job['company']}\n"
                    summary += f"   📍 {job['location']}\n"
                    if job.get('easy_apply'):
                        summary += f"   ✅ Easy Apply\n"
                    summary += f"   🔗 {job['url']}\n\n"

                return [TextContent(type="text", text=summary)]

            except Exception as e:
                logger.error(f"职位搜索失败: {str(e)}")
                return [TextContent(type="text", text=f"搜索失败: {str(e)}")]

        @self.server.tool("analyze_job_match")
        async def analyze_job_match(
            job_description: str,
            resume_path: str = ""
        ) -> List[TextContent]:
            """分析职位匹配度"""
            try:
                from src.ai.job_matcher import JobMatcher

                matcher = JobMatcher(self.settings.ai)
                analysis = await matcher.analyze_match(job_description, resume_path)

                return [TextContent(type="text", text=analysis)]

            except Exception as e:
                logger.error(f"职位匹配分析失败: {str(e)}")
                return [TextContent(type="text", text=f"分析失败: {str(e)}")]

        # 智能内容生成
        @self.server.tool("generate_cover_letter")
        async def generate_cover_letter(
            job_description: str,
            company_name: str,
            position_title: str,
            resume_summary: str = ""
        ) -> List[TextContent]:
            """生成个性化求职信"""
            try:
                from src.ai.content_generator import ContentGenerator

                generator = ContentGenerator(self.settings.ai)
                cover_letter = await generator.generate_cover_letter(
                    job_description, company_name, position_title, resume_summary
                )

                # 保存求职信
                await self._save_cover_letter(company_name, position_title, cover_letter)

                return [TextContent(type="text", text=cover_letter)]

            except Exception as e:
                logger.error(f"求职信生成失败: {str(e)}")
                return [TextContent(type="text", text=f"生成失败: {str(e)}")]

        @self.server.tool("optimize_keywords")
        async def optimize_keywords(
            content: str,
            job_posting: str
        ) -> List[TextContent]:
            """优化关键词匹配"""
            try:
                from src.ai.resume_optimizer import ResumeOptimizer

                optimizer = ResumeOptimizer(self.settings.ai)
                optimized_content = await optimizer.optimize_keywords(content, job_posting)

                return [TextContent(type="text", text=optimized_content)]

            except Exception as e:
                logger.error(f"关键词优化失败: {str(e)}")
                return [TextContent(type="text", text=f"优化失败: {str(e)}")]

        # 自动申请流程
        @self.server.tool("auto_apply_linkedin")
        async def auto_apply_linkedin(
            job_url: str,
            cover_letter: str = "",
            custom_answers: str = "{}"
        ) -> List[TextContent]:
            """自动申请LinkedIn职位"""
            try:
                from src.platforms.linkedin.applier import LinkedInApplier

                applier = LinkedInApplier(self.settings.browser.dict())
                answers_dict = json.loads(custom_answers) if custom_answers else {}

                result = await applier.apply_to_job(job_url, cover_letter, answers_dict)

                # 记录申请状态
                await self.db_manager.save_application(
                    job_url=job_url,
                    platform="linkedin",
                    status=result.get('status', 'failed'),
                    cover_letter=cover_letter,
                    notes=result.get('message', '')
                )

                return [TextContent(type="text", text=f"申请结果: {result}")]

            except Exception as e:
                logger.error(f"LinkedIn申请失败: {str(e)}")
                return [TextContent(type="text", text=f"申请失败: {str(e)}")]

        # 投递管理
        @self.server.tool("track_applications")
        async def track_applications(
            status_filter: str = "all",
            days_back: int = 30
        ) -> List[TextContent]:
            """跟踪申请状态"""
            try:
                applications = await self.db_manager.get_applications(status_filter, days_back)
                summary = self._format_application_summary(applications)

                return [TextContent(type="text", text=summary)]

            except Exception as e:
                logger.error(f"获取申请数据失败: {str(e)}")
                return [TextContent(type="text", text=f"获取数据失败: {str(e)}")]

        @self.server.tool("update_application_status")
        async def update_application_status(
            job_url: str,
            status: str,
            notes: str = ""
        ) -> List[TextContent]:
            """更新申请状态"""
            try:
                success = await self.db_manager.update_application_status(job_url, status, notes)

                if success:
                    return [TextContent(type="text", text=f"已更新申请状态为: {status}")]
                else:
                    return [TextContent(type="text", text="更新失败，请检查职位URL")]

            except Exception as e:
                logger.error(f"更新申请状态失败: {str(e)}")
                return [TextContent(type="text", text=f"更新失败: {str(e)}")]

        @self.server.tool("generate_application_report")
        async def generate_application_report(
            date_range: str = "30"
        ) -> List[TextContent]:
            """生成申请报告"""
            try:
                days = int(date_range)
                report = await self.db_manager.generate_report(days)

                return [TextContent(type="text", text=report)]

            except Exception as e:
                logger.error(f"生成报告失败: {str(e)}")
                return [TextContent(type="text", text=f"生成报告失败: {str(e)}")]

        @self.server.tool("auto_apply_seek")
        async def auto_apply_seek(
            job_url: str,
            cover_letter: str,
            additional_info: Dict[str, str] = {}
        ) -> List[TextContent]:
            """SEEK平台自动投递"""
            try:
                from src.platforms.seek.applier import SeekApplier

                applier = SeekApplier(self.settings.browser.dict())
                result = await applier.apply_to_job(job_url, cover_letter, additional_info)

                if result.get('success'):
                    await self.db_manager.save_application_result(result)
                    return [TextContent(type="text", text=f"✅ SEEK投递成功: {result.get('message', '已完成申请')}")]
                else:
                    return [TextContent(type="text", text=f"❌ SEEK投递失败: {result.get('error', '未知错误')}")]

            except Exception as e:
                logger.error(f"SEEK投递失败: {str(e)}")
                return [TextContent(type="text", text=f"投递失败: {str(e)}")]

        @self.server.tool("customize_resume")
        async def customize_resume(
            base_resume: str,
            job_requirements: str,
            output_format: str = "text"
        ) -> List[TextContent]:
            """根据职位要求定制简历"""
            try:
                from src.ai.resume_optimizer import ResumeOptimizer

                optimizer = ResumeOptimizer(self.settings.ai)
                optimized_resume = await optimizer.optimize_resume(base_resume, job_requirements)

                result = f"🎯 **定制化简历生成完成**\n\n{optimized_resume}"
                return [TextContent(type="text", text=result)]

            except Exception as e:
                logger.error(f"简历定制失败: {str(e)}")
                return [TextContent(type="text", text=f"定制失败: {str(e)}")]

        @self.server.tool("filter_applied_jobs")
        async def filter_applied_jobs(
            job_urls: List[str]
        ) -> List[TextContent]:
            """过滤已申请的职位"""
            try:
                filtered_urls = await self.db_manager.filter_applied_jobs(job_urls)

                filtered_count = len(job_urls) - len(filtered_urls)
                result = f"🔍 **职位过滤完成**\n\n"
                result += f"原始职位数: {len(job_urls)}\n"
                result += f"已申请职位: {filtered_count}\n"
                result += f"可申请职位: {len(filtered_urls)}\n\n"

                if filtered_urls:
                    result += "**可申请职位列表:**\n"
                    for i, url in enumerate(filtered_urls, 1):
                        result += f"{i}. {url}\n"

                return [TextContent(type="text", text=result)]

            except Exception as e:
                logger.error(f"职位过滤失败: {str(e)}")
                return [TextContent(type="text", text=f"过滤失败: {str(e)}")]

        @self.server.tool("optimize_keywords")
        async def optimize_keywords(
            content: str,
            job_posting: str,
            content_type: str = "resume"
        ) -> List[TextContent]:
            """优化关键词以提高ATS通过率"""
            try:
                from src.ai.content_generator import ContentGenerator

                generator = ContentGenerator(self.settings.ai)
                optimized_content = await generator.optimize_keywords(content, job_posting, content_type)

                result = f"🔍 **关键词优化完成**\n\n{optimized_content}"
                return [TextContent(type="text", text=result)]

            except Exception as e:
                logger.error(f"关键词优化失败: {str(e)}")
                return [TextContent(type="text", text=f"优化失败: {str(e)}")]

        @self.server.tool("handle_application_questions")
        async def handle_application_questions(
            questions: List[str],
            job_context: str = "",
            user_profile: str = ""
        ) -> List[TextContent]:
            """智能回答申请问题"""
            try:
                from src.ai.content_generator import ContentGenerator

                generator = ContentGenerator(self.settings.ai)
                answers = await generator.generate_question_answers(questions, job_context, user_profile)

                result = "❓ **申请问题智能回答**\n\n"
                for i, (question, answer) in enumerate(zip(questions, answers), 1):
                    result += f"**问题 {i}**: {question}\n"
                    result += f"**回答**: {answer}\n\n"

                return [TextContent(type="text", text=result)]

            except Exception as e:
                logger.error(f"问题回答生成失败: {str(e)}")
                return [TextContent(type="text", text=f"回答生成失败: {str(e)}")]

    def _register_resources(self):
        """注册MCP资源"""

        @self.server.resource("templates://cover_letters")
        async def get_cover_letter_templates():
            """获取求职信模板"""
            try:
                templates_path = Path("templates/cover_letter_templates.json")
                if templates_path.exists():
                    with open(templates_path, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                    return json.dumps(templates, indent=2, ensure_ascii=False)
                else:
                    return "求职信模板文件不存在"
            except Exception as e:
                return f"读取模板失败: {str(e)}"

    def _register_prompts(self):
        """注册MCP提示模板"""

        @self.server.prompt("job_application_strategy")
        async def job_application_strategy(company: str, role: str):
            """求职策略提示模板"""
            return f"""
            # 求职策略制定

            ## 目标职位信息
            - **公司**: {company}
            - **职位**: {role}

            ## 策略要点
            1. 研究公司文化和价值观
            2. 分析职位要求和技能匹配度
            3. 准备针对性的面试问题
            4. 定制简历和求职信
            5. 制定跟进计划

            请基于以上信息制定详细的申请策略。
            """

    async def _save_cover_letter(self, company: str, position: str, content: str):
        """保存求职信到文件"""
        try:
            cover_letters_dir = Path("data/cover_letters")
            cover_letters_dir.mkdir(exist_ok=True)

            filename = f"{company}_{position}_{asyncio.get_event_loop().time()}.txt"
            filepath = cover_letters_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"求职信已保存: {filepath}")

        except Exception as e:
            logger.error(f"保存求职信失败: {str(e)}")

    def _format_application_summary(self, applications: List[Dict]) -> str:
        """格式化申请摘要"""
        if not applications:
            return "📊 暂无申请记录"

        total = len(applications)
        platforms = {}
        statuses = {}

        for app in applications:
            platform = app.get('platform', 'unknown')
            status = app.get('status', 'unknown')

            platforms[platform] = platforms.get(platform, 0) + 1
            statuses[status] = statuses.get(status, 0) + 1

        summary = f"📊 **申请统计摘要** (共 {total} 份申请)\n\n"

        summary += "### 平台分布\n"
        for platform, count in platforms.items():
            summary += f"- **{platform.title()}**: {count} 份\n"

        summary += "\n### 状态分布\n"
        for status, count in statuses.items():
            emoji = {"applied": "📝", "viewed": "👀", "interview": "🎯", "offer": "🎉", "rejected": "❌"}.get(status, "📋")
            summary += f"- {emoji} **{status.title()}**: {count} 份\n"

        # 计算成功率
        interviews = statuses.get('interview', 0)
        offers = statuses.get('offer', 0)
        if total > 0:
            interview_rate = (interviews / total) * 100
            offer_rate = (offers / total) * 100
            summary += f"\n### 成功率分析\n"
            summary += f"- 📈 **面试邀请率**: {interview_rate:.1f}%\n"
            summary += f"- 🎯 **Offer获得率**: {offer_rate:.1f}%\n"

        return summary

    async def initialize(self):
        """初始化服务器"""
        try:
            await self.db_manager.initialize()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    async def run(self):
        """启动MCP服务器"""
        try:
            await self.initialize()
            logger.info("🚀 MCP智能简历投递助手启动成功")
            await self.server.run()
        except Exception as e:
            logger.error(f"服务器启动失败: {str(e)}")
            raise

if __name__ == "__main__":
    server = JobApplierMCPServer()
    asyncio.run(server.run())