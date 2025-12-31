"""
任务管理路由
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from src.api.dependencies import get_current_user, get_task_service, get_process_service
from src.services.task_service import TaskService
from src.services.process_service import ProcessService
from src.domain.models.task import Task, TaskCreate, TaskUpdate
from src.api.routes.websocket import broadcast_message


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[dict])
async def get_tasks(
    service: TaskService = Depends(get_task_service),
    username: str = Depends(get_current_user)
):
    """获取所有任务"""
    tasks = await service.get_all_tasks()
    return [task.dict() for task in tasks]


@router.get("/{task_id}", response_model=dict)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    username: str = Depends(get_current_user)
):
    """获取单个任务"""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    return task.dict()


@router.post("/", response_model=dict)
async def create_task(
    task_create: TaskCreate,
    service: TaskService = Depends(get_task_service),
    username: str = Depends(get_current_user)
):
    """创建新任务"""
    task = await service.create_task(task_create)
    return {"message": "任务创建成功", "task": task.dict()}


@router.patch("/{task_id}", response_model=dict)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    username: str = Depends(get_current_user)
):
    """更新任务"""
    try:
        task = await service.update_task(task_id, task_update)
        return {"message": "任务更新成功", "task": task.dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{task_id}", response_model=dict)
async def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    username: str = Depends(get_current_user)
):
    """删除任务"""
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务未找到")
    return {"message": "任务删除成功"}


@router.post("/start/{task_id}", response_model=dict)
async def start_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    process_service: ProcessService = Depends(get_process_service),
    username: str = Depends(get_current_user)
):
    """启动单个任务"""
    # 获取任务信息
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")

    # 检查任务是否已启用
    if not task.enabled:
        raise HTTPException(status_code=400, detail="任务已被禁用，无法启动")

    # 检查任务是否已在运行
    if task.is_running:
        raise HTTPException(status_code=400, detail="任务已在运行中")

    # 启动任务进程
    success = await process_service.start_task(task_id, task.task_name)
    if not success:
        raise HTTPException(status_code=500, detail="启动任务失败")

    # 更新任务状态
    await task_service.update_task_status(task_id, True)

    # 广播任务状态变更
    await broadcast_message("task_status_changed", {"id": task_id, "is_running": True})

    return {"message": f"任务 '{task.task_name}' 已启动"}


@router.post("/stop/{task_id}", response_model=dict)
async def stop_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    process_service: ProcessService = Depends(get_process_service),
    username: str = Depends(get_current_user)
):
    """停止单个任务"""
    # 获取任务信息
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")

    # 停止任务进程
    await process_service.stop_task(task_id)

    # 更新任务状态
    await task_service.update_task_status(task_id, False)

    # 广播任务状态变更
    await broadcast_message("task_status_changed", {"id": task_id, "is_running": False})

    return {"message": f"任务ID {task_id} 已发送停止信号"}
