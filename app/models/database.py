"""
SQLAlchemy database setup with SQLite (aiosqlite).

Defines the database schema and models for storing:
- Contests
- Problems
- Submissions
- Sandbox execution logs
"""

import datetime
from typing import Any, Optional
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import config
from app.utils.logger import logger

Base = declarative_base()


class Contest(Base):
    """Database model for CodeChef contests."""

    __tablename__ = "contests"

    contest_code = Column(String, primary_key=True)
    contest_name = Column(String, nullable=False)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    problem_count = Column(Integer, default=0)
    solved_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Problem(Base):
    """Database model for contest problems."""

    __tablename__ = "problems"

    problem_code = Column(String, primary_key=True)
    contest_code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    statement = Column(Text, nullable=True)
    time_limit = Column(String, default="1")
    memory_limit = Column(String, default="50000")
    difficulty = Column(String, default="unknown")
    constraints = Column(Text, nullable=True)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Submission(Base):
    """Database model for user code submissions."""

    __tablename__ = "submissions"

    submission_id = Column(String, primary_key=True)
    contest_code = Column(String, nullable=False)
    problem_code = Column(String, nullable=False)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    verdict = Column(String, default="Pending")
    verdict_code = Column(String, default="wait")
    execution_time = Column(String, default="N/A")
    memory = Column(String, default="N/A")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class ExecutionLog(Base):
    """Database model for secure sandbox executions."""

    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language = Column(String, nullable=False)
    exit_code = Column(Integer, default=0)
    timed_out = Column(Boolean, default=False)
    execution_time = Column(Float, default=0.0)
    compile_error = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


# Asynchronous engine and session maker
engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database schemas and create tables."""
    try:
        async with engine.begin() as conn:
            # Create all tables defined in Base metadata
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def save_contest(
    contest_code: str,
    name: str,
    start_date: str = "",
    end_date: str = "",
    problem_count: int = 0,
    solved_count: int = 0,
) -> None:
    """Save or update a contest in the database."""
    async with AsyncSessionLocal() as session:
        try:
            contest = await session.get(Contest, contest_code)
            if not contest:
                contest = Contest(contest_code=contest_code)
                session.add(contest)
            
            contest.contest_name = name
            contest.start_date = start_date
            contest.end_date = end_date
            contest.problem_count = problem_count
            contest.solved_count = solved_count
            
            await session.commit()
            logger.debug(f"Saved contest {contest_code} to database")
        except Exception as e:
            logger.error(f"Failed to save contest: {e}")
            await session.rollback()


async def get_contest(contest_code: str) -> Optional[Contest]:
    """Retrieve a contest by code."""
    async with AsyncSessionLocal() as session:
        return await session.get(Contest, contest_code)


async def save_problem(problem_data: dict) -> None:
    """Save or update a problem in the database."""
    code = problem_data.get("problem_code")
    if not code:
        return

    async with AsyncSessionLocal() as session:
        try:
            problem = await session.get(Problem, code)
            if not problem:
                problem = Problem(problem_code=code)
                session.add(problem)
            
            problem.contest_code = problem_data.get("contest_code", "")
            problem.name = problem_data.get("name", code)
            problem.statement = problem_data.get("statement", "")
            problem.time_limit = str(problem_data.get("time_limit", "1"))
            problem.memory_limit = str(problem_data.get("memory_limit", "50000"))
            problem.difficulty = problem_data.get("difficulty", "unknown")
            problem.constraints = problem_data.get("constraints", "")
            problem.input_format = problem_data.get("input_format", "")
            problem.output_format = problem_data.get("output_format", "")
            problem.url = problem_data.get("url", "")
            
            await session.commit()
            logger.debug(f"Saved problem {code} to database")
        except Exception as e:
            logger.error(f"Failed to save problem: {e}")
            await session.rollback()


async def get_problem(problem_code: str) -> Optional[Problem]:
    """Retrieve a problem by code."""
    async with AsyncSessionLocal() as session:
        return await session.get(Problem, problem_code)


async def save_submission(
    submission_id: str,
    contest_code: str,
    problem_code: str,
    language: str,
    code: str,
    verdict: str = "Pending",
    verdict_code: str = "wait",
    execution_time: str = "N/A",
    memory: str = "N/A",
) -> None:
    """Save or update a submission in the database."""
    async with AsyncSessionLocal() as session:
        try:
            sub = await session.get(Submission, submission_id)
            if not sub:
                sub = Submission(submission_id=submission_id)
                session.add(sub)
            
            sub.contest_code = contest_code
            sub.problem_code = problem_code
            sub.language = language
            sub.code = code
            sub.verdict = verdict
            sub.verdict_code = verdict_code
            sub.execution_time = execution_time
            sub.memory = memory
            
            await session.commit()
            logger.debug(f"Saved submission {submission_id} to database")
        except Exception as e:
            logger.error(f"Failed to save submission: {e}")
            await session.rollback()


async def get_submission(submission_id: str) -> Optional[Submission]:
    """Retrieve a submission by ID."""
    async with AsyncSessionLocal() as session:
        return await session.get(Submission, submission_id)


async def get_problem_submissions(problem_code: str) -> list[Submission]:
    """Retrieve all submissions for a problem ordered by time descending."""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Submission)
            .where(Submission.problem_code == problem_code)
            .order_by(Submission.timestamp.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def save_execution_log(
    language: str,
    exit_code: int,
    timed_out: bool,
    execution_time: float,
    compile_error: Optional[str] = None,
    stdout: Optional[str] = None,
    stderr: Optional[str] = None,
) -> None:
    """Save a sandbox execution log in the database."""
    async with AsyncSessionLocal() as session:
        try:
            log = ExecutionLog(
                language=language,
                exit_code=exit_code,
                timed_out=timed_out,
                execution_time=execution_time,
                compile_error=compile_error,
                stdout=stdout,
                stderr=stderr,
            )
            session.add(log)
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to save execution log: {e}")
            await session.rollback()
