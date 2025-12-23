from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from utils.atonement import validate_atonement_proof, get_user_atonement_plans
from validation import sanitize_input, ALLOWED_FILE_TYPES
import os

router = APIRouter()

class AtonementSubmission(BaseModel):
    user_id: str
    plan_id: str
    atonement_type: str
    amount: float
    proof_text: Optional[str] = None
    tx_hash: Optional[str] = None

@router.post("/submit")
async def submit_atonement(submission: AtonementSubmission):
    """
    Submit proof for completion of an atonement task.
    """
    # Validate the submission
    success, message, updated_plan = validate_atonement_proof(
        submission.plan_id,
        submission.atonement_type,
        submission.amount,
        submission.proof_text,
        submission.tx_hash
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "status": "success",
        "message": message,
        "plan": updated_plan
    }

@router.post("/submit-with-file")
async def submit_atonement_with_file(
    user_id: str = Form(...),
    plan_id: str = Form(...),
    atonement_type: str = Form(...),
    amount: float = Form(...),
    proof_text: Optional[str] = Form(None),
    tx_hash: Optional[str] = Form(None),
    proof_file: Optional[UploadFile] = File(None)
):
    """
    Submit proof for completion of an atonement task with file upload.
    """
    # Sanitize text inputs
    if proof_text:
        proof_text = sanitize_input(proof_text)
    if tx_hash:
        tx_hash = sanitize_input(tx_hash)
    
    # Validate file if provided
    if proof_file:
        filename = proof_file.filename or ""
        ext = ("." + filename.split(".")[-1].lower()) if "." in filename else ""
        allowed_content_types = {
            'text/plain', 'application/pdf', 'image/jpeg', 'image/jpg', 
            'image/png', 'image/gif', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        # Check extension
        if ext not in ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Check content type
        content_type = proof_file.content_type or 'application/octet-stream'
        if content_type not in allowed_content_types:
            raise HTTPException(status_code=400, detail=f"Content type not allowed: {content_type}")
        
        # Read and size check (limit to 1MB)
        content = await proof_file.read()
        file_size = len(content)
        if file_size > 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 1MB limit")
        
        # Reset file pointer if possible
        if hasattr(proof_file, 'file') and hasattr(proof_file.file, 'seek'):
            try:
                proof_file.file.seek(0)
            except Exception:
                pass
        
        # Store safe file reference (only basename, strip suspicious chars)
        base_name = os.path.basename(filename)
        safe_name = base_name.replace('..', '').replace('/', '').replace('\\', '')
        file_reference = f"{plan_id}_{datetime.now(timezone.utc).timestamp()}_{safe_name}"
        proof_text = f"{proof_text or ''}\nFile reference: {file_reference}"
    
    # Validate the submission
    success, message, updated_plan = validate_atonement_proof(
        plan_id,
        atonement_type,
        amount,
        proof_text,
        tx_hash
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "status": "success",
        "message": message,
        "plan": updated_plan
    }

@router.get("/plans/{user_id}")
async def get_atonement_plans(user_id: str):
    """
    Get all atonement plans for a user.
    """
    plans = get_user_atonement_plans(user_id)
    
    return {
        "status": "success",
        "user_id": user_id,
        "plans": plans
    }