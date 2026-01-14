"""
Results file management routing
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List
import os
import glob
import json
import aiofiles


router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/files")
async def get_result_files():
    """Get a list of all result files"""
    # Mainly from jsonl Get files from directory
    jsonl_dir = "jsonl"
    files = []

    if os.path.isdir(jsonl_dir):
        files = [f for f in os.listdir(jsonl_dir) if f.endswith(".jsonl")]

    # The return format is consistent with the front-end expectation
    return {"files": files}


@router.get("/files/{filename:path}")
async def download_result_file(filename: str):
    """Download the specified results file"""
    # Security Check: Prevent path traversal attacks
    if ".." in filename or filename.startswith("/"):
        return {"error": "Illegal file path"}

    # The file is in jsonl in directory
    file_path = os.path.join("jsonl", filename)

    if not os.path.exists(file_path) or not filename.endswith(".jsonl"):
        return {"error": "File does not exist"}

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/x-ndjson"
    )


@router.delete("/files/{filename:path}")
async def delete_result_file(filename: str):
    """Delete the specified result file"""
    # Security Check: Prevent path traversal attacks
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Illegal file path")

    # Only delete is allowed .jsonl document
    if not filename.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="can only be deleted .jsonl document")

    # The file is in jsonl in directory
    file_path = os.path.join("jsonl", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File does not exist")

    try:
        os.remove(file_path)
        return {"message": f"document {filename} Deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the file: {str(e)}")


@router.get("/{filename}")
async def get_result_file_content(
    filename: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    recommended_only: bool = Query(False),
    sort_by: str = Query("crawl_time"),
    sort_order: str = Query("desc"),
):
    """Read the specified .jsonl File content, support paging、Filter and sort"""
    # security check
    if not filename.endswith(".jsonl") or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid file name")

    filepath = os.path.join("jsonl", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Result file not found")

    results = []
    try:
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            async for line in f:
                try:
                    record = json.loads(line)
                    if recommended_only:
                        if record.get("ai_analysis", {}).get("is_recommended") is True:
                            results.append(record)
                    else:
                        results.append(record)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while reading the results file: {e}")

    # Sorting logic
    def get_sort_key(item):
        info = item.get("Product information", {})
        if sort_by == "publish_time":
            return info.get("Release time", "0000-00-00 00:00")
        elif sort_by == "price":
            price_str = str(info.get("Current selling price", "0")).replace("¥", "").replace(",", "").strip()
            try:
                return float(price_str)
            except (ValueError, TypeError):
                return 0.0
        else:  # default to crawl_time
            return item.get("Crawl time", "")

    is_reverse = (sort_order == "desc")
    results.sort(key=get_sort_key, reverse=is_reverse)

    # Pagination
    total_items = len(results)
    start = (page - 1) * limit
    end = start + limit
    paginated_results = results[start:end]

    return {
        "total_items": total_items,
        "page": page,
        "limit": limit,
        "items": paginated_results
    }
