"""
Database Helper Utilities

This module provides a context manager for database connections, replacing
repetitive try/except/finally patterns throughout the codebase with a clean,
reusable interface.

Usage:
    from utils.db_helpers import db_connection, db_transaction

    # Read-only operations (auto-closes, no commit)
    with db_connection() as (conn, cursor):
        cursor.execute("SELECT * FROM table")
        results = cursor.fetchall()

    # Write operations (auto-commit on success, rollback on error)
    with db_transaction() as (conn, cursor):
        cursor.execute("INSERT INTO table ...")
        # Commits automatically if no exception
"""

from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
from utils.database import get_db_connection


@contextmanager
def db_connection(cursor_factory=RealDictCursor):
    """
    Context manager for read-only database operations.

    Automatically handles connection cleanup. Does not commit.
    Use db_transaction() for write operations.

    @param cursor_factory: Cursor factory to use (default: RealDictCursor)
    @yields: Tuple of (connection, cursor)

    @example:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise ConnectionError("Failed to establish database connection")
        cursor = conn.cursor(cursor_factory=cursor_factory)
        yield conn, cursor
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@contextmanager
def db_transaction(cursor_factory=RealDictCursor):
    """
    Context manager for database write operations with automatic commit/rollback.

    Commits on successful completion, rolls back on any exception.

    @param cursor_factory: Cursor factory to use (default: RealDictCursor)
    @yields: Tuple of (connection, cursor)
    @raises: Re-raises any exception after rollback

    @example:
        with db_transaction() as (conn, cursor):
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
            # Auto-commits if no exception
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise ConnectionError("Failed to establish database connection")
        cursor = conn.cursor(cursor_factory=cursor_factory)
        yield conn, cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_one(query, params=None, cursor_factory=RealDictCursor):
    """
    Execute a query and return a single result.

    @param query: SQL query string
    @param params: Query parameters (tuple or dict)
    @param cursor_factory: Cursor factory to use
    @return: Single row as dict (or None if no results)

    @example:
        user = fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
    """
    with db_connection(cursor_factory=cursor_factory) as (conn, cursor):
        cursor.execute(query, params)
        return cursor.fetchone()


def fetch_all(query, params=None, cursor_factory=RealDictCursor):
    """
    Execute a query and return all results.

    @param query: SQL query string
    @param params: Query parameters (tuple or dict)
    @param cursor_factory: Cursor factory to use
    @return: List of rows as dicts

    @example:
        users = fetch_all("SELECT * FROM users WHERE role = %s", (role,))
    """
    with db_connection(cursor_factory=cursor_factory) as (conn, cursor):
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_query(query, params=None, returning=False):
    """
    Execute a write query with automatic commit.

    @param query: SQL query string
    @param params: Query parameters (tuple or dict)
    @param returning: If True, returns the result of RETURNING clause
    @return: If returning=True, returns fetchone() result; otherwise None

    @example:
        # Simple insert
        execute_query("INSERT INTO logs (msg) VALUES (%s)", (message,))

        # Insert with RETURNING
        new_id = execute_query(
            "INSERT INTO users (name) VALUES (%s) RETURNING id",
            (name,),
            returning=True
        )
    """
    with db_transaction() as (conn, cursor):
        cursor.execute(query, params)
        if returning:
            return cursor.fetchone()
        return None


def execute_many(query, params_list):
    """
    Execute a query multiple times with different parameters.

    @param query: SQL query string
    @param params_list: List of parameter tuples/dicts

    @example:
        execute_many(
            "INSERT INTO scores (user_id, score) VALUES (%s, %s)",
            [(1, 100), (2, 95), (3, 88)]
        )
    """
    with db_transaction() as (conn, cursor):
        cursor.executemany(query, params_list)
