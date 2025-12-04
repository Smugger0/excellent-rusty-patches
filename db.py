# db.py
# -*- coding: utf-8 -*-
"""
Veritabanı Yönetim Modülü
6 Ayrı Veritabanı Yapısı - Database Dizininde
"""

from imports import *


class Database:
    """6 Ayrı Veritabanı ile Çalışan Sınıf - Database Dizininde."""
    def __init__(self):
        # Database dizinini oluştur
        self.db_dir = os.path.join(os.getcwd(), 'Database')
        os.makedirs(self.db_dir, exist_ok=True)
        
        # 6 ayrı veritabanı bağlantısı
        self.gelir_conn = sqlite3.connect(os.path.join(self.db_dir, 'gelir.db'), check_same_thread=False)
        self.gider_conn = sqlite3.connect(os.path.join(self.db_dir, 'gider.db'), check_same_thread=False)
        self.genel_gider_conn = sqlite3.connect(os.path.join(self.db_dir, 'genel_gider.db'), check_same_thread=False)
        self.settings_conn = sqlite3.connect(os.path.join(self.db_dir, 'settings.db'), check_same_thread=False)
        self.exchange_rates_conn = sqlite3.connect(os.path.join(self.db_dir, 'exchange_rates.db'), check_same_thread=False)
        self.history_conn = sqlite3.connect(os.path.join(self.db_dir, 'history.db'), check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Her veritabanında gerekli tabloları oluşturur."""
        try:
            # GELİR VERİTABANI
            gelir_cursor = self.gelir_conn.cursor()
            gelir_cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fatura_no TEXT,
                    irsaliye_no TEXT,
                    tarih TEXT,
                    firma TEXT,
                    malzeme TEXT,
                    miktar TEXT,
                    toplam_tutar_tl REAL,
                    toplam_tutar_usd REAL,
                    toplam_tutar_eur REAL,
                    birim TEXT,
                    kdv_yuzdesi REAL,
                    kdv_tutari REAL,
                    kdv_dahil INTEGER DEFAULT 0,
                    usd_rate REAL,
                    eur_rate REAL
                )
            """)
            
            # Add fatura_no column if it doesn't exist (for existing databases)
            try:
                gelir_cursor.execute("ALTER TABLE invoices ADD COLUMN fatura_no TEXT")
                logging.info("Added fatura_no column to gelir invoices table")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add kur columns if they don't exist
            try:
                gelir_cursor.execute("ALTER TABLE invoices ADD COLUMN usd_rate REAL")
                gelir_cursor.execute("ALTER TABLE invoices ADD COLUMN eur_rate REAL")
                logging.info("Added exchange rate columns to gelir invoices table")
            except sqlite3.OperationalError:
                pass  # Columns already exist
            
            # Add updated_at column if it doesn't exist
            try:
                gelir_cursor.execute("ALTER TABLE invoices ADD COLUMN updated_at TEXT")
                logging.info("Added updated_at column to gelir invoices table")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add created_at column if it doesn't exist
            try:
                gelir_cursor.execute("ALTER TABLE invoices ADD COLUMN created_at TEXT")
                logging.info("Added created_at column to gelir invoices table")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # GİDER VERİTABANI
            gider_cursor = self.gider_conn.cursor()
            gider_cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fatura_no TEXT,
                    irsaliye_no TEXT,
                    tarih TEXT,
                    firma TEXT,
                    malzeme TEXT,
                    miktar TEXT,
                    toplam_tutar_tl REAL,
                    toplam_tutar_usd REAL,
                    toplam_tutar_eur REAL,
                    birim TEXT,
                    kdv_yuzdesi REAL,
                    kdv_tutari REAL,
                    kdv_dahil INTEGER DEFAULT 0,
                    usd_rate REAL,
                    eur_rate REAL
                )
            """)
            
            # Add fatura_no column if it doesn't exist (for existing databases)
            try:
                gider_cursor.execute("ALTER TABLE invoices ADD COLUMN fatura_no TEXT")
                logging.info("Added fatura_no column to gider invoices table")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add kur columns if they don't exist
            try:
                gider_cursor.execute("ALTER TABLE invoices ADD COLUMN usd_rate REAL")
                gider_cursor.execute("ALTER TABLE invoices ADD COLUMN eur_rate REAL")
                logging.info("Added exchange rate columns to gider invoices table")
            except sqlite3.OperationalError:
                pass  # Columns already exist
            
            # Add updated_at column if it doesn't exist
            try:
                gider_cursor.execute("ALTER TABLE invoices ADD COLUMN updated_at TEXT")
                logging.info("Added updated_at column to gider invoices table")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add created_at column if it doesn't exist
            try:
                gider_cursor.execute("ALTER TABLE invoices ADD COLUMN created_at TEXT")
                logging.info("Added created_at column to gider invoices table")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # GENEL GİDERLER VERİTABANI
            genel_gider_cursor = self.genel_gider_conn.cursor()
            genel_gider_cursor.execute("""
                CREATE TABLE IF NOT EXISTS general_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    yil INTEGER,
                    ocak REAL DEFAULT 0,
                    subat REAL DEFAULT 0,
                    mart REAL DEFAULT 0,
                    nisan REAL DEFAULT 0,
                    mayis REAL DEFAULT 0,
                    haziran REAL DEFAULT 0,
                    temmuz REAL DEFAULT 0,
                    agustos REAL DEFAULT 0,
                    eylul REAL DEFAULT 0,
                    ekim REAL DEFAULT 0,
                    kasim REAL DEFAULT 0,
                    aralik REAL DEFAULT 0
                )
            """)
            
            # KURUMLAR VERGİSİ VERİTABANI - Aylık kurumlar vergisi tutarları
            genel_gider_cursor.execute("""
                CREATE TABLE IF NOT EXISTS corporate_tax (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    yil INTEGER,
                    ocak REAL DEFAULT 0,
                    subat REAL DEFAULT 0,
                    mart REAL DEFAULT 0,
                    nisan REAL DEFAULT 0,
                    mayis REAL DEFAULT 0,
                    haziran REAL DEFAULT 0,
                    temmuz REAL DEFAULT 0,
                    agustos REAL DEFAULT 0,
                    eylul REAL DEFAULT 0,
                    ekim REAL DEFAULT 0,
                    kasim REAL DEFAULT 0,
                    aralik REAL DEFAULT 0
                )
            """)
            
            # SETTINGS VERİTABANI
            settings_cursor = self.settings_conn.cursor()
            settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # EXCHANGE RATES VERİTABANI
            exchange_rates_cursor = self.exchange_rates_conn.cursor()
            exchange_rates_cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    currency TEXT PRIMARY KEY,
                    rate REAL,
                    updated_at TEXT
                )
            """)
            
            # HISTORY VERİTABANI
            history_cursor = self.history_conn.cursor()
            history_cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoice_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    invoice_type TEXT NOT NULL,
                    invoice_date TEXT,
                    firma TEXT,
                    amount REAL,
                    operation_date TEXT,
                    operation_time TEXT,
                    details TEXT
                )
            """)
            
            # Değişiklikleri kaydet
            self.gelir_conn.commit()
            self.gider_conn.commit()
            self.genel_gider_conn.commit()
            self.settings_conn.commit()
            self.exchange_rates_conn.commit()
            self.history_conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Tablo oluşturma hatası: {e}")

    def _get_connection(self, db_type):
        """Veritabanı tipine göre bağlantı döndürür."""
        if db_type == 'gelir':
            return self.gelir_conn
        elif db_type == 'gider':
            return self.gider_conn
        elif db_type == 'genel_gider':
            return self.genel_gider_conn
        elif db_type == 'settings':
            return self.settings_conn
        elif db_type == 'exchange_rates':
            return self.exchange_rates_conn
        elif db_type == 'history':
            return self.history_conn
        else:
            logging.error(f"Geçersiz veritabanı tipi: {db_type}")
            return None

    def _execute_query(self, db_type, query, params=()):
        """Belirtilen veritabanında sorgu çalıştırmak için yardımcı metod."""
        try:
            conn = self._get_connection(db_type)
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logging.error(f"Sorgu hatası ({db_type}): {e} - Sorgu: {query} - Parametreler: {params}")
            return None

    # GELİR İŞLEMLERİ
    def add_gelir_invoice(self, data):
        """Gelir veritabanına fatura ekler."""
        query = """
            INSERT INTO invoices (fatura_no, tarih, firma, malzeme, miktar, toplam_tutar_tl, toplam_tutar_usd, toplam_tutar_eur, birim, kdv_yuzdesi, kdv_tutari, kdv_dahil, usd_rate, eur_rate, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('fatura_no'), data.get('tarih'), data.get('firma'),
            data.get('malzeme'), data.get('miktar'), data.get('toplam_tutar_tl'),
            data.get('toplam_tutar_usd'), data.get('toplam_tutar_eur'), data.get('birim'),
            data.get('kdv_yuzdesi', 0), data.get('kdv_tutari', 0), data.get('kdv_dahil', 0),
            data.get('usd_rate'), data.get('eur_rate'), datetime.now().isoformat()
        )
        cursor = self._execute_query('gelir', query, params)
        return cursor.lastrowid if cursor else None

    def update_gelir_invoice(self, invoice_id, data):
        """Gelir veritabanındaki faturayı günceller."""
        query = """
            UPDATE invoices SET
            tarih = ?, firma = ?, malzeme = ?, miktar = ?, 
            toplam_tutar_tl = ?, toplam_tutar_usd = ?, toplam_tutar_eur = ?, birim = ?, kdv_yuzdesi = ?, kdv_tutari = ?, kdv_dahil = ?, usd_rate = ?, eur_rate = ?, updated_at = ?
            WHERE id = ?
        """
        params = (
            data.get('tarih'), data.get('firma'), 
            data.get('malzeme'), data.get('miktar'), data.get('toplam_tutar_tl'),
            data.get('toplam_tutar_usd'), data.get('toplam_tutar_eur'), data.get('birim'),
            data.get('kdv_yuzdesi', 0), data.get('kdv_tutari', 0), data.get('kdv_dahil', 0),
            data.get('usd_rate'), data.get('eur_rate'), datetime.now().isoformat(), invoice_id
        )
        cursor = self._execute_query('gelir', query, params)
        return cursor is not None

    def delete_gelir_invoice(self, invoice_id):
        """Gelir veritabanından fatura siler."""
        query = "DELETE FROM invoices WHERE id = ?"
        cursor = self._execute_query('gelir', query, (invoice_id,))
        return cursor.rowcount if cursor else 0

    def delete_multiple_gelir_invoices(self, invoice_ids):
        """Gelir veritabanından çoklu fatura siler."""
        if not invoice_ids:
            return 0
        
        placeholders = ','.join(['?' for _ in invoice_ids])
        query = f"DELETE FROM invoices WHERE id IN ({placeholders})"
        cursor = self._execute_query('gelir', query, invoice_ids)
        return cursor.rowcount if cursor else 0

    def get_all_gelir_invoices(self, limit=None, offset=0, order_by=None):
        """Gelir veritabanındaki tüm faturaları getirir."""
        if not order_by:
            order_by = "substr(tarih, 7, 4) || substr(tarih, 4, 2) || substr(tarih, 1, 2) DESC"
        
        # Limit ve offset güvenli değerler kullan
        if limit is not None:
            query = f"SELECT * FROM invoices ORDER BY {order_by} LIMIT {int(limit)} OFFSET {int(offset or 0)}"
        else:
            query = f"SELECT * FROM invoices ORDER BY {order_by}"
        
        cursor = self._execute_query('gelir', query)
        if cursor:
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_gelir_invoice_count(self):
        """Gelir tablosundaki toplam fatura sayısını döndürür."""
        query = "SELECT COUNT(*) FROM invoices"
        cursor = self._execute_query('gelir', query)
        if cursor:
            return cursor.fetchone()[0]
        return 0

    def get_gelir_invoice_by_id(self, invoice_id):
        """Gelir veritabanından ID'ye göre tek bir fatura getirir."""
        query = "SELECT * FROM invoices WHERE id = ?"
        cursor = self._execute_query('gelir', query, (invoice_id,))
        if cursor:
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None

    # GİDER İŞLEMLERİ
    def add_gider_invoice(self, data):
        """Gider veritabanına fatura ekler."""
        query = """
            INSERT INTO invoices (fatura_no, tarih, firma, malzeme, miktar, toplam_tutar_tl, toplam_tutar_usd, toplam_tutar_eur, birim, kdv_yuzdesi, kdv_tutari, kdv_dahil, usd_rate, eur_rate, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('fatura_no'), data.get('tarih'), data.get('firma'),
            data.get('malzeme'), data.get('miktar'), data.get('toplam_tutar_tl'),
            data.get('toplam_tutar_usd'), data.get('toplam_tutar_eur'), data.get('birim'),
            data.get('kdv_yuzdesi', 0), data.get('kdv_tutari', 0), data.get('kdv_dahil', 0),
            data.get('usd_rate'), data.get('eur_rate'), datetime.now().isoformat()
        )
        cursor = self._execute_query('gider', query, params)
        return cursor.lastrowid if cursor else None

    def update_gider_invoice(self, invoice_id, data):
        """Gider veritabanındaki faturayı günceller."""
        query = """
            UPDATE invoices SET
            fatura_no = ?, tarih = ?, firma = ?, malzeme = ?, miktar = ?, 
            toplam_tutar_tl = ?, toplam_tutar_usd = ?, toplam_tutar_eur = ?, birim = ?, kdv_yuzdesi = ?, kdv_tutari = ?, kdv_dahil = ?, usd_rate = ?, eur_rate = ?, updated_at = ?
            WHERE id = ?
        """
        params = (
            data.get('fatura_no'), data.get('tarih'), data.get('firma'), 
            data.get('malzeme'), data.get('miktar'), data.get('toplam_tutar_tl'),
            data.get('toplam_tutar_usd'), data.get('toplam_tutar_eur'), data.get('birim'),
            data.get('kdv_yuzdesi', 0), data.get('kdv_tutari', 0), data.get('kdv_dahil', 0),
            data.get('usd_rate'), data.get('eur_rate'), datetime.now().isoformat(), invoice_id
        )
        cursor = self._execute_query('gider', query, params)
        return cursor is not None

    def delete_gider_invoice(self, invoice_id):
        """Gider veritabanından fatura siler."""
        query = "DELETE FROM invoices WHERE id = ?"
        cursor = self._execute_query('gider', query, (invoice_id,))
        return cursor.rowcount if cursor else 0

    def delete_multiple_gider_invoices(self, invoice_ids):
        """Gider veritabanından çoklu fatura siler."""
        if not invoice_ids:
            return 0
        
        placeholders = ','.join(['?' for _ in invoice_ids])
        query = f"DELETE FROM invoices WHERE id IN ({placeholders})"
        cursor = self._execute_query('gider', query, invoice_ids)
        return cursor.rowcount if cursor else 0

    def get_all_gider_invoices(self, limit=None, offset=0, order_by=None):
        """Gider veritabanındaki tüm faturaları getirir."""
        if not order_by:
            order_by = "substr(tarih, 7, 4) || substr(tarih, 4, 2) || substr(tarih, 1, 2) DESC"
        
        # Limit ve offset güvenli değerler kullan
        if limit is not None:
            query = f"SELECT * FROM invoices ORDER BY {order_by} LIMIT {int(limit)} OFFSET {int(offset or 0)}"
        else:
            query = f"SELECT * FROM invoices ORDER BY {order_by}"
        
        cursor = self._execute_query('gider', query)
        if cursor:
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_gider_invoice_count(self):
        """Gider tablosundaki toplam fatura sayısını döndürür."""
        query = "SELECT COUNT(*) FROM invoices"
        cursor = self._execute_query('gider', query)
        if cursor:
            return cursor.fetchone()[0]
        return 0

    def get_gider_invoice_by_id(self, invoice_id):
        """Gider veritabanından ID'ye göre tek bir fatura getirir."""
        query = "SELECT * FROM invoices WHERE id = ?"
        cursor = self._execute_query('gider', query, (invoice_id,))
        if cursor:
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None

    # GENEL GİDER İŞLEMLERİ - AYLIK FORMAT
    def add_or_update_yearly_expenses(self, year, monthly_data):
        """Belirli bir yıl için aylık genel giderleri ekle veya güncelle.
        Args:
            year (int): Yıl
            monthly_data (dict): Ay adları ve tutarlar {'ocak': 1500, 'subat': 800, ...}
        """
        # Önce yılın kayıtlı olup olmadığını kontrol et
        check_query = "SELECT id FROM general_expenses WHERE yil = ?"
        cursor = self._execute_query('genel_gider', check_query, (year,))
        
        if cursor and cursor.fetchone():
            # Güncelle
            set_clauses = []
            params = []
            for month, amount in monthly_data.items():
                if month in ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran',
                           'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']:
                    set_clauses.append(f"{month} = ?")
                    params.append(float(amount or 0))
            
            if set_clauses:
                params.append(year)
                query = f"UPDATE general_expenses SET {', '.join(set_clauses)} WHERE yil = ?"
                self._execute_query('genel_gider', query, tuple(params))
                return True
        else:
            # Ekle
            columns = ['yil']
            values = [year]
            for month in ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran',
                         'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']:
                columns.append(month)
                values.append(float(monthly_data.get(month, 0) or 0))
            
            placeholders = ', '.join(['?'] * len(columns))
            query = f"INSERT INTO general_expenses ({', '.join(columns)}) VALUES ({placeholders})"
            cursor = self._execute_query('genel_gider', query, tuple(values))
            return cursor.lastrowid if cursor else None
        
        return False
    
    def get_yearly_expenses(self, year):
        """Belirli bir yılın aylık genel giderlerini getir."""
        query = "SELECT * FROM general_expenses WHERE yil = ?"
        cursor = self._execute_query('genel_gider', query, (year,))
        if cursor:
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None
    
    def get_all_yearly_expenses(self):
        """Tüm yılların genel giderlerini getir."""
        query = "SELECT * FROM general_expenses ORDER BY yil DESC"
        cursor = self._execute_query('genel_gider', query)
        if cursor:
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    # KURUMLAR VERGİSİ FONKSİYONLARI
    def add_or_update_corporate_tax(self, year, monthly_data):
        """Belirli bir yıl için aylık kurumlar vergisi tutarlarını ekle veya güncelle."""
        # Önce kayıt var mı kontrol et
        check_query = "SELECT id FROM corporate_tax WHERE yil = ?"
        cursor = self._execute_query('genel_gider', check_query, (year,))
        
        if cursor and cursor.fetchone():
            # Güncelleme
            month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 
                         'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
            set_clauses = []
            values = []
            
            for month in month_keys:
                if month in monthly_data:
                    set_clauses.append(f"{month} = ?")
                    values.append(float(monthly_data.get(month, 0) or 0))
            
            if set_clauses:
                query = f"UPDATE corporate_tax SET {', '.join(set_clauses)} WHERE yil = ?"
                values.append(year)
                cursor = self._execute_query('genel_gider', query, tuple(values))
                return cursor is not None
        else:
            # Ekleme
            month_keys = ['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran', 
                         'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik']
            columns = ['yil']
            values = [year]
            
            for month in month_keys:
                columns.append(month)
                values.append(float(monthly_data.get(month, 0) or 0))
            
            placeholders = ', '.join(['?'] * len(columns))
            query = f"INSERT INTO corporate_tax ({', '.join(columns)}) VALUES ({placeholders})"
            cursor = self._execute_query('genel_gider', query, tuple(values))
            return cursor.lastrowid if cursor else None
        
        return False
    
    def get_corporate_tax(self, year):
        """Belirli bir yılın aylık kurumlar vergisi tutarlarını getir."""
        query = "SELECT * FROM corporate_tax WHERE yil = ?"
        cursor = self._execute_query('genel_gider', query, (year,))
        if cursor:
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None

    # KURUMLAR VERGİSİ FONKSİYONLARI
    
    def get_all_genel_gider(self, limit=None, offset=0, order_by=None):
        """Eski format tüm genel giderleri getir - yeni formata çevrilmiş veri döndür."""
        # Yeni sistemden veri çek ve eski formata dönüştür (export için)
        yearly_data = self.get_all_yearly_expenses()
        result = []
        
        for year_record in yearly_data:
            year = year_record.get('yil')
            for month_num, month_name in enumerate(['ocak', 'subat', 'mart', 'nisan', 'mayis', 'haziran',
                                                     'temmuz', 'agustos', 'eylul', 'ekim', 'kasim', 'aralik'], 1):
                amount = year_record.get(month_name, 0)
                if amount and amount > 0:
                    result.append({
                        'id': f"{year}_{month_num}",
                        'tarih': f"01.{month_num:02d}.{year}",
                        'tur': 'Genel Gider',
                        'miktar': amount,
                        'aciklama': f'{month_name.capitalize()} {year}'
                    })
        
        return result
    
    def get_genel_gider_count(self):
        """Genel gider tablosundaki toplam kayıt sayısını döndürür."""
        query = "SELECT COUNT(*) FROM general_expenses"
        cursor = self._execute_query('genel_gider', query)
        if cursor:
            return cursor.fetchone()[0]
        return 0

    def get_genel_gider_by_id(self, gider_id):
        """Genel gider veritabanından ID'ye göre tek bir kayıt getirir."""
        query = "SELECT * FROM general_expenses WHERE id = ?"
        cursor = self._execute_query('genel_gider', query, (gider_id,))
        if cursor:
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None

    # --- Ayarlar ve Kur Yönetimi (Ayrı veritabanları) ---
    def get_setting(self, key):
        query = "SELECT value FROM settings WHERE key = ?"
        cursor = self._execute_query('settings', query, (key,))
        if cursor:
            result = cursor.fetchone()
            return result[0] if result else None
        return None

    def save_setting(self, key, value):
        query = "REPLACE INTO settings (key, value) VALUES (?, ?)"
        self._execute_query('settings', query, (key, str(value)))
        return True

    def get_all_settings(self):
        query = "SELECT key, value FROM settings"
        cursor = self._execute_query('settings', query)
        return dict(cursor.fetchall()) if cursor else {}

    def save_exchange_rates(self, rates):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for currency, rate in rates.items():
            query = "REPLACE INTO exchange_rates (currency, rate, updated_at) VALUES (?, ?, ?)"
            self._execute_query('exchange_rates', query, (currency, rate, current_time))
        return True

    def load_exchange_rates(self):
        query = "SELECT currency, rate FROM exchange_rates"
        cursor = self._execute_query('exchange_rates', query)
        return dict(cursor.fetchall()) if cursor else {}

    # --- İşlem Geçmişi Yönetimi ---
    def add_history_record(self, operation_type, invoice_type, invoice_date=None, firma=None, amount=None, details=None):
        """İşlem geçmişi kaydı ekler."""
        current_time = datetime.now()
        operation_date = current_time.strftime("%d.%m.%Y")
        operation_time = current_time.strftime("%H:%M:%S")
        
        query = """
            INSERT INTO invoice_history (operation_type, invoice_type, invoice_date, firma, amount, operation_date, operation_time, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (operation_type, invoice_type, invoice_date, firma, amount, operation_date, operation_time, details)
        cursor = self._execute_query('history', query, params)
        return cursor.lastrowid if cursor else None

    def get_recent_history(self, limit=20):
        """Son işlem geçmişini getirir."""
        query = """
            SELECT * FROM invoice_history 
            ORDER BY id DESC 
            LIMIT ?
        """
        cursor = self._execute_query('history', query, (limit,))
        if cursor:
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []

    def get_history_by_date_range(self, start_date, end_date, limit=100):
        """Tarih aralığına göre işlem geçmişini getirir."""
        query = """
            SELECT * FROM invoice_history 
            WHERE operation_date BETWEEN ? AND ?
            ORDER BY id DESC 
            LIMIT ?
        """
        cursor = self._execute_query('history', query, (start_date, end_date, limit))
        if cursor:
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []

    def clear_old_history(self, days_to_keep=90):
        """Eski geçmiş kayıtlarını temizler (varsayılan 90 gün)."""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%d.%m.%Y")
        query = "DELETE FROM invoice_history WHERE operation_date < ?"
        cursor = self._execute_query('history', query, (cutoff_date,))
        return cursor.rowcount if cursor else 0
