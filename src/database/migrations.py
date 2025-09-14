"""
数据库迁移管理
处理数据库结构变更和数据迁移
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Migration:
    """单个迁移类"""

    def __init__(self, version: str, description: str, up_sql: str, down_sql: str = ""):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.applied_at = None

class DatabaseMigrator:
    """数据库迁移器"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.migrations: List[Migration] = []
        self._initialize_migrations()

    def _initialize_migrations(self):
        """初始化所有迁移"""

        # 迁移 001: 创建基础表结构
        self.migrations.append(Migration(
            version="001_initial_schema",
            description="创建初始数据库表结构",
            up_sql="""
            -- 职位信息表
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
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 申请记录表
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_id TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'applied',
                cover_letter TEXT,
                custom_resume TEXT,
                application_answers JSON,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job_listings(id)
            );

            -- 用户配置表
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                profile_data JSON,
                preferences JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 公司黑名单/白名单
            CREATE TABLE IF NOT EXISTS company_filters (
                company_name TEXT PRIMARY KEY,
                filter_type TEXT CHECK(filter_type IN ('blacklist', 'whitelist')),
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            down_sql="""
            DROP TABLE IF EXISTS company_filters;
            DROP TABLE IF EXISTS applications;
            DROP TABLE IF EXISTS user_profiles;
            DROP TABLE IF EXISTS job_listings;
            """
        ))

        # 迁移 002: 添加求职信表
        self.migrations.append(Migration(
            version="002_add_cover_letters",
            description="添加求职信存储表",
            up_sql="""
            CREATE TABLE IF NOT EXISTS cover_letters (
                id TEXT PRIMARY KEY,
                job_id TEXT,
                user_id TEXT,
                title TEXT,
                content TEXT NOT NULL,
                template_used TEXT,
                variables JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job_listings(id)
            );

            -- 为快速查询添加索引
            CREATE INDEX IF NOT EXISTS idx_cover_letters_job_id ON cover_letters(job_id);
            CREATE INDEX IF NOT EXISTS idx_cover_letters_user_id ON cover_letters(user_id);
            """,
            down_sql="""
            DROP INDEX IF EXISTS idx_cover_letters_user_id;
            DROP INDEX IF EXISTS idx_cover_letters_job_id;
            DROP TABLE IF EXISTS cover_letters;
            """
        ))

        # 迁移 003: 添加索引优化
        self.migrations.append(Migration(
            version="003_add_indexes",
            description="添加查询性能优化索引",
            up_sql="""
            -- job_listings 表索引
            CREATE INDEX IF NOT EXISTS idx_job_listings_platform ON job_listings(platform);
            CREATE INDEX IF NOT EXISTS idx_job_listings_company ON job_listings(company);
            CREATE INDEX IF NOT EXISTS idx_job_listings_posted_date ON job_listings(posted_date);
            CREATE INDEX IF NOT EXISTS idx_job_listings_scraped_at ON job_listings(scraped_at);

            -- applications 表索引
            CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
            CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
            CREATE INDEX IF NOT EXISTS idx_applications_applied_at ON applications(applied_at);

            -- user_profiles 表索引
            CREATE INDEX IF NOT EXISTS idx_user_profiles_platform ON user_profiles(platform);
            CREATE INDEX IF NOT EXISTS idx_user_profiles_updated_at ON user_profiles(updated_at);

            -- company_filters 表索引
            CREATE INDEX IF NOT EXISTS idx_company_filters_type ON company_filters(filter_type);
            """,
            down_sql="""
            DROP INDEX IF EXISTS idx_company_filters_type;
            DROP INDEX IF EXISTS idx_user_profiles_updated_at;
            DROP INDEX IF EXISTS idx_user_profiles_platform;
            DROP INDEX IF EXISTS idx_applications_applied_at;
            DROP INDEX IF EXISTS idx_applications_status;
            DROP INDEX IF EXISTS idx_applications_job_id;
            DROP INDEX IF EXISTS idx_job_listings_scraped_at;
            DROP INDEX IF EXISTS idx_job_listings_posted_date;
            DROP INDEX IF EXISTS idx_job_listings_company;
            DROP INDEX IF EXISTS idx_job_listings_platform;
            """
        ))

        # 迁移 004: 添加应用统计表
        self.migrations.append(Migration(
            version="004_add_statistics",
            description="添加应用统计和性能监控表",
            up_sql="""
            CREATE TABLE IF NOT EXISTS application_statistics (
                id TEXT PRIMARY KEY,
                date DATE NOT NULL,
                platform TEXT NOT NULL,
                total_applications INTEGER DEFAULT 0,
                successful_applications INTEGER DEFAULT 0,
                rejected_applications INTEGER DEFAULT 0,
                pending_applications INTEGER DEFAULT 0,
                interview_invitations INTEGER DEFAULT 0,
                offers_received INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, platform)
            );

            -- 系统性能监控表
            CREATE TABLE IF NOT EXISTS system_logs (
                id TEXT PRIMARY KEY,
                log_level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                additional_data JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 添加相关索引
            CREATE INDEX IF NOT EXISTS idx_app_stats_date ON application_statistics(date);
            CREATE INDEX IF NOT EXISTS idx_app_stats_platform ON application_statistics(platform);
            CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level);
            CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component);
            CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
            """,
            down_sql="""
            DROP INDEX IF EXISTS idx_system_logs_timestamp;
            DROP INDEX IF EXISTS idx_system_logs_component;
            DROP INDEX IF EXISTS idx_system_logs_level;
            DROP INDEX IF EXISTS idx_app_stats_platform;
            DROP INDEX IF EXISTS idx_app_stats_date;
            DROP TABLE IF EXISTS system_logs;
            DROP TABLE IF EXISTS application_statistics;
            """
        ))

    async def create_migration_table(self, conn: sqlite3.Connection):
        """创建迁移记录表"""
        conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

    async def get_applied_migrations(self, conn: sqlite3.Connection) -> List[str]:
        """获取已应用的迁移版本"""
        try:
            cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY applied_at")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # 迁移表不存在，返回空列表
            return []

    async def apply_migration(self, conn: sqlite3.Connection, migration: Migration):
        """应用单个迁移"""
        try:
            logger.info(f"应用迁移: {migration.version} - {migration.description}")

            # 执行迁移SQL
            conn.executescript(migration.up_sql)

            # 记录迁移
            conn.execute(
                "INSERT OR REPLACE INTO schema_migrations (version, description) VALUES (?, ?)",
                (migration.version, migration.description)
            )

            conn.commit()
            logger.info(f"迁移 {migration.version} 应用成功")

        except Exception as e:
            conn.rollback()
            logger.error(f"迁移 {migration.version} 应用失败: {e}")
            raise

    async def rollback_migration(self, conn: sqlite3.Connection, migration: Migration):
        """回滚单个迁移"""
        if not migration.down_sql:
            logger.warning(f"迁移 {migration.version} 没有回滚SQL")
            return

        try:
            logger.info(f"回滚迁移: {migration.version} - {migration.description}")

            # 执行回滚SQL
            conn.executescript(migration.down_sql)

            # 删除迁移记录
            conn.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))

            conn.commit()
            logger.info(f"迁移 {migration.version} 回滚成功")

        except Exception as e:
            conn.rollback()
            logger.error(f"迁移 {migration.version} 回滚失败: {e}")
            raise

    async def migrate_up(self, target_version: str = None):
        """向上迁移到指定版本（或最新版本）"""
        conn = sqlite3.connect(self.db_path)

        try:
            await self.create_migration_table(conn)
            applied_migrations = await self.get_applied_migrations(conn)

            for migration in self.migrations:
                if migration.version in applied_migrations:
                    continue

                if target_version and migration.version == target_version:
                    await self.apply_migration(conn, migration)
                    break
                elif not target_version:
                    await self.apply_migration(conn, migration)
                elif migration.version == target_version:
                    await self.apply_migration(conn, migration)
                    break

            logger.info("数据库迁移完成")

        finally:
            conn.close()

    async def migrate_down(self, target_version: str):
        """向下回滚到指定版本"""
        conn = sqlite3.connect(self.db_path)

        try:
            applied_migrations = await self.get_applied_migrations(conn)

            # 找到需要回滚的迁移（按版本倒序）
            migrations_to_rollback = []
            for migration in reversed(self.migrations):
                if migration.version in applied_migrations:
                    migrations_to_rollback.append(migration)
                    if migration.version == target_version:
                        break

            # 执行回滚
            for migration in migrations_to_rollback[:-1]:  # 不包括目标版本
                await self.rollback_migration(conn, migration)

            logger.info(f"数据库回滚到版本 {target_version} 完成")

        finally:
            conn.close()

    async def get_migration_status(self) -> Dict:
        """获取迁移状态"""
        conn = sqlite3.connect(self.db_path)

        try:
            await self.create_migration_table(conn)
            applied_migrations = await self.get_applied_migrations(conn)

            status = {
                'total_migrations': len(self.migrations),
                'applied_migrations': len(applied_migrations),
                'pending_migrations': [],
                'applied_list': applied_migrations
            }

            for migration in self.migrations:
                if migration.version not in applied_migrations:
                    status['pending_migrations'].append({
                        'version': migration.version,
                        'description': migration.description
                    })

            return status

        finally:
            conn.close()

    def add_migration(self, migration: Migration):
        """添加新迁移"""
        self.migrations.append(migration)

    async def create_migration_file(self, description: str) -> str:
        """创建新的迁移文件模板"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{description.lower().replace(' ', '_')}"

        template = f'''
# 迁移版本: {version}
# 描述: {description}
# 创建时间: {datetime.now().isoformat()}

migration = Migration(
    version="{version}",
    description="{description}",
    up_sql="""
    -- 在此添加向上迁移的SQL语句

    """,
    down_sql="""
    -- 在此添加向下迁移的SQL语句（可选）

    """
)
'''
        return template

# 便捷函数
async def migrate_database(db_path: str, target_version: str = None):
    """迁移数据库到指定版本"""
    migrator = DatabaseMigrator(db_path)
    await migrator.migrate_up(target_version)

async def get_database_status(db_path: str) -> Dict:
    """获取数据库迁移状态"""
    migrator = DatabaseMigrator(db_path)
    return await migrator.get_migration_status()

if __name__ == "__main__":
    import asyncio

    async def main():
        """测试迁移功能"""
        db_path = "test_migrations.db"

        # 运行迁移
        await migrate_database(db_path)

        # 查看状态
        status = await get_database_status(db_path)
        print(f"迁移状态: {status}")

    asyncio.run(main())