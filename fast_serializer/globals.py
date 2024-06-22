# -*- coding:utf-8 -*-


class GlobalSetting:
    """全局设置"""

    """语言代码 Language code"""
    LANGUAGE_CODE = 'zh-Hans'

    """数据类默认必填"""
    DATACLASS_DEFAULT_REQUIRED = False

    """是否启用国际化"""
    USE_I18N = True

    @classmethod
    def get_language(cls):
        return cls.LANGUAGE_CODE
    
    @classmethod
    def set_language(cls, language_code):
        cls.LANGUAGE_CODE = language_code
        return cls.LANGUAGE_CODE

    @classmethod
    def get_i18n(cls):
        return cls.USE_I18N

    @classmethod
    def set_i18n(cls, use_i18n):
        cls.USE_I18N = use_i18n
        return cls.USE_I18N

    @classmethod
    def get_dataclass_default_required(cls):
        return cls.DATACLASS_DEFAULT_REQUIRED

    @classmethod
    def set_dataclass_default_required(cls, default_required: bool):
        cls.DATACLASS_DEFAULT_REQUIRED = default_required
        return cls.DATACLASS_DEFAULT_REQUIRED