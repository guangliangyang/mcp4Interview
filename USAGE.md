# MCP 智能简历投递助手 - 使用指南

## 📖 概述

这是一个基于 MCP (Model Context Protocol) 的智能简历投递助手，专为 LinkedIn 和 SEEK 平台设计。它可以自动搜索职位、生成个性化求职信、自动填写申请表单，并提供完整的申请数据管理功能。

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装：
- Python 3.9+
- Claude Desktop (免费版即可)
- Chrome 或 Chromium 浏览器

### 2. 安装依赖

```bash
cd /Users/andy/workspace/00-mcp
pip install -r requirements.txt
```

### 3. 配置 Claude Desktop

在 Claude Desktop 配置文件中添加以下内容：

**macOS 路径**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows 路径**: `%APPDATA%\\Claude\\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "job-applier": {
      "command": "python3",
      "args": ["/Users/andy/workspace/00-mcp/src/server.py"],
      "cwd": "/Users/andy/workspace/00-mcp"
    }
  }
}
```

### 4. 配置环境变量 (可选)

如需使用 AI 功能，请设置 API 密钥：

```bash
# 使用 Claude (推荐)
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# 或使用 OpenAI
export OPENAI_API_KEY="your-openai-api-key"
```

### 5. 启动 Claude Desktop

重启 Claude Desktop，现在您可以开始使用智能简历投递助手了！

## 🎯 核心功能使用

### LinkedIn Easy Apply 自动申请

```
请帮我在 LinkedIn 上搜索 "Python Developer" 职位，地点在 "San Francisco"，然后对前5个 Easy Apply 职位进行自动申请。
```

系统会：
1. 搜索匹配职位
2. 筛选 Easy Apply 职位
3. 为每个职位生成个性化求职信
4. 自动填写申请表单
5. 提交申请并记录到数据库

### 智能求职信生成

```
请为这个职位生成一份求职信：
职位：Senior Software Engineer at Google
要求：5年Python经验，熟悉云计算和微服务
我的背景：6年Python开发，AWS认证，Docker和Kubernetes经验
```

### 简历关键词优化

```
请优化我的简历关键词，目标职位是这个：
[粘贴职位描述]

我的简历内容：
[粘贴简历内容]
```

### 申请数据统计和分析

```
请生成我最近30天的申请报告，包括成功率分析和改进建议。
```

## 🛠️ 详细功能说明

### 1. 职位搜索功能

**支持的平台**：LinkedIn, SEEK
**搜索参数**：关键词、地点、薪资、职位类型

```
搜索 LinkedIn 上的 "Data Scientist" 职位，地点 "New York"，最低薪资 $100,000
```

### 2. Easy Apply 专门搜索

专门搜索支持一键申请的 LinkedIn 职位：

```
搜索所有 "Frontend Developer" 的 Easy Apply 职位，限制10个结果
```

### 3. 职位匹配度分析

分析您的简历与特定职位的匹配程度：

```
分析我的简历与以下职位的匹配度：
[职位描述]

简历路径：/path/to/resume.pdf
```

### 4. 自动申请功能

**LinkedIn 自动申请**：
```
自动申请这个 LinkedIn 职位：
https://www.linkedin.com/jobs/view/123456789

使用自定义求职信和标准个人信息
```

**SEEK 自动申请**：
```
自动申请这个 SEEK 职位：
https://www.seek.com.au/job/123456789

包含求职信和工作签证状态信息
```

### 5. 申请状态管理

**跟踪所有申请**：
```
显示我的所有申请状态
```

**更新申请状态**：
```
将职位 https://linkedin.com/jobs/view/123456789 的状态更新为 "interview"，
备注：已安排下周二面试
```

### 6. 数据分析和报告

**生成详细报告**：
```
生成过去3个月的申请活动报告，包括平台分析和成功率统计
```

**获取统计数据**：
```
显示最近7天的申请统计数据
```

## ⚙️ 高级配置

### 1. 个人信息配置

编辑 `config.json` 文件来配置个人信息：

```json
{
  "user_info": {
    "name": "您的姓名",
    "email": "your.email@example.com",
    "phone": "+1-234-567-8900",
    "linkedin": "https://linkedin.com/in/yourprofile",
    "location": "San Francisco, CA"
  }
}
```

### 2. 浏览器设置

```json
{
  "browser": {
    "headless": false,
    "slow_mo": 1000,
    "window_width": 1920,
    "window_height": 1080
  }
}
```

### 3. 申请频率控制

```json
{
  "linkedin": {
    "max_applications_per_hour": 30,
    "delay_between_actions": [3, 8]
  }
}
```

## 📁 文件管理

### 简历管理

系统会自动管理您的简历文件：

- **存储位置**：`data/resumes/`
- **支持格式**：PDF, DOC, DOCX, TXT, RTF
- **自动备份**：保留历史版本

### 求职信管理

- **存储位置**：`data/cover_letters/`
- **自动分类**：按公司和职位自动命名
- **内容预览**：显示前200字符预览

## 🔍 故障排除

### 常见问题

1. **"浏览器启动失败"**
   - 确保已安装 Chrome/Chromium
   - 检查 Playwright 是否正确安装：`python -m playwright install`

2. **"LinkedIn 登录失败"**
   - 确保账号信息正确
   - 可能需要手动完成安全验证
   - 设置 `headless: false` 来观察登录过程

3. **"数据库错误"**
   - 确保 `data/` 目录有写入权限
   - 删除 `data/applications.db` 让系统重新创建

4. **"申请提交失败"**
   - LinkedIn 可能更新了页面结构
   - 检查网络连接
   - 确认职位链接有效且支持 Easy Apply

### 日志查看

系统日志保存在 `data/logs/app.log`：

```bash
tail -f data/logs/app.log  # 实时查看日志
```

### 调试模式

启用调试模式查看详细信息：

```bash
export DEBUG=1
python3 src/server.py
```

## 🔒 隐私和安全

### 数据安全

- **本地存储**：所有数据仅存储在本地
- **加密保护**：敏感信息经过加密处理
- **无外传**：个人信息不会发送到外部服务器

### 使用建议

1. **合规使用**：遵守 LinkedIn 和 SEEK 的使用条款
2. **合理频率**：避免过于频繁的申请操作
3. **质量优先**：专注于高匹配度的职位申请
4. **定期备份**：备份重要的申请数据

## 🎯 最佳实践

### 1. 申请策略

- **质量优于数量**：专注于高匹配度的职位
- **个性化内容**：为每个申请定制求职信
- **及时跟进**：定期更新申请状态

### 2. 效率优化

- **批量操作**：一次搜索多个相关职位
- **模板复用**：建立个人求职信模板库
- **数据分析**：定期分析申请效果并调整策略

### 3. 风险管控

- **分散申请**：不要集中在单一时间大量申请
- **监控响应**：关注申请响应率的变化
- **账号安全**：定期更改密码，启用二步验证

---

**祝您求职成功！** 🎉