import asyncio
import sys
import os
import argparse
import json
import signal
import contextlib

from src.config import STATE_FILE
from src.scraper import scrape_xianyu


async def main():
    parser = argparse.ArgumentParser(
        description="Xianyu product monitoring script supports multi-task configuration and real-timeAIanalyze。",
        epilog="""
Usage example:
  # run config.json All tasks defined in
  python spider_v2.py

  # Only run names named "Sony A7M4" task (Usually called by the scheduler)
  python spider_v2.py --task-name "Sony A7M4"

  # debug mode: Run all tasks, but each task only processes the first3newly discovered items
  python spider_v2.py --debug-limit 3
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--debug-limit", type=int, default=0, help="Debug mode: Each task only processes the first N new items（0 means unlimited）")
    parser.add_argument("--config", type=str, default="config.json", help="Specify the task configuration file path (default is config.json）")
    parser.add_argument("--task-name", type=str, help="Run only a single task with the specified name (Used for scheduled task scheduling)")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        sys.exit(f"mistake: Configuration file '{args.config}' does not exist。")

    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            tasks_config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        sys.exit(f"mistake: Read or parse configuration files '{args.config}' fail: {e}")

    def has_bound_account(tasks: list) -> bool:
        for task in tasks:
            account = task.get("account_state_file")
            if isinstance(account, str) and account.strip():
                return True
        return False

    def has_any_state_file() -> bool:
        state_dir = os.getenv("ACCOUNT_STATE_DIR", "state").strip().strip('"').strip("'")
        if os.path.isdir(state_dir):
            for name in os.listdir(state_dir):
                if name.endswith(".json"):
                    return True
        return False

    if not os.path.exists(STATE_FILE) and not has_bound_account(tasks_config) and not has_any_state_file():
        sys.exit(
            f"mistake: Login status file not found. please state/ Add account or configuration in account_state_file。"
        )

    # read allpromptFile content
    for task in tasks_config:
        if task.get("enabled", False) and task.get("ai_prompt_base_file") and task.get("ai_prompt_criteria_file"):
            try:
                with open(task["ai_prompt_base_file"], 'r', encoding='utf-8') as f_base:
                    base_prompt = f_base.read()
                with open(task["ai_prompt_criteria_file"], 'r', encoding='utf-8') as f_criteria:
                    criteria_text = f_criteria.read()
                
                # dynamically combined into the finalPrompt
                task['ai_prompt_text'] = base_prompt.replace("{{CRITERIA_SECTION}}", criteria_text)
                
                # Verify the generatedpromptIs it valid?
                if len(task['ai_prompt_text']) < 100:
                    print(f"warn: Task '{task['task_name']}' generatedprompttoo short ({len(task['ai_prompt_text'])} character)，There may be a problem。")
                elif "{{CRITERIA_SECTION}}" in task['ai_prompt_text']:
                    print(f"warn: Task '{task['task_name']}' ofpromptstill contains placeholders, replacement may fail。")
                else:
                    print(f"✅ Task '{task['task_name']}' ofpromptGenerated successfully, length: {len(task['ai_prompt_text'])} character")

            except FileNotFoundError as e:
                print(f"warn: Task '{task['task_name']}' ofpromptFile missing: {e}，of this taskAIAnalysis will be skipped。")
                task['ai_prompt_text'] = ""
            except Exception as e:
                print(f"mistake: Task '{task['task_name']}' deal withpromptException occurred while file: {e}，of this taskAIAnalysis will be skipped。")
                task['ai_prompt_text'] = ""
        elif task.get("enabled", False) and task.get("ai_prompt_file"):
            try:
                with open(task["ai_prompt_file"], 'r', encoding='utf-8') as f:
                    task['ai_prompt_text'] = f.read()
                print(f"✅ Task '{task['task_name']}' ofpromptFile read successfully, length: {len(task['ai_prompt_text'])} character")
            except FileNotFoundError:
                print(f"warn: Task '{task['task_name']}' ofpromptdocument '{task['ai_prompt_file']}' Not found, the task'sAIAnalysis will be skipped。")
                task['ai_prompt_text'] = ""
            except Exception as e:
                print(f"mistake: Task '{task['task_name']}' readpromptException occurred while file: {e}，of this taskAIAnalysis will be skipped。")
                task['ai_prompt_text'] = ""

    print("\n--- Start monitoring tasks ---")
    if args.debug_limit > 0:
        print(f"** Debug mode is activated, each task processes up to {args.debug_limit} new items **")
    
    if args.task_name:
        print(f"** Scheduled task mode: only execute tasks '{args.task_name}' **")

    print("--------------------")

    active_task_configs = []
    if args.task_name:
        # If a task name is specified, only that task is found
        task_found = next((task for task in tasks_config if task.get('task_name') == args.task_name), None)
        if task_found:
            if task_found.get("enabled", False):
                active_task_configs.append(task_found)
            else:
                print(f"Task '{args.task_name}' Disabled, skipping execution。")
        else:
            print(f"Error: The file named '{args.task_name}' task。")
            return
    else:
        # Otherwise, load all enabled tasks as originally planned
        active_task_configs = [task for task in tasks_config if task.get("enabled", False)]

    if not active_task_configs:
        print("There are no tasks to be performed and the program exits.。")
        return

    # Create an asynchronous execution coroutine for each enabled task
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    tasks = []
    for task_conf in active_task_configs:
        print(f"-> Task '{task_conf['task_name']}' Joined the execution queue。")
        tasks.append(asyncio.create_task(scrape_xianyu(task_config=task_conf, debug_limit=args.debug_limit)))

    async def _shutdown_watcher():
        await stop_event.wait()
        print("\nReceived termination signal and exiting gracefully，Cancel all crawler tasks...")
        for t in tasks:
            if not t.done():
                t.cancel()

    shutdown_task = asyncio.create_task(_shutdown_watcher())

    try:
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        shutdown_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await shutdown_task

    print("\n--- All tasks completed ---")
    for i, result in enumerate(results):
        task_name = active_task_configs[i]['task_name']
        if isinstance(result, Exception):
            print(f"Task '{task_name}' Terminate due to exception: {result}")
        else:
            print(f"Task '{task_name}' Ended normally, this run processed a total of {result} new items。")

if __name__ == "__main__":
    asyncio.run(main())
