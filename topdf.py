# -*- coding: utf-8 -*-
"""
PDF Export Module for Invoice Management System
Bu modül fatura listelerini PDF formatına dönüştürür.
ReportLab kütüphanesini kullanarak profesyonel görünümlü raporlar oluşturur.
"""

# Merkezi import dosyasından gerekli modülleri al
from imports import *
from locales import tr

# ============================================================================
# FATURA PDF DIŞA AKTARICI
# ============================================================================
class InvoicePDFExporter:
    """
    Fatura listelerini PDF'e dönüştüren ve raporlayan sınıf.
    Türkçe karakter desteği, özel fontlar ve tablo düzeni sağlar.
    """
    
    def __init__(self):
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._setup_custom_styles()
    
    # ------------------------------------------------------------------------
    # FONT KAYDI
    # ------------------------------------------------------------------------
    def _register_fonts(self):
        """
        Türkçe karakterler için gerekli fontları sisteme kaydeder.
        Windows font klasöründen Arial ve Calibri fontlarını yüklemeye çalışır.
        """
        try:
            # Windows varsayılan fontları
            windows_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            
            # Arial fontunu kaydet (Türkçe karakter desteği ile)
            arial_path = os.path.join(windows_fonts, 'arial.ttf')
            if os.path.exists(arial_path):
                pdfmetrics.registerFont(TTFont('Arial-Turkish', arial_path))
                
            
            # Arial Bold (Kalın yazı tipi)
            arial_bold_path = os.path.join(windows_fonts, 'arialbd.ttf')
            if os.path.exists(arial_bold_path):
                pdfmetrics.registerFont(TTFont('Arial-Bold-Turkish', arial_bold_path))
                
            
            # Calibri alternatifi (daha modern görünüm için)
            calibri_path = os.path.join(windows_fonts, 'calibri.ttf')
            if os.path.exists(calibri_path):
                pdfmetrics.registerFont(TTFont('Calibri-Turkish', calibri_path))
                
                
        except Exception as e:
            # Font yüklenemezse varsayılan fontlar kullanılır
            pass
    
    # ------------------------------------------------------------------------
    # STİL AYARLARI
    # ------------------------------------------------------------------------
    def _setup_custom_styles(self):
        """
        Rapor için özel PDF stillerini (başlık, tablo, metin) oluşturur.
        """
        # Türkçe karakter destekli font adları - öncelik sırası
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        
        if 'Calibri-Turkish' in registered_fonts:
            turkish_font = 'Calibri-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Calibri-Turkish'
        elif 'Arial-Turkish' in registered_fonts:
            turkish_font = 'Arial-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Arial-Turkish'
        else:
            turkish_font = 'Helvetica'
            turkish_font_bold = 'Helvetica-Bold'
            
        
        
        
        # Ana başlık stili - daha büyük ve belirgin
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontName=turkish_font_bold,
            fontSize=20,
            spaceAfter=25,
            spaceBefore=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d'),
            leading=24  # Satır aralığı
        ))
        
        # Alt başlık stili
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontName=turkish_font_bold,
            fontSize=16,
            spaceAfter=20,
            spaceBefore=15,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#2d3748'),
            leading=20
        ))
        
        # Normal paragraf stili
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontName=turkish_font,
            fontSize=11,
            spaceAfter=8,
            spaceBefore=4,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#2d3748'),
            leading=14
        ))
        
        # Özet stili
        self.styles.add(ParagraphStyle(
            name='Summary',
            parent=self.styles['Normal'],
            fontName=turkish_font,
            fontSize=12,
            spaceAfter=10,
            spaceBefore=5,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#2c5282'),
            leftIndent=200,
            leading=15
        ))
        
        # Normal metin stili
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontName=turkish_font,
            fontSize=10,
            spaceAfter=10,
            spaceBefore=5,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#4a5568'),
            leading=13
        ))
        
        # Footer stili
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#95a5a6')
        ))

    def export_invoices_to_pdf(self, invoice_data, invoice_type, file_path, lang='tr'):
        """
        Fatura listesini PDF'e dönüştür - Uygulama tablo formatıyla aynı
        
        Args:
            invoice_data (list): Fatura verileri listesi
            invoice_type (str): Fatura tipi ('outgoing' veya 'incoming')
            file_path (str): PDF dosya yolu
            lang (str): Dil kodu ('tr' veya 'en')
            
        Returns:
            bool: Başarılı ise True, aksi halde False
        """
        try:
            # PDF dokümanı oluştur
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=2*cm,
                bottomMargin=1.5*cm
            )
            
            # Font kaydetme
            self._register_fonts()
            
            # Uygulama tarzında tablo düzeni oluştur
            story = self._create_invoice_document_layout(invoice_data, invoice_type, lang)
            
            # PDF oluştur
            doc.build(story)
            return True
            
        except Exception as e:
            return False

    def export_general_expenses_to_pdf(self, expense_data, file_path, lang='tr'):
        """
        Genel gider listesini PDF'e dönüştür - Uygulama formatıyla aynı
        
        Args:
            expense_data (list): Genel gider verileri listesi
            file_path (str): PDF dosya yolu
            lang (str): Dil kodu ('tr' veya 'en')
            
        Returns:
            bool: Başarılı ise True, aksi halde False
        """
        try:
            # PDF dokümanı oluştur
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=2*cm,
                bottomMargin=1.5*cm
            )
            
            # Font kaydetme
            self._register_fonts()
            
            # Uygulama tarzında tablo düzen oluştur
            story = self._create_expense_document_layout(expense_data, lang)
            
            # PDF oluştur
            doc.build(story)
            return True
            
        except Exception as e:
            return False

    def _get_title_by_type(self, invoice_type, lang='tr'):
        """Fatura tipine göre başlık döndür"""
        titles = {
            'outgoing': tr('pdf_title_outgoing', lang),
            'incoming': tr('pdf_title_incoming', lang)
        }
        return titles.get(invoice_type, tr('pdf_title_general', lang))

    def _create_invoice_document_layout(self, invoice_data, invoice_type, lang='tr'):
        """Uygulama fatura tablosu ile tamamen aynı format - irsaliye no hariç"""
        
        story = []
        
        # Türkçe karakter destekli font seçimi
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        
        if 'Calibri-Turkish' in registered_fonts:
            turkish_font = 'Calibri-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Calibri-Turkish'
        elif 'Arial-Turkish' in registered_fonts:
            turkish_font = 'Arial-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Arial-Turkish'
        else:
            turkish_font = 'Helvetica'
            turkish_font_bold = 'Helvetica-Bold'
        
        
        
        # Uygulama benzeri tablo başlığı
        story.append(Paragraph(f'<b>{tr("pdf_list_title", lang)}</b>', 
                             ParagraphStyle('TableTitle', fontName=turkish_font_bold, fontSize=12, 
                                          alignment=1, spaceAfter=5)))
        
        # Fatura tipi başlığı (Gelir mi Gider mi)
        type_text = tr("pdf_income_invoices", lang) if invoice_type == 'outgoing' else tr("pdf_expense_invoices", lang)
        type_color = '#28a745' if invoice_type == 'outgoing' else '#dc3545'  # Yeşil / Kırmızı
        story.append(Paragraph(f'<font color="{type_color}"><b>{type_text}</b></font>', 
                             ParagraphStyle('TypeTitle', fontName=turkish_font_bold, fontSize=10, 
                                          alignment=1, spaceAfter=15)))
        
        # Hücre stili - Metin kaydırma için
        cell_style = ParagraphStyle(
            'CellStyle',
            fontName=turkish_font,
            fontSize=7,
            leading=8,
            alignment=0  # TA_LEFT
        )
        
        # Uygulama ile TAMAMEN AYNI sütun başlıkları (irsaliye no hariç)
        headers = [
            tr("col_invoice_no", lang), 
            tr("col_date", lang), 
            tr("col_company", lang), 
            tr("col_item", lang), 
            tr("col_amount", lang), 
            tr("col_total_tl", lang), 
            tr("col_total_usd", lang), 
            tr("col_total_eur", lang), 
            tr("col_vat", lang)
        ]
        
        # Veri satırları hazırla
        table_data = [headers]
        
        for invoice in invoice_data:
            # Tarihi formatla
            tarih = invoice.get('tarih', '')
            if '-' in tarih:
                try:
                    year, month, day = tarih.split('-')
                    tarih_formatted = f"{day}.{month}.{year}"
                except:
                    tarih_formatted = tarih
            else:
                tarih_formatted = tarih
            
            # KDV bilgileri
            kdv_tutari = float(invoice.get('kdv_tutari', 0) or 0)
            kdv_yuzdesi = float(invoice.get('kdv_yuzdesi', 0) or 0)
            toplam_tutar_tl = float(invoice.get('toplam_tutar_tl', 0) or 0)
            
            # USD ve EUR tutarları
            usd_amount = float(invoice.get('toplam_tutar_usd', 0) or 0)
            eur_amount = float(invoice.get('toplam_tutar_eur', 0) or 0)
            
            # Kur bilgileri
            usd_rate = invoice.get('usd_rate')
            eur_rate = invoice.get('eur_rate')
            usd_rate_val = float(usd_rate) if usd_rate is not None else 0.0
            eur_rate_val = float(eur_rate) if eur_rate is not None else 0.0
            
            # Formatlı metinler (Frontend ile uyumlu)
            # PDF'de yer kazanmak için alt satıra geçebiliriz
            usd_text = f"{usd_amount:,.2f}" if usd_rate_val == 0 else f"{usd_amount:,.2f}\n({usd_rate_val:.2f} {tr('currency_tl', lang)})"
            eur_text = f"{eur_amount:,.2f}" if eur_rate_val == 0 else f"{eur_amount:,.2f}\n({eur_rate_val:.2f} {tr('currency_tl', lang)})"
            kdv_text = f"{kdv_tutari:,.2f}\n(%{kdv_yuzdesi:.0f})"
            
            # Uzun metinleri Paragraph ile sarmala (Otomatik alt satıra geçmesi için)
            fatura_no_para = Paragraph(str(invoice.get('fatura_no', '')), cell_style)
            firma_para = Paragraph(str(invoice.get('firma', '')), cell_style)
            malzeme_para = Paragraph(str(invoice.get('malzeme', '')), cell_style)
            
            # Uygulama ile TAMAMEN AYNI format
            row_data = [
                fatura_no_para,                                    # FATURA NO
                tarih_formatted,                                   # TARIH
                firma_para,                                        # FIRMA
                malzeme_para,                                      # MALZEME
                str(invoice.get('miktar', '')),                    # MIKTAR
                f"{toplam_tutar_tl:,.2f}",                        # TUTAR (TL)
                usd_text,                                         # TUTAR (USD)
                eur_text,                                         # TUTAR (EUR)
                kdv_text                                          # KDV (Tutar/%)
            ]
            
            table_data.append(row_data)
        
        # Fatura no genişletilmiş sütun genişlikleri
        col_widths = [2.8*cm, 1.6*cm, 2.2*cm, 2.2*cm, 1.0*cm, 1.6*cm, 1.6*cm, 1.6*cm, 2.4*cm]
        
        # Ana tablo oluştur
        main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        main_table.setStyle(TableStyle([
            # Header stili - uygulama benzeri
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C5DD3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), turkish_font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Veri satırları - uygulama benzeri
            ('FONTNAME', (0, 1), (-1, -1), turkish_font),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('FONTSIZE', (0, 1), (0, -1), 6),  # Fatura no sütunu daha küçük font
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 1), (-1, -1), 3),
            ('RIGHTPADDING', (0, 1), (-1, -1), 3),
            
            # Hizalamalar - uygulama ile aynı
            ('ALIGN', (0, 1), (4, -1), 'LEFT'),      # Fatura no, tarih, firma, malzeme, miktar - sol
            ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),    # Tutar sütunları - sağ
            
            # Uygulama benzeri alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            
            # Grid lines - uygulama benzeri
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(main_table)
        story.append(Spacer(1, 20))
        
        # Özet bölümü ekle
        summary_section = self._create_table_summary(invoice_data, invoice_type, turkish_font, turkish_font_bold, lang)
        story.extend(summary_section)
        
        return story

    def _create_table_summary(self, invoice_data, invoice_type, turkish_font, turkish_font_bold, lang='tr'):
        """Tablo altına özet bilgileri ekle"""
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.lib.styles import ParagraphStyle
        
        summary_story = []
        
        if not invoice_data:
            return summary_story
        
        # Özet başlığı
        summary_story.append(Spacer(1, 15))
        summary_story.append(Paragraph(f'<b>{tr("summary_title", lang)}</b>', 
                                     ParagraphStyle('SummaryTitle', fontName=turkish_font_bold, 
                                                  fontSize=10, alignment=1, spaceAfter=10)))
        
        # Finansal özetler hesapla
        total_tl = sum(float(inv.get('toplam_tutar_tl', 0) or 0) for inv in invoice_data)
        total_kdv = sum(float(inv.get('kdv_tutari', 0) or 0) for inv in invoice_data)
        count = len(invoice_data)
        average_tl = total_tl / count if count > 0 else 0
        
        # USD ve EUR toplamları
        total_usd = 0
        total_eur = 0
        for inv in invoice_data:
            usd_amount = inv.get('toplam_tutar_usd', 0) or 0
            eur_amount = inv.get('toplam_tutar_eur', 0) or 0
            
            # Eğer USD/EUR yoksa TL'den hesapla
            if usd_amount == 0:
                tl_amount = float(inv.get('toplam_tutar_tl', 0) or 0)
                usd_amount = tl_amount / 42.44 if tl_amount > 0 else 0
            if eur_amount == 0:
                tl_amount = float(inv.get('toplam_tutar_tl', 0) or 0)
                eur_amount = tl_amount / 48.93 if tl_amount > 0 else 0
                
            total_usd += usd_amount
            total_eur += eur_amount
        
        # Özet tablosu verisi
        summary_data = [
            [f'{tr("summary_invoice_count", lang)}:', f'{count} {tr("unit_piece", lang)}', f'{tr("summary_total_tl", lang)}:', f'{total_tl:,.2f} {tr("currency_tl", lang)}'],
            [f'{tr("summary_total_usd", lang)}:', f'{total_usd:,.2f} {tr("currency_usd", lang)}', f'{tr("summary_total_eur", lang)}:', f'{total_eur:,.2f} {tr("currency_eur", lang)}'],
            [f'{tr("summary_total_vat", lang)}:', f'{total_kdv:,.2f} {tr("currency_tl", lang)}', f'{tr("summary_average", lang)}:', f'{average_tl:,.2f} {tr("currency_tl", lang)}']
        ]
        
        # Özet tablosu oluştur
        summary_table = Table(summary_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), turkish_font),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # Etiketler sağa
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),   # Değerler sola
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Etiketler sağa
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),   # Değerler sola
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            # Arka plan renkleri
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f8ff')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f8ff')),
            ('FONTNAME', (0, 0), (0, -1), turkish_font_bold),
            ('FONTNAME', (2, 0), (2, -1), turkish_font_bold),
            # Değer sütunları vurgu
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#e8f5e8')),  # Fatura sayısı
            ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#fff2e8')),  # Toplam TL
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0'))
        ]))
        
        summary_story.append(summary_table)
        summary_story.append(Spacer(1, 15))
        
        # Tarih bilgisi
        current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        summary_story.append(Paragraph(f'<i>{tr("report_date", lang)}: {current_date}</i>', 
                                     ParagraphStyle('DateInfo', fontName=turkish_font, 
                                                  fontSize=7, alignment=1, 
                                                  textColor=colors.HexColor('#666666'))))
        
        return summary_story

    def _create_expense_document_layout(self, expense_data, lang='tr'):
        """Fatura formatı gibi genel gider tablosu - uygulama benzeri"""
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        
        story = []
        
        # Türkçe karakter destekli font seçimi
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        
        if 'Calibri-Turkish' in registered_fonts:
            turkish_font = 'Calibri-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Calibri-Turkish'
        elif 'Arial-Turkish' in registered_fonts:
            turkish_font = 'Arial-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Arial-Turkish'
        else:
            turkish_font = 'Helvetica'
            turkish_font_bold = 'Helvetica-Bold'
        
        
        
        # Fatura benzeri tablo başlığı
        story.append(Paragraph(f'<b>{tr("excel_sheet_general_expenses", lang).upper()}</b>', 
                             ParagraphStyle('TableTitle', fontName=turkish_font_bold, fontSize=12, 
                                          alignment=1, spaceAfter=15)))
        
        # Hücre stili - Metin kaydırma için
        cell_style = ParagraphStyle(
            'CellStyle',
            fontName=turkish_font,
            fontSize=7,
            leading=8,
            alignment=0  # TA_LEFT
        )
        
        # Fatura benzeri sütun başlıkları
        headers = [
            tr("col_date", lang), 
            tr("excel_col_expense_type", lang), 
            tr("col_amount", lang), 
            tr("unit_type", lang), 
            tr("col_total_tl", lang)
        ]
        
        # Veri satırları hazırla
        table_data = [headers]
        
        for expense in expense_data:
            # Tarihi formatla
            tarih = expense.get('tarih', '')
            if '-' in tarih:
                try:
                    year, month, day = tarih.split('-')
                    tarih_formatted = f"{day}.{month}.{year}"
                except:
                    tarih_formatted = tarih
            else:
                tarih_formatted = tarih
            
            # Fatura benzeri veri formatı
            gider_turu = expense.get('tur', '')
            gider_turu_para = Paragraph(str(gider_turu), cell_style)
            
            miktar_value = float(expense.get('miktar', 0) or 0)
            
            row_data = [
                tarih_formatted,                     # TARIH
                gider_turu_para,                     # GIDER TURU
                "1",                                 # MIKTAR (default 1)
                tr("unit_piece", lang),              # BIRIM
                f"{miktar_value:,.2f} {tr('currency_tl', lang)}"            # TUTAR
            ]
            
            table_data.append(row_data)
        
        # Fatura benzeri sütun genişlikleri
        col_widths = [2.5*cm, 4*cm, 1.5*cm, 1.5*cm, 2.5*cm]
        
        # Ana tablo oluştur
        main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        main_table.setStyle(TableStyle([
            # Header stili - fatura benzeri
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C5DD3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), turkish_font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Veri satırları - fatura benzeri
            ('FONTNAME', (0, 1), (-1, -1), turkish_font),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 1), (-1, -1), 3),
            ('RIGHTPADDING', (0, 1), (-1, -1), 3),
            
            # Hizalamalar - fatura benzeri
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),      # Tarih, gider türü - sol
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),    # Miktar, birim, tutar - sağ
            
            # Fatura benzeri alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            
            # Grid lines - fatura benzeri
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(main_table)
        story.append(Spacer(1, 20))
        
        return story

    def _create_summary_section(self, invoice_data, lang='tr'):
        """Özet bölümü oluştur"""
        # Toplamları hesapla
        total_count = len(invoice_data)
        total_amount = sum(float(inv.get('toplam_tutar_tl', 0) or 0) for inv in invoice_data)
        total_kdv = sum(float(inv.get('kdv_tutari', 0) or 0) for inv in invoice_data)
        total_matrah = total_amount - total_kdv
        
        # Para birimlerine göre dağılım
        currency_breakdown = {}
        for inv in invoice_data:
            birim = inv.get('birim', 'TL')
            amount = float(inv.get('toplam_tutar_tl', 0) or 0)
            if birim in currency_breakdown:
                currency_breakdown[birim] += amount
            else:
                currency_breakdown[birim] = amount
        
        # Özet tablosu
        summary_data = [
            [tr('summary_title', lang), ''],
            [tr('summary_invoice_count', lang), f"{total_count:,}"],
            [tr('summary_total_base', lang), f"{total_matrah:,.2f} TL"],
            [tr('summary_total_vat', lang), f"{total_kdv:,.2f} TL"],
            [tr('summary_general_total', lang), f"{total_amount:,.2f} TL"],
        ]
        
        # Para birimi dağılımı ekle
        if len(currency_breakdown) > 1:
            summary_data.append(['', ''])
            summary_data.append([tr('summary_currency_breakdown', lang), ''])
            for currency, amount in currency_breakdown.items():
                summary_data.append([f"{tr('summary_total', lang)} {currency}", f"{amount:,.2f} TL"])
        
        summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        
        return summary_table

    def _add_header_footer(self, canvas, doc, lang='tr'):
        """Header ve footer ekle"""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.HexColor('#2c3e50'))
        canvas.drawString(2*cm, A4[1] - 1*cm, tr('app_title_long', lang))
        
        # Sayfa numarası
        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(colors.HexColor('#7f8c8d'))
        page_num = f"{tr('page', lang)} {canvas.getPageNumber()}"
        canvas.drawRightString(A4[0] - 2*cm, 1*cm, page_num)
        
        canvas.restoreState()


# Yardımcı fonksiyonlar - Frontend'den kolayca çağırılabilir
def export_outgoing_invoices_to_pdf(invoice_data, file_path):
    """Giden faturaları PDF'e aktar"""
    exporter = InvoicePDFExporter()
    return exporter.export_invoices_to_pdf(invoice_data, 'outgoing', file_path)

def export_incoming_invoices_to_pdf(invoice_data, file_path):
    """Gelen faturaları PDF'e aktar"""
    exporter = InvoicePDFExporter()
    return exporter.export_invoices_to_pdf(invoice_data, 'incoming', file_path)

def export_general_expenses_to_pdf(expense_data, file_path):
    """Genel giderleri PDF'e aktar"""
    exporter = InvoicePDFExporter()
    return exporter.export_general_expenses_to_pdf(expense_data, file_path)

def export_monthly_income_to_pdf(year, monthly_results, quarterly_results, summary, file_path, lang='tr'):
    """Dönemsel gelir raporunu PDF'e aktar"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        
        # PDF dokümanı oluştur (yatay sayfa)
        doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
        story = []
        styles = getSampleStyleSheet()
        
        # Türkçe font desteği
        exporter = InvoicePDFExporter()
        exporter._register_fonts()
        
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        if 'Calibri-Turkish' in registered_fonts:
            turkish_font = 'Calibri-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Calibri-Turkish'
        elif 'Arial-Turkish' in registered_fonts:
            turkish_font = 'Arial-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Arial-Turkish'
        else:
            turkish_font = 'Helvetica'
            turkish_font_bold = 'Helvetica-Bold'
        
        # Başlık
        from reportlab.lib.styles import ParagraphStyle
        title = Paragraph(f"<b>{year} {tr('report_title_suffix', lang)}</b>", 
                         ParagraphStyle('Title', fontName=turkish_font_bold, fontSize=18, 
                                      alignment=1, spaceAfter=20))
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Tablo verilerini hazırla
        months = [tr(f"month_{i+1}", lang) for i in range(12)]
        table_data = [[
            tr('col_months', lang), 
            tr('col_income', lang), 
            tr('col_expense', lang), 
            tr('col_vat_diff', lang), 
            tr('col_corp_tax', lang), 
            tr('col_quarter_total', lang)
        ]]
        
        total_kurumlar = 0.0
        
        for i, month_name in enumerate(months):
            monthly_data = monthly_results[i]
            kurumlar = monthly_data.get('kurumlar', 0)
            kurumlar_yuzde = monthly_data.get('kurumlar_yuzde', 0)
            total_kurumlar += kurumlar
            
            gelir = monthly_data.get('kesilen', 0)
            gider = monthly_data.get('gelen', 0)
            gelir_kdv = monthly_data.get('gelir_kdv', 0)
            gider_kdv = monthly_data.get('gider_kdv', 0)
            kdv_farki = gelir_kdv - gider_kdv
            
            odenecek_vergi = ""
            if i % 3 == 0: # Start of quarter
                q_index = i // 3
                if q_index < len(quarterly_results):
                    odenecek_vergi = f"{quarterly_results[q_index].get('odenecek_kv', 0):,.2f} TL"
            
            # Ana tutar satırı
            table_data.append([
                month_name,
                f"{gelir:,.2f} TL",
                f"{gider:,.2f} TL",
                f"{kdv_farki:,.2f} TL",
                f"%{kurumlar_yuzde:.0f}" if kurumlar_yuzde > 0 else "-",
                odenecek_vergi
            ])
            # KDV alt satırı
            table_data.append([
                "",
                f"KDV: {gelir_kdv:,.2f} TL",
                f"KDV: {gider_kdv:,.2f} TL",
                "",
                "",
                ""
            ])
        
        # Tabloyu oluştur
        table = Table(table_data, colWidths=[3*cm, 4*cm, 4*cm, 3.5*cm, 4*cm, 4.5*cm])
        
        # Temel stiller
        table_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C5DD3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), turkish_font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Veri satırları
            ('FONTNAME', (0, 1), (-1, -1), turkish_font),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            
            # Hizalamalar
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Yüzde sütunu ortalı
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        # KDV satırları için küçük font ve gri renk
        for i in range(12):
            kdv_row = 2 + (i * 2)  # Her ayın 2. satırı KDV satırı
            table_styles.append(('FONTSIZE', (0, kdv_row), (-1, kdv_row), 7))
            table_styles.append(('TEXTCOLOR', (0, kdv_row), (-1, kdv_row), colors.HexColor('#666666')))
        
        # Çeyreklik birleştirmeler (Çeyrek Toplam sütunu)
        for q in range(4):
            start_row = q * 6 + 1  # Her çeyrek 6 satır (3 ay * 2 satır)
            end_row = start_row + 5
            table_styles.append(('SPAN', (5, start_row), (5, end_row)))
            table_styles.append(('VALIGN', (5, start_row), (5, end_row), 'MIDDLE'))
            table_styles.append(('ALIGN', (5, start_row), (5, end_row), 'CENTER'))
            table_styles.append(('FONTSIZE', (5, start_row), (5, end_row), 11))
            table_styles.append(('FONTNAME', (5, start_row), (5, end_row), turkish_font_bold))
            
        table.setStyle(TableStyle(table_styles))
        
        story.append(table)
        
        # Tarih bilgisi
        story.append(Spacer(1, 20))
        from datetime import datetime
        current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        date_para = Paragraph(f'<i>{tr("report_date", lang)}: {current_date}</i>', 
                            ParagraphStyle('DateInfo', fontName=turkish_font, 
                                         fontSize=8, alignment=1, 
                                         textColor=colors.HexColor('#666666')))
        story.append(date_para)
        
        doc.build(story)
        return True
        
    except Exception as e:
        return False

def export_monthly_general_expenses_to_pdf(expense_data, year=None, file_path=None, lang='tr'):
    """Genel giderleri aylık formatta PDF'e aktar - Yatay tablo (Aylar sütunlarda)"""
    try:
        from datetime import datetime
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        
        if not year:
            year = datetime.now().year
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"genel_giderler_aylik_{year}_{timestamp}.pdf"
            pdf_folder = "Markdowns"
            if not os.path.exists(pdf_folder):
                os.makedirs(pdf_folder)
            file_path = os.path.join(pdf_folder, filename)
        
        # Yatay sayfa için landscape
        doc = SimpleDocTemplate(
            file_path,
            pagesize=landscape(A4),
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=1.5*cm
        )
        
        story = []
        
        # Font kayıt
        exporter = InvoicePDFExporter()
        exporter._register_fonts()
        
        # Türkçe font seçimi
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        if 'Calibri-Turkish' in registered_fonts:
            turkish_font = 'Calibri-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Calibri-Turkish'
        elif 'Arial-Turkish' in registered_fonts:
            turkish_font = 'Arial-Turkish'
            turkish_font_bold = 'Arial-Bold-Turkish' if 'Arial-Bold-Turkish' in registered_fonts else 'Arial-Turkish'
        else:
            turkish_font = 'Helvetica'
            turkish_font_bold = 'Helvetica-Bold'
        
        # Başlık
        title_style = ParagraphStyle(
            'CustomTitle',
            fontName=turkish_font_bold,
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#6C5DD3')
        )
        story.append(Paragraph(f'<b>{year} {tr("excel_sheet_general_expenses", lang).upper()} ({tr("col_months", lang)})</b>', title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Ayları parse et ve topla
        months = [tr(f"month_{i+1}", lang) for i in range(12)]
        monthly_totals = {i+1: 0.0 for i in range(12)}
        
        # Expense data'dan aylık toplamları hesapla
        for expense in expense_data:
            tarih = expense.get('tarih', '')
            miktar = float(expense.get('miktar', 0) or 0)
            
            # Tarihi parse et
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
        
        # Tablo verisi - Yatay format (Aylar sütunlarda)
        table_data = []
        
        # Başlık satırı (Aylar)
        header_row = [tr('col_months', lang)] + months
        table_data.append(header_row)
        
        # Tutar satırı
        amount_row = [tr('total', lang).upper()] + [f"{monthly_totals[i+1]:,.2f} ₺" for i in range(12)]
        table_data.append(amount_row)
        
        # Sütun genişlikleri
        col_widths = [2*cm] + [2*cm] * 12
        
        # Tablo oluştur
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Header stili
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C5DD3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), turkish_font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # İlk sütun (AY, TUTAR)
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F4F5FA')),
            ('FONTNAME', (0, 1), (0, -1), turkish_font_bold),
            ('FONTSIZE', (0, 1), (0, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            
            # Veri hücreleri
            ('FONTNAME', (1, 1), (-1, -1), turkish_font),
            ('FONTSIZE', (1, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (1, 1), (-1, -1), 6),
            ('TOPPADDING', (1, 1), (-1, -1), 6),
            
            # Kenarlıklar
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#6C5DD3')),
        ]))
        
        story.append(table)
        
        # Toplam hesapla
        total = sum(monthly_totals.values())
        story.append(Spacer(1, 1*cm))
        
        total_style = ParagraphStyle(
            'Total',
            fontName=turkish_font_bold,
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1A1D1F')
        )
        story.append(Paragraph(f'<b>{tr("yearly_general_expenses", lang).upper()}: {total:,.2f} ₺</b>', total_style))
        
        # PDF oluştur
        doc.build(story)
        return True
        
    except Exception as e:
        return False
