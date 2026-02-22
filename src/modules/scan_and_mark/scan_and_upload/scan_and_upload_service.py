from prisma import Prisma
from typing import List


class ScanAndUploadService:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_classes_with_homework(self, teacher_id: str) -> List:
        return await self.db.classes.find_many(
            where={"teacher_id": teacher_id},
            include={"homework": True},
        )
