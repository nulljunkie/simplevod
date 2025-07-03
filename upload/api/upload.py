from typing import Annotated, Dict, List
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import ValidationError
from models.models import (
    InitiateUploadRequest, PresignedUrlRequest, PresignedUrlsRequest, RecordPartRequest,
    CompleteUploadRequest, AbortUploadRequest, ListPartsRequest, SessionData, Parts,
)
from auth.auth import CurrentUser
from .dependencies import get_storage_service, get_session_service, get_video_service
from services.storage import StorageService
from services.session import SessionService
from services.video import VideoService
from core.config import logger

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/initiate")
async def initiate_upload(
    request: InitiateUploadRequest,
    user: CurrentUser,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> Dict:
    """Initiate a multipart video upload."""
    try:
        result = await storage_service.initiate_upload(request, user.user_id)
        await session_service.store_session(result["key"], result["session_data"])
        logger.info(f"Initiated upload for key '{result['key']}' by user '{user.user_id}'")
        return {
            "success": True,
            "message": "Upload initiated successfully",
            "data": {
                "key": result["key"],
                "uploadId": result["upload_id"],
                "objectKey": result["object_key"],
                **({"thumbnailUploadUrl": result["thumbnail_url"]} if result["thumbnail_url"] else {}),
            }
        }
    except Exception as e:
        logger.error(f"Failed to initiate upload: {str(e)}")
        if "upload_id" in locals() and "object_key" in locals():
            await storage_service.abort_upload(result["object_key"], result["upload_id"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/presigned-url")
async def get_presigned_url(
    request: PresignedUrlRequest,
    user: CurrentUser,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> Dict:
    """Generate a presigned URL for a single upload part."""
    session_data = await session_service.validate_session(request.key, user.user_id, "pending")
    url = await storage_service.get_presigned_url(
        session_data.object_key, session_data.minio_upload_id, request.part_number
    )
    await session_service.extend_session_expiry(request.key)
    logger.debug(f"Generated presigned URL for key '{request.key}', part {request.part_number}")
    return {"success": True, "message": "Presigned URL generated", "data": {"url": url}}

@router.post("/presigned-urls")
async def get_presigned_urls(
    request: PresignedUrlsRequest,
    user: CurrentUser,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> Dict:
    """Generate presigned URLs for multiple upload parts."""
    session_data = await session_service.validate_session(request.key, user.user_id, "pending")
    if any(pn > session_data.total_parts for pn in request.part_numbers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Part numbers exceed total parts ({session_data.total_parts})",
        )
    urls = await storage_service.get_presigned_urls(
        session_data.object_key, session_data.minio_upload_id, request.part_numbers
    )
    await session_service.extend_session_expiry(request.key)
    logger.debug(f"Generated {len(urls)} presigned URLs for key '{request.key}'")
    return {"success": True, "message": "Presigned URLs generated", "data": {"urls": urls}}

@router.post("/record-part")
async def record_part(
    request: RecordPartRequest,
    user: CurrentUser,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> Dict:
    """Record a completed upload part."""
    session_data = await session_service.validate_session(request.key, user.user_id, "pending")
    await session_service.record_part(request.key, request.part_number, request.etag)
    logger.info(f"Recorded part {request.part_number} for key '{request.key}'")
    return {"success": True, "message": "Part recorded successfully", "data": {}}

@router.post("/list-parts")
async def list_parts(
    request: ListPartsRequest,
    user: CurrentUser,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> Dict:
    """List all recorded parts for an upload."""
    session_data = await session_service.validate_session(request.key, user.user_id)
    parts = await session_service.list_parts(request.key)
    await session_service.extend_session_expiry(request.key)
    logger.info(f"Listed {len(parts)} parts for key '{request.key}'")
    return {"success": True, "message": "Parts listed successfully", "data": {"uploadedParts": parts}}

@router.post("/complete")
async def complete_upload(
    request: CompleteUploadRequest,
    user: CurrentUser,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    video_service: Annotated[VideoService, Depends(get_video_service)],
    background_tasks: BackgroundTasks,
) -> Dict:
    """Complete a multipart video upload."""
    session_data = await session_service.validate_session(request.key, user.user_id, "pending")
    parts_list = await session_service.list_parts(request.key)
    try:
        parts = Parts(parts=parts_list)
    except ValidationError as e:
        logger.error(f"Part validation failed for key '{request.key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during part validation."
        )

    await storage_service.complete_upload(session_data.object_key, session_data.minio_upload_id, parts)
    video = await video_service.save_video(request.key, session_data, parts, user.user_id, user.username, storage_service)
    session_data.status = "completed"
    await session_service.store_session(request.key, session_data)
    background_tasks.add_task(video_service.publish_processing_message, video)
    await session_service.cleanup_session(request.key)
    logger.info(f"Completed upload for key '{request.key}'")
    return {
        "success": True,
        "message": "Upload completed successfully",
        "data": {"video_id": request.key}
    }


@router.post("/abort")
async def abort_upload(
    request: AbortUploadRequest,
    user: CurrentUser,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    background_tasks: BackgroundTasks,
) -> Dict:
    """Abort a multipart video upload."""
    session_data = await session_service.validate_session(request.key, user.user_id)
    if session_data.status == "completed":
        return {"success": False, "message": "Upload already completed, cannot abort", "data": {}}
    if session_data.minio_upload_id:
        await storage_service.abort_upload(session_data.object_key, session_data.minio_upload_id)
    background_tasks.add_task(session_service.cleanup_session, request.key)
    logger.info(f"Aborted upload for key '{request.key}'")
    return {"success": True, "message": "Upload aborted successfully", "data": {}}
