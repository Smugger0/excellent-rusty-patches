# -*- coding: utf-8 -*-
"""
Merkezi Import Dosyası
Tüm projedeki import'lar bu dosyada toplanmıştır
"""

# ============================================================================
# STANDART KÜTÜPHANELER
# ============================================================================
import sys
import os
import sqlite3
import json
import logging
import time

# ============================================================================
# LOGGİNG YAPILANDIRMASI
# ============================================================================
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
import re
import warnings
import math
import threading
import subprocess
import shutil
import locale
import calendar
import platform
import traceback
import ctypes
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Decimal hassasiyetini ayarla (para hesaplamaları için)
getcontext().prec = 22  # Yüksek hassasiyet
getcontext().rounding = ROUND_HALF_UP  # Standart yuvarlama

# ============================================================================
# WINDOWS API (Sadece Windows için)
# ============================================================================
try:
    import win32event
    import win32api
    import winerror
    WIN32_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: pywin32 kütüphanesi eksik. Windows API özellikleri çalışmayabilir.")
    win32event = None
    win32api = None
    winerror = None
    WIN32_AVAILABLE = False

# ============================================================================
# ÜÇÜNCÜ PARTI KÜTÜPHANELER - VERİ İŞLEME
# ============================================================================
import numpy as np
import pandas as pd
import requests

# ============================================================================
# FLET - Modern UI Framework
# ============================================================================
try:
    import flet as ft
    FLET_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: flet kütüphanesi eksik. UI çalışmayacak.")
    ft = None
    FLET_AVAILABLE = False

# ============================================================================
# ÜÇÜNCÜ PARTI KÜTÜPHANELER - QR KOD VE GÖRÜNTÜ İŞLEME
# ============================================================================
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: opencv-python kütüphanesi eksik. QR kod okuma işlevi devre dışı.")
    cv2 = None
    CV2_AVAILABLE = False

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: pyzbar kütüphanesi eksik. QR kod okuma işlevi devre dışı.")
    pyzbar = None
    PYZBAR_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: PyMuPDF kütüphanesi eksik. PDF QR okuma işlevi devre dışı.")
    fitz = None
    FITZ_AVAILABLE = False

try:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    CONCURRENT_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: concurrent.futures modülü eksik.")
    ThreadPoolExecutor = None
    as_completed = None
    CONCURRENT_AVAILABLE = False

# ============================================================================
# ÜÇÜNCÜ PARTI KÜTÜPHANELER - PDF İŞLEMLERİ
# ============================================================================
try:
    from reportlab.lib.pagesizes import A4, letter, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: reportlab kütüphanesi eksik. PDF export işlevi devre dışı.")
    REPORTLAB_AVAILABLE = False

# ============================================================================
# ÜÇÜNCÜ PARTI KÜTÜPHANELER - EXCEL İŞLEMLERİ
# ============================================================================
try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    logging.warning("UYARI: xlsxwriter kütüphanesi eksik. Excel export işlevi devre dışı.")
    XLSXWRITER_AVAILABLE = False

# ============================================================================
# PROJE MODÜLLERI - PDF & EXCEL EXPORT (LAZY LOADING)
# ============================================================================
# PDF ve Excel modülleri sadece ihtiyaç olduğunda yüklenecek
# Bu, uygulama başlangıç süresini hızlandırır

# Lazy loading için flag'ler
PDF_AVAILABLE = None  # None = henüz kontrol edilmedi
EXCEL_AVAILABLE = None  # None = henüz kontrol edilmedi

# Lazy loading cache
_pdf_module = None
_excel_module = None

def get_pdf_module():
    """PDF modülünü lazy loading ile yükler."""
    global _pdf_module, PDF_AVAILABLE
    
    if PDF_AVAILABLE is None:  # İlk çağrıda kontrol et
        try:
            import topdf
            _pdf_module = topdf
            PDF_AVAILABLE = True
            logging.info("✅ PDF export modülü yüklendi (lazy loading)")
        except ImportError as e:
            logging.warning(f"⚠️ PDF export modülü bulunamadı: {e}")
            PDF_AVAILABLE = False
            _pdf_module = None
    
    return _pdf_module

def get_excel_module():
    """Excel modülünü lazy loading ile yükler."""
    global _excel_module, EXCEL_AVAILABLE
    
    if EXCEL_AVAILABLE is None:  # İlk çağrıda kontrol et
        try:
            import toexcel
            _excel_module = toexcel
            EXCEL_AVAILABLE = True
            logging.info("✅ Excel export modülü yüklendi (lazy loading)")
        except ImportError as e:
            logging.warning(f"⚠️ Excel export modülü bulunamadı: {e}")
            EXCEL_AVAILABLE = False
            _excel_module = None
    
    return _excel_module

# Database modülü db.py'de tanımlanmıştır
# Backend modülü tarafından import edilir
# Backend modülü dinamik olarak import edilecek (circular import önlemek için)

# ============================================================================
# EXPORT EDİLECEK TÜMÜ
# ============================================================================
__all__ = [
    # Standart kütüphaneler
    'sys', 'os', 'sqlite3', 'json', 'logging', 'time', 're', 'warnings', 
    'math', 'datetime', 'timedelta', 'threading', 'subprocess', 'shutil',
    'locale', 'calendar', 'platform', 'traceback', 'ctypes', 'ET',
    
    # Windows API
    'win32event', 'win32api', 'winerror', 'WIN32_AVAILABLE',
    
    # Decimal (para hesaplamaları için)
    'Decimal', 'getcontext', 'ROUND_HALF_UP',
    
    # Veri işleme
    'np', 'pd', 'requests',
    
    # Flet UI
    'ft', 'FLET_AVAILABLE',
    
    # QR kod ve görüntü işleme
    'cv2', 'pyzbar', 'fitz', 'ThreadPoolExecutor', 'as_completed',
    'CV2_AVAILABLE', 'PYZBAR_AVAILABLE', 'FITZ_AVAILABLE', 'CONCURRENT_AVAILABLE',
    
    # ReportLab
    'A4', 'letter', 'landscape', 'colors', 'getSampleStyleSheet', 'ParagraphStyle',
    'inch', 'cm', 'SimpleDocTemplate', 'Table', 'TableStyle', 'Paragraph',
    'Spacer', 'PageBreak', 'canvas', 'TA_CENTER', 'TA_LEFT', 'TA_RIGHT',
    'pdfmetrics', 'TTFont', 'REPORTLAB_AVAILABLE',
    
    # Excel
    'xlsxwriter', 'XLSXWRITER_AVAILABLE',
    
    # Proje modülleri - PDF & Excel (Lazy Loading)
    'get_pdf_module', 'get_excel_module', 'PDF_AVAILABLE', 'EXCEL_AVAILABLE',
]
