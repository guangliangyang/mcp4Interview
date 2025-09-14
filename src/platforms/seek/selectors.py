"""
SEEK页面元素选择器
定义SEEK平台的CSS选择器和XPath表达式
"""

# SEEK 登录页面
LOGIN_SELECTORS = {
    'username_field': 'input[type="email"]',
    'password_field': 'input[type="password"]',
    'login_button': 'button[type="submit"]',
    'remember_me': 'input[type="checkbox"][name="rememberMe"]',
    'forgot_password': 'a[href*="forgot-password"]'
}

# SEEK 职位搜索页面
SEARCH_SELECTORS = {
    'search_keywords': 'input[data-automation="searchKeywordsField"]',
    'search_location': 'input[data-automation="searchLocationField"]',
    'search_button': 'button[data-automation="searchSubmit"]',

    # 筛选器
    'salary_filter': 'button[data-automation="salaryFilter"]',
    'job_type_filter': 'button[data-automation="workTypeFilter"]',
    'date_posted_filter': 'button[data-automation="dateRange"]',
    'company_filter': 'button[data-automation="companyFilter"]',

    # 职位卡片
    'job_cards': '[data-automation="normalJob"]',
    'job_title': '[data-automation="jobTitle"]',
    'company_name': '[data-automation="jobCompany"]',
    'job_location': '[data-automation="jobLocation"]',
    'job_salary': '[data-automation="jobSalary"]',
    'job_classification': '[data-automation="jobClassification"]',

    # 分页
    'next_page': 'a[aria-label="Next"]',
    'pagination': '[data-automation="page-"]',
    'results_count': '[data-automation="totalJobsCount"]'
}

# SEEK 职位详情页面
JOB_DETAIL_SELECTORS = {
    'job_title': 'h1[data-automation="job-detail-title"]',
    'company_name': '[data-automation="advertiser-name"]',
    'job_location': '[data-automation="job-detail-location"]',
    'job_classification': '[data-automation="job-detail-classification"]',
    'job_sub_classification': '[data-automation="job-detail-subClassification"]',
    'job_salary': '[data-automation="job-detail-salary"]',
    'job_work_type': '[data-automation="job-detail-work-type"]',
    'job_description': '[data-automation="jobAdDetails"]',

    # 申请按钮
    'apply_button': '[data-automation="job-detail-apply"]',
    'external_apply_button': '[data-automation="job-detail-apply-link-label"]',

    # 职位详情
    'advertiser_description': '[data-automation="advertiser-description"]',
    'job_reference': '[data-automation="job-reference-number"]',
    'posted_date': '[data-automation="job-posted-date"]'
}

# SEEK 申请流程
APPLICATION_SELECTORS = {
    'application_form': 'form[data-automation="application-form"]',

    # 个人信息
    'first_name': 'input[name="firstName"]',
    'last_name': 'input[name="lastName"]',
    'email': 'input[name="email"]',
    'phone': 'input[name="phone"]',
    'mobile': 'input[name="mobile"]',

    # 地址信息
    'address_line1': 'input[name="addressLine1"]',
    'address_line2': 'input[name="addressLine2"]',
    'suburb': 'input[name="suburb"]',
    'state': 'select[name="state"]',
    'postcode': 'input[name="postcode"]',
    'country': 'select[name="country"]',

    # 签证状态
    'work_rights': 'select[name="workRights"]',
    'visa_status': 'select[name="visaStatus"]',

    # 文件上传
    'resume_upload': 'input[type="file"][accept*=".pdf,.doc"]',
    'cover_letter_upload': 'input[type="file"][accept*=".pdf,.doc,.txt"]',
    'additional_documents': 'input[type="file"][name="additionalDocuments"]',

    # 问题回答
    'text_questions': 'input[type="text"]',
    'textarea_questions': 'textarea',
    'dropdown_questions': 'select',
    'radio_questions': 'input[type="radio"]',
    'checkbox_questions': 'input[type="checkbox"]',

    # 提交按钮
    'submit_application': 'button[data-automation="apply-form-continue-button"]',
    'confirm_application': 'button[data-automation="confirm-application"]',

    # 验证信息
    'error_messages': '.error-message',
    'required_fields': '[required]',
    'field_errors': '.field-error'
}

# SEEK 个人资料页面
PROFILE_SELECTORS = {
    'profile_header': '.profile-header',
    'profile_name': '.profile-name',
    'profile_title': '.profile-title',
    'profile_location': '.profile-location',

    # 个人资料部分
    'personal_details': '.personal-details-section',
    'work_experience': '.work-experience-section',
    'education': '.education-section',
    'skills': '.skills-section',
    'certifications': '.certifications-section',

    # 编辑按钮
    'edit_personal_details': 'button[data-automation="edit-personal-details"]',
    'edit_experience': 'button[data-automation="edit-experience"]',
    'edit_education': 'button[data-automation="edit-education"]',

    # 求职偏好
    'job_preferences': '.job-preferences-section',
    'salary_expectations': 'input[name="salaryExpectation"]',
    'preferred_locations': 'input[name="preferredLocations"]',
    'work_type_preferences': 'select[name="workTypePreferences"]'
}

# SEEK 申请历史页面
APPLICATION_HISTORY_SELECTORS = {
    'applications_list': '.applications-list',
    'application_items': '.application-item',
    'application_status': '.application-status',
    'application_date': '.application-date',
    'job_title_link': '.job-title-link',
    'company_name_text': '.company-name',
    'view_application': 'a[data-automation="view-application"]',
    'withdraw_application': 'button[data-automation="withdraw-application"]'
}

# SEEK 公司页面
COMPANY_SELECTORS = {
    'company_header': '.company-header',
    'company_name': '.company-name',
    'company_logo': '.company-logo img',
    'company_description': '.company-description',
    'company_location': '.company-location',
    'company_size': '.company-size',
    'company_industry': '.company-industry',
    'follow_company': 'button[data-automation="follow-company"]',
    'company_jobs': '.company-jobs-section'
}

# SEEK 通知设置
NOTIFICATION_SELECTORS = {
    'notification_settings': '.notification-settings',
    'email_alerts': 'input[name="emailAlerts"]',
    'sms_alerts': 'input[name="smsAlerts"]',
    'job_alert_frequency': 'select[name="jobAlertFrequency"]',
    'application_updates': 'input[name="applicationUpdates"]',
    'save_settings': 'button[data-automation="save-notification-settings"]'
}

# 通用选择器
COMMON_SELECTORS = {
    'loading_spinner': '.loading-spinner',
    'error_banner': '.error-banner',
    'success_banner': '.success-banner',
    'modal_overlay': '.modal-overlay',
    'modal_close': 'button[data-automation="modal-close"]',
    'tooltip': '.tooltip',
    'dropdown_menu': '.dropdown-menu',
    'pagination_controls': '.pagination-controls',
    'breadcrumbs': '.breadcrumbs'
}

# 表单验证选择器
VALIDATION_SELECTORS = {
    'required_indicator': '.required-indicator',
    'field_error': '.field-error',
    'success_icon': '.success-icon',
    'warning_icon': '.warning-icon',
    'validation_message': '.validation-message'
}

# XPath 表达式
XPATH_SELECTORS = {
    'button_by_text': "//button[contains(text(), '{text}')]",
    'link_by_text': "//a[contains(text(), '{text}')]",
    'label_by_text': "//label[contains(text(), '{text}')]",
    'option_by_text': "//option[contains(text(), '{text}')]",
    'input_by_label': "//label[contains(text(), '{label}')]/following-sibling::input",
    'checkbox_by_label': "//label[contains(text(), '{label}')]/input[@type='checkbox']",
    'radio_by_label': "//label[contains(text(), '{label}')]/input[@type='radio']"
}

# 动态选择器
DYNAMIC_SELECTORS = {
    'job_by_title': lambda title: f'[data-automation="jobTitle"][title*="{title}"]',
    'filter_by_value': lambda filter_type, value: f'[data-automation="{filter_type}Filter"] option[value="{value}"]',
    'salary_range': lambda min_salary, max_salary: f'[data-automation="salaryFilter"] option[value*="{min_salary}-{max_salary}"]',
    'work_type': lambda work_type: f'[data-automation="workTypeFilter"] option[value="{work_type}"]'
}

# 等待条件选择器
WAIT_SELECTORS = {
    'page_loaded': 'main',
    'search_results_loaded': '[data-automation="normalJob"]',
    'job_detail_loaded': '[data-automation="job-detail-title"]',
    'application_form_loaded': '[data-automation="application-form"]',
    'profile_loaded': '.profile-header'
}

# 移动端选择器
MOBILE_SELECTORS = {
    'mobile_menu': '.mobile-menu-toggle',
    'mobile_search': '.mobile-search-form',
    'mobile_job_card': '.mobile-job-card',
    'mobile_filters': '.mobile-filters-toggle'
}

class SeekSelectors:
    """SEEK选择器管理类"""

    def __init__(self):
        self.login = LOGIN_SELECTORS
        self.search = SEARCH_SELECTORS
        self.job_detail = JOB_DETAIL_SELECTORS
        self.application = APPLICATION_SELECTORS
        self.profile = PROFILE_SELECTORS
        self.application_history = APPLICATION_HISTORY_SELECTORS
        self.company = COMPANY_SELECTORS
        self.notification = NOTIFICATION_SELECTORS
        self.common = COMMON_SELECTORS
        self.validation = VALIDATION_SELECTORS
        self.xpath = XPATH_SELECTORS
        self.dynamic = DYNAMIC_SELECTORS
        self.wait = WAIT_SELECTORS
        self.mobile = MOBILE_SELECTORS

    def get_field_selector(self, field_name: str) -> str:
        """根据字段名获取选择器"""
        field_mapping = {
            'firstName': self.application['first_name'],
            'lastName': self.application['last_name'],
            'email': self.application['email'],
            'phone': self.application['phone'],
            'mobile': self.application['mobile'],
            'workRights': self.application['work_rights'],
            'visaStatus': self.application['visa_status'],
            'resume': self.application['resume_upload'],
            'coverLetter': self.application['cover_letter_upload']
        }
        return field_mapping.get(field_name)

    def get_xpath_by_text(self, element_type: str, text: str) -> str:
        """根据文本内容生成XPath"""
        xpath_map = {
            'button': self.xpath['button_by_text'],
            'link': self.xpath['link_by_text'],
            'label': self.xpath['label_by_text'],
            'option': self.xpath['option_by_text']
        }
        if element_type in xpath_map:
            return xpath_map[element_type].format(text=text)
        return None

    def get_dynamic_selector(self, selector_type: str, *args) -> str:
        """获取动态选择器"""
        if selector_type in self.dynamic:
            return self.dynamic[selector_type](*args)
        return None

# 导出默认实例
selectors = SeekSelectors()