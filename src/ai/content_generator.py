"""
AI内容生成器
使用Claude/OpenAI生成个性化求职信和其他内容
"""

import asyncio
import logging
import json
from typing import Dict, Optional, List
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

class ContentGenerator:
    """AI驱动的内容生成器"""

    def __init__(self, ai_config: Dict):
        self.config = ai_config
        self.client = self._initialize_ai_client()

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
                logger.warning("未配置AI API密钥，将使用模板生成")
                return None
        except ImportError as e:
            logger.error(f"AI库导入失败: {e}")
            return None

    async def generate_cover_letter(
        self,
        job_description: str,
        company_name: str,
        position_title: str,
        resume_summary: str = "",
        template_type: str = "generic"
    ) -> str:
        """生成个性化求职信

        Args:
            job_description: 职位描述
            company_name: 公司名称
            position_title: 职位标题
            resume_summary: 简历摘要
            template_type: 模板类型

        Returns:
            生成的求职信
        """
        try:
            if self.client:
                return await self._generate_ai_cover_letter(
                    job_description, company_name, position_title, resume_summary
                )
            else:
                return await self._generate_template_cover_letter(
                    job_description, company_name, position_title, resume_summary, template_type
                )

        except Exception as e:
            logger.error(f"生成求职信失败: {e}")
            return await self._generate_fallback_cover_letter(company_name, position_title)

    async def _generate_ai_cover_letter(
        self,
        job_description: str,
        company_name: str,
        position_title: str,
        resume_summary: str
    ) -> str:
        """使用AI生成求职信"""
        try:
            prompt = self._build_cover_letter_prompt(
                job_description, company_name, position_title, resume_summary
            )

            if 'anthropic' in str(type(self.client)):
                # Claude API
                message = self.client.messages.create(
                    model=self.config.get('default_model', 'claude-3-sonnet-20240229'),
                    max_tokens=self.config.get('max_tokens', 1000),
                    temperature=self.config.get('temperature', 0.7),
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text

            elif 'openai' in str(type(self.client)):
                # OpenAI API
                response = self.client.chat.completions.create(
                    model=self.config.get('default_model', 'gpt-3.5-turbo'),
                    max_tokens=self.config.get('max_tokens', 1000),
                    temperature=self.config.get('temperature', 0.7),
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            else:
                raise Exception("未知的AI客户端类型")

        except Exception as e:
            logger.error(f"AI生成求职信失败: {e}")
            raise

    def _build_cover_letter_prompt(
        self,
        job_description: str,
        company_name: str,
        position_title: str,
        resume_summary: str
    ) -> str:
        """构建求职信生成提示"""
        prompt = f"""
作为一名专业的求职顾问，请为以下职位生成一份个性化的求职信：

**职位信息：**
- 公司: {company_name}
- 职位: {position_title}
- 职位描述: {job_description[:1500]}...

**候选人信息：**
{resume_summary if resume_summary else "请根据职位要求突出相关技能和经验"}

**要求：**
1. 求职信长度控制在300-500字
2. 突出与职位要求最匹配的技能和经验
3. 体现对公司和行业的了解
4. 语气专业但不失热情
5. 包含具体的价值主张
6. 避免过于模板化的表达

**格式：**
- 使用正式的商务信函格式
- 开头："Dear Hiring Manager" 或 "Dear {company_name} Team"
- 结尾：专业的结束语和签名

请生成求职信内容：
"""
        return prompt

    async def _generate_template_cover_letter(
        self,
        job_description: str,
        company_name: str,
        position_title: str,
        resume_summary: str,
        template_type: str
    ) -> str:
        """使用模板生成求职信"""
        try:
            # 加载模板
            templates = await self._load_cover_letter_templates()

            if template_type not in templates:
                template_type = "generic"

            template_data = templates[template_type]
            template = template_data["template"]

            # 提取关键信息
            key_skills = self._extract_key_skills(job_description)
            company_strengths = self._extract_company_info(job_description)

            # 填充模板变量
            variables = {
                "company": company_name,
                "position": position_title,
                "field": self._infer_field(position_title),
                "key_skills": ", ".join(key_skills[:3]),
                "relevant_skills": ", ".join(key_skills[:5]),
                "experience_paragraph": self._generate_experience_paragraph(resume_summary, key_skills),
                "company_strength": company_strengths[0] if company_strengths else "innovative approach",
                "candidate_name": "[Your Name]"
            }

            # 应用变量替换
            cover_letter = template
            for key, value in variables.items():
                cover_letter = cover_letter.replace(f"{{{key}}}", str(value))

            return cover_letter

        except Exception as e:
            logger.error(f"模板生成求职信失败: {e}")
            return await self._generate_fallback_cover_letter(company_name, position_title)

    async def _load_cover_letter_templates(self) -> Dict:
        """加载求职信模板"""
        try:
            templates_path = Path("templates/cover_letter_templates.json")
            if templates_path.exists():
                with open(templates_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载模板失败: {e}")

        # 返回默认模板
        return {
            "generic": {
                "template": """Dear Hiring Manager,

I am writing to express my strong interest in the {position} position at {company}. With my background in {field} and expertise in {key_skills}, I am confident I would be a valuable addition to your team.

{experience_paragraph}

I am particularly drawn to {company}'s {company_strength} and would be excited to contribute my skills in {relevant_skills} to help drive your continued success.

Thank you for your consideration. I look forward to the opportunity to discuss how my experience and enthusiasm can benefit your team.

Best regards,
{candidate_name}"""
            }
        }

    def _extract_key_skills(self, job_description: str) -> List[str]:
        """从职位描述中提取关键技能"""
        # 常见技能关键词
        skill_keywords = [
            'Python', 'JavaScript', 'Java', 'React', 'Node.js', 'SQL', 'AWS',
            'Docker', 'Kubernetes', 'Machine Learning', 'Data Analysis',
            'Project Management', 'Agile', 'Scrum', 'Git', 'API', 'REST',
            'Microservices', 'Cloud', 'DevOps', 'CI/CD', 'Testing'
        ]

        found_skills = []
        job_desc_lower = job_description.lower()

        for skill in skill_keywords:
            if skill.lower() in job_desc_lower:
                found_skills.append(skill)

        return found_skills[:10]  # 返回前10个技能

    def _extract_company_info(self, job_description: str) -> List[str]:
        """提取公司特色信息"""
        company_keywords = [
            "innovative", "leading", "growth", "cutting-edge", "industry leader",
            "market leader", "technology", "collaborative", "dynamic", "fast-paced"
        ]

        found_info = []
        job_desc_lower = job_description.lower()

        for keyword in company_keywords:
            if keyword in job_desc_lower:
                found_info.append(keyword)

        return found_info if found_info else ["innovative approach"]

    def _infer_field(self, position_title: str) -> str:
        """根据职位标题推断领域"""
        title_lower = position_title.lower()

        field_mapping = {
            'software': 'software development',
            'developer': 'software development',
            'engineer': 'engineering',
            'data': 'data science',
            'analyst': 'data analysis',
            'scientist': 'data science',
            'manager': 'management',
            'designer': 'design',
            'marketing': 'marketing',
            'sales': 'sales',
            'product': 'product management'
        }

        for keyword, field in field_mapping.items():
            if keyword in title_lower:
                return field

        return "technology"

    def _generate_experience_paragraph(self, resume_summary: str, key_skills: List[str]) -> str:
        """生成经验段落"""
        if resume_summary:
            return f"Based on my background in {resume_summary[:200]}{'...' if len(resume_summary) > 200 else ''}"

        if key_skills:
            return f"My experience with {', '.join(key_skills[:3])} has prepared me to tackle complex challenges and deliver high-quality solutions."

        return "My professional experience has equipped me with a strong foundation in problem-solving and collaborative teamwork."

    async def _generate_fallback_cover_letter(self, company_name: str, position_title: str) -> str:
        """生成后备求职信"""
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {position_title} position at {company_name}.

With my professional background and technical skills, I am confident that I would be a valuable addition to your team. I am particularly excited about the opportunity to contribute to {company_name}'s continued success and growth.

My experience has taught me the importance of continuous learning, collaboration, and delivering high-quality results. I am eager to bring these qualities to your organization and help drive meaningful impact.

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and enthusiasm can benefit your team.

Best regards,
[Your Name]"""

    async def generate_email_subject(self, position_title: str, company_name: str) -> str:
        """生成邮件主题"""
        subjects = [
            f"Application for {position_title} - [Your Name]",
            f"Interest in {position_title} Position at {company_name}",
            f"{position_title} Application - Experienced Professional",
            f"Enthusiastic {position_title} Candidate - [Your Name]"
        ]

        return subjects[0]  # 返回第一个作为默认

    async def optimize_for_platform(self, content: str, platform: str) -> str:
        """针对平台优化内容"""
        if platform.lower() == 'linkedin':
            # LinkedIn字符限制优化
            if len(content) > 2000:
                # 截取并添加省略
                content = content[:1950] + "...\n\nI would welcome the opportunity to discuss my qualifications further.\n\nBest regards,\n[Your Name]"

        elif platform.lower() == 'seek':
            # SEEK平台优化 - 更多空间，可以更详细
            if len(content) < 300:
                # 如果内容太短，添加更多细节
                content = content.replace(
                    "Thank you for considering my application.",
                    "I am excited about the possibility of joining your team and contributing to your organization's success. Thank you for considering my application."
                )

        return content

    async def optimize_keywords(self, content: str, job_posting: str, content_type: str = "resume") -> str:
        """优化关键词以提高ATS通过率"""
        try:
            if self.ai_client:
                prompt = f"""
                Please optimize the following {content_type} content to improve ATS (Applicant Tracking System) compatibility based on this job posting.

                Job Posting:
                {job_posting}

                Current {content_type.title()}:
                {content}

                Instructions:
                1. Identify key skills, technologies, and qualifications mentioned in the job posting
                2. Naturally incorporate these keywords into the {content_type} without keyword stuffing
                3. Maintain readability and professional tone
                4. Ensure all added keywords are relevant and truthful
                5. Return only the optimized content

                Optimized {content_type.title()}:
                """

                response = await self.ai_client.messages.create(
                    model=self.config.get('default_model', 'claude-3-sonnet-20240229'),
                    max_tokens=self.config.get('max_tokens', 2000),
                    temperature=self.config.get('temperature', 0.3),
                    messages=[{"role": "user", "content": prompt}]
                )

                optimized_content = response.content[0].text.strip()
                logger.info(f"关键词优化完成 - {content_type}")
                return optimized_content

            else:
                # 简单的关键词优化逻辑
                return await self._basic_keyword_optimization(content, job_posting, content_type)

        except Exception as e:
            logger.error(f"关键词优化失败: {e}")
            return content

    async def _basic_keyword_optimization(self, content: str, job_posting: str, content_type: str) -> str:
        """基础关键词优化（无AI时的备选方案）"""
        try:
            # 提取职位要求中的关键词
            import re

            # 常见技能关键词
            tech_keywords = re.findall(r'\b(?:Python|Java|JavaScript|React|SQL|AWS|Docker|Kubernetes|Git|Agile|Scrum|Machine Learning|AI|Data Science|API|REST|GraphQL|MongoDB|PostgreSQL|Redis|Linux|CI/CD|DevOps)\b', job_posting, re.IGNORECASE)

            # 软技能关键词
            soft_keywords = re.findall(r'\b(?:leadership|communication|teamwork|problem-solving|analytical|creative|detail-oriented|self-motivated|adaptable|collaborative)\b', job_posting, re.IGNORECASE)

            # 去重并转换为小写
            all_keywords = list(set([kw.lower() for kw in tech_keywords + soft_keywords]))

            # 在内容中查找可以自然插入关键词的位置
            optimized_content = content

            # 简单的关键词插入逻辑
            if content_type == "resume":
                # 在技能部分添加关键词
                if "Skills" in content or "技能" in content:
                    for keyword in all_keywords[:5]:  # 限制数量
                        if keyword.lower() not in content.lower():
                            optimized_content = optimized_content.replace(
                                "Skills:", f"Skills: {keyword.title()}, "
                            )

            return optimized_content

        except Exception as e:
            logger.error(f"基础关键词优化失败: {e}")
            return content

    async def generate_question_answers(self, questions: List[str], job_context: str = "", user_profile: str = "") -> List[str]:
        """生成申请问题的智能回答"""
        try:
            answers = []

            for question in questions:
                if self.ai_client:
                    prompt = f"""
                    Please provide a professional and appropriate answer to this job application question.

                    Job Context: {job_context}
                    User Profile: {user_profile}
                    Question: {question}

                    Guidelines:
                    1. Keep answers concise but informative
                    2. Be honest and professional
                    3. Relate to the job context when possible
                    4. Avoid generic responses
                    5. Maximum 2-3 sentences for most questions

                    Answer:
                    """

                    response = await self.ai_client.messages.create(
                        model=self.config.get('default_model', 'claude-3-sonnet-20240229'),
                        max_tokens=500,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    answer = response.content[0].text.strip()
                    answers.append(answer)

                else:
                    # 使用模板回答
                    answer = await self._get_template_answer(question)
                    answers.append(answer)

            logger.info(f"生成问题回答: {len(answers)} 个")
            return answers

        except Exception as e:
            logger.error(f"生成问题回答失败: {e}")
            return ["I am excited about this opportunity and believe my skills align well with your requirements." for _ in questions]

    async def _get_template_answer(self, question: str) -> str:
        """获取模板化回答"""
        question_lower = question.lower()

        # 常见问题模板
        if any(keyword in question_lower for keyword in ['salary', 'compensation', 'pay']):
            return "I am open to discussing competitive compensation that reflects the market rate and my experience level."

        elif any(keyword in question_lower for keyword in ['start', 'available', 'notice']):
            return "I am available to start within 2-4 weeks, allowing for proper transition of my current responsibilities."

        elif any(keyword in question_lower for keyword in ['why', 'interested', 'motivate']):
            return "I am interested in this role because it aligns with my career goals and offers opportunities to apply my skills in a meaningful way."

        elif any(keyword in question_lower for keyword in ['experience', 'years']):
            return "I have relevant experience that directly applies to this position and am excited to contribute to your team."

        elif any(keyword in question_lower for keyword in ['relocate', 'move', 'location']):
            return "I am open to discussing relocation options and am flexible regarding location for the right opportunity."

        else:
            return "Yes, I believe my background and enthusiasm make me well-suited for this position."

if __name__ == "__main__":
    async def test_content_generator():
        """测试内容生成器"""
        config = {
            'anthropic_api_key': '',  # 需要实际的API密钥
            'default_model': 'claude-3-sonnet-20240229',
            'max_tokens': 1000,
            'temperature': 0.7
        }

        generator = ContentGenerator(config)

        job_desc = """
        We are looking for a Senior Python Developer to join our team.
        Requirements: 5+ years Python experience, Django, REST APIs, AWS, Docker.
        You will work on building scalable web applications and APIs.
        """

        cover_letter = await generator.generate_cover_letter(
            job_description=job_desc,
            company_name="TechCorp Inc",
            position_title="Senior Python Developer",
            resume_summary="Experienced Python developer with 6 years in web development, Django expert, AWS certified"
        )

        print("Generated Cover Letter:")
        print(cover_letter)

    asyncio.run(test_content_generator())