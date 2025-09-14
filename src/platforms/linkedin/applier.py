"""
LinkedIn自动申请模块
"""

import asyncio
import logging
import random
from typing import Dict, Optional, List
from playwright.async_api import Page, Browser, async_playwright

from src.utils.logger import get_logger

logger = get_logger(__name__)

class LinkedInApplier:
    """LinkedIn自动申请器"""

    def __init__(self, browser_config: Dict):
        self.config = browser_config
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False

    async def initialize(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                slow_mo=self.config.get('slow_mo', 500)
            )

            context = await self.browser.new_context(
                viewport={
                    'width': self.config.get('window_width', 1920),
                    'height': self.config.get('window_height', 1080)
                },
                user_agent=self.config.get('user_agent')
            )

            self.page = await context.new_page()
            self.page.set_default_timeout(self.config.get('page_timeout', 30000))

            logger.info("LinkedIn applier initialized")

        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            raise

    async def apply_to_job(self, job_url: str, cover_letter: str = "", custom_answers: Dict = None) -> Dict:
        """申请LinkedIn职位

        Args:
            job_url: 职位URL
            cover_letter: 求职信
            custom_answers: 自定义问题答案

        Returns:
            申请结果
        """
        if not self.page:
            await self.initialize()

        if custom_answers is None:
            custom_answers = {}

        try:
            logger.info(f"开始申请LinkedIn职位: {job_url}")

            # 导航到职位页面
            await self.page.goto(job_url, wait_until='networkidle')

            # 检查是否需要登录
            if await self._need_login():
                return {
                    "status": "failed",
                    "message": "需要先登录LinkedIn账号"
                }

            # 检查是否有Easy Apply按钮
            easy_apply_button = await self.page.query_selector('button[data-tracking-control-name*="easy_apply"]')
            if not easy_apply_button:
                return {
                    "status": "failed",
                    "message": "此职位不支持Easy Apply"
                }

            # 点击Easy Apply按钮
            await easy_apply_button.click()
            await asyncio.sleep(2)

            # 等待申请模态框出现
            await self.page.wait_for_selector('.jobs-easy-apply-modal', timeout=10000)

            # 填写申请表单
            form_result = await self._fill_application_form(cover_letter, custom_answers)

            if not form_result["success"]:
                return {
                    "status": "failed",
                    "message": f"填写表单失败: {form_result['message']}"
                }

            # 提交申请
            submit_result = await self._submit_application()

            if submit_result:
                logger.info(f"成功申请职位: {job_url}")
                return {
                    "status": "success",
                    "message": "申请已成功提交",
                    "job_url": job_url
                }
            else:
                return {
                    "status": "failed",
                    "message": "申请提交失败"
                }

        except Exception as e:
            logger.error(f"申请职位失败 {job_url}: {e}")
            return {
                "status": "failed",
                "message": f"申请过程中出错: {str(e)}"
            }

    async def _need_login(self) -> bool:
        """检查是否需要登录"""
        try:
            # 检查是否存在登录相关元素
            login_elements = await self.page.query_selector_all('a[href*="login"]')
            return len(login_elements) > 0

        except Exception:
            return True

    async def _fill_application_form(self, cover_letter: str, custom_answers: Dict) -> Dict:
        """填写申请表单

        Args:
            cover_letter: 求职信
            custom_answers: 自定义问题答案

        Returns:
            填写结果
        """
        try:
            # 处理多步骤表单
            step = 1
            max_steps = 5

            while step <= max_steps:
                logger.info(f"处理申请表单步骤 {step}")

                # 检查当前步骤的表单元素
                form_filled = await self._fill_current_step(cover_letter, custom_answers, step)

                # 查找下一步按钮
                next_button = await self.page.query_selector('button[aria-label="继续到下一步骤"]')
                if not next_button:
                    next_button = await self.page.query_selector('button:has-text("下一步")')
                if not next_button:
                    next_button = await self.page.query_selector('button:has-text("Next")')

                if next_button:
                    await next_button.click()
                    await asyncio.sleep(2)
                    step += 1
                else:
                    # 没有下一步按钮，表单填写完成
                    break

                # 避免无限循环
                if step > max_steps:
                    logger.warning("申请表单步骤过多，可能存在问题")
                    break

            return {"success": True, "message": "表单填写完成"}

        except Exception as e:
            logger.error(f"填写申请表单失败: {e}")
            return {"success": False, "message": str(e)}

    async def _fill_current_step(self, cover_letter: str, custom_answers: Dict, step: int) -> bool:
        """填写当前步骤的表单"""
        try:
            filled_any = False

            # 填写求职信
            if cover_letter and step == 1:
                cover_letter_field = await self.page.query_selector('textarea[name*="coverLetter"]')
                if not cover_letter_field:
                    cover_letter_field = await self.page.query_selector('textarea[placeholder*="求职信"]')
                if not cover_letter_field:
                    cover_letter_field = await self.page.query_selector('textarea[placeholder*="cover letter"]')

                if cover_letter_field:
                    await cover_letter_field.fill(cover_letter)
                    filled_any = True
                    logger.info("已填写求职信")

            # 处理文件上传
            await self._handle_file_uploads()

            # 处理问答题
            filled_questions = await self._handle_questions(custom_answers)
            filled_any = filled_any or filled_questions

            # 处理选择题
            filled_selections = await self._handle_selections(custom_answers)
            filled_any = filled_any or filled_selections

            # 随机延迟模拟人工操作
            await asyncio.sleep(random.uniform(1, 3))

            return filled_any

        except Exception as e:
            logger.error(f"填写表单步骤失败: {e}")
            return False

    async def _handle_file_uploads(self):
        """处理文件上传"""
        try:
            # 查找文件上传字段
            file_inputs = await self.page.query_selector_all('input[type="file"]')

            for file_input in file_inputs:
                # 检查是否已有文件上传
                upload_status = await self.page.query_selector('.file-upload__status')
                if upload_status:
                    continue  # 已有文件，跳过

                # 这里可以上传简历文件
                # 暂时跳过文件上传，因为需要具体的文件路径
                logger.info("检测到文件上传字段，但暂未处理")

        except Exception as e:
            logger.warning(f"处理文件上传失败: {e}")

    async def _handle_questions(self, custom_answers: Dict) -> bool:
        """处理问答题"""
        try:
            filled_any = False

            # 查找文本输入框
            text_inputs = await self.page.query_selector_all('input[type="text"], textarea')

            for input_elem in text_inputs:
                # 获取问题文本
                question_text = await self._get_question_text(input_elem)

                if question_text and question_text in custom_answers:
                    await input_elem.fill(custom_answers[question_text])
                    filled_any = True
                    logger.info(f"回答问题: {question_text[:50]}...")

                # 处理常见问题
                elif question_text:
                    answer = await self._get_default_answer(question_text)
                    if answer:
                        await input_elem.fill(answer)
                        filled_any = True
                        logger.info(f"使用默认答案回答: {question_text[:50]}...")

            return filled_any

        except Exception as e:
            logger.error(f"处理问答题失败: {e}")
            return False

    async def _handle_selections(self, custom_answers: Dict) -> bool:
        """处理选择题"""
        try:
            filled_any = False

            # 处理下拉选择
            selects = await self.page.query_selector_all('select')
            for select in selects:
                options = await select.query_selector_all('option')
                if len(options) > 1:  # 有选项可选
                    # 选择第一个非空选项
                    await select.select_option(index=1)
                    filled_any = True

            # 处理单选按钮
            radio_groups = await self.page.query_selector_all('input[type="radio"]')
            processed_names = set()

            for radio in radio_groups:
                name = await radio.get_attribute('name')
                if name and name not in processed_names:
                    # 选择第一个选项
                    await radio.click()
                    processed_names.add(name)
                    filled_any = True

            return filled_any

        except Exception as e:
            logger.error(f"处理选择题失败: {e}")
            return False

    async def _get_question_text(self, input_elem) -> Optional[str]:
        """获取问题文本"""
        try:
            # 尝试多种方式获取问题文本
            label = await input_elem.get_attribute('aria-label')
            if label:
                return label

            placeholder = await input_elem.get_attribute('placeholder')
            if placeholder:
                return placeholder

            # 查找相关的label元素
            input_id = await input_elem.get_attribute('id')
            if input_id:
                label_elem = await self.page.query_selector(f'label[for="{input_id}"]')
                if label_elem:
                    return await label_elem.inner_text()

            return None

        except Exception:
            return None

    async def _get_default_answer(self, question_text: str) -> Optional[str]:
        """获取问题的默认答案"""
        question_lower = question_text.lower()

        # 常见问题的默认答案
        default_answers = {
            "experience": "5+ years",
            "visa": "Authorized to work",
            "salary": "Competitive",
            "start": "Available immediately",
            "relocate": "Yes",
            "remote": "Yes",
            "willing": "Yes"
        }

        for keyword, answer in default_answers.items():
            if keyword in question_lower:
                return answer

        return None

    async def _submit_application(self) -> bool:
        """提交申请"""
        try:
            # 查找提交按钮
            submit_button = await self.page.query_selector('button[data-tracking-control-name*="submit"]')
            if not submit_button:
                submit_button = await self.page.query_selector('button:has-text("提交申请")')
            if not submit_button:
                submit_button = await self.page.query_selector('button:has-text("Submit application")')

            if submit_button:
                await submit_button.click()

                # 等待提交完成 - 查找成功消息或跳转
                try:
                    await self.page.wait_for_selector('.jobs-apply-success', timeout=10000)
                    return True
                except Exception:
                    # 检查URL是否发生变化（通常表示提交成功）
                    await asyncio.sleep(3)
                    current_url = self.page.url
                    if 'applied' in current_url or 'success' in current_url:
                        return True

            return False

        except Exception as e:
            logger.error(f"提交申请失败: {e}")
            return False

    async def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("LinkedIn applier closed")

        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

if __name__ == "__main__":
    async def test_linkedin_applier():
        """测试LinkedIn申请器"""
        config = {
            'headless': False,
            'slow_mo': 1000,
            'window_width': 1920,
            'window_height': 1080
        }

        async with LinkedInApplier(config) as applier:
            # 测试申请（需要有效的job_url）
            test_url = "https://www.linkedin.com/jobs/view/test-job-id"
            cover_letter = "I am interested in this position..."

            result = await applier.apply_to_job(test_url, cover_letter)
            print(f"申请结果: {result}")

    # asyncio.run(test_linkedin_applier())