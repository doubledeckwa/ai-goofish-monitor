"""
Prompt Management routing
"""
import os
import aiofiles
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptUpdate(BaseModel):
    """Prompt Update model"""
    content: str


@router.get("")
async def list_prompts():
    """list all prompt document"""
    prompts_dir = "prompts"
    if not os.path.isdir(prompts_dir):
        return []
    return [f for f in os.listdir(prompts_dir) if f.endswith(".txt")]


@router.get("/{filename}")
async def get_prompt(filename: str):
    """get prompt File content"""
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid file name")

    filepath = os.path.join("prompts", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Prompt file not found")

    async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
        content = await f.read()
    return {"filename": filename, "content": content}


@router.put("/{filename}")
async def update_prompt(
    filename: str,
    prompt_update: PromptUpdate,
):
    """renew prompt File content"""
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid file name")

    filepath = os.path.join("prompts", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Prompt file not found")

    try:
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(prompt_update.content)
        return {"message": f"Prompt document '{filename}' Update successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {e}")
