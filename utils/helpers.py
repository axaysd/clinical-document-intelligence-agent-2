"""
Helper utility functions for the Clinical Document Intelligence Agent.
"""

import uuid
import hashlib
from datetime import datetime
from typing import Any


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"sess_{uuid.uuid4().hex[:12]}"


def generate_document_id(filename: str) -> str:
    """Generate a deterministic document ID based on filename."""
    hash_obj = hashlib.md5(filename.encode())
    return f"doc_{hash_obj.hexdigest()[:12]}"


def generate_chunk_id(doc_id: str, chunk_index: int) -> str:
    """Generate a chunk ID."""
    return f"{doc_id}_chunk_{chunk_index:04d}"


def get_timestamp() -> str:
    """Get ISO format timestamp."""
    return datetime.utcnow().isoformat() + "Z"


def hash_text(text: str) -> str:
    """Generate SHA256 hash of text (for audit logging)."""
    return hashlib.sha256(text.encode()).hexdigest()


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path separators and dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    return "".join(c for c in filename if c in safe_chars)
