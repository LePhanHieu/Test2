"""Safely remove unreviewed accounts while retaining medical and review records."""
from pathlib import Path
from sqlalchemy import select
from werkzeug.utils import secure_filename
from flask import current_app
from ..extensions import db
from ..models import DoctorApplication, User


def pending_certificate(user):
    application = db.session.scalar(
        select(DoctorApplication).where(DoctorApplication.user_id == user.id)
    )
    if application is not None and application.status == "PENDING":
        return application.certificate_path
    return None


def deletion_blocker(user: User) -> str | None:
    """Check actual references; a PENDING application isn't medical history."""
    application = db.session.scalar(
        select(DoctorApplication).where(DoctorApplication.user_id == user.id)
    )
    if application is not None and application.status != "PENDING":
        return "Tài khoản có lịch sử xét duyệt bác sĩ cần lưu giữ."

    for table in db.metadata.tables.values():
        if table.name == "users":
            continue
        for column in table.columns:
            for fk in column.foreign_keys:
                if fk.column.table.name != "users":
                    continue
                # This one application may be removed together with its owner.
                # Never exempt other references, even if their FK uses CASCADE.
                if (table.name == "doctor_applications" and column.name == "user_id"
                        and application is not None and application.status == "PENDING"):
                    continue
                if (fk.ondelete or "").upper() == "SET NULL":
                    continue
                if db.session.execute(
                    select(column).where(column == user.id).limit(1)
                ).first():
                    return f"Không thể xóa: tài khoản còn dữ liệu liên quan tại bảng {table.name}."
    return None


def delete_unrelated_user(user: User) -> str | None:
    """Remove the account and optional pending application in caller's transaction."""
    blocker = deletion_blocker(user)
    if blocker:
        return blocker
    application = db.session.scalar(
        select(DoctorApplication).where(DoctorApplication.user_id == user.id)
    )
    if application is not None:
        db.session.delete(application)
        db.session.flush()
    db.session.delete(user)
    db.session.flush()
    return None


def cleanup_pending_certificate(filename: str | None) -> None:
    """Only after a successful DB commit, remove a unique, in-folder certificate."""
    if not filename or filename != secure_filename(filename):
        return
    if db.session.scalar(
        select(DoctorApplication.id).where(DoctorApplication.certificate_path == filename).limit(1)
    ) is not None:
        return
    root = (Path(current_app.config["UPLOAD_FOLDER"]) / "doctor-certificates").resolve()
    candidate = (root / filename).resolve()
    if candidate.parent != root:
        return
    try:
        candidate.unlink(missing_ok=True)
    except OSError:
        current_app.logger.exception("Unable to clean up pending certificate %s", filename)
