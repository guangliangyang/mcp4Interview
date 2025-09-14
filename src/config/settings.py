"""
配置管理模块
使用Pydantic进行配置验证和管理
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import os

class DatabaseConfig(BaseModel):
    """数据库配置"""
    path: str = "data/applications.db"
    connection_pool_size: int = 5
    timeout: int = 30

class BrowserConfig(BaseModel):
    """浏览器配置"""
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    window_width: int = 1920
    window_height: int = 1080
    page_timeout: int = 30000
    navigation_timeout: int = 30000
    slow_mo: int = 500

class LinkedInConfig(BaseModel):
    """LinkedIn平台配置"""
    login_url: str = "https://www.linkedin.com/login"
    jobs_search_url: str = "https://www.linkedin.com/jobs/search"
    max_applications_per_hour: int = 30
    delay_between_actions: List[int] = Field(default=[2, 5])
    easy_apply_only: bool = True

class SeekConfig(BaseModel):
    """SEEK平台配置"""
    base_url: str = "https://www.seek.com.au"
    login_url: str = "https://www.seek.com.au/oauth/login"
    jobs_search_url: str = "https://www.seek.com.au/jobs"
    max_applications_per_hour: int = 20
    delay_between_actions: List[int] = Field(default=[3, 7])

class AIConfig(BaseModel):
    """AI服务配置"""
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    default_model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4000
    temperature: float = 0.7

    def __init__(self, **data):
        # 从环境变量读取API密钥
        data["anthropic_api_key"] = data.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        data["openai_api_key"] = data.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
        super().__init__(**data)

class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "data/logs/app.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5

class UserInfo(BaseModel):
    """用户信息配置"""
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    location: str = ""
    github: str = ""
    website: str = ""

class Settings(BaseModel):
    """应用程序设置"""
    database: DatabaseConfig = DatabaseConfig()
    browser: BrowserConfig = BrowserConfig()
    linkedin: LinkedInConfig = LinkedInConfig()
    seek: SeekConfig = SeekConfig()
    ai: AIConfig = AIConfig()
    logging: LoggingConfig = LoggingConfig()
    user_info: UserInfo = UserInfo()

    @classmethod
    def load_from_file(cls, config_path: str = "config.json") -> "Settings":
        """从JSON配置文件加载设置"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return cls(**config_data)
            else:
                # 创建默认配置文件
                settings = cls()
                settings.save_to_file(config_path)
                return settings
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return cls()

    def save_to_file(self, config_path: str = "config.json"):
        """保存设置到JSON文件"""
        try:
            config_data = self.model_dump()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get_ai_client(self):
        """获取AI客户端"""
        if self.ai.anthropic_api_key:
            try:
                import anthropic
                return anthropic.Anthropic(api_key=self.ai.anthropic_api_key)
            except ImportError:
                print("未安装anthropic包")
                return None
        elif self.ai.openai_api_key:
            try:
                import openai
                return openai.OpenAI(api_key=self.ai.openai_api_key)
            except ImportError:
                print("未安装openai包")
                return None
        else:
            print("未配置AI API密钥")
            return None

# 全局设置实例
settings = Settings.load_from_file()

if __name__ == "__main__":
    # 测试配置加载
    settings = Settings.load_from_file()
    print("配置加载成功:")
    print(f"数据库路径: {settings.database.path}")
    print(f"LinkedIn配置: {settings.linkedin.max_applications_per_hour} 申请/小时")
    print(f"AI模型: {settings.ai.default_model}")