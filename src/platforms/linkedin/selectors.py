"""
LinkedIn页面元素选择器
定义LinkedIn平台的CSS选择器和XPath表达式
"""

# LinkedIn 登录页面
LOGIN_SELECTORS = {
    'username_field': '#username',
    'password_field': '#password',
    'login_button': 'button[type="submit"]',
    'challenge_form': '.challenge-form',
    'captcha_container': '.captcha-container'
}

# LinkedIn 职位搜索页面
SEARCH_SELECTORS = {
    'search_box': 'input[placeholder*="Search for jobs"]',
    'location_box': 'input[placeholder*="City, state, zip code, or "]',
    'search_button': 'button[aria-label="Search"]',
    'filters_button': 'button[aria-label="All filters"]',
    'job_cards': '.job-search-card',
    'job_title': '.job-search-card__title',
    'company_name': '.job-search-card__subtitle-link',
    'job_location': '.job-search-card__location',
    'easy_apply_tag': '.job-search-card__easy-apply-label',
    'pagination_next': '.artdeco-pagination__button--next'
}

# LinkedIn Easy Apply 申请流程
EASY_APPLY_SELECTORS = {
    'easy_apply_button': '.jobs-apply-button--top-card',
    'modal_container': '.jobs-easy-apply-modal',
    'next_button': 'button[aria-label="Continue to next step"]',
    'submit_button': 'button[aria-label="Submit application"]',
    'review_button': 'button[aria-label="Review your application"]',

    # 表单字段
    'phone_input': 'input[id*="phoneNumber"]',
    'resume_upload': 'input[type="file"][accept*=".pdf,.doc"]',
    'cover_letter_upload': 'input[type="file"][accept*=".pdf,.doc,.txt"]',

    # 问题回答
    'text_inputs': 'input[type="text"]',
    'textareas': 'textarea',
    'radio_buttons': 'input[type="radio"]',
    'checkboxes': 'input[type="checkbox"]',
    'select_dropdowns': 'select',

    # 错误信息
    'error_messages': '.artdeco-inline-feedback--error',
    'required_fields': '[required]',

    # 成功确认
    'success_message': '.jobs-easy-apply-confirmation',
    'application_sent': '.jobs-easy-apply-confirmation__header'
}

# LinkedIn 个人资料页面
PROFILE_SELECTORS = {
    'profile_name': '.text-heading-xlarge',
    'profile_headline': '.text-body-medium',
    'about_section': '.pv-about-section',
    'experience_section': '.pv-experience-section',
    'skills_section': '.pv-skills-section',
    'edit_buttons': '.artdeco-button--secondary'
}

# LinkedIn 消息页面
MESSAGE_SELECTORS = {
    'message_button': '.message-anywhere-button',
    'compose_button': '.msg-compose-button',
    'recipient_field': '.msg-form__recipients',
    'subject_field': 'input[name="subject"]',
    'message_body': '.msg-form__contenteditable',
    'send_button': '.msg-form__send-button'
}

# LinkedIn 连接请求
CONNECT_SELECTORS = {
    'connect_button': 'button[aria-label*="Invite"][aria-label*="to connect"]',
    'connect_modal': '.send-invite',
    'add_note_button': 'button[aria-label="Add a note"]',
    'note_textarea': 'textarea[name="message"]',
    'send_invite_button': 'button[aria-label="Send invitation"]',
    'connection_sent': '.artdeco-toast-message'
}

# LinkedIn 公司页面
COMPANY_SELECTORS = {
    'company_name': '.org-top-card-summary__title',
    'company_description': '.org-about-us-organization-description__text',
    'follow_button': '.org-top-card-primary-actions__action',
    'employees_count': '.org-about-company-module__company-size-definition-text',
    'industry': '.org-about-company-module__company-industries'
}

# LinkedIn 通知页面
NOTIFICATION_SELECTORS = {
    'notifications_bell': '.global-nav__primary-link[href*="notifications"]',
    'notification_items': '.nt-card',
    'mark_read_button': '.nt-card__dismiss-button',
    'view_all_link': '.nt-card__view-all-link'
}

# 通用选择器
COMMON_SELECTORS = {
    'loading_spinner': '.artdeco-spinner',
    'toast_messages': '.artdeco-toast',
    'modal_close': '.artdeco-modal__dismiss',
    'dropdown_options': '.artdeco-dropdown__content li',
    'pagination': '.artdeco-pagination',
    'progress_bar': '.jobs-easy-apply-form-section__progress-bar'
}

# 表单验证选择器
VALIDATION_SELECTORS = {
    'required_indicator': '.required',
    'error_text': '.artdeco-inline-feedback__message',
    'success_checkmark': '.artdeco-icon--check-circle-solid',
    'warning_icon': '.artdeco-icon--warning-solid'
}

# XPath 表达式 (用于复杂选择)
XPATH_SELECTORS = {
    'job_apply_button_by_text': "//button[contains(text(), 'Easy Apply') or contains(text(), 'Apply')]",
    'form_field_by_label': "//label[contains(text(), '{label}')]/following-sibling::input",
    'checkbox_by_text': "//span[contains(text(), '{text}')]/preceding-sibling::input[@type='checkbox']",
    'radio_by_value': "//input[@type='radio'][@value='{value}']",
    'button_by_aria_label': "//button[@aria-label='{label}']",
    'link_by_text': "//a[contains(text(), '{text}')]"
}

# 动态选择器 (根据内容变化)
DYNAMIC_SELECTORS = {
    'salary_range_any': lambda min_salary: f"//span[contains(text(), '{min_salary}') or contains(text(), 'Competitive')]",
    'job_type_filter': lambda job_type: f"//label[contains(text(), '{job_type}')]/input",
    'experience_level': lambda level: f"//button[contains(text(), '{level}')]",
    'company_size': lambda size: f"//span[contains(text(), '{size}')]"
}

# 等待条件选择器 (用于Playwright等待)
WAIT_SELECTORS = {
    'page_loaded': 'main[role="main"]',
    'search_results_loaded': '.job-search-card',
    'easy_apply_modal_loaded': '.jobs-easy-apply-modal',
    'profile_loaded': '.pv-text-details__left-panel',
    'messages_loaded': '.msg-conversation-listitem'
}

# 移动端选择器 (响应式)
MOBILE_SELECTORS = {
    'hamburger_menu': '.global-nav__hamburger-icon',
    'mobile_search': '.jobs-search-box--mobile',
    'mobile_job_card': '.job-card-mobile',
    'mobile_apply_button': '.jobs-apply-button--mobile'
}

class LinkedInSelectors:
    """LinkedIn选择器管理类"""

    def __init__(self):
        self.login = LOGIN_SELECTORS
        self.search = SEARCH_SELECTORS
        self.easy_apply = EASY_APPLY_SELECTORS
        self.profile = PROFILE_SELECTORS
        self.message = MESSAGE_SELECTORS
        self.connect = CONNECT_SELECTORS
        self.company = COMPANY_SELECTORS
        self.notification = NOTIFICATION_SELECTORS
        self.common = COMMON_SELECTORS
        self.validation = VALIDATION_SELECTORS
        self.xpath = XPATH_SELECTORS
        self.dynamic = DYNAMIC_SELECTORS
        self.wait = WAIT_SELECTORS
        self.mobile = MOBILE_SELECTORS

    def get_field_selector(self, field_type: str) -> str:
        """根据字段类型获取选择器"""
        field_mapping = {
            'phone': self.easy_apply['phone_input'],
            'resume': self.easy_apply['resume_upload'],
            'cover_letter': self.easy_apply['cover_letter_upload'],
            'text': self.easy_apply['text_inputs'],
            'textarea': self.easy_apply['textareas'],
            'radio': self.easy_apply['radio_buttons'],
            'checkbox': self.easy_apply['checkboxes'],
            'select': self.easy_apply['select_dropdowns']
        }
        return field_mapping.get(field_type, self.easy_apply['text_inputs'])

    def get_xpath_by_label(self, label: str) -> str:
        """根据标签文本生成XPath"""
        return self.xpath['form_field_by_label'].format(label=label)

    def get_dynamic_selector(self, selector_type: str, value: str) -> str:
        """获取动态选择器"""
        if selector_type in self.dynamic:
            return self.dynamic[selector_type](value)
        return None

# 导出默认实例
selectors = LinkedInSelectors()