from prisma import Prisma
from contextlib import asynccontextmanager

prisma_client = Prisma()

async def connect_db():
    if not prisma_client.is_connected():
        await prisma_client.connect()
    print("✅ Database connected")

async def disconnect_db():
    if prisma_client.is_connected():
        await prisma_client.disconnect()
    print("🔌 Database disconnected")
