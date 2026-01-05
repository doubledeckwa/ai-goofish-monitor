"""
日志管理路由
"""
import os
import aiofiles
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.api.dependencies import get_current_user


router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def get_logs(
    from_pos: int = 0,
    username: str = Depends(get_current_user)
):
    """获取日志内容（增量读取）"""
    log_file_path = os.path.join("logs", "scraper.log")

    if not os.path.exists(log_file_path):
        return JSONResponse(content={
            "new_content": "日志文件不存在或尚未创建。",
            "new_pos": 0
        })

    try:
        async with aiofiles.open(log_file_path, 'rb') as f:
            await f.seek(0, os.SEEK_END)
            file_size = await f.tell()

            if from_pos >= file_size:
                return {"new_content": "", "new_pos": file_size}

            await f.seek(from_pos)
            new_bytes = await f.read()

        new_content = new_bytes.decode('utf-8', errors='replace')
        return {"new_content": new_content, "new_pos": file_size}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"new_content": f"\n读取日志文件时出错: {e}", "new_pos": from_pos}
        )


@router.delete("", response_model=dict)
async def clear_logs(username: str = Depends(get_current_user)):
    """清空日志文件"""
    log_file_path = os.path.join("logs", "scraper.log")

    if not os.path.exists(log_file_path):
        return {"message": "日志文件不存在，无需清空。"}

    try:
        async with aiofiles.open(log_file_path, 'w', encoding='utf-8') as f:
            await f.write("")
        return {"message": "日志已成功清空。"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"清空日志文件时出错: {e}"}
        )
