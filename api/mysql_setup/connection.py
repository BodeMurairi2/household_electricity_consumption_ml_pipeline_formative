from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

MYSQL_URL = "mysql+asyncmy://power:powerpass@mysql:3306/household_power?charset=utf8mb4"

engine = create_async_engine(
    MYSQL_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    """
    FastAPI dependency
    """
    async with SessionLocal() as session:
        yield session
