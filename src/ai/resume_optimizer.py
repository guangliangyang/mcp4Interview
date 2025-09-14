"""
简历优化器
基于职位要求优化简历内容和关键词
"""

import asyncio
import logging
import re
from typing import Dict, List, Tuple, Optional
from collections import Counter

from src.utils.logger import get_logger

logger = get_logger(__name__)

class ResumeOptimizer:
    """简历优化器"""

    def __init__(self, ai_config: Dict):
        self.config = ai_config
        self.client = self._initialize_ai_client()

        # ATS关键词权重
        self.ats_weights = {
            'exact_match': 1.0,      # 完全匹配
            'synonym_match': 0.8,    # 同义词匹配
            'partial_match': 0.6,    # 部分匹配
            'related_match': 0.4     # 相关匹配
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
                logger.info("未配置AI API密钥，使用基础优化算法")
                return None
        except ImportError as e:
            logger.error(f"AI库导入失败: {e}")
            return None

    async def optimize_keywords(self, resume_content: str, job_posting: str) -> str:
        """优化简历关键词

        Args:
            resume_content: 原始简历内容
            job_posting: 职位描述

        Returns:
            优化后的简历内容
        """
        try:
            if self.client:
                return await self._ai_keyword_optimization(resume_content, job_posting)
            else:
                return await self._basic_keyword_optimization(resume_content, job_posting)

        except Exception as e:
            logger.error(f"关键词优化失败: {e}")
            return resume_content

    async def _ai_keyword_optimization(self, resume_content: str, job_posting: str) -> str:
        """使用AI进行关键词优化"""
        try:
            prompt = self._build_optimization_prompt(resume_content, job_posting)

            if 'anthropic' in str(type(self.client)):
                # Claude API
                message = self.client.messages.create(
                    model=self.config.get('default_model', 'claude-3-sonnet-20240229'),
                    max_tokens=self.config.get('max_tokens', 3000),
                    temperature=self.config.get('temperature', 0.5),
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text

            elif 'openai' in str(type(self.client)):
                # OpenAI API
                response = self.client.chat.completions.create(
                    model=self.config.get('default_model', 'gpt-3.5-turbo'),
                    max_tokens=self.config.get('max_tokens', 3000),
                    temperature=self.config.get('temperature', 0.5),
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"AI关键词优化失败: {e}")
            return await self._basic_keyword_optimization(resume_content, job_posting)

    def _build_optimization_prompt(self, resume_content: str, job_posting: str) -> str:
        """构建优化提示"""
        prompt = f"""
作为一名专业的简历优化专家和ATS系统专家，请优化以下简历以匹配目标职位。

**目标职位描述：**
{job_posting[:2000]}

**原始简历内容：**
{resume_content[:2000]}

**优化要求：**

1. **关键词优化**
   - 识别职位描述中的关键技能和要求
   - 在简历中自然地融入这些关键词
   - 确保关键词的使用符合上下文
   - 优化技能关键词以提高ATS通过率

2. **技能部分强化**
   - 重新排列技能部分，优先展示匹配的技能
   - 添加职位要求中提到但简历中缺失的相关技能
   - 使用与职位描述一致的技术术语

3. **经验描述优化**
   - 调整工作经验描述，突出与目标职位相关的成果
   - 使用量化数据增强说服力
   - 采用行动导向的语言（Action-Result format）

4. **格式和结构优化**
   - 确保重要关键词在简历前1/3部分出现
   - 优化段落结构，提高可读性
   - 保持专业格式

5. **ATS友好性**
   - 使用标准的简历段落标题
   - 避免使用图表、特殊字符
   - 确保关键信息易于机器解析

**请返回优化后的完整简历内容，保持原有的基本信息和经历，但要显著提高与目标职位的匹配度。**

优化后的简历：
"""
        return prompt

    async def _basic_keyword_optimization(self, resume_content: str, job_posting: str) -> str:
        """基础关键词优化（无AI）"""
        try:
            # 提取职位关键词
            job_keywords = self._extract_job_keywords(job_posting)

            # 分析当前简历关键词
            resume_keywords = self._extract_resume_keywords(resume_content)

            # 找出缺失的关键词
            missing_keywords = self._find_missing_keywords(job_keywords, resume_keywords)

            # 生成优化建议
            optimized_content = self._apply_basic_optimizations(
                resume_content, job_keywords, missing_keywords
            )

            return optimized_content

        except Exception as e:
            logger.error(f"基础关键词优化失败: {e}")
            return resume_content

    def _extract_job_keywords(self, job_posting: str) -> Dict[str, List[str]]:
        """提取职位关键词"""
        keywords = {
            'technical_skills': [],
            'soft_skills': [],
            'tools': [],
            'certifications': [],
            'experience_keywords': []
        }

        # 技术技能关键词
        technical_patterns = [
            r'\b(Python|JavaScript|Java|C\+\+|C#|Go|Rust|PHP|Ruby|Scala|Kotlin|Swift|TypeScript)\b',
            r'\b(React|Vue|Angular|Django|Flask|Spring|Express|Laravel|Rails|ASP\.NET)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|Terraform|Ansible)\b',
            r'\b(MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Oracle|SQL Server)\b'
        ]

        # 软技能关键词
        soft_skills_patterns = [
            r'\b(leadership|communication|teamwork|problem[- ]solving|analytical|creative|strategic)\b',
            r'\b(project management|agile|scrum|collaboration|mentoring|coaching)\b'
        ]

        # 经验相关关键词
        experience_patterns = [
            r'\b(\d+\+?\s*years?|experience|background|expertise|proficiency)\b',
            r'\b(senior|lead|principal|architect|manager|director)\b',
            r'\b(develop|build|design|implement|manage|lead|coordinate)\b'
        ]

        job_lower = job_posting.lower()

        # 提取技术技能
        for pattern in technical_patterns:
            matches = re.findall(pattern, job_lower, re.IGNORECASE)
            keywords['technical_skills'].extend(matches)

        # 提取软技能
        for pattern in soft_skills_patterns:
            matches = re.findall(pattern, job_lower, re.IGNORECASE)
            keywords['soft_skills'].extend(matches)

        # 提取经验关键词
        for pattern in experience_patterns:
            matches = re.findall(pattern, job_lower, re.IGNORECASE)
            keywords['experience_keywords'].extend(matches)

        # 去重并排序
        for category in keywords:
            keywords[category] = list(set(keywords[category]))
            keywords[category].sort(key=len, reverse=True)  # 长词优先

        return keywords

    def _extract_resume_keywords(self, resume_content: str) -> Dict[str, List[str]]:
        """提取简历关键词"""
        return self._extract_job_keywords(resume_content)  # 复用逻辑

    def _find_missing_keywords(self, job_keywords: Dict, resume_keywords: Dict) -> Dict[str, List[str]]:
        """找出缺失的关键词"""
        missing = {}

        for category in job_keywords:
            job_set = set(keyword.lower() for keyword in job_keywords[category])
            resume_set = set(keyword.lower() for keyword in resume_keywords.get(category, []))

            missing_set = job_set - resume_set
            missing[category] = list(missing_set)

        return missing

    def _apply_basic_optimizations(
        self,
        resume_content: str,
        job_keywords: Dict,
        missing_keywords: Dict
    ) -> str:
        """应用基础优化"""
        optimized_content = resume_content

        # 创建优化建议而不是直接修改简历
        optimization_suggestions = self._generate_optimization_suggestions(
            job_keywords, missing_keywords
        )

        # 在简历末尾添加优化建议
        optimized_content += "\n\n" + "="*50
        optimized_content += "\n📊 简历优化建议\n"
        optimized_content += "="*50 + "\n"
        optimized_content += optimization_suggestions

        return optimized_content

    def _generate_optimization_suggestions(self, job_keywords: Dict, missing_keywords: Dict) -> str:
        """生成优化建议"""
        suggestions = []

        # 分析缺失的技术技能
        if missing_keywords.get('technical_skills'):
            suggestions.append("🔧 **技术技能优化**")
            suggestions.append("建议在简历中添加以下技能（如果你有相关经验）：")
            for skill in missing_keywords['technical_skills'][:5]:
                suggestions.append(f"   • {skill.title()}")
            suggestions.append("")

        # 分析缺失的软技能
        if missing_keywords.get('soft_skills'):
            suggestions.append("💡 **软技能强化**")
            suggestions.append("建议在工作经验中体现以下能力：")
            for skill in missing_keywords['soft_skills'][:3]:
                suggestions.append(f"   • {skill.title()}")
            suggestions.append("")

        # 关键词密度分析
        all_job_keywords = []
        for category in job_keywords.values():
            all_job_keywords.extend(category)

        if all_job_keywords:
            suggestions.append("📈 **关键词优化**")
            suggestions.append("职位描述中的高频关键词：")
            keyword_counter = Counter(all_job_keywords)
            for keyword, count in keyword_counter.most_common(8):
                suggestions.append(f"   • {keyword.title()} (出现 {count} 次)")
            suggestions.append("")

        # ATS优化建议
        suggestions.append("🤖 **ATS系统优化**")
        suggestions.append("   • 使用标准的简历段落标题（如 'Professional Experience'）")
        suggestions.append("   • 在简历前1/3部分包含关键技能")
        suggestions.append("   • 使用项目符号列举技能和成就")
        suggestions.append("   • 避免使用表格、图片或特殊格式")
        suggestions.append("   • 确保联系信息清晰可读")
        suggestions.append("")

        # 量化建议
        suggestions.append("📊 **成果量化建议**")
        suggestions.append("   • 使用具体数字描述项目规模和影响")
        suggestions.append("   • 突出改进效果（如'提升效率30%'）")
        suggestions.append("   • 强调团队规模和管理经验")
        suggestions.append("   • 展示技术项目的用户量或性能提升")
        suggestions.append("")

        return "\n".join(suggestions)

    async def analyze_ats_compatibility(self, resume_content: str) -> Dict[str, any]:
        """分析ATS兼容性"""
        try:
            analysis = {
                'score': 0,
                'issues': [],
                'recommendations': [],
                'keyword_density': {},
                'format_score': 0
            }

            # 格式分析
            format_issues = self._analyze_format_compatibility(resume_content)
            analysis['issues'].extend(format_issues)

            # 关键词密度分析
            keyword_analysis = self._analyze_keyword_density(resume_content)
            analysis['keyword_density'] = keyword_analysis

            # 结构分析
            structure_score = self._analyze_resume_structure(resume_content)
            analysis['format_score'] = structure_score

            # 计算总体评分
            analysis['score'] = self._calculate_ats_score(analysis)

            # 生成建议
            analysis['recommendations'] = self._generate_ats_recommendations(analysis)

            return analysis

        except Exception as e:
            logger.error(f"ATS兼容性分析失败: {e}")
            return {'score': 0, 'error': str(e)}

    def _analyze_format_compatibility(self, resume_content: str) -> List[str]:
        """分析格式兼容性"""
        issues = []

        # 检查特殊字符
        special_chars = re.findall(r'[^\w\s\-.,()@/:]', resume_content)
        if len(special_chars) > 10:
            issues.append("包含过多特殊字符，可能影响ATS解析")

        # 检查是否有标准段落标题
        standard_sections = [
            'experience', 'education', 'skills', 'summary', 'objective'
        ]
        found_sections = 0
        for section in standard_sections:
            if section.lower() in resume_content.lower():
                found_sections += 1

        if found_sections < 3:
            issues.append("缺少标准简历段落标题")

        # 检查联系信息
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_content):
            issues.append("未找到有效的邮箱地址")

        return issues

    def _analyze_keyword_density(self, resume_content: str) -> Dict[str, int]:
        """分析关键词密度"""
        # 提取关键词并统计频率
        words = re.findall(r'\b\w{4,}\b', resume_content.lower())
        word_counter = Counter(words)

        # 过滤停用词
        stop_words = {
            'experience', 'work', 'company', 'project', 'team', 'development',
            'management', 'application', 'system', 'technology', 'business'
        }

        filtered_counter = {
            word: count for word, count in word_counter.items()
            if word not in stop_words and count > 1
        }

        return dict(filtered_counter.most_common(15))

    def _analyze_resume_structure(self, resume_content: str) -> float:
        """分析简历结构评分"""
        score = 0.0

        # 长度检查 (1-2页最佳)
        word_count = len(resume_content.split())
        if 300 <= word_count <= 800:
            score += 25

        # 段落结构检查
        paragraphs = resume_content.split('\n\n')
        if 4 <= len(paragraphs) <= 8:
            score += 25

        # 项目符号使用
        bullet_points = resume_content.count('•') + resume_content.count('-')
        if bullet_points >= 5:
            score += 25

        # 数字和量化指标
        numbers = re.findall(r'\d+', resume_content)
        if len(numbers) >= 8:
            score += 25

        return score

    def _calculate_ats_score(self, analysis: Dict) -> float:
        """计算ATS总评分"""
        base_score = 100.0

        # 扣分项
        penalty = len(analysis['issues']) * 10
        base_score -= penalty

        # 格式评分权重
        format_weight = 0.4
        keyword_weight = 0.6

        format_score = analysis['format_score']
        keyword_score = min(len(analysis['keyword_density']) * 5, 60)  # 关键词多样性

        total_score = (format_score * format_weight + keyword_score * keyword_weight)
        return max(0, min(100, total_score))

    def _generate_ats_recommendations(self, analysis: Dict) -> List[str]:
        """生成ATS优化建议"""
        recommendations = []

        if analysis['score'] < 60:
            recommendations.append("🔴 ATS兼容性需要重大改进")
        elif analysis['score'] < 80:
            recommendations.append("🟡 ATS兼容性良好，但有改进空间")
        else:
            recommendations.append("🟢 ATS兼容性优秀")

        # 具体建议
        if analysis['issues']:
            recommendations.append("**立即解决的问题：**")
            recommendations.extend([f"  • {issue}" for issue in analysis['issues']])

        if analysis['keyword_density']:
            recommendations.append("**关键词优化：**")
            recommendations.append("  • 适当增加以下高频词汇的使用：")
            top_keywords = list(analysis['keyword_density'].keys())[:5]
            recommendations.append(f"    {', '.join(top_keywords)}")

        return recommendations

if __name__ == "__main__":
    async def test_resume_optimizer():
        """测试简历优化器"""
        config = {
            'anthropic_api_key': '',  # 需要实际的API密钥
            'default_model': 'claude-3-sonnet-20240229',
            'max_tokens': 3000,
            'temperature': 0.5
        }

        optimizer = ResumeOptimizer(config)

        sample_resume = """
        John Smith
        Software Developer
        john.smith@email.com | (555) 123-4567

        EXPERIENCE
        Senior Developer at TechCorp (2020-2024)
        - Developed web applications using Python and JavaScript
        - Worked with databases and APIs
        - Led a small team of developers

        EDUCATION
        Bachelor of Computer Science, University of Technology (2016-2020)

        SKILLS
        Programming: Python, JavaScript, HTML, CSS
        Databases: MySQL, PostgreSQL
        """

        job_posting = """
        Senior Python Developer - Remote

        We are seeking a Senior Python Developer with expertise in:
        - 5+ years Python development experience
        - Django and Flask frameworks
        - REST API development and integration
        - AWS cloud services (EC2, S3, RDS)
        - Docker containerization
        - PostgreSQL and Redis databases
        - Agile development methodologies
        - Strong problem-solving and communication skills

        Responsibilities:
        - Design and develop scalable web applications
        - Lead technical architecture decisions
        - Mentor junior developers
        - Collaborate with cross-functional teams
        """

        optimized = await optimizer.optimize_keywords(sample_resume, job_posting)
        print("优化后的简历：")
        print(optimized)
        print("\n" + "="*60 + "\n")

        # ATS兼容性分析
        ats_analysis = await optimizer.analyze_ats_compatibility(sample_resume)
        print("ATS兼容性分析：")
        print(f"评分: {ats_analysis['score']:.1f}/100")
        print("建议：")
        for rec in ats_analysis['recommendations']:
            print(f"  {rec}")

    asyncio.run(test_resume_optimizer())