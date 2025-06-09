from fastapi import APIRouter, Request, Form, UploadFile, File, Query
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import aiofiles

from mcp_server import (
    mcp_get_all_submissions,
    mcp_create_submission,
    mcp_get_pending_submissions,
    mcp_update_submission_status,
    mcp_get_submission_by_id,
    mcp_get_submissions_by_folder,
    mcp_get_submissions_grouped_by_folder,
    mcp_update_submission_filepath
)
from email_utils import send_approval_email, notify_sender  # If you split email logic
 
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
 
router = APIRouter()
templates = Jinja2Templates(directory="templates")
 
@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
 
@router.get("/home")
def home(request: Request):
    folders = mcp_get_submissions_grouped_by_folder()
   
    return templates.TemplateResponse("home.html", {
        "request": request,
        "folders": folders
    })
 
@router.get("/login")
def login_get(request: Request, role: str = "sender"):
    return templates.TemplateResponse("login.html", {"request": request, "role": role, "error": None})
 
@router.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    if username == "sender" and password == "sender123":
        return RedirectResponse("/sender", status_code=302)
    elif username == "approver" and password == "approver123":
        return RedirectResponse("/approve", status_code=302)
    return RedirectResponse("/login", status_code=302)
 
@router.get("/sender")
def sender_get(request: Request):
    submissions = mcp_get_all_submissions()
    return templates.TemplateResponse("sender.html", {
        "request": request,
        "submissions": submissions,
        "message": request.query_params.get("message")
    })
 
@router.post("/sender")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder: str = Form(...),
    sender_email: str = Form(...),
    sender_password: str = Form(...),
    approver_email: str = Form(...)
):
    # submission_id is now generated within mcp_create_submission
    folder_path = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
 
   # 1. Create the submission record.
    # mcp_create_submission now takes filepath as an optional argument.
    # We'll pass None initially, or a placeholder if your mcp_server.py still requires it.
    # Assuming your mcp_server.py was updated as per previous suggestion:
    submission = mcp_create_submission(
        filename=file.filename,
        folder=folder,
        sender_email=sender_email,
        sender_password=sender_password, # SECURITY WARNING: Storing/using plaintext passwords
        approver_email=approver_email
    )
    if not submission:
        # Handle error: submission creation failed
        return RedirectResponse("/sender?message=Error creating submission record", status_code=303) # Or 500

    # 2. Construct the actual filepath using the submission ID.
    actual_filepath = os.path.join(folder_path, f"{submission.id}_{file.filename}")

    # 3. Save the uploaded file to this actual_filepath.
    async with aiofiles.open(actual_filepath, "wb") as buffer:
        content = await file.read()  # Read content from UploadFile
        await buffer.write(content)  # Asynchronously write to file

    # 4. Update the submission record with the actual_filepath.
    updated_submission = mcp_update_submission_filepath(submission.id, actual_filepath)

    if updated_submission:
         # 5. Send email using the submission object that now has the correct filepath.
         send_approval_email(updated_submission) # Use the object with the correct filepath
 
    return RedirectResponse("/sender?message=File submitted successfully", status_code=303)
 
@router.get("/approve")
def approve_get(request: Request):
    pending = mcp_get_pending_submissions()
    return templates.TemplateResponse("approve.html", {
        "request": request,
        "pending": pending
    })
 
@router.post("/approve")
async def submit_decision(submission_id: str = Form(...), action: str = Form(...)):
    new_status = "Approved" if action == "approve" else "Referred Back"
    submission = mcp_update_submission_status(submission_id, new_status)
    if submission:
        notify_sender(submission)
    return RedirectResponse("/approve", status_code=303)
 
@router.get("/email/decision/{submission_id}/{action}")
def email_decision(submission_id: str, action: str):
    # It's generally better to fetch the submission first to check its current status if needed
    current_submission = mcp_get_submission_by_id(submission_id)
    if current_submission and current_submission.status == "Pending Approval":
        new_status = "Approved" if action == "approve" else "Referred Back"
        submission = mcp_update_submission_status(submission_id, new_status)
        notify_sender(submission)
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
  <title>Decision Recorded</title>
  <script>
    alert("The file '{current_submission.filename}' has been {'approved' if action == 'approve' else 'referred back'}.");
    window.close(); // Try to close the tab
  </script>
</head>
<body>
  <p>If this tab doesn't close automatically, you can close it manually.</p>
</body>
</html>
""")
 
@router.get("/download/{submission_id}")
def download_file(submission_id: str):
    submission = mcp_get_submission_by_id(submission_id)
    if submission:
        return FileResponse(submission.filepath, filename=submission.filename)
    return {"error": "File not found"}
 
@router.get("/folderview")
def folderview_get(request: Request, folder: str = Query(None)):
    if folder:
        # Show specific folder's files
        submissions = mcp_get_submissions_by_folder(folder)
        return templates.TemplateResponse("folderview.html", {
            "request": request,
            "folder_name": folder,
            "files": submissions
        })
    else:
        # Show list of folders with grouped files (same as /home)
        folders = mcp_get_submissions_grouped_by_folder()
        return templates.TemplateResponse("home.html", {
            "request": request,
            "folders": folders
        })
   
def include_routes(app):
    app.include_router(router)