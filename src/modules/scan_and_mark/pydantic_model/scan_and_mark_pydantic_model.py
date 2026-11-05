from typing import Annotated, List, Literal, Optional
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, field_validator


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


class QuestionDocumentMetadata(BaseModel):
    question_document_id: UuidStr
    file_name: str = Field(min_length=1)
    file_size: int = Field(ge=0)
    content_type: Literal['application/pdf']
    checksum: str = Field(min_length=1)

    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        # This becomes one storage-path segment, never a client-supplied path.
        if not value.strip() or any(char in value for char in ('/', '\\', '\x00')) or value in ('.', '..'):
            raise ValueError('file_name must be a filename without path separators')
        return value


class HomeworkExtraInformation(BaseModel):
    questions: str = ''
    marking_guidance: str = ''
    marking_answers: str = ''
    question_filter: str = ''


class OnetimeCriteria(BaseModel):
    homeworkTitle: str
    selectedLevel: str
    selectedOneTimeSubject: str
    markingScheme: MarkingSchemeMetadata
    questionDocument: QuestionDocumentMetadata | None = None
    extra_information: HomeworkExtraInformation = Field(default_factory=HomeworkExtraInformation)


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
    question_document_id: Optional[UuidStr] = None
