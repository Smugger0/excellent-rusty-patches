# -*- coding: utf-8 -*-
"""
Excel Export Module for Invoice Management System
Bu modül fatura listelerini Excel formatına dönüştürür.
Pandas ve XlsxWriter kullanarak formatlı raporlar oluşturur.
"""

# Merkezi import dosyasından gerekli modülleri al
from imports import *

# ============================================================================
# FATURA EXCEL DIŞA AKTARICI
# ============================================================================
class InvoiceExcelExporter:
    """
    Fatura listelerini Excel'e dönüştüren ve raporlayan sınıf.
    Otomatik sütun genişliği, hücre biçimlendirme ve özet tabloları içerir.
    """
    
    def __init__(self):
        self.excel_folder = "ExcelReports"
        # Klasör oluşturma işlemi artık ana uygulamada yapılıyor
        # if not os.path.exists(self.excel_folder):
        #     os.makedirs(self.excel_folder)
    
    # ------------------------------------------------------------------------
    # SÜTUN GENİŞLİĞİ AYARLAMA
    # ------------------------------------------------------------------------
    def _auto_adjust_column_widths(self, writer, sheet_name, df):
        """
        Excel sütun genişliklerini içeriğe göre otomatik ayarlar.
        Ayrıca başlık ve hücre stillerini (renk, kenarlık vb.) uygular.
        """
        try:
            worksheet = writer.sheets[sheet_name]
            workbook = writer.book
            
            # Başlık stili: Koyu, beyaz yazı, mor arka plan
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#6C5DD3',
                'font_color': 'white',
                'border': 1
            })
            
            # Standart hücre stili
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1
            })
            
            # Para birimi stili (2 ondalık basamak)
            money_format = workbook.add_format({
                'num_format': '#,##0.00',
                'valign': 'top',
                'border': 1
            })
            
            # Döviz kuru stili (5 ondalık basamak - hassas hesaplama için)
            currency_format = workbook.add_format({
                'num_format': '#,##0.00000',
                'valign': 'top',
                'border': 1
            })
            
            for i, col in enumerate(df.columns):
                # Kolon başlığının uzunluğu
                header_len = len(str(col))
                
                # Kolon verilerinin maksimum uzunluğu
                if len(df) > 0:
                    max_len = df[col].astype(str).map(len).max()
                    # En uzun değeri bul, ancak çok uzun olmasın
                    col_width = min(max(max_len, header_len) + 2, 50)
                else:
                    col_width = header_len + 2
                
                # Minimum genişlik
                col_width = max(col_width, 10)
                
                # Sütun genişliğini ayarla
                worksheet.set_column(i, i, col_width)
                
                # Header'ı formatla
                worksheet.write(0, i, col, header_format)
                
                # Veri tipine göre format uygula
                if len(df) > 0:
                    for row_num in range(1, len(df) + 1):
                        cell_value = df.iloc[row_num-1, i]
                        if col in ['TUTAR (TL)', 'TUTAR', 'MİKTAR'] and isinstance(cell_value, (int, float)):
                            worksheet.write(row_num, i, cell_value, money_format)
                        else:
                            worksheet.write(row_num, i, cell_value, cell_format)
                            
        except Exception as e:
            logging.error(f"Sütun genişlik ayarlama hatası: {e}")
    
    # ------------------------------------------------------------------------
    # EXCEL DIŞA AKTARMA
    # ------------------------------------------------------------------------
    def export_to_excel(self, file_path, sheets_data):
        """
        Verilen verileri bir Excel dosyasına aktarır ve sütun genişliklerini otomatik ayarlar
        
        Args:
            file_path (str): Excel dosya yolu
            sheets_data (dict): Sayfa adları ve verileri içeren sözlük
        
        Returns:
            bool: Başarılı ise True, aksi halde False
        """
        try:
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                for sheet_name, content in sheets_data.items():
                    df = pd.DataFrame(content.get("data", []))
                    if not df.empty:
                        # Veriyi yaz (header olmadan)
                        df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=1)
                        # Sütun genişliklerini ve formatları ayarla
                        self._auto_adjust_column_widths(writer, sheet_name, df)
            
            return True
        except Exception as e:
            logging.error(f"Excel'e aktarma hatası: {e}")
            return False

    def _format_date(self, date_str):
        """Tarih formatını düzenle"""
        if not date_str:
            return ''
        
        if '-' in date_str:
            try:
                year, month, day = date_str.split('-')
                return f"{day}.{month}.{year}"
            except:
                return date_str
        return date_str
    
    def _prepare_invoice_data(self, invoice_data):
        """Fatura verilerini Excel formatına hazırla"""
        excel_data = []
        for invoice in invoice_data:
            # Kur bilgilerini al
            usd_rate = invoice.get('usd_rate')
            eur_rate = invoice.get('eur_rate')
            
            usd_rate_val = float(usd_rate) if usd_rate is not None else 0.0
            eur_rate_val = float(eur_rate) if eur_rate is not None else 0.0
            
            # Tutarları al
            tutar_tl = float(invoice.get('toplam_tutar_tl', 0) or 0)
            tutar_usd = float(invoice.get('toplam_tutar_usd', 0) or 0)
            tutar_eur = float(invoice.get('toplam_tutar_eur', 0) or 0)
            
            # KDV bilgileri
            kdv_tutari = float(invoice.get('kdv_tutari', 0) or 0)
            kdv_yuzdesi = float(invoice.get('kdv_yuzdesi', 0) or 0)
            
            # Formatlı metinler (Frontend ile uyumlu)
            usd_text = f"{tutar_usd:,.2f}" if usd_rate_val == 0 else f"{tutar_usd:,.2f} ({usd_rate_val:.2f} TL)"
            eur_text = f"{tutar_eur:,.2f}" if eur_rate_val == 0 else f"{tutar_eur:,.2f} ({eur_rate_val:.2f} TL)"
            kdv_text = f"{kdv_tutari:,.2f} (%{kdv_yuzdesi:.0f})"
            
            row = {
                'FATURA NO': invoice.get('fatura_no', ''),
                'TARİH': self._format_date(invoice.get('tarih', '')),
                'FİRMA': invoice.get('firma', ''),
                'MALZEME': invoice.get('malzeme', ''),
                'MİKTAR': invoice.get('miktar', ''),
                'TUTAR (TL)': tutar_tl,
                'TUTAR (USD)': usd_text,
                'TUTAR (EUR)': eur_text,
                'KDV (Tutar/%)': kdv_text
            }
            excel_data.append(row)
        return excel_data

    def export_invoices_to_excel(self, invoice_data, invoice_type, file_path=None):
        """Fatura listesini Excel'e dönüştür"""
        try:
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{invoice_type}_faturalari_{timestamp}.xlsx"
                file_path = os.path.join(self.excel_folder, filename)
            
            excel_data = self._prepare_invoice_data(invoice_data)
            sheets_data = {f"{invoice_type.title()} Faturalar": {"data": excel_data}}
            
            return self.export_to_excel(file_path, sheets_data)
            
        except Exception as e:
            logging.error(f"Fatura Excel aktarma hatası: {e}")
            return False

    def export_general_expenses_to_excel(self, expense_data, file_path=None):
        """Genel gider listesini Excel'e dönüştür"""
        try:
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"genel_giderler_{timestamp}.xlsx"
                file_path = os.path.join(self.excel_folder, filename)
            
            excel_data = []
            for expense in expense_data:
                row = {
                    'TARİH': self._format_date(expense.get('tarih', '')),
                    'GİDER TÜRÜ': expense.get('tur', ''),
                    'TUTAR': float(expense.get('miktar', 0) or 0),
                    'AÇIKLAMA': expense.get('aciklama', '')
                }
                excel_data.append(row)
            
            sheets_data = {"Genel Giderler": {"data": excel_data}}
            return self.export_to_excel(file_path, sheets_data)
            
        except Exception as e:
            logging.error(f"Genel gider Excel aktarma hatası: {e}")
            return False


# Frontend'den kolayca çağırılabilir yardımcı fonksiyonlar
def export_outgoing_invoices_to_excel(invoice_data, file_path=None):
    """Giden faturaları Excel'e aktar"""
    exporter = InvoiceExcelExporter()
    return exporter.export_invoices_to_excel(invoice_data, 'outgoing', file_path)

def export_incoming_invoices_to_excel(invoice_data, file_path=None):
    """Gelen faturaları Excel'e aktar"""
    exporter = InvoiceExcelExporter()
    return exporter.export_invoices_to_excel(invoice_data, 'incoming', file_path)

def export_general_expenses_to_excel(expense_data, file_path=None):
    """Genel giderleri Excel'e aktar"""
    exporter = InvoiceExcelExporter()
    return exporter.export_general_expenses_to_excel(expense_data, file_path)

def export_monthly_general_expenses_to_excel(expense_data, year=None, file_path=None):
    """Genel giderleri aylık formatta Excel'e aktar - Yatay tablo (Aylar sütunlarda)"""
    try:
        if not year:
            year = datetime.now().year
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"genel_giderler_aylik_{year}_{timestamp}.xlsx"
            exporter = InvoiceExcelExporter()
            file_path = os.path.join(exporter.excel_folder, filename)
        
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet(f'{year} Genel Giderler')
        
        # Formatlar
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#6C5DD3',
            'font_color': 'white',
            'border': 1,
            'font_size': 12
        })
        
        money_format = workbook.add_format({
            'num_format': '#,##0.00 "₺"',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 11
        })
        
        # Ayları parse et ve topla
        months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        monthly_totals = {i+1: 0.0 for i in range(12)}
        
        # Expense data'dan aylık toplamları hesapla
        for expense in expense_data:
            tarih = expense.get('tarih', '')
            miktar = float(expense.get('miktar', 0) or 0)
            
            # Tarihi parse et (formatlar: DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD)
            try:
                if '.' in tarih:
                    parts = tarih.split('.')
                    month = int(parts[1])
                elif '/' in tarih:
                    parts = tarih.split('/')
                    month = int(parts[1])
                elif '-' in tarih:
                    parts = tarih.split('-')
                    month = int(parts[1])
                else:
                    continue
                    
                if 1 <= month <= 12:
                    monthly_totals[month] += miktar
            except:
                continue
        
        # Başlık satırı (Aylar)
        worksheet.write(0, 0, 'AY', header_format)
        for i, month in enumerate(months):
            worksheet.write(0, i+1, month, header_format)
        
        # Tutar satırı
        worksheet.write(1, 0, 'TUTAR', header_format)
        for i in range(12):
            worksheet.write(1, i+1, monthly_totals[i+1], money_format)
        
        # Sütun genişliklerini ayarla
        worksheet.set_column(0, 0, 12)  # İlk sütun (AY)
        worksheet.set_column(1, 12, 15)  # Ay sütunları
        
        workbook.close()
        logging.info(f"Aylık genel giderler '{os.path.basename(file_path)}' dosyasına aktarıldı.")
        return True
        
    except Exception as e:
        logging.error(f"Aylık genel gider Excel aktarma hatası: {e}")
        return False

def export_monthly_income_to_excel(year, monthly_results, quarterly_results, summary, file_path):
    """Dönemsel gelir raporunu Excel'e aktar - Uygulama görünümüne benzer formatla"""
    try:
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet(f'{year} Raporu')
        
        # Renkler - Mor tema (açıktan koyuya)
        colors = {
            'mavi': '#E8E5F5',      # Ocak-Mart (açık mor)
            'pembe': '#D4CDED',     # Nisan-Haziran (orta açık mor)
            'sari': '#C0B5E5',      # Temmuz-Eylül (orta mor)
            'yesil': '#AC9EDD'      # Ekim-Aralık (koyu mor)
        }
        
        # Formatlar
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#6C5DD3',
            'font_color': 'white',
            'border': 1,
            'font_size': 11
        })
        
        month_format_base = {
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10
        }
        
        # Her üç ayın formatı
        month_formats = {}
        for color_name, color_code in colors.items():
            month_formats[color_name] = workbook.add_format({
                **month_format_base,
                'bg_color': color_code
            })
        
        money_format_base = {
            'num_format': '#,##0.00 ₺',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10
        }
        
        # Para formatları (renkli)
        money_formats = {}
        for color_name, color_code in colors.items():
            money_formats[color_name] = workbook.add_format({
                **money_format_base,
                'bg_color': color_code
            })
        
        # KDV alt satırı için format (daha küçük ve gri)
        kdv_format_base = {
            'num_format': '"KDV: "#,##0.00 ₺',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
            'font_color': '#666666'
        }
        
        kdv_formats = {}
        for color_name, color_code in colors.items():
            kdv_formats[color_name] = workbook.add_format({
                **kdv_format_base,
                'bg_color': color_code
            })
        
        # Yüzde formatı
        percent_format_base = {
            'num_format': '%#,##0',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10
        }
        
        percent_formats = {}
        for color_name, color_code in colors.items():
            percent_formats[color_name] = workbook.add_format({
                **percent_format_base,
                'bg_color': color_code
            })
        
        # Toplam satırı formatı
        total_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E7E6E6',
            'border': 1,
            'font_size': 11
        })
        
        total_money_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00 ₺',
            'align': 'right',
            'valign': 'vcenter',
            'bg_color': '#E7E6E6',
            'border': 1,
            'font_size': 11
        })
        
        total_kdv_format = workbook.add_format({
            'num_format': '"KDV: "#,##0.00 ₺',
            'align': 'right',
            'valign': 'vcenter',
            'bg_color': '#E7E6E6',
            'border': 1,
            'font_size': 9,
            'font_color': '#666666'
        })
        
        # Kâr satırı formatı
        kar_label_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'valign': 'vcenter',
            'bg_color': '#E7E6E6',
            'border': 1,
            'font_size': 11
        })
        
        kar_value_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00 ₺',
            'align': 'right',
            'valign': 'vcenter',
            'bg_color': '#E7E6E6',
            'border': 1,
            'font_size': 11
        })
        
        # Sütun genişlikleri
        worksheet.set_column('A:A', 14)  # AYLAR
        worksheet.set_column('B:C', 22)  # Gelir, Gider (KDV alt satırı için daha geniş)
        worksheet.set_column('D:D', 16)  # KDV Farkı
        worksheet.set_column('E:E', 18)  # Kurumlar Vergisi (%)
        worksheet.set_column('F:F', 22)  # Çeyrek Toplam
        
        # Başlıklar
        headers = ['AYLAR', 'GELİR', 'GİDER', 'KDV FARKI', 'KURUMLAR VERGİSİ (%)', 'ÇEYREK TOPLAM']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Aylar ve veriler
        months = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", 
                 "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
        
        color_mapping = {
            0: 'mavi', 1: 'mavi', 2: 'mavi',
            3: 'pembe', 4: 'pembe', 5: 'pembe',
            6: 'sari', 7: 'sari', 8: 'sari',
            9: 'yesil', 10: 'yesil', 11: 'yesil'
        }
        
        total_kurumlar = 0.0
        
        # Her ay için 2 satır kullanılacak: 1. Tutar, 2. KDV
        current_row = 1
        for i, month_name in enumerate(months):
            monthly_data = monthly_results[i]
            color = color_mapping[i]
            
            kurumlar_yuzde = monthly_data.get('kurumlar_yuzde', 0)
            kurumlar = monthly_data.get('kurumlar', 0)
            total_kurumlar += kurumlar
            
            gelir = monthly_data.get('kesilen', 0)
            gider = monthly_data.get('gelen', 0)
            gelir_kdv = monthly_data.get('gelir_kdv', 0)
            gider_kdv = monthly_data.get('gider_kdv', 0)
            kdv_farki = gelir_kdv - gider_kdv
            
            # Ana satır - Tutar
            worksheet.write(current_row, 0, month_name, month_formats[color])
            worksheet.write(current_row, 1, gelir, money_formats[color])
            worksheet.write(current_row, 2, gider, money_formats[color])
            worksheet.write(current_row, 3, kdv_farki, money_formats[color])
            worksheet.write(current_row, 4, kurumlar_yuzde / 100 if kurumlar_yuzde else 0, percent_formats[color])
            
            # Alt satır - KDV
            worksheet.write(current_row + 1, 0, '', month_formats[color])
            worksheet.write(current_row + 1, 1, gelir_kdv, kdv_formats[color])
            worksheet.write(current_row + 1, 2, gider_kdv, kdv_formats[color])
            worksheet.write(current_row + 1, 3, '', month_formats[color])
            worksheet.write(current_row + 1, 4, '', month_formats[color])
            
            # Çeyrek Toplam (her 3 ayda bir birleştirme)
            if i % 3 == 0:
                q_index = i // 3
                odenecek_vergi = 0.0
                if q_index < len(quarterly_results):
                    odenecek_vergi = quarterly_results[q_index].get('odenecek_kv', 0)
                
                # 6 satırı birleştir (3 ay * 2 satır)
                merged_format = workbook.add_format({
                    'num_format': '#,##0.00 ₺',
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                    'font_size': 12,
                    'bold': True,
                    'bg_color': colors[color]
                })
                worksheet.merge_range(current_row, 5, current_row + 5, 5, odenecek_vergi, merged_format)
            
            current_row += 2  # Her ay için 2 satır
        
        # Satır yükseklikleri
        worksheet.set_row(0, 25)  # Başlık
        for i in range(1, current_row):
            worksheet.set_row(i, 18)  # Veri satırları
        
        workbook.close()
        
        logging.info(f"Dönemsel gelir raporu başarıyla oluşturuldu: {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Dönemsel gelir Excel aktarma hatası: {e}")
        return False