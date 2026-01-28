import asyncio
import json
import os
import random
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from playwright.async_api import (
    Response,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from src.ai_handler import (
    download_all_images,
    get_ai_analysis,
    send_ntfy_notification,
    cleanup_task_images,
)
from src.config import (
    AI_DEBUG_MODE,
    API_URL_PATTERN,
    DETAIL_API_URL_PATTERN,
    LOGIN_IS_EDGE,
    RUN_HEADLESS,
    RUNNING_IN_DOCKER,
    STATE_FILE,
)
from src.parsers import (
    _parse_search_results_json,
    _parse_user_items_data,
    calculate_reputation_from_ratings,
    parse_ratings_data,
    parse_user_head_data,
)
from src.utils import (
    format_registration_days,
    get_link_unique_key,
    random_sleep,
    safe_get,
    save_to_jsonl,
    log_time,
)
from src.rotation import RotationPool, load_state_files, parse_proxy_pool, RotationItem
from src.infrastructure.config.settings import feature_settings


class RiskControlError(Exception):
    pass


# Enhanced anti-blocking detection patterns
BLOCKING_SELECTORS = [
    # Existing patterns
    "div.baxia-dialog-mask",
    "div.J_MIDDLEWARE_FRAME_WIDGET",
    
    # New common blocking patterns
    ".ant-modal-root",
    ".verify-modal", 
    "[class*='verify']",
    "[class*='captcha']",
    "[class*='verification']",
    "[style*='position: fixed'][style*='z-index']",
    "iframe[src*='captcha']",
    "div[id*='popup']",
    "div[class*='overlay']",
    "div[role='dialog']",
    ".modal-backdrop",
    ".ant-modal-wrap"
]

# Enhanced anti-detection script for better fingerprint evasion
ENHANCED_ANTI_DETECTION_SCRIPT = """
// Remove webdriver traces
delete navigator.__proto__.webdriver;
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

// Realistic plugin simulation
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
        {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
    ]
});

// Enhanced permissions handling
Object.defineProperty(navigator, 'permissions', {
    get: () => ({
        query: (params) => {
            const permissions = {
                'notifications': {state: Notification.permission},
                'geolocation': {state: 'prompt'},
                'camera': {state: 'prompt'},
                'microphone': {state: 'prompt'}
            };
            return Promise.resolve(permissions[params.name] || {state: 'denied'});
        }
    })
});

// Mobile device emulation improvements
Object.defineProperty(screen, 'width', {get: () => 412});
Object.defineProperty(screen, 'height', {get: () => 915});
Object.defineProperty(screen, 'availWidth', {get: () => 412});
Object.defineProperty(screen, 'availHeight', {get: () => 815});

// Anti-fingerprinting
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 5});

// Language simulation
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en-US', 'en']});

// Chrome object for authenticity
window.chrome = {
    runtime: {},
    loadTimes: function() { return {}; },
    csi: function() { return {}; },
    app: {}
};

// Canvas fingerprint randomization
if (typeof HTMLCanvasElement !== 'undefined') {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(...args) {
        // Add slight noise to canvas data
        const ctx = this.getContext('2d');
        if (ctx && Math.random() < 0.1) {  // 10% chance
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const data = imageData.data;
            for (let i = 0; i < data.length; i += 4) {
                if (Math.random() < 0.001) {
                    data[i] = Math.min(255, data[i] + Math.random() * 2 - 1);
                    data[i + 1] = Math.min(255, data[i + 1] + Math.random() * 2 - 1);
                    data[i + 2] = Math.min(255, data[i + 2] + Math.random() * 2 - 1);
                }
            }
            ctx.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, args);
    };
}
"""


async def detect_blocking_elements(page):
    """Detect blocking elements dynamically"""
    return await page.evaluate("""
        () => {
            const elements = document.querySelectorAll('*');
            const blockers = [];
            elements.forEach(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                // Check for overlay characteristics
                if (style.position === 'fixed' && 
                    parseInt(style.zIndex) > 1000 &&
                    rect.width > 200 && rect.height > 100 &&
                    style.display !== 'none') {
                    
                    // Try to generate selector for this element
                    let selector = '';
                    if (el.id) {
                        selector = `#${el.id}`;
                    } else if (el.className) {
                        selector = `.${el.className.split(' ').join('.')}`;
                    } else {
                        selector = el.tagName.toLowerCase();
                    }
                    
                    blockers.push({
                        selector: selector,
                        zIndex: style.zIndex,
                        visible: style.visibility !== 'hidden',
                        width: rect.width,
                        height: rect.height
                    });
                }
            });
            return blockers;
        }
    """)


async def remove_blocking_elements(page, aggressive=False):
    """Remove blocking elements with intelligent detection"""
    removed_count = 0
    
    # 1. Check known blocking selectors first
    for selector in BLOCKING_SELECTORS:
        try:
            element = page.locator(selector)
            if await element.count() > 0:
                # Try to find close button first
                close_btn = element.locator('[class*="close"], [aria-label*="close"], [title*="close"]')
                if await close_btn.count() > 0:
                    await close_btn.click()
                    print(f"Clicked close button for: {selector}")
                else:
                    # Remove entire element if no close button
                    await element.evaluate("el => el.remove()")
                    print(f"Removed blocking element: {selector}")
                removed_count += 1
        except Exception as e:
            if aggressive:
                # Fallback: force removal via JavaScript
                await page.evaluate(f"""
                    try {{
                        document.querySelector('{selector}')?.remove();
                    }} catch(e) {{
                        // Ignore errors during removal
                    }}
                """)
                removed_count += 1
    
    # 2. Dynamic detection for unknown blocking elements
    if feature_settings.advanced_blocking_enabled:
        try:
            blocking_elements = await detect_blocking_elements(page)
            for blocker in blocking_elements:
                selector = blocker['selector']
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        # Try click close button first
                        close_btn = element.locator('[class*="close"], [aria-label*="close"], [title*="close"]')
                        if await close_btn.count() > 0:
                            await close_btn.click()
                        else:
                            await element.evaluate("el => el.remove()")
                        
                        print(f"Removed dynamically detected blocker: {selector} (z-index: {blocker['zIndex']})")
                        removed_count += 1
                except Exception as e:
                    print(f"Failed to remove dynamic blocker: {e}")
        except Exception as e:
            print(f"Dynamic blocking detection failed: {e}")
    
    return removed_count


def _as_bool(value, default: bool = False) -> bool:
    """Convert value to boolean"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value, default: int) -> int:
    """Convert value to integer"""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_rotation_settings(task_config: dict) -> dict:
    account_cfg = task_config.get("account_rotation") or {}
    proxy_cfg = task_config.get("proxy_rotation") or {}

    account_enabled = _as_bool(account_cfg.get("enabled"), _as_bool(os.getenv("ACCOUNT_ROTATION_ENABLED"), False))
    account_mode = (account_cfg.get("mode") or os.getenv("ACCOUNT_ROTATION_MODE", "per_task")).lower()
    account_state_dir = account_cfg.get("state_dir") or os.getenv("ACCOUNT_STATE_DIR", "state")
    account_retry_limit = _as_int(account_cfg.get("retry_limit"), _as_int(os.getenv("ACCOUNT_ROTATION_RETRY_LIMIT"), 2))
    account_blacklist_ttl = _as_int(account_cfg.get("blacklist_ttl_sec"), _as_int(os.getenv("ACCOUNT_BLACKLIST_TTL"), 300))

    proxy_enabled = _as_bool(proxy_cfg.get("enabled"), _as_bool(os.getenv("PROXY_ROTATION_ENABLED"), False))
    proxy_mode = (proxy_cfg.get("mode") or os.getenv("PROXY_ROTATION_MODE", "per_task")).lower()
    proxy_pool = proxy_cfg.get("proxy_pool") or os.getenv("PROXY_POOL", "")
    proxy_retry_limit = _as_int(proxy_cfg.get("retry_limit"), _as_int(os.getenv("PROXY_ROTATION_RETRY_LIMIT"), 2))
    proxy_blacklist_ttl = _as_int(proxy_cfg.get("blacklist_ttl_sec"), _as_int(os.getenv("PROXY_BLACKLIST_TTL"), 300))

    return {
        "account_enabled": account_enabled,
        "account_mode": account_mode,
        "account_state_dir": account_state_dir,
        "account_retry_limit": max(1, account_retry_limit),
        "account_blacklist_ttl": max(0, account_blacklist_ttl),
        "proxy_enabled": proxy_enabled,
        "proxy_mode": proxy_mode,
        "proxy_pool": proxy_pool,
        "proxy_retry_limit": max(1, proxy_retry_limit),
        "proxy_blacklist_ttl": max(0, proxy_blacklist_ttl),
    }


def _default_context_options() -> dict:
    return {
        "user_agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "viewport": {"width": 412, "height": 915},
        "device_scale_factor": 2.625,
        "is_mobile": True,
        "has_touch": True,
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
        "permissions": ["geolocation"],
        "geolocation": {"longitude": 121.4737, "latitude": 31.2304},
        "color_scheme": "light",
    }


def _clean_kwargs(options: dict) -> dict:
    return {k: v for k, v in options.items() if v is not None}


def _looks_like_mobile(ua: str) -> Optional[bool]:
    if not ua:
        return None
    ua_lower = ua.lower()
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        return True
    if "windows" in ua_lower or "macintosh" in ua_lower:
        return False
    return None


def _build_context_overrides(snapshot: dict) -> dict:
    env = snapshot.get("env") or {}
    headers = snapshot.get("headers") or {}
    navigator = env.get("navigator") or {}
    screen = env.get("screen") or {}
    intl = env.get("intl") or {}

    overrides = {}

    ua = headers.get("User-Agent") or headers.get("user-agent") or navigator.get("userAgent")
    if ua:
        overrides["user_agent"] = ua

    accept_language = headers.get("Accept-Language") or headers.get("accept-language")
    locale = None
    if accept_language:
        locale = accept_language.split(",")[0].strip()
    elif navigator.get("language"):
        locale = navigator["language"]
    if locale:
        overrides["locale"] = locale

    tz = intl.get("timeZone")
    if tz:
        overrides["timezone_id"] = tz

    width = screen.get("width")
    height = screen.get("height")
    if isinstance(width, (int, float)) and isinstance(height, (int, float)):
        overrides["viewport"] = {"width": int(width), "height": int(height)}

    dpr = screen.get("devicePixelRatio")
    if isinstance(dpr, (int, float)):
        overrides["device_scale_factor"] = float(dpr)

    touch_points = navigator.get("maxTouchPoints")
    if isinstance(touch_points, (int, float)):
        overrides["has_touch"] = touch_points > 0

    mobile_flag = _looks_like_mobile(ua or "")
    if mobile_flag is not None:
        overrides["is_mobile"] = mobile_flag

    return _clean_kwargs(overrides)


def _build_extra_headers(raw_headers: Optional[dict]) -> dict:
    if not raw_headers:
        return {}
    excluded = {"cookie", "content-length"}
    headers = {}
    for key, value in raw_headers.items():
        if not key or key.lower() in excluded or value is None:
            continue
        headers[key] = value
    return headers


async def scrape_user_profile(context, user_id: str) -> dict:
    """
    【New version】Access the personal homepage of the specified user，Collect its summary information, complete product list and complete review list in order。
    """
    print(f"   -> Start collecting usersID: {user_id} complete information...")
    profile_data = {}
    page = await context.new_page()

    # Prepare for various asynchronous tasksFutureand data container
    head_api_future = asyncio.get_event_loop().create_future()

    all_items, all_ratings = [], []
    stop_item_scrolling, stop_rating_scrolling = asyncio.Event(), asyncio.Event()

    async def handle_response(response: Response):
        # Capture header summaryAPI
        if "mtop.idle.web.user.page.head" in response.url and not head_api_future.done():
            try:
                head_api_future.set_result(await response.json())
                print(f"      [APIcapture] User header information... success")
            except Exception as e:
                if not head_api_future.done(): head_api_future.set_exception(e)

        # Capture product listAPI
        elif "mtop.idle.web.xyh.item.list" in response.url:
            try:
                data = await response.json()
                all_items.extend(data.get('data', {}).get('cardList', []))
                print(f"      [APIcapture] Product list... Currently captured {len(all_items)} pieces")
                if not data.get('data', {}).get('nextPage', True):
                    stop_item_scrolling.set()
            except Exception as e:
                stop_item_scrolling.set()

        # Capture review listAPI
        elif "mtop.idle.web.trade.rate.list" in response.url:
            try:
                data = await response.json()
                all_ratings.extend(data.get('data', {}).get('cardList', []))
                print(f"      [APIcapture] Review list... Currently captured {len(all_ratings)} strip")
                if not data.get('data', {}).get('nextPage', True):
                    stop_rating_scrolling.set()
            except Exception as e:
                stop_rating_scrolling.set()

    page.on("response", handle_response)

    try:
        # --- Task1: Navigate and collect header information ---
        await page.goto(f"https://www.goofish.com/personal?userId={user_id}", wait_until="domcontentloaded", timeout=20000)
        head_data = await asyncio.wait_for(head_api_future, timeout=15)
        profile_data = await parse_user_head_data(head_data)

        # --- Task2: Scroll to load all products (Default page) ---
        print("      [Collection phase] Start collecting the user's product list...")
        await random_sleep(2, 4) # Waiting for the first page of productsAPIFinish
        while not stop_item_scrolling.is_set():
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            try:
                await asyncio.wait_for(stop_item_scrolling.wait(), timeout=8)
            except asyncio.TimeoutError:
                print("      [scroll timeout] The product list may have finished loading。")
                break
        profile_data["Product list posted by seller"] = await _parse_user_items_data(all_items)

        # --- Task3: Click and collect all reviews ---
        print("      [Collection phase] Start collecting the user's evaluation list...")
        rating_tab_locator = page.locator("//div[text()='Credit and evaluation']/ancestor::li")
        if await rating_tab_locator.count() > 0:
            await rating_tab_locator.click()
            await random_sleep(3, 5) # Waiting for first page reviewsAPIFinish

            while not stop_rating_scrolling.is_set():
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                try:
                    await asyncio.wait_for(stop_rating_scrolling.wait(), timeout=8)
                except asyncio.TimeoutError:
                    print("      [scroll timeout] The review list may have finished loading。")
                    break

            profile_data['List of reviews received by the seller'] = await parse_ratings_data(all_ratings)
            reputation_stats = await calculate_reputation_from_ratings(all_ratings)
            profile_data.update(reputation_stats)
        else:
            print("      [warn] Review tab not found, review collection skipped。")

    except Exception as e:
        print(f"   [mistake] Collect users {user_id} An error occurred during the message: {e}")
    finally:
        page.remove_listener("response", handle_response)
        await page.close()
        print(f"   -> user {user_id} Information collection completed。")

    return profile_data


def load_seen_products(task_name: str) -> set:
    """
    Load previously seen product IDs from file
    
    Args:
        task_name: Name of the task
    
    Returns:
        Set of product IDs that have been processed
    """
    state_dir = "state"
    os.makedirs(state_dir, exist_ok=True)
    seen_file = os.path.join(state_dir, f"seen_products_{task_name.replace(' ', '_')}.json")
    
    if os.path.exists(seen_file):
        try:
            with open(seen_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            print(f"   [warn] Failed to load seen products file: {e}")
            return set()
    return set()


def save_seen_products(task_name: str, seen_products: set) -> None:
    """
    Save seen product IDs to file
    
    Args:
        task_name: Name of the task
        seen_products: Set of product IDs to save
    """
    state_dir = "state"
    os.makedirs(state_dir, exist_ok=True)
    seen_file = os.path.join(state_dir, f"seen_products_{task_name.replace(' ', '_')}.json")
    
    try:
        with open(seen_file, 'w', encoding='utf-8') as f:
            json.dump(list(seen_products), f, ensure_ascii=False, indent=2)
        print(f"   [Seller Monitoring] Saved {len(seen_products)} seen product IDs")
    except IOError as e:
        print(f"   [Error] Failed to save seen products: {e}")


async def scrape_seller_products(
    context,
    seller_id: str,
    task_name: str,
    task_config: dict,
    seen_products: set,
    output_filename: str
):
    """
    Monitor all products from a specific seller
    Uses scrape_user_profile to collect all products with pagination
    
    Args:
        context: Playwright browser context
        seller_id: Seller ID on Xianyu
        task_name: Task name
        task_config: Task configuration
        seen_products: Set of already processed product IDs
        output_filename: Output JSONL file path
    
    Returns:
        Number of new products processed
    """
    print(f"   [Seller Monitoring] Starting monitoring for seller {seller_id}...")
    
    # 1. Collect seller profile (includes ALL products via pagination)
    user_profile = await scrape_user_profile(context, seller_id)
    
    # 2. Get product list (already includes all products after scrolling)
    products_list = user_profile.get("Product list posted by seller", [])
    print(f"   [Seller Monitoring] Found {len(products_list)} total products from seller")
    
    # 3. Filter only new products (status "On sale")
    new_products = []
    on_sale_count = 0
    for product in products_list:
        if product.get('Product status') == 'On sale':
            on_sale_count += 1
            product_id = str(product.get('commodityID', ''))
            if product_id and product_id not in seen_products:
                new_products.append(product)
                seen_products.add(product_id)
    
    print(f"   [Seller Monitoring] {on_sale_count} products on sale, {len(new_products)} are new")
    
    # 3.5. Limit products per run if specified
    max_products = task_config.get('max_products_per_run')
    if max_products and max_products > 0 and len(new_products) > max_products:
        print(f"   [Seller Monitoring] Limiting to {max_products} products per run")
        new_products = new_products[:max_products]
    
    # 4. Collect detailed information for each new product
    ai_prompt_text = task_config.get('ai_prompt_text', '')
    processed_count = 0
    
    for idx, product in enumerate(new_products, 1):
        print(f"   [Seller Monitoring] Processing new product {idx}/{len(new_products)}: {product.get('Product title', 'N/A')}")
        detail_page = await context.new_page()
        try:
            product_id = product.get('commodityID')
            product_link = f"https://www.goofish.com/item?id={product_id}"
            
            # Navigate to product page and collect details
            async with detail_page.expect_response(
                lambda r: DETAIL_API_URL_PATTERN in r.url,
                timeout=25000
            ) as detail_info:
                await detail_page.goto(product_link, wait_until="domcontentloaded", timeout=25000)
            
            detail_response = await detail_info.value
            detail_json = await detail_response.json()
            
            # Parse product details
            main_data = await safe_get(detail_json, 'data', 'mainData', default={})
            seller_do = await safe_get(detail_json, 'data', 'sellerDO', default={})
            
            # Build complete product record
            item_title = await safe_get(main_data, "title", default="Unknown")
            item_price = await safe_get(main_data, "price", default="0")
            item_images = await safe_get(main_data, "images", default=[])
            item_desc = await safe_get(main_data, "desc", default="")
            
            reg_days_raw = await safe_get(seller_do, 'userRegDay', default=0)
            registration_duration_text = format_registration_days(reg_days_raw)
            zhima_credit_text = await safe_get(seller_do, 'zhimaLevelInfo', 'levelName')
            
            # Add seller profile info
            user_profile['Seller Sesame Credit'] = zhima_credit_text
            user_profile['Seller registration time'] = registration_duration_text
            
            product_record = {
                "Product information": {
                    "Product link": product_link,
                    "Product title": item_title,
                    "Product price": item_price,
                    "Product main image": item_images[0] if item_images else "",
                    "Product description": item_desc,
                    "Product images": item_images,
                    "Product status": product.get('Product status'),
                },
                "Seller information": user_profile,
                "Task name": task_name,
                "Crawl time": datetime.now().isoformat()
            }
            
            # AI analysis
            if ai_prompt_text and not SKIP_AI_ANALYSIS:
                print(f"   [AI Analysis] Analyzing product...")
                
                # Download images
                task_image_dir = f"{TASK_IMAGE_DIR_PREFIX}{task_name.replace(' ', '_')}"
                os.makedirs(task_image_dir, exist_ok=True)
                
                image_paths = await download_all_images(item_images[:3], task_image_dir)
                
                try:
                    ai_result = await get_ai_analysis(
                        product_record=product_record,
                        image_paths=image_paths,
                        ai_prompt_text=ai_prompt_text
                    )
                    
                    product_record["AI analysis results"] = ai_result
                    
                    # Send notification if recommended
                    is_recommended = ai_result.get("is_recommended", False)
                    if is_recommended:
                        print(f"   [AI Recommendation] Product recommended! Sending notification...")
                        await send_ntfy_notification(product_record, task_config)
                    
                except Exception as e:
                    print(f"   [AI Error] AI analysis failed: {e}")
                    product_record["AI analysis results"] = {"error": str(e)}
            
            # Save to JSONL
            await save_to_jsonl(product_record, output_filename)
            processed_count += 1
            
            # Small delay between products
            await random_sleep(1, 2)
            
        except Exception as e:
            print(f"   [Error] Failed to process product {product.get('commodityID')}: {e}")
        finally:
            await detail_page.close()
    
    print(f"   [Seller Monitoring] Successfully processed {processed_count} new products")
    return processed_count


async def scrape_xianyu(task_config: dict, debug_limit: int = 0):
    """
    【core executor】
    Asynchronously crawl Xianyu product data based on single task configuration，and conduct real-time, independent analysis of each newly discovered itemAIAnalysis and Notification。
    
    Supports two task types:
    - keyword_search: Search by keyword (default)
    - seller_monitoring: Monitor all products from a specific seller
    """
    # Check task type and route to appropriate handler
    task_type = task_config.get('task_type', 'keyword_search')
    task_name = task_config.get('task_name', 'unnamed_task')
    
    if task_type == 'seller_monitoring':
        print(f"LOG: Task '{task_name}' is a seller monitoring task")
        seller_id = task_config.get('seller_id')
        if not seller_id:
            print(f"ERROR: seller_id is required for seller_monitoring tasks")
            return
        
        # Load seen products
        seen_products = load_seen_products(task_name)
        print(f"LOG: Loaded {len(seen_products)} previously seen products")
        
        # Prepare output filename
        output_filename = os.path.join("jsonl", f"seller_{seller_id}_{task_name.replace(' ', '_')}.jsonl")
        
        # Get rotation settings and account
        rotation_settings = _get_rotation_settings(task_config)
        forced_account = task_config.get("account_state_file") or None
        if isinstance(forced_account, str) and not forced_account.strip():
            forced_account = None
        if forced_account:
            rotation_settings["account_enabled"] = False
        account_items = load_state_files(rotation_settings["account_state_dir"])
        if not forced_account and os.path.exists(STATE_FILE):
            account_items = [STATE_FILE]
        if not forced_account and not os.path.exists(STATE_FILE) and account_items:
            rotation_settings["account_enabled"] = True
        
        # Setup browser context
        async with async_playwright() as p:
            context_options = _default_context_options()
            
            # Load account state if available
            if forced_account:
                print(f"LOG: Using forced account: {forced_account}")
                with open(forced_account, "r", encoding="utf-8") as f:
                    storage_state = json.load(f)
                context_options["storage_state"] = storage_state
            elif account_items:
                print(f"LOG: Using first available account: {account_items[0]}")
                with open(account_items[0], "r", encoding="utf-8") as f:
                    storage_state = json.load(f)
                context_options["storage_state"] = storage_state
            
            browser = await p.chromium.launch(headless=RUN_HEADLESS)
            context = await browser.new_context(**context_options)
            
            try:
                # Run seller monitoring
                await scrape_seller_products(
                    context=context,
                    seller_id=seller_id,
                    task_name=task_name,
                    task_config=task_config,
                    seen_products=seen_products,
                    output_filename=output_filename
                )
                
                # Save seen products
                save_seen_products(task_name, seen_products)
                
            finally:
                await context.close()
                await browser.close()
        
        return
    
    # Original keyword search logic
    keyword = task_config['keyword']
    max_pages = task_config.get('max_pages', 1)
    personal_only = task_config.get('personal_only', False)
    min_price = task_config.get('min_price')
    max_price = task_config.get('max_price')
    ai_prompt_text = task_config.get('ai_prompt_text', '')
    free_shipping = task_config.get('free_shipping', False)
    raw_new_publish = task_config.get('new_publish_option') or ''
    new_publish_option = raw_new_publish.strip()
    if new_publish_option == '__none__':
        new_publish_option = ''
    region_filter = (task_config.get('region') or '').strip()

    processed_links = set()
    output_filename = os.path.join("jsonl", f"{keyword.replace(' ', '_')}_full_data.jsonl")
    if os.path.exists(output_filename):
        print(f"LOG: Found file already exists {output_filename}，Loading history for deduplication...")
        try:
            with open(output_filename, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        link = record.get('Product information', {}).get('Product link', '')
                        if link:
                            processed_links.add(get_link_unique_key(link))
                    except json.JSONDecodeError:
                        print(f"   [warn] There is a line in the file that cannot be parsed asJSON，skipped。")
            print(f"LOG: Loading completed, recorded {len(processed_links)} items processed。")
        except IOError as e:
            print(f"   [warn] An error occurred while reading the history file: {e}")
    else:
        print(f"LOG: output file {output_filename} does not exist, a new file will be created。")

    rotation_settings = _get_rotation_settings(task_config)
    forced_account = task_config.get("account_state_file") or None
    if isinstance(forced_account, str) and not forced_account.strip():
        forced_account = None
    if forced_account:
        rotation_settings["account_enabled"] = False
    account_items = load_state_files(rotation_settings["account_state_dir"])
    if not forced_account and os.path.exists(STATE_FILE):
        account_items = [STATE_FILE]
    if not forced_account and not os.path.exists(STATE_FILE) and account_items:
        rotation_settings["account_enabled"] = True

    account_pool = RotationPool(account_items, rotation_settings["account_blacklist_ttl"], "account")
    proxy_pool = RotationPool(parse_proxy_pool(rotation_settings["proxy_pool"]), rotation_settings["proxy_blacklist_ttl"], "proxy")

    selected_account: Optional[RotationItem] = None
    selected_proxy: Optional[RotationItem] = None

    def _select_account(force_new: bool = False) -> Optional[RotationItem]:
        nonlocal selected_account
        if forced_account:
            return RotationItem(value=forced_account)
        if not rotation_settings["account_enabled"]:
            if os.path.exists(STATE_FILE):
                return RotationItem(value=STATE_FILE)
            return None
        if rotation_settings["account_mode"] == "per_task" and selected_account and not force_new:
            return selected_account
        picked = account_pool.pick_random()
        return picked or selected_account

    def _select_proxy(force_new: bool = False) -> Optional[RotationItem]:
        nonlocal selected_proxy
        if not rotation_settings["proxy_enabled"]:
            return None
        if rotation_settings["proxy_mode"] == "per_task" and selected_proxy and not force_new:
            return selected_proxy
        picked = proxy_pool.pick_random()
        return picked or selected_proxy

    async def _run_scrape_attempt(state_file: str, proxy_server: Optional[str]) -> int:
        processed_item_count = 0
        stop_scraping = False

        if not os.path.exists(state_file):
            raise FileNotFoundError(f"Login status file does not exist: {state_file}")

        snapshot_data = None
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                snapshot_data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to read login status file，will be used directly by path: {e}")

        async with async_playwright() as p:
            # Anti-detection startup parameters
            launch_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]

            launch_kwargs = {"headless": RUN_HEADLESS, "args": launch_args}
            if proxy_server:
                launch_kwargs["proxy"] = {"server": proxy_server}

            if LOGIN_IS_EDGE:
                launch_kwargs["channel"] = "msedge"
            else:
                if not RUNNING_IN_DOCKER:
                    launch_kwargs["channel"] = "chrome"

            browser = await p.chromium.launch(**launch_kwargs)

            context_kwargs = _default_context_options()
            storage_state_arg = state_file

            if isinstance(snapshot_data, dict):
                # Enhanced snapshot exported by the new version of the extension, including environment andHeader
                if any(key in snapshot_data for key in ("env", "headers", "page", "storage")):
                    print(f"Enhanced browser snapshot detected, environment parameters applied: {state_file}")
                    storage_state_arg = {"cookies": snapshot_data.get("cookies", [])}
                    context_kwargs.update(_build_context_overrides(snapshot_data))
                    extra_headers = _build_extra_headers(snapshot_data.get("headers"))
                    if extra_headers:
                        context_kwargs["extra_http_headers"] = extra_headers
                else:
                    storage_state_arg = snapshot_data

            context_kwargs = _clean_kwargs(context_kwargs)
            context = await browser.new_context(storage_state=storage_state_arg, **context_kwargs)

            # Enhanced anti-detection script
            if feature_settings.advanced_blocking_enabled:
                await context.add_init_script(ENHANCED_ANTI_DETECTION_SCRIPT)
            else:
                # Fallback to original script for compatibility
                await context.add_init_script("""
                    // Removewebdriverlogo
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

                    // Simulates real mobile devicesnavigatorproperty
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en-US', 'en']});

                    // Add tochromeobject
                    window.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}};

                    // Analog touch support
                    Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 5});

                    // coverpermissionsQuery (avoid exposing automation）
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({state: Notification.permission}) :
                            originalQuery(parameters)
                    );
                """)

            page = await context.new_page()

            try:
                # step 0 - Simulate real users: first visit the homepage（Important anti-detection measures）
                log_time("step 0 - Simulate real users visiting the homepage...")
                await page.goto("https://www.goofish.com/", wait_until="domcontentloaded", timeout=30000)
                log_time("[Climb backward] Stay on the homepage and simulate browsing...")
                await random_sleep(1, 2)

                # Simulate random scrolling (touch scrolling for mobile devices）
                await page.evaluate("window.scrollBy(0, Math.random() * 500 + 200)")
                await random_sleep(1, 2)

                log_time("step 1 - Navigate to the search results page...")
                # use 'q' Parameters build correct searchURL，and proceedURLcoding
                params = {'q': keyword}
                search_url = f"https://www.goofish.com/search?{urlencode(params)}"
                log_time(f"TargetURL: {search_url}")

                # use expect_response Capture initial search while navigatingAPIdata
                async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=30000) as response_info:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

                initial_response = await response_info.value

                # Wait for the page to load the key filter elements to confirm that you have successfully entered the search results page
                await page.wait_for_selector('text=new release', timeout=15000)

                # Simulate real user behavior: initial stay and browsing after page loading
                log_time("[Climb backward] Simulate user viewing page...")
                await random_sleep(1, 3)

                # --- Enhanced blocking detection and removal ---
                if feature_settings.advanced_blocking_enabled:
                    # Use advanced blocking detection
                    removed_count = await remove_blocking_elements(page, aggressive=True)
                    if removed_count > 0:
                        print(f"[Advanced Blocking] Removed {removed_count} blocking elements")
                else:
                    # Fallback to original detection for compatibility
                    baxia_dialog = page.locator("div.baxia-dialog-mask")
                    middleware_widget = page.locator("div.J_MIDDLEWARE_FRAME_WIDGET")
                    try:
                        await baxia_dialog.wait_for(state='visible', timeout=2000)
                        print("\n==================== CRITICAL BLOCK DETECTED ====================")
                        print("Xianyu anti-crawler verification pop-up window detected (baxia-dialog)，Unable to continue operation。")
                        print("This is usually because the operation is too frequent or is recognized as a robot。")
                        print("suggestion：")
                        print("1. Stop the script for a while and try again。")
                        print("2. (recommend) exist .env Set in file RUN_HEADLESS=false，Run in non-headless mode, which helps bypass detection。")
                        print(f"Task '{keyword}' will abort here。")
                        print("===================================================================")
                        raise RiskControlError("baxia-dialog")
                    except PlaywrightTimeoutError:
                        pass

                    try:
                        await middleware_widget.wait_for(state='visible', timeout=2000)
                        print("\n==================== CRITICAL BLOCK DETECTED ====================")
                        print("Xianyu anti-crawler verification pop-up window detected (J_MIDDLEWARE_FRAME_WIDGET)，Unable to continue operation。")
                        print("This is usually because the operation is too frequent or is recognized as a robot。")
                        print("suggestion：")
                        print("1. Stop the script for a while and try again。")
                        print("2. (recommend) Update the login status file to ensure the login status is valid。")
                        print("3. Reduce the frequency of task execution to avoid being recognized as a robot。")
                        print(f"Task '{keyword}' will abort here。")
                        print("===================================================================")
                        raise RiskControlError("J_MIDDLEWARE_FRAME_WIDGET")
                    except PlaywrightTimeoutError:
                        pass
                # --- End enhanced blocking detection ---

                try:
                    await page.click("div[class*='closeIconBg']", timeout=3000)
                    print("LOG: Advertising pop-ups have been closed。")
                except PlaywrightTimeoutError:
                    print("LOG: Advertising pop-ups not detected。")

                final_response = None
                log_time("step 2 - Apply filters...")
                if new_publish_option:
                    try:
                        await page.click('text=new release')
                        await random_sleep(1, 2) # It turned out to be (1.5, 2.5)
                        async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=20000) as response_info:
                            await page.click(f"text={new_publish_option}")
                            # --- Revise: Increase waiting time after sorting ---
                            await random_sleep(2, 4) # It turned out to be (3, 5)
                        final_response = await response_info.value
                    except PlaywrightTimeoutError:
                        log_time(f"New release filter '{new_publish_option}' Request timed out, continue execution。")
                    except Exception as e:
                        print(f"LOG: Applying new release filter failed: {e}")

                if personal_only:
                    async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=20000) as response_info:
                        await page.click('text=Personal idle')
                        # --- Revise: Change the fixed wait to a random wait and lengthen it ---
                        await random_sleep(2, 4) # It turned out to be asyncio.sleep(5)
                    final_response = await response_info.value

                if free_shipping:
                    try:
                        async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=20000) as response_info:
                            await page.click('text=Free shipping')
                            await random_sleep(2, 4)
                        final_response = await response_info.value
                    except PlaywrightTimeoutError:
                        log_time("Free shipping filtering request timed out, continue execution。")
                    except Exception as e:
                        print(f"LOG: Application of free shipping filter failed: {e}")

                if region_filter:
                    try:
                        area_trigger = page.get_by_text("area", exact=True)
                        if await area_trigger.count():
                            await area_trigger.first.click()
                            await random_sleep(1.5, 2)
                            popover_candidates = page.locator("div.ant-popover")
                            popover = popover_candidates.filter(has=page.locator(".areaWrap--FaZHsn8E, [class*='areaWrap']")).last
                            if not await popover.count():
                                popover = popover_candidates.filter(has=page.get_by_text("Reposition")).last
                            if not await popover.count():
                                popover = popover_candidates.filter(has=page.get_by_text("Check")).last
                            if not await popover.count():
                                print("LOG: Area pop-up not found, skip area filtering。")
                                raise PlaywrightTimeoutError("region-popover-not-found")
                            await popover.wait_for(state="visible", timeout=5000)

                            # List container: first level children i.e. province/city/Area three columns, no longer strongly dependent on specific class names，Improve robustness
                            area_wrap = popover.locator(".areaWrap--FaZHsn8E, [class*='areaWrap']").first
                            await area_wrap.wait_for(state="visible", timeout=3000)
                            columns = area_wrap.locator(":scope > div")
                            col_prov = columns.nth(0)
                            col_city = columns.nth(1)
                            col_dist = columns.nth(2)

                            region_parts = [p.strip() for p in region_filter.split('/') if p.strip()]

                            async def _click_in_column(column_locator, text_value: str, desc: str) -> None:
                                option = column_locator.locator(".provItem--QAdOx8nD", has_text=text_value).first
                                if await option.count():
                                    await option.click()
                                    await random_sleep(1.5, 2)
                                    try:
                                        await option.wait_for(state="attached", timeout=1500)
                                        await option.wait_for(state="visible", timeout=1500)
                                    except PlaywrightTimeoutError:
                                        pass
                                else:
                                    print(f"LOG: not found{desc} '{text_value}'，jump over。")

                            if len(region_parts) >= 1:
                                await _click_in_column(col_prov, region_parts[0], "province")
                                await random_sleep(1, 2)
                            if len(region_parts) >= 2:
                                await _click_in_column(col_city, region_parts[1], "City")
                                await random_sleep(1, 2)
                            if len(region_parts) >= 3:
                                await _click_in_column(col_dist, region_parts[2], "district/county")
                                await random_sleep(1, 2)

                            search_btn = popover.locator("div.searchBtn--Ic6RKcAb").first
                            if await search_btn.count():
                                try:
                                    async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=20000) as response_info:
                                        await search_btn.click()
                                        await random_sleep(2, 3)
                                    final_response = await response_info.value
                                except PlaywrightTimeoutError:
                                    log_time("Regional filtering submission timed out, continue execution。")
                            else:
                                print("LOG: Area not found pop-up window \"ViewXX\\\"Baby\\\" button,FF0CSkip submission。")
                        else:
                            print("LOG: Region filter trigger not found。")
                    except PlaywrightTimeoutError:
                        log_time(f"Area filter '{region_filter}' Request timed out, continue execution。")
                    except Exception as e:
                        print(f"LOG: Apply regional filter '{region_filter}' fail: {e}")

                if min_price or max_price:
                    price_container = page.locator('div[class*="search-price-input-container"]').first
                    if await price_container.is_visible():
                        if min_price:
                            await price_container.get_by_placeholder("¥").first.fill(min_price)
                            # --- Revise: Change fixed wait to random wait ---
                            await random_sleep(1, 2.5) # It turned out to be asyncio.sleep(5)
                        if max_price:
                            await price_container.get_by_placeholder("¥").nth(1).fill(max_price)
                            # --- Revise: Change fixed wait to random wait ---
                            await random_sleep(1, 2.5) # It turned out to be asyncio.sleep(5)

                        async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=20000) as response_info:
                            await page.keyboard.press('Tab')
                            # --- Revise: Increase the waiting time after confirming the price ---
                            await random_sleep(2, 4) # It turned out to be asyncio.sleep(5)
                        final_response = await response_info.value
                    else:
                        print("LOG: warn - Price input container not found。")

                log_time("All screening has been completed and product list processing has begun....")

                current_response = final_response if final_response and final_response.ok else initial_response
                for page_num in range(1, max_pages + 1):
                    if stop_scraping:
                        break
                    log_time(f"Start processing the {page_num}/{max_pages} Page ...")

                    if page_num > 1:
                        # Find "Next Page" that is not disabled”button. Xianyu added by 'disabled' class name to disable the button instead of using disabled property。
                        next_btn = page.locator("[class*='search-pagination-arrow-right']:not([class*='disabled'])")
                        if not await next_btn.count():
                            log_time("Reached last page, no available ones found‘Next’ button，Stop turning pages。")
                            break
                        try:
                            async with page.expect_response(lambda r: API_URL_PATTERN in r.url, timeout=20000) as response_info:
                                await next_btn.click()
                                # --- Revise: Increase the waiting time after turning pages ---
                                await random_sleep(2, 5) # It turned out to be (1.5, 3.5)
                            current_response = await response_info.value
                        except PlaywrightTimeoutError:
                            log_time(f"Turn page to page {page_num} Page timeout, stop turning pages。")
                            break

                    if not (current_response and current_response.ok):
                        log_time(f"No. {page_num} Page response is invalid and skipped。")
                        continue

                    basic_items = await _parse_search_results_json(await current_response.json(), f"No. {page_num} Page")
                    if not basic_items:
                        break

                    total_items_on_page = len(basic_items)
                    for i, item_data in enumerate(basic_items, 1):
                        if debug_limit > 0 and processed_item_count >= debug_limit:
                            log_time(f"Debugging limit reached ({debug_limit})，Stop getting new items。")
                            stop_scraping = True
                            break

                        unique_key = get_link_unique_key(item_data["Product link"])
                        if unique_key in processed_links:
                            log_time(f"[In-page progress {i}/{total_items_on_page}] commodity '{item_data['Product title'][:20]}...' Already exists, skip。")
                            continue

                        log_time(f"[In-page progress {i}/{total_items_on_page}] Discover new products and get details: {item_data['Product title'][:30]}...")
                        # --- Revise: The waiting time before accessing the details page. The simulated user looks at the list page for a while. ---
                        await random_sleep(2, 4) # It turned out to be (2, 4)

                        detail_page = await context.new_page()
                        try:
                            async with detail_page.expect_response(lambda r: DETAIL_API_URL_PATTERN in r.url, timeout=25000) as detail_info:
                                await detail_page.goto(item_data["Product link"], wait_until="domcontentloaded", timeout=25000)

                            detail_response = await detail_info.value
                            if detail_response.ok:
                                detail_json = await detail_response.json()

                                ret_string = str(await safe_get(detail_json, 'ret', default=[]))
                                if "FAIL_SYS_USER_VALIDATE" in ret_string:
                                    print("\n==================== CRITICAL BLOCK DETECTED ====================")
                                    print("Xianyu anti-crawler verification detected (FAIL_SYS_USER_VALIDATE)，The program will terminate。")
                                    long_sleep_duration = random.randint(3, 60)
                                    print(f"To avoid account risks, a long hibernation will be performed ({long_sleep_duration} Second) then exit...")
                                    await asyncio.sleep(long_sleep_duration)
                                    print("Long hibernation has ended and will now exit safely。")
                                    print("===================================================================")
                                    raise RiskControlError("FAIL_SYS_USER_VALIDATE")

                                # Parse product details data and update item_data
                                item_do = await safe_get(detail_json, 'data', 'itemDO', default={})
                                seller_do = await safe_get(detail_json, 'data', 'sellerDO', default={})

                                reg_days_raw = await safe_get(seller_do, 'userRegDay', default=0)
                                registration_duration_text = format_registration_days(reg_days_raw)

                                # --- START: Add code block ---

                                # 1. Extract seller’s Zhima credit information
                                zhima_credit_text = await safe_get(seller_do, 'zhimaLevelInfo', 'levelName')

                                # 2. Extract the complete image list of this product
                                image_infos = await safe_get(item_do, 'imageInfos', default=[])
                                if image_infos:
                                    # Use list comprehension to get all valid imagesURL
                                    all_image_urls = [img.get('url') for img in image_infos if img.get('url')]
                                    if all_image_urls:
                                        # Use a new field to store the image list, replacing the old single link
                                        item_data['Product picture list'] = all_image_urls
                                        # (Optional) Still keeping the link to the main image, just in case
                                        item_data['Product main image link'] = all_image_urls[0]

                                # --- END: Add code block ---
                                item_data['“"Want" number of people'] = await safe_get(item_do, 'wantCnt', default=item_data.get('“"Want" number of people', 'NaN'))
                                item_data['Views'] = await safe_get(item_do, 'browseCnt', default='-')
                                # ...[Here you can add more product information parsed from the details page]...

                                # Call the core function to collect seller information
                                user_profile_data = {}
                                user_id = await safe_get(seller_do, 'sellerId')
                                if user_id:
                                    # New, efficient calling method:
                                    user_profile_data = await scrape_user_profile(context, str(user_id))
                                else:
                                    print("   [warn] Unable to obtain detailsAPIObtain the seller fromID。")
                                user_profile_data['Seller Sesame Credit'] = zhima_credit_text
                                user_profile_data['Seller registration time'] = registration_duration_text

                                # Build base records
                                final_record = {
                                    "Crawl time": datetime.now().isoformat(),
                                    "Search keywords": keyword,
                                    "Task name": task_config.get('task_name', 'Untitled Task'),
                                    "Product information": item_data,
                                    "Seller information": user_profile_data
                                }

                                # --- START: Real-time AI Analysis & Notification ---
                                from src.config import SKIP_AI_ANALYSIS

                                # Check if skippedAIAnalyze and send notifications directly
                                if SKIP_AI_ANALYSIS:
                                    log_time("environment variables SKIP_AI_ANALYSIS Already set, skipAIAnalyze and send notifications directly...")
                                    # Download pictures
                                    image_urls = item_data.get('Product picture list', [])
                                    downloaded_image_paths = await download_all_images(item_data['commodityID'], image_urls, task_config.get('task_name', 'default'))

                                    # Delete downloaded image files to save space
                                    for img_path in downloaded_image_paths:
                                        try:
                                            if os.path.exists(img_path):
                                                os.remove(img_path)
                                                print(f"   [picture] Temporary image files deleted: {img_path}")
                                        except Exception as e:
                                            print(f"   [picture] Error deleting picture file: {e}")

                                    # Send notifications directly to mark all products as recommended
                                    log_time("Product skippedAIAnalyze and prepare notifications...")
                                    await send_ntfy_notification(item_data, "Product skippedAIAnalysis, direct notification")
                                else:
                                    log_time(f"start product #{item_data['commodityID']} perform real-timeAIanalyze...")
                                    # 1. Download images
                                    image_urls = item_data.get('Product picture list', [])
                                    downloaded_image_paths = await download_all_images(item_data['commodityID'], image_urls, task_config.get('task_name', 'default'))

                                    # 2. Get AI analysis
                                    ai_analysis_result = None
                                    if ai_prompt_text:
                                        try:
                                            # Note: Here we pass the entire record toAI，Give it the fullest context
                                            ai_analysis_result = await get_ai_analysis(final_record, downloaded_image_paths, prompt_text=ai_prompt_text)
                                            if ai_analysis_result:
                                                final_record['ai_analysis'] = ai_analysis_result
                                                log_time(f"AIAnalysis completed. Recommended status: {ai_analysis_result.get('is_recommended')}")
                                            else:
                                                final_record['ai_analysis'] = {'error': 'AI analysis returned None after retries.'}
                                        except Exception as e:
                                            print(f"   -> AIA serious error occurred during analysis: {e}")
                                            final_record['ai_analysis'] = {'error': str(e)}
                                    else:
                                        print("   -> Task not configuredAI prompt，skip analysis。")

                                    # Delete downloaded image files to save space
                                    for img_path in downloaded_image_paths:
                                        try:
                                            if os.path.exists(img_path):
                                                os.remove(img_path)
                                                print(f"   [picture] Temporary image files deleted: {img_path}")
                                        except Exception as e:
                                            print(f"   [picture] Error deleting picture file: {e}")

                                    # 3. Send notification if recommended
                                    if ai_analysis_result and ai_analysis_result.get('is_recommended'):
                                        log_time("Product quiltAIRecommended, ready to send notification...")
                                        await send_ntfy_notification(item_data, ai_analysis_result.get("reason", "none"))
                                # --- END: Real-time AI Analysis & Notification ---

                                # 4. Save containsAIFull record of results
                                await save_to_jsonl(final_record, keyword)

                                processed_links.add(unique_key)
                                processed_item_count += 1
                                log_time(f"The product processing process is completed. Cumulative processing {processed_item_count} new items。")

                                # --- Revise: Adds major delay after single item processing ---
                                log_time("[Climb backward] Perform a major random delay to simulate user browsing intervals...")
                                await random_sleep(5, 10)
                            else:
                                print(f"   mistake: Get product detailsAPIResponse failed, status code: {detail_response.status}")
                                if AI_DEBUG_MODE:
                                    print(f"--- [DETAIL DEBUG] FAILED RESPONSE from {item_data['Product link']} ---")
                                    try:
                                        print(await detail_response.text())
                                    except Exception as e:
                                        print(f"Unable to read response content: {e}")
                                    print("----------------------------------------------------")

                        except PlaywrightTimeoutError:
                            print(f"   mistake: Visit the product details page or waitAPIResponse timeout。")
                        except Exception as e:
                            print(f"   mistake: An unknown error occurred while processing product listings: {e}")
                        finally:
                            await detail_page.close()
                            # --- Revise: Increase the short cleaning time after closing the page ---
                            await random_sleep(2, 4) # It turned out to be (1, 2.5)

                    # --- New: After processing all the products on a page, before turning the page，Add a longer "break"”time ---
                    if not stop_scraping and page_num < max_pages:
                        print(f"--- No. {page_num} Page processing completed, ready to turn pages。Perform a long break between pages... ---")
                        await random_sleep(10, 15)

            except PlaywrightTimeoutError as e:
                print(f"\nOperation timeout error: The page element or network response did not appear within the specified time。\n{e}")
                raise
            except asyncio.CancelledError:
                log_time("A cancellation signal has been received and the current crawler task is being terminated....")
                raise
            except Exception as e:
                if type(e).__name__ == "TargetClosedError":
                    log_time("The browser has been closed, ignore subsequent exceptions（Maybe the task was stopped）。")
                    return processed_item_count
                print(f"\nAn unknown error occurred during crawling: {e}")
                raise
            finally:
                log_time("After the task is completed, the browser will5Automatically shut down after seconds...")
                await asyncio.sleep(5)
                if debug_limit:
                    input("Press the Enter key to close the browser...")
                await browser.close()

        return processed_item_count

    processed_item_count = 0
    attempt_limit = max(rotation_settings["account_retry_limit"], rotation_settings["proxy_retry_limit"], 1)
    last_error = ""

    for attempt in range(1, attempt_limit + 1):
        if attempt == 1:
            selected_account = _select_account()
            selected_proxy = _select_proxy()
        else:
            if rotation_settings["account_enabled"] and rotation_settings["account_mode"] == "on_failure":
                account_pool.mark_bad(selected_account, last_error)
                selected_account = _select_account(force_new=True)
            if rotation_settings["proxy_enabled"] and rotation_settings["proxy_mode"] == "on_failure":
                proxy_pool.mark_bad(selected_proxy, last_error)
                selected_proxy = _select_proxy(force_new=True)

        if rotation_settings["account_enabled"] and not selected_account:
            print("No available login status file found, task cannot be continued。")
            break
        if not rotation_settings["account_enabled"] and not selected_account:
            print("No available login status file found, task cannot be continued。")
            break
        if rotation_settings["proxy_enabled"] and not selected_proxy:
            print("No available proxy address was found and the task cannot be continued.。")
            break

        state_path = selected_account.value if selected_account else STATE_FILE
        proxy_server = selected_proxy.value if selected_proxy else None
        if rotation_settings["account_enabled"]:
            print(f"Account rotation: use logged-in status {state_path}")
        if rotation_settings["proxy_enabled"] and proxy_server:
            print(f"IP Rotation: Using a proxy {proxy_server}")

        try:
            processed_item_count += await _run_scrape_attempt(state_path, proxy_server)
            break
        except RiskControlError as e:
            last_error = str(e)
            print(f"Risk control or verification trigger detected: {e}")
            if attempt < attempt_limit:
                print("Will try to rotate account/IP Try again later...")
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            print(f"This attempt failed: {last_error}")
            if attempt < attempt_limit:
                print("Will try to rotate account/IP Try again later...")

    # Clean up task picture directory
    cleanup_task_images(task_config.get('task_name', 'default'))

    return processed_item_count
