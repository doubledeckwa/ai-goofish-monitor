import os
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI

# --- AI & Notification Configuration ---
load_dotenv()

# --- File Paths & Directories ---
STATE_FILE = "xianyu_state.json"
IMAGE_SAVE_DIR = "images"
CONFIG_FILE = "config.json"
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

# Temporary image directory prefix for task isolation
TASK_IMAGE_DIR_PREFIX = "task_images_"

# --- API URL Patterns ---
API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search"
DETAIL_API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail"

# --- Environment Variables ---
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
PROXY_URL = os.getenv("PROXY_URL")
NTFY_TOPIC_URL = os.getenv("NTFY_TOPIC_URL")
GOTIFY_URL = os.getenv("GOTIFY_URL")
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN")
BARK_URL = os.getenv("BARK_URL")
WX_BOT_URL = os.getenv("WX_BOT_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_METHOD = os.getenv("WEBHOOK_METHOD", "POST").upper()
WEBHOOK_HEADERS = os.getenv("WEBHOOK_HEADERS")
WEBHOOK_CONTENT_TYPE = os.getenv("WEBHOOK_CONTENT_TYPE", "JSON").upper()
WEBHOOK_QUERY_PARAMETERS = os.getenv("WEBHOOK_QUERY_PARAMETERS")
WEBHOOK_BODY = os.getenv("WEBHOOK_BODY")
PCURL_TO_MOBILE = os.getenv("PCURL_TO_MOBILE", "false").lower() == "true"
RUN_HEADLESS = os.getenv("RUN_HEADLESS", "true").lower() != "false"
LOGIN_IS_EDGE = os.getenv("LOGIN_IS_EDGE", "false").lower() == "true"
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
AI_DEBUG_MODE = os.getenv("AI_DEBUG_MODE", "false").lower() == "true"
SKIP_AI_ANALYSIS = os.getenv("SKIP_AI_ANALYSIS", "false").lower() == "true"
ENABLE_THINKING = os.getenv("ENABLE_THINKING", "false").lower() == "true"
ENABLE_RESPONSE_FORMAT = os.getenv("ENABLE_RESPONSE_FORMAT", "true").lower() == "true"

# --- Headers ---
IMAGE_DOWNLOAD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# --- Client Initialization ---
# Check whether the configuration is complete
if not all([BASE_URL, MODEL_NAME]):
    print("Warning: not present .env Complete settings in file OPENAI_BASE_URL and OPENAI_MODEL_NAME。AIRelated functions may not be available。")
    client = None
else:
    try:
        if PROXY_URL:
            print(f"working onAIRequest to useHTTP/Sacting: {PROXY_URL}")
            # httpx Proxy settings are automatically read from environment variables
            os.environ['HTTP_PROXY'] = PROXY_URL
            os.environ['HTTPS_PROXY'] = PROXY_URL

        # openai internal to client httpx Agent configuration will be automatically obtained from environment variables
        client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    except Exception as e:
        print(f"initialization OpenAI An error occurred on the client side: {e}")
        client = None

# examineAIWhether the client initialized successfully
if not client:
    # exist prompt_generator.py in if client for None，Will directly report an error and exit
    # exist spider_v2.py middle，AIAnalysis will be skipped
    # For consistency, only warnings are printed here，The specific logic is handled by the caller
    pass

# Check key configuration
if not all([BASE_URL, MODEL_NAME]) and 'prompt_generator.py' in sys.argv[0]:
    sys.exit("Error: Please make sure the .env Completely set up in the file OPENAI_BASE_URL and OPENAI_MODEL_NAME。(OPENAI_API_KEY Optional for some services)")

def get_ai_request_params(**kwargs):
    """
    buildAIRequest parameters, according toENABLE_THINKINGandENABLE_RESPONSE_FORMATEnvironment variables determine whether to add corresponding parameters
    """
    if ENABLE_THINKING:
        kwargs["extra_body"] = {"enable_thinking": False}
    
    # If disabledresponse_format，then remove this parameter
    if not ENABLE_RESPONSE_FORMAT and "response_format" in kwargs:
        del kwargs["response_format"]
    
    return kwargs
