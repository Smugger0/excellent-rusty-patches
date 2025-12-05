# Frontend.py - Flet UI
# Merkezi imports'tan gerekli kütüphaneleri al
from imports import (
    ft, datetime, time, threading, Decimal, os, sys, 
    win32event, win32api, winerror, ctypes, traceback
)
if getattr(sys, 'frozen', False):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# Windows görev çubuğu simgesi için AppUserModelID ayarla (en başta yapılmalı)
try:
    myappid = 'excellent.dashboard.app.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Backend modüllerini import et
from backend import Backend
from invoices import InvoiceProcessor
# Lazy loading için kaldırıldı: toexcel, topdf, backup

# Tek instance kontrolü
mutex = win32event.CreateMutex(None, False, 'Global\\ExcellentMVPSingleInstance')
last_error = win32api.GetLastError()

if last_error == winerror.ERROR_ALREADY_EXISTS:
    # Uygulama zaten çalışıyor
    ctypes.windll.user32.MessageBoxW(0, "Excellent uygulaması zaten çalışıyor!", "Uyarı", 0x30)
    sys.exit(0)

# Backend instance oluştur
backend_instance = Backend()
invoice_processor = InvoiceProcessor(backend_instance)
# Exporters lazy load edilecek

# Backend callback'lerini ayarla (Flet uyumlu)
def on_backend_data_updated():
    """Backend'den veri güncellendiğinde tüm sayfalardaki bileşenleri günceller"""
    try:
        # Tüm kayıtlı callback'leri çağır
        for page_name, callback in state["update_callbacks"].items():
            if callback is not None:
                try:
                    callback()
                except Exception as ex:
                    pass
    except Exception as e:
        pass

def on_backend_status_updated(message, duration):
    """Backend'den status mesajı geldiğinde çağrılır"""
    pass  # İleride UI'da snackbar/toast gösterilebilir

backend_instance.on_data_updated = on_backend_data_updated
backend_instance.on_status_updated = on_backend_status_updated

# --- RENK PALETİ ---
col_primary = "#6C5DD3"   # Mor
col_secondary = "#FF9F43" # Turuncu
col_success = "#4CD964"   # Yeşil
col_danger = "#FF3B30"    # Kırmızı
col_bg = "#F4F5FA"        # Arka Plan
col_white = "#FFFFFF"     # Beyaz
col_text = "#1A1D1F"      # Koyu Metin
col_text_light = "#9AA1B9" # Gri Metin
col_blue_donut = "#2D9CDB"
col_border = "#E6E8EC"
col_table_header_bg = "#5A5278"
col_selected_row = "#E8F5E9" 
col_input_bg = "#FFFFFF"
col_text_secondary = "#6B7280"  # Gri metin (input label)
col_card = "#FFFFFF"  # Beyaz (input arka plan) 

# Şeffaf Renkler
col_primary_50 = "#806C5DD3"
col_secondary_50 = "#80FF9F43"
transparent_white = "#00FFFFFF"
tooltip_bg = "#CC1A1D1F"

# --- GLOBAL DURUM ---
state = {
    "sidebar_expanded": False,
    "current_currency": "TRY",
    "donuts": [],
    "invoice_type": "income",
    "selected_row": None,
    "current_page": "home",
    "invoice_sort_option": "newest",
    "animation_completed": False,
    "excel_export_path": os.path.join(os.getcwd(), "ExcelReports"),
    "pdf_export_path": os.path.join(os.getcwd(), "PDFExports"),
    # Dinamik güncelleme için referanslar
    "update_callbacks": {
        "home_page": None,
        "donemsel_page": None,
        "invoice_page": None,
        "general_expenses": None
    }
}

# --- BACKEND YARDIMCI FONKSİYONLAR ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_exchange_rates():
    """Backend'den güncel döviz kurlarını al"""
    return backend_instance.exchange_rates

def convert_currency(amount, from_currency, to_currency):
    """Para birimi dönüşümü yap"""
    return backend_instance.convert_currency(amount, from_currency, to_currency)

def process_invoice(invoice_data):
    """Fatura verilerini işle ve KDV hesapla"""
    return invoice_processor.process_invoice_data(invoice_data)

def format_currency(amount, currency="TRY", compact=False):
    """Para birimi formatla - compact=True ise K/M formatında göster"""
    symbol = "₺"
    if currency == "USD":
        symbol = "$"
    elif currency == "EUR":
        symbol = "€"
        
    if compact:
        # Kompakt format (K/M ile)
        if amount >= 1000000:
            return f"{symbol} {amount/1000000:.1f}M"
        elif amount >= 1000:
            return f"{symbol} {amount/1000:.1f}K"
        else:
            return f"{symbol} {amount:.0f}"
    
    # Normal format
    if currency == "TRY":
        return f"{amount:,.2f} ₺"
    elif currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    return f"{amount:,.2f} {currency}"

def get_exchange_rate_display():
    """Kur bilgilerini string olarak döndür"""
    rates = get_exchange_rates()
    usd_rate = rates.get('USD', 0)
    eur_rate = rates.get('EUR', 0)
    
    if usd_rate > 0 and eur_rate > 0:
        usd_tl = 1 / usd_rate
        eur_tl = 1 / eur_rate
        return f"1 USD = {usd_tl:.2f} TL | 1 EUR = {eur_tl:.2f} TL"
    return "Kur bilgisi yükleniyor..."

# --- YARDIMCI BİLEŞENLER ---

class ScaleButton(ft.Container):
    def __init__(self, icon, color, tooltip_text, width=50, height=45, on_click=None):
        super().__init__()
        self.bgcolor = color
        self.border_radius = 8
        self.width = width
        self.height = height
        self.tooltip = tooltip_text
        self.alignment = ft.alignment.center
        self.animate_scale = ft.Animation(200, ft.AnimationCurve.EASE_OUT_BACK)
        self.animate = ft.Animation(200, "easeOut")
        self.ink = False 
        if on_click:
            self.on_click = on_click
        
        hex_code = color.lstrip("#")
        shadow_color = f"#80{hex_code}"
        self.shadow = ft.BoxShadow(blur_radius=5, color=shadow_color, offset=ft.Offset(0, 3))
        self.content = ft.Icon(icon, color=col_white, size=22)
        self.on_hover = self.hover_effect
        self.scale = 1.0 

    def hover_effect(self, e):
        if e.data == "true":
            self.scale = 1.15
            self.shadow.blur_radius = 15
            self.shadow.offset = ft.Offset(0, 6)
        else:
            self.scale = 1.0 
            self.shadow.blur_radius = 5
            self.shadow.offset = ft.Offset(0, 3)
        self.update()

class AestheticButton(ft.Container):
    def __init__(self, text, icon, color, width=130, on_click=None):
        super().__init__()
        self.bgcolor = color
        self.border_radius = 8
        self.padding = ft.padding.symmetric(horizontal=15, vertical=10)
        self.width = width
        self.animate_scale = ft.Animation(150, ft.AnimationCurve.EASE_OUT)
        self.animate = ft.Animation(200, "easeOut") 
        self.ink = False 
        if on_click:
            self.on_click = on_click
        
        hex_code = color.lstrip("#")
        self.shadow = ft.BoxShadow(blur_radius=8, color=f"#4D{hex_code}", offset=ft.Offset(0, 3))
        
        self.content = ft.Row([
            ft.Icon(icon, color=col_white, size=18),
            ft.Text(text, color=col_white, weight="bold", size=12)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        self.on_hover = self.hover_effect
        self.scale = 1.0
        
    def hover_effect(self, e):
        if e.data == "true":
            self.scale = 1.08
            self.shadow.offset = ft.Offset(0, 5)
            self.shadow.blur_radius = 12
        else:
            self.scale = 1.0
            self.shadow.offset = ft.Offset(0, 3)
            self.shadow.blur_radius = 8
        self.update()

def format_date_input(date_str):
    """
    Esnek tarih girişini standart formata (gg.aa.yyyy) çevirir.
    Desteklenen formatlar:
    - 121225 -> 12.12.2025 (ggaayy)
    - 12122025 -> 12.12.2025 (ggaayyyy)
    - 12.12.2025, 12/12/2025, 12-12-2025 (ayırıcılı formatlar)
    """
    if not date_str or not isinstance(date_str, str):
        return date_str
    
    date_str = date_str.strip()
    
    # Sadece rakamları al
    cleaned = ''.join(c for c in date_str if c.isdigit())
    
    # 6 karakterlik format: ggaayy -> gg.aa.20yy
    if len(cleaned) == 6:
        gun = cleaned[:2]
        ay = cleaned[2:4]
        yil_short = cleaned[4:6]
        yil = "20" + yil_short
        try:
            # Geçerli tarih mi kontrol et
            datetime(int(yil), int(ay), int(gun))
            return f"{gun}.{ay}.{yil}"
        except ValueError:
            return date_str
    
    # 8 karakterlik format: ggaayyyy -> gg.aa.yyyy
    elif len(cleaned) == 8:
        # İlk 4 karakter yıl gibi görünüyorsa (2000-2099 arası)
        if cleaned[:4].startswith('20'):
            # yyyyaagg formatı
            yil = cleaned[:4]
            ay = cleaned[4:6]
            gun = cleaned[6:8]
        else:
            # ggaayyyy formatı
            gun = cleaned[:2]
            ay = cleaned[2:4]
            yil = cleaned[4:8]
        try:
            datetime(int(yil), int(ay), int(gun))
            return f"{gun}.{ay}.{yil}"
        except ValueError:
            return date_str
    
    # Zaten formatlanmış veya ayırıcı içeren tarihler
    for sep in ['.', '/', '-']:
        if sep in date_str:
            parts = date_str.split(sep)
            if len(parts) == 3:
                try:
                    gun, ay, yil = parts
                    # 2 basamaklı yıl ise 20xx'e çevir
                    if len(yil) == 2:
                        yil = "20" + yil
                    datetime(int(yil), int(ay), int(gun))
                    return f"{gun.zfill(2)}.{ay.zfill(2)}.{yil}"
                except (ValueError, TypeError):
                    pass
    
    return date_str

def create_vertical_input(label, hint, width=None, expand=True, is_dropdown=False, dropdown_options=None):
    if is_dropdown:
        input_control = ft.Dropdown(
            options=[ft.dropdown.Option(opt) for opt in dropdown_options] if dropdown_options else [],
            text_size=13, color=col_text, border_color="transparent", bgcolor="transparent",
            content_padding=ft.padding.only(left=10, bottom=5), hint_text=hint,
            hint_style=ft.TextStyle(color="#D0D0D0", size=12),
        )
    else:
        input_control = ft.TextField(
            hint_text=hint, hint_style=ft.TextStyle(color="#D0D0D0", size=12),
            text_size=13, color=col_text, border_color="transparent", bgcolor="transparent",
            content_padding=ft.padding.only(left=10, bottom=12), 
        )

    return ft.Column([
        ft.Text(label, size=12, color=col_text_light, weight="bold"),
        ft.Container(
            content=input_control, bgcolor=col_white, border=ft.border.all(1, col_border),
            border_radius=8, height=38, width=width
        )
    ], spacing=3, expand=expand)

# --- FATURA VERİSİ ---
# Frontend sample invoice data removed to avoid embedded backend/test scaffolding.
# Integrate a backend data source and supply rows dynamically when ready.

# ============================================================================
# FATURA TABLOSU OLUŞTURMA (Invoice Table Creation)
# ============================================================================
def create_invoice_table_content(sort_option="newest", invoice_type="income", on_select_changed=None, invoice_list=None):
    """Backend'den fatura verilerini çekerek DataTable oluşturur."""
    def header(t): return ft.DataColumn(ft.Text(t, weight="bold", color=col_white, size=12))
    
    # Backend'den faturaları çek (eğer liste verilmediyse)
    rows = []
    invoices = invoice_list  # Liste cache'i için
    
    try:
        if invoices is None:
            # invoice_type'a göre doğru veritabanını belirle
            db_type = 'outgoing' if invoice_type == 'income' else 'incoming'
            
            # Sıralama seçeneğine göre order_by parametresi
            if sort_option == "newest":
                order_by = "id DESC"
            elif sort_option == "date_desc":
                # SQLite date format conversion for sorting: DD.MM.YYYY -> YYYYMMDD
                order_by = "substr(tarih, 7, 4) || substr(tarih, 4, 2) || substr(tarih, 1, 2) DESC"
            elif sort_option == "date_asc":
                # SQLite date format conversion for sorting: DD.MM.YYYY -> YYYYMMDD
                order_by = "substr(tarih, 7, 4) || substr(tarih, 4, 2) || substr(tarih, 1, 2) ASC"
            else:
                order_by = "id DESC"
            
            # Backend'den faturaları al
            invoices = backend_instance.handle_invoice_operation(
                operation='get',
                invoice_type=db_type,
                limit=100,
                offset=0,
                order_by=order_by
            )
            
        
        # DataTable satırlarını oluştur
        if invoices:
            for inv in invoices:
                def cell(text, color=col_text): 
                    return ft.DataCell(ft.Text(str(text), size=12, color=color))
                
                # Checkbox hücresi - manuel seçim için
                checkbox = ft.Checkbox(value=False, on_change=on_select_changed if on_select_changed else None)
                checkbox_cell = ft.DataCell(checkbox)
                
                # Kur bilgilerini al (None kontrolü yap)
                usd_rate = inv.get('usd_rate')
                eur_rate = inv.get('eur_rate')
                
                usd_rate_val = float(usd_rate) if usd_rate is not None else 0.0
                eur_rate_val = float(eur_rate) if eur_rate is not None else 0.0
                
                # Tutar görüntüleme - kur bilgisi ile
                tutar_usd = float(inv.get('toplam_tutar_usd', 0) or 0)
                tutar_eur = float(inv.get('toplam_tutar_eur', 0) or 0)
                
                usd_display = f"{tutar_usd:,.2f}"
                eur_display = f"{tutar_eur:,.2f}"
                
                # KDV hesaplama
                kdv_tutari = float(inv.get('kdv_tutari', 0))
                kdv_yuzdesi = float(inv.get('kdv_yuzdesi', 0))
                kdv_text = f"{kdv_tutari:,.2f} (%{kdv_yuzdesi:.0f})"

                def create_currency_cell(amount_text, rate_val):
                    if rate_val > 0:
                        return ft.DataCell(
                            ft.Column([
                                ft.Text(amount_text, size=12, color=col_text, weight="bold"),
                                ft.Text(f"Kur: {rate_val:.2f}", size=10, color=col_text_light)
                            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
                        )
                    return ft.DataCell(ft.Text(amount_text, size=12, color=col_text))

                # Her satıra invoice verilerini data olarak ekle
                row = ft.DataRow(
                    data=inv,  # Tüm invoice verisini data olarak sakla
                    cells=[
                        checkbox_cell,  # İlk hücre checkbox
                        cell(inv.get('fatura_no', '')),
                        cell(inv.get('tarih', '')),
                        cell(inv.get('firma', '')),
                        cell(inv.get('malzeme', '')),
                        cell(inv.get('miktar', '')),
                        ft.DataCell(ft.Text(f"{float(inv.get('toplam_tutar_tl', 0)):,.2f}", size=12, color=col_text, weight="bold")),
                        create_currency_cell(usd_display, usd_rate_val),
                        create_currency_cell(eur_display, eur_rate_val),
                        cell(kdv_text)
                    ]
                )
                rows.append(row)
    except Exception as e:
        pass

    return ft.DataTable(
        columns=[header("SEÇ"), header("FATURA NO"), header("TARİH"), header("FİRMA"), header("MALZEME"), header("MİKTAR"), ft.DataColumn(ft.Text("TUTAR (TL)", weight="bold", color=col_white, size=12), numeric=True), ft.DataColumn(ft.Text("TUTAR (USD)", weight="bold", color=col_white, size=12), numeric=True), ft.DataColumn(ft.Text("TUTAR (EUR)", weight="bold", color=col_white, size=12), numeric=True), header("KDV (Tutar/%)")],
        rows=rows, heading_row_color=col_table_header_bg, heading_row_height=48, data_row_max_height=60,
        vertical_lines=ft.border.BorderSide(0, "transparent"), horizontal_lines=ft.border.BorderSide(1, "#F0F0F0"),
        column_spacing=25, width=float("inf")
    )

# ============================================================================
# DÖNEMSEL TABLO OLUŞTURMA (Periodic Table Creation)
# ============================================================================
def create_donemsel_table(year=None, tax_fields=None, on_tax_change=None):
    """Dönemsel gelir/gider tablosu - Gerçek verilerle dolu"""
    if year is None:
        year = datetime.now().year
    
    months = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
    quarter_colors = [col_danger, col_success, col_secondary, col_blue_donut]
    def header(t): return ft.DataColumn(ft.Text(t, weight="bold", color=col_white, size=12))
    def cell(t): return ft.DataCell(ft.Text(t, color="#333333", size=12))
    
    # Backend'den verileri çek
    try:
        income_invoices = backend_instance.handle_invoice_operation('get', 'outgoing') or []
        expense_invoices = backend_instance.handle_invoice_operation('get', 'incoming') or []
        
        # Genel giderleri çek
        general_expenses = backend_instance.db.get_yearly_expenses(year) or {}
        
        # Kurumlar vergisi tutarlarını çek (aylık)
        corporate_tax_data = backend_instance.db.get_corporate_tax(year) or {}
        
        # Aylık toplamları hesapla
        monthly_income = [0.0] * 12
        monthly_expense = [0.0] * 12
        monthly_general = [0.0] * 12
        monthly_corporate_tax = [0.0] * 12  # Aylık kurumlar vergisi tutarları
        monthly_income_kdv = [0.0] * 12  # Gelir faturalarındaki KDV
        monthly_expense_kdv = [0.0] * 12  # Gider faturalarındaki KDV
        
        # Gelir faturalarını işle
        for invoice in income_invoices:
            tarih = invoice.get('tarih', '')
            if not tarih: continue
            
            parts = tarih.split('.')
            if len(parts) != 3: continue
            
            try:
                month = int(parts[1])
                invoice_year = int(parts[2])
                
                if invoice_year == year:
                    amount_tl = float(invoice.get('toplam_tutar_tl', 0))
                    kdv_tl = float(invoice.get('kdv_tutari', 0))
                    monthly_income[month-1] += amount_tl
                    monthly_income_kdv[month-1] += kdv_tl
            except (ValueError, IndexError):
                continue
        
        # Gider faturalarını işle
        for invoice in expense_invoices:
            tarih = invoice.get('tarih', '')
            if not tarih: continue
            
            parts = tarih.split('.')
            if len(parts) != 3: continue
            
            try:
                month = int(parts[1])
                invoice_year = int(parts[2])
                
                if invoice_year == year:
                    amount_tl = float(invoice.get('toplam_tutar_tl', 0))
                    kdv_tl = float(invoice.get('kdv_tutari', 0))
                    monthly_expense[month-1] += amount_tl
                    monthly_expense_kdv[month-1] += kdv_tl
            except (ValueError, IndexError):
                continue
        
        # Genel giderleri ay ay ekle
        month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
        for month_idx in range(12):
            month_key = month_keys[month_idx]
            if month_key in general_expenses:
                monthly_general[month_idx] = float(general_expenses[month_key] or 0)
            if month_key in corporate_tax_data:
                monthly_corporate_tax[month_idx] = float(corporate_tax_data[month_key] or 0)
        
        # --- TABLO OLUŞTURMA (YENİ TASARIM - 3 AYLIK GRUPLAMA) ---
        
        # Sütun Genişlikleri
        w_donem = 90
        w_gelir = 140
        w_gider = 140
        w_kdv_farki = 120
        w_kurumlar = 140
        w_odenecek = 160
        
        # Header
        header_row = ft.Container(
            bgcolor=col_table_header_bg,
            padding=ft.padding.symmetric(vertical=12, horizontal=10),
            border_radius=ft.border_radius.only(top_left=10, top_right=10),
            content=ft.Row([
                ft.Container(width=w_donem, content=ft.Text("DÖNEM", weight="bold", color=col_white, size=11)),
                ft.Container(width=w_gelir, content=ft.Text("GELİR (Kesilen)", weight="bold", color=col_white, size=11)),
                ft.Container(width=w_gider, content=ft.Text("GİDER (Gelen + Genel)", weight="bold", color=col_white, size=11)),
                ft.Container(width=w_kdv_farki, content=ft.Text("KDV FARKI", weight="bold", color=col_white, size=11)),
                ft.Container(width=w_kurumlar, content=ft.Text("KURUMLAR VERGİSİ", weight="bold", color=col_white, size=11)),
                ft.Container(expand=True, content=ft.Text("ÖDENECEK VERGİ (3 Aylık)", weight="bold", color=col_white, size=11)),
            ], spacing=8)
        )
        
        quarter_blocks = []
        
        total_income = 0.0
        total_expense = 0.0
        total_general = 0.0
        total_income_kdv = 0.0
        total_expense_kdv = 0.0
        total_kurumlar_vergisi = 0.0
        
        # 4 Çeyrek Döngüsü
        for q in range(4):
            start_month = q * 3
            quarter_kurumlar_total = 0.0  # Çeyrek Kurumlar Vergisi toplamı
            
            left_rows = []
            
            # Çeyrek içindeki 3 ay
            for i in range(start_month, start_month + 3):
                m = months[i]
                current_color = quarter_colors[q]
                
                income = monthly_income[i]
                expense = monthly_expense[i]
                general = monthly_general[i]
                income_kdv = monthly_income_kdv[i]
                expense_kdv = monthly_expense_kdv[i]
                
                tax_percentage = monthly_corporate_tax[i]
                total_month_expense = expense + general
                
                # Kurumlar vergisi: Gelir - Gider üzerinden hesaplanır
                # Negatif değerler de gösterilir (zarar durumu)
                taxable_base = income - total_month_expense
                kurumlar_vergisi = (taxable_base * tax_percentage / 100) if tax_percentage > 0 else 0
                
                # Toplamları güncelle
                total_income += income
                total_expense += total_month_expense
                total_general += general
                total_income_kdv += income_kdv
                total_expense_kdv += expense_kdv
                total_kurumlar_vergisi += kurumlar_vergisi
                
                # Çeyrek içindeki kurumlar vergisi toplamını güncelle
                quarter_kurumlar_total += kurumlar_vergisi
                
                # Sol taraf satırı (Ay detayları)
                month_cell = ft.Container(
                    width=w_donem,
                    content=ft.Text(m, color=current_color, weight="bold", size=12), 
                    padding=ft.padding.only(left=8), 
                    border=ft.border.only(left=ft.border.BorderSide(3, current_color)), 
                    alignment=ft.alignment.center_left
                )
                
                # Gelir bölümü: Tutar ve altında KDV
                gelir_content = ft.Column([
                    ft.Text(f"{income:,.2f} TL", size=12, color="#333333", weight="bold"),
                    ft.Text(f"KDV: {income_kdv:,.2f} TL", size=9, color="#9AA1B9")
                ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.START)
                
                # Gider bölümü: Tutar ve altında KDV
                gider_content = ft.Column([
                    ft.Text(f"{total_month_expense:,.2f} TL", size=12, color="#333333", weight="bold"),
                    ft.Text(f"KDV: {expense_kdv:,.2f} TL", size=9, color="#9AA1B9")
                ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.START)
                
                # KDV Farkı hesapla (Gelir KDV - Gider KDV)
                kdv_farki = income_kdv - expense_kdv
                kdv_farki_color = "#28a745" if kdv_farki >= 0 else "#dc3545"
                kdv_farki_content = ft.Text(f"{kdv_farki:,.2f} TL", size=12, color=kdv_farki_color, weight="bold")
                
                # Kurumlar vergisi bölümü: Sadece TextField (yüzde girişi)
                if tax_fields and i < len(tax_fields):
                    kurumlar_content = tax_fields[i]
                else:
                    kurumlar_content = ft.Text(f"%{kurumlar_yuzde:.0f}" if kurumlar_yuzde > 0 else "-", 
                                              size=12, color="#333333")
                
                row = ft.Container(
                    height=48,  # Satır yüksekliği normale döndü
                    padding=ft.padding.symmetric(vertical=5),
                    border=ft.border.only(bottom=ft.border.BorderSide(1, "#F0F0F0")) if i % 3 != 2 else None,
                    content=ft.Row([
                        month_cell,
                        ft.Container(width=w_gelir, content=gelir_content),
                        ft.Container(width=w_gider, content=gider_content),
                        ft.Container(width=w_kdv_farki, content=kdv_farki_content, alignment=ft.alignment.center),
                        ft.Container(width=w_kurumlar, content=kurumlar_content, alignment=ft.alignment.center),
                    ], spacing=8, alignment=ft.MainAxisAlignment.START)
                )
                left_rows.append(row)
            
            # Sol Kolon (3 Satır)
            left_column = ft.Column(left_rows, spacing=0)
            
            # Sağ Kolon (Tek Büyük Hücre) - Kurumlar Vergisi toplamı gösterilir
            quarter_color = "#28a745" if quarter_kurumlar_total >= 0 else "#dc3545"
            right_cell = ft.Container(
                expand=True,
                height=144, # 3 * 48 (satır yüksekliği güncellendi)
                content=ft.Column([
                    ft.Text("ÇEYREK TOPLAM", size=10, color="#999999", weight="bold"),
                    ft.Text(f"{quarter_kurumlar_total:,.2f} TL", size=16, weight="bold", color=quarter_color)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                border=ft.border.only(left=ft.border.BorderSide(1, "#E0E0E0")),
                bgcolor="#FAFAFA"
            )
            
            # Çeyrek Bloğu
            quarter_block = ft.Container(
                content=ft.Row([left_column, right_cell], spacing=10),
                border=ft.border.all(1, "#E0E0E0"),
                border_radius=8,
                margin=ft.margin.only(bottom=10),
                bgcolor=col_white
            )
            quarter_blocks.append(quarter_block)
        
        return ft.Column([header_row] + quarter_blocks)
        
    except Exception as e:
        return ft.Text("Veri yüklenirken hata oluştu.")

# ============================================================================
# GENEL GİDERLER TABLOSU (General Expenses Grid)
# ============================================================================
def create_grid_expenses(page):
    months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
    
    # Yıl seçenekleri
    current_year = datetime.now().year
    year_options = [ft.dropdown.Option(str(y)) for y in range(current_year - 2, current_year + 2)]
    
    year_dropdown = ft.Dropdown(
        options=year_options,
        value=str(current_year),
        text_size=12,
        content_padding=10,
        width=95,
        bgcolor=col_white,
        border_color=col_border,
        border_radius=8
    )

    # Para birimi seçenekleri
    currency_options = [ft.dropdown.Option("TL"), ft.dropdown.Option("USD"), ft.dropdown.Option("EUR")]
    currency_dropdown = ft.Dropdown(
        options=currency_options,
        value="TL",
        text_size=12,
        content_padding=10,
        width=80,
        bgcolor=col_white,
        border_color=col_border,
        border_radius=8,
        hint_text="Birim"
    )
    
    # TextField'ları sakla
    expense_fields = {}
    expense_cards = []
    
    for i, m in enumerate(months):
        text_field = ft.TextField(
            value="0", 
            text_size=14, 
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD), 
            color=col_text, 
            text_align=ft.TextAlign.CENTER, 
            border_color="#E0E0E0", 
            focused_border_color=col_primary, 
            height=35, 
            content_padding=5, 
            bgcolor="#FAFAFA", 
            prefix_text="₺ "
        )
        expense_fields[month_keys[i]] = text_field
        
        card = ft.Container(
            bgcolor=col_white, 
            border_radius=12, 
            padding=10, 
            width=140, 
            height=85, 
            shadow=ft.BoxShadow(blur_radius=5, color="#08000000", offset=ft.Offset(0,3)), 
            border=ft.border.all(1, "#F0F0F0"), 
            content=ft.Column([
                ft.Container(content=ft.Text(m, size=13, weight="bold", color=col_primary), alignment=ft.alignment.center), 
                ft.Divider(height=5, color="transparent"), 
                text_field
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
        )
        expense_cards.append(card)
    
    # Seçili yılın verilerini yükle
    def load_year_data(year=None):
        if year is None:
            year = int(year_dropdown.value)
        yearly_data = backend_instance.db.get_yearly_expenses(year)
        
        current_curr = currency_dropdown.value
        symbol = "₺ " if current_curr == "TL" else ("$ " if current_curr == "USD" else "€ ")
        
        if yearly_data:
            for month_key in month_keys:
                amount_tl = yearly_data.get(month_key, 0)
                if amount_tl:
                    if current_curr == "TL":
                        val = amount_tl
                    else:
                        # TL'den seçili para birimine çevir (Görüntüleme için)
                        val = backend_instance.convert_currency(amount_tl, "TRY", current_curr)
                    
                    expense_fields[month_key].value = f"{val:.2f}"
                else:
                    expense_fields[month_key].value = "0"
        else:
            # Veri yoksa sıfırla
            for month_key in month_keys:
                expense_fields[month_key].value = "0"
        
        # Prefix güncelle
        for field in expense_fields.values():
            field.prefix_text = symbol
            if field.page:
                field.update()
            
        if page:
            try:
                page.update()
            except:
                pass
    
    # Yıl değiştiğinde verileri yükle
    def on_year_change(e):
        load_year_data(int(e.control.value))
    
    year_dropdown.on_change = on_year_change

    # Para birimi değiştiğinde verileri yükle
    def on_currency_change(e):
        load_year_data()
    
    currency_dropdown.on_change = on_currency_change
    
    # Kaydet butonu fonksiyonu
    def save_expenses(e):
        """Genel giderleri database'e kaydet"""
        try:
            selected_year = int(year_dropdown.value)
            current_curr = currency_dropdown.value
            monthly_data = {}
            
            # Tüm ayların değerlerini topla
            for month_key in month_keys:
                value = expense_fields[month_key].value
                try:
                    amount = float(value) if value else 0
                    
                    if current_curr != "TL":
                        # Seçili para biriminden TL'ye çevir (Kayıt için)
                        # Bu işlem o anki kur ile yapılır ve sabitlenir (Historik)
                        amount_tl = backend_instance.convert_currency(amount, current_curr, "TRY")
                        monthly_data[month_key] = amount_tl
                    else:
                        monthly_data[month_key] = amount
                        
                except ValueError:
                    monthly_data[month_key] = 0
            
            # Database'e kaydet
            result = backend_instance.db.add_or_update_yearly_expenses(selected_year, monthly_data)
            
            if result:
                # Veri güncelleme callback'ini çağır
                if backend_instance.on_data_updated:
                    backend_instance.on_data_updated()
                
                msg = f"✅ {selected_year} yılı genel giderleri kaydedildi!"
                if current_curr != "TL":
                    msg += f" ({current_curr} -> TL çevrildi)"
                
                page.snack_bar = ft.SnackBar(content=ft.Text(msg, color=col_white), bgcolor=col_success)
                page.snack_bar.open = True
                page.update()
                
                # Kaydettikten sonra TL moduna dönmek mantıklı olabilir, ama kullanıcı aynı birimde devam etmek isteyebilir.
                # Verileri yeniden yükleyerek (TL'den çevirerek) tutarlılığı gösterelim
                load_year_data()
                
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text("❌ Kaydetme işlemi başarısız!", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()
                
        except Exception as ex:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Hata: {str(ex)}", color=col_white), bgcolor=col_danger)
            page.snack_bar.open = True
            page.update()
    
    def export_general_expenses_excel(e):
        """Genel giderleri Excel'e aktar - Aylık format"""
        try:
            expenses = backend_instance.handle_genel_gider_operation('get', limit=1000)
            
            if not expenses:
                page.snack_bar = ft.SnackBar(content=ft.Text("❌ Dışa aktarılacak genel gider bulunamadı!", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()
                return
            
            def on_save_result(e: ft.FilePickerResultEvent):
                if e.path:
                    file_path = e.path
                    selected_year = int(year_dropdown.value)
                    
                    # Aylık formatta Excel'e aktar
                    from toexcel import export_monthly_general_expenses_to_excel
                    success = export_monthly_general_expenses_to_excel(expenses, year=selected_year, file_path=file_path)
                    
                    if success:
                        def close_success_dlg(e):
                            success_dlg.open = False
                            page.update()

                        success_dlg = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Başarılı"),
                            content=ft.Text(f"Dosya başarıyla kaydedildi:\n{file_path}"),
                            actions=[
                                ft.ElevatedButton("Tamam", on_click=close_success_dlg, bgcolor=col_primary, color=col_white),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )
                        page.overlay.append(success_dlg)
                        success_dlg.open = True
                        page.update()
                else:
                    page.snack_bar = ft.SnackBar(content=ft.Text("❌ Excel aktarımı başarısız!", color=col_white), bgcolor=col_danger)
                    page.snack_bar.open = True
                    page.update()

            # Dosya yolu oluştur
            selected_year = int(year_dropdown.value)
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename = f"GenelGiderler_{selected_year}_{timestamp}.xlsx"
            
            save_file_picker = ft.FilePicker(on_result=on_save_result)
            page.overlay.append(save_file_picker)
            page.update()
            save_file_picker.save_file(dialog_title="Excel Dosyasını Kaydet", file_name=filename, allowed_extensions=["xlsx"])
                
        except Exception as ex:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Excel hatası: {str(ex)}", color=col_white), bgcolor=col_danger)
            page.snack_bar.open = True
            page.update()
    
    def export_general_expenses_pdf(e):
        """Genel giderleri PDF'e aktar - Aylık format"""
        try:
            expenses = backend_instance.handle_genel_gider_operation('get', limit=1000)
            
            if not expenses:
                page.snack_bar = ft.SnackBar(content=ft.Text("❌ Dışa aktarılacak genel gider bulunamadı!", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()
                return
            
            def on_save_result(e: ft.FilePickerResultEvent):
                if e.path:
                    file_path = e.path
                    selected_year = int(year_dropdown.value)
                    
                    # Aylık formatta PDF'e aktar
                    from topdf import export_monthly_general_expenses_to_pdf
                    success = export_monthly_general_expenses_to_pdf(expenses, year=selected_year, file_path=file_path)
                    
                    if success:
                        def close_success_dlg(e):
                            success_dlg.open = False
                            page.update()

                        success_dlg = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Başarılı"),
                            content=ft.Text(f"Dosya başarıyla kaydedildi:\n{file_path}"),
                            actions=[
                                ft.ElevatedButton("Tamam", on_click=close_success_dlg, bgcolor=col_primary, color=col_white),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )
                        page.overlay.append(success_dlg)
                        success_dlg.open = True
                        page.update()
                    else:
                        page.snack_bar = ft.SnackBar(content=ft.Text("❌ PDF aktarımı başarısız!", color=col_white), bgcolor=col_danger)
                        page.snack_bar.open = True
                        page.update()

            # Dosya yolu oluştur
            selected_year = int(year_dropdown.value)
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename = f"GenelGiderler_{selected_year}_{timestamp}.pdf"
            
            save_file_picker = ft.FilePicker(on_result=on_save_result)
            page.overlay.append(save_file_picker)
            page.update()
            save_file_picker.save_file(dialog_title="PDF Dosyasını Kaydet", file_name=filename, allowed_extensions=["pdf"])
                
        except Exception as ex:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ PDF hatası: {str(ex)}", color=col_white), bgcolor=col_danger)
            page.snack_bar.open = True
            page.update()
    
    # Sayfa yüklendiğinde mevcut verileri yükle
    load_year_data()
    
    # Dinamik güncelleme için callback oluştur
    def refresh_general_expenses():
        """Genel giderleri yeniden yükle"""
        try:
            load_year_data()
        except:
            pass
    
    state["update_callbacks"]["general_expenses"] = refresh_general_expenses
    
    # Butonları event handler'larla oluştur
    btn_save = ScaleButton("save", "#4CD964", "Kaydet", width=40, height=40)
    btn_save.on_click = save_expenses
    
    btn_excel = ScaleButton("table_view", "#217346", "Excel İndir", width=40, height=40)
    btn_excel.on_click = export_general_expenses_excel
    
    btn_pdf = ScaleButton("picture_as_pdf", "#D32F2F", "PDF İndir", width=40, height=40)
    btn_pdf.on_click = export_general_expenses_pdf
    
    expense_buttons = ft.Container(padding=ft.padding.only(right=40), content=ft.Row([ft.Container(height=38, content=year_dropdown), ft.Container(height=38, content=currency_dropdown), btn_save, btn_excel, btn_pdf], spacing=5))
    
    return ft.Container(padding=ft.padding.only(top=15), content=ft.Column([ft.Row([ft.Row([ft.Icon("calendar_month", color=col_secondary, size=20), ft.Text("Yıllık Genel Giderler", size=16, weight="bold", color=col_text)], spacing=8), expense_buttons], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(height=10), ft.Row(controls=expense_cards, wrap=True, spacing=15, run_spacing=15, alignment=ft.MainAxisAlignment.CENTER)]))

class AnimatedDonut(ft.Stack):
    def __init__(self, value, total, color, text_value):
        super().__init__()
        self.width = 110
        self.height = 110
        self.alignment = ft.alignment.center
        hex_code = color.lstrip("#")
        shadow_color = f"#66{hex_code}"
        remainder_color = f"#1A{hex_code}"
        self.chart_rotate = ft.Rotate(-3.14, alignment=ft.alignment.center)
        self.chart = ft.PieChart(
            sections=[
                ft.PieChartSection(value=value, color=color, radius=14, title=""),
                ft.PieChartSection(value=total - value, color=remainder_color, radius=14, title=""),
            ],
            center_space_radius=38, sections_space=0, start_degree_offset=-90
        )
        self.chart_container = ft.Container(
            content=self.chart, width=110, height=110, bgcolor=col_white, shape=ft.BoxShape.CIRCLE,
            shadow=ft.BoxShadow(blur_radius=20, spread_radius=2, color=shadow_color, offset=ft.Offset(0, 8)),
            rotate=self.chart_rotate, opacity=0, animate_opacity=ft.Animation(800, "easeIn"), animate_rotation=ft.Animation(1500, "easeOutBack")
        )
        self.text_container = ft.Container(content=ft.Text(text_value, size=15, weight="bold", color=col_text, text_align="center"), alignment=ft.alignment.center, rotate=ft.Rotate(0, alignment=ft.alignment.center))
        self.controls = [self.chart_container, self.text_container]
        state["donuts"].append(self)

    def start_animation(self):
        try:
            # Sayfa yüklü değilse veya obje sayfada değilse çalışma
            if not self.chart_container.page: return

            if state["animation_completed"]:
                self.chart_container.opacity = 1
                self.chart_container.rotate.angle = 0
                self.chart_container.animate_opacity = None 
                self.chart_container.animate_rotation = None
                self.chart_container.update()
            else:
                self.chart_container.rotate.angle = 0
                self.chart_container.opacity = 1
                self.chart_container.update()
        except: pass
    
    def update_value(self, new_value, new_total, new_text):
        """Donut değerlerini günceller"""
        try:
            # Chart sections'ı güncelle
            self.chart.sections[0].value = new_value
            self.chart.sections[1].value = max(0, new_total - new_value)
            
            # Text'i güncelle
            self.text_container.content.value = new_text
            
            if not self.chart_container.page: return
            
            # Güncellemeyi uygula
            self.chart_container.update()
            self.text_container.update()
        except Exception as e:
            pass

class DonutStatCard(ft.Container):
    def __init__(self, title, icon, color, trend_text, donut_val, donut_total, display_text):
        super().__init__()
        self.bgcolor = col_white
        self.border_radius = 24
        self.padding = ft.padding.all(20)
        self.expand = 1
        self.shadow = ft.BoxShadow(blur_radius=15, color="#08000000", offset=ft.Offset(0, 5))
        self.donut = AnimatedDonut(value=donut_val, total=donut_total, color=color, text_value=display_text)
        self.content = ft.Row([
            ft.Column([
                ft.Container(content=ft.Icon(icon, color=col_white, size=24), bgcolor=color, border_radius=14, width=48, height=48, alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=10, color=f"#4D{color.lstrip('#')}", offset=ft.Offset(0,4))),
                ft.Container(height=5),
                ft.Text(title, size=14, color=col_text_light, weight="w600"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
            ft.Container(content=self.donut, alignment=ft.alignment.center_right)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

class TransactionRow(ft.Container):
    def __init__(self, title, date, amount, is_income=True, is_updated=False, is_deleted=False, invoice_date=None):
        super().__init__()
        self.padding = ft.padding.symmetric(vertical=10)
        self.border = ft.border.only(bottom=ft.border.BorderSide(1, "#F0F0F0"))
        
        if is_deleted:
            color = "#9E9E9E"  # Gri
            icon = "delete_outline"
            sign = ""
            bg_color = "#EEEEEE"
        else:
            color = col_success if is_income else col_danger
            icon = "arrow_upward" if is_income else "arrow_downward"
            sign = "+" if is_income else "-"
            bg_color = f"{color}20"
        
        # Güncellenmiş faturalar için özel gösterge
        status_indicator = None
        if is_updated and not is_deleted:
            status_indicator = ft.Container(
                width=8,
                height=8,
                bgcolor="#FF9F43",  # Turuncu nokta
                border_radius=4,
                tooltip="Güncellenmiş fatura"
            )
        elif is_deleted:
            status_indicator = ft.Container(
                width=8,
                height=8,
                bgcolor="#9E9E9E",  # Gri nokta
                border_radius=4,
                tooltip="Silinmiş fatura"
            )
        
        # İkon container'ı
        icon_container = ft.Container(
            width=40, 
            height=40, 
            bgcolor=bg_color, 
            border_radius=10, 
            content=ft.Icon(icon, color=color, size=20), 
            alignment=ft.alignment.center
        )
        
        # Güncellenmiş ise border ekle
        if is_updated and not is_deleted:
            icon_container.border = ft.border.all(2, "#FF9F43")
        
        # Row içeriği
        row_controls = [icon_container]
        
        # Tarih formatı: işlem tarihi (Fat.Tar. fatura_tarihi)
        date_text = date
        if invoice_date and invoice_date != date:
            date_text = f"{date} (Fat.Tar. {invoice_date})"
        
        # Tarih için Row - normal kısım ve parantez kısmı farklı fontlarla
        if invoice_date and invoice_date != date:
            date_row = ft.Row([
                ft.Text(date, size=12, color=col_text_light),
                ft.Text(f" (Fat.Tar. {invoice_date})", size=10, color=col_text_light, italic=True)
            ], spacing=0)
        else:
            date_row = ft.Text(date, size=12, color=col_text_light)
        
        # Başlık stili
        title_style = ft.TextStyle(weight="bold", size=14, color=col_text)
        if is_deleted:
            title_style.decoration = ft.TextDecoration.LINE_THROUGH
            title_style.color = "#9E9E9E"
            
        # Başlık ve tarih - güncellenmiş veya silinmiş ise yanında nokta
        if is_updated or is_deleted:
            title_row = ft.Row([
                ft.Text(title, style=title_style),
                status_indicator
            ], spacing=5)
            row_controls.append(
                ft.Column([title_row, date_row], spacing=2, expand=True)
            )
        else:
            row_controls.append(
                ft.Column([ft.Text(title, style=title_style), date_row], spacing=2, expand=True)
            )
        
        amount_text = f"{sign} {amount}"
        amount_style = ft.TextStyle(weight="bold", size=15, color=color)
        if is_deleted:
            amount_style.decoration = ft.TextDecoration.LINE_THROUGH
            
        row_controls.append(ft.Text(amount_text, style=amount_style))
        
        self.content = ft.Row(row_controls, spacing=12)

def currency_button(text, currency_code, current_selection, on_click_handler):
    is_selected = (currency_code == current_selection)
    return ft.Container(
        content=ft.Text(text, color=col_primary if is_selected else col_text_light, weight="bold" if is_selected else "normal"),
        bgcolor=col_white if is_selected else "transparent",
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=5, color="#10000000", offset=ft.Offset(0,2)) if is_selected else None,
        on_click=lambda e: on_click_handler(currency_code),
        animate=ft.Animation(200, "easeOut")
    )

# --- ANA UYGULAMA ---
# ============================================================================
# ANA UYGULAMA (Main Application)
# ============================================================================
def main(page: ft.Page):
    page.title = "Excellent"
    page.padding = 0
    page.bgcolor = col_bg
    page.window.width = 1400 
    page.window.height = 900
    page.window.icon = resource_path("app_icon.ico")
    page.theme_mode = ft.ThemeMode.LIGHT

    # ------------------------------------------------------------------------
    # VERİ YARDIMCILARI (Data Helpers)
    # ------------------------------------------------------------------------
    def get_all_available_years():
        """Veritabanındaki tüm yılları döndürür (gelir, gider ve genel gider tablolarından) - sadece veri olan yıllar"""
        years = set()
        try:
            # Gelir faturalarından yılları topla
            income_invoices = backend_instance.handle_invoice_operation('get', 'outgoing') or []
            for invoice in income_invoices:
                tarih = invoice.get('tarih', '')
                if tarih:
                    parts = tarih.split('.')
                    if len(parts) == 3:
                        try:
                            years.add(int(parts[2]))
                        except ValueError:
                            pass
            
            # Gider faturalarından yılları topla
            expense_invoices = backend_instance.handle_invoice_operation('get', 'incoming') or []
            for invoice in expense_invoices:
                tarih = invoice.get('tarih', '')
                if tarih:
                    parts = tarih.split('.')
                    if len(parts) == 3:
                        try:
                            years.add(int(parts[2]))
                        except ValueError:
                            pass
            
            # Genel giderlerden yılları topla (sadece en az bir aya veri girilmişse)
            try:
                all_general_expenses = backend_instance.db.get_all_yearly_expenses()
                month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 
                             'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
                
                for expense_data in all_general_expenses:
                    if expense_data and 'yil' in expense_data:
                        # En az bir ayda veri var mı kontrol et
                        has_data = False
                        for month in month_keys:
                            if expense_data.get(month) and float(expense_data.get(month, 0) or 0) > 0:
                                has_data = True
                                break
                        
                        if has_data:
                            try:
                                years.add(int(expense_data['yil']))
                            except (ValueError, TypeError):
                                pass
            except:
                pass
            
        except Exception as e:
            pass
        
        # Eğer hiç yıl bulunamadıysa mevcut yılı ekle
        if not years:
            years.add(datetime.now().year)
        
        return sorted(years, reverse=True)
    
    def get_line_chart_data():
        """Backend'den aylık gelir/gider verilerini çeker ve line chart formatında döndürür"""
        try:
            # Seçili para birimini belirle
            current_currency = state.get("current_currency", "TRY")
            amount_field = "toplam_tutar_tl"
            if current_currency == "USD":
                amount_field = "toplam_tutar_usd"
            elif current_currency == "EUR":
                amount_field = "toplam_tutar_eur"
            
            # Backend'den tüm faturaları al (operation='get')
            income_invoices = backend_instance.handle_invoice_operation('get', 'outgoing') or []
            expense_invoices = backend_instance.handle_invoice_operation('get', 'incoming') or []
            
            # Yıllara göre grupla
            yearly_data = {}
            
            # Gelir faturalarını işle
            for idx, invoice in enumerate(income_invoices):
                tarih = invoice.get('tarih', '')
                if not tarih: 
                    continue
                
                parts = tarih.split('.')
                if len(parts) != 3: 
                    continue
                
                try:
                    month = int(parts[1])
                    year = int(parts[2])
                    amount = float(invoice.get(amount_field, 0)) / 1000  # K (bin) cinsine çevir
                    
                    if year not in yearly_data:
                        yearly_data[year] = {"gelir": [0]*12, "gider": [0]*12}
                    
                    yearly_data[year]["gelir"][month-1] += amount
                except (ValueError, IndexError) as ex:
                    continue
            
            # Gider faturalarını işle
            for invoice in expense_invoices:
                tarih = invoice.get('tarih', '')
                if not tarih: continue
                
                parts = tarih.split('.')
                if len(parts) != 3: continue
                
                try:
                    month = int(parts[1])
                    year = int(parts[2])
                    amount = float(invoice.get(amount_field, 0)) / 1000  # K (bin) cinsine çevir
                    
                    if year not in yearly_data:
                        yearly_data[year] = {"gelir": [0]*12, "gider": [0]*12}
                    
                    yearly_data[year]["gider"][month-1] += amount
                except (ValueError, IndexError):
                    continue
            
            # Genel giderleri ekle - her yıl için
            month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
            for year in list(yearly_data.keys()):
                general_expenses = backend_instance.db.get_yearly_expenses(year)
                if general_expenses:
                    for month_idx, month_key in enumerate(month_keys):
                        if month_key in general_expenses:
                            general_amount_tl = float(general_expenses[month_key] or 0)
                            
                            # Para birimine göre çevir
                            general_amount = general_amount_tl
                            if current_currency != "TRY":
                                general_amount = backend_instance.convert_currency(general_amount_tl, "TRY", current_currency)
                            
                            yearly_data[year]["gider"][month_idx] += (general_amount / 1000)  # K cinsine çevir
            
            # Eğer veri yoksa boş dict döndür
            if not yearly_data:
                return {}
            
            return yearly_data
        except Exception as e:
            return {}
    
    # ------------------------------------------------------------------------
    # GRAFİK ÇİZİM FONKSİYONLARI (Chart Drawing Functions)
    # ------------------------------------------------------------------------
    full_data = get_line_chart_data()  # Backend'den gerçek veri

    # Max değeri hesapla (dinamik Y ekseni için)
    def calculate_max_y(year=None):
        """Grafikteki maksimum değeri bulur ve uygun Y ekseni limiti döndürür. Eğer yıl belirtilirse sadece o yılın verilerini kullanır."""
        if not full_data:
            return 150  # Varsayılan
        
        max_value = 0
        
        if year and year in full_data:
            # Sadece belirtilen yılın verileri
            year_data = full_data[year]
            max_value = max(max(year_data.get("gelir", [0])), max(year_data.get("gider", [0])))
        else:
            # Tüm yılların verileri
            for year_data in full_data.values():
                max_value = max(max_value, max(year_data.get("gelir", [0])), max(year_data.get("gider", [0])))
        
        # Yuvarla (50'lik artışlarla)
        if max_value == 0:
            return 150
        
        # Daha iyi görünüm için biraz boşluk bırak
        return ((int(max_value) // 50) + 2) * 50
    
    chart_max_y = calculate_max_y()
    
    # Y ekseni label'larını dinamik oluştur
    def get_y_axis_labels(max_y):
        """Y ekseni için dinamik label'lar oluşturur"""
        current_currency = state.get("current_currency", "TRY")
        symbol = ""
        if current_currency == "USD":
            symbol = "$"
        elif current_currency == "EUR":
            symbol = "€"
            
        step = max_y // 3
        return [
            ft.ChartAxisLabel(value=0, label=ft.Text("0", size=10, color=col_text_light)),
            ft.ChartAxisLabel(value=step, label=ft.Text(f"{symbol}{step}K", size=10, color=col_text_light)),
            ft.ChartAxisLabel(value=step*2, label=ft.Text(f"{symbol}{step*2}K", size=10, color=col_text_light)),
            ft.ChartAxisLabel(value=max_y, label=ft.Text(f"{symbol}{max_y}K", size=10, color=col_text_light))
        ]
    
    line_chart = ft.LineChart(data_series=[ft.LineChartData(data_points=[], stroke_width=5, color=col_primary, curved=True, stroke_cap_round=True, below_line_gradient=ft.LinearGradient(begin=ft.alignment.top_center, end=ft.alignment.bottom_center, colors=[col_primary_50, transparent_white])), ft.LineChartData(data_points=[], stroke_width=5, color=col_secondary, curved=True, stroke_cap_round=True, below_line_gradient=ft.LinearGradient(begin=ft.alignment.top_center, end=ft.alignment.bottom_center, colors=[col_secondary_50, transparent_white]))], border=ft.border.all(0, "transparent"), bottom_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=i, label=ft.Text(m, size=12, color=col_text_light)) for i, m in enumerate(["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"])], labels_size=30), left_axis=ft.ChartAxis(labels=get_y_axis_labels(chart_max_y), labels_size=40), tooltip_bgcolor=tooltip_bg, min_y=0, max_y=chart_max_y, min_x=0, max_x=11, expand=True, horizontal_grid_lines=ft.ChartGridLines(color="#F0F0F0", width=1, dash_pattern=[5, 5]), animate=None)

    def draw_snake_chart(year):
        """Yılan grafiğini çizen fonksiyon - yıl parametresi int veya str olabilir"""
        # Yıl değerini int'e çevir
        try:
            year = int(year)
        except (ValueError, TypeError):
            return
            
        if state["current_page"] != "home": return
        
        # SAYFADAN KONTROL: Eğer bileşen sayfada yoksa işlem yapma
        if not line_chart.page: return
        
        # Veri kontrolü - Eğer seçili yıl veya veri yoksa boş grafik göster
        if not full_data or year not in full_data:
            line_chart.data_series[0].data_points = []
            line_chart.data_series[1].data_points = []
            try: line_chart.update()
            except: pass
            return
        
        # Seçili yıla göre Y eksenini yeniden hesapla ve güncelle
        year_max_y = calculate_max_y(year)
        line_chart.max_y = year_max_y
        line_chart.left_axis.labels = get_y_axis_labels(year_max_y)
        
        # Para birimi sembolü
        current_currency = state.get("current_currency", "TRY")
        symbol = ""
        if current_currency == "USD":
            symbol = "$"
        elif current_currency == "EUR":
            symbol = "€"

        # Animasyon bittiyse direkt çiz
        if state["animation_completed"]:
            line_chart.data_series[0].data_points = [ft.LineChartDataPoint(i, full_data[year]["gelir"][i], tooltip=f"{symbol}{full_data[year]['gelir'][i]:.1f}K") for i in range(12)]
            line_chart.data_series[1].data_points = [ft.LineChartDataPoint(i, full_data[year]["gider"][i], tooltip=f"{symbol}{full_data[year]['gider'][i]:.1f}K") for i in range(12)]
            try: 
                line_chart.update()
            except Exception as ex:
                pass
            return

        # Animasyonlu Çizim Başlangıcı
        line_chart.data_series[0].data_points = []
        line_chart.data_series[1].data_points = []
        try: line_chart.update()
        except: pass
        
        time.sleep(0.2) 
        
        gelir_data = full_data[year]["gelir"]
        gider_data = full_data[year]["gider"]
        
        for i in range(len(gelir_data)):
            if state["current_page"] != "home": 
                state["animation_completed"] = True
                return
            
            line_chart.data_series[0].data_points.append(ft.LineChartDataPoint(i, gelir_data[i], tooltip=f"{symbol}{gelir_data[i]:.1f}K"))
            line_chart.data_series[1].data_points.append(ft.LineChartDataPoint(i, gider_data[i], tooltip=f"{symbol}{gider_data[i]:.1f}K"))
            
            try:
                if line_chart.page: line_chart.update()
            except: pass
            time.sleep(0.04) 
        
        state["animation_completed"] = True 
        try:
            if line_chart.page: line_chart.update()
        except Exception as ex:
            pass

    def on_year_change(e): 
        state["animation_completed"] = False
        # Hem yılan grafik hem de donut'ları güncelle
        threading.Thread(target=draw_snake_chart, args=(e.control.value,), daemon=True).start()
        # Donut'ları da güncelle
        update_donuts_for_year(int(e.control.value))
    
    def update_donuts_for_year(year):
        """Seçili yıla göre donut'ları günceller"""
        try:
            # Seçili para birimini al
            current_currency = state.get("current_currency", "TRY")
            
            # Seçili yıl için istatistikleri al
            year_stats = get_dashboard_stats(year)
            
            # Her donut için yeni değerleri hesapla
            profit_max = max(abs(year_stats['net_profit']) * 1.2, 10000)
            income_max = max(year_stats['total_income'] * 1.2, 10000)
            expense_max = max(year_stats['total_expense'] * 1.2, 10000)
            avg_max = max(year_stats['monthly_avg'] * 1.2, 10000)
            
            # Donut'ları güncelle
            if len(state["donuts"]) >= 4:
                # Net kâr donut
                state["donuts"][0].update_value(abs(year_stats['net_profit']), profit_max, format_currency(year_stats['net_profit'], currency=current_currency, compact=True))
                
                # Toplam gelir donut
                state["donuts"][1].update_value(year_stats['total_income'], income_max, format_currency(year_stats['total_income'], currency=current_currency, compact=True))
                
                # Toplam gider donut
                state["donuts"][2].update_value(year_stats['total_expense'], expense_max, format_currency(year_stats['total_expense'], currency=current_currency, compact=True))
                
                # Aylık ortalama donut
                state["donuts"][3].update_value(year_stats['monthly_avg'], avg_max, format_currency(year_stats['monthly_avg'], currency=current_currency, compact=True))
        except Exception as e:
            pass

    # Backend callback'ini yeniden tanımla (grafikleri güncellemek için)
    # ------------------------------------------------------------------------
    # VERİ GÜNCELLEME (Data Refresh)
    # ------------------------------------------------------------------------
    def refresh_charts_and_data():
        """Grafikleri ve verileri yeniden yükler"""
        try:
            nonlocal full_data, chart_max_y, year_dropdown_options, available_years
            
            # 1. Grafik verilerini yeniden yükle
            full_data = get_line_chart_data()
            
            # 2. Yıl seçeneklerini güncelle - tüm veritabanı yıllarını çek
            available_years = get_all_available_years()
            year_dropdown_options = [ft.dropdown.Option(str(year)) for year in available_years]
            
            # 3. Dropdown'ı güncelle
            if year_dropdown_ref:
                year_dropdown_ref.options = year_dropdown_options
                # Eğer seçili yıl hala mevcut değilse, ilk yılı seç
                current_selected = year_dropdown_ref.value
                if current_selected not in [str(y) for y in available_years]:
                    year_dropdown_ref.value = str(available_years[0]) if available_years else str(datetime.now().year)
                
                if hasattr(year_dropdown_ref, 'page') and year_dropdown_ref.page:
                    year_dropdown_ref.update()
            
            # 4. Seçili yılı al
            selected_year = int(year_dropdown_ref.value) if year_dropdown_ref and year_dropdown_ref.value else (available_years[0] if available_years else datetime.now().year)
            
            # 5. Seçili yıla göre Max Y değerini hesapla
            chart_max_y = calculate_max_y(selected_year)
            
            # Para birimi sembolü
            current_currency = state.get("current_currency", "TRY")
            symbol = ""
            if current_currency == "USD":
                symbol = "$"
            elif current_currency == "EUR":
                symbol = "€"
            
            # 6. Line chart'ı güncelle
            if line_chart:
                try:
                    line_chart.left_axis.labels = get_y_axis_labels(chart_max_y)
                    line_chart.max_y = chart_max_y
                    
                    if selected_year in full_data:
                        # Grafiği direkt çiz (animasyonsuz)
                        line_chart.data_series[0].data_points = [ft.LineChartDataPoint(i, full_data[selected_year]["gelir"][i], tooltip=f"{symbol}{full_data[selected_year]['gelir'][i]:.1f}K") for i in range(12)]
                        line_chart.data_series[1].data_points = [ft.LineChartDataPoint(i, full_data[selected_year]["gider"][i], tooltip=f"{symbol}{full_data[selected_year]['gider'][i]:.1f}K") for i in range(12)]
                    else:
                        # Veri yoksa grafiği temizle
                        line_chart.data_series[0].data_points = []
                        line_chart.data_series[1].data_points = []
                    
                    # Update sadece page varsa
                    if hasattr(line_chart, 'page') and line_chart.page:
                        line_chart.update()
                except:
                    pass
            
            # 7. Donut grafikleri güncelle - seçili yıla göre
            update_donuts_for_year(selected_year)
            
            # 7. Sayfayı güncelle
            try:
                page.update()
            except:
                pass
                        
        except Exception as e:
            pass
    
    # Ana sayfa için birleşik callback - hem grafikler hem işlem geçmişi
    state["update_callbacks"]["home_page"] = refresh_charts_and_data

    # ------------------------------------------------------------------------
    # SIDEBAR BİLEŞENLERİ (Sidebar Components)
    # ------------------------------------------------------------------------
    class SidebarButton(ft.Container):
        def __init__(self, icon_name, text, page_name, is_selected=False):
            super().__init__()
            self.data = page_name
            self.is_selected = is_selected
            self.icon_name = icon_name  # İkon adını sakla
            self.width = 50
            self.height = 50
            self.border_radius = 12
            self.padding = 0
            self.alignment = ft.alignment.center
            self.animate = ft.Animation(200, "easeOut") 
            # Başlangıç rengi - seçili ise beyaz, değilse koyu gri
            initial_color = col_white if is_selected else "#374151"
            # İKİ AYRI IKON OLUŞTUR
            self.icon_expanded = ft.Icon(icon_name, size=24, color=initial_color)
            self.icon_collapsed = ft.Icon(icon_name, size=24, color=initial_color)
            self.text_control = ft.Text(text, size=15, weight="w600", visible=state["sidebar_expanded"], color=initial_color)
            self.content_row = ft.Row([self.icon_expanded, self.text_control], spacing=15, alignment=ft.MainAxisAlignment.START, visible=state["sidebar_expanded"])
            self.content_icon_only = ft.Container(content=self.icon_collapsed, alignment=ft.alignment.center, visible=not state["sidebar_expanded"])
            self.content = ft.Stack([self.content_row, self.content_icon_only])
            self.update_visuals(run_update=False)

        def update_visuals(self, run_update=True):
            self.text_control.visible = state["sidebar_expanded"]
            self.content_row.visible = state["sidebar_expanded"]
            self.content_icon_only.visible = not state["sidebar_expanded"]
            self.width = 220 if state["sidebar_expanded"] else 50
            self.padding = ft.padding.only(left=15) if state["sidebar_expanded"] else 0
            self.alignment = ft.alignment.center_left if state["sidebar_expanded"] else ft.alignment.center
            
            # --- STANDART KURAL ---
            if self.is_selected:
                self.bgcolor = col_primary
                new_color = col_white
                self.shadow = ft.BoxShadow(blur_radius=10, color=col_primary_50, offset=ft.Offset(0, 4))
            else:
                self.bgcolor = "transparent"  # Şeffaf arka plan
                new_color = "#374151"  # Daha koyu gri - neredeyse siyah
                self.shadow = None
            
            # Her iki ikonu da güncelle
            self.icon_expanded.color = new_color
            self.icon_collapsed.color = new_color
            self.text_control.color = new_color
                
            if run_update: self.update()

    def toggle_sidebar(e):
        state["sidebar_expanded"] = not state["sidebar_expanded"]
        sidebar_container.width = 260 if state["sidebar_expanded"] else 90
        logo_column.visible = state["sidebar_expanded"]
        menu_row.alignment = ft.MainAxisAlignment.START if state["sidebar_expanded"] else ft.MainAxisAlignment.CENTER
        
        # Nested Column yapısında butonları güncelle
        for col in sidebar_column.controls:
            if isinstance(col, ft.Column):
                for btn in col.controls:
                    if isinstance(btn, SidebarButton):
                        # Önce görünürlük ayarlarını güncelle
                        btn.text_control.visible = state["sidebar_expanded"]
                        btn.content_row.visible = state["sidebar_expanded"]
                        btn.content_icon_only.visible = not state["sidebar_expanded"]
                        btn.width = 220 if state["sidebar_expanded"] else 50
                        btn.padding = ft.padding.only(left=15) if state["sidebar_expanded"] else 0
                        btn.alignment = ft.alignment.center_left if state["sidebar_expanded"] else ft.alignment.center
                        
                        # Renkleri güncelle
                        if btn.is_selected:
                            btn.bgcolor = col_primary
                            btn.icon_expanded.color = col_white
                            btn.icon_collapsed.color = col_white
                            btn.text_control.color = col_white
                            btn.shadow = ft.BoxShadow(blur_radius=10, color=col_primary_50, offset=ft.Offset(0, 4))
                        else:
                            btn.bgcolor = "transparent"
                            btn.icon_expanded.color = "#374151"
                            btn.icon_collapsed.color = "#374151"
                            btn.text_control.color = "#374151"
                            btn.shadow = None
                        
                        btn.update()
        page.update()

    # ------------------------------------------------------------------------
    # DÖNEMSEL GELİR SAYFASI (Periodic Income Page)
    # ------------------------------------------------------------------------
    def create_donemsel_page():
        # Yıl dropdown'ı için seçenekler
        current_year = datetime.now().year
        year_options = [ft.dropdown.Option(str(y)) for y in range(current_year - 2, current_year + 2)]
        
        year_dropdown = ft.Dropdown(
            options=year_options,
            value=str(current_year),
            text_size=12,
            content_padding=10,
            width=95,
            bgcolor=col_white,
            border_color=col_border,
            border_radius=8
        )
        
        # Kurumlar vergisi input field'ları - tabloda kullanılacak
        month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
        tax_fields_dict = {}
        tax_fields_list = []
        
        # Kaydetme fonksiyonu - odak kaybedildiğinde çalışır
        def on_tax_field_blur(e):
            """TextField'dan çıkıldığında otomatik kaydet"""
            try:
                selected_year = int(year_dropdown.value)
                monthly_data = {}
                
                for month_key in month_keys:
                    value = tax_fields_dict[month_key].value
                    try:
                        monthly_data[month_key] = float(value.replace(',', '.')) if value else 0
                    except ValueError:
                        monthly_data[month_key] = 0
                
                # Database'e kaydet
                backend_instance.db.add_or_update_corporate_tax(selected_year, monthly_data)
                
                # Veri güncelleme callback'ini çağır
                if backend_instance.on_data_updated:
                    backend_instance.on_data_updated()
                
                # Tabloyu güncelle (ödenecek vergi hesabı için)
                table_container.content = create_donemsel_table(selected_year, tax_fields_list, on_tax_field_blur)
                page.update()
            except:
                pass
        
        # 12 aylık TextField oluştur
        for i, month_key in enumerate(month_keys):
            text_field = ft.TextField(
                value="0",
                text_size=12,
                color=col_text,
                text_align=ft.TextAlign.CENTER,
                border_color="#E0E0E0",
                focused_border_color=col_primary,
                height=35,
                width=120,
                content_padding=ft.padding.symmetric(horizontal=5, vertical=5),
                bgcolor="#FAFAFA",
                suffix_text=" %",
                hint_text="0",
                on_blur=on_tax_field_blur
            )
            tax_fields_dict[month_key] = text_field
            tax_fields_list.append(text_field)
        
        # Database'den kurumlar vergisi verilerini yükle
        def load_corporate_tax_data():
            selected_year = int(year_dropdown.value)
            tax_data = backend_instance.db.get_corporate_tax(selected_year) or {}
            for month_key in month_keys:
                amount = tax_data.get(month_key, 0)
                tax_fields_dict[month_key].value = str(amount) if amount else "0"
            # Tabloya field'ları geç ve güncelle
            table_container.content = create_donemsel_table(selected_year, tax_fields_list, on_tax_field_blur)
            page.update()
        
        # Dinamik güncelleme için callback kaydet
        def refresh_donemsel_data():
            """Veri değiştiğinde dönemsel tabloyu güncelle"""
            try:
                # Sadece dönemsel sayfadayken güncelle
                if state["current_page"] != "donemsel":
                    return
                    
                selected_year = int(year_dropdown.value)
                
                # Kurumlar vergisi verilerini yeniden yükle
                tax_data = backend_instance.db.get_corporate_tax(selected_year) or {}
                month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
                for month_key in month_keys:
                    amount = tax_data.get(month_key, 0)
                    if month_key in tax_fields_dict:
                        tax_fields_dict[month_key].value = str(amount) if amount else "0"
                
                # Tabloyu güncelle
                table_container.content = create_donemsel_table(selected_year, tax_fields_list, on_tax_field_blur)
                if table_container.page:
                    table_container.update()
                    page.update()
            except:
                pass
        
        state["update_callbacks"]["donemsel_page"] = refresh_donemsel_data
        
        # Tablo container - başlangıçta field'ları ile oluştur
        table_container = ft.Container(
            expand=True,
            bgcolor=col_white,
            padding=20,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=10, color="#1A000000", offset=ft.Offset(0, 5)),
            content=create_donemsel_table(current_year, tax_fields_list, on_tax_field_blur)
        )
        
        # İlk yüklemede verileri doldur
        load_corporate_tax_data()
        
        def on_year_change(e):
            """Yıl değiştiğinde tabloyu güncelle"""
            selected_year = int(e.control.value)
            
            # Kurumlar vergisi verilerini yükle
            tax_data = backend_instance.db.get_corporate_tax(selected_year) or {}
            month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
            for month_key in month_keys:
                amount = tax_data.get(month_key, 0)
                tax_fields_dict[month_key].value = str(amount) if amount else "0"
            
            # Tabloyu güncelle
            table_container.content = create_donemsel_table(selected_year, tax_fields_list, on_tax_field_blur)
            page.update()
        
        year_dropdown.on_change = on_year_change
        
        # Export fonksiyonları
        def export_to_excel_donemsel(e):
            """Dönemsel gelir raporunu Excel'e aktar"""
            try:
                selected_year = int(year_dropdown.value)
                
                def on_save_result(e: ft.FilePickerResultEvent):
                    if e.path:
                        file_path = e.path
                        # Verileri topla
                        monthly_results, quarterly_results, summary = calculate_periodic_data(selected_year)
                        
                        # Export
                        from toexcel import export_monthly_income_to_excel
                        success = export_monthly_income_to_excel(selected_year, monthly_results, quarterly_results, summary, file_path)
                        
                        if success:
                            def close_success_dlg(e):
                                success_dlg.open = False
                                page.update()

                            success_dlg = ft.AlertDialog(
                                modal=True,
                                title=ft.Text("Başarılı"),
                                content=ft.Text(f"Dosya başarıyla kaydedildi:\n{file_path}"),
                                actions=[
                                    ft.ElevatedButton("Tamam", on_click=close_success_dlg, bgcolor=col_primary, color=col_white),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(success_dlg)
                            success_dlg.open = True
                            page.update()
                        else:
                            page.snack_bar = ft.SnackBar(content=ft.Text("❌ Excel raporu oluşturulamadı!", color=col_white), bgcolor=col_danger)
                            page.snack_bar.open = True
                            page.update()

                timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                filename = f"DonemselGelir_{selected_year}_{timestamp}.xlsx"
                
                save_file_picker = ft.FilePicker(on_result=on_save_result)
                page.overlay.append(save_file_picker)
                page.update()
                save_file_picker.save_file(dialog_title="Excel Raporunu Kaydet", file_name=filename, allowed_extensions=["xlsx"])
                    
            except Exception as ex:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Hata: {str(ex)}", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()
        
        def export_to_pdf_donemsel(e):
            """Dönemsel gelir raporunu PDF'e aktar"""
            try:
                selected_year = int(year_dropdown.value)
                
                def on_save_result(e: ft.FilePickerResultEvent):
                    if e.path:
                        file_path = e.path
                        # Verileri topla
                        monthly_results, quarterly_results, summary = calculate_periodic_data(selected_year)
                        
                        # Export
                        from topdf import export_monthly_income_to_pdf
                        success = export_monthly_income_to_pdf(selected_year, monthly_results, quarterly_results, summary, file_path)
                        
                        if success:
                            def close_success_dlg(e):
                                success_dlg.open = False
                                page.update()

                            success_dlg = ft.AlertDialog(
                                modal=True,
                                title=ft.Text("Başarılı"),
                                content=ft.Text(f"Dosya başarıyla kaydedildi:\n{file_path}"),
                                actions=[
                                    ft.ElevatedButton("Tamam", on_click=close_success_dlg, bgcolor=col_primary, color=col_white),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(success_dlg)
                            success_dlg.open = True
                            page.update()
                        else:
                            page.snack_bar = ft.SnackBar(content=ft.Text("❌ PDF raporu oluşturulamadı!", color=col_white), bgcolor=col_danger)
                            page.snack_bar.open = True
                            page.update()

                timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                filename = f"DonemselGelir_{selected_year}_{timestamp}.pdf"
                
                save_file_picker = ft.FilePicker(on_result=on_save_result)
                page.overlay.append(save_file_picker)
                page.update()
                save_file_picker.save_file(dialog_title="PDF Raporunu Kaydet", file_name=filename, allowed_extensions=["pdf"])
                    
            except Exception as ex:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Hata: {str(ex)}", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()
        
        def calculate_periodic_data(year):
            """Dönemsel veriler için hesaplama yap"""
            # Backend'den verileri çek
            income_invoices = backend_instance.handle_invoice_operation('get', 'outgoing') or []
            expense_invoices = backend_instance.handle_invoice_operation('get', 'incoming') or []
            general_expenses = backend_instance.db.get_yearly_expenses(year) or {}
            corporate_tax_data = backend_instance.db.get_corporate_tax(year) or {}
            
            # Aylık hesaplamalar
            monthly_income = [0.0] * 12
            monthly_expense = [0.0] * 12
            monthly_general = [0.0] * 12
            monthly_income_kdv = [0.0] * 12
            monthly_expense_kdv = [0.0] * 12
            monthly_corporate_tax = [0.0] * 12
            
            # Gelir faturalarını işle
            for invoice in income_invoices:
                tarih = invoice.get('tarih', '')
                if not tarih: continue
                parts = tarih.split('.')
                if len(parts) != 3: continue
                try:
                    month = int(parts[1])
                    invoice_year = int(parts[2])
                    if invoice_year == year:
                        monthly_income[month-1] += float(invoice.get('toplam_tutar_tl', 0))
                        monthly_income_kdv[month-1] += float(invoice.get('kdv_tutari', 0))
                except (ValueError, IndexError):
                    continue
            
            # Gider faturalarını işle
            for invoice in expense_invoices:
                tarih = invoice.get('tarih', '')
                if not tarih: continue
                parts = tarih.split('.')
                if len(parts) != 3: continue
                try:
                    month = int(parts[1])
                    invoice_year = int(parts[2])
                    if invoice_year == year:
                        monthly_expense[month-1] += float(invoice.get('toplam_tutar_tl', 0))
                        monthly_expense_kdv[month-1] += float(invoice.get('kdv_tutari', 0))
                except (ValueError, IndexError):
                    continue
            
            # Genel gider ve kurumlar vergisi
            month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
            for i in range(12):
                month_key = month_keys[i]
                if month_key in general_expenses:
                    monthly_general[i] = float(general_expenses[month_key] or 0)
                if month_key in corporate_tax_data:
                    monthly_corporate_tax[i] = float(corporate_tax_data[month_key] or 0)
            
            # Aylık sonuçları hazırla
            monthly_results = []
            total_income = 0.0
            total_expense = 0.0
            
            for i in range(12):
                income = monthly_income[i]
                expense = monthly_expense[i]
                general = monthly_general[i]
                income_kdv = monthly_income_kdv[i]
                expense_kdv = monthly_expense_kdv[i]
                tax_percentage = monthly_corporate_tax[i]
                
                total_month_expense = expense + general
                taxable_base = income - total_month_expense
                kurumlar_vergisi = (taxable_base * tax_percentage / 100) if tax_percentage > 0 else 0
                
                total_income += income
                total_expense += total_month_expense
                
                monthly_results.append({
                    'kesilen': income,
                    'gelen': total_month_expense,
                    'kdv': income_kdv - expense_kdv,
                    'kurumlar': kurumlar_vergisi,
                    'kurumlar_yuzde': tax_percentage,
                    'gelir_kdv': income_kdv,
                    'gider_kdv': expense_kdv
                })
            
            # Çeyreklik sonuçları hesapla
            quarterly_results = []
            for q in range(4):
                start_month = q * 3
                quarter_kurumlar = sum(monthly_results[start_month + j]['kurumlar'] for j in range(3))
                quarterly_results.append({'odenecek_kv': quarter_kurumlar})
            
            total_kurumlar = sum(q['odenecek_kv'] for q in quarterly_results)
            total_kdv = sum(m['kdv'] for m in monthly_results)
            net_profit = total_income - total_expense - total_kurumlar
            
            summary = {
                'toplam_gelir': total_income,
                'toplam_gider': total_expense,
                'yillik_kar': net_profit
            }
            
            return monthly_results, quarterly_results, summary
        
        right_buttons = ft.Container(
            padding=ft.padding.only(right=40),
            content=ft.Row([
                ScaleButton("table_view", "#217346", "Excel", width=45, height=40, on_click=export_to_excel_donemsel),
                ScaleButton("picture_as_pdf", "#D32F2F", "PDF", width=45, height=40, on_click=export_to_pdf_donemsel),
            ], spacing=8)
        )

        top_bar = ft.Row([
            ft.Container(height=38, content=year_dropdown),
            right_buttons
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        return ft.Container(
            alignment=ft.alignment.top_center,
            padding=30,
            content=ft.Column([
                ft.Row([ft.Text("Dönemsel ve Yıllık Gelir", size=26, weight="bold", color=col_text)]),
                ft.Container(height=15),
                ft.Container(content=top_bar),
                ft.Container(height=15),
                table_container
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH, scroll=ft.ScrollMode.AUTO, expand=True)
        )

    # ------------------------------------------------------------------------
    # FATURALAR SAYFASI (Invoices Page)
    # ------------------------------------------------------------------------
    def create_invoices_page():
        general_expenses_section = create_grid_expenses(page)
        # Başlangıç durumuna göre visibility ayarla (income=gelir ise gizli, expense=gider ise görünür)
        general_expenses_section.visible = (state.get("invoice_type", "income") == "expense")

        # Seçili fatura sayısını gösteren text
        selected_count_text = ft.Text("", size=12, color=col_danger, weight="bold", visible=False)
        
        # Tarih alanı için on_blur handler - kullanıcı alanı terk ettiğinde tarihi formatla
        def on_tarih_blur(e):
            if e.control.value:
                formatted = format_date_input(e.control.value)
                if formatted != e.control.value:
                    e.control.value = formatted
                    e.control.update()
        
        # Input alanları önce tanımlanmalı (update_selected_count bunları kullanacak)
        input_fatura_no = ft.TextField(hint_text="FAT-2025...", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        input_tarih = ft.TextField(hint_text="ggaayy veya gg.aa.yyyy (örn. 121225)", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12), on_blur=on_tarih_blur)
        input_firma = ft.TextField(hint_text="Firma seçiniz...", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        input_malzeme = ft.TextField(hint_text="Ürün giriniz...", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        input_miktar = ft.TextField(hint_text="0", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        input_tutar = ft.TextField(hint_text="0.00", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        input_para_birimi = ft.Dropdown(options=[ft.dropdown.Option("TL"), ft.dropdown.Option("USD"), ft.dropdown.Option("EUR")], text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=5), hint_text="TL", hint_style=ft.TextStyle(color="#D0D0D0", size=12), value="TL")
        input_kdv = ft.TextField(hint_text="Varsayılan (%)20", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        
        # Manuel döviz kuru girişi (opsiyonel)
        input_usd_kur = ft.TextField(hint_text="Opsiyonel (TCMB)", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        input_eur_kur = ft.TextField(hint_text="Opsiyonel (TCMB)", hint_style=ft.TextStyle(color="#D0D0D0", size=12), text_size=13, color=col_text, border_color="transparent", bgcolor="transparent", content_padding=ft.padding.only(left=10, bottom=12))
        
        def update_selected_count(e=None):
            """Seçili fatura sayısını güncelle ve tek seçimde inputları doldur"""
            try:
                if table_container.content and hasattr(table_container.content, 'rows'):
                    # Checkbox'lardan seçili olanları bul
                    selected_rows = []
                    for row in table_container.content.rows:
                        # İlk hücredeki checkbox'u kontrol et
                        if len(row.cells) > 0:
                            first_cell = row.cells[0]
                            if hasattr(first_cell, 'content') and isinstance(first_cell.content, ft.Checkbox):
                                if first_cell.content.value:
                                    selected_rows.append(row)
                    
                    selected_count = len(selected_rows)
                    
                    if selected_count > 0:
                        selected_count_text.value = f"({selected_count})"
                        selected_count_text.visible = True
                        
                        # Tek satır seçiliyse inputları doldur
                        if selected_count == 1 and isinstance(selected_rows[0].data, dict):
                            invoice = selected_rows[0].data
                            input_fatura_no.value = str(invoice.get('fatura_no', ''))
                            input_tarih.value = str(invoice.get('tarih', ''))
                            input_firma.value = str(invoice.get('firma', ''))
                            input_malzeme.value = str(invoice.get('malzeme', ''))
                            input_miktar.value = str(invoice.get('miktar', ''))
                            
                            # Para birimine göre doğru tutar alanını seç
                            birim = str(invoice.get('birim', 'TL'))
                            input_para_birimi.value = birim
                            
                            if birim == 'TL':
                                tutar = round(float(invoice.get('toplam_tutar_tl', 0)), 5)
                            elif birim == 'USD':
                                tutar = round(float(invoice.get('toplam_tutar_usd', 0)), 5)
                            elif birim == 'EUR':
                                tutar = round(float(invoice.get('toplam_tutar_eur', 0)), 5)
                            else:
                                tutar = round(float(invoice.get('toplam_tutar_tl', 0)), 5)
                            
                            input_tutar.value = str(tutar) if tutar else '0'
                            input_kdv.value = str(round(float(invoice.get('kdv_yuzdesi', 20.0)), 5))
                            
                            # Manuel döviz kurlarını doldur (varsa)
                            usd_rate = round(float(invoice.get('usd_rate', 0)), 5)
                            eur_rate = round(float(invoice.get('eur_rate', 0)), 5)
                            
                            input_usd_kur.value = str(usd_rate) if usd_rate and usd_rate > 0 else ''
                            input_eur_kur.value = str(eur_rate) if eur_rate and eur_rate > 0 else ''
                    else:
                        selected_count_text.value = ""
                        selected_count_text.visible = False
                    
                    # Hem selected_count_text hem de tüm input alanlarını güncelle
                    selected_count_text.update()
                    table_container.update()
                    page.update()
            except Exception as ex:
                pass
        
        table_container = ft.Container(
            expand=True,
            border_radius=12, 
            shadow=ft.BoxShadow(blur_radius=15, color="#1A000000", offset=ft.Offset(0, 5)), 
            bgcolor=col_white, 
            content=create_invoice_table_content("newest", state.get("invoice_type", "income"), on_select_changed=update_selected_count)
        )

        def update_invoice_table(sort_option=None):
            # Sadece fatura sayfasındayken güncelle
            if state["current_page"] != "invoices":
                return
                
            # Güncel invoice_type'ı kullan
            if sort_option is None:
                sort_option = state.get("invoice_sort_option", "newest")
            current_invoice_type = state.get("invoice_type", "income")
            table_container.content = create_invoice_table_content(sort_option, current_invoice_type, on_select_changed=update_selected_count)
            if table_container.page:
                table_container.update()
        
        # Dinamik güncelleme için callback kaydet
        state["update_callbacks"]["invoice_page"] = update_invoice_table

        def on_sort_change(e): update_invoice_table(e.control.value)

        def toggle_invoice_type(e):
            # State'i değiştir
            state["invoice_type"] = "expense" if state["invoice_type"] == "income" else "income"
            is_expense = state["invoice_type"] == "expense"
            
            # Buton görünümünü güncelle
            active_color = col_secondary if is_expense else col_primary
            btn_container = e.control
            btn_container.content.controls[0].value = "Gelen Faturalar (Gider)" if is_expense else "Giden Faturalar (Gelir)"
            btn_container.bgcolor = active_color
            btn_container.shadow.color = col_secondary_50 if is_expense else col_primary_50
            btn_container.update()
            
            # Genel giderler bölümünü göster/gizle
            general_expenses_section.visible = is_expense
            general_expenses_section.update()
            
            # Fatura tablosunu güncelle
            update_invoice_table(state.get("invoice_sort_option", "newest"))

        # Başlangıç durumuna göre buton ayarla (state başlangıçta "income")
        initial_is_expense = state.get("invoice_type", "income") == "expense"
        initial_color = col_secondary if initial_is_expense else col_primary
        initial_text = "Gelen Faturalar (Gider)" if initial_is_expense else "Giden Faturalar (Gelir)"
        initial_shadow = col_secondary_50 if initial_is_expense else col_primary_50
        
        type_toggle_btn = ft.Container(
            content=ft.Row([
                ft.Text(initial_text, color=col_white, weight="bold", size=14), 
                ft.Icon("swap_horiz", color=col_white, size=20)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5), 
            bgcolor=initial_color, 
            padding=ft.padding.symmetric(horizontal=20, vertical=10), 
            border_radius=8, 
            on_click=toggle_invoice_type, 
            ink=False, 
            shadow=ft.BoxShadow(blur_radius=5, color=initial_shadow, offset=ft.Offset(0,2)), 
            animate=ft.Animation(100, "easeOut")
        )

        def clear_inputs(e=None):
            """Input alanlarını temizle ve seçimleri kaldır"""
            try:
                input_fatura_no.value = ""
                input_tarih.value = ""
                input_firma.value = ""
                input_malzeme.value = ""
                input_miktar.value = ""
                input_tutar.value = ""
                input_para_birimi.value = "TL"
                input_kdv.value = ""
                input_usd_kur.value = ""
                input_eur_kur.value = ""
                state["selected_invoice_id"] = None
                
                # Tüm checkbox seçimlerini kaldır
                if table_container.content and hasattr(table_container.content, 'rows'):
                    for row in table_container.content.rows:
                        if len(row.cells) > 0:
                            first_cell = row.cells[0]
                            if hasattr(first_cell, 'content') and isinstance(first_cell.content, ft.Checkbox):
                                first_cell.content.value = False
                
                # Seçim sayısını sıfırla
                selected_count_text.value = ""
                selected_count_text.visible = False
                
                page.update()
            except Exception as ex:
                pass

        def add_invoice(e):
            """Fatura ekle"""
            try:
                # Input verilerini topla
                invoice_data = {
                    'fatura_no': input_fatura_no.value or "",
                    'tarih': input_tarih.value or "",
                    'firma': input_firma.value or "",
                    'malzeme': input_malzeme.value or "",
                    'miktar': input_miktar.value or "",
                    'toplam_tutar': float(input_tutar.value) if input_tutar.value else 0,
                    'birim': input_para_birimi.value or "TL",
                    'kdv_yuzdesi': float(input_kdv.value) if input_kdv.value else 20.0
                }
                
                # Manuel kur girişi varsa ekle (opsiyonel)
                if input_usd_kur.value and input_usd_kur.value.strip():
                    try:
                        invoice_data['manual_usd_rate'] = float(input_usd_kur.value.replace(',', '.'))
                    except ValueError:
                        pass
                
                if input_eur_kur.value and input_eur_kur.value.strip():
                    try:
                        invoice_data['manual_eur_rate'] = float(input_eur_kur.value.replace(',', '.'))
                    except ValueError:
                        pass
                
                # Fatura işle
                processed_data = process_invoice(invoice_data)
                
                if processed_data:
                    # Backend'e kaydet
                    invoice_type = 'incoming' if state["invoice_type"] == "expense" else 'outgoing'
                    
                    result = backend_instance.handle_invoice_operation('add', invoice_type, processed_data)
                    
                    if result:
                        # Başarılı - tabloyu güncelle
                        update_invoice_table(state.get("invoice_sort_option", "newest"))
                        clear_inputs()
                        page.snack_bar = ft.SnackBar(content=ft.Text("✅ Fatura başarıyla eklendi!", color=col_white), bgcolor=col_success)
                        page.snack_bar.open = True
                        page.update()
                    else:
                        page.snack_bar = ft.SnackBar(content=ft.Text("❌ Fatura eklenemedi!", color=col_white), bgcolor=col_danger)
                        page.snack_bar.open = True
                        page.update()
                else:
                    page.snack_bar = ft.SnackBar(content=ft.Text("❌ Geçersiz fatura verisi! Tutar giriniz.", color=col_white), bgcolor=col_danger)
                    page.snack_bar.open = True
                    page.update()
                    
            except Exception as ex:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Hata: {str(ex)}", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()

        def update_invoice(e):
            """Seçili faturayi güncelle"""
            try:
                # Checkbox'lardan seçili olanları bul
                selected_rows = []
                for row in table_container.content.rows:
                    if len(row.cells) > 0:
                        first_cell = row.cells[0]
                        if hasattr(first_cell, 'content') and isinstance(first_cell.content, ft.Checkbox):
                            if first_cell.content.value:
                                selected_rows.append(row)
                
                if not selected_rows:
                    page.snack_bar = ft.SnackBar(content=ft.Text("⚠️ Güncellemek için bir fatura seçin!", color=col_white), bgcolor=col_secondary)
                    page.snack_bar.open = True
                    page.update()
                    return
                
                if len(selected_rows) > 1:
                    page.snack_bar = ft.SnackBar(content=ft.Text("⚠️ Sadece bir fatura seçin!", color=col_white), bgcolor=col_secondary)
                    page.snack_bar.open = True
                    page.update()
                    return
                
                # Input verilerini topla
                invoice_data = {
                    'fatura_no': input_fatura_no.value or "",
                    'tarih': input_tarih.value or "",
                    'firma': input_firma.value or "",
                    'malzeme': input_malzeme.value or "",
                    'miktar': input_miktar.value or "",
                    'toplam_tutar': float(input_tutar.value) if input_tutar.value else 0,
                    'birim': input_para_birimi.value or "TL",
                    'kdv_yuzdesi': float(input_kdv.value) if input_kdv.value else 20.0
                }
                
                # Manuel kur girişi varsa ekle (opsiyonel)
                if input_usd_kur.value and input_usd_kur.value.strip():
                    try:
                        invoice_data['manual_usd_rate'] = float(input_usd_kur.value.replace(',', '.'))
                    except ValueError:
                        pass
                
                if input_eur_kur.value and input_eur_kur.value.strip():
                    try:
                        invoice_data['manual_eur_rate'] = float(input_eur_kur.value.replace(',', '.'))
                    except ValueError:
                        pass
                
                # Fatura işle
                processed_data = process_invoice(invoice_data)
                
                if processed_data:
                    # Backend'e güncelle
                    invoice_data_from_row = selected_rows[0].data
                    invoice_id = invoice_data_from_row.get('id') if isinstance(invoice_data_from_row, dict) else invoice_data_from_row
                    invoice_type = 'incoming' if state["invoice_type"] == "expense" else 'outgoing'
                    
                    result = backend_instance.handle_invoice_operation('update', invoice_type, processed_data, record_id=invoice_id)
                    
                    if result:
                        # Tabloyu yenile - invoice type'a göre
                        table_container.content = create_invoice_table_content(
                            state.get("invoice_sort_option", "newest"),
                            state.get("invoice_type", "income"),
                            on_select_changed=update_selected_count
                        )
                        table_container.update()
                        clear_inputs()
                        page.snack_bar = ft.SnackBar(content=ft.Text("✅ Fatura güncellendi!", color=col_white), bgcolor=col_success)
                        page.snack_bar.open = True
                        page.update()
                    else:
                        page.snack_bar = ft.SnackBar(content=ft.Text("❌ Güncelleme başarısız!", color=col_white), bgcolor=col_danger)
                        page.snack_bar.open = True
                        page.update()
                else:
                    page.snack_bar = ft.SnackBar(content=ft.Text("❌ Geçersiz fatura verisi!", color=col_white), bgcolor=col_danger)
                    page.snack_bar.open = True
                    page.update()
                    
            except Exception as ex:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Güncelleme hatası: {str(ex)}", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()

        def delete_invoice(e):
            """Seçili faturaları sil - Çoklu seçim destekli"""
            try:
                # Checkbox'lardan seçili olanları bul
                selected_rows = []
                if table_container.content and hasattr(table_container.content, 'rows'):
                    for row in table_container.content.rows:
                        if len(row.cells) > 0:
                            first_cell = row.cells[0]
                            if hasattr(first_cell, 'content') and isinstance(first_cell.content, ft.Checkbox):
                                if first_cell.content.value:
                                    selected_rows.append(row)
                
                
                if not selected_rows:
                    page.snack_bar = ft.SnackBar(content=ft.Text("⚠️ Lütfen silmek için en az bir fatura seçin!", color=col_white), bgcolor=col_secondary)
                    page.snack_bar.open = True
                    page.update()
                    return
                
                selected_count = len(selected_rows)
                
                # Dialog referansı (closure içinde erişim için)
                dlg_modal = None

                # Onay Dialogu Fonksiyonları
                def close_dlg(e):
                    if dlg_modal:
                        dlg_modal.open = False
                        page.update()
                    
                def confirm_delete(e):
                    if dlg_modal:
                        dlg_modal.open = False
                        page.update()
                        
                    # Tüm faturaları direkt sil (tek veya çoklu, fark etmez)
                    try:
                        current_invoice_type = state.get("invoice_type", "income")
                        db_type = 'outgoing' if current_invoice_type == 'income' else 'incoming'
                        
                        # Callback'i geçici olarak devre dışı bırak (çoklu silmede her seferinde tetiklenmesin)
                        original_callback = backend_instance.on_data_updated
                        backend_instance.on_data_updated = None
                        
                        # Her seçili satırı sil
                        deleted_count = 0
                        failed_count = 0
                        for idx, row in enumerate(selected_rows):
                            invoice_data = row.data
                            
                            if invoice_data and isinstance(invoice_data, dict) and 'id' in invoice_data:
                                invoice_id = invoice_data['id']
                                result = backend_instance.handle_invoice_operation(
                                    operation='delete',
                                    invoice_type=db_type,
                                    record_id=invoice_id
                                )
                                if result:
                                    deleted_count += 1
                                else:
                                    failed_count += 1
                            else:
                                failed_count += 1
                        
                        # Callback'i geri yükle
                        backend_instance.on_data_updated = original_callback
                        
                        # Tabloyu yenile
                        table_container.content = create_invoice_table_content(
                            state.get("invoice_sort_option", "newest"),
                            state.get("invoice_type", "income"),
                            on_select_changed=update_selected_count
                        )
                        clear_inputs()
                        
                        # Callback'i manuel olarak tetikle (tek seferde tüm güncellemeleri yap)
                        if original_callback:
                            original_callback()
                        
                        # Bildirim göster
                        if deleted_count > 0:
                            message = f"✅ {deleted_count} fatura silindi!"
                            if failed_count > 0:
                                message += f" ({failed_count} başarısız)"
                            page.snack_bar = ft.SnackBar(
                                content=ft.Text(message, color=col_white),
                                bgcolor=col_success
                            )
                        else:
                            page.snack_bar = ft.SnackBar(
                                content=ft.Text("❌ Hiçbir fatura silinemedi!", color=col_white),
                                bgcolor=col_danger
                            )
                        page.snack_bar.open = True
                        page.update()
                        
                    except Exception as ex:
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"❌ Silme hatası: {str(ex)}", color=col_white),
                            bgcolor=col_danger
                        )
                        page.snack_bar.open = True
                        page.update()

                # Mesajı belirle
                msg = f"Seçili {selected_count} faturayı silmek istediğinize emin misiniz?"
                if selected_count == 1:
                    msg = "Seçili faturayı silmek istediğinize emin misiniz?"

                # Dialog oluştur ve göster
                dlg_modal = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Silme Onayı"),
                    content=ft.Text(msg),
                    actions=[
                        ft.ElevatedButton("Evet", on_click=confirm_delete, bgcolor=col_success, color=col_white),
                        ft.ElevatedButton("Hayır", on_click=close_dlg, bgcolor=col_danger, color=col_white),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )

                # Dialog'u sayfaya ekle (overlay veya dialog property ile)
                page.overlay.append(dlg_modal)
                dlg_modal.open = True
                page.update()
            
            except Exception as ex:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Hata: {str(ex)}", color=col_white),
                    bgcolor=col_danger
                )
                page.snack_bar.open = True
                page.update()

        def process_qr_folder(e):
            """QR kodları okuyup faturalara aktar"""
            try:
                # Klasör seçme dialogu
                def on_folder_selected(e: ft.FilePickerResultEvent):
                    try:
                        
                        if not e.path:
                            return
                        
                        folder_path = e.path
                        
                        # Dialog referansı için
                        type_dialog = None
                        
                        # QR işleme (thread'de) - Tip seçildikten sonra çalışacak
                        def process_in_thread(selected_type):
                            try:
                                
                                # İlerleme dialogu oluştur (burada oluşturuyoruz ki thread başlamadan görünsün)
                                # Not: Flet'te UI güncellemeleri ana thread'de olmalı, bu yüzden dialogu 
                                # on_type_selected içinde açacağız, burada sadece güncelleme yapacağız.
                                
                                # QR dosyalarını oku
                                results = backend_instance.process_qr_files_in_folder(
                                    folder_path,
                                    max_workers=6,
                                    status_callback=status_callback
                                )
                                
                                
                                if not results:
                                    progress_dialog.open = False
                                    page.snack_bar = ft.SnackBar(
                                        content=ft.Text("❌ Klasörde işlenebilir dosya bulunamadı!", color=col_white),
                                        bgcolor=col_danger
                                    )
                                    page.snack_bar.open = True
                                    page.update()
                                    return
                                
                                # Backend'e aktar - backend metodu kullan
                                summary = backend_instance.add_invoices_from_qr_data(
                                    results,
                                    selected_type
                                )
                                
                                # Dialog içeriğini güncelle (Kapatma)
                                progress_dialog.title = ft.Text("İşlem Tamamlandı", weight="bold")
                                
                                summary_text = (
                                    f"Toplam Dosya: {summary['total']}\n"
                                    f"Başarılı: {summary['added']}\n"
                                    f"Başarısız: {summary['failed']}\n"
                                    f"Mükerrer (Atlanan): {summary['skipped_duplicates']}\n"
                                    f"İşlem Tipi: {'GELİR' if selected_type == 'outgoing' else 'GIDER'}"
                                )
                                
                                def close_dlg(e):
                                    progress_dialog.open = False
                                    page.update()

                                progress_dialog.content = ft.Container(
                                    width=450,
                                    height=180,
                                    content=ft.Column([
                                        ft.Text(summary_text, size=15, color=col_text),
                                        ft.Container(height=20),
                                        ft.Row([
                                            ft.ElevatedButton("Tamam", on_click=close_dlg, bgcolor=col_primary, color=col_white)
                                        ], alignment=ft.MainAxisAlignment.END)
                                    ])
                                )
                                # Actions varsa temizle
                                progress_dialog.actions = []
                                
                                page.update()
                                
                                # Tabloyu güncelle
                                update_invoice_table(state.get("invoice_sort_option", "newest"))

                                
                            except Exception as ex:
                                error_detail = traceback.format_exc()
                                
                                progress_dialog.open = False
                                page.snack_bar = ft.SnackBar(
                                    content=ft.Text(f"QR isleme hatasi: {str(ex)}", color=col_white),
                                    bgcolor=col_danger,
                                    duration=5000
                                )
                                page.snack_bar.open = True
                                page.update()

                        # İlerleme dialogu ve callback tanımları
                        progress_bar = ft.ProgressBar(width=400, value=0)
                        progress_text = ft.Text("QR kodları okunuyor...", size=14, color=col_text)
                        
                        progress_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("QR Kod İşleme", weight="bold"),
                            content=ft.Container(
                                width=450,
                                height=120,
                                content=ft.Column([
                                    progress_text,
                                    ft.Container(height=10),
                                    progress_bar
                                ])
                            )
                        )
                        
                        def status_callback(message, progress):
                            progress_text.value = message
                            progress_bar.value = progress / 100
                            page.update()
                            return True

                        # Fatura tipi seçme dialogu callback'i
                        def on_type_selected(invoice_type):
                            
                            # BottomSheet'i kapat (eğer bs referansı varsa)
                            # Not: bs referansı aşağıda tanımlanıyor, lambda içinde closure olarak gelecek
                            
                            # Progress dialogu aç
                            page.overlay.append(progress_dialog)
                            progress_dialog.open = True
                            page.update()
                            
                            # Thread'i başlat
                            threading.Thread(target=process_in_thread, args=(invoice_type,), daemon=True).start()
                    
                        # Kompakt BottomSheet ile tip seçme
                        
                        def close_bs(bs):
                            bs.open = False
                            page.update()
                        
                        # BottomSheet tanımla
                        bs = ft.BottomSheet(
                            content=ft.Container(
                                padding=20,
                                bgcolor="#1A1D1F", # col_dark yerine hardcoded, col_dark tanımlı olmayabilir
                                content=ft.Column([
                                    ft.Text("Fatura Tipi Seçin", size=20, weight="bold", color=col_white),
                                    ft.Container(height=10),
                                    ft.ElevatedButton(
                                        content=ft.Row([
                                            ft.Icon(ft.Icons.ARROW_DOWNWARD, color=col_white),
                                            ft.Text("GELİR (Satış Faturası)", color=col_white, size=16)
                                        ], tight=True),
                                        on_click=lambda _: (close_bs(bs), on_type_selected('outgoing')),
                                        bgcolor=col_success,
                                        width=300,
                                        height=60
                                    ),
                                    ft.Container(height=10),
                                    ft.ElevatedButton(
                                        content=ft.Row([
                                            ft.Icon(ft.Icons.ARROW_UPWARD, color=col_white),
                                            ft.Text("GİDER (Alış Faturası)", color=col_white, size=16)
                                        ], tight=True),
                                        on_click=lambda _: (close_bs(bs), on_type_selected('incoming')),
                                        bgcolor=col_danger,
                                        width=300,
                                        height=60
                                    ),
                                    ft.Container(height=10),
                                    ft.TextButton(
                                        "İptal",
                                        on_click=lambda _: close_bs(bs)
                                    )
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=0)
                            ),
                            open=True,
                            on_dismiss=lambda _: None
                        )
                        
                        page.overlay.append(bs)
                        page.update()
                        
                    except Exception as dialog_error:
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"Dialog hatasi: {str(dialog_error)}", color=col_white),
                            bgcolor=col_danger
                        )
                        page.snack_bar.open = True
                        page.update()
                
                # Klasör seçici
                file_picker = ft.FilePicker(on_result=on_folder_selected)
                page.overlay.append(file_picker)
                page.update()
                file_picker.get_directory_path(dialog_title="QR PDF/Resim Klasörünü Seç")
                
            except Exception as ex:
                error_detail = traceback.format_exc()
                
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"QR okuma hatasi: {str(ex)}", color=col_white),
                    bgcolor=col_danger
                )
                page.snack_bar.open = True
                page.update()

        def backup_database(e):
            """Veritabanını yedekle"""
            try:
                from backup import LocalBackupManager
                manager = LocalBackupManager()
                default_filename = manager.get_default_filename()
                
                def on_save_result(e: ft.FilePickerResultEvent):
                    if e.path:
                        file_path = e.path
                        success, msg = manager.create_backup(file_path)
                        
                        if success:
                            def close_success_dlg(e):
                                success_dlg.open = False
                                page.update()

                            success_dlg = ft.AlertDialog(
                                modal=True,
                                title=ft.Text("Yedekleme Başarılı"),
                                content=ft.Text(msg),
                                actions=[
                                    ft.ElevatedButton("Tamam", on_click=close_success_dlg, bgcolor=col_primary, color=col_white),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(success_dlg)
                            success_dlg.open = True
                            page.update()
                        else:
                            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ {msg}", color=col_white), bgcolor=col_danger)
                            page.snack_bar.open = True
                            page.update()

                save_file_picker = ft.FilePicker(on_result=on_save_result)
                page.overlay.append(save_file_picker)
                page.update()
                save_file_picker.save_file(dialog_title="Yedek Dosyasını Kaydet", file_name=default_filename, allowed_extensions=["zip"])
                
            except Exception as ex:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Yedekleme hatası: {str(ex)}", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()

        def export_to_excel(e):
            """Faturalari Excel'e aktar"""
            try:
                current_invoice_type = state.get("invoice_type", "income")
                db_type = 'outgoing' if current_invoice_type == 'income' else 'incoming'
                
                invoices = backend_instance.handle_invoice_operation(
                    operation='get',
                    invoice_type=db_type,
                    limit=1000
                )
                
                if not invoices:
                    page.snack_bar = ft.SnackBar(content=ft.Text("❌ Dışa aktarılacak fatura bulunamadı!", color=col_white), bgcolor=col_danger)
                    page.snack_bar.open = True
                    page.update()
                    return
                
                def on_save_result(e: ft.FilePickerResultEvent):
                    if e.path:
                        file_path = e.path
                        type_name = "GelirFaturalari" if current_invoice_type == "income" else "GiderFaturalari"
                        
                        # Excel'e aktar
                        from toexcel import InvoiceExcelExporter
                        excel_exporter = InvoiceExcelExporter()
                        success = excel_exporter.export_invoices_to_excel(invoices, type_name, file_path)
                        
                        if success:
                            def close_success_dlg(e):
                                success_dlg.open = False
                                page.update()

                            success_dlg = ft.AlertDialog(
                                modal=True,
                                title=ft.Text("Başarılı"),
                                content=ft.Text(f"Dosya başarıyla kaydedildi:\n{file_path}"),
                                actions=[
                                    ft.ElevatedButton("Tamam", on_click=close_success_dlg, bgcolor=col_primary, color=col_white),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(success_dlg)
                            success_dlg.open = True
                            page.update()
                        else:
                            page.snack_bar = ft.SnackBar(content=ft.Text("❌ Excel aktarımı başarısız!", color=col_white), bgcolor=col_danger)
                            page.snack_bar.open = True
                            page.update()

                # Dosya yolu oluştur
                type_name = "GelirFaturalari" if current_invoice_type == "income" else "GiderFaturalari"
                timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                filename = f"{type_name}_{timestamp}.xlsx"
                
                save_file_picker = ft.FilePicker(on_result=on_save_result)
                page.overlay.append(save_file_picker)
                page.update()
                save_file_picker.save_file(dialog_title="Excel Dosyasını Kaydet", file_name=filename, allowed_extensions=["xlsx"])
                    
            except Exception as ex:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Excel hatası: {str(ex)}", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()

        def export_to_pdf(e):
            """Faturalari PDF'e aktar"""
            try:
                current_invoice_type = state.get("invoice_type", "income")
                db_type = 'outgoing' if current_invoice_type == 'income' else 'incoming'
                
                invoices = backend_instance.handle_invoice_operation(
                    operation='get',
                    invoice_type=db_type,
                    limit=1000
                )
                
                if not invoices:
                    page.snack_bar = ft.SnackBar(content=ft.Text("❌ Dışa aktarılacak fatura bulunamadı!", color=col_white), bgcolor=col_danger)
                    page.snack_bar.open = True
                    page.update()
                    return
                
                def on_save_result(e: ft.FilePickerResultEvent):
                    if e.path:
                        file_path = e.path
                        
                        # PDF'e aktar
                        from topdf import InvoicePDFExporter
                        pdf_exporter = InvoicePDFExporter()
                        success = pdf_exporter.export_invoices_to_pdf(invoices, db_type, file_path)
                        
                        if success:
                            def close_success_dlg(e):
                                success_dlg.open = False
                                page.update()

                            success_dlg = ft.AlertDialog(
                                modal=True,
                                title=ft.Text("Başarılı"),
                                content=ft.Text(f"Dosya başarıyla kaydedildi:\n{file_path}"),
                                actions=[
                                    ft.ElevatedButton("Tamam", on_click=close_success_dlg, bgcolor=col_primary, color=col_white),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(success_dlg)
                            success_dlg.open = True
                            page.update()
                        else:
                            page.snack_bar = ft.SnackBar(content=ft.Text("❌ PDF aktarımı başarısız!", color=col_white), bgcolor=col_danger)
                            page.snack_bar.open = True
                            page.update()

                # Dosya yolu oluştur
                type_name = "GelirFaturalari" if current_invoice_type == "income" else "GiderFaturalari"
                timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                filename = f"{type_name}_{timestamp}.pdf"
                
                save_file_picker = ft.FilePicker(on_result=on_save_result)
                page.overlay.append(save_file_picker)
                page.update()
                save_file_picker.save_file(dialog_title="PDF Dosyasını Kaydet", file_name=filename, allowed_extensions=["pdf"])
                    
            except Exception as ex:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ PDF hatası: {str(ex)}", color=col_white), bgcolor=col_danger)
                page.snack_bar.open = True
                page.update()

        # Butonları oluştur
        btn_clear = AestheticButton("Yeni / Temizle", "refresh", "#7F8C8D", width=145, on_click=clear_inputs)
        btn_add = AestheticButton("Ekle", "add", col_success, width=110, on_click=add_invoice)
        btn_update = AestheticButton("Güncelle", "update", col_blue_donut, width=125, on_click=update_invoice)
        
        # Sil butonu - seçili sayı ile
        btn_delete_container = ft.Row([
            AestheticButton("Sil", "delete", col_danger, width=110, on_click=delete_invoice),
            selected_count_text
        ], spacing=5, alignment=ft.MainAxisAlignment.START)
        
        operation_buttons = ft.Row([btn_clear, btn_add, btn_update, btn_delete_container], spacing=15)

        # Sağ üst butonlar - QR, Excel, PDF export
        btn_qr = ScaleButton("qr_code_scanner", "#3498DB", "QR Okuma / Klasör Ekle", width=50, height=45)
        btn_qr.on_click = process_qr_folder
        
        btn_excel = ScaleButton("table_view", "#217346", "Excel Olarak İndir", width=50, height=45)
        btn_excel.on_click = export_to_excel
        
        btn_pdf = ScaleButton("picture_as_pdf", "#D32F2F", "PDF Olarak İndir", width=50, height=45)
        btn_pdf.on_click = export_to_pdf
        
        right_buttons_row = ft.Row([btn_qr, btn_excel, btn_pdf], spacing=10)
        
        right_buttons_container = ft.Container(content=right_buttons_row, padding=ft.padding.only(right=25))

        sort_dropdown = ft.Container(padding=ft.padding.only(left=20), content=ft.Dropdown(options=[ft.dropdown.Option("newest", "Son Eklenen"), ft.dropdown.Option("date_desc", "Yeniden Eskiye"), ft.dropdown.Option("date_asc", "Eskiden Yeniye")], value="newest", on_change=on_sort_change, width=160, text_size=13, label="Sıralama", border_radius=10, content_padding=10, bgcolor=col_white, border_color=col_border))

        # Backup butonu
        btn_backup = ScaleButton("backup", "#8E44AD", "Veritabanını Yedekle", width=50, height=45)
        btn_backup.on_click = backup_database

        controls_row = ft.Row([type_toggle_btn, sort_dropdown, btn_backup, ft.Container(expand=True), right_buttons_container], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Input satırları - TextField referanslarını kullan
        input_line_1 = ft.Row([
            ft.Column([ft.Text("Fatura No", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_fatura_no, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Column([ft.Text("Tarih", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_tarih, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Column([ft.Text("Firma", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_firma, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Column([ft.Text("Malzeme/Hizmet", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_malzeme, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1)
        ], spacing=15)
        
        input_line_2 = ft.Row([
            ft.Column([ft.Text("Miktar", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_miktar, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Column([ft.Text("Tutar", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_tutar, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Column([ft.Text("Para Birimi", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_para_birimi, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Column([ft.Text("KDV Tutarı", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_kdv, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1)
        ], spacing=15)
        
        # Manuel döviz kuru satırı (opsiyonel)
        input_line_3 = ft.Row([
            ft.Column([ft.Text("USD Kuru (1 USD = ? TL)", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_usd_kur, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Column([ft.Text("EUR Kuru (1 EUR = ? TL)", size=12, weight="w500", color=col_text_secondary), ft.Container(content=input_eur_kur, bgcolor=col_card, border_radius=6, height=42, border=ft.border.all(1, "#E0E0E0"))], spacing=5, expand=1),
            ft.Container(expand=3)  # Boş alan
        ], spacing=15)

        return ft.Container(alignment=ft.alignment.top_center, padding=30, content=ft.Column([
            ft.Row([ft.Text("Fatura Yönetimi", size=28, weight="bold", color=col_text)]),
            ft.Container(height=15), ft.Container(content=controls_row), ft.Container(height=20),
            ft.Container(content=ft.Column([input_line_1, ft.Container(height=5), input_line_2, ft.Container(height=5), input_line_3], spacing=10)),
            ft.Container(height=10), ft.Container(content=operation_buttons, alignment=ft.alignment.center_left, padding=ft.padding.only(left=15)),
            ft.Container(height=20),
            table_container, 
            ft.Container(height=50), 
            ft.Container(content=general_expenses_section)
        ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH, scroll=ft.ScrollMode.AUTO), expand=True)

    # ------------------------------------------------------------------------
    # SAYFA YÖNETİMİ VE NAVİGASYON (Page Management & Navigation)
    # ------------------------------------------------------------------------
    # Sayfa Yöneticisi
    dashboard_content = ft.Container() 
    faturalar_page = create_invoices_page()
    donemsel_page = create_donemsel_page()
    
    def change_view(e):
        clicked_btn_data = e.control.data
        
        if state["current_page"] == "home" and clicked_btn_data != "home":
             state["animation_completed"] = True 
        
        state["current_page"] = clicked_btn_data
        
        # Nested Column yapısında butonları güncelle
        for col in sidebar_column.controls:
            if isinstance(col, ft.Column):
                for btn in col.controls:
                    if isinstance(btn, SidebarButton):
                        btn.is_selected = (btn.data == clicked_btn_data)
                        btn.update_visuals()
        
        if clicked_btn_data == "home":
            content_area.content = dashboard_content
            # Ana sayfa yüklendiğinde verileri güncelle - Animasyondan ÖNCE
            if state["update_callbacks"]["home_page"]:
                state["update_callbacks"]["home_page"]()
            threading.Thread(target=start_animations, daemon=True).start()
        elif clicked_btn_data == "faturalar":
            state["current_page"] = "invoices"  # Fatura sayfası için doğru key
            content_area.content = faturalar_page
            # Fatura sayfası yüklendiğinde tabloyu güncelle
            if state["update_callbacks"]["invoice_page"]:
                state["update_callbacks"]["invoice_page"]()
        elif clicked_btn_data == "raporlar":
            state["current_page"] = "donemsel"  # Dönemsel sayfa için doğru key
            content_area.content = donemsel_page
            # Dönemsel sayfa yüklendiğinde tabloyu güncelle
            if state["update_callbacks"]["donemsel_page"]:
                state["update_callbacks"]["donemsel_page"]()
        
        content_area.update()

    
    logo_text = ft.Text("Excellent", size=24, weight="bold", color=col_text)
    logo_text2 = ft.Text("with Rust", size=10, weight="normal", color=col_text)
    menu_icon = ft.IconButton(icon="menu", icon_color=col_text, on_click=toggle_sidebar)
    logo_column = ft.Column([logo_text, logo_text2], spacing=0, visible=False, alignment=ft.MainAxisAlignment.CENTER)
    menu_row = ft.Row([menu_icon, logo_column], spacing=5, alignment=ft.MainAxisAlignment.CENTER)

    btn_home = SidebarButton("home_rounded", "Giriş", "home", False)  # Başlangıçta False
    btn_faturalar = SidebarButton("receipt_long_rounded", "Faturalar", "faturalar")
    btn_raporlar = SidebarButton("bar_chart_rounded", "Raporlar", "raporlar")
    btn_home.on_click = change_view
    btn_faturalar.on_click = change_view
    btn_raporlar.on_click = change_view
    
    # Ev butonunu başlangıçta seçili yap
    btn_home.is_selected = True
    btn_home.update_visuals(run_update=False)

    # Sidebar'ı MainAxisAlignment.SPACE_BETWEEN ile düzenle - Ayarlar en altta
    sidebar_column = ft.Column([
        ft.Column([
            ft.Container(height=20),
            menu_row,
            ft.Container(height=30),
            btn_home,
            btn_faturalar,
            btn_raporlar
        ], spacing=15),
        ft.Column([
            ft.Container(height=20)
        ], spacing=15)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    sidebar_container = ft.Container(width=90, height=900, bgcolor=col_white, padding=ft.padding.symmetric(horizontal=15, vertical=20), content=sidebar_column, animate=ft.Animation(300, "easeOut"), shadow=ft.BoxShadow(blur_radius=10, color="#05000000"))

    # ------------------------------------------------------------------------
    # DASHBOARD İÇERİK VE YARDIMCILARI (Dashboard Content & Helpers)
    # ------------------------------------------------------------------------
    # --- DASHBOARD İÇERİK ---
    def change_currency(currency_code):
        state["current_currency"] = currency_code
        currency_selector_container.content = create_currency_selector()
        currency_selector_container.update()
        
        # Grafikleri ve verileri güncelle
        refresh_charts_and_data()

    def create_currency_selector():
        curr = state["current_currency"]
        return ft.Container(bgcolor=col_bg, border_radius=12, padding=4, content=ft.Row([currency_button("₺ TRY", "TRY", curr, change_currency), currency_button("$ USD", "USD", curr, change_currency), currency_button("€ EUR", "EUR", curr, change_currency)], spacing=0, tight=True))
    currency_selector_container = ft.Container(content=create_currency_selector())

    # Kur bilgisi text'i dinamik olarak oluştur
    exchange_rate_text = ft.Text(get_exchange_rate_display(), size=13, color=col_text_light, weight="w600")
    
    header = ft.Row([ft.Text("Genel Durum Paneli", size=26, weight="bold", color=col_text), ft.Row([ft.Container(bgcolor="#EAF2F8", padding=ft.padding.symmetric(horizontal=15, vertical=10), border_radius=8, content=ft.Row([ft.Icon("currency_exchange", size=16, color=col_blue_donut), exchange_rate_text], spacing=10)), currency_selector_container], spacing=20)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # Backend'den gerçek verileri çek
    def get_dashboard_stats(year=None):
        """Dashboard için istatistikleri hesapla - isteğe bağlı yıl filtresi"""
        try:
            # Seçili para birimini belirle
            current_currency = state.get("current_currency", "TRY")
            amount_field = "toplam_tutar_tl"
            if current_currency == "USD":
                amount_field = "toplam_tutar_usd"
            elif current_currency == "EUR":
                amount_field = "toplam_tutar_eur"
                
            # Giden faturalar (Gelir)
            income_invoices = backend_instance.handle_invoice_operation(
                operation='get',
                invoice_type='outgoing',
                limit=1000,
                offset=0
            ) or []
            
            # Gelen faturalar (Gider)
            expense_invoices = backend_instance.handle_invoice_operation(
                operation='get',
                invoice_type='incoming',
                limit=1000,
                offset=0
            ) or []
            
            # Eğer yıl filtresi varsa, sadece o yıla ait faturaları al
            if year:
                income_invoices = [inv for inv in income_invoices if inv.get('tarih', '').endswith(str(year))]
                expense_invoices = [inv for inv in expense_invoices if inv.get('tarih', '').endswith(str(year))]
            
            # Toplam gelir
            total_income = sum(float(inv.get(amount_field, 0)) for inv in income_invoices)
            
            # Toplam gider
            total_expense = sum(float(inv.get(amount_field, 0)) for inv in expense_invoices)
            
            # Genel giderleri ekle
            if year:
                general_expenses = backend_instance.db.get_yearly_expenses(year)
                if general_expenses:
                    month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
                    for month_key in month_keys:
                        if month_key in general_expenses:
                            general_amount_tl = float(general_expenses[month_key] or 0)
                            
                            # Para birimine göre çevir
                            general_amount = general_amount_tl
                            if current_currency != "TRY":
                                general_amount = backend_instance.convert_currency(general_amount_tl, "TRY", current_currency)
                                
                            total_expense += general_amount
            
            # Net kâr
            net_profit = total_income - total_expense
            
            # Aylık ortalama (son 12 ay gelir ortalaması)
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # Eğer seçili yıl geçmiş yılsa, 12 aya böl
            if year and year < current_year:
                monthly_avg = total_income / 12
            else:
                monthly_avg = total_income / max(current_month, 1)
            
            return {
                'net_profit': net_profit,
                'total_income': total_income,
                'total_expense': total_expense,
                'monthly_avg': monthly_avg,
                'income_count': len(income_invoices),
                'expense_count': len(expense_invoices)
            }
        except Exception as e:
            return {
                'net_profit': 0,
                'total_income': 0,
                'total_expense': 0,
                'monthly_avg': 0,
                'income_count': 0,
                'expense_count': 0
            }
    
    # İstatistikleri al
    stats = get_dashboard_stats()
    
    # Trend hesapla (basit - önceki aya göre %15 artış varsayımı)
    net_profit_trend = "+15%" if stats['net_profit'] > 0 else "0%"
    income_trend = "+4%" if stats['total_income'] > 0 else "0%"
    expense_trend = "-2%" if stats['total_expense'] > 0 else "0%"
    avg_trend = "+1%" if stats['monthly_avg'] > 0 else "0%"
    
    # Her donut için kendi max değerini hesapla (değerin %120'si, min 10K)
    profit_max = max(abs(stats['net_profit']) * 1.2, 10000)
    income_max = max(stats['total_income'] * 1.2, 10000)
    expense_max = max(stats['total_expense'] * 1.2, 10000)
    avg_max = max(stats['monthly_avg'] * 1.2, 10000)
    
    current_currency = state.get("current_currency", "TRY")

    stats_row = ft.Row([
        DonutStatCard("Anlık Net Kâr", "attach_money", col_blue_donut, net_profit_trend, 
                     abs(stats['net_profit']), profit_max, format_currency(stats['net_profit'], currency=current_currency, compact=True)),
        DonutStatCard("Toplam Gelir", "arrow_upward", col_success, income_trend, 
                     stats['total_income'], income_max, format_currency(stats['total_income'], currency=current_currency, compact=True)),
        DonutStatCard("Toplam Gider", "arrow_downward", col_secondary, expense_trend, 
                     stats['total_expense'], expense_max, format_currency(stats['total_expense'], currency=current_currency, compact=True)),
        DonutStatCard("Aylık Ortalama", "pie_chart", "#FF5B5B", avg_trend, 
                     stats['monthly_avg'], avg_max, format_currency(stats['monthly_avg'], currency=current_currency, compact=True))
    ], spacing=20)
    
    # Son işlemleri backend'den çek
    def get_recent_transactions():
        """Son işlem geçmişini getir"""
        try:
            # İşlem geçmişinden son kayıtları al
            history_records = backend_instance.get_recent_history(limit=10)
            return _process_history_records(history_records)
        except Exception as e:
            return []
    
    def _process_history_records(records):
        """Geçmiş kayıtlarını transaction formatına çevirir"""
        transactions = []
        
        for record in records:
            operation_type = record.get('operation_type', '')
            invoice_type = record.get('invoice_type', '')
            
            # Gelir mi gider mi?
            is_income = (invoice_type == 'gelir' or invoice_type == 'outgoing')
            
            # İşlem tipi kontrolü
            is_updated = (operation_type == 'GÜNCELLEME')
            is_deleted = (operation_type == 'SİLME')
            
            # Tarih ve saat
            op_date = record.get('operation_date', '')
            op_time = record.get('operation_time', '')
            display_date = f"{op_date} {op_time}"
            
            # Fatura tarihi
            invoice_date = record.get('invoice_date', '')
            
            # Başlık (Firma veya Detay)
            title = record.get('firma')
            if not title or title == 'None':
                title = record.get('details', 'İşlem')
            
            # Tutar
            amount_val = record.get('amount')
            if amount_val:
                try:
                    amount_str = f"{float(amount_val):,.2f}"
                except:
                    amount_str = str(amount_val)
            else:
                amount_str = "0.00"
            
            transactions.append({
                'title': title,
                'display_date': display_date,
                'invoice_date': invoice_date,
                'amount': amount_str,
                'income': is_income,
                'is_updated': is_updated,
                'is_deleted': is_deleted
            })
        
        return transactions
    
    transactions_column = ft.Column(spacing=5, scroll=ft.ScrollMode.ALWAYS, expand=True)
    current_filter_date = None  # Aktif tarih filtresini sakla

    def update_transactions(filter_date=None):
        """Geçmiş işlemleri günceller - filtre varsa veritabanından çeker"""
        nonlocal current_filter_date
        
        # Eğer parametre verilmediyse, mevcut filtreyi kullan
        if filter_date is None and current_filter_date is not None:
            filter_date = current_filter_date
        else:
            current_filter_date = filter_date
        
        transactions_column.controls.clear()
        filtered_data = []
        
        if filter_date:
            # Tarih filtresi varsa veritabanından o tarihteki işlemleri çek
            str_date = filter_date.strftime("%d.%m.%Y")
            
            # O tarihteki işlemleri getir
            history_records = backend_instance.get_history_by_date_range(str_date, str_date)
            filtered_data = _process_history_records(history_records)
        else:
            # Filtre yoksa son işlemleri yeniden çek
            filtered_data = get_recent_transactions()

        if not filtered_data:
            transactions_column.controls.append(ft.Container(content=ft.Text("Bu tarihte işlem bulunamadı.", color=col_text_light), alignment=ft.alignment.center, padding=20))
        else:
            for t in filtered_data:
                transactions_column.controls.append(
                    TransactionRow(
                        t["title"], 
                        t["display_date"], 
                        t["amount"], 
                        t["income"],
                        is_updated=t.get("is_updated", False),
                        is_deleted=t.get("is_deleted", False),
                        invoice_date=t.get("invoice_date")
                    )
                )
        
        try:
            if transactions_column.page: 
                transactions_column.update()
        except:
            pass

    update_transactions()

    def handle_date_change(e):
        if e.control.value: update_transactions(e.control.value)

    # Özel Türkçe tarih seçici dialog
    date_input_field = ft.TextField(
        hint_text="ggaayy veya gg.aa.yyyy (örn. 121225)",
        hint_style=ft.TextStyle(color="#D0D0D0", size=12),
        text_size=14,
        color=col_text,
        border_color=col_border,
        focused_border_color=col_primary,
        border_radius=8,
        content_padding=ft.padding.symmetric(horizontal=15, vertical=12),
        width=280
    )
    
    date_dialog_error = ft.Text("", color=col_danger, size=12, visible=False)
    
    def close_date_dialog(e):
        date_dialog.open = False
        date_input_field.value = ""
        date_dialog_error.visible = False
        page.update()
    
    def apply_date_filter(e):
        """Girilen tarihi parse edip filtrele"""
        input_val = date_input_field.value
        if not input_val or not input_val.strip():
            date_dialog_error.value = "Lütfen bir tarih girin"
            date_dialog_error.visible = True
            page.update()
            return
        
        # Tarihi formatla
        formatted = format_date_input(input_val.strip())
        
        # Geçerli tarih mi kontrol et
        try:
            parts = formatted.split('.')
            if len(parts) == 3:
                gun, ay, yil = int(parts[0]), int(parts[1]), int(parts[2])
                selected_date = datetime(yil, ay, gun)
                
                # Dialog'u kapat ve filtrele
                date_dialog.open = False
                date_input_field.value = ""
                date_dialog_error.visible = False
                page.update()
                
                update_transactions(selected_date)
            else:
                raise ValueError("Geçersiz format")
        except (ValueError, IndexError):
            date_dialog_error.value = "Geçersiz tarih! Örn: 121225 veya 12.12.2025"
            date_dialog_error.visible = True
            page.update()
    
    # Türkçe ay isimleri ile takvim görünümü için basit bir seçici
    TURKISH_MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                      "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    
    current_cal_year = datetime.now().year
    current_cal_month = datetime.now().month
    
    def get_month_days(year, month):
        """Ayın gün sayısını döndür"""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        return (next_month - datetime(year, month, 1)).days
    
    def select_day(day, year, month):
        """Gün seçildiğinde"""
        def handler(e):
            selected_date = datetime(year, month, day)
            date_dialog.open = False
            date_input_field.value = ""
            date_dialog_error.visible = False
            page.update()
            update_transactions(selected_date)
        return handler
    
    calendar_grid = ft.Column(spacing=5)
    month_year_text = ft.Text("", size=16, weight="bold", color=col_text)
    
    def build_calendar(year, month):
        """Takvim grid'ini oluştur"""
        nonlocal current_cal_year, current_cal_month
        current_cal_year = year
        current_cal_month = month
        
        month_year_text.value = f"{TURKISH_MONTHS[month-1]} {year}"
        
        calendar_grid.controls.clear()
        
        # Gün başlıkları
        day_headers = ft.Row(
            [ft.Container(
                width=35, height=25,
                content=ft.Text(d, size=11, weight="bold", color=col_text_light, text_align=ft.TextAlign.CENTER),
                alignment=ft.alignment.center
            ) for d in ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=2
        )
        calendar_grid.controls.append(day_headers)
        
        # Ayın ilk gününün haftanın hangi günü olduğunu bul (0=Pazartesi)
        first_day = datetime(year, month, 1)
        start_weekday = first_day.weekday()
        
        # Ayın toplam gün sayısı
        total_days = get_month_days(year, month)
        
        # Takvim satırlarını oluştur
        day_num = 1
        for week in range(6):  # Max 6 hafta
            if day_num > total_days:
                break
            
            week_row = []
            for weekday in range(7):
                if week == 0 and weekday < start_weekday:
                    # Boş hücre
                    week_row.append(ft.Container(width=35, height=30))
                elif day_num <= total_days:
                    # Bugün mü kontrol et
                    is_today = (year == datetime.now().year and 
                               month == datetime.now().month and 
                               day_num == datetime.now().day)
                    
                    day_btn = ft.Container(
                        width=35, height=30,
                        bgcolor=col_primary if is_today else None,
                        border_radius=5,
                        content=ft.Text(
                            str(day_num), 
                            size=12, 
                            color=col_white if is_today else col_text,
                            text_align=ft.TextAlign.CENTER
                        ),
                        alignment=ft.alignment.center,
                        on_click=select_day(day_num, year, month),
                        ink=True
                    )
                    week_row.append(day_btn)
                    day_num += 1
                else:
                    week_row.append(ft.Container(width=35, height=30))
            
            calendar_grid.controls.append(
                ft.Row(week_row, alignment=ft.MainAxisAlignment.CENTER, spacing=2)
            )
        
        if calendar_grid.page:
            calendar_grid.update()
            month_year_text.update()
    
    def prev_month(e):
        nonlocal current_cal_year, current_cal_month
        if current_cal_month == 1:
            current_cal_month = 12
            current_cal_year -= 1
        else:
            current_cal_month -= 1
        build_calendar(current_cal_year, current_cal_month)
    
    def next_month(e):
        nonlocal current_cal_year, current_cal_month
        if current_cal_month == 12:
            current_cal_month = 1
            current_cal_year += 1
        else:
            current_cal_month += 1
        build_calendar(current_cal_year, current_cal_month)
    
    # İlk takvimi oluştur
    build_calendar(current_cal_year, current_cal_month)
    
    date_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Tarih Seçin", weight="bold", size=18),
        content=ft.Container(
            width=320,
            content=ft.Column([
                # Manuel tarih girişi
                ft.Text("Tarih Girin:", size=13, color=col_text_secondary),
                date_input_field,
                date_dialog_error,
                ft.Container(height=5),
                ft.ElevatedButton(
                    "Tarihe Git",
                    icon="search",
                    bgcolor=col_primary,
                    color=col_white,
                    on_click=apply_date_filter,
                    width=280
                ),
                ft.Divider(height=20),
                # Takvim görünümü
                ft.Text("veya Takvimden Seçin:", size=13, color=col_text_secondary),
                ft.Container(height=5),
                ft.Row([
                    ft.IconButton(icon="chevron_left", on_click=prev_month, icon_color=col_primary),
                    month_year_text,
                    ft.IconButton(icon="chevron_right", on_click=next_month, icon_color=col_primary)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                calendar_grid
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),
        actions=[
            ft.TextButton("İptal", on_click=close_date_dialog, style=ft.ButtonStyle(color=col_text_light))
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    page.overlay.append(date_dialog)
    
    def open_date_dialog(e):
        # Takvimi bugünün tarihine sıfırla
        build_calendar(datetime.now().year, datetime.now().month)
        date_dialog.open = True
        page.update()

    def reset_transactions(e): update_transactions(None)

    transactions_list_content = ft.Column([ft.Row([ft.Text("Son İşlemler", size=18, weight="bold", color=col_text), ft.Row([ft.IconButton(icon="calendar_month", icon_color=col_text_light, tooltip="Tarihe Göre Git", on_click=open_date_dialog), ft.TextButton("En Son Girilenler", style=ft.ButtonStyle(color=col_primary), on_click=reset_transactions)])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(height=15), transactions_column], spacing=5)

    transactions_list = ft.Container(bgcolor=col_white, border_radius=20, padding=25, shadow=ft.BoxShadow(blur_radius=20, color="#08000000"), height=450, content=transactions_list_content)

    # Yıl dropdown'ı için dinamik seçenekler oluştur - tüm veritabanı yıllarını çek
    available_years = get_all_available_years()
    year_dropdown_options = [ft.dropdown.Option(str(year)) for year in available_years]
    default_year = str(available_years[0]) if available_years else str(datetime.now().year)
    
    # Dropdown'ı değişkene ata (refresh fonksiyonunda kullanmak için)
    year_dropdown_ref = ft.Dropdown(width=100, options=year_dropdown_options, value=default_year, on_change=on_year_change, border_radius=10, text_size=13, content_padding=10)
    
    chart_container = ft.Container(bgcolor=col_white, border_radius=20, padding=ft.padding.only(left=30, right=30, top=30, bottom=10), expand=2, shadow=ft.BoxShadow(blur_radius=20, color="#08000000"), height=450, content=ft.Column([ft.Row([ft.Column([ft.Text("Performans Analizi", size=20, weight="bold", color=col_text), ft.Text("Yıllık gelir ve gider karşılaştırması", size=13, color=col_text_light)]), year_dropdown_ref], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(height=20), ft.Container(content=line_chart, expand=True), ft.Row([ft.Row([ft.Container(width=10, height=10, bgcolor=col_primary, border_radius=2), ft.Text("Gelir", size=12, color="grey")], spacing=5), ft.Row([ft.Container(width=10, height=10, bgcolor=col_secondary, border_radius=2), ft.Text("Gider", size=12, color="grey")], spacing=5)], alignment=ft.MainAxisAlignment.CENTER)]))

    dashboard_layout = ft.Column([header, ft.Container(height=10), stats_row, ft.Container(height=10), ft.Row([chart_container, ft.Container(content=transactions_list, expand=1)], expand=True, spacing=20)], spacing=10)

    dashboard_content.content = dashboard_layout
    content_area = ft.Container(expand=True, padding=30, content=dashboard_content)

    layout = ft.Row([sidebar_container, content_area], expand=True, spacing=0)
    page.add(layout)
    
    def start_animations():
        time.sleep(0.5) 
        for donut in state["donuts"]: donut.start_animation()
        # İlk yüklemede varsayılan yılı çiz
        if available_years:
            first_year = available_years[0]
            draw_snake_chart(first_year)
        
        # Animasyonlar başladıktan sonra callback'leri kaydet
        time.sleep(0.3)  # Animasyonların tamamlanmasını bekle
        
        # Ana sayfa için birleşik callback - hem grafikler hem işlem geçmişi
        def home_page_full_update():
            refresh_charts_and_data()
            update_transactions()  # İşlem geçmişini de güncelle
        
        state["update_callbacks"]["home_page"] = home_page_full_update

    threading.Thread(target=start_animations, daemon=True).start()

    # ------------------------------------------------------------------------
    # GÜNCELLEME FONKSİYONLARI (Update Functions)
    # ------------------------------------------------------------------------

    # Güncelleme kontrolü - sadece ana sayfa için
    def check_for_updates():
        """Uygulama güncellemelerini kontrol et"""
        try:
            # Ana sayfa açıkken güncelleme kontrolü yap
            if state["current_page"] != "home":
                return
            
            # Güncelleme kontrolü yap
            update_info = backend_instance.check_for_updates()
            
            if update_info and update_info.get("update_available", False):
                # Güncelleme mevcutsa, bilgilendirme mesajı göster
                msg = f"Yeni bir güncelleme mevcut: {update_info.get('version', 'Bilinmiyor')}\n\nAçıklama: {update_info.get('description', 'No description')}\n\nGüncellemek için 'Evet' butonuna tıklayın."
                
                def on_update_confirm(e):
                    # Güncelleme işlemini başlat
                    backend_instance.download_and_install_update()
                    
                    # Bilgilendirme mesajı
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Güncelleme indiriliyor ve uygulanıyor...", color=col_white),
                        bgcolor=col_success
                    )
                    page.snack_bar.open = True
                    page.update()
                    
                    # Uygulamayı yeniden başlat
                    time.sleep(2)
                    os.execl(sys.executable, sys.executable, *sys.argv)
                
                # Güncelleme onayı için dialog göster
                update_dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Güncelleme Mevcut"),
                    content=ft.Text(msg),
                    actions=[
                        ft.ElevatedButton("Evet", on_click=on_update_confirm, bgcolor=col_success, color=col_white),
                        ft.ElevatedButton("Hayır", on_click=lambda e: update_dlg.close(), bgcolor=col_danger, color=col_white)
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                
                page.overlay.append(update_dlg)
                update_dlg.open = True
                page.update()
        except Exception as e:
            pass

    # Ana sayfa yüklendiğinde güncelleme kontrolü yap
    if state["current_page"] == "home":
        check_for_updates()

# Assets dizinini belirle (PyInstaller için)
def get_assets_dir():
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return sys._MEIPASS
    except Exception:
        return os.path.abspath(".")

ft.app(target=main, assets_dir=get_assets_dir())