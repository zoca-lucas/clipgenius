"""
ClipGenius - Database Setup
Thread-safe SQLite configuration with scoped sessions and WAL mode
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from config import DATABASE_URL
import threading

# Create engine with proper connection pooling for SQLite
# Using QueuePool with pool_size=5 for concurrent access
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # Wait up to 30s for locks
    },
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # Verify connections are alive
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Configure SQLite for better concurrent access:
    - WAL mode: allows concurrent reads during writes
    - busy_timeout: wait for locks instead of failing immediately
    - synchronous=NORMAL: good balance of safety and speed
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create session factory
_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session provides thread-local sessions
# Each thread gets its own session instance
SessionLocal = scoped_session(_session_factory)

Base = declarative_base()

# Lock for critical database operations
db_lock = threading.Lock()


def get_db():
    """
    Dependency to get database session for FastAPI endpoints.
    Uses scoped_session for thread-safety.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_background_session():
    """
    Get a new session for background tasks.
    Returns a session that must be manually closed.
    """
    return _session_factory()


def init_db():
    """Initialize database tables and verify WAL mode"""
    Base.metadata.create_all(bind=engine)

    # Verify WAL mode is enabled
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA journal_mode"))
        mode = result.scalar()
        print(f"📦 SQLite journal mode: {mode}")
