# backend.py
# -*- coding: utf-8 -*-

# Merkezi import dosyasından gerekli modülleri al
from imports import *
from db import Database
from invoices import InvoiceProcessor, InvoiceManager, PeriodicIncomeCalculator


class Backend:
    """Uygulamanın ana iş mantığını yöneten sınıf."""

    class Event:
        def __init__(self):
            self.handlers = []
        def connect(self, handler):
            self.handlers.append(handler)
        def emit(self, *args, **kwargs):
            for handler in self.handlers:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    pass

    def __init__(self):
        """
        Backend başlatıcısı.
        """
        # Callback fonksiyonları (Flet uyumlu)
        self.on_data_updated = None  # Frontend tarafından atanacak
        self.on_status_updated = None  # Frontend tarafından atanacak
        
        self.db = Database()
        self.settings = self.db.get_all_settings()
        # Vergi oranını float'a dönüştür
        if 'kurumlar_vergisi_yuzdesi' in self.settings:
            try:
                self.settings['kurumlar_vergisi_yuzdesi'] = float(self.settings['kurumlar_vergisi_yuzdesi'])
            except (ValueError, TypeError):
                self.settings['kurumlar_vergisi_yuzdesi'] = 22.0
        else:
            self.settings['kurumlar_vergisi_yuzdesi'] = 22.0

        # Fatura işleyici ve yönetici
        self.invoice_processor = InvoiceProcessor(self)
        self.invoice_manager = InvoiceManager(self)
        
        # Dönemsel gelir hesaplayıcı
        self.periodic_calculator = PeriodicIncomeCalculator(self)
        
        # QR Entegrasyon - Lazy loading (gerektiğinde yüklenecek)
        self._qr_integrator = None
        
        # Sinyaller
        self.data_updated = self.Event() # Veri güncelleme sinyali
        
        # Döviz kurları
        self.exchange_rates = {
            'USD': 0.0,
            'EUR': 0.0
        }
        
        # Kurları başlangıçta bir kez çek
        self.update_exchange_rates()

    @property
    def qr_integrator(self):
        """QR entegratörünü lazy loading ile başlatır - OPTİMİZE EDİLMİŞ MODÜL."""
        if self._qr_integrator is None:
            from fromqr import QRInvoiceIntegrator
            self._qr_integrator = QRInvoiceIntegrator(self)
            logging.info("✅ QR Entegratörü başlatıldı (optimize edilmiş)")
        return self._qr_integrator
    
    def start_timers(self):
        """
        Uygulama döngüsü başladıktan sonra çağrılacak zamanlayıcıları başlatır.
        Threading.Timer ile 5 dakikada bir kur güncellemesi yapar.
        """
        def schedule_rate_update():
            self.update_exchange_rates()
            # 5 dakika sonra tekrar çalıştır
            self.rate_update_timer = threading.Timer(300.0, schedule_rate_update)
            self.rate_update_timer.daemon = True
            self.rate_update_timer.start()
        
        # İlk timer'ı başlat
        self.rate_update_timer = threading.Timer(300.0, schedule_rate_update)
        self.rate_update_timer.daemon = True
        self.rate_update_timer.start()
        

    def update_exchange_rates(self):
        """Döviz kurlarını TCMB'den çeker, başarısız olursa önceki günün kurlarını kullanır."""
        
        # Önce TCMB'den deneyelim
        if self._fetch_from_tcmb():
            return
        
        # TCMB başarısız olursa önceki günün kurlarını deneyelim
        if self._fetch_tcmb_previous_day():
            if self.on_status_updated:
                self.on_status_updated("TCMB önceki gün kurları kullanılıyor.", 4000)
            return
        
        # Önceki gün de başarısız olursa veritabanından son kaydedilen kurları yükle
        if self._load_rates_from_db():
            if self.on_status_updated:
                self.on_status_updated("Son kaydedilen döviz kurları kullanılıyor.", 4000)
            return
        
        # Hiçbir kaynak yoksa gerçekçi varsayılan değerleri kullan
        logging.warning("Tüm döviz kuru kaynakları başarısız. Varsayılan kurlar kullanılıyor.")
        self.exchange_rates = {'USD': 0.030, 'EUR': 0.028} 
        if self.on_status_updated:
            self.on_status_updated("İnternet bağlantısı yok! Varsayılan kurlar kullanılıyor.", 5000)
    
    def _fetch_from_tcmb(self):
        """TCMB'den bugünün banknote selling kurlarını çeker."""
        try:
            # TCMB today.xml URL'i sabit
            url = "https://www.tcmb.gov.tr/kurlar/today.xml"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            tree = ET.fromstring(response.content)
            
            usd_sell = None
            eur_sell = None
            
            for currency in tree.findall('./Currency'):
                currency_code = currency.get('Kod')
                if currency_code == 'USD':
                    # Sadece BanknoteSelling kullan
                    usd_sell_node = currency.find('BanknoteSelling')
                    if usd_sell_node is not None and usd_sell_node.text:
                        usd_sell = float(usd_sell_node.text.replace(',', '.'))
                elif currency_code == 'EUR':
                    # Sadece BanknoteSelling kullan
                    eur_sell_node = currency.find('BanknoteSelling')
                    if eur_sell_node is not None and eur_sell_node.text:
                        eur_sell = float(eur_sell_node.text.replace(',', '.'))
            
            if usd_sell and eur_sell:
                usd_rate = 1.0 / usd_sell
                eur_rate = 1.0 / eur_sell
                self.exchange_rates = {'USD': usd_rate, 'EUR': eur_rate}
                self._save_rates_to_db()  # Kurları veritabanına kaydet
                if self.on_status_updated:
                    self.on_status_updated("TCMB döviz kurları güncellendi.", 3000)
                logging.info(f"TCMB kurları (BanknoteSelling): 1 USD = {usd_sell:.4f} TL, 1 EUR = {eur_sell:.4f} TL")
                return True
        except Exception as e:
            logging.error(f"TCMB bugünün kurlarından kur alınamadı: {e}")
        return False
    
    def _fetch_tcmb_previous_day(self):
        """TCMB'den önceki iş gününün banknote selling kurlarını çeker."""
        try:
            # Son 7 günü dene (hafta sonu ve tatilleri atlamak için)
            for days_back in range(1, 8):
                prev_date = datetime.now() - timedelta(days=days_back)
                url = f"https://www.tcmb.gov.tr/kurlar/{prev_date.year}{prev_date.month:02d}/{prev_date.day:02d}{prev_date.month:02d}{prev_date.year}.xml"
                
                try:
                    response = requests.get(url, timeout=5)
                    response.raise_for_status()
                    
                    tree = ET.fromstring(response.content)
                    
                    usd_sell = None
                    eur_sell = None
                    
                    for currency in tree.findall('./Currency'):
                        currency_code = currency.get('Kod')
                        if currency_code == 'USD':
                            usd_sell_node = currency.find('BanknoteSelling')
                            if usd_sell_node is not None and usd_sell_node.text:
                                usd_sell = float(usd_sell_node.text.replace(',', '.'))
                        elif currency_code == 'EUR':
                            eur_sell_node = currency.find('BanknoteSelling')
                            if eur_sell_node is not None and eur_sell_node.text:
                                eur_sell = float(eur_sell_node.text.replace(',', '.'))
                    
                    if usd_sell and eur_sell:
                        usd_rate = 1.0 / usd_sell
                        eur_rate = 1.0 / eur_sell
                        self.exchange_rates = {'USD': usd_rate, 'EUR': eur_rate}
                        self._save_rates_to_db()
                        logging.info(f"TCMB önceki gün kurları ({prev_date.strftime('%d.%m.%Y')} - BanknoteSelling): 1 USD = {usd_sell:.4f} TL, 1 EUR = {eur_sell:.4f} TL")
                        return True
                except:
                    continue  # Bu tarihte kur yoksa bir sonraki güne geç
            
        except Exception as e:
            logging.error(f"TCMB önceki gün kurlarından kur alınamadı: {e}")
        return False
    
    def _save_rates_to_db(self):
        """Güncel döviz kurlarını veritabanına kaydeder."""
        try:
            self.db.save_exchange_rates(self.exchange_rates)
        except Exception as e:
            logging.error(f"Kurları veritabanına kaydetme hatası: {e}")
    
    def _load_rates_from_db(self):
        """Veritabanından son kaydedilen kurları yükler."""
        try:
            rates = self.db.load_exchange_rates()
            if rates:
                self.exchange_rates = rates
                logging.info(f"Veritabanından yüklenen kurlar: {self.exchange_rates}")
                return True
        except Exception as e:
            logging.error(f"Veritabanından kur yükleme hatası: {e}")
        return False

    def convert_currency(self, amount, from_currency, to_currency):
        """
        Para birimleri arasında dönüşüm yapar.
        Decimal ve float değerleri destekler.
        Tüm sonuçlar 5 ondalık basamağa yuvarlanır.
        """
        if not amount:
            return 0.0
        
        # Decimal'i float'a çevir
        if isinstance(amount, Decimal):
            amount = float(amount)
        
        from_currency = self._normalize_currency(from_currency)
        to_currency = self._normalize_currency(to_currency)
        
        if from_currency == to_currency:
            return round(amount, 5)
        
        if from_currency == 'TRY':
            rate = self.exchange_rates.get(to_currency)
            return round(amount * rate, 5) if rate else 0.0
        
        if to_currency == 'TRY':
            rate = self.exchange_rates.get(from_currency)
            return round(amount / rate, 5) if rate else 0.0
        
        try_amount = self.convert_currency(amount, from_currency, 'TRY')
        return round(self.convert_currency(try_amount, 'TRY', to_currency), 5)
    
    def _normalize_currency(self, currency):
        """Para birimi kodunu normalize eder (TL -> TRY)."""
        if not currency:
            return 'TRY'
        
        currency = str(currency).upper().strip()
        
        if currency in ['TL', 'TRL', 'TÜRK LİRASI', 'TURK LIRASI', 'TURKISH LIRA']:
            return 'TRY'
        
        return currency

    def handle_invoice_operation(self, operation, invoice_type, data=None, record_id=None, limit=None, offset=None, order_by=None):
        """Frontend için fatura işlem merkezi - InvoiceManager'a yönlendirir."""
        return self.invoice_manager.handle_invoice_operation(operation, invoice_type, data, record_id, limit, offset, order_by)

    def handle_genel_gider_operation(self, operation, data=None, record_id=None, limit=None, offset=None):
        """Genel gider işlemleri - InvoiceManager'a yönlendirir."""
        return self.invoice_manager.handle_genel_gider_operation(operation, data, record_id, limit, offset)

    def delete_multiple_invoices(self, invoice_type, invoice_ids):
        """Çoklu fatura silme - InvoiceManager'a yönlendirir."""
        return self.invoice_manager.delete_multiple_invoices(invoice_type, invoice_ids)

    # ============================================================================
    # DÖNEMSEL GELİR HESAPLAMALARI (Periodic Income Calculations)
    # ============================================================================

    def get_summary_data(self):
        """Gelir, gider ve kar/zarar özetini hesaplar - PeriodicIncomeCalculator'a yönlendirir."""
        return self.periodic_calculator.get_summary_data()
    
    def get_year_range(self):
        """Fatura verilerinde bulunan tüm yılların listesini döndürür - PeriodicIncomeCalculator'a yönlendirir."""
        return self.periodic_calculator.get_year_range()
    
    def get_calculations_for_year(self, year):
        """Belirli bir yıl için aylık ve çeyrek dönem hesaplamaları - PeriodicIncomeCalculator'a yönlendirir."""
        return self.periodic_calculator.get_calculations_for_year(year)
    
    def get_yearly_summary(self, year):
        """Belirli bir yıl için yıllık özet - PeriodicIncomeCalculator'a yönlendirir."""
        return self.periodic_calculator.get_yearly_summary(year)

    # ============================================================================
    # İŞLEM GEÇMİŞİ YÖNETİMİ (History Management)
    # ============================================================================
    def get_recent_history(self, limit=20):
        """Son işlem geçmişini getirir."""
        return self.db.get_recent_history(limit)

    def get_history_by_date_range(self, start_date, end_date, limit=100):
        """Tarih aralığına göre işlem geçmişini getirir."""
        return self.db.get_history_by_date_range(start_date, end_date, limit)

    def clear_old_history(self, days_to_keep=90):
        """Eski geçmiş kayıtlarını temizler."""
        deleted_count = self.db.clear_old_history(days_to_keep)
        return deleted_count

    # ============================================================================
    # AYARLAR YÖNETİMİ (Settings Management)
    # ============================================================================
    
    def save_setting(self, key, value):
        """Ayarları kaydeder ve cache'i günceller."""
        # Database'e kaydet
        self.db.save_setting(key, value)
        # Cache'i güncelle ve türüne göre dönüştür
        if key == 'kurumlar_vergisi_yuzdesi':
            self.settings[key] = float(value)
        else:
            self.settings[key] = value
        # Veri güncellendiği callback'ini çağır
        if self.on_data_updated:
            self.on_data_updated()
        return True

    # ============================================================================
    # GÜNCELLEME YÖNETİMİ (Update Management)
    # ============================================================================
    
    def check_for_updates(self):
        """
        Uygulama güncellemelerini kontrol eder.
        Şimdilik placeholder olarak False döndürür.
        """
        # İleride buraya GitHub API veya başka bir kaynak üzerinden versiyon kontrolü eklenebilir.
        return {"update_available": False}

    def download_and_install_update(self):
        """
        Güncellemeyi indirir ve kurar.
        Şimdilik placeholder.
        """
        pass

    # ============================================================================
    # YARDIMCI FONKSİYONLAR (Helper Functions)
    # ============================================================================
    
    def _is_in_month_year(self, date_str, month, year):
        """Tarihin belirtilen ay ve yılda olup olmadığını kontrol eder."""
        try:
            if not date_str: return False
            parts = date_str.split('.')
            if len(parts) == 3:
                return int(parts[1]) == month and int(parts[2]) == year
            return False
        except (ValueError, IndexError):
            return False
    
    def _is_in_year(self, date_str, year):
        """Tarihin belirtilen yılda olup olmadığını kontrol eder."""
        try:
            if not date_str: return False
            parts = date_str.split('.')
            if len(parts) == 3:
                return int(parts[2]) == year
            return False
        except (ValueError, IndexError):
            return False
    
    def format_date(self, date_str):
        """Tarih string'ini DD.MM.YYYY formatına dönüştürür."""
        if not date_str:
            return datetime.now().strftime("%d.%m.%Y")
        
        try:
            # Zaten DD.MM.YYYY formatındaysa direkt döndür
            if re.match(r'^\d{2}\.\d{2}\.\d{4}$', str(date_str)):
                return str(date_str)
            
            # YYYY-MM-DD formatı
            if re.match(r'^\d{4}-\d{2}-\d{2}', str(date_str)):
                date_obj = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
                return date_obj.strftime('%d.%m.%Y')
            
            # DD/MM/YYYY formatı
            if re.match(r'^\d{2}/\d{2}/\d{4}$', str(date_str)):
                return str(date_str).replace('/', '.')
            
            # Varsayılan olarak bugünün tarihi
            return datetime.now().strftime("%d.%m.%Y")
        except Exception as e:
            logging.warning(f"Tarih formatı dönüştürülemedi: {date_str}, hata: {e}")
            return datetime.now().strftime("%d.%m.%Y")
    
    # ============================================================================
    # QR İŞLEMLERİ - ENTEGRE SİSTEM (QR Operations - Integrated System)
    # ============================================================================
     
    def process_qr_files_in_folder(self, folder_path, max_workers=8, status_callback=None):
        """
        QR dosyalarını işler - qrayiklanmis.py modülüne yönlendirir.
        
        Args:
            folder_path: İşlenecek dosyaların klasör yolu
            max_workers: Paralel işlem sayısı
            status_callback: İlerleme bildirimi için callback (opsiyonel)
            
        Returns:
            list: QR işleme sonuçları
        """
        # Callback wrapper - hem backend hem de frontend callback'i çağır
        def combined_callback(msg, duration):
            # Backend status callback'ini çağır
            if self.on_status_updated:
                self.on_status_updated(msg, duration)
            # Frontend callback varsa çağır
            if status_callback:
                return status_callback(msg, duration)
            return True
        
        # QR entegratörüne callback'i geçir
        return self.qr_integrator.process_qr_files_in_folder(
            folder_path, 
            max_workers, 
            status_callback=combined_callback if status_callback else None
        )
    
    def add_invoices_from_qr_data(self, qr_results, invoice_type):
        """
        QR sonuçlarını veritabanına ekler - MANUEL TİP SEÇİMİ
        
        Args:
            qr_results: QR işleme sonuçları
            invoice_type: 'outgoing' (gelir) veya 'incoming' (gider)
            
        Returns:
            dict: {
                'success': bool,
                'added': int,
                'failed': int,
                'total': int,
                'invoice_type': str,
                'processing_details': list
            }
        """
        return self.qr_integrator.add_invoices_from_qr_data(qr_results, invoice_type)

    def fetch_historical_rates(self, date_str):
        """
        Belirtilen tarih için TCMB'den döviz kurlarını (BanknoteSelling) çeker.
        Eğer o tarihte veri yoksa (hafta sonu/tatil), geriye doğru giderek ilk iş gününü bulur.
        
        Args:
            date_str: 'DD.MM.YYYY' formatında tarih stringi
            
        Returns:
            dict: {'USD': rate, 'EUR': rate} (TL karşılığı) veya None
        """
        try:
            if not date_str:
                return None
                
            # Tarihi parse et
            try:
                target_date = datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                logging.warning(f"Geçersiz tarih formatı: {date_str}")
                return None
            
            # En fazla 10 gün geriye git (bayram tatilleri vs. için)
            for i in range(10):
                current_date = target_date - timedelta(days=i)
                
                # Bugünün tarihi ise today.xml kullan
                if current_date.date() == datetime.now().date():
                    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
                else:
                    # YYYYMM/DDMMYYYY.xml formatı
                    url = f"https://www.tcmb.gov.tr/kurlar/{current_date.year}{current_date.month:02d}/{current_date.day:02d}{current_date.month:02d}{current_date.year}.xml"
                
                try:
                    
                    response = requests.get(url, timeout=3)
                    if response.status_code == 404:
                        continue # Bu tarihte yok, bir gün geriye git
                        
                    response.raise_for_status()
                    
                    tree = ET.fromstring(response.content)
                    
                    usd_sell = None
                    eur_sell = None
                    
                    for currency in tree.findall('./Currency'):
                        currency_code = currency.get('Kod')
                        if currency_code == 'USD':
                            node = currency.find('BanknoteSelling')
                            if node is not None and node.text:
                                usd_sell = float(node.text.replace(',', '.'))
                        elif currency_code == 'EUR':
                            node = currency.find('BanknoteSelling')
                            if node is not None and node.text:
                                eur_sell = float(node.text.replace(',', '.'))
                    
                    if usd_sell and eur_sell:                        
                        return {'USD': usd_sell, 'EUR': eur_sell}
                        
                except Exception as e:
                    # logging.warning(f"Tarihli kur çekme hatası ({current_date.strftime('%d.%m.%Y')}): {e}")
                    continue
            
            print(f"   ⚠️ {date_str} için uygun kur bulunamadı (10 gün geriye gidildi).")
            return None
            
        except Exception as e:
            print(f"❌ fetch_historical_rates genel hatası: {e}")
            return None