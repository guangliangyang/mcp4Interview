"""
数据库查询操作
定义常用的数据库查询和复杂查询逻辑
"""

import sqlite3
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class QueryBuilder:
    """SQL查询构建器"""

    def __init__(self):
        self.query = ""
        self.params = []

    def select(self, columns: str = "*"):
        self.query = f"SELECT {columns}"
        return self

    def from_table(self, table: str):
        self.query += f" FROM {table}"
        return self

    def where(self, condition: str, *params):
        if "WHERE" not in self.query:
            self.query += " WHERE "
        else:
            self.query += " AND "
        self.query += condition
        self.params.extend(params)
        return self

    def or_where(self, condition: str, *params):
        if "WHERE" not in self.query:
            self.query += " WHERE "
        else:
            self.query += " OR "
        self.query += condition
        self.params.extend(params)
        return self

    def join(self, table: str, condition: str):
        self.query += f" JOIN {table} ON {condition}"
        return self

    def left_join(self, table: str, condition: str):
        self.query += f" LEFT JOIN {table} ON {condition}"
        return self

    def order_by(self, column: str, direction: str = "ASC"):
        self.query += f" ORDER BY {column} {direction}"
        return self

    def limit(self, count: int):
        self.query += f" LIMIT {count}"
        return self

    def offset(self, count: int):
        self.query += f" OFFSET {count}"
        return self

    def group_by(self, column: str):
        self.query += f" GROUP BY {column}"
        return self

    def having(self, condition: str, *params):
        self.query += f" HAVING {condition}"
        self.params.extend(params)
        return self

    def build(self) -> Tuple[str, List]:
        return self.query, self.params

class JobListingsQueries:
    """职位信息查询"""

    @staticmethod
    def create_job_listing() -> str:
        """创建职位记录"""
        return """
        INSERT OR REPLACE INTO job_listings
        (id, platform, title, company, location, salary_range, job_description,
         requirements, posted_date, job_url, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

    @staticmethod
    def get_job_by_url() -> str:
        """根据URL获取职位"""
        return """
        SELECT * FROM job_listings
        WHERE job_url = ?
        """

    @staticmethod
    def search_jobs_by_keywords() -> str:
        """根据关键词搜索职位"""
        return """
        SELECT * FROM job_listings
        WHERE (title LIKE ? OR job_description LIKE ? OR requirements LIKE ?)
        AND platform = ?
        ORDER BY scraped_at DESC
        LIMIT ?
        """

    @staticmethod
    def get_jobs_by_company() -> str:
        """获取指定公司的职位"""
        return """
        SELECT * FROM job_listings
        WHERE company = ?
        ORDER BY posted_date DESC
        """

    @staticmethod
    def get_recent_jobs() -> str:
        """获取最近爬取的职位"""
        return """
        SELECT * FROM job_listings
        WHERE scraped_at >= ?
        AND platform = ?
        ORDER BY scraped_at DESC
        LIMIT ?
        """

    @staticmethod
    def get_jobs_by_location() -> str:
        """按地区查询职位"""
        return """
        SELECT * FROM job_listings
        WHERE location LIKE ?
        ORDER BY posted_date DESC
        """

    @staticmethod
    def get_job_statistics() -> str:
        """获取职位统计数据"""
        return """
        SELECT
            platform,
            COUNT(*) as total_jobs,
            COUNT(DISTINCT company) as unique_companies,
            DATE(MIN(scraped_at)) as earliest_scrape,
            DATE(MAX(scraped_at)) as latest_scrape
        FROM job_listings
        GROUP BY platform
        """

class ApplicationQueries:
    """申请记录查询"""

    @staticmethod
    def create_application() -> str:
        """创建申请记录"""
        return """
        INSERT INTO applications
        (id, job_id, applied_at, status, cover_letter, custom_resume, application_answers, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

    @staticmethod
    def get_application_by_id() -> str:
        """根据ID获取申请记录"""
        return """
        SELECT a.*, j.title as job_title, j.company, j.platform, j.job_url
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE a.id = ?
        """

    @staticmethod
    def get_applications_by_status() -> str:
        """根据状态获取申请"""
        return """
        SELECT a.*, j.title as job_title, j.company, j.platform
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE a.status = ?
        ORDER BY a.applied_at DESC
        """

    @staticmethod
    def get_applications_by_date_range() -> str:
        """获取指定日期范围的申请"""
        return """
        SELECT a.*, j.title as job_title, j.company, j.platform, j.job_url
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE a.applied_at BETWEEN ? AND ?
        ORDER BY a.applied_at DESC
        """

    @staticmethod
    def update_application_status() -> str:
        """更新申请状态"""
        return """
        UPDATE applications
        SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

    @staticmethod
    def get_applied_job_urls() -> str:
        """获取已申请的职位URL"""
        return """
        SELECT DISTINCT j.job_url
        FROM applications a
        JOIN job_listings j ON a.job_id = j.id
        WHERE j.job_url IN ({placeholders})
        """

    @staticmethod
    def get_application_statistics() -> str:
        """获取申请统计"""
        return """
        SELECT
            j.platform,
            a.status,
            COUNT(*) as count,
            DATE(a.applied_at) as application_date
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE a.applied_at >= ?
        GROUP BY j.platform, a.status, DATE(a.applied_at)
        ORDER BY application_date DESC
        """

    @staticmethod
    def get_success_rate_by_platform() -> str:
        """获取各平台成功率"""
        return """
        SELECT
            j.platform,
            COUNT(*) as total_applications,
            SUM(CASE WHEN a.status IN ('interview', 'offer') THEN 1 ELSE 0 END) as successful,
            ROUND(
                (SUM(CASE WHEN a.status IN ('interview', 'offer') THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                2
            ) as success_rate
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE a.applied_at >= ?
        GROUP BY j.platform
        """

class UserProfileQueries:
    """用户配置查询"""

    @staticmethod
    def create_or_update_profile() -> str:
        """创建或更新用户配置"""
        return """
        INSERT OR REPLACE INTO user_profiles
        (id, platform, profile_data, preferences, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """

    @staticmethod
    def get_profile_by_platform() -> str:
        """根据平台获取用户配置"""
        return """
        SELECT * FROM user_profiles
        WHERE platform = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """

    @staticmethod
    def get_all_profiles() -> str:
        """获取所有用户配置"""
        return """
        SELECT * FROM user_profiles
        ORDER BY updated_at DESC
        """

class CompanyFilterQueries:
    """公司过滤查询"""

    @staticmethod
    def add_company_filter() -> str:
        """添加公司过滤规则"""
        return """
        INSERT OR REPLACE INTO company_filters
        (company_name, filter_type, reason, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """

    @staticmethod
    def remove_company_filter() -> str:
        """移除公司过滤规则"""
        return """
        DELETE FROM company_filters
        WHERE company_name = ?
        """

    @staticmethod
    def get_filtered_companies() -> str:
        """获取过滤公司列表"""
        return """
        SELECT * FROM company_filters
        WHERE filter_type = ?
        ORDER BY created_at DESC
        """

    @staticmethod
    def check_company_filter() -> str:
        """检查公司是否被过滤"""
        return """
        SELECT filter_type FROM company_filters
        WHERE company_name = ?
        """

class CoverLetterQueries:
    """求职信查询"""

    @staticmethod
    def create_cover_letter() -> str:
        """创建求职信记录"""
        return """
        INSERT INTO cover_letters
        (id, job_id, user_id, title, content, template_used, variables)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

    @staticmethod
    def get_cover_letter_by_job() -> str:
        """根据职位ID获取求职信"""
        return """
        SELECT * FROM cover_letters
        WHERE job_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """

    @staticmethod
    def get_cover_letters_by_user() -> str:
        """获取用户的求职信"""
        return """
        SELECT cl.*, jl.title as job_title, jl.company
        FROM cover_letters cl
        LEFT JOIN job_listings jl ON cl.job_id = jl.id
        WHERE cl.user_id = ?
        ORDER BY cl.created_at DESC
        LIMIT ?
        """

    @staticmethod
    def update_cover_letter() -> str:
        """更新求职信"""
        return """
        UPDATE cover_letters
        SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

class StatisticsQueries:
    """统计查询"""

    @staticmethod
    def get_daily_application_stats() -> str:
        """获取每日申请统计"""
        return """
        SELECT
            DATE(applied_at) as date,
            j.platform,
            COUNT(*) as applications,
            SUM(CASE WHEN status = 'interview' THEN 1 ELSE 0 END) as interviews,
            SUM(CASE WHEN status = 'offer' THEN 1 ELSE 0 END) as offers
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE applied_at >= ?
        GROUP BY DATE(applied_at), j.platform
        ORDER BY date DESC
        """

    @staticmethod
    def get_company_application_stats() -> str:
        """获取公司申请统计"""
        return """
        SELECT
            j.company,
            COUNT(*) as total_applications,
            SUM(CASE WHEN a.status = 'interview' THEN 1 ELSE 0 END) as interviews,
            SUM(CASE WHEN a.status = 'offer' THEN 1 ELSE 0 END) as offers,
            MAX(a.applied_at) as last_application
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE a.applied_at >= ?
        GROUP BY j.company
        HAVING total_applications > 0
        ORDER BY total_applications DESC
        LIMIT ?
        """

    @staticmethod
    def get_keyword_performance() -> str:
        """获取关键词表现统计"""
        return """
        SELECT
            substr(j.title, 1, 50) as job_title_prefix,
            COUNT(*) as applications,
            AVG(CASE WHEN a.status IN ('interview', 'offer') THEN 1.0 ELSE 0.0 END) as success_rate
        FROM applications a
        LEFT JOIN job_listings j ON a.job_id = j.id
        WHERE a.applied_at >= ?
        GROUP BY substr(j.title, 1, 50)
        HAVING applications >= ?
        ORDER BY success_rate DESC, applications DESC
        """

class DatabaseQueries:
    """数据库查询管理类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.job_listings = JobListingsQueries()
        self.applications = ApplicationQueries()
        self.user_profiles = UserProfileQueries()
        self.company_filters = CompanyFilterQueries()
        self.cover_letters = CoverLetterQueries()
        self.statistics = StatisticsQueries()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """执行查询并返回结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """执行写操作并返回受影响的行数"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(query, params)
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            return affected_rows
        except Exception as e:
            logger.error(f"写操作执行失败: {e}")
            raise

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """执行批量操作"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.executemany(query, params_list)
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            return affected_rows
        except Exception as e:
            logger.error(f"批量操作执行失败: {e}")
            raise

    def build_query(self) -> QueryBuilder:
        """创建查询构建器"""
        return QueryBuilder()

    async def get_complex_application_report(self, days: int = 30) -> Dict:
        """生成复杂的申请报告"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 基础统计
        basic_stats = self.execute_query(
            self.statistics.get_daily_application_stats(),
            (start_date.isoformat(),)
        )

        # 公司统计
        company_stats = self.execute_query(
            self.statistics.get_company_application_stats(),
            (start_date.isoformat(), 20)
        )

        # 成功率统计
        success_rates = self.execute_query(
            self.applications.get_success_rate_by_platform(),
            (start_date.isoformat(),)
        )

        return {
            'period': f'{days} days',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily_stats': basic_stats,
            'company_performance': company_stats,
            'platform_success_rates': success_rates
        }

if __name__ == "__main__":
    # 测试查询
    db_path = "test_queries.db"
    queries = DatabaseQueries(db_path)

    # 测试查询构建器
    builder = queries.build_query()
    query, params = (builder
                    .select("title, company")
                    .from_table("job_listings")
                    .where("platform = ?", "linkedin")
                    .where("scraped_at >= ?", "2024-01-01")
                    .order_by("scraped_at", "DESC")
                    .limit(10)
                    .build())

    print(f"构建的查询: {query}")
    print(f"参数: {params}")