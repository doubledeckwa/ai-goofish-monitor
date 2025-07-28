import asyncio
import base64
import json
import os
import re

import requests

from src.config import (
    AI_DEBUG_MODE,
    IMAGE_DOWNLOAD_HEADERS,
    IMAGE_SAVE_DIR,
    MODEL_NAME,
    NTFY_TOPIC_URL,
    PCURL_TO_MOBILE,
    WX_BOT_URL,
    client,
)
from src.utils import convert_goofish_link, retry_on_failure


@retry_on_failure(retries=2, delay=3)
async def _download_single_image(url, save_path):
    """一个带重试的内部函数，用于异步下载单个图片。"""
    loop = asyncio.get_running_loop()
    # 使用 run_in_executor 运行同步的 requests 代码，避免阻塞事件循环
    response = await loop.run_in_executor(
        None,
        lambda: requests.get(url, headers=IMAGE_DOWNLOAD_HEADERS, timeout=20, stream=True)
    )
    response.raise_for_status()
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return save_path


async def download_all_images(product_id, image_urls):
    """异步下载一个商品的所有图片。如果图片已存在则跳过。"""
    if not image_urls:
        return []

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

            save_path = os.path.join(IMAGE_SAVE_DIR, file_name)

            if os.path.exists(save_path):
                print(f"   [图片] 图片 {i + 1}/{total_images} 已存在，跳过下载: {os.path.basename(save_path)}")
                saved_paths.append(save_path)
                continue

            print(f"   [图片] 正在下载图片 {i + 1}/{total_images}: {url}")
            if await _download_single_image(url, save_path):
                print(f"   [图片] 图片 {i + 1}/{total_images} 已成功下载到: {os.path.basename(save_path)}")
                saved_paths.append(save_path)
        except Exception as e:
            print(f"   [图片] 处理图片 {url} 时发生错误，已跳过此图: {e}")

    return saved_paths


def encode_image_to_base64(image_path):
    """将本地图片文件编码为 Base64 字符串。"""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"编码图片时出错: {e}")
        return None


@retry_on_failure(retries=3, delay=5)
async def send_ntfy_notification(product_data, reason):
    """当发现推荐商品时，异步发送一个高优先级的 ntfy.sh 通知。"""
    if not NTFY_TOPIC_URL and not WX_BOT_URL:
        print("警告：未在 .env 文件中配置 NTFY_TOPIC_URL 或 WX_BOT_URL，跳过通知。")
        return

    title = product_data.get('商品标题', 'N/A')
    price = product_data.get('当前售价', 'N/A')
    link = product_data.get('商品链接', '#')
    if PCURL_TO_MOBILE:
        mobile_link = convert_goofish_link(link)
        message = f"价格: {price}\n原因: {reason}\n手机端链接: {mobile_link}\n电脑端链接: {link}"
    else:
        message = f"价格: {price}\n原因: {reason}\n链接: {link}"

    notification_title = f"🚨 新推荐! {title[:30]}..."

    # --- 发送 ntfy 通知 ---
    if NTFY_TOPIC_URL:
        try:
            print(f"   -> 正在发送 ntfy 通知到: {NTFY_TOPIC_URL}")
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
            print("   -> ntfy 通知发送成功。")
        except Exception as e:
            print(f"   -> 发送 ntfy 通知失败: {e}")

    # --- 发送企业微信机器人通知 ---
    if WX_BOT_URL:
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"{notification_title}\n{message}"
            }
        }

        try:
            print(f"   -> 正在发送企业微信通知到: {WX_BOT_URL}")
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
            print(f"   -> 企业微信通知发送成功。响应: {result}")
        except requests.exceptions.RequestException as e:
            print(f"   -> 发送企业微信通知失败: {e}")
        except Exception as e:
            print(f"   -> 发送企业微信通知时发生未知错误: {e}")


@retry_on_failure(retries=5, delay=10)
async def get_ai_analysis(product_data, image_paths=None, prompt_text=""):
    """将完整的商品JSON数据和所有图片发送给 AI 进行分析（异步）。"""
    if not client:
        print("   [AI分析] 错误：AI客户端未初始化，跳过分析。")
        return None

    item_info = product_data.get('商品信息', {})
    product_id = item_info.get('商品ID', 'N/A')

    print(f"\n   [AI分析] 开始分析商品 #{product_id} (含 {len(image_paths or [])} 张图片)...")
    print(f"   [AI分析] 标题: {item_info.get('商品标题', '无')}")

    if not prompt_text:
        print("   [AI分析] 错误：未提供AI分析所需的prompt文本。")
        return None

    product_details_json = json.dumps(product_data, ensure_ascii=False, indent=2)
    system_prompt = prompt_text

    if AI_DEBUG_MODE:
        print("\n--- [AI DEBUG] ---")
        print("--- PROMPT TEXT (first 500 chars) ---")
        print(prompt_text[:500] + "...")
        print("--- PRODUCT DATA (JSON) ---")
        print(product_details_json)
        print("-------------------\n")

    combined_text_prompt = f"""{system_prompt}

请基于你的专业知识和我的要求，分析以下完整的商品JSON数据：

```json
    {product_details_json}
"""
    user_content_list = [{"type": "text", "text": combined_text_prompt}]

    if image_paths:
        for path in image_paths:
            base64_image = encode_image_to_base64(path)
            if base64_image:
                user_content_list.append(
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

    messages = [{"role": "user", "content": user_content_list}]

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"}
    )

    ai_response_content = response.choices[0].message.content

    if AI_DEBUG_MODE:
        print("\n--- [AI DEBUG] ---")
        print("--- RAW AI RESPONSE ---")
        print(ai_response_content)
        print("---------------------\n")

    try:
        # --- 新增代码：从Markdown代码块中提取JSON ---
        # 寻找第一个 "{" 和最后一个 "}" 来捕获完整的JSON对象
        json_start_index = ai_response_content.find('{')
        json_end_index = ai_response_content.rfind('}')
        
        if json_start_index != -1 and json_end_index != -1:
            clean_json_str = ai_response_content[json_start_index : json_end_index + 1]
            return json.loads(clean_json_str)
        else:
            # 如果找不到 "{" 或 "}"，说明响应格式异常，按原样尝试解析并准备捕获错误
            print("---!!! AI RESPONSE WARNING: Could not find JSON object markers '{' and '}' in the response. !!!---")
            return json.loads(ai_response_content) # 这行很可能会再次触发错误，但保留逻辑完整性
        # --- 修改结束 ---
        
    except json.JSONDecodeError as e:
        print("---!!! AI RESPONSE PARSING FAILED (JSONDecodeError) !!!---")
        print(f"原始返回值 (Raw response from AI):\n---\n{ai_response_content}\n---")
        raise e
