"""
职位匹配度分析器
分析简历与职位的匹配程度，提供优化建议
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

class JobMatcher:
    """职位匹配度分析器"""

    def __init__(self, ai_config: Dict):
        self.config = ai_config
        self.client = self._initialize_ai_client()

        # 技能权重配置
        self.skill_weights = {
            'programming_languages': 0.3,
            'frameworks': 0.25,
            'tools': 0.2,
            'databases': 0.15,
            'soft_skills': 0.1
        }

    def _initialize_ai_client(self):
        """初始化AI客户端"""
        try:
            if self.config.get('anthropic_api_key'):
                import anthropic
                return anthropic.Anthropic(api_key=self.config['anthropic_api_key'])
            elif self.config.get('openai_api_key'):
                import openai
                return openai.OpenAI(api_key=self.config['openai_api_key'])
            else:
                logger.info("未配置AI API密钥，使用基础匹配算法")
                return None
        except ImportError as e:
            logger.error(f"AI库导入失败: {e}")
            return None

    async def analyze_match(self, job_description: str, resume_content: str = "") -> str:
        """分析职位匹配度

        Args:
            job_description: 职位描述
            resume_content: 简历内容或路径

        Returns:
            匹配度分析报告
        """
        try:
            # 读取简历内容
            if resume_content and Path(resume_content).exists():
                resume_content = await self._read_resume_file(resume_content)

            if self.client and resume_content:
                return await self._ai_match_analysis(job_description, resume_content)
            else:
                return await self._basic_match_analysis(job_description, resume_content)

        except Exception as e:
            logger.error(f"职位匹配分析失败: {e}")
            return f"分析失败: {str(e)}"

    async def _read_resume_file(self, file_path: str) -> str:
        """读取简历文件内容"""
        try:
            file_path = Path(file_path)

            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif file_path.suffix.lower() == '.pdf':
                # 需要PDF读取库
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        return text
                except ImportError:
                    logger.warning("未安装PyPDF2，无法读取PDF简历")
                    return ""

            else:
                logger.warning(f"不支持的简历文件格式: {file_path.suffix}")
                return ""

        except Exception as e:
            logger.error(f"读取简历文件失败: {e}")
            return ""

    async def _ai_match_analysis(self, job_description: str, resume_content: str) -> str:
        """使用AI进行深度匹配分析"""
        try:
            prompt = self._build_match_analysis_prompt(job_description, resume_content)

            if 'anthropic' in str(type(self.client)):
                # Claude API
                message = self.client.messages.create(
                    model=self.config.get('default_model', 'claude-3-sonnet-20240229'),
                    max_tokens=self.config.get('max_tokens', 2000),
                    temperature=self.config.get('temperature', 0.3),
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text

            elif 'openai' in str(type(self.client)):
                # OpenAI API
                response = self.client.chat.completions.create(
                    model=self.config.get('default_model', 'gpt-3.5-turbo'),
                    max_tokens=self.config.get('max_tokens', 2000),
                    temperature=self.config.get('temperature', 0.3),
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"AI匹配分析失败: {e}")
            return await self._basic_match_analysis(job_description, resume_content)

    def _build_match_analysis_prompt(self, job_description: str, resume_content: str) -> str:
        """构建匹配分析提示"""
        prompt = f"""
作为一名专业的招聘顾问和简历分析师，请分析以下简历与职位的匹配度：

**职位描述：**
{job_description[:2000]}

**简历内容：**
{resume_content[:2000]}

请提供详细的匹配度分析报告，包括：

**1. 整体匹配度评分 (0-100分)**
基于技能、经验、教育背景等因素给出综合评分

**2. 技能匹配分析**
- 完全匹配的技能
- 部分匹配的技能
- 缺失的关键技能

**3. 经验匹配度**
- 相关工作经验年限
- 行业背景契合度
- 项目经验相关性

**4. 关键词优化建议**
- 需要增加的关键词
- 可以强化的技能描述
- ATS系统优化建议

**5. 简历改进建议**
- 具体的优化方向
- 需要突出的经验
- 格式和结构建议

**6. 申请成功概率评估**
基于匹配度给出申请成功的可能性

请用结构化的格式提供分析结果，使用emoji来增强可读性。
"""
        return prompt

    async def _basic_match_analysis(self, job_description: str, resume_content: str = "") -> str:
        """基础匹配分析（无AI）"""
        try:
            # 提取职位要求
            job_skills = self._extract_skills_from_job(job_description)
            job_keywords = self._extract_keywords(job_description)

            # 分析简历（如果有）
            if resume_content:
                resume_skills = self._extract_skills_from_resume(resume_content)
                resume_keywords = self._extract_keywords(resume_content)

                # 计算匹配度
                skill_match = self._calculate_skill_match(job_skills, resume_skills)
                keyword_match = self._calculate_keyword_match(job_keywords, resume_keywords)

                overall_score = (skill_match * 0.7 + keyword_match * 0.3)

                return self._format_basic_analysis(
                    overall_score, job_skills, resume_skills, job_keywords, resume_keywords
                )
            else:
                return self._format_job_only_analysis(job_skills, job_keywords)

        except Exception as e:
            logger.error(f"基础匹配分析失败: {e}")
            return f"分析过程中出现错误: {str(e)}"

    def _extract_skills_from_job(self, job_description: str) -> Dict[str, List[str]]:
        """从职位描述中提取技能"""
        skills = {
            'programming_languages': [],
            'frameworks': [],
            'tools': [],
            'databases': [],
            'soft_skills': []
        }

        # 编程语言
        prog_langs = ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Scala', 'Kotlin', 'Swift', 'TypeScript']
        # 框架
        frameworks = ['React', 'Vue', 'Angular', 'Django', 'Flask', 'Spring', 'Express', 'Laravel', 'Rails', 'ASP.NET']
        # 工具
        tools = ['Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git', 'Jenkins', 'Terraform', 'Ansible']
        # 数据库
        databases = ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch', 'Oracle', 'SQL Server']
        # 软技能
        soft_skills = ['leadership', 'communication', 'teamwork', 'problem solving', 'analytical', 'creative']

        job_desc_lower = job_description.lower()

        for lang in prog_langs:
            if lang.lower() in job_desc_lower:
                skills['programming_languages'].append(lang)

        for framework in frameworks:
            if framework.lower() in job_desc_lower:
                skills['frameworks'].append(framework)

        for tool in tools:
            if tool.lower() in job_desc_lower:
                skills['tools'].append(tool)

        for db in databases:
            if db.lower() in job_desc_lower:
                skills['databases'].append(db)

        for skill in soft_skills:
            if skill in job_desc_lower:
                skills['soft_skills'].append(skill)

        return skills

    def _extract_skills_from_resume(self, resume_content: str) -> Dict[str, List[str]]:
        """从简历中提取技能"""
        # 复用职位技能提取逻辑
        return self._extract_skills_from_job(resume_content)

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 移除标点符号并转换为小写
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = cleaned_text.split()

        # 过滤停用词和短词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]

        # 返回最常见的关键词
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(20)]

    def _calculate_skill_match(self, job_skills: Dict, resume_skills: Dict) -> float:
        """计算技能匹配度"""
        total_score = 0.0
        total_weight = 0.0

        for category, weight in self.skill_weights.items():
            job_category_skills = set(skill.lower() for skill in job_skills.get(category, []))
            resume_category_skills = set(skill.lower() for skill in resume_skills.get(category, []))

            if job_category_skills:
                match_count = len(job_category_skills.intersection(resume_category_skills))
                category_score = match_count / len(job_category_skills)
                total_score += category_score * weight
                total_weight += weight

        return (total_score / total_weight * 100) if total_weight > 0 else 0.0

    def _calculate_keyword_match(self, job_keywords: List[str], resume_keywords: List[str]) -> float:
        """计算关键词匹配度"""
        if not job_keywords:
            return 0.0

        job_set = set(job_keywords)
        resume_set = set(resume_keywords)

        match_count = len(job_set.intersection(resume_set))
        return (match_count / len(job_set)) * 100

    def _format_basic_analysis(
        self,
        overall_score: float,
        job_skills: Dict,
        resume_skills: Dict,
        job_keywords: List[str],
        resume_keywords: List[str]
    ) -> str:
        """格式化基础分析结果"""
        # 计算匹配和缺失的技能
        matched_skills = []
        missing_skills = []

        for category in job_skills:
            job_category_skills = set(skill.lower() for skill in job_skills[category])
            resume_category_skills = set(skill.lower() for skill in resume_skills[category])

            matched = job_category_skills.intersection(resume_category_skills)
            missing = job_category_skills - resume_category_skills

            matched_skills.extend([skill.title() for skill in matched])
            missing_skills.extend([skill.title() for skill in missing])

        # 格式化结果
        result = f"""# 📊 职位匹配度分析报告

## 🎯 整体匹配度评分
**{overall_score:.1f}/100分** {'🟢' if overall_score >= 70 else '🟡' if overall_score >= 50 else '🔴'}

## ✅ 技能匹配情况

### 匹配的技能 ({len(matched_skills)} 项)
{', '.join(matched_skills) if matched_skills else '暂未发现明显匹配的技能'}

### ⚠️ 缺失的关键技能 ({len(missing_skills)} 项)
{', '.join(missing_skills) if missing_skills else '所有关键技能都已覆盖'}

## 🔍 关键词分析

### 职位关键词 (Top 10)
{', '.join(job_keywords[:10])}

### 简历关键词覆盖
{', '.join(set(job_keywords).intersection(set(resume_keywords))) if set(job_keywords).intersection(set(resume_keywords)) else '关键词覆盖较少'}

## 💡 优化建议

### 立即改进项
"""

        if overall_score < 50:
            result += """
- 🔴 **匹配度较低**：建议重新审视是否适合申请此职位
- 📚 **技能提升**：优先学习缺失的关键技能
- 📝 **简历优化**：增加相关项目经验描述
"""
        elif overall_score < 70:
            result += """
- 🟡 **有一定机会**：可以尝试申请，但需要优化
- 🎯 **突出优势**：在求职信中强调匹配的技能
- 📈 **补充经验**：寻找相关项目或培训经历
"""
        else:
            result += """
- 🟢 **匹配度良好**：建议积极申请
- ⭐ **保持优势**：继续强化已有技能
- 🚀 **展示成果**：突出相关项目的具体成果
"""

        if missing_skills:
            result += f"\n### 🎯 技能发展重点\n"
            for skill in missing_skills[:5]:  # 显示前5个最重要的缺失技能
                result += f"- 学习和掌握 **{skill}**\n"

        return result

    def _format_job_only_analysis(self, job_skills: Dict, job_keywords: List[str]) -> str:
        """格式化仅职位分析结果"""
        total_skills = sum(len(skills) for skills in job_skills.values())

        result = f"""# 📋 职位要求分析

## 🎯 技能要求概览 (共 {total_skills} 项技能)

"""

        for category, skills in job_skills.items():
            if skills:
                category_name = {
                    'programming_languages': '编程语言',
                    'frameworks': '框架/库',
                    'tools': '工具/平台',
                    'databases': '数据库',
                    'soft_skills': '软技能'
                }.get(category, category)

                result += f"### {category_name}\n"
                result += f"{', '.join(skills)}\n\n"

        result += f"""## 🔑 关键词重点

### 高频关键词 (Top 10)
{', '.join(job_keywords[:10])}

## 💡 申请建议

### 简历优化重点
- ✅ 确保简历包含上述关键技能
- 📝 使用相同的技术术语和关键词
- 🎯 突出相关项目经验和成果
- 📊 量化工作成果和影响

### 求职信要点
- 🎨 针对性地展示匹配的技能
- 💼 强调相关行业经验
- 🚀 体现学习能力和适应性
- 🤝 展现团队合作和沟通能力

## ⚠️ 注意事项
- 如果缺少关键技能，考虑先进行学习或培训
- 准备面试时重点复习相关技术知识
- 了解公司背景和行业趋势
"""

        return result

if __name__ == "__main__":
    async def test_job_matcher():
        """测试职位匹配器"""
        config = {
            'anthropic_api_key': '',  # 需要实际的API密钥
            'default_model': 'claude-3-sonnet-20240229',
            'max_tokens': 2000,
            'temperature': 0.3
        }

        matcher = JobMatcher(config)

        job_desc = """
        Senior Python Developer position requiring:
        - 5+ years Python development experience
        - Django, Flask frameworks
        - REST API development
        - AWS cloud platforms
        - Docker, Kubernetes
        - PostgreSQL, Redis
        - Strong problem-solving skills
        """

        resume = """
        Senior Software Developer with 6 years experience in Python development.
        Expert in Django and Flask frameworks. Built scalable REST APIs.
        Experience with AWS services including EC2, S3, RDS.
        Proficient in Docker containerization and Kubernetes orchestration.
        Database experience with PostgreSQL and MongoDB.
        Strong analytical and communication skills.
        """

        analysis = await matcher.analyze_match(job_desc, resume)
        print(analysis)

    asyncio.run(test_job_matcher())