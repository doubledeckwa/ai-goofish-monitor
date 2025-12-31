"""
进程管理服务
负责管理爬虫进程的启动和停止
"""
import asyncio
import sys
import os
import signal
from typing import Dict


class ProcessService:
    """进程管理服务"""

    def __init__(self):
        self.processes: Dict[int, asyncio.subprocess.Process] = {}

    def is_running(self, task_id: int) -> bool:
        """检查任务是否正在运行"""
        process = self.processes.get(task_id)
        return process is not None and process.returncode is None

    async def start_task(self, task_id: int, task_name: str) -> bool:
        """启动任务进程"""
        if self.is_running(task_id):
            print(f"任务 '{task_name}' (ID: {task_id}) 已在运行中")
            return False

        try:
            os.makedirs("logs", exist_ok=True)
            log_file_path = os.path.join("logs", "scraper.log")
            log_file_handle = open(log_file_path, 'a', encoding='utf-8')

            preexec_fn = os.setsid if sys.platform != "win32" else None
            child_env = os.environ.copy()
            child_env["PYTHONIOENCODING"] = "utf-8"
            child_env["PYTHONUTF8"] = "1"

            process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", "spider_v2.py", "--task-name", task_name,
                stdout=log_file_handle,
                stderr=log_file_handle,
                preexec_fn=preexec_fn,
                env=child_env
            )

            self.processes[task_id] = process
            print(f"启动任务 '{task_name}' (PID: {process.pid})")
            return True

        except Exception as e:
            print(f"启动任务 '{task_name}' 失败: {e}")
            return False

    async def stop_task(self, task_id: int) -> bool:
        """停止任务进程"""
        process = self.processes.get(task_id)
        if not process or process.returncode is not None:
            print(f"任务 ID {task_id} 没有正在运行的进程")
            if task_id in self.processes:
                del self.processes[task_id]
            return False

        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()

            await process.wait()
            print(f"任务进程 {process.pid} (ID: {task_id}) 已终止")
            del self.processes[task_id]
            return True

        except ProcessLookupError:
            print(f"进程 (ID: {task_id}) 已不存在")
            if task_id in self.processes:
                del self.processes[task_id]
            return False
        except Exception as e:
            print(f"停止任务进程 (ID: {task_id}) 时出错: {e}")
            return False

    async def stop_all(self):
        """停止所有任务进程"""
        task_ids = list(self.processes.keys())
        for task_id in task_ids:
            await self.stop_task(task_id)
