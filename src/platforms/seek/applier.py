"""
SEEK自动申请模块
澳洲求职平台专用
"""

import asyncio
import logging
import random
from typing import Dict, Optional, List
from playwright.async_api import Page, Browser, async_playwright

from src.utils.logger import get_logger

logger = get_logger(__name__)

class SeekApplier:
    """SEEK自动申请器"""

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

            logger.info("SEEK applier initialized")

        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            raise

    async def apply_to_job(self, job_url: str, application_data: Dict) -> Dict:
        """申请SEEK职位

        Args:
            job_url: 职位URL
            application_data: 申请数据，包含求职信、个人信息等

        Returns:
            申请结果
        """
        if not self.page:
            await self.initialize()

        try:
            logger.info(f"开始申请SEEK职位: {job_url}")

            # 导航到职位页面
            await self.page.goto(job_url, wait_until='networkidle')

            # 检查是否需要登录
            if await self._need_login():
                return {
                    "status": "failed",
                    "message": "需要先登录SEEK账号"
                }

            # 查找申请按钮并获取申请链接
            apply_url = await self._get_apply_url()

            if not apply_url:
                return {
                    "status": "failed",
                    "message": "未找到申请链接"
                }

            # 导航到申请页面
            await self.page.goto(apply_url, wait_until='networkidle')

            # 填写申请表单
            form_result = await self._fill_application_form(application_data)

            if not form_result["success"]:
                return {
                    "status": "failed",
                    "message": f"填写表单失败: {form_result['message']}"
                }

            # 提交申请
            submit_result = await self._submit_application()

            if submit_result:
                logger.info(f"成功申请SEEK职位: {job_url}")
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
            logger.error(f"申请SEEK职位失败 {job_url}: {e}")
            return {
                "status": "failed",
                "message": f"申请过程中出错: {str(e)}"
            }

    async def _need_login(self) -> bool:
        """检查是否需要登录"""
        try:
            # 检查是否存在登录相关元素
            login_button = await self.page.query_selector('a[href*="login"]')
            sign_in_button = await self.page.query_selector('button:has-text("Sign in")')

            return login_button is not None or sign_in_button is not None

        except Exception:
            return True

    async def _get_apply_url(self) -> Optional[str]:
        """获取申请链接"""
        try:
            # 查找申请按钮
            apply_button = await self.page.query_selector('[data-automation="job-apply"]')
            if apply_button:
                apply_url = await apply_button.get_attribute('href')
                if apply_url:
                    if not apply_url.startswith('http'):
                        apply_url = f"https://www.seek.com.au{apply_url}"
                    return apply_url

            # 备选查找方式
            apply_links = await self.page.query_selector_all('a[href*="apply"]')
            for link in apply_links:
                href = await link.get_attribute('href')
                if href and 'apply' in href:
                    if not href.startswith('http'):
                        href = f"https://www.seek.com.au{href}"
                    return href

            return None

        except Exception as e:
            logger.error(f"获取申请链接失败: {e}")
            return None

    async def _fill_application_form(self, application_data: Dict) -> Dict:
        """填写申请表单

        Args:
            application_data: 申请数据
                - cover_letter: 求职信
                - personal_info: 个人信息
                - visa_status: 签证状态
                - salary_expectation: 薪资期望

        Returns:
            填写结果
        """
        try:
            # 等待表单加载
            await asyncio.sleep(2)

            # 填写个人信息
            await self._fill_personal_info(application_data.get('personal_info', {}))

            # 填写求职信
            cover_letter = application_data.get('cover_letter', '')
            if cover_letter:
                await self._fill_cover_letter(cover_letter)

            # 处理文件上传
            await self._handle_file_uploads(application_data.get('resume_path'))

            # 填写签证状态
            visa_status = application_data.get('visa_status', '')
            if visa_status:
                await self._fill_visa_status(visa_status)

            # 填写薪资期望
            salary_expectation = application_data.get('salary_expectation', '')
            if salary_expectation:
                await self._fill_salary_expectation(salary_expectation)

            # 处理其他问题
            await self._handle_additional_questions(application_data.get('additional_answers', {}))

            return {"success": True, "message": "表单填写完成"}

        except Exception as e:
            logger.error(f"填写申请表单失败: {e}")
            return {"success": False, "message": str(e)}

    async def _fill_personal_info(self, personal_info: Dict):
        """填写个人信息"""
        try:
            # 填写姓名
            if 'name' in personal_info:
                name_fields = await self.page.query_selector_all('input[name*="name"], input[placeholder*="name"]')
                for field in name_fields:
                    await field.fill(personal_info['name'])
                    break

            # 填写邮箱
            if 'email' in personal_info:
                email_fields = await self.page.query_selector_all('input[type="email"], input[name*="email"]')
                for field in email_fields:
                    await field.fill(personal_info['email'])
                    break

            # 填写电话
            if 'phone' in personal_info:
                phone_fields = await self.page.query_selector_all('input[type="tel"], input[name*="phone"]')
                for field in phone_fields:
                    await field.fill(personal_info['phone'])
                    break

            logger.info("已填写个人信息")

        except Exception as e:
            logger.warning(f"填写个人信息失败: {e}")

    async def _fill_cover_letter(self, cover_letter: str):
        """填写求职信"""
        try:
            # 查找求职信文本框
            cover_letter_fields = await self.page.query_selector_all(
                'textarea[name*="cover"], textarea[placeholder*="cover"], textarea[name*="letter"]'
            )

            if cover_letter_fields:
                await cover_letter_fields[0].fill(cover_letter)
                logger.info("已填写求职信")
            else:
                # 查找大型文本框
                text_areas = await self.page.query_selector_all('textarea')
                if text_areas:
                    # 选择最大的文本框作为求职信字段
                    largest_textarea = None
                    max_size = 0

                    for textarea in text_areas:
                        try:
                            placeholder = await textarea.get_attribute('placeholder') or ""
                            rows = await textarea.get_attribute('rows') or "1"
                            size = int(rows) * len(placeholder)

                            if size > max_size:
                                max_size = size
                                largest_textarea = textarea
                        except:
                            continue

                    if largest_textarea:
                        await largest_textarea.fill(cover_letter)
                        logger.info("已填写求职信（自动检测字段）")

        except Exception as e:
            logger.warning(f"填写求职信失败: {e}")

    async def _handle_file_uploads(self, resume_path: Optional[str]):
        """处理文件上传"""
        try:
            if not resume_path:
                return

            # 查找文件上传字段
            file_inputs = await self.page.query_selector_all('input[type="file"]')

            for file_input in file_inputs:
                # 检查是否为简历上传字段
                label_text = ""
                input_id = await file_input.get_attribute('id')
                if input_id:
                    label = await self.page.query_selector(f'label[for="{input_id}"]')
                    if label:
                        label_text = await label.inner_text()

                if 'resume' in label_text.lower() or 'cv' in label_text.lower():
                    await file_input.set_input_files(resume_path)
                    logger.info("已上传简历文件")
                    break

        except Exception as e:
            logger.warning(f"处理文件上传失败: {e}")

    async def _fill_visa_status(self, visa_status: str):
        """填写签证状态"""
        try:
            # 查找签证状态相关字段
            visa_selects = await self.page.query_selector_all('select')

            for select in visa_selects:
                label_text = ""
                select_name = await select.get_attribute('name') or ""

                # 查找相关标签
                if 'visa' in select_name.lower() or 'work' in select_name.lower():
                    options = await select.query_selector_all('option')

                    for option in options:
                        option_text = await option.inner_text()

                        # 匹配签证状态
                        if (visa_status.lower() == 'authorized' and
                                ('authorized' in option_text.lower() or 'citizen' in option_text.lower())):
                            await select.select_option(value=await option.get_attribute('value'))
                            logger.info("已选择签证状态")
                            return

        except Exception as e:
            logger.warning(f"填写签证状态失败: {e}")

    async def _fill_salary_expectation(self, salary_expectation: str):
        """填写薪资期望"""
        try:
            # 查找薪资相关字段
            salary_inputs = await self.page.query_selector_all('input')

            for input_field in salary_inputs:
                name = await input_field.get_attribute('name') or ""
                placeholder = await input_field.get_attribute('placeholder') or ""

                if ('salary' in name.lower() or 'salary' in placeholder.lower() or
                        'pay' in name.lower() or 'pay' in placeholder.lower()):
                    await input_field.fill(salary_expectation)
                    logger.info("已填写薪资期望")
                    break

        except Exception as e:
            logger.warning(f"填写薪资期望失败: {e}")

    async def _handle_additional_questions(self, additional_answers: Dict):
        """处理附加问题"""
        try:
            # 处理文本输入问题
            text_inputs = await self.page.query_selector_all('input[type="text"], textarea')

            for input_elem in text_inputs:
                question_text = await self._get_question_text(input_elem)

                if question_text and question_text in additional_answers:
                    await input_elem.fill(additional_answers[question_text])
                    logger.info(f"回答问题: {question_text[:30]}...")

            # 处理选择题
            selects = await self.page.query_selector_all('select')
            for select in selects:
                # 如果没有明确答案，选择合理的默认选项
                options = await select.query_selector_all('option')
                if len(options) > 1:
                    await select.select_option(index=1)

        except Exception as e:
            logger.warning(f"处理附加问题失败: {e}")

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

    async def _submit_application(self) -> bool:
        """提交申请"""
        try:
            # 查找提交按钮
            submit_button = await self.page.query_selector('button[type="submit"]')
            if not submit_button:
                submit_button = await self.page.query_selector('button:has-text("Apply")')
            if not submit_button:
                submit_button = await self.page.query_selector('button:has-text("Submit")')
            if not submit_button:
                submit_button = await self.page.query_selector('input[type="submit"]')

            if submit_button:
                await submit_button.click()

                # 等待提交完成
                try:
                    # 等待成功页面或确认消息
                    await self.page.wait_for_selector('.success, .confirmation', timeout=10000)
                    return True
                except Exception:
                    # 检查URL变化或其他成功指标
                    await asyncio.sleep(3)
                    current_url = self.page.url

                    if ('success' in current_url or 'confirmation' in current_url or
                            'thank' in current_url or 'applied' in current_url):
                        return True

                    # 检查页面是否包含成功消息
                    page_content = await self.page.content()
                    success_keywords = ['successfully applied', 'application received', 'thank you']

                    for keyword in success_keywords:
                        if keyword.lower() in page_content.lower():
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
            logger.info("SEEK applier closed")

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
    async def test_seek_applier():
        """测试SEEK申请器"""
        config = {
            'headless': False,
            'slow_mo': 1000,
            'window_width': 1920,
            'window_height': 1080
        }

        application_data = {
            'cover_letter': 'I am very interested in this position...',
            'personal_info': {
                'name': 'Test User',
                'email': 'test@example.com',
                'phone': '+61 400 000 000'
            },
            'visa_status': 'authorized',
            'salary_expectation': 'Competitive'
        }

        async with SeekApplier(config) as applier:
            # 测试申请（需要有效的job_url）
            test_url = "https://www.seek.com.au/job/test-job-id"

            result = await applier.apply_to_job(test_url, application_data)
            print(f"申请结果: {result}")

    # asyncio.run(test_seek_applier())