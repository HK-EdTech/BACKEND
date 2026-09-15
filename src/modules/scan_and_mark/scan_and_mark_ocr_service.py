from prisma import Prisma


class ScanAndMarkOcrService:
    def __init__(self, db: Prisma):
        self.db = db
