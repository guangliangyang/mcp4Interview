"""
数据库模型和管理器
使用SQLite进行数据持久化
"""

import aiosqlite
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "data/applications.db"):
        self.db_path = db_path
        # 确保数据库目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初始化数据库表结构"""
        async with aiosqlite.connect(self.db_path) as db:
            # 创建职位信息表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS job_listings (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    salary_range TEXT,
                    job_description TEXT,
                    requirements TEXT,
                    posted_date DATE,
                    job_url TEXT UNIQUE,
                    easy_apply BOOLEAN DEFAULT FALSE,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建申请记录表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id TEXT PRIMARY KEY,
                    job_id TEXT,
                    job_url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'applied',
                    cover_letter TEXT,
                    custom_resume TEXT,
                    application_answers TEXT,
                    notes TEXT,
                    FOREIGN KEY (job_id) REFERENCES job_listings (id)
                )
            """)

            # 创建用户配置表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    profile_data TEXT,
                    preferences TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建公司过滤表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS company_filters (
                    company_name TEXT PRIMARY KEY,
                    filter_type TEXT NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            await db.execute("CREATE INDEX IF NOT EXISTS idx_job_url ON job_listings(job_url)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_application_status ON applications(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_application_date ON applications(applied_at)")

            await db.commit()
            logger.info("数据库初始化完成")

    async def save_job_listing(self, job_data: Dict[str, Any]) -> str:
        """保存职位信息"""
        try:
            job_id = str(uuid.uuid4())

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO job_listings (
                        id, platform, title, company, location, salary_range,
                        job_description, requirements, job_url, easy_apply
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id,
                    job_data.get('platform', ''),
                    job_data.get('title', ''),
                    job_data.get('company', ''),
                    job_data.get('location', ''),
                    job_data.get('salary_range', ''),
                    job_data.get('description', ''),
                    job_data.get('requirements', ''),
                    job_data.get('url', ''),
                    job_data.get('easy_apply', False)
                ))
                await db.commit()

            logger.info(f"保存职位信息: {job_data.get('title')} at {job_data.get('company')}")
            return job_id

        except Exception as e:
            logger.error(f"保存职位信息失败: {e}")
            return ""

    async def save_application(self, job_url: str, platform: str, status: str = "applied",
                              cover_letter: str = "", notes: str = "") -> str:
        """保存申请记录"""
        try:
            app_id = str(uuid.uuid4())

            # 查找对应的job_id
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT id FROM job_listings WHERE job_url = ?", (job_url,))
                result = await cursor.fetchone()
                job_id = result[0] if result else None

                await db.execute("""
                    INSERT INTO applications (
                        id, job_id, job_url, platform, status, cover_letter, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (app_id, job_id, job_url, platform, status, cover_letter, notes))

                await db.commit()

            logger.info(f"保存申请记录: {job_url} - {status}")
            return app_id

        except Exception as e:
            logger.error(f"保存申请记录失败: {e}")
            return ""

    async def get_applications(self, status_filter: str = "all", days_back: int = 30) -> List[Dict]:
        """获取申请记录"""
        try:
            since_date = datetime.now() - timedelta(days=days_back)

            async with aiosqlite.connect(self.db_path) as db:
                if status_filter == "all":
                    cursor = await db.execute("""
                        SELECT a.*, j.title, j.company
                        FROM applications a
                        LEFT JOIN job_listings j ON a.job_id = j.id
                        WHERE a.applied_at >= ?
                        ORDER BY a.applied_at DESC
                    """, (since_date,))
                else:
                    cursor = await db.execute("""
                        SELECT a.*, j.title, j.company
                        FROM applications a
                        LEFT JOIN job_listings j ON a.job_id = j.id
                        WHERE a.status = ? AND a.applied_at >= ?
                        ORDER BY a.applied_at DESC
                    """, (status_filter, since_date))

                rows = await cursor.fetchall()

                # 转换为字典列表
                columns = [description[0] for description in cursor.description]
                applications = [dict(zip(columns, row)) for row in rows]

            logger.info(f"获取申请记录: {len(applications)} 条")
            return applications

        except Exception as e:
            logger.error(f"获取申请记录失败: {e}")
            return []

    async def update_application_status(self, job_url: str, status: str, notes: str = "") -> bool:
        """更新申请状态"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    UPDATE applications
                    SET status = ?, notes = COALESCE(?, notes)
                    WHERE job_url = ?
                """, (status, notes, job_url))

                await db.commit()
                success = cursor.rowcount > 0

            if success:
                logger.info(f"更新申请状态: {job_url} -> {status}")
            else:
                logger.warning(f"未找到申请记录: {job_url}")

            return success

        except Exception as e:
            logger.error(f"更新申请状态失败: {e}")
            return False

    async def get_job_by_url(self, job_url: str) -> Optional[Dict]:
        """根据URL获取职位信息"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT * FROM job_listings WHERE job_url = ?", (job_url,))
                row = await cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))

            return None

        except Exception as e:
            logger.error(f"获取职位信息失败: {e}")
            return None

    async def check_already_applied(self, job_url: str) -> bool:
        """检查是否已申请该职位"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM applications WHERE job_url = ?", (job_url,))
                result = await cursor.fetchone()
                return result[0] > 0 if result else False

        except Exception as e:
            logger.error(f"检查申请状态失败: {e}")
            return False

    async def add_company_filter(self, company_name: str, filter_type: str, reason: str = ""):
        """添加公司过滤规则"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO company_filters (company_name, filter_type, reason)
                    VALUES (?, ?, ?)
                """, (company_name, filter_type, reason))
                await db.commit()

            logger.info(f"添加公司过滤: {company_name} - {filter_type}")

        except Exception as e:
            logger.error(f"添加公司过滤失败: {e}")

    async def is_company_filtered(self, company_name: str) -> Optional[str]:
        """检查公司是否被过滤"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT filter_type FROM company_filters WHERE company_name = ?
                """, (company_name,))
                result = await cursor.fetchone()
                return result[0] if result else None

        except Exception as e:
            logger.error(f"检查公司过滤状态失败: {e}")
            return None

    async def generate_report(self, days_back: int = 30) -> str:
        """生成申请报告"""
        try:
            applications = await self.get_applications("all", days_back)

            if not applications:
                return f"📊 过去 {days_back} 天内暂无申请记录"

            # 统计数据
            total = len(applications)
            platforms = {}
            statuses = {}
            companies = {}

            for app in applications:
                platform = app.get('platform', 'unknown')
                status = app.get('status', 'unknown')
                company = app.get('company', 'unknown')

                platforms[platform] = platforms.get(platform, 0) + 1
                statuses[status] = statuses.get(status, 0) + 1
                companies[company] = companies.get(company, 0) + 1

            # 生成报告
            report = f"# 📊 申请活动报告 ({days_back} 天)\n\n"
            report += f"**总申请数**: {total}\n\n"

            # 平台分析
            report += "## 📈 平台分布\n"
            for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                report += f"- **{platform.title()}**: {count} 份 ({percentage:.1f}%)\n"

            # 状态分析
            report += "\n## 📋 申请状态\n"
            status_emojis = {
                "applied": "📝", "viewed": "👀", "interview": "🎯",
                "offer": "🎉", "rejected": "❌", "pending": "⏳"
            }
            for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                emoji = status_emojis.get(status, "📋")
                report += f"- {emoji} **{status.title()}**: {count} 份 ({percentage:.1f}%)\n"

            # 成功率分析
            interviews = statuses.get('interview', 0)
            offers = statuses.get('offer', 0)
            interview_rate = (interviews / total) * 100
            offer_rate = (offers / total) * 100

            report += "\n## 🎯 成功率分析\n"
            report += f"- **面试邀请率**: {interview_rate:.1f}% ({interviews}/{total})\n"
            report += f"- **Offer获得率**: {offer_rate:.1f}% ({offers}/{total})\n"

            # 热门公司
            if companies:
                report += "\n## 🏢 申请公司分布 (Top 5)\n"
                top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
                for company, count in top_companies:
                    report += f"- **{company}**: {count} 份\n"

            # 改进建议
            report += "\n## 💡 改进建议\n"
            if interview_rate < 10:
                report += "- 考虑优化简历关键词匹配度\n"
                report += "- 提高求职信个性化程度\n"
            if offer_rate < 5:
                report += "- 加强面试准备和技能提升\n"
                report += "- 针对目标公司做更深入研究\n"

            return report

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return f"生成报告失败: {str(e)}"

    async def filter_applied_jobs(self, job_urls: List[str]) -> List[str]:
        """过滤已申请的职位URL"""
        try:
            if not job_urls:
                return []

            # 构建SQL IN子句的占位符
            placeholders = ",".join("?" * len(job_urls))

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(f"""
                    SELECT DISTINCT j.job_url
                    FROM applications a
                    JOIN job_listings j ON a.job_id = j.id
                    WHERE j.job_url IN ({placeholders})
                """, job_urls)

                applied_urls = set(row[0] for row in await cursor.fetchall())

            # 返回未申请的职位URL
            filtered_urls = [url for url in job_urls if url not in applied_urls]

            logger.info(f"过滤职位URL: {len(job_urls)} -> {len(filtered_urls)}")
            return filtered_urls

        except Exception as e:
            logger.error(f"过滤已申请职位失败: {e}")
            return job_urls  # 出错时返回原始列表

    async def close(self):
        """关闭数据库连接"""
        # SQLite连接自动管理，无需显式关闭
        pass

if __name__ == "__main__":
    import asyncio

    async def test_database():
        """测试数据库功能"""
        db = DatabaseManager("test.db")
        await db.initialize()

        # 测试保存职位
        job_data = {
            'platform': 'linkedin',
            'title': 'Python Developer',
            'company': 'Tech Corp',
            'location': 'San Francisco',
            'url': 'https://linkedin.com/jobs/123',
            'easy_apply': True
        }

        job_id = await db.save_job_listing(job_data)
        print(f"保存职位ID: {job_id}")

        # 测试保存申请
        app_id = await db.save_application(
            job_url='https://linkedin.com/jobs/123',
            platform='linkedin',
            status='applied'
        )
        print(f"保存申请ID: {app_id}")

        # 测试获取申请
        apps = await db.get_applications()
        print(f"获取申请数量: {len(apps)}")

        # 测试生成报告
        report = await db.generate_report()
        print("申请报告:")
        print(report)

    asyncio.run(test_database())