import asyncio
import base64
import json
import os
import re
import sys
import shutil
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

import requests

# Set standard output encoding toUTF-8，solveWindowsConsole encoding issue
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from src.config import (
    AI_DEBUG_MODE,
    IMAGE_DOWNLOAD_HEADERS,
    IMAGE_SAVE_DIR,
    TASK_IMAGE_DIR_PREFIX,
    MODEL_NAME,
    NTFY_TOPIC_URL,
    GOTIFY_URL,
    GOTIFY_TOKEN,
    BARK_URL,
    PCURL_TO_MOBILE,
    WX_BOT_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    WEBHOOK_URL,
    WEBHOOK_METHOD,
    WEBHOOK_HEADERS,
    WEBHOOK_CONTENT_TYPE,
    WEBHOOK_QUERY_PARAMETERS,
    WEBHOOK_BODY,
    ENABLE_RESPONSE_FORMAT,
    client,
)
from src.utils import convert_goofish_link, retry_on_failure


def safe_print(text):
    """Safe printing functions that handle encoding errors"""
    try:
        print(text)
    except UnicodeEncodeError:
        # If you encounter encoding errors, try usingASCIIEncode and ignore unencodable characters
        try:
            print(text.encode('ascii', errors='ignore').decode('ascii'))
        except:
            # If it still fails, print a simplified message
            print("[Output contains characters that cannot be displayed]")


@retry_on_failure(retries=2, delay=3)
async def _download_single_image(url, save_path):
    """An internal function with retries for asynchronously downloading a single image。"""
    loop = asyncio.get_running_loop()
    # use run_in_executor run synchronized requests code to avoid blocking the event loop
    response = await loop.run_in_executor(
        None,
        lambda: requests.get(url, headers=IMAGE_DOWNLOAD_HEADERS, timeout=20, stream=True)
    )
    response.raise_for_status()
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return save_path


async def download_all_images(product_id, image_urls, task_name="default"):
    """Download all images of a product asynchronously. Skip if image already exists。Support task isolation。"""
    if not image_urls:
        return []

    # Create separate image directories for each task
    task_image_dir = os.path.join(IMAGE_SAVE_DIR, f"{TASK_IMAGE_DIR_PREFIX}{task_name}")
    os.makedirs(task_image_dir, exist_ok=True)

    urls = [url.strip() for url in image_urls if url.strip().startswith('http')]
    if not urls:
        return []

    saved_paths = []
    total_images = len(urls)
    for i, url in enumerate(urls):
        try:
            clean_url = url.split('.heic')[0] if '.heic' in url else url
            file_name_base = os.path.basename(clean_url).split('?')[0]
            file_name = f"product_{product_id}_{i + 1}_{file_name_base}"
            file_name = re.sub(r'[\\/*?:"<>|]', "", file_name)
            if not os.path.splitext(file_name)[1]:
                file_name += ".jpg"

            save_path = os.path.join(task_image_dir, file_name)

            if os.path.exists(save_path):
                safe_print(f"   [picture] picture {i + 1}/{total_images} Already exists, skip download: {os.path.basename(save_path)}")
                saved_paths.append(save_path)
                continue

            safe_print(f"   [picture] Downloading pictures {i + 1}/{total_images}: {url}")
            if await _download_single_image(url, save_path):
                safe_print(f"   [picture] picture {i + 1}/{total_images} Successfully downloaded to: {os.path.basename(save_path)}")
                saved_paths.append(save_path)
        except Exception as e:
            safe_print(f"   [picture] Process pictures {url} An error occurred and this image has been skipped: {e}")

    return saved_paths


def cleanup_task_images(task_name):
    """Clean up the picture directory of the specified task"""
    task_image_dir = os.path.join(IMAGE_SAVE_DIR, f"{TASK_IMAGE_DIR_PREFIX}{task_name}")
    if os.path.exists(task_image_dir):
        try:
            shutil.rmtree(task_image_dir)
            safe_print(f"   [clean up] Task deleted '{task_name}' Temporary picture directory: {task_image_dir}")
        except Exception as e:
            safe_print(f"   [clean up] Delete task '{task_name}' An error occurred while creating the temporary image directory: {e}")
    else:
        safe_print(f"   [clean up] Task '{task_name}' The temporary picture directory does not exist: {task_image_dir}")


def cleanup_ai_logs(logs_dir: str, keep_days: int = 1) -> None:
    try:
        cutoff = datetime.now() - timedelta(days=keep_days)
        for filename in os.listdir(logs_dir):
            if not filename.endswith(".log"):
                continue
            try:
                timestamp = datetime.strptime(filename[:15], "%Y%m%d_%H%M%S")
            except ValueError:
                continue
            if timestamp < cutoff:
                os.remove(os.path.join(logs_dir, filename))
    except Exception as e:
        safe_print(f"   [log] clean upAIError while logging: {e}")


def encode_image_to_base64(image_path):
    """Encode local image files to Base64 string。"""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        safe_print(f"Error while encoding image: {e}")
        return None


def validate_ai_response_format(parsed_response):
    """verifyAIWhether the response is formatted according to the expected structure"""
    required_fields = [
        "prompt_version",
        "is_recommended",
        "reason",
        "risk_tags",
        "criteria_analysis"
    ]

    # Check top-level fields
    for field in required_fields:
        if field not in parsed_response:
            safe_print(f"   [AIanalyze] Warning: Response is missing a required field '{field}'")
            return False

    # examinecriteria_analysisWhether it is a dictionary and not empty
    criteria_analysis = parsed_response.get("criteria_analysis", {})
    if not isinstance(criteria_analysis, dict) or not criteria_analysis:
        safe_print("   [AIanalyze] warn：criteria_analysisMust be a non-empty dictionary")
        return False

    # examineseller_typeField (required for all products）
    if "seller_type" not in criteria_analysis:
        safe_print("   [AIanalyze] warn：criteria_analysisMissing required field 'seller_type'")
        return False

    # Check data type
    if not isinstance(parsed_response.get("is_recommended"), bool):
        safe_print("   [AIanalyze] warn：is_recommendedField is not of type boolean")
        return False

    if not isinstance(parsed_response.get("risk_tags"), list):
        safe_print("   [AIanalyze] warn：risk_tagsField is not a list type")
        return False

    return True


@retry_on_failure(retries=3, delay=5)
async def send_ntfy_notification(product_data, reason):
    """When a recommended product is found, a high-priority message is sent asynchronously ntfy.sh notify。"""
    if not NTFY_TOPIC_URL and not WX_BOT_URL and not (GOTIFY_URL and GOTIFY_TOKEN) and not BARK_URL and not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) and not WEBHOOK_URL:
        safe_print("Warning: not present .env Configure any notification services in the file (NTFY_TOPIC_URL, WX_BOT_URL, GOTIFY_URL/TOKEN, BARK_URL, TELEGRAM_BOT_TOKEN/CHAT_ID, WEBHOOK_URL)，Skip notification。")
        return

    title = product_data.get('Product title', 'N/A')
    price = product_data.get('Current selling price', 'N/A')
    link = product_data.get('Product link', '#')
    if PCURL_TO_MOBILE:
        mobile_link = convert_goofish_link(link)
        message = f"price: {price}\nreason: {reason}\nMobile link: {mobile_link}\nPC link: {link}"
    else:
        message = f"price: {price}\nreason: {reason}\nLink: {link}"

    notification_title = f"🚨 New recommendations! {title[:30]}..."

    # --- send ntfy notify ---
    if NTFY_TOPIC_URL:
        try:
            safe_print(f"   -> Sending ntfy Notified: {NTFY_TOPIC_URL}")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: requests.post(
                    NTFY_TOPIC_URL,
                    data=message.encode('utf-8'),
                    headers={
                        "Title": notification_title.encode('utf-8'),
                        "Priority": "urgent",
                        "Tags": "bell,vibration"
                    },
                    timeout=10
                )
            )
            safe_print("   -> ntfy Notification sent successfully。")
        except Exception as e:
            safe_print(f"   -> send ntfy Notification failed: {e}")

    # --- send Gotify notify ---
    if GOTIFY_URL and GOTIFY_TOKEN:
        try:
            safe_print(f"   -> Sending Gotify Notified: {GOTIFY_URL}")
            # Gotify uses multipart/form-data
            payload = {
                'title': (None, notification_title),
                'message': (None, message),
                'priority': (None, '5')
            }

            gotify_url_with_token = f"{GOTIFY_URL}/message?token={GOTIFY_TOKEN}"

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    gotify_url_with_token,
                    files=payload,
                    timeout=10
                )
            )
            response.raise_for_status()
            safe_print("   -> Gotify Notification sent successfully。")
        except requests.exceptions.RequestException as e:
            safe_print(f"   -> send Gotify Notification failed: {e}")
        except Exception as e:
            safe_print(f"   -> send Gotify An unknown error occurred while notifying: {e}")

    # --- send Bark notify ---
    if BARK_URL:
        try:
            safe_print(f"   -> Sending Bark notify...")

            bark_payload = {
                "title": notification_title,
                "body": message,
                "level": "timeSensitive",
                "group": "Xianyu monitoring"
            }

            link_to_use = convert_goofish_link(link) if PCURL_TO_MOBILE else link
            bark_payload["url"] = link_to_use

            # Add icon if available
            main_image = product_data.get('Product main image link')
            if not main_image:
                # Fallback to image list if main image not present
                image_list = product_data.get('Product picture list', [])
                if image_list:
                    main_image = image_list[0]

            if main_image:
                bark_payload['icon'] = main_image

            headers = { "Content-Type": "application/json; charset=utf-8" }
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    BARK_URL,
                    json=bark_payload,
                    headers=headers,
                    timeout=10
                )
            )
            response.raise_for_status()
            safe_print("   -> Bark Notification sent successfully。")
        except requests.exceptions.RequestException as e:
            safe_print(f"   -> send Bark Notification failed: {e}")
        except Exception as e:
            safe_print(f"   -> send Bark An unknown error occurred while notifying: {e}")

    # --- Send enterprise WeChat robot notifications ---
    if WX_BOT_URL:
        # Convert message toMarkdownFormat to make the link clickable
        lines = message.split('\n')
        markdown_content = f"## {notification_title}\n\n"

        for line in lines:
            if line.startswith('Mobile link:') or line.startswith('PC link:') or line.startswith('Link:'):
                # Extract the link part and convert toMarkdownhyperlink
                if ':' in line:
                    label, url = line.split(':', 1)
                    url = url.strip()
                    if url and url != '#':
                        markdown_content += f"- **{label}:** [{url}]({url})\n"
                    else:
                        markdown_content += f"- **{label}:** No link yet\n"
                else:
                    markdown_content += f"- {line}\n"
            else:
                # Leave other lines as is
                if line:
                    markdown_content += f"- {line}\n"
                else:
                    markdown_content += "\n"

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": markdown_content
            }
        }

        try:
            safe_print(f"   -> Sending corporate WeChat notification to: {WX_BOT_URL}")
            headers = { "Content-Type": "application/json" }
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    WX_BOT_URL,
                    json=payload,
                    headers=headers,
                    timeout=10
                )
            )
            response.raise_for_status()
            result = response.json()
            safe_print(f"   -> The corporate WeChat notification was sent successfully. response: {result}")
        except requests.exceptions.RequestException as e:
            safe_print(f"   -> Failed to send corporate WeChat notification: {e}")
        except Exception as e:
            safe_print(f"   -> An unknown error occurred while sending corporate WeChat notifications: {e}")

    # --- send Telegram Bot notifications ---
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            safe_print(f"   -> Sending Telegram notify...")
            
            # build Telegram API URL
            telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            # Format message content
            telegram_message = f"🚨 <b>New recommendations!</b>\n\n"
            telegram_message += f"<b>{title[:50]}...</b>\n\n"
            telegram_message += f"💰 price: {price}\n"
            telegram_message += f"📝 reason: {reason}\n"
            
            # Add link
            if PCURL_TO_MOBILE:
                mobile_link = convert_goofish_link(link)
                telegram_message += f"📱 <a href='{mobile_link}'>Mobile link</a>\n"
            telegram_message += f"💻 <a href='{link}'>PC link</a>"
            
            # Build request payload
            telegram_payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": telegram_message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            
            headers = {"Content-Type": "application/json"}
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    telegram_api_url,
                    json=telegram_payload,
                    headers=headers,
                    timeout=10
                )
            )
            response.raise_for_status()
            result = response.json()
            if result.get("ok"):
                safe_print("   -> Telegram Notification sent successfully。")
            else:
                safe_print(f"   -> Telegram Notification failed to send: {result.get('description', 'unknown error')}")
        except requests.exceptions.RequestException as e:
            safe_print(f"   -> send Telegram Notification failed: {e}")
        except Exception as e:
            safe_print(f"   -> send Telegram An unknown error occurred while notifying: {e}")

    # --- send universal Webhook notify ---
    if WEBHOOK_URL:
        try:
            safe_print(f"   -> Sending general Webhook Notified: {WEBHOOK_URL}")

            # replace placeholder
            def replace_placeholders(template_str):
                if not template_str:
                    return ""
                # perform contentJSONEscape to avoid breaking newlines and special charactersJSONFormat
                safe_title = json.dumps(notification_title, ensure_ascii=False)[1:-1]  # Remove outer quotes
                safe_content = json.dumps(message, ensure_ascii=False)[1:-1]  # Remove outer quotes
                # Also supports old${title}${content}and new{{title}}{{content}}Format
                return template_str.replace("${title}", safe_title).replace("${content}", safe_content).replace("{{title}}", safe_title).replace("{{content}}", safe_content)

            # Prepare request header
            headers = {}
            if WEBHOOK_HEADERS:
                try:
                    headers = json.loads(WEBHOOK_HEADERS)
                except json.JSONDecodeError:
                    safe_print(f"   -> [warn] Webhook The request header format is wrong, please check .env in WEBHOOK_HEADERS。")

            loop = asyncio.get_running_loop()

            if WEBHOOK_METHOD == "GET":
                # Prepare query parameters
                final_url = WEBHOOK_URL
                if WEBHOOK_QUERY_PARAMETERS:
                    try:
                        params_str = replace_placeholders(WEBHOOK_QUERY_PARAMETERS)
                        params = json.loads(params_str)

                        # parse rawURLand append new parameters
                        url_parts = list(urlparse(final_url))
                        query = dict(parse_qsl(url_parts[4]))
                        query.update(params)
                        url_parts[4] = urlencode(query)
                        final_url = urlunparse(url_parts)
                    except json.JSONDecodeError:
                        safe_print(f"   -> [warn] Webhook Query parameter format is wrong, please check .env in WEBHOOK_QUERY_PARAMETERS。")

                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(final_url, headers=headers, timeout=15)
                )

            elif WEBHOOK_METHOD == "POST":
                # PrepareURL（Handle query parameters）
                final_url = WEBHOOK_URL
                if WEBHOOK_QUERY_PARAMETERS:
                    try:
                        params_str = replace_placeholders(WEBHOOK_QUERY_PARAMETERS)
                        params = json.loads(params_str)

                        # parse rawURLand append new parameters
                        url_parts = list(urlparse(final_url))
                        query = dict(parse_qsl(url_parts[4]))
                        query.update(params)
                        url_parts[4] = urlencode(query)
                        final_url = urlunparse(url_parts)
                    except json.JSONDecodeError:
                        safe_print(f"   -> [warn] Webhook Query parameter format is wrong, please check .env in WEBHOOK_QUERY_PARAMETERS。")

                # Prepare request body
                data = None
                json_payload = None

                if WEBHOOK_BODY:
                    body_str = replace_placeholders(WEBHOOK_BODY)
                    try:
                        if WEBHOOK_CONTENT_TYPE == "JSON":
                            json_payload = json.loads(body_str)
                            if 'Content-Type' not in headers and 'content-type' not in headers:
                                headers['Content-Type'] = 'application/json; charset=utf-8'
                        elif WEBHOOK_CONTENT_TYPE == "FORM":
                            data = json.loads(body_str)  # requestsWill handle iturl-encoding
                            if 'Content-Type' not in headers and 'content-type' not in headers:
                                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                        else:
                            safe_print(f"   -> [warn] Not supported WEBHOOK_CONTENT_TYPE: {WEBHOOK_CONTENT_TYPE}。")
                    except json.JSONDecodeError:
                        safe_print(f"   -> [warn] Webhook The request body format is wrong, please check .env in WEBHOOK_BODY。")

                response = await loop.run_in_executor(
                    None,
                    lambda: requests.post(final_url, headers=headers, json=json_payload, data=data, timeout=15)
                )
            else:
                safe_print(f"   -> [warn] Not supported WEBHOOK_METHOD: {WEBHOOK_METHOD}。")
                return

            response.raise_for_status()
            safe_print(f"   -> Webhook Notification sent successfully. status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            safe_print(f"   -> send Webhook Notification failed: {e}")
        except Exception as e:
            safe_print(f"   -> send Webhook An unknown error occurred while notifying: {e}")


@retry_on_failure(retries=3, delay=5)
async def get_ai_analysis(product_data, image_paths=None, prompt_text=""):
    """complete productJSONData and all images are sent to AI Perform analysis (asynchronous）。"""
    if not client:
        safe_print("   [AIanalyze] mistake：AIThe client is not initialized and analysis is skipped.。")
        return None

    item_info = product_data.get('Product information', {})
    product_id = item_info.get('commodityID', 'N/A')

    safe_print(f"\n   [AIanalyze] Start analyzing products #{product_id} (Contains {len(image_paths or [])} pictures)...")
    safe_print(f"   [AIanalyze] title: {item_info.get('Product title', 'none')}")

    if not prompt_text:
        safe_print("   [AIanalyze] Error: Not providedAIrequired for analysisprompttext。")
        return None

    product_details_json = json.dumps(product_data, ensure_ascii=False, indent=2)
    system_prompt = prompt_text

    if AI_DEBUG_MODE:
        safe_print("\n--- [AI DEBUG] ---")
        safe_print("--- PRODUCT DATA (JSON) ---")
        safe_print(product_details_json)
        safe_print("--- PROMPT TEXT (full content) ---")
        safe_print(prompt_text)
        safe_print("-------------------\n")

    combined_text_prompt = f"""Please analyze the complete offer below based on your expertise and my requirementsJSONdata：

```json
    {product_details_json}
```

{system_prompt}
"""
    user_content_list = []

    # Add image content first
    if image_paths:
        for path in image_paths:
            base64_image = encode_image_to_base64(path)
            if base64_image:
                user_content_list.append(
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

    # Add text content
    user_content_list.append({"type": "text", "text": combined_text_prompt})

    messages = [{"role": "user", "content": user_content_list}]

    # Save final transfer content to log file
    try:
        # createlogsfolder
        logs_dir = os.path.join("logs", "ai")
        os.makedirs(logs_dir, exist_ok=True)
        cleanup_ai_logs(logs_dir, keep_days=1)

        # Generate log file name (current time）
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{current_time}.log"
        log_filepath = os.path.join(logs_dir, log_filename)

        task_name = product_data.get("Task name") or product_data.get("Task name") or "unknown"
        log_payload = {
            "timestamp": current_time,
            "task_name": task_name,
            "product_id": product_id,
            "title": item_info.get("Product title", "none"),
            "image_count": len(image_paths or []),
        }
        log_content = json.dumps(log_payload, ensure_ascii=False)

        # Write to log file
        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write(log_content)

        safe_print(f"   [log] AIAnalysis request saved to: {log_filepath}")

    except Exception as e:
        safe_print(f"   [log] saveAIAn error occurred while parsing the log: {e}")

    # enhancedAICall, including stricter format control and retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Adjust parameters based on the number of retries
            current_temperature = 0.1 if attempt == 0 else 0.05  # Use lower temperature when retrying

            from src.config import get_ai_request_params
            
            # Build request parameters, based onENABLE_RESPONSE_FORMATdecide whether to useresponse_format
            request_params = {
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": current_temperature,
                "max_tokens": 4000
            }
            
            # Only enableresponse_formatThis parameter is added only when
            if ENABLE_RESPONSE_FORMAT:
                request_params["response_format"] = {"type": "json_object"}
            
            response = await client.chat.completions.create(
                **get_ai_request_params(**request_params)
            )

            # Compatible with differentAPIresponse format, checkresponseWhether it is a string
            if hasattr(response, 'choices'):
                ai_response_content = response.choices[0].message.content
            else:
                # ifresponseis a string, use it directly
                ai_response_content = response

            if AI_DEBUG_MODE:
                safe_print(f"\n--- [AI DEBUG] No.{attempt + 1}attempts ---")
                safe_print("--- RAW AI RESPONSE ---")
                safe_print(ai_response_content)
                safe_print("---------------------\n")

            # Try to parse directlyJSON
            try:
                parsed_response = json.loads(ai_response_content)

                # Verify response format
                if validate_ai_response_format(parsed_response):
                    safe_print(f"   [AIanalyze] No.{attempt + 1}Successful attempts, response format verification passed")
                    return parsed_response
                else:
                    safe_print(f"   [AIanalyze] No.{attempt + 1}Format validation failed in attempts")
                    if attempt < max_retries - 1:
                        safe_print(f"   [AIanalyze] Prepare for Chapter{attempt + 2}retries...")
                        continue
                    else:
                        safe_print("   [AIanalyze] All retries are completed and the last result is used")
                        return parsed_response

            except json.JSONDecodeError:
                safe_print(f"   [AIanalyze] No.{attempt + 1}attemptsJSONParsing failed, try to clean response content...")

                # Clean up possibleMarkdowncode block tag
                cleaned_content = ai_response_content.strip()
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.startswith('```'):
                    cleaned_content = cleaned_content[3:]
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()

                # looking forJSONobject bounds
                json_start_index = cleaned_content.find('{')
                json_end_index = cleaned_content.rfind('}')

                if json_start_index != -1 and json_end_index != -1 and json_end_index > json_start_index:
                    json_str = cleaned_content[json_start_index:json_end_index + 1]
                    try:
                        parsed_response = json.loads(json_str)
                        if validate_ai_response_format(parsed_response):
                            safe_print(f"   [AIanalyze] No.{attempt + 1}Cleanup succeeded after attempts")
                            return parsed_response
                        else:
                            if attempt < max_retries - 1:
                                safe_print(f"   [AIanalyze] Prepare for Chapter{attempt + 2}retries...")
                                continue
                            else:
                                safe_print("   [AIanalyze] All retries complete, use cleaned results")
                                return parsed_response
                    except json.JSONDecodeError as e:
                        safe_print(f"   [AIanalyze] No.{attempt + 1}After attempts to cleanJSONParsing still fails: {e}")
                        if attempt < max_retries - 1:
                            safe_print(f"   [AIanalyze] Prepare for Chapter{attempt + 2}retries...")
                            continue
                        else:
                            raise e
                else:
                    safe_print(f"   [AIanalyze] No.{attempt + 1}attempts failed to find a validJSONobject")
                    if attempt < max_retries - 1:
                        safe_print(f"   [AIanalyze] Prepare for Chapter{attempt + 2}retries...")
                        continue
                    else:
                        raise json.JSONDecodeError("No valid JSON object found", ai_response_content, 0)

        except Exception as e:
            safe_print(f"   [AIanalyze] No.{attempt + 1}attemptsAICall failed: {e}")
            if attempt < max_retries - 1:
                safe_print(f"   [AIanalyze] Prepare for Chapter{attempt + 2}retries...")
                continue
            else:
                raise e
