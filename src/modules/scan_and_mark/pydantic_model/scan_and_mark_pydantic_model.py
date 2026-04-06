from pydantic import BaseModel
from typing import List, Literal, Union


class HomeworkPdfMetadata(BaseModel):
    file_name: str
    content_type: str
    file_size: int
    checksum: str
    student_name: str


class MarkingSchemeMetadata(BaseModel):
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


class UploadForSignedUrlRequest(BaseModel):
    homework_pdf_entries: List[HomeworkPdfMetadata]
    homework_criteria: List  # [type_flag: 'onetime'|'class', criteria: dict]
