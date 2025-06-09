from models import Submission, SessionLocal
import uuid
from contextlib import contextmanager
from typing import List, Optional, Dict

# Helper to manage database sessions
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def mcp_get_all_submissions() -> List[Submission]:
    """Retrieves all submissions from the database."""
    with get_db_session() as db:
        return db.query(Submission).all()

def mcp_create_submission(
    filename: str,
    folder: str,
    sender_email: str,
    sender_password: str,
    approver_email: str,
    filepath: Optional[str] = None  
) -> Submission:
    """Creates a new submission entry in the database."""
    submission_id = str(uuid.uuid4())
    with get_db_session() as db:
        submission = Submission(
            id=submission_id,
            filename=filename,
            filepath=filepath,
            folder=folder,
            status="Pending Approval",
            sender_email=sender_email,
            sender_password=sender_password,
            approver_email=approver_email
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

def mcp_get_pending_submissions() -> List[Submission]:
    """Retrieves all submissions with 'Pending Approval' status."""
    with get_db_session() as db:
        return db.query(Submission).filter(Submission.status == "Pending Approval").all()

def mcp_update_submission_status(submission_id: str, new_status: str) -> Optional[Submission]:
    """Updates the status of a specific submission."""
    with get_db_session() as db:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = new_status
            db.commit()
            db.refresh(submission)
            return submission
        return None

def mcp_update_submission_filepath(submission_id: str, new_filepath: str) -> Optional[Submission]:
    """Updates the filepath of a specific submission."""
    with get_db_session() as db:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.filepath = new_filepath
            db.commit()
            db.refresh(submission)
            return submission
        return None

def mcp_get_submission_by_id(submission_id: str) -> Optional[Submission]:
    """Retrieves a specific submission by its ID."""
    with get_db_session() as db:
        return db.query(Submission).filter(Submission.id == submission_id).first()

def mcp_get_submissions_by_folder(folder_name: str) -> List[Submission]:
    """Retrieves all submissions within a specific folder."""
    with get_db_session() as db:
        return db.query(Submission).filter(Submission.folder == folder_name).all()

def mcp_get_submissions_grouped_by_folder() -> Dict[str, List[Submission]]:
    """Retrieves all submissions and groups them by folder."""
    submissions = mcp_get_all_submissions()
    folders: Dict[str, List[Submission]] = {}
    for sub in submissions:
        folders.setdefault(sub.folder or "Uncategorized", []).append(sub)
    return folders
