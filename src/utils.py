import asyncio
import json
import math
import os
import random
import re
import glob
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from openai import APIStatusError
from requests.exceptions import HTTPError


def retry_on_failure(retries=3, delay=5):
    """
    A generic asynchronous retry decorator that adds support forHTTPDetailed logging of errors。
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except (APIStatusError, HTTPError) as e:
                    print(f"function {func.__name__} No. {i + 1}/{retries} failed attempts, occurredHTTPmistake。")
                    if hasattr(e, 'status_code'):
                        print(f"  - status code (Status Code): {e.status_code}")
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        response_text = e.response.text
                        print(
                            f"  - return value (Response): {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
                except json.JSONDecodeError as e:
                    print(f"function {func.__name__} No. {i + 1}/{retries} failed attempts: JSONParse error - {e}")
                except Exception as e:
                    print(f"function {func.__name__} No. {i + 1}/{retries} failed attempts: {type(e).__name__} - {e}")

                if i < retries - 1:
                    print(f"will be in {delay} Try again in seconds...")
                    await asyncio.sleep(delay)

            print(f"function {func.__name__} exist {retries} Total failure after attempts。")
            return None
        return wrapper
    return decorator


async def safe_get(data, *keys, default="None yet"):
    """Safely get nested dictionary values"""
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError, IndexError):
            return default
    return data


async def random_sleep(min_seconds: float, max_seconds: float):
    """Asynchronously waits for a random time within a specified range。"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"   [Delay] wait {delay:.2f} Second... (scope: {min_seconds}-{max_seconds}s)")
    await asyncio.sleep(delay)


def log_time(message: str, prefix: str = "") -> None:
    """Add before the log YY-MM-DD HH:MM:SS Simple printing of timestamp。"""
    try:
        ts = datetime.now().strftime(' %Y-%m-%d %H:%M:%S')
    except Exception:
        ts = "--:--:--"
    print(f"[{ts}] {prefix}{message}")


def sanitize_filename(value: str) -> str:
    """生成安全的文件名片段。"""
    if not value:
        return "task"
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "task"


def build_task_log_path(task_id: int, task_name: str) -> str:
    """Generate task log path (including task name）。"""
    safe_name = sanitize_filename(task_name)
    filename = f"{safe_name}_{task_id}.log"
    return os.path.join("logs", filename)


def resolve_task_log_path(task_id: int, task_name: str) -> str:
    """Priority is given to using the task name to generate the log path. If it does not exist, it will fall back to pressing ID match。"""
    primary_path = build_task_log_path(task_id, task_name)
    if os.path.exists(primary_path):
        return primary_path
    pattern = os.path.join("logs", f"*_{task_id}.log")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    return primary_path


def convert_goofish_link(url: str) -> str:
    """
    WillGoofishProduct links are converted to include only productsIDmobile phone format。
    """
    match_first_link = re.search(r'item\?id=(\d+)', url)
    if match_first_link:
        item_id = match_first_link.group(1)
        bfp_json = f'{{"id":{item_id}}}'
        return f"https://pages.goofish.com/sharexy?loadingVisible=false&bft=item&bfs=idlepc.item&spm=a21ybx.item.0.0&bfp={quote(bfp_json)}"
    return url


def get_link_unique_key(link: str) -> str:
    """Intercept the first link"&"The previous content is used as the basis for unique identification.。"""
    return link.split('&', 1)[0]


async def save_to_jsonl(data_record: dict, keyword: str):
    """Append a complete record containing product and seller information to .jsonl document。"""
    output_dir = "jsonl"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{keyword.replace(' ', '_')}_full_data.jsonl")
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data_record, ensure_ascii=False) + "\n")
        return True
    except IOError as e:
        print(f"write file {filename} Error: {e}")
        return False


def format_registration_days(total_days: int) -> str:
    """
    Format the total number of days as“XYearYmonth" string。
    """
    if not isinstance(total_days, int) or total_days <= 0:
        return 'unknown'

    DAYS_IN_YEAR = 365.25
    DAYS_IN_MONTH = DAYS_IN_YEAR / 12

    years = math.floor(total_days / DAYS_IN_YEAR)
    remaining_days = total_days - (years * DAYS_IN_YEAR)
    months = round(remaining_days / DAYS_IN_MONTH)

    if months == 12:
        years += 1
        months = 0

    if years > 0 and months > 0:
        return f"Come to Xianyu{years}Year{months}months"
    elif years > 0 and months == 0:
        return f"Come to Xianyu{years}whole year"
    elif years == 0 and months > 0:
        return f"Come to Xianyu{months}months"
    else:
        return "Been in Xianyu for less than a month"
