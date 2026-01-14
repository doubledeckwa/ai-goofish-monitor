"""
Dispatch service
Responsible for managing the scheduling of scheduled tasks
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import List
from src.domain.models.task import Task
from src.services.process_service import ProcessService


class SchedulerService:
    """Dispatch service"""

    def __init__(self, process_service: ProcessService):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.process_service = process_service

    def start(self):
        """Start scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("Scheduler started")

    def stop(self):
        """Stop scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Scheduler has stopped")

    async def reload_jobs(self, tasks: List[Task]):
        """Reload all scheduled tasks"""
        print("Reloading scheduled tasks...")
        self.scheduler.remove_all_jobs()

        for task in tasks:
            if task.enabled and task.cron:
                try:
                    trigger = CronTrigger.from_crontab(task.cron)
                    self.scheduler.add_job(
                        self._run_task,
                        trigger=trigger,
                        args=[task.id, task.task_name],
                        id=f"task_{task.id}",
                        name=f"Scheduled: {task.task_name}",
                        replace_existing=True
                    )
                    print(f"  -> Already tasked '{task.task_name}' Add timing rules: '{task.cron}'")
                except ValueError as e:
                    print(f"  -> [warn] Task '{task.task_name}' of Cron Invalid expression: {e}")

        print("Scheduled task loading completed")

    async def _run_task(self, task_id: int, task_name: str):
        """Execute scheduled tasks"""
        print(f"Scheduled task trigger: working on task '{task_name}' Start the crawler...")
        await self.process_service.start_task(task_id, task_name)
