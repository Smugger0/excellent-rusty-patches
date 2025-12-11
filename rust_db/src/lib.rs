use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::exceptions::PyRuntimeError;
use sqlx::sqlite::{SqlitePool, SqlitePoolOptions, SqliteConnectOptions};
use sqlx::Row;
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::runtime::Runtime;
use chrono::{Utc, NaiveDate};
use std::str::FromStr;
use std::fs;
use std::path::Path;

// ============================================================================
// YARDIMCI FONKSİYONLAR
// ============================================================================

// Tarih dönüşümü için yardımcı fonksiyonlar
fn to_iso_date(date: &str) -> String {
    if let Ok(d) = NaiveDate::parse_from_str(date, "%d.%m.%Y") {
        d.format("%Y-%m-%d").to_string()
    } else {
        date.to_string()
    }
}

fn to_display_date(date: &str) -> String {
    if let Ok(d) = NaiveDate::parse_from_str(date, "%Y-%m-%d") {
        d.format("%d.%m.%Y").to_string()
    } else {
        date.to_string()
    }
}

// ============================================================================
// VERİTABANI SINIFI
// ============================================================================
#[pyclass]
struct Database {
    invoices_pool: Arc<RwLock<Option<SqlitePool>>>,
    settings_pool: Arc<RwLock<Option<SqlitePool>>>,
    history_pool: Arc<RwLock<Option<SqlitePool>>>,
    runtime: Runtime,
}

#[pymethods]
impl Database {
    #[new]
    fn new() -> Self {
        Database {
            invoices_pool: Arc::new(RwLock::new(None)),
            settings_pool: Arc::new(RwLock::new(None)),
            history_pool: Arc::new(RwLock::new(None)),
            runtime: Runtime::new().unwrap(),
        }
    }

    // ------------------------------------------------------------------------
    // BAĞLANTI VE TABLO OLUŞTURMA
    // ------------------------------------------------------------------------

    fn init_connections(&self) -> PyResult<()> {
        // Database klasörünün var olduğundan emin ol
        if !Path::new("Database").exists() {
            fs::create_dir("Database").map_err(|e| PyRuntimeError::new_err(format!("Failed to create Database directory: {}", e)))?;
        }

        let invoices_pool = self.invoices_pool.clone();
        let settings_pool = self.settings_pool.clone();
        let history_pool = self.history_pool.clone();

        self.runtime.block_on(async move {
            // Faturalar Veritabanı (Faturalar ve Genel Giderler)
            let opts = SqliteConnectOptions::from_str("sqlite:Database/invoices.db?mode=rwc")
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to parse connection string: {}", e)))?
                .journal_mode(sqlx::sqlite::SqliteJournalMode::Wal);
            
            let pool = SqlitePoolOptions::new()
                .max_connections(5)
                .connect_with(opts).await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to connect to invoices.db: {}", e)))?;
            *invoices_pool.write().await = Some(pool);

            // Ayarlar Veritabanı (Ayarlar ve Döviz Kurları)
            let opts = SqliteConnectOptions::from_str("sqlite:Database/settings.db?mode=rwc")
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to parse connection string: {}", e)))?
                .journal_mode(sqlx::sqlite::SqliteJournalMode::Wal);

            let pool = SqlitePoolOptions::new()
                .max_connections(5)
                .connect_with(opts).await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to connect to settings.db: {}", e)))?;
            *settings_pool.write().await = Some(pool);

            // Geçmiş Veritabanı (İşlem Geçmişi)
            let opts = SqliteConnectOptions::from_str("sqlite:Database/history.db?mode=rwc")
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to parse connection string: {}", e)))?
                .journal_mode(sqlx::sqlite::SqliteJournalMode::Wal);

            let pool = SqlitePoolOptions::new()
                .max_connections(5)
                .connect_with(opts).await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to connect to history.db: {}", e)))?;
            *history_pool.write().await = Some(pool);

            Ok(())
        })
    }

    fn create_tables(&self) -> PyResult<()> {
        let invoices_pool = self.invoices_pool.clone();
        let settings_pool = self.settings_pool.clone();
        let history_pool = self.history_pool.clone();

        self.runtime.block_on(async move {
            // FATURA VERİTABANI TABLOLARI
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                // Gelir Faturaları
                sqlx::query(
                    r#"
                    CREATE TABLE IF NOT EXISTS income_invoices (
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
                        eur_rate REAL,
                        updated_at TEXT,
                        created_at TEXT
                    )
                    "#
                )
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create income_invoices table: {}", e)))?;

                // Gider Faturaları
                sqlx::query(
                    r#"
                    CREATE TABLE IF NOT EXISTS expense_invoices (
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
                        eur_rate REAL,
                        updated_at TEXT,
                        created_at TEXT
                    )
                    "#
                )
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create expense_invoices table: {}", e)))?;

                // Genel Giderler
                sqlx::query(
                    r#"
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
                    "#
                )
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create general_expenses: {}", e)))?;

                // Kurumlar Vergisi
                sqlx::query(
                    r#"
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
                    "#
                )
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create corporate_tax: {}", e)))?;
            }

            // AYARLAR VERİTABANI TABLOLARI
            if let Some(pool) = settings_pool.read().await.as_ref() {
                sqlx::query(
                    r#"
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                    "#
                )
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create settings: {}", e)))?;

                sqlx::query(
                    r#"
                    CREATE TABLE IF NOT EXISTS exchange_rates (
                        date TEXT PRIMARY KEY,
                        usd_rate REAL,
                        eur_rate REAL
                    )
                    "#
                )
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create exchange_rates: {}", e)))?;
            }

            // GEÇMİŞ VERİTABANI TABLOLARI
            if let Some(pool) = history_pool.read().await.as_ref() {
                sqlx::query(
                    r#"
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action TEXT NOT NULL,
                        details TEXT,
                        timestamp TEXT
                    )
                    "#
                )
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create history: {}", e)))?;
            }

            Ok(())
        })
    }

    // ============================================================================
    // GELİR FATURASI METOTLARI
    // ============================================================================
    
    fn add_gelir_invoice(&self, data: &Bound<'_, PyDict>) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        // Python sözlüğünden değerleri al
        let fatura_no: Option<String> = data.get_item("fatura_no")?.and_then(|v| v.extract().ok());
        let tarih_raw: Option<String> = data.get_item("tarih")?.and_then(|v| v.extract().ok());
        let tarih = tarih_raw.map(|t| to_iso_date(&t)); // ISO formatına çevir
        
        let firma: Option<String> = data.get_item("firma")?.and_then(|v| v.extract().ok());
        let malzeme: Option<String> = data.get_item("malzeme")?.and_then(|v| v.extract().ok());
        let miktar: Option<String> = data.get_item("miktar")?.and_then(|v| v.extract().ok());
        let toplam_tutar_tl: Option<f64> = data.get_item("toplam_tutar_tl")?.and_then(|v| v.extract().ok());
        let toplam_tutar_usd: Option<f64> = data.get_item("toplam_tutar_usd")?.and_then(|v| v.extract().ok());
        let toplam_tutar_eur: Option<f64> = data.get_item("toplam_tutar_eur")?.and_then(|v| v.extract().ok());
        let birim: Option<String> = data.get_item("birim")?.and_then(|v| v.extract().ok());
        let kdv_yuzdesi: f64 = data.get_item("kdv_yuzdesi")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_tutari: f64 = data.get_item("kdv_tutari")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_dahil: i64 = data.get_item("kdv_dahil")?.and_then(|v| v.extract().ok()).unwrap_or(0);
        let usd_rate: Option<f64> = data.get_item("usd_rate")?.and_then(|v| v.extract().ok());
        let eur_rate: Option<f64> = data.get_item("eur_rate")?.and_then(|v| v.extract().ok());

        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let created_at = Utc::now().to_rfc3339();
                
                let result = sqlx::query(
                    r#"
                    INSERT INTO income_invoices (fatura_no, tarih, firma, malzeme, miktar, toplam_tutar_tl, 
                                        toplam_tutar_usd, toplam_tutar_eur, birim, kdv_yuzdesi, kdv_tutari, 
                                        kdv_dahil, usd_rate, eur_rate, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    "#
                )
                .bind(fatura_no)
                .bind(tarih)
                .bind(firma)
                .bind(malzeme)
                .bind(miktar)
                .bind(toplam_tutar_tl)
                .bind(toplam_tutar_usd)
                .bind(toplam_tutar_eur)
                .bind(birim)
                .bind(kdv_yuzdesi)
                .bind(kdv_tutari)
                .bind(kdv_dahil)
                .bind(usd_rate)
                .bind(eur_rate)
                .bind(created_at)
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to insert gelir invoice: {}", e)))?;

                Ok(result.last_insert_rowid())
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn update_gelir_invoice(&self, invoice_id: i64, data: &Bound<'_, PyDict>) -> PyResult<bool> {
        let invoices_pool = self.invoices_pool.clone();
        
        let tarih_raw: Option<String> = data.get_item("tarih")?.and_then(|v| v.extract().ok());
        let tarih = tarih_raw.map(|t| to_iso_date(&t)); // ISO formatına çevir

        let firma: Option<String> = data.get_item("firma")?.and_then(|v| v.extract().ok());
        let malzeme: Option<String> = data.get_item("malzeme")?.and_then(|v| v.extract().ok());
        let miktar: Option<String> = data.get_item("miktar")?.and_then(|v| v.extract().ok());
        let toplam_tutar_tl: Option<f64> = data.get_item("toplam_tutar_tl")?.and_then(|v| v.extract().ok());
        let toplam_tutar_usd: Option<f64> = data.get_item("toplam_tutar_usd")?.and_then(|v| v.extract().ok());
        let toplam_tutar_eur: Option<f64> = data.get_item("toplam_tutar_eur")?.and_then(|v| v.extract().ok());
        let birim: Option<String> = data.get_item("birim")?.and_then(|v| v.extract().ok());
        let kdv_yuzdesi: f64 = data.get_item("kdv_yuzdesi")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_tutari: f64 = data.get_item("kdv_tutari")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_dahil: i64 = data.get_item("kdv_dahil")?.and_then(|v| v.extract().ok()).unwrap_or(0);
        let usd_rate: Option<f64> = data.get_item("usd_rate")?.and_then(|v| v.extract().ok());
        let eur_rate: Option<f64> = data.get_item("eur_rate")?.and_then(|v| v.extract().ok());

        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let updated_at = Utc::now().to_rfc3339();
                
                let result = sqlx::query(
                    r#"
                    UPDATE income_invoices SET
                    tarih = ?, firma = ?, malzeme = ?, miktar = ?, 
                    toplam_tutar_tl = ?, toplam_tutar_usd = ?, toplam_tutar_eur = ?, birim = ?, 
                    kdv_yuzdesi = ?, kdv_tutari = ?, kdv_dahil = ?, usd_rate = ?, eur_rate = ?, updated_at = ?
                    WHERE id = ?
                    "#
                )
                .bind(tarih)
                .bind(firma)
                .bind(malzeme)
                .bind(miktar)
                .bind(toplam_tutar_tl)
                .bind(toplam_tutar_usd)
                .bind(toplam_tutar_eur)
                .bind(birim)
                .bind(kdv_yuzdesi)
                .bind(kdv_tutari)
                .bind(kdv_dahil)
                .bind(usd_rate)
                .bind(eur_rate)
                .bind(updated_at)
                .bind(invoice_id)
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to update gelir invoice: {}", e)))?;

                Ok(result.rows_affected() > 0)
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn delete_gelir_invoice(&self, invoice_id: i64) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let result = sqlx::query("DELETE FROM income_invoices WHERE id = ?")
                    .bind(invoice_id)
                    .execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to delete gelir invoice: {}", e)))?;

                Ok(result.rows_affected() as i64)
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn delete_multiple_gelir_invoices(&self, invoice_ids: Vec<i64>) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        self.runtime.block_on(async move {
            if invoice_ids.is_empty() {
                return Ok(0);
            }

            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let placeholders = vec!["?"; invoice_ids.len()].join(",");
                let query = format!("DELETE FROM income_invoices WHERE id IN ({})", placeholders);
                
                let mut q = sqlx::query(&query);
                for id in invoice_ids {
                    q = q.bind(id);
                }
                
                let result = q.execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to delete multiple gelir invoices: {}", e)))?;

                Ok(result.rows_affected() as i64)
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_all_gelir_invoices(&self, py: Python<'_>, limit: Option<i64>, offset: Option<i64>, order_by: Option<String>) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let rows = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let order_clause = order_by.unwrap_or_else(|| "tarih DESC".to_string());
                let query = if let Some(lim) = limit {
                    format!(
                        "SELECT * FROM income_invoices ORDER BY {} LIMIT {} OFFSET {}",
                        order_clause, lim, offset.unwrap_or(0)
                    )
                } else {
                    format!("SELECT * FROM income_invoices ORDER BY {}", order_clause)
                };

                sqlx::query(&query)
                    .fetch_all(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to fetch gelir invoices: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        let result = PyList::empty_bound(py);
        for row in rows {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", row.get::<i64, _>("id"))?;
            dict.set_item("fatura_no", row.try_get::<String, _>("fatura_no").ok())?;
            
            // ISO tarihini görüntüleme formatına geri çevir
            let tarih_iso = row.try_get::<String, _>("tarih").ok();
            let tarih_display = tarih_iso.as_ref().map(|t| to_display_date(t));
            dict.set_item("tarih", tarih_display)?;

            dict.set_item("firma", row.try_get::<String, _>("firma").ok())?;
            dict.set_item("malzeme", row.try_get::<String, _>("malzeme").ok())?;
            dict.set_item("miktar", row.try_get::<String, _>("miktar").ok())?;
            dict.set_item("toplam_tutar_tl", row.try_get::<f64, _>("toplam_tutar_tl").ok())?;
            dict.set_item("toplam_tutar_usd", row.try_get::<f64, _>("toplam_tutar_usd").ok())?;
            dict.set_item("toplam_tutar_eur", row.try_get::<f64, _>("toplam_tutar_eur").ok())?;
            dict.set_item("birim", row.try_get::<String, _>("birim").ok())?;
            dict.set_item("kdv_yuzdesi", row.try_get::<f64, _>("kdv_yuzdesi").ok())?;
            dict.set_item("kdv_tutari", row.try_get::<f64, _>("kdv_tutari").ok())?;
            dict.set_item("kdv_dahil", row.try_get::<i64, _>("kdv_dahil").ok())?;
            dict.set_item("usd_rate", row.try_get::<f64, _>("usd_rate").ok())?;
            dict.set_item("eur_rate", row.try_get::<f64, _>("eur_rate").ok())?;
            dict.set_item("updated_at", row.try_get::<String, _>("updated_at").ok())?;
            dict.set_item("created_at", row.try_get::<String, _>("created_at").ok())?;
            result.append(dict)?;
        }
        Ok(result.into())
    }

    fn get_gelir_invoice_count(&self) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let row = sqlx::query("SELECT COUNT(*) as count FROM income_invoices")
                    .fetch_one(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to count gelir invoices: {}", e)))?;

                Ok(row.get::<i64, _>("count"))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_gelir_invoice_by_id(&self, py: Python<'_>, invoice_id: i64) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let row = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                sqlx::query("SELECT * FROM income_invoices WHERE id = ?")
                    .bind(invoice_id)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to fetch gelir invoice: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        if let Some(r) = row {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", r.get::<i64, _>("id"))?;
            dict.set_item("fatura_no", r.try_get::<String, _>("fatura_no").ok())?;
            
            let tarih_iso = r.try_get::<String, _>("tarih").ok();
            let tarih_display = tarih_iso.as_ref().map(|t| to_display_date(t));
            dict.set_item("tarih", tarih_display)?;

            dict.set_item("firma", r.try_get::<String, _>("firma").ok())?;
            dict.set_item("malzeme", r.try_get::<String, _>("malzeme").ok())?;
            dict.set_item("miktar", r.try_get::<String, _>("miktar").ok())?;
            dict.set_item("toplam_tutar_tl", r.try_get::<f64, _>("toplam_tutar_tl").ok())?;
            dict.set_item("toplam_tutar_usd", r.try_get::<f64, _>("toplam_tutar_usd").ok())?;
            dict.set_item("toplam_tutar_eur", r.try_get::<f64, _>("toplam_tutar_eur").ok())?;
            dict.set_item("birim", r.try_get::<String, _>("birim").ok())?;
            dict.set_item("kdv_yuzdesi", r.try_get::<f64, _>("kdv_yuzdesi").ok())?;
            dict.set_item("kdv_tutari", r.try_get::<f64, _>("kdv_tutari").ok())?;
            dict.set_item("kdv_dahil", r.try_get::<i64, _>("kdv_dahil").ok())?;
            dict.set_item("usd_rate", r.try_get::<f64, _>("usd_rate").ok())?;
            dict.set_item("eur_rate", r.try_get::<f64, _>("eur_rate").ok())?;
            dict.set_item("updated_at", r.try_get::<String, _>("updated_at").ok())?;
            dict.set_item("created_at", r.try_get::<String, _>("created_at").ok())?;
            Ok(dict.into())
        } else {
            Ok(py.None())
        }
    }

    // ============================================================================
    // GİDER FATURASI METOTLARI
    // ============================================================================
    
    fn add_gider_invoice(&self, data: &Bound<'_, PyDict>) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        let fatura_no: Option<String> = data.get_item("fatura_no")?.and_then(|v| v.extract().ok());
        let tarih_raw: Option<String> = data.get_item("tarih")?.and_then(|v| v.extract().ok());
        let tarih = tarih_raw.map(|t| to_iso_date(&t));

        let firma: Option<String> = data.get_item("firma")?.and_then(|v| v.extract().ok());
        let malzeme: Option<String> = data.get_item("malzeme")?.and_then(|v| v.extract().ok());
        let miktar: Option<String> = data.get_item("miktar")?.and_then(|v| v.extract().ok());
        let toplam_tutar_tl: Option<f64> = data.get_item("toplam_tutar_tl")?.and_then(|v| v.extract().ok());
        let toplam_tutar_usd: Option<f64> = data.get_item("toplam_tutar_usd")?.and_then(|v| v.extract().ok());
        let toplam_tutar_eur: Option<f64> = data.get_item("toplam_tutar_eur")?.and_then(|v| v.extract().ok());
        let birim: Option<String> = data.get_item("birim")?.and_then(|v| v.extract().ok());
        let kdv_yuzdesi: f64 = data.get_item("kdv_yuzdesi")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_tutari: f64 = data.get_item("kdv_tutari")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_dahil: i64 = data.get_item("kdv_dahil")?.and_then(|v| v.extract().ok()).unwrap_or(0);
        let usd_rate: Option<f64> = data.get_item("usd_rate")?.and_then(|v| v.extract().ok());
        let eur_rate: Option<f64> = data.get_item("eur_rate")?.and_then(|v| v.extract().ok());

        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let created_at = Utc::now().to_rfc3339();
                
                let result = sqlx::query(
                    r#"
                    INSERT INTO expense_invoices (fatura_no, tarih, firma, malzeme, miktar, toplam_tutar_tl, 
                                        toplam_tutar_usd, toplam_tutar_eur, birim, kdv_yuzdesi, kdv_tutari, 
                                        kdv_dahil, usd_rate, eur_rate, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    "#
                )
                .bind(fatura_no)
                .bind(tarih)
                .bind(firma)
                .bind(malzeme)
                .bind(miktar)
                .bind(toplam_tutar_tl)
                .bind(toplam_tutar_usd)
                .bind(toplam_tutar_eur)
                .bind(birim)
                .bind(kdv_yuzdesi)
                .bind(kdv_tutari)
                .bind(kdv_dahil)
                .bind(usd_rate)
                .bind(eur_rate)
                .bind(created_at)
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to insert gider invoice: {}", e)))?;

                Ok(result.last_insert_rowid())
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn update_gider_invoice(&self, invoice_id: i64, data: &Bound<'_, PyDict>) -> PyResult<bool> {
        let invoices_pool = self.invoices_pool.clone();
        
        let fatura_no: Option<String> = data.get_item("fatura_no")?.and_then(|v| v.extract().ok());
        let tarih_raw: Option<String> = data.get_item("tarih")?.and_then(|v| v.extract().ok());
        let tarih = tarih_raw.map(|t| to_iso_date(&t));

        let firma: Option<String> = data.get_item("firma")?.and_then(|v| v.extract().ok());
        let malzeme: Option<String> = data.get_item("malzeme")?.and_then(|v| v.extract().ok());
        let miktar: Option<String> = data.get_item("miktar")?.and_then(|v| v.extract().ok());
        let toplam_tutar_tl: Option<f64> = data.get_item("toplam_tutar_tl")?.and_then(|v| v.extract().ok());
        let toplam_tutar_usd: Option<f64> = data.get_item("toplam_tutar_usd")?.and_then(|v| v.extract().ok());
        let toplam_tutar_eur: Option<f64> = data.get_item("toplam_tutar_eur")?.and_then(|v| v.extract().ok());
        let birim: Option<String> = data.get_item("birim")?.and_then(|v| v.extract().ok());
        let kdv_yuzdesi: f64 = data.get_item("kdv_yuzdesi")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_tutari: f64 = data.get_item("kdv_tutari")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let kdv_dahil: i64 = data.get_item("kdv_dahil")?.and_then(|v| v.extract().ok()).unwrap_or(0);
        let usd_rate: Option<f64> = data.get_item("usd_rate")?.and_then(|v| v.extract().ok());
        let eur_rate: Option<f64> = data.get_item("eur_rate")?.and_then(|v| v.extract().ok());

        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let updated_at = Utc::now().to_rfc3339();
                
                let result = sqlx::query(
                    r#"
                    UPDATE expense_invoices SET
                    fatura_no = ?, tarih = ?, firma = ?, malzeme = ?, miktar = ?, 
                    toplam_tutar_tl = ?, toplam_tutar_usd = ?, toplam_tutar_eur = ?, birim = ?, 
                    kdv_yuzdesi = ?, kdv_tutari = ?, kdv_dahil = ?, usd_rate = ?, eur_rate = ?, updated_at = ?
                    WHERE id = ?
                    "#
                )
                .bind(fatura_no)
                .bind(tarih)
                .bind(firma)
                .bind(malzeme)
                .bind(miktar)
                .bind(toplam_tutar_tl)
                .bind(toplam_tutar_usd)
                .bind(toplam_tutar_eur)
                .bind(birim)
                .bind(kdv_yuzdesi)
                .bind(kdv_tutari)
                .bind(kdv_dahil)
                .bind(usd_rate)
                .bind(eur_rate)
                .bind(updated_at)
                .bind(invoice_id)
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to update gider invoice: {}", e)))?;

                Ok(result.rows_affected() > 0)
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn delete_gider_invoice(&self, invoice_id: i64) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let result = sqlx::query("DELETE FROM expense_invoices WHERE id = ?")
                    .bind(invoice_id)
                    .execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to delete gider invoice: {}", e)))?;

                Ok(result.rows_affected() as i64)
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn delete_multiple_gider_invoices(&self, invoice_ids: Vec<i64>) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        self.runtime.block_on(async move {
            if invoice_ids.is_empty() {
                return Ok(0);
            }

            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let placeholders = vec!["?"; invoice_ids.len()].join(",");
                let query = format!("DELETE FROM expense_invoices WHERE id IN ({})", placeholders);
                
                let mut q = sqlx::query(&query);
                for id in invoice_ids {
                    q = q.bind(id);
                }
                
                let result = q.execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to delete multiple gider invoices: {}", e)))?;

                Ok(result.rows_affected() as i64)
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_all_gider_invoices(&self, py: Python<'_>, limit: Option<i64>, offset: Option<i64>, order_by: Option<String>) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let rows = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let order_clause = order_by.unwrap_or_else(|| "tarih DESC".to_string());
                let query = if let Some(lim) = limit {
                    format!(
                        "SELECT * FROM expense_invoices ORDER BY {} LIMIT {} OFFSET {}",
                        order_clause, lim, offset.unwrap_or(0)
                    )
                } else {
                    format!("SELECT * FROM expense_invoices ORDER BY {}", order_clause)
                };

                sqlx::query(&query)
                    .fetch_all(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to fetch gider invoices: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        let result = PyList::empty_bound(py);
        for row in rows {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", row.get::<i64, _>("id"))?;
            dict.set_item("fatura_no", row.try_get::<String, _>("fatura_no").ok())?;
            
            let tarih_iso = row.try_get::<String, _>("tarih").ok();
            let tarih_display = tarih_iso.as_ref().map(|t| to_display_date(t));
            dict.set_item("tarih", tarih_display)?;

            dict.set_item("firma", row.try_get::<String, _>("firma").ok())?;
            dict.set_item("malzeme", row.try_get::<String, _>("malzeme").ok())?;
            dict.set_item("miktar", row.try_get::<String, _>("miktar").ok())?;
            dict.set_item("toplam_tutar_tl", row.try_get::<f64, _>("toplam_tutar_tl").ok())?;
            dict.set_item("toplam_tutar_usd", row.try_get::<f64, _>("toplam_tutar_usd").ok())?;
            dict.set_item("toplam_tutar_eur", row.try_get::<f64, _>("toplam_tutar_eur").ok())?;
            dict.set_item("birim", row.try_get::<String, _>("birim").ok())?;
            dict.set_item("kdv_yuzdesi", row.try_get::<f64, _>("kdv_yuzdesi").ok())?;
            dict.set_item("kdv_tutari", row.try_get::<f64, _>("kdv_tutari").ok())?;
            dict.set_item("kdv_dahil", row.try_get::<i64, _>("kdv_dahil").ok())?;
            dict.set_item("usd_rate", row.try_get::<f64, _>("usd_rate").ok())?;
            dict.set_item("eur_rate", row.try_get::<f64, _>("eur_rate").ok())?;
            dict.set_item("updated_at", row.try_get::<String, _>("updated_at").ok())?;
            dict.set_item("created_at", row.try_get::<String, _>("created_at").ok())?;
            result.append(dict)?;
        }
        Ok(result.into())
    }

    fn get_gider_invoice_count(&self) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let row = sqlx::query("SELECT COUNT(*) as count FROM expense_invoices")
                    .fetch_one(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to count gider invoices: {}", e)))?;

                Ok(row.get::<i64, _>("count"))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_gider_invoice_by_id(&self, py: Python<'_>, invoice_id: i64) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let row = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                sqlx::query("SELECT * FROM expense_invoices WHERE id = ?")
                    .bind(invoice_id)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to fetch gider invoice: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        if let Some(r) = row {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", r.get::<i64, _>("id"))?;
            dict.set_item("fatura_no", r.try_get::<String, _>("fatura_no").ok())?;
            
            let tarih_iso = r.try_get::<String, _>("tarih").ok();
            let tarih_display = tarih_iso.as_ref().map(|t| to_display_date(t));
            dict.set_item("tarih", tarih_display)?;

            dict.set_item("firma", r.try_get::<String, _>("firma").ok())?;
            dict.set_item("malzeme", r.try_get::<String, _>("malzeme").ok())?;
            dict.set_item("miktar", r.try_get::<String, _>("miktar").ok())?;
            dict.set_item("toplam_tutar_tl", r.try_get::<f64, _>("toplam_tutar_tl").ok())?;
            dict.set_item("toplam_tutar_usd", r.try_get::<f64, _>("toplam_tutar_usd").ok())?;
            dict.set_item("toplam_tutar_eur", r.try_get::<f64, _>("toplam_tutar_eur").ok())?;
            dict.set_item("birim", r.try_get::<String, _>("birim").ok())?;
            dict.set_item("kdv_yuzdesi", r.try_get::<f64, _>("kdv_yuzdesi").ok())?;
            dict.set_item("kdv_tutari", r.try_get::<f64, _>("kdv_tutari").ok())?;
            dict.set_item("kdv_dahil", r.try_get::<i64, _>("kdv_dahil").ok())?;
            dict.set_item("usd_rate", r.try_get::<f64, _>("usd_rate").ok())?;
            dict.set_item("eur_rate", r.try_get::<f64, _>("eur_rate").ok())?;
            dict.set_item("updated_at", r.try_get::<String, _>("updated_at").ok())?;
            dict.set_item("created_at", r.try_get::<String, _>("created_at").ok())?;
            Ok(dict.into())
        } else {
            Ok(py.None())
        }
    }

    // ============================================================================
    // AYAR METOTLARI
    // ============================================================================
    
    fn get_setting(&self, key: String) -> PyResult<Option<String>> {
        let settings_pool = self.settings_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = settings_pool.read().await.as_ref() {
                let row = sqlx::query("SELECT value FROM settings WHERE key = ?")
                    .bind(&key)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get setting: {}", e)))?;

                Ok(row.and_then(|r| r.try_get::<String, _>("value").ok()))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn save_setting(&self, key: String, value: String) -> PyResult<()> {
        let settings_pool = self.settings_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = settings_pool.read().await.as_ref() {
                sqlx::query(
                    r#"
                    INSERT INTO settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    "#
                )
                .bind(key)
                .bind(value)
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to save setting: {}", e)))?;

                Ok(())
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_all_settings(&self, py: Python<'_>) -> PyResult<PyObject> {
        let settings_pool = self.settings_pool.clone();
        
        let rows = self.runtime.block_on(async move {
            if let Some(pool) = settings_pool.read().await.as_ref() {
                sqlx::query("SELECT key, value FROM settings")
                    .fetch_all(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get all settings: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        let dict = PyDict::new_bound(py);
        for row in rows {
            let key = row.get::<String, _>("key");
            let value = row.get::<String, _>("value");
            dict.set_item(key, value)?;
        }
        Ok(dict.into())
    }

    // ============================================================================
    // DÖVİZ KURU METOTLARI
    // ============================================================================
    
    fn save_exchange_rates(&self, usd_rate: f64, eur_rate: f64) -> PyResult<()> {
        let settings_pool = self.settings_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = settings_pool.read().await.as_ref() {
                let date = Utc::now().format("%Y-%m-%d").to_string();
                
                sqlx::query(
                    r#"
                    INSERT INTO exchange_rates (date, usd_rate, eur_rate) VALUES (?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET usd_rate = excluded.usd_rate, eur_rate = excluded.eur_rate
                    "#
                )
                .bind(date)
                .bind(usd_rate)
                .bind(eur_rate)
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to save exchange rates: {}", e)))?;

                Ok(())
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn load_exchange_rates(&self) -> PyResult<(f64, f64)> {
        let settings_pool = self.settings_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = settings_pool.read().await.as_ref() {
                let date = Utc::now().format("%Y-%m-%d").to_string();
                
                let row = sqlx::query("SELECT usd_rate, eur_rate FROM exchange_rates WHERE date = ?")
                    .bind(date)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to load exchange rates: {}", e)))?;

                if let Some(r) = row {
                    Ok((
                        r.get::<f64, _>("usd_rate"),
                        r.get::<f64, _>("eur_rate")
                    ))
                } else {
                    Ok((0.0, 0.0))
                }
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    // ===== GEÇMİŞ METOTLARI =====
    
    fn add_history_record(&self, action: String, details: String) -> PyResult<()> {
        let history_pool = self.history_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = history_pool.read().await.as_ref() {
                let timestamp = Utc::now().to_rfc3339();
                
                sqlx::query(
                    "INSERT INTO history (action, details, timestamp) VALUES (?, ?, ?)"
                )
                .bind(action)
                .bind(details)
                .bind(timestamp)
                .execute(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to add history record: {}", e)))?;

                Ok(())
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_recent_history(&self, py: Python<'_>, limit: i64) -> PyResult<PyObject> {
        let history_pool = self.history_pool.clone();
        
        let rows = self.runtime.block_on(async move {
            if let Some(pool) = history_pool.read().await.as_ref() {
                sqlx::query("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?")
                    .bind(limit)
                    .fetch_all(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get recent history: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        let result = PyList::empty_bound(py);
        for row in rows {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", row.get::<i64, _>("id"))?;
            dict.set_item("action", row.get::<String, _>("action"))?;
            dict.set_item("details", row.get::<String, _>("details"))?;
            dict.set_item("timestamp", row.get::<String, _>("timestamp"))?;
            result.append(dict)?;
        }
        Ok(result.into())
    }

    fn get_history_by_date_range(&self, py: Python<'_>, start_date: String, end_date: String) -> PyResult<PyObject> {
        let history_pool = self.history_pool.clone();
        
        let rows = self.runtime.block_on(async move {
            if let Some(pool) = history_pool.read().await.as_ref() {
                sqlx::query(
                    "SELECT * FROM history WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp DESC"
                )
                .bind(start_date)
                .bind(end_date)
                .fetch_all(pool)
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to get history by date range: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        let result = PyList::empty_bound(py);
        for row in rows {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", row.get::<i64, _>("id"))?;
            dict.set_item("action", row.get::<String, _>("action"))?;
            dict.set_item("details", row.get::<String, _>("details"))?;
            dict.set_item("timestamp", row.get::<String, _>("timestamp"))?;
            result.append(dict)?;
        }
        Ok(result.into())
    }

    fn clear_old_history(&self, days: i64) -> PyResult<i64> {
        let history_pool = self.history_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = history_pool.read().await.as_ref() {
                let cutoff_date = (Utc::now() - chrono::Duration::days(days)).to_rfc3339();
                
                let result = sqlx::query("DELETE FROM history WHERE timestamp < ?")
                    .bind(cutoff_date)
                    .execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to clear old history: {}", e)))?;

                Ok(result.rows_affected() as i64)
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    // ===== YILLIK GİDER METOTLARI =====
    
    fn add_or_update_yearly_expenses(&self, year: i64, _py: Python<'_>, monthly_data: &Bound<'_, PyDict>) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        // Aylık verileri çıkar
        let months = vec!["ocak", "subat", "mart", "nisan", "mayis", "haziran",
                         "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"];
        let mut monthly_amounts: Vec<f64> = Vec::new();
        
        for month in &months {
            let amount = monthly_data.get_item(month)?
                .and_then(|v| v.extract::<f64>().ok())
                .unwrap_or(0.0);
            monthly_amounts.push(amount);
        }
        
        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                // Yılın var olup olmadığını kontrol et
                let check = sqlx::query("SELECT id FROM general_expenses WHERE yil = ?")
                    .bind(year)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to check yearly expenses: {}", e)))?;

                if check.is_some() {
                    // Güncelle
                    let result = sqlx::query(
                        r#"
                        UPDATE general_expenses SET
                        ocak = ?, subat = ?, mart = ?, nisan = ?, mayis = ?, haziran = ?,
                        temmuz = ?, agustos = ?, eylul = ?, ekim = ?, kasim = ?, aralik = ?
                        WHERE yil = ?
                        "#
                    )
                    .bind(monthly_amounts[0])
                    .bind(monthly_amounts[1])
                    .bind(monthly_amounts[2])
                    .bind(monthly_amounts[3])
                    .bind(monthly_amounts[4])
                    .bind(monthly_amounts[5])
                    .bind(monthly_amounts[6])
                    .bind(monthly_amounts[7])
                    .bind(monthly_amounts[8])
                    .bind(monthly_amounts[9])
                    .bind(monthly_amounts[10])
                    .bind(monthly_amounts[11])
                    .bind(year)
                    .execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to update yearly expenses: {}", e)))?;

                    Ok(result.rows_affected() as i64)
                } else {
                    // Ekle
                    let result = sqlx::query(
                        r#"
                        INSERT INTO general_expenses (yil, ocak, subat, mart, nisan, mayis, haziran,
                                                     temmuz, agustos, eylul, ekim, kasim, aralik)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        "#
                    )
                    .bind(year)
                    .bind(monthly_amounts[0])
                    .bind(monthly_amounts[1])
                    .bind(monthly_amounts[2])
                    .bind(monthly_amounts[3])
                    .bind(monthly_amounts[4])
                    .bind(monthly_amounts[5])
                    .bind(monthly_amounts[6])
                    .bind(monthly_amounts[7])
                    .bind(monthly_amounts[8])
                    .bind(monthly_amounts[9])
                    .bind(monthly_amounts[10])
                    .bind(monthly_amounts[11])
                    .execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to insert yearly expenses: {}", e)))?;

                    Ok(result.last_insert_rowid())
                }
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_yearly_expenses(&self, py: Python<'_>, year: i64) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let row = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                sqlx::query("SELECT * FROM general_expenses WHERE yil = ?")
                    .bind(year)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get yearly expenses: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        if let Some(r) = row {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", r.get::<i64, _>("id"))?;
            dict.set_item("yil", r.get::<i64, _>("yil"))?;
            dict.set_item("ocak", r.get::<f64, _>("ocak"))?;
            dict.set_item("subat", r.get::<f64, _>("subat"))?;
            dict.set_item("mart", r.get::<f64, _>("mart"))?;
            dict.set_item("nisan", r.get::<f64, _>("nisan"))?;
            dict.set_item("mayis", r.get::<f64, _>("mayis"))?;
            dict.set_item("haziran", r.get::<f64, _>("haziran"))?;
            dict.set_item("temmuz", r.get::<f64, _>("temmuz"))?;
            dict.set_item("agustos", r.get::<f64, _>("agustos"))?;
            dict.set_item("eylul", r.get::<f64, _>("eylul"))?;
            dict.set_item("ekim", r.get::<f64, _>("ekim"))?;
            dict.set_item("kasim", r.get::<f64, _>("kasim"))?;
            dict.set_item("aralik", r.get::<f64, _>("aralik"))?;
            Ok(dict.into())
        } else {
            Ok(py.None())
        }
    }

    fn get_yearly_expenses_by_id(&self, py: Python<'_>, id: i64) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let row = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                sqlx::query("SELECT * FROM general_expenses WHERE id = ?")
                    .bind(id)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get yearly expenses by id: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        if let Some(r) = row {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", r.get::<i64, _>("id"))?;
            dict.set_item("yil", r.get::<i64, _>("yil"))?;
            dict.set_item("ocak", r.get::<f64, _>("ocak"))?;
            dict.set_item("subat", r.get::<f64, _>("subat"))?;
            dict.set_item("mart", r.get::<f64, _>("mart"))?;
            dict.set_item("nisan", r.get::<f64, _>("nisan"))?;
            dict.set_item("mayis", r.get::<f64, _>("mayis"))?;
            dict.set_item("haziran", r.get::<f64, _>("haziran"))?;
            dict.set_item("temmuz", r.get::<f64, _>("temmuz"))?;
            dict.set_item("agustos", r.get::<f64, _>("agustos"))?;
            dict.set_item("eylul", r.get::<f64, _>("eylul"))?;
            dict.set_item("ekim", r.get::<f64, _>("ekim"))?;
            dict.set_item("kasim", r.get::<f64, _>("kasim"))?;
            dict.set_item("aralik", r.get::<f64, _>("aralik"))?;
            Ok(dict.into())
        } else {
            Ok(py.None())
        }
    }

    fn get_yearly_expenses_count(&self) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                let row = sqlx::query("SELECT COUNT(*) as count FROM general_expenses")
                    .fetch_one(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to count yearly expenses: {}", e)))?;

                Ok(row.get::<i64, _>("count"))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_all_yearly_expenses(&self, py: Python<'_>) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let rows = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                sqlx::query("SELECT * FROM general_expenses ORDER BY yil DESC")
                    .fetch_all(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get all yearly expenses: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        let result = PyList::empty_bound(py);
        for row in rows {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", row.get::<i64, _>("id"))?;
            dict.set_item("yil", row.get::<i64, _>("yil"))?;
            dict.set_item("ocak", row.get::<f64, _>("ocak"))?;
            dict.set_item("subat", row.get::<f64, _>("subat"))?;
            dict.set_item("mart", row.get::<f64, _>("mart"))?;
            dict.set_item("nisan", row.get::<f64, _>("nisan"))?;
            dict.set_item("mayis", row.get::<f64, _>("mayis"))?;
            dict.set_item("haziran", row.get::<f64, _>("haziran"))?;
            dict.set_item("temmuz", row.get::<f64, _>("temmuz"))?;
            dict.set_item("agustos", row.get::<f64, _>("agustos"))?;
            dict.set_item("eylul", row.get::<f64, _>("eylul"))?;
            dict.set_item("ekim", row.get::<f64, _>("ekim"))?;
            dict.set_item("kasim", row.get::<f64, _>("kasim"))?;
            dict.set_item("aralik", row.get::<f64, _>("aralik"))?;
            result.append(dict)?;
        }
        Ok(result.into())
    }

    // ===== KURUMLAR VERGİSİ METOTLARI =====
    
    fn add_or_update_corporate_tax(&self, year: i64, _py: Python<'_>, monthly_data: &Bound<'_, PyDict>) -> PyResult<i64> {
        let invoices_pool = self.invoices_pool.clone();
        
        // Aylık verileri çıkar
        let months = vec!["ocak", "subat", "mart", "nisan", "mayis", "haziran",
                         "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"];
        let mut monthly_amounts: Vec<f64> = Vec::new();
        
        for month in &months {
            let amount = monthly_data.get_item(month)?
                .and_then(|v| v.extract::<f64>().ok())
                .unwrap_or(0.0);
            monthly_amounts.push(amount);
        }
        
        self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                // Yılın var olup olmadığını kontrol et
                let check = sqlx::query("SELECT id FROM corporate_tax WHERE yil = ?")
                    .bind(year)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to check corporate tax: {}", e)))?;

                if check.is_some() {
                    // Güncelle
                    let result = sqlx::query(
                        r#"
                        UPDATE corporate_tax SET
                        ocak = ?, subat = ?, mart = ?, nisan = ?, mayis = ?, haziran = ?,
                        temmuz = ?, agustos = ?, eylul = ?, ekim = ?, kasim = ?, aralik = ?
                        WHERE yil = ?
                        "#
                    )
                    .bind(monthly_amounts[0])
                    .bind(monthly_amounts[1])
                    .bind(monthly_amounts[2])
                    .bind(monthly_amounts[3])
                    .bind(monthly_amounts[4])
                    .bind(monthly_amounts[5])
                    .bind(monthly_amounts[6])
                    .bind(monthly_amounts[7])
                    .bind(monthly_amounts[8])
                    .bind(monthly_amounts[9])
                    .bind(monthly_amounts[10])
                    .bind(monthly_amounts[11])
                    .bind(year)
                    .execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to update corporate tax: {}", e)))?;

                    Ok(result.rows_affected() as i64)
                } else {
                    // Ekle
                    let result = sqlx::query(
                        r#"
                        INSERT INTO corporate_tax (yil, ocak, subat, mart, nisan, mayis, haziran,
                                                   temmuz, agustos, eylul, ekim, kasim, aralik)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        "#
                    )
                    .bind(year)
                    .bind(monthly_amounts[0])
                    .bind(monthly_amounts[1])
                    .bind(monthly_amounts[2])
                    .bind(monthly_amounts[3])
                    .bind(monthly_amounts[4])
                    .bind(monthly_amounts[5])
                    .bind(monthly_amounts[6])
                    .bind(monthly_amounts[7])
                    .bind(monthly_amounts[8])
                    .bind(monthly_amounts[9])
                    .bind(monthly_amounts[10])
                    .bind(monthly_amounts[11])
                    .execute(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to insert corporate tax: {}", e)))?;

                    Ok(result.last_insert_rowid())
                }
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })
    }

    fn get_corporate_tax(&self, py: Python<'_>, year: i64) -> PyResult<PyObject> {
        let invoices_pool = self.invoices_pool.clone();
        
        let row = self.runtime.block_on(async move {
            if let Some(pool) = invoices_pool.read().await.as_ref() {
                sqlx::query("SELECT * FROM corporate_tax WHERE yil = ?")
                    .bind(year)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get corporate tax: {}", e)))
            } else {
                Err(PyRuntimeError::new_err("Database not initialized"))
            }
        })?;

        if let Some(r) = row {
            let dict = PyDict::new_bound(py);
            dict.set_item("id", r.get::<i64, _>("id"))?;
            dict.set_item("yil", r.get::<i64, _>("yil"))?;
            dict.set_item("ocak", r.get::<f64, _>("ocak"))?;
            dict.set_item("subat", r.get::<f64, _>("subat"))?;
            dict.set_item("mart", r.get::<f64, _>("mart"))?;
            dict.set_item("nisan", r.get::<f64, _>("nisan"))?;
            dict.set_item("mayis", r.get::<f64, _>("mayis"))?;
            dict.set_item("haziran", r.get::<f64, _>("haziran"))?;
            dict.set_item("temmuz", r.get::<f64, _>("temmuz"))?;
            dict.set_item("agustos", r.get::<f64, _>("agustos"))?;
            dict.set_item("eylul", r.get::<f64, _>("eylul"))?;
            dict.set_item("ekim", r.get::<f64, _>("ekim"))?;
            dict.set_item("kasim", r.get::<f64, _>("kasim"))?;
            dict.set_item("aralik", r.get::<f64, _>("aralik"))?;
            Ok(dict.into())
        } else {
            Ok(py.None())
        }
    }
}

#[pymodule]
fn rust_db(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Database>()?;
    Ok(())
}
