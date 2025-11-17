"""
Database utilities for storing and tracking email campaigns.

Uses SQLite for local storage with full ACID compliance.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class Database:
    """Database manager for university email campaigns."""

    def __init__(self, db_path: Path = config.DB_PATH):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create database and tables if they don't exist."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                sent_at DATETIME,
                response_at DATETIME,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(university, email)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON email_campaigns(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email ON email_campaigns(email)
        """)

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_email(
            self,
            university: str,
            email: str,
            status: str = config.STATUS_PENDING
    ) -> Optional[int]:
        """
        Insert a new email campaign record.
        
        Args:
            university: University name
            email: Email address
            status: Initial status
        
        Returns:
            Record ID if successful, None otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO email_campaigns (university, email, status)
                VALUES (?, ?, ?)
            """, (university, email, status))
            self.conn.commit()

            if cursor.lastrowid > 0:
                logger.debug(f"Inserted email: {email} for {university}")
                return cursor.lastrowid
            return None
        except sqlite3.Error as e:
            logger.error(f"Error inserting email {email}: {e}")
            return None

    def update_status(
            self,
            email: str,
            status: str,
            error: Optional[str] = None,
            increment_retry: bool = False
    ) -> bool:
        """
        Update email campaign status.
        
        Args:
            email: Email address to update
            status: New status
            error: Error message if applicable
            increment_retry: Whether to increment retry count
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()

            sent_at = datetime.now() if status == config.STATUS_SENT else None

            if increment_retry:
                cursor.execute("""
                    UPDATE email_campaigns
                    SET status = ?,
                        error = ?,
                        retry_count = retry_count + 1,
                        updated_at = CURRENT_TIMESTAMP,
                        sent_at = COALESCE(sent_at, ?)
                    WHERE email = ?
                """, (status, error, sent_at, email))
            else:
                cursor.execute("""
                    UPDATE email_campaigns
                    SET status = ?,
                        error = ?,
                        updated_at = CURRENT_TIMESTAMP,
                        sent_at = COALESCE(sent_at, ?)
                    WHERE email = ?
                """, (status, error, sent_at, email))

            self.conn.commit()
            logger.debug(f"Updated {email} to status {status}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating status for {email}: {e}")
            return False

    def get_pending_emails(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all pending emails to send.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of email records as dictionaries
        """
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT * FROM email_campaigns
                WHERE status IN (?, ?)
                ORDER BY created_at ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (config.STATUS_PENDING, config.STATUS_RETRYING))
            rows = cursor.fetchall()

            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching pending emails: {e}")
            return []

    def get_statistics(self) -> Dict[str, int]:
        """
        Get campaign statistics.
        
        Returns:
            Dictionary with status counts
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM email_campaigns
                GROUP BY status
            """)

            stats = {row['status']: row['count'] for row in cursor.fetchall()}

            # Add total
            cursor.execute("SELECT COUNT(*) as total FROM email_campaigns")
            stats['TOTAL'] = cursor.fetchone()['total']

            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def email_exists(self, university: str, email: str) -> bool:
        """
        Check if email already exists in database.
        
        Args:
            university: University name
            email: Email address
        
        Returns:
            True if exists, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM email_campaigns
                WHERE university = ? AND email = ?
            """, (university, email))

            return cursor.fetchone()['count'] > 0
        except sqlite3.Error as e:
            logger.error(f"Error checking email existence: {e}")
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
