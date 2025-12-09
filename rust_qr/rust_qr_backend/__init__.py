"""
Rust QR Backend Module
High-performance QR code generation and reading using Rust
"""

try:
    from .rust_qr_backend import scan_image_bytes, clean_json_string, scan_raw_luma
    __all__ = ["scan_image_bytes", "clean_json_string", "scan_raw_luma"]
except ImportError:
    # Fallback for different import scenarios
    try:
        from . import rust_qr_backend as _rust_qr_backend
        scan_image_bytes = _rust_qr_backend.scan_image_bytes
        clean_json_string = _rust_qr_backend.clean_json_string
        scan_raw_luma = _rust_qr_backend.scan_raw_luma
        __all__ = ["scan_image_bytes", "clean_json_string", "scan_raw_luma"]
    except ImportError:
        pass

__version__ = "1.1.0"
