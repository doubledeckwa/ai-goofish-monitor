"""
Task management routing
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import os
import aiofiles
from src.api.dependencies import get_task_service, get_process_service
from src.services.task_service import TaskService
from src.services.process_service import ProcessService
from src.domain.models.task import Task, TaskCreate, TaskUpdate, TaskGenerateRequest
from src.api.routes.websocket import broadcast_message
from src.prompt_utils import generate_criteria
from src.utils import resolve_task_log_path


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[dict])
async def get_tasks(
    service: TaskService = Depends(get_task_service),
):
    """Get all tasks"""
    tasks = await service.get_all_tasks()
    return [task.dict() for task in tasks]


@router.get("/{task_id}", response_model=dict)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
):
    """Get a single task"""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.dict()


@router.post("/", response_model=dict)
async def create_task(
    task_create: TaskCreate,
    service: TaskService = Depends(get_task_service),
):
    """Create new task"""
    task = await service.create_task(task_create)
    return {"message": "Task created successfully", "task": task.dict()}


@router.post("/generate", response_model=dict)
async def generate_task(
    req: TaskGenerateRequest,
    service: TaskService = Depends(get_task_service),
):
    """use AI Generate analysis criteria and create new tasks"""
    print(f"receive AI Task generation request: {req.task_name}")

    try:
        # 1. Generate unique file names
        safe_keyword = "".join(
            c for c in req.keyword.lower().replace(' ', '_')
            if c.isalnum() or c in "_-"
        ).rstrip()
        output_filename = f"prompts/{safe_keyword}_criteria.txt"
        print(f"Generated file path: {output_filename}")

        # 2. call AI Generate analysis criteria
        print("Start callingAIGenerate analysis criteria...")
        generated_criteria = await generate_criteria(
            user_description=req.description,
            reference_file_path="prompts/macbook_criteria.txt"
        )

        print(f"AIGenerated analysis standard length: {len(generated_criteria) if generated_criteria else 0}")
        if not generated_criteria or len(generated_criteria.strip()) == 0:
            print("AIThe returned content is empty or contains only whitespace characters")
            raise HTTPException(status_code=500, detail="AIFailed to generate analysis criteria, the returned content is empty。")

        # 3. Save the generated text to a new file
        print(f"Start saving analysis standards to file: {output_filename}")
        try:
            os.makedirs("prompts", exist_ok=True)
            async with aiofiles.open(output_filename, 'w', encoding='utf-8') as f:
                await f.write(generated_criteria)
            print(f"New analysis standard has been saved to: {output_filename}")
        except IOError as e:
            print(f"Failed to save analysis standard file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save analysis standard file: {e}")

        # 4. Create new task object
        print("Start creating a new task object...")
        task_create = TaskCreate(
            task_name=req.task_name,
            enabled=True,
            keyword=req.keyword,
            description=req.description,
            max_pages=req.max_pages,
            personal_only=req.personal_only,
            min_price=req.min_price,
            max_price=req.max_price,
            cron=req.cron,
            ai_prompt_base_file="prompts/base_prompt.txt",
            ai_prompt_criteria_file=output_filename,
            account_state_file=req.account_state_file,
            free_shipping=req.free_shipping,
            new_publish_option=req.new_publish_option,
            region=req.region,
        )

        # 5. use TaskService Create tasks
        print("start passing TaskService Create tasks...")
        task = await service.create_task(task_create)

        print(f"AITask created successfully: {req.task_name}")
        return {"message": "AI Task created successfully。", "task": task.dict()}

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"AITask generationAPIAn unknown error occurred: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())

        # If the file was created but the task creation failed, clean the file
        if 'output_filename' in locals() and os.path.exists(output_filename):
            try:
                os.remove(output_filename)
                print(f"Failed file deletion: {output_filename}")
            except Exception as cleanup_error:
                print(f"Error while cleaning failed files: {cleanup_error}")

        raise HTTPException(status_code=500, detail=error_msg)


@router.patch("/{task_id}", response_model=dict)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):
    """update task"""
    try:
        existing_task = await service.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Check if regeneration is required criteria document
        if task_update.description is not None and task_update.description != existing_task.description:
            print(f"Task detected {task_id} of description Update, start regeneration criteria document...")

            try:
                # Generate new file name
                safe_keyword = "".join(
                    c for c in existing_task.keyword.lower().replace(' ', '_')
                    if c.isalnum() or c in "_-"
                ).rstrip()
                output_filename = f"prompts/{safe_keyword}_criteria.txt"
                print(f"Target file path: {output_filename}")

                # call AI Generate new analysis standards
                print("Start calling AI Generate new analysis standards...")
                generated_criteria = await generate_criteria(
                    user_description=task_update.description,
                    reference_file_path="prompts/macbook_criteria.txt"
                )

                if not generated_criteria or len(generated_criteria.strip()) == 0:
                    print("AI The returned content is empty")
                    raise HTTPException(status_code=500, detail="AI Failed to generate analysis criteria, the returned content is empty。")

                # Save generated text to file
                print(f"Save new analysis standards to: {output_filename}")
                os.makedirs("prompts", exist_ok=True)
                async with aiofiles.open(output_filename, 'w', encoding='utf-8') as f:
                    await f.write(generated_criteria)
                print(f"New analysis standard saved")

                # renew task_update in ai_prompt_criteria_file Field
                task_update.ai_prompt_criteria_file = output_filename
                print(f"updated ai_prompt_criteria_file The fields are: {output_filename}")

            except HTTPException:
                raise
            except Exception as e:
                error_msg = f"Regenerate criteria Error while file: {str(e)}"
                print(error_msg)
                import traceback
                print(traceback.format_exc())
                raise HTTPException(status_code=500, detail=error_msg)

        # Execute task update
        task = await service.update_task(task_id, task_update)
        return {"message": "Task updated successfully", "task": task.dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{task_id}", response_model=dict)
async def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
):
    """Delete task"""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        keyword = (task.keyword or "").strip()
        if keyword:
            filename = f"{keyword.replace(' ', '_')}_full_data.jsonl"
            file_path = os.path.join("jsonl", filename)
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error deleting task results file: {e}")

    try:
        log_file_path = resolve_task_log_path(task_id, task.task_name)
        if os.path.exists(log_file_path):
            os.remove(log_file_path)
    except Exception as e:
        print(f"Error deleting task log file: {e}")

    return {"message": "Task deleted successfully"}


@router.post("/start/{task_id}", response_model=dict)
async def start_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    process_service: ProcessService = Depends(get_process_service),
):
    """Start a single task"""
    # Get task information
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if the task is enabled
    if not task.enabled:
        raise HTTPException(status_code=400, detail="The task is disabled and cannot be started")

    # Check if the task is already running
    if task.is_running:
        raise HTTPException(status_code=400, detail="Task is already running")

    # Start task process
    success = await process_service.start_task(task_id, task.task_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start task")

    # Update task status
    await task_service.update_task_status(task_id, True)

    # Broadcast task status changes
    await broadcast_message("task_status_changed", {"id": task_id, "is_running": True})

    return {"message": f"Task '{task.task_name}' Started"}


@router.post("/stop/{task_id}", response_model=dict)
async def stop_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    process_service: ProcessService = Depends(get_process_service),
):
    """Stop a single task"""
    # Get task information
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Stop task process
    await process_service.stop_task(task_id)

    # Update task status
    await task_service.update_task_status(task_id, False)

    # Broadcast task status changes
    await broadcast_message("task_status_changed", {"id": task_id, "is_running": False})

    return {"message": f"TaskID {task_id} Stop signal sent"}
