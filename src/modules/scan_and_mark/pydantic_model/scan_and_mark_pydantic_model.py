from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import AfterValidator, BaseModel


def _validate_uuid(v: str) -> str:
    # Client-generated ids are the DB primary keys (@db.Uuid columns). Validate the format
    # here so a malformed id returns a clean 422 instead of a raw Postgres 22P02 (500).
    try:
        UUID(v)
    except (ValueError, AttributeError, TypeError):
        raise ValueError("must be a valid UUID")
    return v


# A UUID string kept as `str` (Prisma's @db.Uuid columns take str), validated on the way in.
UuidStr = Annotated[str, AfterValidator(_validate_uuid)]


class SubmissionPdfMetadata(BaseModel):
    submission_id: UuidStr  # client-generated; used as the homework_submission_onetime PK
    file_name: str
    content_type: str
    file_size: int
    checksum: str
    student_name: str


class MarkingSchemeMetadata(BaseModel):
    marking_scheme_id: Optional[UuidStr] = None  # client-generated PK; None when no marking scheme
    file_name: str
    file_size: int
    content_type: str
    checksum: str


class OnetimeCriteria(BaseModel):
    homeworkTitle: str
    selectedLevel: str
    selectedOneTimeSubject: str
    markingScheme: MarkingSchemeMetadata


class ClassCriteria(BaseModel):
    pass  # TODO: define class criteria fields


class CreateDatabaseRecordAndGetSignedUrlRequest(BaseModel):
    homework_id: UuidStr  # client-generated; used as the homework PK
    submission_pdf_entries: List[SubmissionPdfMetadata]
    homework_criteria: List  # [type_flag: 'onetime'|'class', criteria: dict]


class RetryCheckStorageRequest(BaseModel):
    homework_id: UuidStr
    submission_ids: List[UuidStr]
    marking_scheme_id: Optional[UuidStr] = None
