"""
统一配置管理模块
使用 Pydantic 进行类型安全的配置管理
"""
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field
from typing import Optional
import os


class AISettings(BaseSettings):
    """AI模型配置"""
    api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    base_url: str = Field("", env="OPENAI_BASE_URL")
    model_name: str = Field("", env="OPENAI_MODEL_NAME", alias="model_name")
    proxy_url: Optional[str] = Field(None, env="PROXY_URL")
    debug_mode: bool = Field(False, env="AI_DEBUG_MODE")
    enable_response_format: bool = Field(True, env="ENABLE_RESPONSE_FORMAT")
    enable_thinking: bool = Field(False, env="ENABLE_THINKING")
    skip_analysis: bool = Field(False, env="SKIP_AI_ANALYSIS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        extra = "ignore"
        protected_namespaces = ()

    def is_configured(self) -> bool:
        """检查AI是否已正确配置"""
        return bool(self.base_url and self.model_name)


class NotificationSettings(BaseSettings):
    """通知服务配置"""
    ntfy_topic_url: Optional[str] = Field(None, env="NTFY_TOPIC_URL")
    gotify_url: Optional[str] = Field(None, env="GOTIFY_URL")
    gotify_token: Optional[str] = Field(None, env="GOTIFY_TOKEN")
    bark_url: Optional[str] = Field(None, env="BARK_URL")
    wx_bot_url: Optional[str] = Field(None, env="WX_BOT_URL")
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")
    webhook_url: Optional[str] = Field(None, env="WEBHOOK_URL")
    webhook_method: str = Field("POST", env="WEBHOOK_METHOD")
    webhook_headers: Optional[str] = Field(None, env="WEBHOOK_HEADERS")
    webhook_content_type: str = Field("JSON", env="WEBHOOK_CONTENT_TYPE")
    webhook_query_parameters: Optional[str] = Field(None, env="WEBHOOK_QUERY_PARAMETERS")
    webhook_body: Optional[str] = Field(None, env="WEBHOOK_BODY")
    pcurl_to_mobile: bool = Field(True, env="PCURL_TO_MOBILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def has_any_notification_enabled(self) -> bool:
        """检查是否配置了任何通知服务"""
        return any([
            self.ntfy_topic_url,
            self.wx_bot_url,
            self.gotify_url and self.gotify_token,
            self.bark_url,
            self.telegram_bot_token and self.telegram_chat_id,
            self.webhook_url
        ])


class ScraperSettings(BaseSettings):
    """爬虫相关配置"""
    run_headless: bool = Field(True, env="RUN_HEADLESS")
    login_is_edge: bool = Field(False, env="LOGIN_IS_EDGE")
    running_in_docker: bool = Field(False, env="RUNNING_IN_DOCKER")
    state_file: str = Field("xianyu_state.json", env="STATE_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class AppSettings(BaseSettings):
    """应用主配置"""
    server_port: int = Field(8000, env="SERVER_PORT")
    web_username: str = Field("admin", env="WEB_USERNAME")
    web_password: str = Field("admin123", env="WEB_PASSWORD")

    # 文件路径配置
    config_file: str = "config.json"
    image_save_dir: str = "images"
    task_image_dir_prefix: str = "task_images_"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 创建必要的目录
        os.makedirs(self.image_save_dir, exist_ok=True)


# 全局配置实例（单例模式）
_settings_instance = None

def get_settings() -> AppSettings:
    """获取全局配置实例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AppSettings()
    return _settings_instance


# 导出便捷访问的配置实例
settings = get_settings()
ai_settings = AISettings()
notification_settings = NotificationSettings()
scraper_settings = ScraperSettings()
