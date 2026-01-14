"""
Login status management routing
"""
import os
import json
import aiofiles
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/login-state", tags=["login-state"])


class LoginStateUpdate(BaseModel):
    """Login status update model"""
    content: str


@router.post("", response_model=dict)
async def update_login_state(
    data: LoginStateUpdate,
):
    """Receive the login status sent by the front endJSONstring and save to xianyu_state.json"""
    state_file = "xianyu_state.json"

    try:
        # Verify if it is validJSON
        json.loads(data.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="The content provided is not validJSONFormat。")

    try:
        async with aiofiles.open(state_file, 'w', encoding='utf-8') as f:
            await f.write(data.content)
        return {"message": f"Login status file '{state_file}' Updated successfully。"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing login status file: {e}")


@router.delete("", response_model=dict)
async def delete_login_state():
    """delete xianyu_state.json document"""
    state_file = "xianyu_state.json"

    if os.path.exists(state_file):
        try:
            os.remove(state_file)
            return {"message": "Login status file deleted successfully。"}
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Error deleting login status file: {e}")

    return {"message": "The login status file does not exist and does not need to be deleted.。"}
