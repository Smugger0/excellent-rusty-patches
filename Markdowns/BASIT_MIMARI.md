# 🏗️ Basit Sistem Mimarisi - Finansal Yönetim Uygulaması (EXCELLENT)

## 🎯 Bu Dokümantasyon Kim İçin?

Bu dokümantasyon, **ilk defa böyle bir proje geliştiren** ekip üyeleri için hazırlanmıştır. Karmaşık terimler yerine **basit açıklamalar** ve **görsel örnekler** kullanılmıştır.

## 🏠 Sistemimizin Genel Görünümü


```
🏠 EXCELLENT

┌─────────────────────────────────────────────────────────┐
│                    KULLANICI ARAYÜZÜ                    │
│  (Buraya kullanıcılar bakacak ve işlem yapacak)        │
│                                                         │
│  📱 Fatura Giriş Ekranı                                │
│  📊 Rapor Görüntüleme                                  │
│  📋 Para Birimi Ayarları                               │
│  💾 Excel Çıktısı Alma                                 │
└─────────────────────────────────────────────────────────┘
                            ↕️ (Veri Alışverişi)
┌─────────────────────────────────────────────────────────┐
│                    İŞLEM MOTORU                         │
│  (Burada tüm hesaplamalar ve işlemler yapılacak)       │
│                                                         │
│  🧮 KDV Hesaplama                                       │
│  💱 Para Birimi Çevirme                                 │
│  📈 Rapor Oluşturma                                     │
│  💾 Veri Kaydetme/Getirme                               │
└─────────────────────────────────────────────────────────┘
                            ↕️ (Veri Saklama)
┌─────────────────────────────────────────────────────────┐
│                    VERİ DEPOSU                          │
│  (Tüm bilgiler burada güvenle saklanacak)              │
│                                                         │
│  📁 Fatura Bilgileri                                    │
│  💰 Para Birimi Kurları                                 │
│  📊 Rapor Geçmişi                                       │
│  ⚙️ Sistem Ayarları                                     │
└─────────────────────────────────────────────────────────┘
```

## 👥 Ekip Üyelerinin Görevleri

### 🎨 **Frontend Developer (UI Developer)**
**Ne Yapacak:** User Interface (kullanıcı arayüzü) tasarlayıp kodlayacak

**Görevleri:**
- ✅ Kullanıcıların göreceği ekranları tasarlamak (UI Design)
- ✅ Fatura giriş formunu yapmak (Form Development)
- ✅ Rapor görüntüleme ekranını yapmak (Report View)
- ✅ Excel export butonunu yapmak (Export Button)

**Kullanacağı Araçlar:**
- **PyQt6** - Desktop UI framework (masaüstü arayüz çerçevesi)

**Basit Açıklama:** "Kullanıcının gördüğü ve tıkladığı her şeyi yapacak (User Interface)"

---

### ⚙️ **Backend Developer (Server-side Developer)**
**Ne Yapacak:** Business Logic (iş mantığı) ve Data Processing (veri işleme) yapacak

**Görevleri:**
- ✅ Fatura bilgilerini kaydetmek (Data Storage)
- ✅ KDV hesaplamalarını yapmak (Tax Calculation)
- ✅ Para birimi çevirmelerini yapmak (Currency Conversion)
- ✅ Raporları oluşturmak (Report Generation)

**Kullanacağı Araçlar:**
- **FastAPI** - Web API framework (web servis çerçevesi)
- **SQLite** - Database (veritabanı)

**Basit Açıklama:** "User'ın yaptığı işlemleri işleyip response döndürecek (API)"

---

### 📋 **Project Manager (Proje Yöneticisi)**
**Ne Yapacak:** Project Coordination (proje koordinasyonu) ve Quality Control (kalite kontrol) yapacak

**Görevleri:**
- ✅ Herkesin görevini yapıp yapmadığını kontrol etmek (Task Management)
- ✅ Sorunları çözmek (Problem Solving)
- ✅ Müşteri ile iletişim kurmak (Client Communication)
- ✅ Testleri yapmak (Testing & QA)

**Basit Açıklama:** "Projenin patronu - her şeyin yolunda gittiğinden emin olacak (Project Lead)"

## 🔄 Veri Nasıl Akıyor?

Kullanıcı bir fatura girdiğinde ne oluyor? Adım adım görelim:

```
1️⃣ KULLANICI FATURA GİRİYOR
   👤 Kullanıcı: "Yeni fatura ekleyeyim"
   📱 Arayüz: "Tamam, formu açıyorum"

2️⃣ BİLGİLER ARAYÜZDEN MOTORA GİDİYOR
   📱 Arayüz: "İşte fatura bilgileri: Müşteri: ABC Şirketi, Tutar: 1000 TL"
   ⚙️ Motor: "Anladım, hesaplayalım"

3️⃣ MOTOR HESAPLAMALARI YAPIYOR
   🧮 Motor: "KDV %18 = 180 TL, Toplam = 1180 TL"
   💱 Motor: "Para birimi: TL ✓"
   💾 Motor: "Veritabanına kaydediyorum"

4️⃣ SONUÇ KULLANICIYA DÖNÜYOR
   ⚙️ Motor: "İşlem tamam! Fatura kaydedildi"
   📱 Arayüz: "Başarılı! Fatura eklendi ✅"
   👤 Kullanıcı: "Harika!"

5️⃣ VERİ GÜVENLİ ŞEKİLDE SAKLANIYOR
   📁 Veri Deposu: "Fatura bilgileri güvenle saklandı"
```

## 🏗️ System Layers (Sistem Katmanları)

### 🎨 **Layer 1: User Interface (Frontend)**
**Ne İşe Yarar:** User'ın sistemle konuştuğu yer (Client-side)

**İçinde Neler Var:**
```
📱 MAIN WINDOW
├── 🏠 Navigation Menu (Fatura, Rapor, Ayarlar)
├── 📝 Invoice Entry Form
├── 📊 Report View Screen
├── ⚙️ Currency Settings
└── 💾 Export Button

📋 INVOICE FORM
├── 📝 Invoice Number (input field)
├── 👤 Customer Name (input field)
├── 💰 Amount (input field)
├── 💱 Currency (dropdown: TL/USD/EUR)
├── 📅 Date (date picker)
└── ✅ Save Button (click event)
```

**Kim Yapar:** Frontend Developer (UI Developer)
**Nasıl Yapar:** PyQt6 ile ekranları tasarlayıp kodlar (GUI Development)

---

### ⚙️ **Layer 2: Business Logic (Backend)**
**Ne İşe Yarar:** Tüm calculations ve business rules yapan akıllı sistem (Server-side)

**İçinde Neler Var:**
```
🧮 BUSINESS LOGIC ENGINE
├── 💰 Tax Calculator (Amount × 18%)
├── 💱 Currency Converter (TL ↔ USD ↔ EUR)
├── 📊 Report Generator (Monthly/Yearly)
└── 💾 Data Manager (CRUD Operations)

🔄 PROCESSING FLOW
1. Receive Data (from UI)
2. Calculate (tax, total, convert)
3. Save (to Database)
4. Return Response (to UI)
```

**Kim Yapar:** Backend Developer (Server-side Developer)
**Nasıl Yapar:** FastAPI ile API endpoints yazar (REST API)

---

### 📁 **Layer 3: Database (Veri Deposu)**
**Ne İşe Yarar:** Tüm data'nın güvenle saklandığı yer (Data Persistence)

**İçinde Neler Var:**
```
📁 DATABASE (SQLite)
├── 📋 Invoices Table
│   ├── invoice_no, customer, amount, date
│   └── tax, total, currency
├── 💰 Currencies Table
│   ├── TL, USD, EUR rates
│   └── current exchange rates
└── 📊 Reports Table
    ├── generated reports
    └── report history
```

**Kim Yapar:** Backend Developer (database schema tasarlar)
**Nasıl Yapar:** SQLite ile tables oluşturur (Database Design)

## 🔧 Development Tools (Geliştirme Araçları)

### **Frontend Development Tools:**
```
🛠️ PYQT6 (Desktop UI Framework)
├── Ne İşe Yarar: Desktop applications yapmak (GUI)
├── Neden Bu: Cross-platform, powerful, free
├── Örnek: Windows Calculator gibi
└── Öğrenmesi: 1-2 hafta

📚 LEARNING RESOURCES:
├── YouTube: "PyQt6 Tutorial" (English)
├── Documentation: https://doc.qt.io/qtforpython/
├── Stack Overflow: "PyQt6" tag
└── GitHub: "PyQt6 examples" search
```

### **Backend Development Tools:**
```
🛠️ FASTAPI (Web API Framework)
├── Ne İşe Yarar: REST API endpoints yapmak
├── Neden Bu: Fast, modern, auto-documentation
├── Örnek: Restaurant kitchen gibi (customer görmez ama works)
└── Öğrenmesi: 1-2 hafta

🛠️ SQLITE (Database Engine)
├── Ne İşe Yarar: Data persistence, CRUD operations
├── Neden Bu: Lightweight, file-based, no setup
├── Örnek: Excel file gibi ama daha powerful
└── Öğrenmesi: 1 hafta

📚 LEARNING RESOURCES:
├── YouTube: "FastAPI Tutorial" (English)
├── Documentation: https://fastapi.tiangolo.com/
├── SQLite Docs: https://www.sqlite.org/docs.html
└── Stack Overflow: "FastAPI" + "SQLite" tags
```

## 📋 Weekly Task Distribution (Haftalık Görev Dağılımı)

### **WEEK 1: Basic Setup (Temel Kurulum)**
```
🎨 Frontend Developer (UI Developer):
├── ✅ Main window setup (Window Creation)
├── ✅ Basic menu design (Menu Design)
└── ✅ "Hello World" screen (UI Testing)

⚙️ Backend Developer (Server-side Developer):
├── ✅ Basic calculation engine (Business Logic)
├── ✅ "2+2=4" calculation test (Unit Testing)
└── ✅ Database setup (Data Layer)

📋 Project Manager:
├── ✅ Task tracking (Task Management)
├── ✅ Problem solving (Issue Resolution)
└── ✅ Week 1 report (Progress Reporting)
```

### **WEEK 2: Invoice Operations (Fatura İşlemleri)**
```
🎨 Frontend Developer (UI Developer):
├── ✅ Invoice entry screen (Form Development)
├── ✅ Invoice list screen (Data Display)
└── ✅ Basic buttons (UI Components)

⚙️ Backend Developer (Server-side Developer):
├── ✅ Invoice saving (Data Persistence)
├── ✅ Invoice listing (Data Retrieval)
└── ✅ Tax calculation (Business Logic)

📋 Project Manager:
├── ✅ Testing (QA Testing)
├── ✅ Bug finding (Bug Tracking)
└── ✅ Fixes implementation (Bug Resolution)
```

### **WEEK 3: MVP Completion (MVP Tamamlama)**
```
🎨 Frontend Developer (UI Developer):
├── ✅ Currency selection (UI Components)
├── ✅ Excel export button (Export Feature)
└── ✅ Final touches (UI Polish)

⚙️ Backend Developer (Server-side Developer):
├── ✅ Currency conversion (Business Logic)
├── ✅ Excel export (Export Service)
└── ✅ Final optimizations (Performance Tuning)

📋 Project Manager:
├── ✅ MVP testing (Final Testing)
├── ✅ Client demo preparation (Demo Preparation)
└── ✅ 🚀 MVP TESLİMİ
```

## 🔄 Data Flow Examples (Veri Akışı Örnekleri)

### **Example 1: Invoice Creation (Fatura Ekleme)**
```
👤 USER: "I want to add new invoice"
    ↓
📱 UI: Opens invoice form (Form Display)
    ↓
👤 USER: Enters data (Customer: ABC, Amount: 1000 TL)
    ↓
📱 UI: Clicks "Save" button (User Action)
    ↓
⚙️ BACKEND: Receives data (API Call)
    ↓
🧮 BACKEND: Calculates tax (1000 × 0.18 = 180 TL) (Business Logic)
    ↓
🧮 BACKEND: Calculates total (1000 + 180 = 1180 TL) (Calculation)
    ↓
💾 BACKEND: Saves to database (Data Persistence)
    ↓
📁 DATABASE: "Invoice saved" (Data Storage)
    ↓
⚙️ BACKEND: Returns "Success" message (API Response)
    ↓
📱 UI: Shows "Invoice added!" message (User Feedback)
    ↓
👤 USER: "Great!" (User Experience)
```

### **Example 2: Report Generation (Rapor Oluşturma)**
```
👤 USER: "I want to see this month's report"
    ↓
📱 UI: "Which month?" asks (User Input)
    ↓
👤 USER: Selects "January 2024" (Data Selection)
    ↓
📱 UI: Clicks "Generate Report" button (User Action)
    ↓
⚙️ BACKEND: Searches January 2024 invoices (Data Query)
    ↓
📁 DATABASE: "Here are January invoices" (Data Retrieval)
    ↓
🧮 BACKEND: Calculates totals (income, expense, tax) (Business Logic)
    ↓
📊 BACKEND: Prepares report (Report Generation)
    ↓
⚙️ BACKEND: Returns report (API Response)
    ↓
📱 UI: Shows report in nice table (Data Visualization)
    ↓
👤 USER: "Very nice report!" (User Satisfaction)
```

## 🎯 MVP Features (MVP Özellikleri)

### **✅ Included in MVP (MVP'de Olacaklar):**
```
📋 CORE FEATURES (Temel Özellikler):
├── ✅ Invoice CRUD operations (Create, Read, Update, Delete)
├── ✅ Invoice list display (Data Display)
├── ✅ Tax calculation (18%) (Business Logic)
├── ✅ Currency selection (TL, USD, EUR) (Multi-currency)
├── ✅ Manual exchange rate entry (Data Input)
├── ✅ Monthly invoice summary (Report Generation)
├── ✅ Excel export functionality (Export Feature)
└── ✅ Basic search/filtering (Data Filtering)
```

### **❌ Not in MVP (V2.0'da olacak):**
```
🚫 ADVANCED FEATURES (Gelişmiş Özellikler):
├── ❌ Auto exchange rate updates (API Integration)
├── ❌ PDF report generation (Advanced Reporting)
├── ❌ Charts and visualizations (Data Visualization)
├── ❌ Corporate tax calculation (Advanced Tax)
├── ❌ User authentication/encryption (Security)
└── ❌ Multi-user support (User Management)
```

## 🚨 Önemli Notlar (Yeni Başlayanlar İçin)

### **✅ Yapılması Gerekenler:**
```
📚 ÖĞRENME:
├── ✅ Her hafta yeni şeyler öğrenmeye hazır olun
├── ✅ Hata yapmaktan korkmayın (öğrenmenin parçası)
├── ✅ Soru sormaktan çekinmeyin
└── ✅ Dokümantasyonları okuyun

🤝 EKİP ÇALIŞMASI:
├── ✅ Her gün kısa toplantı yapın
├── ✅ Sorunları hemen paylaşın
├── ✅ Birbirinize yardım edin
└── ✅ Pozitif kalın
```

### **❌ Yapılmaması Gerekenler:**
```
🚫 OVERCOMPLICATING (Karmaşıklaştırma):
├── ❌ Don't try to do everything at once (Scope Management)
├── ❌ Don't try to be perfect (MVP is enough)
├── ❌ Don't work alone (Team Collaboration)
└── ❌ Don't hide problems (Transparency)
```

## 🎉 Success Tips (Başarı İpuçları)

### **For Frontend Developer (UI Developer):**
```
💡 TIPS (İpuçları):
├── 💡 Start with simple screens first (UI Development)
├── 💡 Make user-friendly design (UX Design)
├── 💡 Show clearly what each button does (UI Clarity)
└── 💡 Write understandable error messages (Error Handling)
```

### **For Backend Developer (Server-side Developer):**
```
💡 TIPS (İpuçları):
├── 💡 Start with simple calculations first (Business Logic)
├── 💡 Test each operation step by step (Unit Testing)
├── 💡 Be careful to prevent data loss (Data Safety)
└── 💡 Double-check calculations (Data Validation)
```

### **For Project Manager:**
```
💡 TIPS (İpuçları):
├── 💡 Track progress daily (Progress Monitoring)
├── 💡 Detect problems early (Issue Management)
├── 💡 Motivate the team (Team Leadership)
└── 💡 Stay in constant communication with client (Client Management)
```

## 📞 Help & Support (Yardım ve Destek)

### **When You Have Problems (Sorun Yaşadığınızda):**
```
🆘 GETTING HELP (Yardım Alma):
├── 🆘 Ask your team member first (Team Communication)
├── 🆘 Search on Google (English resources)
├── 🆘 Watch YouTube tutorials (Video Learning)
└── 🆘 Ask questions on Stack Overflow (Community Help)
```

### **Learning Resources (Öğrenme Kaynakları):**
```
📚 RESOURCES (Kaynaklar):
├── 📚 Python Basics: https://www.w3schools.com/python/
├── 📚 PyQt6 Tutorials: https://doc.qt.io/qtforpython/
├── 📚 FastAPI Docs: https://fastapi.tiangolo.com/tutorial/
├── 📚 SQLite Documentation: https://www.sqlite.org/docs.html
├── 📚 Stack Overflow: "Python", "PyQt6", "FastAPI" tags
└── 📚 GitHub: Search "PyQt6 examples", "FastAPI examples"
```

---

**🎯 Conclusion (Sonuç):** Bu dokümantasyon, sistemin nasıl çalıştığını basit terimlerle açıklıyor. Don't overcomplicate things, proceed step by step, and never hesitate to ask questions. Good luck! 🚀
