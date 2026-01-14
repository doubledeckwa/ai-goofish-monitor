"""
The main application entrance of the new architecture
Integrate all routes and services
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.routes import tasks, logs, settings, prompts, results, login_state, websocket, accounts
from src.api.dependencies import set_process_service
from src.services.task_service import TaskService
from src.services.process_service import ProcessService
from src.services.scheduler_service import SchedulerService
from src.infrastructure.persistence.json_task_repository import JsonTaskRepository


# Global service instance
process_service = ProcessService()
scheduler_service = SchedulerService(process_service)

# Set global ProcessService Instance used for dependency injection
set_process_service(process_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application life cycle management"""
    # On startup
    print("Starting application...")

    # Reset all task status to stopped
    task_repo = JsonTaskRepository()
    task_service = TaskService(task_repo)
    tasks_list = await task_service.get_all_tasks()

    for task in tasks_list:
        if task.is_running:
            await task_service.update_task_status(task.id, False)

    # Load scheduled tasks
    await scheduler_service.reload_jobs(tasks_list)
    scheduler_service.start()

    print("Application startup completed")

    yield

    # when closed
    print("Closing application...")
    scheduler_service.stop()
    await process_service.stop_all()
    print("App is closed")


# create FastAPI application
app = FastAPI(
    title="Xianyu intelligent monitoring robot",
    description="based onAIXianyu product monitoring system",
    version="2.0.0",
    lifespan=lifespan
)

# Register route
app.include_router(tasks.router)
app.include_router(logs.router)
app.include_router(settings.router)
app.include_router(prompts.router)
app.include_router(results.router)
app.include_router(login_state.router)
app.include_router(websocket.router)
app.include_router(accounts.router)

# Mount static files
# Old static files directory (for screenshots etc.）
app.mount("/static", StaticFiles(directory="static"), name="static")

# mount Vue 3 Front-end build product
# NOTE: Required at all API Mount after routing to avoid overwriting API routing
import os
if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")


# health check endpoint
@app.get("/health")
async def health_check():
    """Health check (no certification required）"""
    return {"status": "healthy", "message": "Service is running normally"}


# Authentication status check endpoint
from fastapi import Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.infrastructure.config.settings import settings

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/status")
async def auth_status(payload: LoginRequest):
    """Check certification status"""
    if payload.username == settings.web_username and payload.password == settings.web_password:
        return {"authenticated": True, "username": payload.username}
    raise HTTPException(status_code=401, detail="Authentication failed")


# Home route - Serve Vue 3 SPA
from fastapi.responses import JSONResponse

@app.get("/")
async def read_root(request: Request):
    """supply Vue 3 SPA 's main page"""
    if os.path.exists("dist/index.html"):
        return FileResponse("dist/index.html")
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "The front-end build product does not exist, please run it first cd web-ui && npm run build"}
        )


# Catch-all routing - Handles all front-end routing (must be placed last）
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """
    Catch-all routing, all non- API Requests are redirected to index.html
    This can support Vue Router of HTML5 History model
    """
    # If the request is for a static resource (e.g. favicon.ico），return 404
    if full_path.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js', '.json')):
        return JSONResponse(status_code=404, content={"error": "Resource not found"})

    # All other paths return index.html，Let the front-end routing handle it
    if os.path.exists("dist/index.html"):
        return FileResponse("dist/index.html")
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "The front-end build product does not exist, please run it first cd web-ui && npm run build"}
        )


if __name__ == "__main__":
    import uvicorn
    from src.infrastructure.config.settings import settings

    print(f"Start new architecture application, port: {settings.server_port}")
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)
