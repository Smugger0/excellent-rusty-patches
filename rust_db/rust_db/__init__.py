"""
Rust Database Module
High-performance SQLite database operations using Rust
"""

try:
    from .rust_db import Database
    __all__ = ["Database"]
except ImportError:
    # Fallback for different import scenarios
    from . import rust_db as _rust_db
    Database = _rust_db.Database
    __all__ = ["Database"]

__version__ = "1.2.0"
