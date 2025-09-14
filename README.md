# MCP智能简历投递助手

一个基于MCP（模型上下文协议）的智能简历投递助手，专门针对LinkedIn和SEEK平台，提供AI驱动的求职信生成、自动化投递和智能管理功能。

## 🌟 核心功能

### 1. 智能工作搜索
- **多平台支持**：LinkedIn和SEEK平台集成
- **智能过滤**：基于薪资、位置、工作类型的精确筛选
- **一键申请检测**：自动识别LinkedIn Easy Apply职位

### 2. AI内容生成
- **智能求职信**：基于工作描述和个人资料生成定制化求职信
- **多模板支持**：软件工程师、数据科学家、产品经理等专业模板
- **平台优化**：针对LinkedIn和SEEK平台的内容长度和语调优化
- **双AI支持**：Claude和OpenAI API双重支持

### 3. 自动化投递
- **LinkedIn Easy Apply**：全自动化投递流程
- **智能问答**：基于预设模板自动回答申请问题
- **人性化操作**：反检测技术确保自然的操作模式
- **投递限制**：遵守平台规则，防止账号风险

### 4. 投递管理
- **全程追踪**：记录每次投递的详细信息
- **状态管理**：实时更新申请状态（已投递、面试中、已拒绝等）
- **数据统计**：投递成功率、回复率等关键指标
- **文件管理**：简历、求职信、附件的集中管理

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+ （用于浏览器自动化）
- SQLite 3.0+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/guangliangyang/mcp4Interview.git
cd mcp4Interview
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **安装Playwright浏览器**
```bash
playwright install chromium
```

4. **配置环境变量**
```bash
cp config/.env.example config/.env
# 编辑.env文件，添加API密钥和配置
```

5. **初始化数据库**
```bash
python -c "from src.database.models import init_db; import asyncio; asyncio.run(init_db())"
```

### 配置说明

在 `config/.env` 文件中配置以下参数：

```env
# AI API配置
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
PRIMARY_AI_PROVIDER=claude  # 或 openai

# LinkedIn配置
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# SEEK配置
SEEK_EMAIL=your_email@example.com
SEEK_PASSWORD=your_password

# 浏览器配置
BROWSER_HEADLESS=true
BROWSER_SLOW_MO=500

# 投递限制
MAX_DAILY_APPLICATIONS=10
MAX_HOURLY_APPLICATIONS=3
```

## 📖 使用指南

### 基本使用

1. **启动MCP服务器**
```bash
python src/server.py
```

2. **搜索工作机会**
```python
# 在Claude Code或支持MCP的客户端中使用
await search_jobs(
    platform="linkedin",
    keywords="python developer",
    location="sydney",
    salary_min=80000
)
```

3. **生成求职信**
```python
await generate_cover_letter(
    job_description="...",
    candidate_profile="...",
    job_title="Software Engineer",
    company_name="Tech Corp"
)
```

4. **自动投递**
```python
await auto_apply_linkedin(
    job_url="https://linkedin.com/jobs/view/123456789",
    cover_letter="Your customized cover letter...",
    additional_info={
        "phone": "+61 4XX XXX XXX",
        "visa_status": "Australian Citizen"
    }
)
```

### 高级功能

#### 批量投递
```python
# 批量搜索并投递匹配的职位
jobs = await search_jobs("linkedin", "data scientist", "melbourne", limit=20)
for job in jobs:
    if job["easy_apply"]:
        cover_letter = await generate_cover_letter(job["description"], your_profile)
        await auto_apply_linkedin(job["url"], cover_letter)
```

#### 投递追踪
```python
# 查看投递历史
applications = await track_applications("linkedin", days_back=30)

# 更新申请状态
await update_application_status("app_123", "interview_scheduled")
```

#### 文件管理
```python
# 上传简历
await upload_resume("/path/to/resume.pdf", "Software_Engineer_Resume")

# 管理求职信模板
templates = await list_cover_letter_templates()
```

## 🛠 技术架构

### 系统组件

```
src/
├── server.py              # MCP服务器主入口
├── config/                # 配置管理
│   ├── settings.py        # Pydantic配置模型
│   └── .env              # 环境变量
├── platforms/            # 平台集成
│   ├── linkedin/         # LinkedIn平台
│   │   ├── scraper.py    # 职位爬取
│   │   └── applier.py    # 自动投递
│   └── seek/            # SEEK平台
├── ai/                  # AI内容生成
│   ├── content_generator.py
│   ├── job_matcher.py
│   └── resume_optimizer.py
├── database/           # 数据库层
│   ├── models.py       # SQLAlchemy模型
│   └── repositories.py # 数据访问层
└── utils/             # 工具模块
    ├── browser_manager.py
    ├── anti_detection.py
    └── file_manager.py
```

### 核心技术栈

- **MCP协议**：与Claude Code等AI工具的标准化集成
- **Playwright**：高性能浏览器自动化
- **SQLAlchemy**：现代化的数据库ORM
- **Pydantic**：类型安全的配置管理
- **AsyncIO**：高并发异步处理
- **Claude/OpenAI API**：AI驱动的内容生成

## 🔒 安全与合规

### 反检测措施
- 随机用户代理和视口大小
- 人性化的鼠标移动和输入模拟
- 智能延迟和行为噪音
- 请求频率限制

### 平台合规
- 遵守LinkedIn和SEEK的使用条款
- 合理的投递频率限制
- 尊重平台的反爬虫机制
- 用户数据隐私保护

### 数据安全
- 本地数据存储
- 敏感信息加密
- 安全的API密钥管理
- 定期数据清理

## 📊 功能特性

| 功能模块 | LinkedIn | SEEK | 状态 |
|---------|----------|------|------|
| 职位搜索 | ✅ | ✅ | 完成 |
| Easy Apply检测 | ✅ | ✅ | 完成 |
| 自动投递 | ✅ | 🔄 | 进行中 |
| 求职信生成 | ✅ | ✅ | 完成 |
| 投递追踪 | ✅ | ✅ | 完成 |
| 文件管理 | ✅ | ✅ | 完成 |
| 反检测 | ✅ | ✅ | 完成 |

## 🚨 重要提醒

### 使用限制
- 请遵守平台的使用条款
- 建议每日投递不超过10个职位
- 定期检查并更新个人资料
- 避免使用虚假信息

### 最佳实践
- 定制化求职信内容，避免模板化
- 定期更新技能和经验信息
- 监控投递成功率，调整策略
- 保持简历和LinkedIn资料同步

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 开发设置
```bash
# 克隆开发分支
git clone -b develop https://github.com/guangliangyang/mcp4Interview.git

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black src/
isort src/
```

## 📝 更新日志

### v1.0.0 (2024-12-XX)
- 🎉 首次发布
- ✅ LinkedIn和SEEK平台集成
- ✅ AI驱动的求职信生成
- ✅ 自动化投递流程
- ✅ 投递管理和追踪

### 路线图
- [ ] 更多平台支持（Indeed、Glassdoor等）
- [ ] 面试准备AI助手
- [ ] 移动端应用
- [ ] 高级数据分析
- [ ] 团队协作功能

## 📞 支持与反馈

- 🐛 Bug报告：[GitHub Issues](https://github.com/guangliangyang/mcp4Interview/issues)
- 💬 功能建议：[GitHub Discussions](https://github.com/guangliangyang/mcp4Interview/discussions)
- 📧 联系邮箱：support@mcp4interview.com
- 📚 文档：[完整文档](https://mcp4interview.com/docs)

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！

**免责声明**：本工具仅用于学习和研究目的。用户应遵守相关平台的使用条款，合理合法地使用本工具。作者不对使用本工具可能产生的任何后果承担责任。