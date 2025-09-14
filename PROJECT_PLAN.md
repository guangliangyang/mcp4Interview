# MCP 智能简历投递助手 - LinkedIn & SEEK 专项版

## 项目概述
开发一个专注于 LinkedIn 和 SEEK 的 MCP 自动化简历投递工具，利用 2025 年最新的 Playwright MCP 和 AI 技术，实现：
- 智能职位筛选和匹配
- 自动表单填写和简历上传
- AI 驱动的 Cover Letter 生成
- 投递状态跟踪和管理
- 反检测和合规操作

## 技术架构

### 1. **核心 MCP 服务器**
- **主框架**: Python MCP + Playwright MCP Server (2025版)
- **AI 引擎**: Claude 3.5 Sonnet (通过 MCP 集成)
- **浏览器引擎**: Playwright (支持 Chrome/Firefox/Safari)
- **数据存储**: SQLite + JSON 配置文件
- **传输协议**: STDIO (Claude Desktop 原生支持)

### 2. **平台特定实现**

#### **LinkedIn 自动化模块**
- **Easy Apply 检测**: 优先处理一键申请职位
- **表单识别**: 智能识别 LinkedIn 表单字段
- **文件上传**: 自动上传简历和求职信文件
- **问题回答**: 处理标准化筛选问题
- **连接建立**: 可选的 HR/招聘官连接请求

#### **SEEK 自动化模块**
- **职位爬取**: 基于关键词和地理位置搜索
- **申请流程**: 处理 SEEK 特有的申请步骤
- **个人档案**: 维护和更新 SEEK 个人资料
- **求职偏好**: 自动设置薪资期望和工作类型
- **状态同步**: 跟踪申请进度和雇主反馈

### 3. **MCP 工具函数设计**

#### **职位搜索和筛选**
```python
@mcp.tool()
async def search_jobs(platform: str, keywords: str, location: str,
                     salary_min: int, job_type: str) -> List[JobListing]

@mcp.tool()
async def analyze_job_match(job_description: str, resume_path: str) -> MatchAnalysis

@mcp.tool()
async def filter_applied_jobs(job_urls: List[str]) -> List[str]
```

#### **智能内容生成**
```python
@mcp.tool()
async def generate_cover_letter(job_description: str, company_name: str,
                               resume_summary: str) -> str

@mcp.tool()
async def customize_resume(base_resume: str, job_requirements: str) -> str

@mcp.tool()
async def optimize_keywords(content: str, job_posting: str) -> str
```

#### **自动申请流程**
```python
@mcp.tool()
async def auto_apply_linkedin(job_url: str, cover_letter: str,
                             custom_answers: Dict) -> ApplicationResult

@mcp.tool()
async def auto_apply_seek(job_url: str, application_data: Dict) -> ApplicationResult

@mcp.tool()
async def handle_application_questions(questions: List[str],
                                     job_context: str) -> List[str]
```

#### **投递管理**
```python
@mcp.tool()
async def track_applications() -> List[ApplicationStatus]

@mcp.tool()
async def update_application_status(job_id: str, status: str, notes: str) -> bool

@mcp.tool()
async def generate_application_report(date_range: str) -> ApplicationReport
```

### 4. **数据库设计**
```sql
-- 职位信息表
CREATE TABLE job_listings (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,  -- 'linkedin' or 'seek'
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary_range TEXT,
    job_description TEXT,
    requirements TEXT,
    posted_date DATE,
    job_url TEXT UNIQUE,
    scraped_at TIMESTAMP
);

-- 申请记录表
CREATE TABLE applications (
    id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES job_listings(id),
    applied_at TIMESTAMP,
    status TEXT DEFAULT 'applied',  -- applied, viewed, rejected, interview, offer
    cover_letter TEXT,
    custom_resume TEXT,
    application_answers JSON,
    notes TEXT
);

-- 用户配置表
CREATE TABLE user_profiles (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    profile_data JSON,  -- 存储个人信息、技能、经验等
    preferences JSON,   -- 薪资期望、工作类型、地点等
    updated_at TIMESTAMP
);

-- 公司黑名单/白名单
CREATE TABLE company_filters (
    company_name TEXT PRIMARY KEY,
    filter_type TEXT,  -- 'blacklist' or 'whitelist'
    reason TEXT,
    created_at TIMESTAMP
);
```

### 5. **智能特性**

#### **AI 驱动的内容个性化**
- **动态简历**: 根据职位要求调整技能重点和项目描述
- **智能求职信**: 基于公司文化和职位描述生成个性化内容
- **关键词优化**: 提高 ATS (申请人跟踪系统) 通过率
- **语言本地化**: LinkedIn (英文) vs SEEK (澳式英文) 的表达差异

#### **反检测策略**
- **人性化操作**: 随机延迟、鼠标轨迹模拟
- **会话管理**: 维护登录状态，避免频繁登录
- **请求限制**: 每小时申请数量限制 (LinkedIn: 50, SEEK: 30)
- **User-Agent 轮换**: 模拟不同设备和浏览器

#### **错误处理和恢复**
- **验证码识别**: 集成 OCR 或手动介入机制
- **网页变化适应**: DOM 结构变化的自动适应
- **网络异常**: 自动重试和状态恢复
- **数据备份**: 申请数据本地备份和同步

### 6. **实现阶段**

#### **Phase 1: 基础架构 (Week 1-2)**
1. 搭建 MCP 服务器框架
2. 集成 Playwright MCP 2025 版本
3. 创建数据库架构和基础数据模型
4. 实现配置管理系统

#### **Phase 2: LinkedIn 集成 (Week 3-4)**
1. LinkedIn 登录和会话管理
2. Easy Apply 职位识别和申请流程
3. 表单自动填写和文件上传
4. 申请状态跟踪和数据存储

#### **Phase 3: SEEK 集成 (Week 5-6)**
1. SEEK 平台特定功能开发
2. 澳洲求职市场适配
3. SEEK 申请流程自动化
4. 跨平台数据同步

#### **Phase 4: AI 内容生成 (Week 7-8)**
1. Claude 集成的 Cover Letter 生成
2. 简历动态定制功能
3. 职位匹配度分析
4. ATS 关键词优化

#### **Phase 5: 优化和测试 (Week 9-10)**
1. 反检测机制完善
2. 错误处理和异常恢复
3. 性能优化和并发控制
4. 全面测试和用户体验优化

### 7. **目录结构**
```
mcp-job-applier/
├── src/
│   ├── server.py                   # 主 MCP 服务器
│   ├── config/
│   │   ├── settings.py            # 配置管理
│   │   └── user_profiles.json     # 用户档案模板
│   ├── platforms/
│   │   ├── linkedin/
│   │   │   ├── scraper.py         # LinkedIn 职位抓取
│   │   │   ├── applier.py         # 自动申请逻辑
│   │   │   └── selectors.py       # 页面元素选择器
│   │   └── seek/
│   │       ├── scraper.py         # SEEK 职位抓取
│   │       ├── applier.py         # 自动申请逻辑
│   │       └── selectors.py       # 页面元素选择器
│   ├── ai/
│   │   ├── content_generator.py   # AI 内容生成
│   │   ├── job_matcher.py         # 职位匹配分析
│   │   └── resume_optimizer.py    # 简历优化
│   ├── database/
│   │   ├── models.py              # 数据模型
│   │   ├── migrations.py          # 数据库迁移
│   │   └── queries.py             # 查询操作
│   ├── utils/
│   │   ├── browser_manager.py     # 浏览器管理
│   │   ├── anti_detection.py      # 反检测工具
│   │   ├── file_manager.py        # 文件上传管理
│   │   └── logger.py              # 日志系统
├── data/
│   ├── applications.db            # SQLite 数据库
│   ├── resumes/                   # 简历文件存储
│   ├── cover_letters/             # 求职信存储
│   └── logs/                      # 运行日志
├── templates/
│   ├── cover_letter_templates.json # 求职信模板
│   ├── resume_templates.json       # 简历模板
│   └── question_answers.json      # 常见问题答案
├── tests/
├── requirements.txt
└── claude_desktop_config.json     # MCP 客户端配置
```

### 8. **合规和道德考虑**

#### **使用条款遵循**
- **LinkedIn**: 遵守反机器人政策，合理控制请求频率
- **SEEK**: 遵守澳洲就业法规和平台使用条款
- **用户同意**: 所有操作需用户明确授权

#### **数据隐私**
- **本地存储**: 个人信息仅存储在本地
- **加密保护**: 敏感数据加密存储
- **访问控制**: 严格的数据访问权限管理

### 9. **成功指标**

#### **技术指标**
- ✅ 支持 LinkedIn Easy Apply (成功率 >90%)
- ✅ 支持 SEEK 标准申请流程 (成功率 >85%)
- ✅ AI 生成内容质量评分 >4.0/5.0
- ✅ 系统稳定运行，错误率 <5%
- ✅ 单日处理申请数量: LinkedIn (30-50), SEEK (20-30)

#### **用户价值**
- ✅ 申请效率提升 10x (从每日 5 份到 50 份)
- ✅ Cover Letter 个性化匹配度提升
- ✅ 面试邀请率相比手动申请提升 20%
- ✅ 求职时间缩短 60%

这个专注版本将 MCP 的强大功能与实用的求职自动化需求完美结合，为求职者提供真正有价值的 AI 助手工具。