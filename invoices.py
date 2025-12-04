# invoices.py
# -*- coding: utf-8 -*-
"""
Fatura işleme ve hesaplama fonksiyonları
"""

from imports import *


# ============================================================================
# FATURA İŞLEME SINIFI (Invoice Processor Class)
# ============================================================================
class InvoiceProcessor:
    """Fatura verilerini işleyen ve hesaplayan sınıf."""
    
    def __init__(self, backend):
        """
        InvoiceProcessor başlatıcısı.
        
        Args:
            backend: Backend instance (settings, exchange_rates, convert_currency erişimi için)
        """
        self.backend = backend
    
    def _to_decimal(self, value):
        """Bir değeri güvenli bir şekilde Decimal'e çevirir (para hesaplamaları için)."""
        if value is None or value == '': 
            return Decimal('0')
        
        try:
            # Eğer zaten Decimal ise direkt döndür
            if isinstance(value, Decimal):
                return value
            
            str_value = str(value).strip()
            
            if not str_value or str_value.lower() in ['none', 'null', 'n/a']:
                return Decimal('0')
            
            # Sadece rakam, nokta, virgül ve işaretleri bırak
            str_value = re.sub(r'[^\d.,\-+]', '', str_value)
            
            # Hem virgül hem nokta varsa format belirle
            if ',' in str_value and '.' in str_value:
                last_comma = str_value.rfind(',')
                last_dot = str_value.rfind('.')
                
                if last_comma > last_dot:
                    # Avrupa formatı: 1.234,56 -> 1234.56
                    str_value = str_value.replace('.', '').replace(',', '.')
                else:
                    # ABD formatı: 1,234.56 -> 1234.56
                    str_value = str_value.replace(',', '')
            elif ',' in str_value:
                # Sadece virgül var
                parts = str_value.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Ondalık ayırıcı: 123,45 -> 123.45
                    str_value = str_value.replace(',', '.')
                else:
                    # Binlik ayırıcı: 1,234 -> 1234
                    str_value = str_value.replace(',', '')
            
            return Decimal(str_value)
            
        except (ValueError, TypeError, AttributeError) as e:
            logging.warning(f"Decimal dönüşüm hatası: '{value}' -> Hata: {e}")
            return Decimal('0')

    def format_date(self, date_str):
        """Tarih string'ini 'dd.mm.yyyy' formatına çevirir."""
        # Boş string veya None ise None döndür (bugünün tarihi değil)
        if not date_str or (isinstance(date_str, str) and not date_str.strip()):
            return None
        
        # String değilse string'e çevir
        if not isinstance(date_str, str):
            date_str = str(date_str)
        
        date_str = date_str.strip()
        
        # Yaygın tarih formatlarını dene (4 basamaklı yıl)
        for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%d.%m.%Y")
            except ValueError:
                continue
        
        # 2 basamaklı yıl içeren ayırıcılı formatları dene (örn: 12.12.25 -> 12.12.2025)
        for fmt in ("%d.%m.%y", "%d-%m-%y", "%d/%m/%y"):
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%d.%m.%Y")
            except ValueError:
                continue
        
        # Sadece rakamları al
        cleaned_date = re.sub(r'[^0-9]', '', date_str)
        
        if len(cleaned_date) == 8:
            # İlk 4 karakter yıl gibi görünüyorsa (2000-2099 arası)
            if cleaned_date[:4] in [str(y) for y in range(2000, 2100)]:
                # YYYYaag formatı
                yil = cleaned_date[:4]
                ay = cleaned_date[4:6]
                gun = cleaned_date[6:8]
                try:
                    parsed_date = datetime(int(yil), int(ay), int(gun))
                    return parsed_date.strftime("%d.%m.%Y")
                except ValueError:
                    pass
            else:
                # ggaaYYYY formatı (12112025 gibi)
                gun = cleaned_date[:2]
                ay = cleaned_date[2:4]
                yil = cleaned_date[4:8]
                try:
                    parsed_date = datetime(int(yil), int(ay), int(gun))
                    return parsed_date.strftime("%d.%m.%Y")
                except ValueError:
                    pass
        elif len(cleaned_date) == 6:
            # ggaayy formatı (121125 -> 12.11.2025)
            gun = cleaned_date[:2]
            ay = cleaned_date[2:4]
            yil_short = cleaned_date[4:6]
            # 2000'li yıllara çevir
            yil = "20" + yil_short
            try:
                parsed_date = datetime(int(yil), int(ay), int(gun))
                return parsed_date.strftime("%d.%m.%Y")
            except ValueError:
                pass
        
        # Geçersiz tarih ise bugünün tarihini döndür
        return datetime.now().strftime("%d.%m.%Y")

    def process_invoice_data(self, invoice_data):
        """
        Fatura verilerini işler, doğrular ve KDV/kur hesaplamalarını yapar.
        Decimal kullanarak yüksek hassasiyetle para hesaplamaları yapar.
        """
        # Sadece toplam tutar zorunlu olsun, diğer alanlar boş kalabilir
        toplam_tutar = self._to_decimal(invoice_data.get('toplam_tutar', 0))
        if toplam_tutar <= 0:
            logging.warning(f"Toplam tutar girilmemiş veya geçersiz: {invoice_data}")
            return None
        
        try:            
            processed = invoice_data.copy()
            
            # Boş alanları olduğu gibi bırak
            processed['fatura_no'] = processed.get('fatura_no', '').strip()
            processed['firma'] = processed.get('firma', '').strip()
            processed['malzeme'] = processed.get('malzeme', '').strip()
            
            # Tarih işleme - kullanıcı girişi varsa onu kullan, yoksa bugünün tarihini kullan
            input_date = processed.get('tarih', '')
            if input_date and input_date.strip():
                formatted_date = self.format_date(input_date)
                processed['tarih'] = formatted_date if formatted_date else datetime.now().strftime("%d.%m.%Y")
            else:
                processed['tarih'] = datetime.now().strftime("%d.%m.%Y")
            
            processed['miktar'] = str(processed.get('miktar', '')).strip()
            
            toplam_tutar = self._to_decimal(processed.get('toplam_tutar', 0))
            kdv_yuzdesi = self._to_decimal(processed.get('kdv_yuzdesi', 0))
            kdv_tutari_input = self._to_decimal(processed.get('kdv_tutari', 0)) 
            birim = processed.get('birim', 'TL')
            
            logging.info(f"\n   🧾 FATURA İŞLEME BAŞLADI (KDV DAHİL SİSTEM - DECIMAL)")
            logging.info(f"   📋 Giriş Verileri:")
            logging.info(f"     - Girilen Tutar (KDV DAHİL): {toplam_tutar} {birim}")
            logging.info(f"     - KDV Yüzdesi: {kdv_yuzdesi}%")
            
            # KDV yüzdesi kontrolü
            if kdv_yuzdesi <= 0:
                kdv_yuzdesi = self._to_decimal(self.backend.settings.get('kdv_yuzdesi', 20.0))
                logging.info(f"   ⚙️ KDV yüzdesi girilmedi, varsayılan kullanılıyor: {kdv_yuzdesi}%")
            
            # Manuel kur girişi kontrolü - önce kontrol et
            manual_usd_rate = invoice_data.get('manual_usd_rate', None)
            manual_eur_rate = invoice_data.get('manual_eur_rate', None)
            
            if manual_usd_rate and manual_usd_rate > 0:
                # Manuel USD kuru girilmiş (1 USD = ? TL formatında)
                usd_to_tl = manual_usd_rate
                logging.info(f"   💱 Manuel USD kuru kullanılıyor: 1 USD = {usd_to_tl} TL")
            else:
                # TCMB kurunu kullan
                current_rates = self.backend.exchange_rates
                usd_rate = current_rates.get('USD', 0)
                usd_to_tl = (1 / usd_rate) if usd_rate > 0 else 0
                logging.info(f"   💱 TCMB USD kuru kullanılıyor: 1 USD = {usd_to_tl} TL")
            
            if manual_eur_rate and manual_eur_rate > 0:
                # Manuel EUR kuru girilmiş (1 EUR = ? TL formatında)
                eur_to_tl = manual_eur_rate
                logging.info(f"   💱 Manuel EUR kuru kullanılıyor: 1 EUR = {eur_to_tl} TL")
            else:
                # TCMB kurunu kullan
                current_rates = self.backend.exchange_rates
                eur_rate = current_rates.get('EUR', 0)
                eur_to_tl = (1 / eur_rate) if eur_rate > 0 else 0
                logging.info(f"   💱 TCMB EUR kuru kullanılıyor: 1 EUR = {eur_to_tl} TL")

            # KDV DAHİL SİSTEM - Tüm girilen tutarlar KDV dahildir
            # KDV hesaplaması her zaman TL üzerinden yapılır
            if toplam_tutar > 0:
                try:
                    # Önce TL'ye çevir
                    conversion_rate = Decimal('1.0')
                    if birim == 'USD':
                        # Float'tan Decimal'e çevirirken string kullanmak daha güvenli
                        # Ancak float 'nan' veya 'inf' ise hata verebilir, kontrol et
                        if math.isnan(usd_to_tl) or math.isinf(usd_to_tl):
                            conversion_rate = Decimal('0')
                        else:
                            conversion_rate = Decimal(str(usd_to_tl))
                    elif birim == 'EUR':
                        if math.isnan(eur_to_tl) or math.isinf(eur_to_tl):
                            conversion_rate = Decimal('0')
                        else:
                            conversion_rate = Decimal(str(eur_to_tl))
                    
                    toplam_tutar_tl_decimal = toplam_tutar * conversion_rate
                    
                    # KDV dahil TL tutardan matrahı ve KDV tutarını hesapla (Decimal ile)
                    kdv_katsayisi = Decimal('1') + (kdv_yuzdesi / Decimal('100'))
                    
                    if kdv_katsayisi == 0:
                        matrah_tl = toplam_tutar_tl_decimal
                        kdv_tutari_tl = Decimal('0')
                    else:
                        matrah_tl = toplam_tutar_tl_decimal / kdv_katsayisi
                        kdv_tutari_tl = toplam_tutar_tl_decimal - matrah_tl
                    
                    # 5 ondalık basamağa yuvarla
                    matrah_tl = matrah_tl.quantize(Decimal('0.00001'))
                    kdv_tutari_tl = kdv_tutari_tl.quantize(Decimal('0.00001'))
                    
                    logging.info(f"   ✅ KDV DAHİL HESAPLAMA (TL ÜZERİNDEN):")
                    logging.info(f"     - Girilen Tutar: {toplam_tutar} {birim}")
                    logging.info(f"     - Kur: {conversion_rate}")
                    logging.info(f"     - TL Karşılığı: {toplam_tutar_tl_decimal} TL")
                    logging.info(f"     - KDV Katsayısı: {kdv_katsayisi}")
                    logging.info(f"     - Matrah (TL): {matrah_tl} TL")
                    logging.info(f"     - KDV Tutarı (TL): {kdv_tutari_tl} TL")
                    
                except Exception as calc_err:
                    logging.error(f"   ❌ Hesaplama hatası (Decimal): {calc_err}")
                    # Hata durumunda varsayılan değerler
                    matrah_tl = Decimal('0')
                    kdv_tutari_tl = Decimal('0')
                    toplam_tutar_tl_decimal = Decimal('0')
                    
            else:
                logging.error(f"   ❌ HATA: Toplam tutar girilmemiş!")
                return None
            
            toplam_kdv_dahil_tl = matrah_tl + kdv_tutari_tl

            # Sonuç verilerini hazırla - toplam_tutar_tl artık KDV DAHİL tutar
            # Tüm tutarları 5 ondalık basamağa yuvarla
            processed['toplam_tutar_tl'] = round(float(toplam_kdv_dahil_tl), 5)
            
            # USD ve EUR tutarlarını manuel kurlar ile hesapla
            if usd_to_tl > 0:
                processed['toplam_tutar_usd'] = round(float(toplam_kdv_dahil_tl) / usd_to_tl, 5)
            else:
                processed['toplam_tutar_usd'] = 0
                
            if eur_to_tl > 0:
                processed['toplam_tutar_eur'] = round(float(toplam_kdv_dahil_tl) / eur_to_tl, 5)
            else:
                processed['toplam_tutar_eur'] = 0
            
            processed['birim'] = birim 
            processed['kdv_yuzdesi'] = round(float(kdv_yuzdesi), 5)
            processed['kdv_dahil'] = 1  # Her zaman KDV dahil
            processed['kdv_tutari'] = round(float(kdv_tutari_tl), 5)
            processed['usd_rate'] = round(float(usd_to_tl), 5)
            processed['eur_rate'] = round(float(eur_to_tl), 5)
            
            logging.info(f"   📊 SONUÇ (TL CİNSİNDEN):")
            logging.info(f"     - Matrah: {matrah_tl:.2f} TL")
            logging.info(f"     - KDV Tutarı: {kdv_tutari_tl:.2f} TL") 
            logging.info(f"     - TOPLAM (KDV DAHİL): {toplam_kdv_dahil_tl:.2f} TL")
            logging.info(f"   ✅ İşlem başarılı!\n")
            
            return processed

        except (ValueError, TypeError) as e:
            logging.error(f"❌ Fatura veri işleme hatası: {e} - Veri: {invoice_data}")
            return None

    def process_genel_gider_data(self, gider_data):
        """Genel gider verilerini genel_gider.db formatına çevirir. Decimal kullanır."""
        if not gider_data:
            return None
        
        # Miktar alanını hem sayı hem metin olarak kabul et
        miktar_input = gider_data.get('miktar', '')
        if not miktar_input or str(miktar_input).strip() == '':
            logging.warning(f"Genel gider miktarı girilmemiş: {gider_data}")
            return None
        
        # Eğer sayısal bir değer ise float'a çevir, değilse string olarak bırak
        try:
            miktar_float = float(miktar_input)
            # 5 ondalık basamağa yuvarla
            miktar = round(miktar_float, 5)
        except:
            # Sayısal olmayan miktar değerlerini string olarak sakla
            miktar = str(miktar_input).strip()
        
        # Genel gider verilerini direkt format
        input_date = gider_data.get('tarih', '')
        if input_date and input_date.strip():
            formatted_date = self.format_date(input_date)
            tarih = formatted_date if formatted_date else datetime.now().strftime("%d.%m.%Y")
        else:
            tarih = datetime.now().strftime("%d.%m.%Y")
            
        processed = {
            'tarih': tarih,
            'tur': gider_data.get('tur', 'Genel Gider'),
            'miktar': miktar,
            'aciklama': gider_data.get('aciklama', '')
        }
        
        return processed


# ============================================================================
# FATURA YÖNETİM SINIFI (Invoice Manager Class)
# ============================================================================
class InvoiceManager:
    """Fatura operasyonlarını yöneten sınıf."""
    
    def __init__(self, backend):
        """
        InvoiceManager başlatıcısı.
        
        Args:
            backend: Backend instance (db, data_updated sinyal erişimi için)
        """
        self.backend = backend
        self.processor = InvoiceProcessor(backend)
    
    def handle_invoice_operation(self, operation, invoice_type, data=None, record_id=None, limit=None, offset=None, order_by=None):
        """Frontend için fatura işlem merkezi - 3 ayrı veritabanı ile."""
        
        if operation == 'add':
            processed_data = self.processor.process_invoice_data(data)
            if not processed_data:
                logging.error(f"❌ İşlenmiş veri boş! Ham veri: {data}")
                return False
            
            logging.info(f"🔹 Fatura ekleniyor -> Tip: {invoice_type}, Firma: {processed_data.get('firma', 'N/A')[:30]}")
            
            if invoice_type == 'outgoing':
                result = self.backend.db.add_gelir_invoice(processed_data)
                if result:
                    self._add_history_record('EKLEME', 'gelir', processed_data)
                    logging.info(f"✅ GELİR faturası eklendi (ID: {result})")
                else:
                    logging.error(f"❌ GELİR faturası eklenemedi!")
            elif invoice_type == 'incoming':
                result = self.backend.db.add_gider_invoice(processed_data)
                if result:
                    self._add_history_record('EKLEME', 'gider', processed_data)
                    logging.info(f"✅ GİDER faturası eklendi (ID: {result})")
                else:
                    logging.error(f"❌ GİDER faturası eklenemedi!")
            else:
                logging.error(f"❌ Geçersiz invoice_type: {invoice_type}")
                return False
                
            if result:
                if self.backend.on_data_updated: self.backend.on_data_updated()
                return True
            return False
        
        elif operation == 'update':
            processed_data = self.processor.process_invoice_data(data)
            if not processed_data:
                return False
            
            if invoice_type == 'outgoing':
                result = self.backend.db.update_gelir_invoice(record_id, processed_data)
                if result:
                    self._add_history_record('GÜNCELLEME', 'gelir', processed_data)
            elif invoice_type == 'incoming':
                result = self.backend.db.update_gider_invoice(record_id, processed_data)
                if result:
                    self._add_history_record('GÜNCELLEME', 'gider', processed_data)
            else:
                return False
                
            if result:
                if self.backend.on_data_updated: self.backend.on_data_updated()
                return True
            return False
        
        elif operation == 'delete':
            # Silmeden önce fatura bilgilerini al
            if invoice_type == 'outgoing':
                invoice_data = self.backend.db.get_gelir_invoice_by_id(record_id)
                result = self.backend.db.delete_gelir_invoice(record_id)
                if result and invoice_data:
                    self._add_history_record('SİLME', 'gelir', invoice_data)
            elif invoice_type == 'incoming':
                invoice_data = self.backend.db.get_gider_invoice_by_id(record_id)
                result = self.backend.db.delete_gider_invoice(record_id)
                if result and invoice_data:
                    self._add_history_record('SİLME', 'gider', invoice_data)
            else:
                return False
                
            if result:
                if self.backend.on_data_updated: self.backend.on_data_updated()
                return True
            return False
        
        elif operation == 'get':
            if invoice_type == 'outgoing':
                return self.backend.db.get_all_gelir_invoices(limit=limit, offset=offset, order_by=order_by)
            elif invoice_type == 'incoming':
                return self.backend.db.get_all_gider_invoices(limit=limit, offset=offset, order_by=order_by)
            else:
                return []
        
        elif operation == 'count':
            if invoice_type == 'outgoing':
                return self.backend.db.get_gelir_invoice_count()
            elif invoice_type == 'incoming':
                return self.backend.db.get_gider_invoice_count()
            else:
                return 0
        
        elif operation == 'get_by_id':
            if invoice_type == 'outgoing':
                return self.backend.db.get_gelir_invoice_by_id(record_id)
            elif invoice_type == 'incoming':
                return self.backend.db.get_gider_invoice_by_id(record_id)
            else:
                return None
        
        logging.warning(f"Geçersiz fatura operasyonu: {operation}")
        return False

    def handle_genel_gider_operation(self, operation, data=None, record_id=None, limit=None, offset=None):
        """Genel gider işlemleri için özel metod - ayrı veritabanı ile."""
        
        if operation == 'get':
            return self.backend.db.get_all_genel_gider(limit=limit, offset=offset)
        
        elif operation == 'count':
            return self.backend.db.get_genel_gider_count()
        
        elif operation == 'get_by_id':
            return self.backend.db.get_genel_gider_by_id(record_id)
        
        return None

    def delete_multiple_invoices(self, invoice_type, invoice_ids):
        """Çoklu fatura silme işlemi - 3 ayrı veritabanı ile."""
        try:
            if invoice_type == 'outgoing':
                deleted_count = self.backend.db.delete_multiple_gelir_invoices(invoice_ids)
            elif invoice_type == 'incoming':
                deleted_count = self.backend.db.delete_multiple_gider_invoices(invoice_ids)
            else:
                return 0
                
            if deleted_count > 0:
                if self.backend.on_data_updated: self.backend.on_data_updated()
            return deleted_count
        except Exception as e:
            logging.error(f"Çoklu {invoice_type} faturası silme hatası: {e}")
            return 0

    def _add_history_record(self, operation_type, invoice_type, invoice_data=None, details=None):
        """Fatura işlemlerinde geçmiş kaydı ekler."""
        try:
            invoice_date = None
            firma = None
            amount = None
            
            if invoice_data:
                invoice_date = invoice_data.get('tarih')
                firma = invoice_data.get('firma') or invoice_data.get('tur')
                amount = invoice_data.get('toplam_tutar_tl') or invoice_data.get('miktar')
            
            # İşlem tipine göre detay mesajı oluştur
            if not details:
                if operation_type == 'EKLEME':
                    details = f"{invoice_type.title()} fatura eklendi"
                elif operation_type == 'GÜNCELLEME':
                    details = f"{invoice_type.title()} fatura güncellendi"
                elif operation_type == 'SİLME':
                    details = f"{invoice_type.title()} fatura silindi"
                else:
                    details = f"{operation_type} işlemi"
            
            self.backend.db.add_history_record(operation_type, invoice_type, invoice_date, firma, amount, details)
            
        except Exception as e:
            logging.error(f"Geçmiş kaydı ekleme hatası: {e}")


# ============================================================================
# DÖNEMSEL GELİR HESAPLAMALARI (Periodic Income Calculations)
# ============================================================================

class PeriodicIncomeCalculator:
    """Dönemsel gelir, gider ve kar/zarar hesaplamaları yapan sınıf."""
    
    def __init__(self, backend):
        """
        PeriodicIncomeCalculator başlatıcısı.
        
        Args:
            backend: Backend instance (db, settings erişimi için)
        """
        self.backend = backend
    
    def get_summary_data(self):
        """Gelir, gider ve kar/zarar özetini hesaplar - 3 ayrı veritabanı ile."""
        # Gelir toplamı (KDV dahil)
        gelir_cursor = self.backend.db.gelir_conn.cursor()
        gelir_cursor.execute("SELECT SUM(toplam_tutar_tl), SUM(kdv_tutari) FROM invoices")
        gelir_row = gelir_cursor.fetchone()
        total_revenue_kdv_dahil = gelir_row[0] or 0
        total_revenue_kdv = gelir_row[1] or 0
        total_revenue = total_revenue_kdv_dahil - total_revenue_kdv  # Matrah (KDV hariç)
        
        # Fatura giderleri toplamı (KDV dahil)
        gider_cursor = self.backend.db.gider_conn.cursor()
        gider_cursor.execute("SELECT SUM(toplam_tutar_tl), SUM(kdv_tutari) FROM invoices")
        gider_row = gider_cursor.fetchone()
        invoice_expenses_kdv_dahil = gider_row[0] or 0
        invoice_expenses_kdv = gider_row[1] or 0
        invoice_expenses = invoice_expenses_kdv_dahil - invoice_expenses_kdv  # Matrah (KDV hariç)
        
        # Genel giderler toplamı
        genel_gider_cursor = self.backend.db.genel_gider_conn.cursor()
        genel_gider_cursor.execute("SELECT SUM(miktar) FROM general_expenses")
        general_expenses = genel_gider_cursor.fetchone()[0] or 0
        
        # Toplam gider
        total_expense = invoice_expenses + general_expenses
        
        # Aylık veriler
        monthly_income = [0] * 12
        monthly_expenses = [0] * 12
        current_year = datetime.now().year
        
        # Gelir aylık dağılım
        gelir_cursor.execute("""
            SELECT tarih, toplam_tutar_tl FROM invoices 
            WHERE tarih LIKE ?
        """, (f"%.{current_year}",))
        
        for row in gelir_cursor.fetchall():
            try:
                parts = row[0].split('.')
                if len(parts) == 3:
                    month = int(parts[1]) - 1
                    monthly_income[month] += row[1]
            except:
                continue
        
        # Fatura giderleri aylık dağılım
        gider_cursor.execute("""
            SELECT tarih, toplam_tutar_tl FROM invoices 
            WHERE tarih LIKE ?
        """, (f"%.{current_year}",))
        
        for row in gider_cursor.fetchall():
            try:
                parts = row[0].split('.')
                if len(parts) == 3:
                    month = int(parts[1]) - 1
                    monthly_expenses[month] += row[1]
            except:
                continue
                
        # Genel giderler aylık dağılım
        genel_gider_cursor.execute("""
            SELECT tarih, miktar FROM general_expenses 
            WHERE tarih LIKE ?
        """, (f"%.{current_year}",))
        
        for row in genel_gider_cursor.fetchall():
            try:
                parts = row[0].split('.')
                if len(parts) == 3:
                    month = int(parts[1]) - 1
                    monthly_expenses[month] += row[1]
            except:
                continue
        
        active_income_months = sum(1 for income in monthly_income if income > 0)
        total_income_this_year = sum(monthly_income)
        monthly_average = total_income_this_year / active_income_months if active_income_months > 0 else 0
        
        net_profit = total_revenue - total_expense

        return {
            "son_gelirler": total_revenue,
            "toplam_giderler": total_expense,
            "net_kar": net_profit,
            "aylik_ortalama": monthly_average,
        }, {
            "income": monthly_income,
            "expenses": monthly_expenses
        }
    
    def get_year_range(self):
        """Fatura verilerinde bulunan tüm yılların listesini döndürür - 3 ayrı veritabanı ile."""
        years_set = set()
        current_year = datetime.now().year
        
        years_set.add(str(current_year))
        
        # Gelir veritabanından yılları al
        gelir_invoices = self.backend.db.get_all_gelir_invoices()
        for inv in gelir_invoices:
            try:
                if 'tarih' in inv and inv['tarih']:
                    date_obj = datetime.strptime(inv['tarih'], "%d.%m.%Y")
                    years_set.add(str(date_obj.year))
            except (ValueError, KeyError):
                continue
        
        # Gider veritabanından yılları al
        gider_invoices = self.backend.db.get_all_gider_invoices()
        for inv in gider_invoices:
            try:
                if 'tarih' in inv and inv['tarih']:
                    date_obj = datetime.strptime(inv['tarih'], "%d.%m.%Y")
                    years_set.add(str(date_obj.year))
            except (ValueError, KeyError):
                continue
        
        # Genel gider veritabanından yılları al
        genel_gider_list = self.backend.db.get_all_genel_gider()
        for gider in genel_gider_list:
            try:
                if 'tarih' in gider and gider['tarih']:
                    date_obj = datetime.strptime(gider['tarih'], "%d.%m.%Y")
                    years_set.add(str(date_obj.year))
            except (ValueError, KeyError):
                continue
        
        return sorted(list(years_set), reverse=True)
    
    def get_calculations_for_year(self, year):
        """Belirli bir yıl için aylık ve çeyrek dönem hesaplamaları - 3 ayrı veritabanı ile."""
        # Vergi oranını güvenli şekilde float'a dönüştür
        tax_rate_raw = self.backend.settings.get('kurumlar_vergisi_yuzdesi', 22.0)
        tax_rate = float(tax_rate_raw) / 100.0
        
        monthly_results = []
        
        for month in range(1, 13):
            # Gelir hesapla - toplam_tutar_tl artık KDV dahil, kar için matrah hesaplayalım
            gelir_cursor = self.backend.db.gelir_conn.cursor()
            gelir_cursor.execute("""
                SELECT SUM(toplam_tutar_tl), SUM(kdv_tutari) 
                FROM invoices 
                WHERE tarih LIKE ?
            """, (f"%.{month:02d}.{year}",))
            gelir_row = gelir_cursor.fetchone()
            kesilen_kdv_dahil = gelir_row[0] or 0
            kesilen_kdv = gelir_row[1] or 0
            kesilen_matrah = kesilen_kdv_dahil - kesilen_kdv  # KDV dahil tutardan matrahı çıkar
            
            # Fatura giderleri hesapla
            gider_cursor = self.backend.db.gider_conn.cursor()
            gider_cursor.execute("""
                SELECT SUM(toplam_tutar_tl), SUM(kdv_tutari) 
                FROM invoices 
                WHERE tarih LIKE ?
            """, (f"%.{month:02d}.{year}",))
            gider_row = gider_cursor.fetchone()
            fatura_giderleri_kdv_dahil = gider_row[0] or 0
            fatura_gider_kdv = gider_row[1] or 0
            fatura_giderleri_matrah = fatura_giderleri_kdv_dahil - fatura_gider_kdv
            
            # Genel giderleri hesapla
            genel_gider_cursor = self.backend.db.genel_gider_conn.cursor()
            genel_gider_cursor.execute("""
                SELECT SUM(miktar) 
                FROM general_expenses 
                WHERE tarih LIKE ?
            """, (f"%.{month:02d}.{year}",))
            genel_gider_row = genel_gider_cursor.fetchone()
            genel_giderler = genel_gider_row[0] or 0
            
            # Toplam gider (matrah bazında)
            toplam_gider_matrah = fatura_giderleri_matrah + genel_giderler
            
            monthly_results.append({
                'kesilen': kesilen_matrah,  # Kar hesabı için matrah kullanılıyor
                'gelen': toplam_gider_matrah,
                'kdv': kesilen_kdv - fatura_gider_kdv  # Genel giderlerde KDV yok
            })
        
        quarterly_results = []
        cumulative_profit = 0
        for quarter in range(4):
            start_month_idx = quarter * 3
            end_month_idx = start_month_idx + 3
            
            period_income = sum(m['kesilen'] for m in monthly_results[start_month_idx:end_month_idx])
            period_expense = sum(m['gelen'] for m in monthly_results[start_month_idx:end_month_idx])
            
            cumulative_profit += (period_income - period_expense)
            
            tax_for_period = cumulative_profit * tax_rate if cumulative_profit > 0 else 0
            
            paid_tax_in_previous_quarters = sum(q.get('vergi', 0) for q in quarterly_results)
            payable_tax = tax_for_period - paid_tax_in_previous_quarters
            
            quarterly_results.append({
                'kar': cumulative_profit, 
                'vergi': tax_for_period,
                'odenecek_kv': payable_tax if payable_tax > 0 else 0
            })
        
        return monthly_results, quarterly_results
    
    def get_yearly_summary(self, year):
        """Belirli bir yıl için yıllık özet - 3 ayrı veritabanı ile."""
        
        # Gelir hesapla (KDV dahil tutardan matrahı çıkar)
        gelir_cursor = self.backend.db.gelir_conn.cursor()
        gelir_cursor.execute("""
            SELECT SUM(toplam_tutar_tl), SUM(kdv_tutari) FROM invoices 
            WHERE tarih LIKE ?
        """, (f"%.{year}",))
        gelir_row = gelir_cursor.fetchone()
        gelir_kdv_dahil = gelir_row[0] or 0
        gelir_kdv = gelir_row[1] or 0
        gelir_matrah = gelir_kdv_dahil - gelir_kdv
        
        # Fatura giderleri hesapla (KDV dahil tutardan matrahı çıkar)
        gider_cursor = self.backend.db.gider_conn.cursor()
        gider_cursor.execute("""
            SELECT SUM(toplam_tutar_tl), SUM(kdv_tutari) FROM invoices 
            WHERE tarih LIKE ?
        """, (f"%.{year}",))
        gider_row = gider_cursor.fetchone()
        fatura_giderleri_kdv_dahil = gider_row[0] or 0
        fatura_giderleri_kdv = gider_row[1] or 0
        fatura_giderleri_matrah = fatura_giderleri_kdv_dahil - fatura_giderleri_kdv
        
        # Genel giderleri hesapla
        genel_gider_cursor = self.backend.db.genel_gider_conn.cursor()
        genel_gider_cursor.execute("""
            SELECT SUM(miktar) FROM general_expenses 
            WHERE tarih LIKE ?
        """, (f"%.{year}",))
        genel_giderler = genel_gider_cursor.fetchone()[0] or 0
        
        # Toplam gider (matrah bazında)
        toplam_gider_matrah = fatura_giderleri_matrah + genel_giderler
        
        brut_kar = gelir_matrah - toplam_gider_matrah
        
        # Vergi oranını güvenli şekilde float'a dönüştür
        tax_rate_raw = self.backend.settings.get('kurumlar_vergisi_yuzdesi', 22.0)
        tax_rate = float(tax_rate_raw) / 100
        vergi = brut_kar * tax_rate if brut_kar > 0 else 0
        
        return {
            'toplam_gelir': gelir_matrah,
            'toplam_gider': toplam_gider_matrah,
            'yillik_kar': brut_kar - vergi, # Net kar
            'vergi_tutari': vergi,
            'vergi_yuzdesi': tax_rate * 100
        }
