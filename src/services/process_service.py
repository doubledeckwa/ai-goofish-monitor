"""
Process management service
Responsible for managing the starting and stopping of the crawler process
"""
import asyncio
import sys
import os
import signal
from datetime import datetime
from typing import Dict
from src.utils import build_task_log_path


class ProcessService:
    """Process management service"""

    def __init__(self):
        self.processes: Dict[int, asyncio.subprocess.Process] = {}
        self.log_paths: Dict[int, str] = {}

    def is_running(self, task_id: int) -> bool:
        """Check if the task is running"""
        process = self.processes.get(task_id)
        return process is not None and process.returncode is None

    async def start_task(self, task_id: int, task_name: str) -> bool:
        """Start task process"""
        if self.is_running(task_id):
            print(f"Task '{task_name}' (ID: {task_id}) Already running")
            return False

        try:
            os.makedirs("logs", exist_ok=True)
            log_file_path = build_task_log_path(task_id, task_name)
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
            self.log_paths[task_id] = log_file_path
            print(f"Start task '{task_name}' (PID: {process.pid})")
            return True

        except Exception as e:
            if task_id in self.log_paths:
                del self.log_paths[task_id]
            print(f"Start task '{task_name}' fail: {e}")
            return False

    def _append_stop_marker(self, log_path: str | None) -> None:
        if not log_path:
            return
        try:
            ts = datetime.now().strftime(' %Y-%m-%d %H:%M:%S')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{ts}] !!! Task has been terminated !!!\n")
        except Exception as e:
            print(f"Failed to write task termination flag: {e}")

    async def stop_task(self, task_id: int) -> bool:
        """Stop task process"""
        process = self.processes.pop(task_id, None)
        log_path = self.log_paths.pop(task_id, None)
        if not process:
            print(f"Task ID {task_id} There are no running processes")
            return False
        if process.returncode is not None:
            print(f"task process {process.pid} (ID: {task_id}) Exited, skip stopping")
            return False

        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()

            try:
                await asyncio.wait_for(process.wait(), timeout=20)
            except asyncio.TimeoutError:
                print(f"task process {process.pid} (ID: {task_id}) Not here 20 Exit within seconds, prepare for forced termination...")
                if sys.platform != "win32":
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                await process.wait()

            self._append_stop_marker(log_path)
            print(f"task process {process.pid} (ID: {task_id}) terminated")
            return True

        except ProcessLookupError:
            print(f"process (ID: {task_id}) no longer exists")
            return False
        except Exception as e:
            print(f"Stop task process (ID: {task_id}) error: {e}")
            return False

    async def stop_all(self):
        """Stop all task processes"""
        task_ids = list(self.processes.keys())
        for task_id in task_ids:
            await self.stop_task(task_id)
