# 🏗️ Proje Mimarisi - Excellent

## 📋 Mimari Özet

Bu dokümantasyon, Excellent uygulamasının teknik mimarisini ve ekip üyelerinin sorumluluklarını detaylı olarak açıklamaktadır. Mimari, MVP odaklı geliştirme sürecini destekleyecek şekilde tasarlanmıştır.

## 🎯 Mimari Prensipler

### **1. MVP Odaklı Mimari**
- **Prensip:** 3 haftalık MVP teslimi için minimal ama genişletilebilir mimari
- **Uygulama:** Sadece MVP için gerekli bileşenler, V2.0 için hazır altyapı
- **Sorumlu:** Proje Yöneticisi / Test Koordinatörü

### **2. Separation of Concerns**
- **Prensip:** Backend, Frontend ve Veri katmanlarının ayrılması
- **Uygulama:** API-based communication, loose coupling
- **Sorumlu:** Backend Developer (API design), Frontend Developer (UI separation)

### **3. Scalability by Design**
- **Prensip:** Gelecekteki büyüme için hazır mimari
- **Uygulama:** Microservice-ready, database abstraction
- **Sorumlu:** Backend Developer

### **4. Testability**
- **Prensip:** Her bileşen test edilebilir olmalı
- **Uygulama:** Unit tests, integration tests, mock objects
- **Sorumlu:** Tüm ekip

## 🏛️ Sistem Mimarisi Diyagramı

```
┌─────────────────────────────────────────────────────────────────┐
│                           EXCELLENT              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   FRONTEND      │    │    BACKEND      │    │   DATABASE   │ │
│  │   (PyQt6)       │    │   (FastAPI)     │    │   (SQLite)   │ │
│  │                 │    │                 │    │              │ │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌──────────┐ │ │
│  │ │ Ana Pencere │ │◄──►│ │ API Gateway │ │◄──►│ │ Fatura   │ │ │
│  │ │             │ │    │ │             │ │    │ │ Tablosu  │ │ │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └──────────┘ │ │
│  │                 │    │                 │    │              │ │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌──────────┐ │ │
│  │ │ Fatura Form │ │◄──►│ │ Fatura API  │ │◄──►│ │ Para     │ │ │
│  │ │             │ │    │ │             │ │    │ │ Birimi   │ │ │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ │ Tablosu  │ │ │
│  │                 │    │                 │    │ └──────────┘ │ │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │              │ │
│  │ │ Rapor       │ │◄──►│ │ Rapor API   │ │◄──►│ ┌──────────┐ │ │
│  │ │ Görünümü    │ │    │ │             │ │    │ │ Rapor    │ │ │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ │ Tablosu  │ │ │
│  │                 │    │                 │    │ └──────────┘ │ │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │              │ │
│  │ │ Excel       │ │◄──►│ │ Excel       │ │    │              │ │
│  │ │ Export UI   │ │    │ │ Export      │ │    │              │ │
│  │ └─────────────┘ │    │ │ Servisi     │ │    │              │ │
│  │                 │    │ └─────────────┘ │    │              │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                              │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   EXTERNAL      │    │   BACKGROUND    │                     │
│  │   SERVICES      │    │   SERVICES      │                     │
│  │                 │    │                 │                     │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │                     │
│  │ │ Döviz Kuru  │ │    │ │ Celery      │ │                     │
│  │ │ API         │ │◄──►│ │ Worker      │ │                     │
│  │ └─────────────┘ │    │ └─────────────┘ │                     │
│  │                 │    │                 │                     │
│  │                 │    │ ┌─────────────┐ │                     │
│  │                 │    │ │ Redis       │ │                     │
│  │                 │    │ │ Cache       │ │                     │
│  │                 │    │ └─────────────┘ │                     │
│  └─────────────────┘    └─────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Ekip Sorumlulukları ve Mimari Bileşenler

### **Proje Yöneticisi / Test Koordinatörü**
**Mimari Sorumlulukları:**
- ✅ **Mimari Kararlar:** Teknik mimari onayı ve koordinasyonu
- ✅ **API Contract Yönetimi:** Backend-Frontend API contract'larının belirlenmesi
- ✅ **Test Stratejisi:** Mimari bileşenlerin test stratejisinin belirlenmesi
- ✅ **Deployment Koordinasyonu:** Sistem deployment'ının koordinasyonu

**Mimari Dokümantasyonu:**
```
📁 mimari_dokumantasyonu/
├── api_contracts.md          # API endpoint'leri ve data modelleri
├── test_strategy.md          # Test stratejisi ve senaryoları
├── deployment_plan.md        # Deployment planı ve prosedürleri
└── architecture_decisions.md # Mimari kararlar ve gerekçeleri
```

### **Backend Developer**
**Mimari Sorumlulukları:**
- ✅ **API Tasarımı:** RESTful API endpoint'lerinin tasarımı ve implementasyonu
- ✅ **Veritabanı Tasarımı:** SQLAlchemy modelleri ve migration'lar
- ✅ **Servis Katmanı:** İş mantığı servislerinin geliştirilmesi
- ✅ **Background Jobs:** Celery worker'ları ve asenkron görevler

**Backend Mimari Yapısı:**
```
📁 backend/
├── app/
│   ├── main.py              # FastAPI uygulaması entry point
│   ├── config.py            # Konfigürasyon yönetimi
│   ├── database.py          # Veritabanı bağlantı yönetimi
│   └── models/              # SQLAlchemy veri modelleri
│       ├── fatura.py        # Fatura modeli
│       ├── para_birimi.py   # Para birimi modeli
│       └── rapor.py         # Rapor modeli
├── api/                     # API endpoint'leri
│   ├── fatura.py           # Fatura CRUD API'leri
│   ├── para_birimi.py      # Para birimi API'leri
│   └── rapor.py            # Rapor API'leri
├── services/               # İş mantığı servisleri
│   ├── fatura_service.py   # Fatura iş mantığı
│   ├── doviz_service.py    # Döviz kuru servisleri
│   └── rapor_service.py    # Rapor oluşturma servisleri
├── utils/                  # Yardımcı fonksiyonlar
│   ├── hesaplamalar.py     # KDV, vergi hesaplamaları
│   └── validasyon.py       # Veri validasyon fonksiyonları
└── tests/                  # Backend testleri
    ├── test_api.py         # API testleri
    ├── test_services.py    # Servis testleri
    └── test_models.py      # Model testleri
```

**API Endpoint Tasarımı:**
```python
# Fatura API Endpoints
POST   /api/v1/faturalar/           # Yeni fatura oluştur
GET    /api/v1/faturalar/           # Fatura listesi (filtreleme ile)
GET    /api/v1/faturalar/{id}       # Tekil fatura detayı
PUT    /api/v1/faturalar/{id}       # Fatura güncelle
DELETE /api/v1/faturalar/{id}       # Fatura sil

# Para Birimi API Endpoints
GET    /api/v1/para-birimleri/      # Para birimi listesi
POST   /api/v1/para-birimleri/kur/  # Döviz kuru güncelle
GET    /api/v1/para-birimleri/kur/  # Güncel kurlar

# Rapor API Endpoints
GET    /api/v1/raporlar/aylik/      # Aylık fatura raporu
GET    /api/v1/raporlar/excel/      # Excel export
GET    /api/v1/raporlar/pdf/        # PDF export (V2.0)
```

### **Frontend Developer**
**Mimari Sorumlulukları:**
- ✅ **UI Katmanı:** PyQt6 masaüstü uygulaması tasarımı
- ✅ **API Entegrasyonu:** Backend API'leri ile iletişim
- ✅ **Kullanıcı Deneyimi:** UI/UX tasarımı ve optimizasyonu
- ✅ **Komponent Mimarisi:** Yeniden kullanılabilir UI komponentleri

**Frontend Mimari Yapısı:**
```
📁 frontend/
├── main.py                 # PyQt6 ana uygulama entry point
├── ui/                     # UI sınıfları ve widget'ları
│   ├── main_window.py      # Ana pencere ve menü sistemi
│   ├── fatura_form.py      # Fatura giriş/düzenleme formu
│   ├── fatura_list.py      # Fatura listesi görünümü
│   ├── rapor_view.py       # Rapor görünümleri
│   └── components/         # Yeniden kullanılabilir komponentler
│       ├── excel_table.py  # Excel benzeri tablo komponenti
│       ├── para_birimi_selector.py  # Para birimi seçici
│       ├── chart_widget.py # Grafik widget'ı
│       └── export_dialog.py # Export dialog'u
├── controllers/            # UI kontrolcüleri
│   ├── fatura_controller.py # Fatura işlem kontrolcüsü
│   ├── rapor_controller.py  # Rapor kontrolcüsü
│   └── api_client.py       # Backend API client
├── models/                 # Frontend veri modelleri
│   ├── fatura_model.py     # Fatura veri modeli
│   └── rapor_model.py      # Rapor veri modeli
└── tests/                  # Frontend testleri
    ├── test_ui.py          # UI widget testleri
    └── test_controllers.py # Controller testleri
```

**UI Komponent Mimarisi:**
```python
# Ana UI Bileşenleri
MainWindow
├── MenuBar (Fatura, Para Birimi, Raporlar, Yardım)
├── ToolBar (Hızlı erişim butonları)
├── StatusBar (Durum bilgileri)
└── CentralWidget
    ├── FaturaForm (Fatura giriş/düzenleme)
    ├── FaturaList (Fatura listesi ve filtreleme)
    ├── RaporView (Rapor görünümleri)
    └── SettingsDialog (Ayarlar)

# Yeniden Kullanılabilir Komponentler
ExcelTable
├── Header (Sıralama, filtreleme)
├── Body (Veri gösterimi)
└── Footer (Toplam, sayfa bilgisi)

ParaBirimiSelector
├── CurrencyDropdown (TL, USD, EUR)
├── RateInput (Manuel kur girişi)
└── AutoUpdateToggle (Otomatik güncelleme)
```

## 🗄️ Veri Mimarisi

### **Veritabanı Şeması (SQLite/PostgreSQL)**

**Fatura Tablosu:**
```sql
CREATE TABLE faturalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fatura_no VARCHAR(50) NOT NULL,
    fatura_tipi ENUM('kesilen', 'gelen') NOT NULL,
    tarih DATE NOT NULL,
    musteri_adi VARCHAR(255) NOT NULL,
    tutar DECIMAL(15,2) NOT NULL,
    para_birimi VARCHAR(3) NOT NULL,
    kdv_orani DECIMAL(5,2) DEFAULT 18.00,
    kdv_tutari DECIMAL(15,2),
    toplam_tutar DECIMAL(15,2),
    durum ENUM('beklemede', 'odenmis', 'gecikmis') DEFAULT 'beklemede',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Para Birimi Tablosu:**
```sql
CREATE TABLE para_birimleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kod VARCHAR(3) NOT NULL UNIQUE,
    ad VARCHAR(50) NOT NULL,
    sembol VARCHAR(5) NOT NULL,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE doviz_kurlari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    para_birimi_id INTEGER NOT NULL,
    kur DECIMAL(10,4) NOT NULL,
    tarih DATE NOT NULL,
    kaynak VARCHAR(50) DEFAULT 'manuel',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (para_birimi_id) REFERENCES para_birimleri(id)
);
```

**Rapor Tablosu:**
```sql
CREATE TABLE raporlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rapor_adi VARCHAR(255) NOT NULL,
    rapor_tipi ENUM('aylik', 'yillik', 'ozel') NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    parametreler JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Veri Akışı Mimarisi**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FRONTEND  │    │   BACKEND   │    │  DATABASE   │
│             │    │             │    │             │
│ Fatura Form │───►│ API Gateway │───►│ Fatura      │
│             │    │             │    │ Tablosu     │
│             │    │             │    │             │
│ Validasyon  │◄───│ Validasyon  │◄───│ Constraint  │
│             │    │             │    │ Check       │
│             │    │             │    │             │
│ API Call    │───►│ Service     │───►│ Transaction │
│             │    │ Layer       │    │ Management  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔄 API Mimarisi

### **RESTful API Tasarım Prensipleri**

**1. Resource-Based URLs:**
```
/faturalar          # Fatura koleksiyonu
/faturalar/123      # Tekil fatura
/faturalar/123/rapor # Fatura raporu
```

**2. HTTP Method Semantikleri:**
```
GET    /faturalar           # Liste getir
POST   /faturalar           # Yeni oluştur
GET    /faturalar/123       # Tekil getir
PUT    /faturalar/123       # Tamamen güncelle
PATCH  /faturalar/123       # Kısmi güncelle
DELETE /faturalar/123       # Sil
```

**3. Response Format Standardı:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "fatura_no": "FAT-2024-001",
    "tutar": 1000.00,
    "para_birimi": "TL"
  },
  "message": "Fatura başarıyla oluşturuldu",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### **Error Handling Mimarisi**
```python
# API Error Response Format
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Geçersiz veri girişi",
    "details": [
      {
        "field": "tutar",
        "message": "Tutar 0'dan büyük olmalıdır"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔧 Servis Katmanı Mimarisi

### **Business Logic Services**

**Fatura Servisi:**
```python
class FaturaService:
    def fatura_olustur(self, fatura_data: FaturaCreateModel) -> FaturaModel:
        # 1. Veri validasyonu
        # 2. KDV hesaplama
        # 3. Para birimi dönüşümü
        # 4. Veritabanına kaydetme
        # 5. Response dönme
    
    def fatura_listele(self, filters: FaturaFilterModel) -> List[FaturaModel]:
        # 1. Filtreleme parametrelerini işleme
        # 2. Veritabanı sorgusu
        # 3. Pagination
        # 4. Response dönme
    
    def kdv_hesapla(self, tutar: Decimal, kdv_orani: Decimal) -> Decimal:
        # KDV hesaplama mantığı
    
    def para_birimi_donustur(self, tutar: Decimal, 
                           from_currency: str, 
                           to_currency: str) -> Decimal:
        # Para birimi dönüşüm mantığı
```

**Döviz Kuru Servisi:**
```python
class DovizService:
    def kur_guncelle(self, para_birimi: str) -> Decimal:
        # 1. External API çağrısı
        # 2. Veri validasyonu
        # 3. Veritabanına kaydetme
        # 4. Cache güncelleme
    
    def guncel_kur_getir(self, para_birimi: str) -> Decimal:
        # 1. Cache kontrolü
        # 2. Veritabanından kur getirme
        # 3. Fallback mekanizması
    
    def otomatik_kur_guncelleme(self):
        # Celery background job
        # Tüm para birimleri için kur güncelleme
```

**Rapor Servisi:**
```python
class RaporService:
    def aylik_rapor_olustur(self, ay: int, yil: int) -> RaporModel:
        # 1. Tarih aralığı hesaplama
        # 2. Fatura verilerini toplama
        # 3. İstatistiksel hesaplamalar
        # 4. Rapor formatına dönüştürme
    
    def excel_export(self, rapor_data: RaporModel) -> bytes:
        # 1. Excel template oluşturma
        # 2. Veri yerleştirme
        # 3. Formatting
        # 4. Binary data dönme
    
    def pdf_export(self, rapor_data: RaporModel) -> bytes:
        # V2.0 için PDF oluşturma
```

## 🧪 Test Mimarisi

### **Test Piramidi**

```
┌─────────────────────────────────────┐
│           E2E Tests (5%)            │  ← Proje Yöneticisi
├─────────────────────────────────────┤
│        Integration Tests (15%)      │  ← Backend + Frontend
├─────────────────────────────────────┤
│          Unit Tests (80%)           │  ← Her geliştirici
└─────────────────────────────────────┘
```

### **Test Stratejisi**

**Backend Testleri:**
```python
# Unit Tests
test_fatura_service.py     # Servis katmanı testleri
test_api_endpoints.py      # API endpoint testleri
test_models.py            # Model validasyon testleri

# Integration Tests
test_database_integration.py  # Veritabanı entegrasyon testleri
test_external_api.py         # Dış API entegrasyon testleri

# Performance Tests
test_api_performance.py      # API performans testleri
test_database_performance.py # Veritabanı performans testleri
```

**Frontend Testleri:**
```python
# Unit Tests
test_ui_components.py        # UI komponent testleri
test_controllers.py          # Controller testleri
test_api_client.py          # API client testleri

# Integration Tests
test_ui_integration.py       # UI entegrasyon testleri
test_backend_integration.py  # Backend entegrasyon testleri

# UI Tests
test_user_workflows.py       # Kullanıcı akış testleri
test_form_validation.py      # Form validasyon testleri
```

## 🚀 Deployment Mimarisi

### **Development Environment**
```
Developer Machine
├── Python 3.11+
├── Virtual Environment
├── SQLite Database
├── Local Redis (optional)
└── PyQt6 Development Tools
```

### **Production Environment**
```
Production Server
├── Python 3.11+
├── PostgreSQL Database
├── Redis Cache
├── Nginx (Reverse Proxy)
├── Uvicorn (ASGI Server)
└── Celery Workers
```

### **Deployment Pipeline**
```
1. Code Commit → GitHub
2. Automated Tests → CI/CD Pipeline
3. Build → Docker Container
4. Deploy → Production Server
5. Health Check → Monitoring
```

## 📊 Monitoring ve Logging Mimarisi

### **Logging Strategy**
```python
# Structured Logging
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "fatura_service",
  "action": "fatura_olustur",
  "user_id": "user123",
  "fatura_id": "FAT-2024-001",
  "duration_ms": 150,
  "message": "Fatura başarıyla oluşturuldu"
}
```

### **Monitoring Metrics**
- **API Response Time:** <200ms (95th percentile)
- **Database Query Time:** <100ms (average)
- **Memory Usage:** <512MB
- **CPU Usage:** <70%
- **Error Rate:** <1%

### **Health Checks**
```python
# API Health Endpoints
GET /health/ready    # Ready check
GET /health/live     # Liveness check
GET /health/db       # Database connectivity
GET /health/redis    # Redis connectivity
```

## 🔒 Güvenlik Mimarisi

### **Authentication & Authorization**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CLIENT    │    │   API       │    │  DATABASE   │
│             │    │   GATEWAY   │    │             │
│ Login       │───►│ JWT Token   │───►│ User        │
│ Request     │    │ Validation  │    │ Validation  │
│             │    │             │    │             │
│ Session     │◄───│ Token       │◄───│ Role        │
│ Management  │    │ Response    │    │ Check       │
└─────────────┘    └─────────────┘    └─────────────┘
```

### **Data Protection**
- **Encryption at Rest:** SQLite encryption
- **Encryption in Transit:** HTTPS/TLS
- **Input Validation:** Pydantic models
- **SQL Injection Prevention:** SQLAlchemy ORM
- **XSS Prevention:** Input sanitization

## 📈 Performans Mimarisi

### **Caching Strategy**
```python
# Multi-level Caching
L1 Cache (In-Memory)
├── API Response Cache (5 minutes)
├── Database Query Cache (10 minutes)
└── Static Data Cache (1 hour)

L2 Cache (Redis)
├── Session Data
├── User Preferences
└── Report Cache
```

### **Database Optimization**
```sql
-- Indexing Strategy
CREATE INDEX idx_faturalar_tarih ON faturalar(tarih);
CREATE INDEX idx_faturalar_musteri ON faturalar(musteri_adi);
CREATE INDEX idx_faturalar_durum ON faturalar(durum);
CREATE INDEX idx_doviz_kurlari_para_birimi_tarih 
    ON doviz_kurlari(para_birimi_id, tarih);
```

## 🔄 Backup ve Recovery Mimarisi

### **Backup Strategy**
```
Daily Backup
├── Database Backup (SQLite/PostgreSQL dump)
├── Configuration Files Backup
├── Log Files Archive
└── User Data Backup

Weekly Backup
├── Full System Backup
├── Application Code Backup
└── Backup Verification
```

### **Recovery Procedures**
```
1. Database Recovery
   ├── Restore from latest backup
   ├── Verify data integrity
   └── Test application connectivity

2. Application Recovery
   ├── Deploy from backup
   ├── Restore configuration
   └── Verify functionality

3. Full System Recovery
   ├── Restore complete system
   ├── Restore database
   ├── Restore application
   └── Run health checks
```

## 🎯 MVP vs V2.0 Mimari Karşılaştırması

### **MVP Mimari (3 Hafta)**
```
Minimal Components:
├── SQLite Database
├── Basic FastAPI
├── Simple PyQt6 UI
├── Manual Currency Rates
├── Basic Excel Export
└── Simple Error Handling
```

### **V2.0 Mimari (8 Hafta)**
```
Enhanced Components:
├── PostgreSQL Database
├── Advanced FastAPI with Auth
├── Rich PyQt6 UI with Charts
├── Automated Currency API
├── PDF Export + Advanced Excel
├── Celery Background Jobs
├── Redis Caching
├── Comprehensive Logging
└── Production Deployment
```

## 📋 Mimari Kararlar ve Gerekçeleri

### **Karar 1: SQLite → PostgreSQL Geçişi**
- **Gerekçe:** MVP için SQLite yeterli, V2.0 için PostgreSQL scalability
- **Timeline:** MVP'de SQLite, V2.0'da PostgreSQL
- **Etki:** Veritabanı abstraction layer ile kolay geçiş

### **Karar 2: FastAPI Seçimi**
- **Gerekçe:** Modern, hızlı, otomatik dokümantasyon
- **Alternatifler:** Django, Flask
- **Karar:** FastAPI'nin async desteği ve performance avantajı

### **Karar 3: PyQt6 Seçimi**
- **Gerekçe:** Cross-platform, modern UI, Python entegrasyonu
- **Alternatifler:** Tkinter, Kivy, Electron
- **Karar:** PyQt6'nın masaüstü uygulaması için en uygun seçenek

### **Karar 4: API-First Tasarım**
- **Gerekçe:** Frontend-Backend separation, testability
- **Etki:** Loose coupling, independent development
- **Fayda:** Gelecekte web/mobile extension kolaylığı

Bu mimari dokümantasyonu, ekip üyelerinin sorumluluklarını ve sistem bileşenlerini net bir şekilde tanımlar. Her geliştirici bu dokümantasyona bakarak ne yapması gerektiğini kolayca anlayabilir.
