# fromqr.py
# -*- coding: utf-8 -*-
"""
OPTIMIZE EDİLMİŞ QR İŞLEME SİSTEMİ
- 3 Aşamalı Akıllı Tarama (Hızlı → Orta → Derin)
- Otomatik Fatura Tipi Tespiti (SATIS/ALIS)
- Performans ve Doğruluk Dengesi
"""

from imports import *


class OptimizedQRProcessor:
    """PERFORMANS-DOĞRULUK DENGELİ QR İŞLEMCİSİ"""
    
    def __init__(self):
        self.opencv_detector = None
        self.tools_loaded = False
        self.stats = {
            'smart_dpi_300': 0,    # Yüksek kalite dosyalar
            'smart_dpi_450': 0,    # Orta kalite dosyalar  
            'smart_dpi_600': 0,    # Düşük kalite dosyalar
            'fallback_scan': 0,    # Son çare tam tarama
            'stage1_fast': 0,      # Resim işleme - hızlı tarama
            'stage2_medium': 0,    # Resim işleme - orta tarama
            'stage3_deep': 0,      # Resim işleme - derin tarama
            'failed': 0
        }
        # Dosya kalite cache (aynı dosya tekrar işlenirse hızlı olsun)
        self.file_quality_cache = {}
    
    def _extract_fatura_no_from_filename(self, filename):
        """
        Dosya adından CR ile başlayan fatura numarasını çıkar.
        Örnek: 'CRA2025000000081 ATLAS MADEN AŞ İŞCİLİK.pdf' -> 'CRA2025000000081'
        """
        # Dosya adından uzantıyı çıkar
        name_without_ext = os.path.splitext(filename)[0]
        
        # CR ile başlayan ve ardından harf+sayı kombinasyonu olan pattern
        # CRA, CRB, CR1, vs. ve ardından sayılar
        pattern = r'^(CR[A-Z0-9]?\d+)'
        match = re.match(pattern, name_without_ext)
        
        if match:
            return match.group(1)
        
        # Alternatif: dosya adı içinde CR pattern ara
        pattern_anywhere = r'(CR[A-Z0-9]?\d+)'
        match = re.search(pattern_anywhere, name_without_ext)
        
        if match:
            return match.group(1)
        
        return None
    
    def _init_qr_tools(self):
        """QR araçlarını lazy loading ile yükle"""
        if self.tools_loaded:
            return
        
        try:
            cv2.setNumThreads(6)
            cv2.setUseOptimized(True)
            self.opencv_detector = cv2.QRCodeDetector()
            self.tools_loaded = True
            logging.info("✅ QR araçları yüklendi")
        except Exception as e:
            logging.error(f"❌ QR araçları yüklenemedi: {e}")
            raise ImportError("QR kütüphaneleri eksik! pip install opencv-python-headless pyzbar PyMuPDF")
    
    def analyze_pdf_quality(self, pdf_path):
        """PDF kalitesini analiz et ve optimal DPI'yi belirle"""
        # Cache kontrolü
        if pdf_path in self.file_quality_cache:
            return self.file_quality_cache[pdf_path]
        
        try:
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            
            # Hızlı sayfa analizi (72 DPI ile)
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            
            # Sayfa boyutları (point olarak)
            page_width = page.rect.width
            page_height = page.rect.height
            page_area = page_width * page_height
            
            # Metin yoğunluğu analizi
            text_length = len(page.get_text())
            text_density = text_length / page_area if page_area > 0 else 0
            
            doc.close()
            
            # ESKİ BAŞARILI DPI STRATEJİSİ (KONSERVATIF YAKLAŞIM)
            # Çoğu E-fatura için yüksek DPI gerekiyor, düşük risk alalım
            if file_size_mb < 0.3:  # 300KB altı - Kesinlikle yüksek DPI
                optimal_dpi = 600
                quality_level = "DÜŞÜK"
            elif file_size_mb < 1.0:  # 300KB-1MB - Hala yüksek DPI 
                optimal_dpi = 550
                quality_level = "ORTA-DÜŞÜK"
            elif file_size_mb < 3.0:  # 1-3MB - Orta DPI
                optimal_dpi = 450
                quality_level = "ORTA"
            else:  # 3MB üstü - Düşük DPI yeterli
                optimal_dpi = 400
                quality_level = "YÜKSEK"
            
            # Metin yoğunluğu düzeltmesi - Daha agresif
            if text_density < 0.002:  # Az metin = muhtemelen taranmış → Yüksek DPI
                optimal_dpi = 600
                quality_level += "+TARANMIŞ"
            
            quality_info = {
                'dpi': optimal_dpi,
                'level': quality_level,
                'file_size_mb': file_size_mb,
                'text_density': text_density,
                'fallback_dpi': optimal_dpi + 150  # Başarısızsa kullanılacak
            }
            
            # Cache'e kaydet
            self.file_quality_cache[pdf_path] = quality_info
            
            logging.info(f"   📊 Dosya kalitesi: {quality_level}, DPI: {optimal_dpi}, Boyut: {file_size_mb:.1f}MB")
            return quality_info
            
        except Exception as e:
            logging.warning(f"   ⚠️ Kalite analizi başarısız: {e}")
            # Varsayılan değerler
            return {
                'dpi': 450,
                'level': 'VARSAYILAN',
                'file_size_mb': 0,
                'text_density': 0,
                'fallback_dpi': 600
            }
    
    def clean_json(self, qr_text):
        """Geliştirilmiş JSON temizleme"""
        if not qr_text or len(qr_text.strip()) < 5:
            return {}
        
        cleaned = qr_text.strip()
        
        # Kontrol karakterlerini temizle
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
        cleaned = re.sub(r'\\x[0-9a-fA-F]{2}', '', cleaned)
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
        
        # JSON parse denemeleri
        parse_attempts = [
            cleaned,
            cleaned.replace("'", '"'),
            re.sub(r'[""‚›‛′‵]', '"', cleaned),
        ]
        
        for attempt in parse_attempts:
            try:
                return json.loads(attempt)
            except:
                continue
        
        # Manuel key-value çıkarma
        try:
            kv_pairs = {}
            pattern = r'["\']?([a-zA-Z_]\w*)["\']?\s*:\s*["\']?([^,"}\]\n]+)["\']?'
            matches = re.findall(pattern, cleaned)
            
            for key, value in matches:
                value = value.strip().strip('"').strip("'")
                try:
                    kv_pairs[key] = float(value) if '.' in value and value.replace('.', '').isdigit() else value
                except:
                    kv_pairs[key] = value
            
            if kv_pairs:
                logging.info(f"✅ Manuel parse başarılı: {len(kv_pairs)} alan")
                return kv_pairs
        except:
            pass
        
        logging.warning(f"⚠️ JSON parse başarısız: {qr_text[:100]}")
        return {"_raw_data": qr_text, "_parse_error": True}
    
    # ================== AŞAMA 1: HIZLI TARAMA ==================
    
    def _stage1_fast(self, img):
        """AŞAMA 1: Hızlı tarama - Sağ üst bölge + tam resim"""
        h, w = img.shape[:2]
        
        # 1. Sağ üst bölge (E-faturaların %70'i burada)
        try:
            region = img[0:int(h*0.4), int(w*0.6):w]
            if region.size > 0:
                codes = pyzbar.decode(region)
                if codes:
                    data = self._extract_qr_data(codes[0])
                    if data:
                        return data
        except:
            pass
        
        # 2. Tam resim PyZBar
        try:
            codes = pyzbar.decode(img)
            if codes:
                data = self._extract_qr_data(codes[0])
                if data:
                    return data
        except:
            pass
        
        return None
    
    # ================== AŞAMA 2: ORTA SEVİYE ==================
    
    def _stage2_medium(self, img):
        """AŞAMA 2: Orta seviye - 3 bölge + kontrast artırma"""
        # Gri tonlama + kontrast
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        h, w = enhanced.shape[:2]
        
        # Sadece kritik sağ bölgeleri tara (E-faturaların %95'i burada)
        regions = [
            ("Sağ Üst", enhanced[0:int(h*0.4), int(w*0.65):w]),
            ("Sağ Orta", enhanced[int(h*0.25):int(h*0.75), int(w*0.70):w]),
        ]
        
        for region_name, region in regions:
            if region.size > 0:
                try:
                    codes = pyzbar.decode(region)
                    if codes:
                        data = self._extract_qr_data(codes[0])
                        if data:
                            logging.debug(f"✅ {region_name} bölgede bulundu")
                            return data
                except:
                    pass
        
        # Tam resim tarama
        try:
            codes = pyzbar.decode(enhanced)
            if codes:
                data = self._extract_qr_data(codes[0])
                if data:
                    return data
        except:
            pass
        
        return None
    
    # ================== AŞAMA 3: DERİN TARAMA ==================
    
    def _stage3_deep(self, img):
        """AŞAMA 3: Derin tarama - Çoklu görüntü işleme"""
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Çoklu işleme teknikleri
        processing_methods = [
            ("Gaussian Blur", lambda g: cv2.GaussianBlur(g, (5, 5), 0)),
            ("Adaptive Threshold", lambda g: cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
            ("Otsu Threshold", lambda g: cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            ("CLAHE Enhanced", lambda g: cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(g)),
        ]
        
        for method_name, method_func in processing_methods:
            try:
                processed = method_func(gray)
                
                # PyZBar dene
                codes = pyzbar.decode(processed)
                if codes:
                    data = self._extract_qr_data(codes[0])
                    if data:
                        logging.debug(f"✅ {method_name} ile bulundu")
                        return data
                
                # OpenCV dene
                if self.opencv_detector:
                    qr_data, _, _ = self.opencv_detector.detectAndDecode(processed)
                    if qr_data and len(qr_data.strip()) > 10:
                        logging.debug(f"✅ {method_name} + OpenCV ile bulundu")
                        return qr_data
            except:
                continue
        
        return None
    
    # ================== PDF İŞLEME - 3 DPI SEVİYESİ ==================
    
    def extract_text_from_pdf(self, pdf_path):
        """PDF'den metin çıkar - GELİŞTİRİLMİŞ TABLO ALGILAMA"""
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            
            # Standart metin çıkarma
            text = page.get_text()
            
            doc.close()
            return text
        except Exception as e:
            logging.warning(f"⚠️ PDF metin çıkarma hatası ({os.path.basename(pdf_path)}): {e}")
            return ""
    
    def extract_table_from_pdf(self, pdf_path):
        """PDF'den TABLO VERİSİNİ SÜTUN BAZLI çıkar (koordinat analizi)"""
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            
            # Tüm metin blokları (koordinat bilgili)
            blocks = page.get_text("dict")["blocks"]
            
            # Kelime bazlı çıkarma (x, y koordinatları ile)
            words = []
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                # Koordinatlar: x0, y0 = sol üst köşe
                                bbox = span["bbox"]
                                words.append({
                                    'text': text,
                                    'x': bbox[0],  # Sol kenar
                                    'y': bbox[1],  # Üst kenar
                                    'x1': bbox[2], # Sağ kenar
                                    'y1': bbox[3]  # Alt kenar
                                })
            
            doc.close()
            return words
            
        except Exception as e:
            logging.warning(f"⚠️ PDF tablo çıkarma hatası: {e}")
            return []
    
    def process_pdf(self, pdf_path):
        """PDF işleme - AKILLI DPI SEÇİMİ + metin çıkarma"""
        if not self.tools_loaded:
            self._init_qr_tools()
        
        # PDF'den metin çıkar (Firma ve Mal-Hizmet bilgisi için)
        pdf_text = self.extract_text_from_pdf(pdf_path)
        
        try:
            # AŞAMA 1: Dosya kalitesi analizi
            quality_info = self.analyze_pdf_quality(pdf_path)
            optimal_dpi = quality_info['dpi']
            fallback_dpi = quality_info['fallback_dpi']
            
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            
            # AŞAMA 2: Akıllı başlangıç DPI (ESKİ YÖNTEMİNİZLE)
            result = self._try_pdf_with_dpi(page, optimal_dpi, "AKILLI")
            if result:
                doc.close()
                if optimal_dpi <= 400:
                    self.stats['smart_dpi_300'] += 1
                elif optimal_dpi <= 500:
                    self.stats['smart_dpi_450'] += 1
                else:
                    self.stats['smart_dpi_600'] += 1
                return result, pdf_text
            
            # AŞAMA 3: ESKİ BAŞARILI ORTA SEVİYE (600 DPI)
            if optimal_dpi < 600:  # Zaten 600 DPI denemediyse
                result = self._try_pdf_with_dpi(page, 600, "ORTA")
                if result:
                    doc.close()
                    self.stats['smart_dpi_600'] += 1
                    return result, pdf_text
            
            # AŞAMA 4: ESKİ BAŞARILI YÜKSEK SEVİYE (750 DPI)
            result = self._try_pdf_with_dpi(page, 750, "YÜKSEK")
            if result:
                doc.close()
                self.stats['fallback_scan'] += 1
                return result, pdf_text
            
            doc.close()
            self.stats['failed'] += 1
            return None, pdf_text
            
        except Exception as e:
            logging.error(f"❌ PDF hatası ({os.path.basename(pdf_path)}): {e}")
            self.stats['failed'] += 1
            return None, ""
    
    def _try_pdf_with_dpi(self, page, dpi, stage_name):
        """ESKİ BAŞARILI YÖNTEMİNİZ - Belirli DPI ile PDF'den QR okumayı dene"""
        try:
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img_data = pix.tobytes("png")
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
            
            # Aşamaya göre işleme (ESKİ BAŞARILI YÖNTEMLERİNİZ)
            if stage_name == "AKILLI":
                return self._smart_region_scan(img)  # Hızlı başlangıç
            elif stage_name == "ORTA":
                return self._stage2_medium(img)  # ESKİ ORTA SEVİYE
            elif stage_name == "YÜKSEK":
                return self._stage3_deep(img)   # ESKİ YÜKSEK SEVİYE
            
        except Exception as e:
            logging.debug(f"   PDF tarama hatası ({stage_name}): {e}")
            pass
        
        return None
    
    def _smart_region_scan(self, img):
        """Sadece kritik bölgeleri tara - ESKİ BAŞARILI KOORDİNATLARLA"""
        h, w = img.shape[:2]
        
        # 1. Sağ üst bölge (ESKİ BAŞARILI KOORDİNATLAR)
        try:
            region = img[0:int(h*0.4), int(w*0.6):w]  # Eski: 0.6, Yeni: 0.65 → GERİ DÖNDÜK
            if region.size > 0:
                codes = pyzbar.decode(region)
                if codes:
                    data = self._extract_qr_data(codes[0])
                    if data:
                        logging.debug(f"   ✅ Sağ üst bölgede bulundu")
                        return data
        except:
            pass
        
        # 2. Tam resim PyZBar (ESKİ BAŞARILI YÖNTEMİNİZ)
        try:
            codes = pyzbar.decode(img)
            if codes:
                data = self._extract_qr_data(codes[0])
                if data:
                    logging.debug(f"   ✅ Tam resim taramada bulundu")
                    return data
        except:
            pass
        
        return None
    
    def _fallback_full_scan(self, img):
        """ESKİ BAŞARILI AŞAMA 2 YÖNTEMİNİZ - Kontrast artırma + bölge tarama"""
        # Gri tonlama + kontrast
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # CLAHE (ESKİ BAŞARILI AYARLARINIZ)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))  # Eski: 2.0, Yeni: 3.0 → GERİ DÖNDÜK
        enhanced = clahe.apply(gray)
        
        h, w = enhanced.shape[:2]
        
        # ESKİ BAŞARILI BÖLGE KOORDİNATLARINIZ
        regions = [
            ("Sağ Üst", enhanced[0:int(h*0.4), int(w*0.65):w]),
            ("Sağ Orta", enhanced[int(h*0.25):int(h*0.75), int(w*0.70):w]),
        ]
        
        for region_name, region in regions:
            if region.size > 0:
                try:
                    codes = pyzbar.decode(region)
                    if codes:
                        data = self._extract_qr_data(codes[0])
                        if data:
                            logging.debug(f"✅ {region_name} bölgede bulundu (fallback)")
                            return data
                except:
                    pass
        
        # Tam resim tarama (ESKİ YÖNTEMİNİZ)
        try:
            codes = pyzbar.decode(enhanced)
            if codes:
                data = self._extract_qr_data(codes[0])
                if data:
                    logging.debug(f"✅ Fallback tam taramada bulundu")
                    return data
        except:
            pass
        
        # OpenCV son deneme
        if self.opencv_detector:
            try:
                qr_data, _, _ = self.opencv_detector.detectAndDecode(enhanced)
                if qr_data and len(qr_data.strip()) > 10:
                    logging.debug(f"✅ Fallback OpenCV'de bulundu")
                    return qr_data
            except:
                pass
        
        return None
    
    # ================== RESİM İŞLEME ==================
    
    def process_image(self, image_path):
        """Resim işleme - 3 aşamalı"""
        if not self.tools_loaded:
            self._init_qr_tools()
        
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None, ""
            
            # AŞAMA 1
            result = self._stage1_fast(img)
            if result:
                self.stats['stage1_fast'] += 1
                return result, ""
            
            # AŞAMA 2
            result = self._stage2_medium(img)
            if result:
                self.stats['stage2_medium'] += 1
                return result, ""
            
            # AŞAMA 3
            result = self._stage3_deep(img)
            if result:
                self.stats['stage3_deep'] += 1
                return result, ""
            
            self.stats['failed'] += 1
            return None, ""
            
        except Exception as e:
            logging.error(f"❌ Resim hatası ({os.path.basename(image_path)}): {e}")
            self.stats['failed'] += 1
            return None, ""
    
    # ================== YARDIMCI FONKSİYONLAR ==================
    
    def _extract_qr_data(self, code):
        """PyZBar QR code objesinden veriyi çıkar"""
        try:
            data = code.data
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
            if data and len(data.strip()) > 10:
                return data
        except:
            pass
        return None
    
    def extract_info_from_text(self, pdf_text, file_name, pdf_path=None):
        """PDF metninden firma, mal-hizmet ve miktar bilgisi çıkar - GELİŞTİRİLMİŞ"""
        info = {
            'firma': None,
            'malzeme': None,
            'miktar': None
        }
        
        if not pdf_text:
            return info
        
        # ⭐ ÖNCE SÜTUN BAZLI TABLO ANALİZİ DENE ⭐
        if pdf_path:
            table_info = self._extract_from_table_structure(pdf_path)
            if table_info.get('malzeme') or table_info.get('miktar'):
                logging.info("   ✅ Sütun bazlı tablo analizinden veri alındı")
                info.update(table_info)
                # Eğer her iki bilgi de bulunduysa, firma kontrolü yap ve dön
                if info['malzeme'] and info['miktar']:
                    # Sadece firma eksikse, text parsing ile bul
                    if not info['firma']:
                        info['firma'] = self._extract_firma_from_text(pdf_text)
                    return info
        
        # ⭐ TABLO ANALİZİ BAŞARISIZ - KLASİK METİN PARSE ⭐
        lines = pdf_text.split('\n')
        
        # Firma çıkarma
        info['firma'] = self._extract_firma_from_text(pdf_text)
        
        # ========== MALZEME VE MİKTAR - KLASİK METİN PARSE ==========
        # (Sütun analizi başarısız olduğu için buraya gelindi)
        info['malzeme'] = self._extract_malzeme_classic(lines)
        info['miktar'] = self._extract_miktar_classic(lines)
        
        return info
    
    def _extract_firma_from_text(self, pdf_text):
        """PDF metninden firma adı çıkar"""
        lines = pdf_text.split('\n')
        firma = None
        
        # ========== FİRMA ADI TESPİTİ - "SAYIN" KELİMESİNİN ALTINDA ==========
        # "SAYIN" kelimesini bul (koyu yazılı olabilir, regex ile case-insensitive ara)
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # "SAYIN" kelimesini içeren satırı bul
            if re.search(r'\bSAYIN\b', line_stripped, re.IGNORECASE):
                logging.debug(f"   🔍 'SAYIN' kelimesi bulundu: {line_stripped}")
                
                # Hemen altındaki satırı firma adı olarak al
                for j in range(i+1, min(i+4, len(lines))):
                    candidate = lines[j].strip()
                    
                    # Boş satırları atla
                    if not candidate or len(candidate) < 3:
                        continue
                    
                    # Sadece sayılardan oluşan satırları atla (VKN/TCKN olabilir)
                    if re.match(r'^[\d\s\-]+$', candidate):
                        continue
                    
                    # Telefon numarası formatını atla
                    if re.match(r'^[\d\s\-\+\(\)]{10,}$', candidate):
                        continue
                    
                    # Tarih formatını atla
                    if re.match(r'\d{2}[\.\/\-]\d{2}[\.\/\-]\d{4}', candidate):
                        continue
                    
                    # E-posta adreslerini atla
                    if '@' in candidate and '.' in candidate:
                        continue
                    
                    # Geçerli firma adı bulundu
                    firma = candidate
                    logging.debug(f"   🏢 Firma adı (SAYIN altında): {candidate}")
                    break
                
                if firma:
                    break
        
        # Eğer SAYIN ile bulunamadıysa, klasik yöntemle dene
        if not firma:
            firma_keywords = [
                'alıcı unvan', 'alici unvan', 'satıcı unvan', 'satici unvan',
                'müşteri', 'musteri', 'firma adı', 'firma adi',
                'unvan', 'şirket', 'sirket', 'company name'
            ]
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                if any(keyword in line_lower for keyword in firma_keywords):
                    for j in range(i+1, min(i+5, len(lines))):
                        candidate = lines[j].strip()
                        if candidate and len(candidate) > 3:
                            if re.match(r'^\d{10,11}$', candidate):
                                continue
                            if re.match(r'^[\d\s\-\+\(\)]{10,}$', candidate):
                                continue
                            if re.match(r'\d{2}[\.\/\-]\d{2}[\.\/\-]\d{4}', candidate):
                                continue
                            
                            firma = candidate
                            logging.debug(f"   🏢 Firma adı (keyword): {candidate}")
                            break
                    if firma:
                        break
        
        return firma
    
    def _extract_from_table_structure(self, pdf_path):
        """PDF'den SÜTUN BAZLI tablo analizi ile malzeme ve miktar çıkar"""
        info = {'firma': None, 'malzeme': None, 'miktar': None}
        
        try:
            words = self.extract_table_from_pdf(pdf_path)
            if not words:
                return info
            
            logging.info(f"   🔍 {len(words)} kelime koordinatı alındı")
            
            # DEBUG: İlk 50 kelimeyi logla
            logging.info("   📋 İLK 50 KELİME (koordinatlarla):")
            for i, w in enumerate(words[:50]):
                logging.info(f"      [{i}] '{w['text']}' -> x={w['x']:.0f}, y={w['y']:.0f}")
            
            # Y koordinatına göre satırlara grupla (tolerance: 5 piksel)
            rows = self._group_words_into_rows(words, y_tolerance=5)
            
            # Başlık satırlarını bul
            malzeme_col_x = None
            miktar_col_x = None
            header_y = None
            
            logging.info("   🔎 BAŞLIK ARAMA:")
            
            for row_y, row_words in rows.items():
                row_text = ' '.join([w['text'] for w in row_words]).lower()
                
                # DEBUG: Her satırı logla
                logging.info(f"      Satır y={row_y:.0f}: {row_text[:100]}")
                
                # Malzeme/Mal Hizmet başlığı
                for word in row_words:
                    word_lower = word['text'].lower()
                    if any(keyword in word_lower for keyword in ['mal', 'hizmet', 'açıklama', 'malzeme', 'ürün']):
                        malzeme_col_x = word['x']
                        header_y = row_y
                        logging.info(f"      ✅ Malzeme sütunu başlığı: '{word['text']}' -> x={malzeme_col_x:.0f}, y={row_y:.0f}")
                        break
                
                # Miktar başlığı
                for word in row_words:
                    word_lower = word['text'].lower()
                    if any(keyword in word_lower for keyword in ['miktar', 'adet', 'qty', 'quantity']):
                        miktar_col_x = word['x']
                        if not header_y:
                            header_y = row_y
                        logging.info(f"      ✅ Miktar sütunu başlığı: '{word['text']}' -> x={miktar_col_x:.0f}, y={row_y:.0f}")
                        break
                
                if malzeme_col_x and miktar_col_x:
                    break
            
            if not header_y:
                logging.warning("   ❌ Tablo başlıkları bulunamadı")
                return info
            
            logging.info(f"   📊 Başlık bulundu: Malzeme x={malzeme_col_x}, Miktar x={miktar_col_x}, y={header_y:.0f}")
            
            # Başlık satırından sonraki satırlarda veri ara
            logging.info("   🔎 VERİ ARAMA:")
            for row_y in sorted(rows.keys()):
                if row_y <= header_y + 10:  # Başlık satırını ve hemen altını atla
                    continue
                
                row_words = rows[row_y]
                row_text = ' '.join([w['text'] for w in row_words])
                logging.info(f"      Veri satırı y={row_y:.0f}: {row_text[:80]}")
                
                # Malzeme sütunundan veri al (x koordinatı yakın olanlar)
                if malzeme_col_x and not info['malzeme']:
                    malzeme_candidates = [
                        w for w in row_words 
                        if abs(w['x'] - malzeme_col_x) < 80  # 80 piksel tolerance (artırıldı)
                        and len(w['text']) > 3
                        and not re.match(r'^[\d\s\.\,\-\%\:]+$', w['text'])
                    ]
                    
                    if malzeme_candidates:
                        cand_info = ', '.join([f"{w['text']}(x={w['x']:.0f})" for w in malzeme_candidates[:3]])
                        logging.info(f"         Malzeme adayları: {cand_info}")
                    
                    if malzeme_candidates:
                        # En yakın olanı al
                        malzeme_candidates.sort(key=lambda w: abs(w['x'] - malzeme_col_x))
                        info['malzeme'] = malzeme_candidates[0]['text']
                        logging.info(f"         ✅ Malzeme SEÇİLDİ: '{info['malzeme']}' (x={malzeme_candidates[0]['x']:.0f})")
                
                # ⭐ MİKTAR SÜTUNU - GELİŞTİRİLMİŞ ARAMA ⭐
                if miktar_col_x and not info['miktar']:
                    # YENİ STRATEJI: Miktar + Birim birleştirme
                    
                    # 1. SADECE SAYISAL değerleri bul (miktar sütunu yakını)
                    sayi_candidates = [
                        w for w in row_words 
                        if abs(w['x'] - miktar_col_x) < 80  # Miktar sütununa yakın
                        and re.match(r'^[\d\s\.\,]+$', w['text'])  # Sadece rakam/nokta/virgül
                        and len(w['text'].strip()) > 0
                        and not re.match(r'^\d{3,4}$', w['text'])  # 654, 1234 gibi kanun numaralarını ele
                    ]
                    
                    # 2. BİRİM içeren kelimeleri bul (daha geniş alan)
                    birim_candidates = [
                        w for w in row_words
                        if abs(w['x'] - miktar_col_x) < 120  # Biraz daha geniş arama
                        and self._is_valid_birim(w['text'])  # Güvenli birim kontrolü
                    ]
                    
                    # 3. KARMA kelimeler ("1 Adet", "2 KG" gibi - M2, M3 pure birimler değil!)
                    karma_candidates = [
                        w for w in row_words
                        if abs(w['x'] - miktar_col_x) < 100
                        and re.search(r'\d', w['text'])  # İçinde rakam var
                        and re.search(r'[A-Za-zÇğİŞÜçşıöü]', w['text'])  # İçinde harf var
                        and self._is_valid_birim(re.sub(r'[\d\s\.\,]+', '', w['text']).strip())  # Harf kısmı geçerli birim
                        and not re.match(r'^[A-Z]+\d+$', w['text'].upper())  # M2, M3 gibi pure birimleri çıkar
                        and not re.search(r'kanun|madde|fıkra|bent|no:|sayı', w['text'], re.IGNORECASE)  # Kanun ifadelerini ele
                    ]
                    
                    sayi_list = ', '.join([f"{w['text']}(x={w['x']:.0f})" for w in sayi_candidates])
                    birim_list = ', '.join([f"{w['text']}(x={w['x']:.0f})" for w in birim_candidates])
                    karma_list = ', '.join([f"{w['text']}(x={w['x']:.0f})" for w in karma_candidates])
                    
                    logging.info(f"         🔍 Sayı adayları: {sayi_list}")
                    logging.info(f"         🔍 Birim adayları: {birim_list}")
                    logging.info(f"         🔍 Karma adayları: {karma_list}")
                    
                    miktar_result = None
                    
                    # ÖNCELİK 1: Karma adaylar ("1 Adet" gibi - tek kelimede sayı+birim)
                    if karma_candidates:
                        # En yakınını seç
                        karma_candidates.sort(key=lambda w: abs(w['x'] - miktar_col_x))
                        selected = karma_candidates[0]
                        
                        # Sayı ve birim kısımlarını ayır
                        sayi_part = re.search(r'([\d\s\.\,]+)', selected['text'])
                        birim_part = re.sub(r'[\d\s\.\,]+', '', selected['text']).strip().upper()
                        
                        if sayi_part:
                            sayi_temiz = sayi_part.group(1).replace('.', '').replace(',', '.').replace(' ', '')
                            try:
                                float_val = float(sayi_temiz)
                                if 0 < float_val < 100000:  # Makul aralık
                                    miktar_result = f"{sayi_temiz} {birim_part}"
                                    logging.info(f"         ✅ KARMA SEÇİLDİ: {miktar_result} (orijinal: '{selected['text']}')") 
                            except:
                                pass
                    
                    # ÖNCELİK 2: Sayı + yakındaki birim birleştir (ayrı kelimeler: "54.000" + "M2")  
                    if not miktar_result and sayi_candidates and birim_candidates:
                        # Tüm sayı-birim çiftlerini değerlendirip en iyisini seç
                        best_pair = None
                        best_score = float('inf')
                        
                        for sayi_w in sayi_candidates:
                            sayi_temiz = sayi_w['text'].replace('.', '').replace(',', '.').replace(' ', '')
                            try:
                                float_val = float(sayi_temiz)
                                if float_val <= 0:  # Sıfır ve negatif sayıları atla
                                    continue
                                    
                                for birim_w in birim_candidates:
                                    x_distance = abs(birim_w['x'] - sayi_w['x'])
                                    y_distance = abs(birim_w['y'] - sayi_w['y'])
                                    miktar_col_distance = abs(sayi_w['x'] - miktar_col_x)
                                    
                                    # Skorlama: X mesafesi + Y mesafesi + miktar sütununa uzaklık
                                    total_score = x_distance + y_distance * 2 + miktar_col_distance * 0.5
                                    
                                    if x_distance < 80 and y_distance <= 15 and total_score < best_score:
                                        best_pair = (sayi_w, birim_w, total_score)
                                        best_score = total_score
                            except:
                                continue
                        
                        if best_pair:
                            sayi_w, birim_w, score = best_pair
                            sayi_temiz = sayi_w['text'].replace('.', '').replace(',', '.').replace(' ', '')
                            try:
                                float_val = float(sayi_temiz)
                                miktar_result = f"{float_val:.0f} {birim_w['text'].upper().strip()}"
                                logging.info(f"         ✅ SAYI+BİRİM SEÇİLDİ: {miktar_result} (sayı: '{sayi_w['text']}', birim: '{birim_w['text']}', skor: {score:.1f})")
                            except:
                                pass
                    
                    # ÖNCELİK 3: Eğer hiç birim yoksa, sadece en yakın sayıyı al
                    if not miktar_result and sayi_candidates:
                        sayi_candidates.sort(key=lambda w: abs(w['x'] - miktar_col_x))
                        
                        for sayi_w in sayi_candidates:
                            sayi_temiz = sayi_w['text'].replace('.', '').replace(',', '.').replace(' ', '')
                            try:
                                float_val = float(sayi_temiz)
                                if 0 < float_val < 100000:  # Makul aralık
                                    miktar_result = sayi_temiz
                                    logging.info(f"         ✅ SADECE SAYI SEÇİLDİ: {miktar_result} (orijinal: '{sayi_w['text']}')")
                                    break
                            except:
                                continue
                    
                    if miktar_result:
                        info['miktar'] = miktar_result
                
                # Her ikisi de bulunduysa dur
                if info['malzeme'] and info['miktar']:
                    break
            
            # ⭐ ALTERNATİF: Eğer miktar hala bulunamadıysa, MALZEME SATIRI ÜZERİNDE ara ⭐
            if info['malzeme'] and not info['miktar']:
                logging.info("   🔍 Miktar sütunda bulunamadı, malzeme satırı taranacak...")
                
                # Malzeme satırını bul
                for row_y in sorted(rows.keys()):
                    if row_y <= header_y + 10:
                        continue
                    
                    row_words = rows[row_y]
                    # Bu satırda malzeme var mı?
                    has_malzeme = any(w['text'] == info['malzeme'] for w in row_words)
                    
                    if has_malzeme:
                        # Aynı satırdaki TÜM sayısal değerleri bul
                        numeric_values = [
                            w for w in row_words
                            if re.match(r'^[\d\s\.\,]+$', w['text'])
                            and len(w['text'].strip()) > 0
                        ]
                        
                        if numeric_values:
                            nums_info = ', '.join([f"{w['text']}(x={w['x']:.0f})" for w in numeric_values[:5]])
                            logging.info(f"      Malzeme satırındaki sayılar: {nums_info}")
                            
                            # Malzemeden en uzak olanı al (genelde malzeme solda, miktar sağda)
                            malzeme_x = next((w['x'] for w in row_words if w['text'] == info['malzeme']), 0)
                            numeric_values.sort(key=lambda w: abs(w['x'] - malzeme_x), reverse=True)
                            
                            for num_val in numeric_values:
                                cleaned = num_val['text'].replace('.', '').replace(',', '.').replace(' ', '')
                                try:
                                    float_val = float(cleaned)
                                    # Sadece pozitif sayılar (1, 2, 3 dahil geçerli!)
                                    if float_val > 0:
                                        # ⭐ BİRİM BİLGİSİNİ BUL ⭐
                                        birim_text = self._find_birim_near_miktar(row_words, num_val, miktar_col_x if miktar_col_x else num_val['x'])
                                        if birim_text:
                                            info['miktar'] = f"{cleaned} {birim_text}"
                                        else:
                                            info['miktar'] = cleaned
                                        
                                        logging.info(f"      ✅ Miktar (malzeme satırından): {info['miktar']} (x={num_val['x']:.0f})")
                                        break
                                except:
                                    continue
                        
                        if info['miktar']:
                            break
            
            return info
            
        except Exception as e:
            logging.warning(f"   ⚠️ Tablo analizi hatası: {e}")
            return info
    
    def _is_valid_birim(self, text):
        """
        Verilen metnin geçerli bir ölçü birimi olup olmadığını kontrol eder
        
        Args:
            text: Kontrol edilecek metin
            
        Returns:
            bool: Geçerli birim ise True
        """
        if not text:
            return False
            
        text_upper = text.upper().strip()
        
        # GENİŞ BİRİM SÖZLÜĞÜ - Faturalarda sık kullanılan birimler
        valid_units = {
            # Alan/Hacim birimleri
            'M2', 'M²', 'M3', 'M³', 'CM2', 'CM²', 'CM3', 'CM³', 'MM2', 'MM²', 'MM3', 'MM³',
            'DM2', 'DM²', 'DM3', 'DM³', 'KM2', 'KM²', 'HEKTAR', 'DÖNÜM',
            
            # Ağırlık birimleri  
            'KG', 'KILO', 'KILOGRAM', 'GR', 'GRAM', 'TON', 'MG', 'MILIGRAM',
            'LB', 'POUND', 'OZ', 'OUNCE',
            
            # Hacim/Sıvı birimleri
            'LT', 'LITRE', 'ML', 'MILILITRE', 'CL', 'SANTILITRE', 'DL', 'DESILITRE',
            'GAL', 'GALON', 'BARREL', 'VARIL',
            
            # Uzunluk birimleri
            'METRE', 'MT', 'M', 'CM', 'SANTIMETRE', 'MM', 'MILIMETRE', 'KM', 'KILOMETRE',
            'INCH', 'INC', 'INÇI', 'FT', 'FOOT', 'FEET', 'YARD', 'YRD',
            
            # Adet/Sayı birimleri
            'ADET', 'AD', 'PIECE', 'PCS', 'PARÇA', 'TANE', 'DANE', 'BIRIM',
            
            # Paket birimleri
            'PAKET', 'PKT', 'KUTU', 'KT', 'KOLI', 'SANDIK', 'ÇUVAL', 'TORBA',
            'DESTE', 'TAKIM', 'SET', 'KIT', 'ÇIFT',
            
            # Zaman birimleri
            'SAAT', 'SA', 'DAKIKA', 'DK', 'SANIYE', 'SN', 'GÜN', 'HAFTA', 'AY', 'YIL',
            
            # Enerji/Elektrik birimleri
            'KWH', 'KWHL', 'MWH', 'MWHL', 'WH', 'WATT', 'KW', 'KILOWATT', 'MW', 'MEGAWATT',
            'VOLT', 'AMPER', 'AMP',
            
            # Diğer teknik birimler
            'BAR', 'PSI', 'PASCAL', 'ATM', 'ATMOSFER', 'DERECE', '°C', 'CELSIUS',
            'KALORI', 'JOULE', 'BTU'
        }
        
        # Tam eşleşme kontrolü
        if text_upper in valid_units:
            return True
            
        # Kısmi eşleşme (güvenli) - çok kısa olmamalı
        if len(text_upper) >= 2:
            for unit in valid_units:
                if unit in text_upper and len(text_upper) <= len(unit) + 3:  # Biraz ekstra tolerans
                    return True
                    
        return False
    
    def _find_birim_near_miktar(self, row_words, miktar_word, miktar_col_x):
        """
        Miktarın yakınındaki birim bilgisini bul (M2, KG, ADET, vb.)
        
        Args:
            row_words: Satırdaki tüm kelimeler
            miktar_word: Miktar kelimesi objesi (x, y, text)
            miktar_col_x: Miktar sütun başlığının x koordinatı
        
        Returns:
            Birim string (M2, KG, ADET, vb.) veya None
        """
        try:
            miktar_x = miktar_word['x']
            miktar_y = miktar_word['y']
            
            # Miktarın sağındaki (x > miktar_x) ve yakın (y ± 5px) kelimeleri bul
            nearby_words = [
                w for w in row_words
                if w['x'] > miktar_x  # Sağ tarafta
                and w['x'] < miktar_x + 100  # Fazla uzak olmasın (100px içinde)
                and abs(w['y'] - miktar_y) <= 5  # Aynı satırda
            ]
            
            # Yakından uzak sırasıyla kontrol et
            nearby_words.sort(key=lambda w: w['x'])
            
            for word in nearby_words:
                # Yeni güvenli birim kontrolü
                if self._is_valid_birim(word['text']):
                    return word['text'].upper().strip()
            
            return None
            
        except Exception as e:
            logging.debug(f"   Birim bulma hatası: {e}")
            return None
    
    def _group_words_into_rows(self, words, y_tolerance=5):
        """Kelimeleri Y koordinatına göre satırlara grupla"""
        rows = {}
        
        for word in words:
            y = word['y']
            # Yakın Y değerlerini aynı satıra grupla
            found_row = False
            for row_y in rows.keys():
                if abs(row_y - y) <= y_tolerance:
                    rows[row_y].append(word)
                    found_row = True
                    break
            
            if not found_row:
                rows[y] = [word]
        
        # Her satırdaki kelimeleri X'e göre sırala
        for row_y in rows:
            rows[row_y].sort(key=lambda w: w['x'])
        
        return rows
    
    def _extract_malzeme_classic(self, lines):
        """Klasik metin parse ile malzeme çıkar"""
        malzeme = None
        
        # ========== MALZEME ADI TESPİTİ - TABLO İÇİNDEN (SÜTUN BAZLI) ==========
        # Tablo başlık satırlarını bul
        malzeme_header_patterns = [
            r'mal\s+hizmet',  # "Mal Hizmet" (boşluklu)
            r'mal.*hizmet', 
            r'hizmet.*açıklama', 
            r'açıklama', 
            r'ürün.*ad',
            r'malzeme.*ad', 
            r'description', 
            r'item.*name', 
            r'product'
        ]
        
        table_start_idx = None
        header_line = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Tablo başlığını tespit et
            if any(re.search(pattern, line_lower) for pattern in malzeme_header_patterns):
                table_start_idx = i
                header_line = lines[i]
                logging.debug(f"   📊 Tablo başlığı bulundu (satır {i}): {line_lower}")
                break
        
        # Tablo bulunduysa, ALTINDA (sonraki satırlarda) malzeme ara
        if table_start_idx is not None:
            # Başlık satırının HEMEN ALTINDAN başla (başlık atlanır)
            # Not: Bazı faturalarda başlık ile veri arasında ayırıcı çizgi olabilir
            search_start = table_start_idx + 1
            
            # İlk boş olmayan satırı atla (genelde ayırıcı çizgi: -----)
            if search_start < len(lines):
                first_line = lines[search_start].strip()
                if re.match(r'^[\-\_\=\s]+$', first_line) or len(first_line) < 2:
                    search_start += 1
            
            # Başlıktan sonraki 30 satırı tara (tablo içeriği)
            for i in range(search_start, min(search_start + 30, len(lines))):
                candidate = lines[i].strip()
                
                # Boş satırları atla
                if not candidate or len(candidate) < 3:
                    continue
                
                # Sadece sayı/noktalama/birim içeren satırları atla
                if re.match(r'^[\d\s\.\,\-\%\:]+$', candidate):
                    continue
                
                # Sadece birim olan satırları atla (M2, KG, ADET vb.)
                if re.match(r'^[A-Z]{1,4}\d?$', candidate):
                    continue
                
                # Para birimi satırlarını atla (EUR, TL, USD vb.)
                if candidate.upper() in ['EUR', 'TL', 'USD', 'GBP', 'TRY']:
                    continue
                
                # Tarih formatını atla
                if re.match(r'\d{2}[\.\/\-]\d{2}[\.\/\-]\d{4}', candidate):
                    continue
                
                # Çok kısa satırları atla (sıra numarası olabilir)
                if len(candidate) <= 3:
                    continue
                
                # "Fiyat", "Tutar", "Vergi" gibi başlıkları atla
                if any(keyword in candidate.lower() for keyword in ['fiyat', 'tutar', 'vergi', 'kdv', 'birim']):
                    continue
                
                # Tablo bitiş göstergelerinde dur
                if any(keyword in candidate.lower() for keyword in ['toplam', 'genel', 'ara toplam', 'total']):
                    break
                
                # Geçerli malzeme adı (en az 5 karakter, harf içermeli)
                if len(candidate) >= 5 and re.search(r'[a-zA-ZğüşıöçĞÜŞİÖÇ]', candidate):
                    malzeme = candidate
                    logging.debug(f"   📦 Malzeme adı (başlık altından): {candidate}")
                    break
        
        return malzeme
    
    def _extract_miktar_classic(self, lines):
        """Klasik metin parse ile miktar çıkar"""
        miktar = None
        
        # ========== MİKTAR TESPİTİ - TABLO İÇİNDEN (SÜTUN BAZLI) ==========
        # Miktar sütun başlığını bul
        miktar_header_patterns = [
            r'\bmiktar\b', r'\badet\b', r'\bquantity\b', 
            r'\bqty\b', r'\bamount\b', r'\bmkt\b'
        ]
        
        miktar_column_idx = None
        miktar_header_line = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Miktar başlığını tespit et
            if any(re.search(pattern, line_lower) for pattern in miktar_header_patterns):
                miktar_column_idx = i
                miktar_header_line = lines[i]
                logging.debug(f"   📊 Miktar başlığı bulundu (satır {i}): {line_lower}")
                break
        
        # Miktar başlığı bulunduysa, ALTINDA (sonraki satırlarda) miktar ara
        if miktar_column_idx is not None:
            # Başlık satırının HEMEN ALTINDAN başla
            search_start = miktar_column_idx + 1
            
            # İlk boş olmayan satırı atla (genelde ayırıcı çizgi: -----)
            if search_start < len(lines):
                first_line = lines[search_start].strip()
                if re.match(r'^[\-\_\=\s]+$', first_line) or len(first_line) < 2:
                    search_start += 1
            
            # Başlıktan sonraki 20 satırı tara
            for i in range(search_start, min(search_start + 20, len(lines))):
                line_stripped = lines[i].strip()
                
                # Boş satırları atla
                if not line_stripped:
                    continue
                
                # Para birimi satırlarını atla
                if line_stripped.upper() in ['EUR', 'TL', 'USD', 'GBP', 'TRY']:
                    continue
                
                # Sadece birim olan satırları atla (M2, KG, ADET vb.)
                if re.match(r'^[A-Z]{1,4}\d?$', line_stripped):
                    continue
                
                # Sadece sayı içeren satır (miktar değeri)
                # 54.000 veya 54,000 gibi formatları yakala
                if re.match(r'^[\d\.\,\s]+$', line_stripped):
                    # Nokta ve virgülleri temizle, sayıyı normalize et
                    cleaned_number = line_stripped.replace('.', '').replace(',', '.').replace(' ', '')
                    
                    # Geçerli bir sayı mı?
                    try:
                        float_value = float(cleaned_number)
                        if float_value > 0:
                            miktar = cleaned_number
                            logging.debug(f"   🔢 Miktar (başlık altından): {cleaned_number} (orijinal: {line_stripped})")
                            break
                    except ValueError:
                        continue
        
        return miktar
        return miktar
    
    def process_file(self, file_path):
        """Tek dosya işleme - Ana giriş noktası (QR bulunamadığında da PDF tarama)"""
        try:
            file_basename = os.path.basename(file_path)
            # Dosya adından uzantıyı çıkar (fatura_no için)
            file_name_without_ext = os.path.splitext(file_basename)[0]
            
            # ⭐ FATURA NUMARASINI DOSYA ADINDAN CR PATTERNİ İLE ÇIKAR ⭐
            fatura_no_extracted = self._extract_fatura_no_from_filename(file_basename)
            # CR pattern bulunamazsa tüm dosya adını kullan
            fatura_no_from_filename = fatura_no_extracted if fatura_no_extracted else file_name_without_ext
            
            # Dosya tipine göre işleme
            if file_path.lower().endswith('.pdf'):
                qr_data, pdf_text = self.process_pdf(file_path)
            else:
                qr_data, pdf_text = self.process_image(file_path)
            
            # PDF metninden ek bilgiler çıkar (her durumda) - SÜTUN BAZLI ANALİZ
            extracted_info = self.extract_info_from_text(pdf_text, file_name_without_ext, pdf_path=file_path)
            
            # ⭐ QR KOD BULUNDU ⭐
            if qr_data:
                json_data = self.clean_json(qr_data)
                
                if json_data and not json_data.get('_parse_error'):
                    return {
                        'dosya_adi': file_basename,
                        'dosya_yolu': file_path,
                        'fatura_no_from_filename': fatura_no_from_filename,
                        'durum': 'BAŞARILI',
                        'json_data': json_data,
                        'extracted_info': extracted_info
                    }
                else:
                    return {
                        'dosya_adi': file_basename,
                        'dosya_yolu': file_path,
                        'fatura_no_from_filename': fatura_no_from_filename,
                        'durum': 'JSON HATASI',
                        'json_data': json_data,
                        'extracted_info': extracted_info
                    }
            
            # ⭐ QR KOD BULUNAMADI - GELİŞMİŞ PDF METİN TARAMA DEVREDE ⭐
            logging.info(f"   🔍 QR bulunamadı, PDF metin taraması devrede: {file_basename}")
            
            # PDF'den tüm bilgileri çıkar
            if pdf_text:
                # Tarih
                tarih = self._extract_date_from_text(pdf_text)
                
                # Fatura No - CR pattern'den alındıysa onu kullan
                fatura_no = fatura_no_from_filename
                
                # Tutarlar (toplam, matrah, KDV)
                amounts = self._extract_amount_from_text(pdf_text)
                
                # Firma, malzeme, miktar (extracted_info'dan)
                firma = extracted_info.get('firma')
                malzeme = extracted_info.get('malzeme')
                miktar = extracted_info.get('miktar')
                
                # En az firma bilgisi olmalı
                if firma or amounts['toplam'] > 0:
                    # Gelişmiş JSON oluştur
                    fallback_json = {
                        'faturaNo': fatura_no,
                        'invoiceDate': tarih,
                        'firma': firma or 'Bilinmeyen Firma',
                        'tip': malzeme or 'Fatura',
                        'miktar': miktar or '',
                        'payableAmount': amounts['toplam'],
                        'taxableAmount': amounts['matrah'],
                        'hesaplanankdv': amounts['kdv'],
                        'kdvOrani': amounts['kdv_yuzdesi'],
                        'currency': 'TRY',
                        '_source': 'PDF_TEXT_EXTRACTION'
                    }
                    
                    logging.info(f"   ✅ PDF'den bilgi çıkarıldı:")
                    logging.info(f"      - Firma: {firma or 'Yok'}")
                    logging.info(f"      - Fatura No: {fatura_no}")
                    logging.info(f"      - Tarih: {tarih}")
                    logging.info(f"      - Toplam: {amounts['toplam']}")
                    logging.info(f"      - Matrah: {amounts['matrah']}")
                    logging.info(f"      - KDV: {amounts['kdv']} ({amounts['kdv_yuzdesi']}%)")
                    
                    return {
                        'dosya_adi': file_basename,
                        'dosya_yolu': file_path,
                        'fatura_no_from_filename': fatura_no_from_filename,
                        'durum': 'BAŞARILI',
                        'json_data': fallback_json,
                        'extracted_info': extracted_info
                    }
                else:
                    logging.warning(f"   ⚠️ PDF'den yeterli bilgi çıkarılamadı (firma veya tutar yok)")
            
            # Hiçbir bilgi çıkarılamadı
            return {
                'dosya_adi': file_basename,
                'dosya_yolu': file_path,
                'fatura_no_from_filename': fatura_no_from_filename,
                'durum': 'QR BULUNAMADI',
                'json_data': {},
                'extracted_info': extracted_info
            }
            
        except Exception as e:
            logging.error(f"[ERROR] Dosya isleme hatasi ({file_path}): {e}")
            # Exception durumunda da CR pattern'i kullanmaya çalış
            file_basename = os.path.basename(file_path)
            fatura_no_extracted = self._extract_fatura_no_from_filename(file_basename)
            fatura_no_from_filename = fatura_no_extracted if fatura_no_extracted else os.path.splitext(file_basename)[0]
            return {
                'dosya_adi': file_basename,
                'dosya_yolu': file_path,
                'fatura_no_from_filename': fatura_no_from_filename,
                'durum': 'KRİTİK HATA',
                'json_data': {},
                'extracted_info': {'firma': None, 'malzeme': None, 'miktar': None},
                'hata': str(e)
            }
    
    def _extract_date_from_text(self, pdf_text):
        """PDF metninden tarih çıkar - Gelişmiş"""
        if not pdf_text:
            return datetime.now().strftime("%d.%m.%Y")
        
        lines = pdf_text.split('\n')
        
        # Fatura tarihi anahtar kelimeleri
        date_keywords = [
            r'fatura\s*tarih[i]?',
            r'tarih',
            r'date',
            r'düzenlenme\s*tarih[i]?',
            r'belge\s*tarih[i]?'
        ]
        
        # Tarih formatları
        date_patterns = [
            r'(\d{2})[./-](\d{2})[./-](\d{4})',
            r'(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+(\d{4})'
        ]
        
        # Önce anahtar kelimelerin yakınında ara
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(re.search(keyword, line_lower) for keyword in date_keywords):
                # Bu satır ve sonraki 3 satırda tarih ara
                for j in range(i, min(i+4, len(lines))):
                    for pattern in date_patterns:
                        match = re.search(pattern, lines[j])
                        if match:
                            if len(match.groups()) == 3 and match.group(1).isdigit():
                                date_str = f"{match.group(1).zfill(2)}.{match.group(2).zfill(2)}.{match.group(3)}"
                                logging.debug(f"   Tarih bulundu: {date_str}")
                                return date_str
        
        # Genel tarama
        for pattern in date_patterns:
            match = re.search(pattern, pdf_text)
            if match:
                if len(match.groups()) == 3 and match.group(1).isdigit():
                    date_str = f"{match.group(1).zfill(2)}.{match.group(2).zfill(2)}.{match.group(3)}"
                    logging.debug(f"   Tarih bulundu (genel): {date_str}")
                    return date_str
        
        # Bulunamadıysa bugünün tarihi
        logging.warning(f"   PDF'de tarih bulunamadi, bugun kullanilacak")
        return datetime.now().strftime("%d.%m.%Y")
    
    def _extract_invoice_number_from_text(self, pdf_text):
        """PDF metninden fatura numarası çıkar"""
        if not pdf_text:
            return None
        
        lines = pdf_text.split('\n')
        
        # Fatura no anahtar kelimeleri
        invoice_keywords = [
            r'fatura\s*no',
            r'fatura\s*numaras[ıi]',
            r'invoice\s*number',
            r'belge\s*no',
            r'seri\s*no'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in invoice_keywords:
                if re.search(keyword, line_lower):
                    # Bu satırda veya sonraki 2 satırda fatura no ara
                    for j in range(i, min(i+3, len(lines))):
                        # Fatura no pattern: Harfler ve sayılar
                        invoice_match = re.search(r'([A-Z]{3}\d{12,}|[A-Z0-9]{10,})', lines[j])
                        if invoice_match:
                            invoice_no = invoice_match.group(1)
                            logging.debug(f"   Fatura No: {invoice_no}")
                            return invoice_no
        
        return None
    
    def _extract_amount_from_text(self, pdf_text):
        """PDF metninden tutar çıkar - Gelişmiş (Toplam, Matrah, KDV)"""
        if not pdf_text:
            return {'toplam': 0.0, 'matrah': 0.0, 'kdv': 0.0, 'kdv_yuzdesi': 0.0}
        
        lines = pdf_text.split('\n')
        amounts = {
            'toplam': 0.0,
            'matrah': 0.0,
            'kdv': 0.0,
            'kdv_yuzdesi': 0.0
        }
        
        # TOPLAM TUTAR (Ödenecek, Genel Toplam)
        toplam_keywords = [
            r'ödenecek\s*tutar',
            r'genel\s*toplam',
            r'toplam\s*tutar',
            r'vergiler\s*dahil\s*toplam',
            r'total\s*amount',
            r'payable\s*amount'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in toplam_keywords:
                if re.search(keyword, line_lower):
                    for j in range(i, min(i+3, len(lines))):
                        amount_match = re.search(r'([\d.,]+)\s*(?:TL|₺|EUR|USD)?', lines[j])
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                amount = float(amount_str)
                                if amount > 10:
                                    amounts['toplam'] = amount
                                    logging.debug(f"   Toplam tutar: {amount}")
                                    break
                            except:
                                continue
                    if amounts['toplam'] > 0:
                        break
            if amounts['toplam'] > 0:
                break
        
        # MATRAH (KDV Matrahı)
        matrah_keywords = [
            r'kdv\s*matrah[ıi]?',
            r'matrah',
            r'mal\s*hizmet\s*toplam',
            r'vergiden\s*önceki\s*toplam',
            r'net\s*tutar'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in matrah_keywords:
                if re.search(keyword, line_lower):
                    for j in range(i, min(i+3, len(lines))):
                        amount_match = re.search(r'([\d.,]+)\s*(?:TL|₺|EUR|USD)?', lines[j])
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                amount = float(amount_str)
                                if amount > 0:
                                    amounts['matrah'] = amount
                                    logging.debug(f"   Matrah: {amount}")
                                    break
                            except:
                                continue
                    if amounts['matrah'] > 0:
                        break
            if amounts['matrah'] > 0:
                break
        
        # KDV TUTARI
        kdv_keywords = [
            r'hesaplanan\s*kdv',
            r'kdv\s*tutar[ıi]?',
            r'kdv\s*toplam[ıi]?',
            r'vergi\s*tutar[ıi]?',
            r'tax\s*amount'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in kdv_keywords:
                if re.search(keyword, line_lower):
                    for j in range(i, min(i+3, len(lines))):
                        amount_match = re.search(r'([\d.,]+)\s*(?:TL|₺|EUR|USD)?', lines[j])
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                amount = float(amount_str)
                                if amount > 0:
                                    amounts['kdv'] = amount
                                    logging.debug(f"   KDV tutari: {amount}")
                                    break
                            except:
                                continue
                    if amounts['kdv'] > 0:
                        break
            if amounts['kdv'] > 0:
                break
        
        # KDV YÜZDESİ
        kdv_percent_match = re.search(r'%\s*(\d+)', pdf_text)
        if kdv_percent_match:
            amounts['kdv_yuzdesi'] = float(kdv_percent_match.group(1))
            logging.debug(f"   KDV %: {amounts['kdv_yuzdesi']}")
        elif amounts['matrah'] > 0 and amounts['kdv'] > 0:
            amounts['kdv_yuzdesi'] = round((amounts['kdv'] / amounts['matrah']) * 100, 2)
            logging.debug(f"   KDV % (hesaplanan): {amounts['kdv_yuzdesi']}")
        
        # Tutarları doğrula ve düzelt
        if amounts['toplam'] == 0 and amounts['matrah'] > 0 and amounts['kdv'] > 0:
            amounts['toplam'] = amounts['matrah'] + amounts['kdv']
            logging.debug(f"   Toplam hesaplandi: {amounts['toplam']}")
        
        if amounts['matrah'] == 0 and amounts['toplam'] > 0 and amounts['kdv'] > 0:
            amounts['matrah'] = amounts['toplam'] - amounts['kdv']
            logging.debug(f"   Matrah hesaplandi: {amounts['matrah']}")
        
        return amounts

    def process_qr_files_in_folder(self, folder_path, max_workers=6, status_callback=None):
        """Klasördeki tüm dosyaları paralel işle"""
        if not self.tools_loaded:
            self._init_qr_tools()
        
        logging.info(f"🚀 QR klasör işleme başlıyor: {folder_path}")
        
        if status_callback:
            status_callback("📁 Dosyalar taranıyor...", 5)
        
        # Dosyaları topla
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp'}
        file_paths = []
        
        try:
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file_name)
                    if ext.lower() in allowed_extensions:
                        file_paths.append(file_path)
        except Exception as e:
            logging.error(f"❌ Klasör okuma hatası: {e}")
            return []
        
        if not file_paths:
            logging.warning("⚠️ İşlenebilir dosya bulunamadı")
            return []
        
        logging.info(f"📁 {len(file_paths)} dosya bulundu, {max_workers} thread kullanılacak")
        
        results = []
        completed_count = 0
        start_time = time.time()
        
        # Paralel işleme
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {executor.submit(self.process_file, path): path for path in file_paths}
            
            for future in as_completed(future_to_path):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                    completed_count += 1
                    
                    # İlerleme bildirimi - Her dosyada güncelle
                    if status_callback:
                        progress = int((completed_count / len(file_paths)) * 95)
                        elapsed = time.time() - start_time
                        rate = completed_count / elapsed if elapsed > 0 else 0
                        
                        # Yüzdelik gösterim ekle
                        msg = f"İşleniyor: %{progress} ({completed_count}/{len(file_paths)})"
                        
                        if not status_callback(msg, progress):
                            # İptal edildi
                            logging.warning("⚠️ Kullanıcı işlemi iptal etti")
                            break
                    
                except Exception as e:
                    file_path = future_to_path[future]
                    logging.error(f"❌ Timeout/Hata: {os.path.basename(file_path)}")
                    results.append({
                        'dosya_adi': os.path.basename(file_path),
                        'durum': 'TIMEOUT',
                        'json_data': {}
                    })
                    completed_count += 1
        
        total_time = time.time() - start_time
        success_count = len([r for r in results if r.get('durum') == 'BAŞARILI'])
        
        # Başarısız dosyaları taşı
        # Kullanıcı isteği: exe veya frontend.py'nin bulunduğu dizine taşı (CWD)
        failed_dir = os.path.join(os.getcwd(), "BasarisizQRlar")
        
        for result in results:
            if result.get('durum') != 'BAŞARILI':
                try:
                    if not os.path.exists(failed_dir):
                        os.makedirs(failed_dir)
                        
                    source_path = result.get('dosya_yolu')
                    file_name = result.get('dosya_adi')
                    
                    if source_path and os.path.exists(source_path):
                        dest_path = os.path.join(failed_dir, file_name)
                        
                        # Eğer hedefte dosya varsa üzerine yazmamak için ismini değiştir
                        if os.path.exists(dest_path):
                            base, ext = os.path.splitext(file_name)
                            timestamp = int(time.time())
                            dest_path = os.path.join(failed_dir, f"{base}_{timestamp}{ext}")
                            
                        shutil.move(source_path, dest_path)
                        logging.info(f"   📦 Başarısız dosya taşındı: {file_name} -> BasarisizQRlar")
                        
                        # Sonuçtaki yolu güncelle
                        result['dosya_yolu'] = dest_path
                        result['tasindi'] = True
                except Exception as e:
                    logging.error(f"   ❌ Dosya taşıma hatası ({result.get('dosya_adi')}): {e}")
        
        # İstatistikler
        logging.info(f"🏁 QR işleme bitti!")
        logging.info(f"📊 Başarılı: {success_count}/{len(results)} (%{(success_count/len(results)*100):.0f})")
        logging.info(f"⏱️  Süre: {total_time:.1f}s, Hız: {len(results)/total_time:.1f} dosya/s")
        logging.info(f"📈 Akıllı DPI İstatistikleri:")
        logging.info(f"   • Yüksek Kalite (300 DPI): {self.stats['smart_dpi_300']}")
        logging.info(f"   • Orta Kalite (450 DPI): {self.stats['smart_dpi_450']}")
        logging.info(f"   • Düşük Kalite (600 DPI): {self.stats['smart_dpi_600']}")
        logging.info(f"   • Fallback Tarama: {self.stats['fallback_scan']}")
        logging.info(f"   • Başarısız: {self.stats['failed']}")
        
        if status_callback:
            status_callback("✅ QR işleme tamamlandı!", 100)
        
        return results


# ============================================================================
# QRInvoiceIntegrator - Backend Entegrasyonu + Otomatik Tip Tespiti
# ============================================================================

class QRInvoiceIntegrator:
    """
    QR İŞLEME VE BACKEND ENTEGRASYONU
    - Otomatik fatura tipi tespiti (SATIS/ALIS)
    - Backend ile senkronizasyon
    """
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.qr_processor = OptimizedQRProcessor()
        logging.info("🔗 QRInvoiceIntegrator başlatıldı (optimize edilmiş)")
    
    def process_qr_files_in_folder(self, folder_path, max_workers=6, status_callback=None):
        """Klasördeki dosyaları işle"""
        return self.qr_processor.process_qr_files_in_folder(
            folder_path, 
            max_workers=max_workers,
            status_callback=status_callback
        )
    
    def add_invoices_from_qr_data(self, qr_results, invoice_type):
        """
        QR sonuçlarını veritabanına ekle - MANUEL TİP SEÇİMİ + DUPLICATE KONTROL
        
        Args:
            qr_results: QR işleme sonuçları
            invoice_type: 'outgoing' (gelir) veya 'incoming' (gider) - KULLANICI SEÇİMİ
        
        Returns:
            dict: {
                'success': True,
                'added': int,
                'failed': int,
                'skipped_duplicates': int,
                'total': int,
                'invoice_type': str,
                'processing_details': list,
                'failed_files': list
            }
        """
        if not qr_results:
            logging.warning("QR sonuçları boş!")
            return {
                'success': False,
                'added': 0,
                'failed': 0,
                'skipped_duplicates': 0,
                'total': 0,
                'invoice_type': invoice_type,
                'processing_details': [],
                'failed_files': []
            }
        
        successful_imports = 0
        failed_imports = 0
        skipped_duplicates = 0
        processing_details = []
        failed_files = []
        
        type_text = "GELİR (Satış)" if invoice_type == 'outgoing' else "GİDER (Alış)"
        logging.info(f"🔄 {len(qr_results)} QR sonucu işlenecek (TİP: {type_text} + DUPLICATE KONTROL)")
        
        for i, result in enumerate(qr_results, 1):
            dosya_adi = result.get('dosya_adi', 'Bilinmeyen')
            dosya_yolu = result.get('dosya_yolu', '')
            
            if result.get('durum') == 'BAŞARILI':
                qr_json = result.get('json_data', {})
                extracted_info = result.get('extracted_info', {})
                fatura_no_from_filename = result.get('fatura_no_from_filename', '')
                
                # Fatura alanlarına dönüştür
                parsed_fields = self._parse_qr_to_invoice_fields(qr_json, extracted_info, fatura_no_from_filename)
                
                if not parsed_fields or not parsed_fields.get('firma'):
                    logging.warning(f"   ⚠️ {dosya_adi}: Eksik fatura bilgisi")
                    failed_imports += 1
                    failed_files.append(dosya_yolu)
                    processing_details.append({
                        'file': dosya_adi,
                        'status': 'BAŞARISIZ',
                        'error': 'Firma bilgisi eksik'
                    })
                    continue
                
                # ⭐ DUPLICATE KONTROL ⭐
                fatura_no = parsed_fields.get('fatura_no', '')
                if self._is_duplicate_invoice(fatura_no):
                    skipped_duplicates += 1
                    logging.info(f"   ⏭️  {dosya_adi} -> ATLANDI (Duplicate: {fatura_no})")
                    processing_details.append({
                        'file': dosya_adi,
                        'status': 'ATLANDI (DUPLICATE)',
                        'fatura_no': fatura_no,
                        'error': None
                    })
                    continue
                
                # Backend'e ekle (manuel seçilen tip ile)
                try:
                    logging.info(f"   📝 {dosya_adi} kaydediliyor -> Tip: {invoice_type}, Firma: {parsed_fields.get('firma', 'N/A')[:30]}")
                    
                    result = self.backend.handle_invoice_operation(
                        operation='add',
                        invoice_type=invoice_type,
                        data=parsed_fields
                    )
                    
                    if result:
                        successful_imports += 1
                        logging.info(f"   ✅ {dosya_adi} -> {invoice_type.upper()} olarak KAYDEDİLDİ (Firma: {parsed_fields.get('firma', 'N/A')[:30]})")
                    else:
                        failed_imports += 1
                        failed_files.append(dosya_yolu)
                        logging.error(f"   ❌ {dosya_adi} -> Kaydedilemedi (Backend False döndü)")
                        processing_details.append({
                            'file': dosya_adi,
                            'status': 'BAŞARISIZ',
                            'error': 'Backend False döndü'
                        })
                        continue
                    processing_details.append({
                        'file': dosya_adi,
                        'status': 'BAŞARILI',
                        'type': invoice_type,
                        'fatura_no': fatura_no,
                        'error': None
                    })
                    
                except Exception as e:
                    logging.error(f"   ❌ {dosya_adi}: Veritabanı hatası - {e}")
                    failed_imports += 1
                    failed_files.append(dosya_yolu)
                    processing_details.append({
                        'file': dosya_adi,
                        'status': 'BAŞARISIZ',
                        'error': f'DB hatası: {e}'
                    })
            else:
                failed_imports += 1
                failed_files.append(dosya_yolu)
                processing_details.append({
                    'file': dosya_adi,
                    'status': 'BAŞARISIZ',
                    'error': result.get('durum', 'Bilinmeyen hata')
                })
        
        logging.info(f"\n{'='*60}")
        logging.info(f"✅ İşlem Tamamlandı!")
        logging.info(f"📊 Başarılı: {successful_imports}, Başarısız: {failed_imports}, Duplicate: {skipped_duplicates}")
        logging.info(f"📋 Tip: {invoice_type.upper()}")
        logging.info(f"{'='*60}\n")
        
        # Backend sinyalini tetikle
        self.backend.data_updated.emit()
        
        return {
            'success': True,
            'added': successful_imports,
            'failed': failed_imports,
            'skipped_duplicates': skipped_duplicates,
            'total': len(qr_results),
            'invoice_type': invoice_type,
            'processing_details': processing_details,
            'failed_files': failed_files
        }
    
    def _is_duplicate_invoice(self, fatura_no):
        """Veritabanında aynı fatura no var mı kontrol et"""
        if not fatura_no:
            return False
        
        try:
            # Hem gelir hem gider veritabanında kontrol et
            for db_type in ['outgoing', 'incoming']:
                invoices = self.backend.handle_invoice_operation(
                    operation='get',
                    invoice_type=db_type,
                    limit=None
                )
                
                if invoices:
                    for invoice in invoices:
                        existing_fatura_no = invoice.get('fatura_no', '')
                        if existing_fatura_no and existing_fatura_no == fatura_no:
                            return True
            
            return False
        except Exception as e:
            logging.warning(f"⚠️ Duplicate kontrol hatası: {e}")
            return False
    
    def _detect_invoice_type(self, qr_json, parsed_fields):
        """
        ⭐ OTOMATİK FATURA TİPİ TESPİTİ ⭐
        
        SATIS -> outgoing (gelir)
        ALIS -> incoming (gider)
        """
        # TİP alanına bak (öncelikli)
        tip_field = self._get_value_case_insensitive(qr_json, ['tip', 'type', 'senaryo', 'invoiceType'])
        
        if tip_field:
            tip_upper = str(tip_field).upper()
            
            # SATIS -> GELİR
            if any(keyword in tip_upper for keyword in ['SATIS', 'SATŞ', 'SALE', 'SELLING', 'TEMEL', 'TICARIFATURA']):
                logging.info(f"      🔍 Tip tespiti: SATIS -> GELİR (tip='{tip_field}')")
                return 'outgoing'
            
            # ALIS -> GİDER
            if any(keyword in tip_upper for keyword in ['ALIS', 'ALIŞ', 'PURCHASE', 'BUYING', 'ALIM']):
                logging.info(f"      🔍 Tip tespiti: ALIS -> GİDER (tip='{tip_field}')")
                return 'incoming'
        
        # Malzeme/Açıklama alanına bak
        malzeme = parsed_fields.get('malzeme', '').upper()
        if 'SATIS' in malzeme or 'SATŞ' in malzeme:
            logging.info(f"      🔍 Malzeme tespiti: SATIS -> GELİR")
            return 'outgoing'
        if 'ALIS' in malzeme or 'ALIŞ' in malzeme:
            logging.info(f"      🔍 Malzeme tespiti: ALIS -> GİDER")
            return 'incoming'
        
        # Varsayılan: E-faturalar genelde satış (gelir)
        logging.info(f"      ⚠️ Tip tespit edilemedi, varsayılan: GELİR")
        return 'outgoing'
    
    def _parse_qr_to_invoice_fields(self, qr_json, extracted_info=None, fatura_no_from_filename=''):
        """QR JSON'ını fatura alanlarına dönüştür + OCR bilgisi ekle"""
        if not qr_json:
            return {}
        
        if extracted_info is None:
            extracted_info = {}
        
        # ⭐ DEBUG: QR JSON yapısını logla ⭐
        logging.info(f"   🔍 QR JSON İÇERİĞİ:")
        logging.info(f"      Tüm anahtarlar: {list(qr_json.keys())}")
        
        # Tutar ile ilgili tüm alanları bul
        tutar_related = {}
        for key, value in qr_json.items():
            key_lower = key.lower()
            if any(word in key_lower for word in ['tutar', 'amount', 'total', 'pay', 'matrah', 'tax', 'kdv']):
                tutar_related[key] = value
        
        if tutar_related:
            logging.info(f"      💰 Tutar ile ilgili alanlar: {tutar_related}")
        else:
            logging.warning(f"      ⚠️ Tutar ile ilgili hiçbir alan bulunamadı!")
        
        # Anahtar eşleme sözlüğü
        key_map = {
            'fatura_no': ['faturaNo', 'invoiceNumber', 'faturanumarasi', 'belgeNo', 'documentNo', 'seriNo', 'faturaid', 'belge_no'],
            'tarih': ['invoiceDate', 'faturaTarihi', 'tarih', 'date', 'issueDate', 'belge_tarihi', 'belgeTarihi'],
            'firma': ['sellerName', 'saticiUnvan', 'firma', 'supplier', 'company', 'companyName', 'buyerName', 'aliciUnvan', 'satici_unvan', 'alici_unvan'],
            'malzeme': ['tip', 'type', 'itemName', 'description', 'malzeme', 'hizmet', 'urun', 'product', 'senaryo', 'aciklama'],
            'miktar': ['quantity', 'miktar', 'adet', 'amount', 'qty'],
            'toplam_tutar': ['payableAmount', 'odenecek', 'totalAmount', 'toplamTutar', 'total', 'tutar', 
                            'odenecekTutar', 'odenecek_tutar', 'toplam', 'hesaplanan_odenecek_tutar',
                            'vergilerDahilToplamTutar', 'vergiler_dahil_toplam_tutar', 'genel_toplam',
                            'mal_hizmet_toplam_tutari', 'malhizmettoplam', 'netAmount'],
            'matrah': ['taxableAmount', 'matrah', 'malhizmettoplam', 'mal_hizmet_toplam_tutari',
                      'hesaplanan_kdv_matrah', 'kdv_matrah', 'matrah_toplam', 'netAmount'],
            'kdv_tutari': ['taxAmount', 'hesaplanankdv', 'kdv', 'kdvtoplam', 'hesaplanan_kdv', 'kdv_tutari',
                          'toplam_kdv', 'vergi_tutari', 'hesaplanan_kdv_tutari'],
            'kdv_yuzdesi': ['taxRate', 'kdvOrani', 'vatRate', 'kdv_orani', 'oran'],
            'birim': ['currency', 'parabirimi', 'currencyCode', 'para_birimi']
        }
        
        parsed = {}
        
        # ⭐ Fatura No - DOSYA ADINDAN AL (ÖNCELİKLİ) ⭐
        qr_fatura_no = self._get_value_case_insensitive(qr_json, key_map['fatura_no'])
        if fatura_no_from_filename:
            parsed['fatura_no'] = str(fatura_no_from_filename)
            logging.debug(f"   📄 Fatura No dosya adından alındı: {fatura_no_from_filename}")
        elif qr_fatura_no:
            parsed['fatura_no'] = str(qr_fatura_no)
        else:
            parsed['fatura_no'] = ''
        
        # Tarih
        qr_tarih = self._get_value_case_insensitive(qr_json, key_map['tarih'])
        parsed['tarih'] = self.backend.format_date(str(qr_tarih)) if qr_tarih else datetime.now().strftime("%d.%m.%Y")
        
        # ⭐ TARİHLİ KUR ÇEKME (YENİ ÖZELLİK) ⭐
        # Fatura tarihine ait TCMB BanknoteSelling kurunu çek
        try:
            historical_rates = self.backend.fetch_historical_rates(parsed['tarih'])
            if historical_rates:
                parsed['manual_usd_rate'] = historical_rates.get('USD')
                parsed['manual_eur_rate'] = historical_rates.get('EUR')
                print(f"   💱 {parsed['tarih']} tarihli kurlar faturaya eklendi: USD={parsed['manual_usd_rate']}, EUR={parsed['manual_eur_rate']}")
        except Exception as e:
            print(f"   ⚠️ Tarihli kur ekleme hatası: {e}")
        
        # ⭐ Firma - OCR'DAN AL (QR'da yoksa) ⭐
        firma = self._get_value_case_insensitive(qr_json, key_map['firma'])
        if not firma or (isinstance(firma, str) and firma.isdigit()):
            # QR'da yoksa OCR'dan al
            if extracted_info.get('firma'):
                firma = extracted_info['firma']
                logging.debug(f"   🔍 Firma OCR'dan alındı: {firma}")
            else:
                # Alternatif alanlar
                firma = self._get_value_case_insensitive(qr_json, ['satici', 'alici', 'vkn', 'unvan']) or 'Firma Bilgisi Yok'
        parsed['firma'] = str(firma)
        
        # ⭐ Malzeme - HER ZAMAN OCR'DAN AL (PDF Tablosundan) ⭐
        malzeme = None
        if extracted_info.get('malzeme'):
            malzeme = extracted_info['malzeme']
            logging.debug(f"   🔍 Malzeme OCR'dan alındı: {malzeme}")
        else:
            # OCR'da bulunamadıysa QR'dan deneme yap
            qr_malzeme = self._get_value_case_insensitive(qr_json, key_map['malzeme'])
            if qr_malzeme and qr_malzeme not in ['SATIS', 'ALIS', 'EARSIV', 'TICARIFATURA']:
                malzeme = qr_malzeme
                logging.debug(f"   🔍 Malzeme QR'dan alındı: {malzeme}")
            else:
                malzeme = 'QR Kodlu E-Fatura'
                logging.debug(f"   ⚠️ Malzeme bulunamadı, default kullanıldı")
        parsed['malzeme'] = str(malzeme)
        
        # ⭐ MİKTAR - OCR'DAN ÖNCE AL, SONRA QR'YA BAK ⭐
        miktar = None
        
        # 1. Öncelik: OCR'dan alınan miktar (tablo koordinatlarından)
        if extracted_info.get('miktar'):
            miktar = extracted_info['miktar']
            logging.info(f"   🔍 Miktar OCR'dan alındı: {miktar}")
        else:
            # 2. OCR'da yoksa QR'dan dene
            qr_miktar = self._get_value_case_insensitive(qr_json, key_map['miktar'])
            if qr_miktar and qr_miktar != '0' and qr_miktar != 0:
                miktar = qr_miktar
                logging.info(f"   🔍 Miktar QR'dan alındı: {miktar}")
            else:
                # 3. Hiçbir yerde yoksa boş bırak
                logging.info(f"   ⚠️ Miktar bulunamadı, boş bırakıldı")
        
        parsed['miktar'] = str(miktar) if miktar else ''
        
        # Para birimi
        birim = str(self._get_value_case_insensitive(qr_json, key_map['birim']) or 'TRY').upper()
        parsed['birim'] = 'TL' if birim in ['TRY', 'TRL'] else birim
        
        # Tutar hesaplamaları
        toplam = self._to_float(self._get_value_case_insensitive(qr_json, key_map['toplam_tutar']))
        matrah = self._to_float(self._get_value_case_insensitive(qr_json, key_map['matrah']))
        kdv_tutari = self._to_float(self._get_value_case_insensitive(qr_json, key_map['kdv_tutari']))
        kdv_yuzdesi = self._to_float(self._get_value_case_insensitive(qr_json, key_map['kdv_yuzdesi']))
        
        # Eğer matrah ve toplam aynı alandan geliyorsa, birini sıfırla
        if toplam == matrah and toplam > 0:
            # mal_hizmet_toplam_tutari hem toplam hem matrah için kullanılmış olabilir
            # Bu durumda toplam'ı kullan, matrah'ı sıfırla
            matrah = 0.0
            logging.debug(f"      ⚠️ Toplam ve matrah aynı ({toplam}), matrah sıfırlandı")
        
        logging.info(f"      📊 Parse edilen değerler:")
        logging.info(f"         - Toplam: {toplam}")
        logging.info(f"         - Matrah: {matrah}")
        logging.info(f"         - KDV Tutarı: {kdv_tutari}")
        logging.info(f"         - KDV %: {kdv_yuzdesi}")
        
        # KDV yüzdesi
        if kdv_yuzdesi > 0:
            parsed['kdv_yuzdesi'] = kdv_yuzdesi
        elif matrah > 0 and kdv_tutari > 0:
            parsed['kdv_yuzdesi'] = round((kdv_tutari / matrah) * 100, 2)
        else:
            parsed['kdv_yuzdesi'] = self.backend.settings.get('kdv_yuzdesi', 20.0)
        
        # Tutar ve KDV hesaplama
        if matrah > 0 and toplam > 0:
            # Hem matrah hem toplam var
            parsed['toplam_tutar'] = matrah
            parsed['kdv_dahil'] = False
            parsed['kdv_tutari'] = kdv_tutari if kdv_tutari > 0 else round(matrah * parsed['kdv_yuzdesi'] / 100, 2)
            logging.info(f"      ✅ Durum 1: Hem matrah hem toplam var (matrah={matrah}, toplam={toplam})")
        elif toplam > 0:
            # Sadece toplam var
            parsed['toplam_tutar'] = toplam
            if kdv_tutari > 0:
                parsed['kdv_dahil'] = True
                parsed['kdv_tutari'] = kdv_tutari
            else:
                parsed['kdv_dahil'] = False
                parsed['kdv_tutari'] = round(toplam * parsed['kdv_yuzdesi'] / 100, 2)
            logging.info(f"      ✅ Durum 2: Sadece toplam var (toplam={toplam})")
        elif matrah > 0:
            # Sadece matrah var
            parsed['toplam_tutar'] = matrah
            parsed['kdv_dahil'] = False
            parsed['kdv_tutari'] = kdv_tutari if kdv_tutari > 0 else round(matrah * parsed['kdv_yuzdesi'] / 100, 2)
            logging.info(f"      ✅ Durum 3: Sadece matrah var (matrah={matrah})")
        else:
            # Hiçbiri yok - QR JSON'dan herhangi bir sayısal değer bul
            logging.warning(f"      ⚠️ Standart tutar alanları bulunamadı, alternatif arama yapılıyor...")
            
            # Tüm JSON alanlarını tara, sayısal değerleri bul
            possible_amounts = []
            for key, value in qr_json.items():
                if isinstance(value, (int, float)) and value > 0:
                    possible_amounts.append((key, value))
                elif isinstance(value, str):
                    # String içinde sayı var mı kontrol et
                    try:
                        cleaned = value.replace(',', '.').replace(' ', '').strip()
                        cleaned = re.sub(r'[^\d.-]', '', cleaned)
                        if cleaned:
                            num_val = float(cleaned)
                            if num_val > 0:
                                possible_amounts.append((key, num_val))
                    except:
                        pass
            
            if possible_amounts:
                # En büyük değeri al (genelde toplam tutar en büyük olur)
                possible_amounts.sort(key=lambda x: x[1], reverse=True)
                best_amount = possible_amounts[0][1]
                logging.info(f"      ✅ Alternatif tutar bulundu: {best_amount} (alan: {possible_amounts[0][0]})")
                parsed['toplam_tutar'] = best_amount
                parsed['kdv_dahil'] = False
                parsed['kdv_tutari'] = round(best_amount * parsed['kdv_yuzdesi'] / 100, 2)
            else:
                # Gerçekten hiçbir tutar yok
                logging.error(f"      ❌ QR'da hiçbir tutar bilgisi bulunamadı!")
                logging.error(f"      📋 QR JSON: {json.dumps(qr_json, indent=2, ensure_ascii=False)}")
                parsed['toplam_tutar'] = 0.0
                parsed['kdv_dahil'] = False
                parsed['kdv_tutari'] = 0.0
        
        logging.info(f"      💎 Final: Firma={parsed.get('firma', 'N/A')[:30]}, Tutar={parsed.get('toplam_tutar')}, Malzeme={parsed.get('malzeme', 'N/A')[:30]}")
        return parsed
    
    def _get_value_case_insensitive(self, data_dict, keys):
        """Büyük/küçük harf duyarsız anahtar arama"""
        for key in keys:
            if key in data_dict:
                return data_dict[key]
        
        # Lowercase karşılaştırma
        data_lower = {k.lower(): v for k, v in data_dict.items()}
        for key in keys:
            if key.lower() in data_lower:
                return data_lower[key.lower()]
        
        return None
    
    def _to_float(self, value):
        """Güvenli float dönüşümü"""
        if value is None or value == '':
            return 0.0
        
        try:
            # String ise temizle
            if isinstance(value, str):
                value = value.replace(',', '.').replace(' ', '').strip()
                # TL, USD gibi para birimi sembollerini kaldır
                value = re.sub(r'[^\d.-]', '', value)
            
            return float(value)
        except:
            return 0.0
    
    def _extract_date_from_text(self, pdf_text):
        """PDF metninden tarih çıkar - Gelişmiş"""
        if not pdf_text:
            return datetime.now().strftime("%d.%m.%Y")
        
        lines = pdf_text.split('\n')
        
        # Fatura tarihi anahtar kelimeleri
        date_keywords = [
            r'fatura\s*tarih[i]?',
            r'tarih',
            r'date',
            r'düzenlenme\s*tarih[i]?',
            r'belge\s*tarih[i]?'
        ]
        
        # Tarih formatları
        date_patterns = [
            r'(\d{2})[./-](\d{2})[./-](\d{4})',
            r'(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+(\d{4})'
        ]
        
        # Önce anahtar kelimelerin yakınında ara
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(re.search(keyword, line_lower) for keyword in date_keywords):
                # Bu satır ve sonraki 3 satırda tarih ara
                for j in range(i, min(i+4, len(lines))):
                    for pattern in date_patterns:
                        match = re.search(pattern, lines[j])
                        if match:
                            if len(match.groups()) == 3 and match.group(1).isdigit():
                                date_str = f"{match.group(1).zfill(2)}.{match.group(2).zfill(2)}.{match.group(3)}"
                                logging.debug(f"   📅 Tarih bulundu: {date_str}")
                                return date_str
        
        # Genel tarama
        for pattern in date_patterns:
            match = re.search(pattern, pdf_text)
            if match:
                if len(match.groups()) == 3 and match.group(1).isdigit():
                    date_str = f"{match.group(1).zfill(2)}.{match.group(2).zfill(2)}.{match.group(3)}"
                    logging.debug(f"   📅 Tarih bulundu (genel): {date_str}")
                    return date_str
        
        # Bulunamadıysa bugünün tarihi
        logging.warning(f"   ⚠️ PDF'de tarih bulunamadı, bugün kullanılacak")
        return datetime.now().strftime("%d.%m.%Y")
    
    def _extract_invoice_number_from_text(self, pdf_text):
        """PDF metninden fatura numarası çıkar"""
        if not pdf_text:
            return None
        
        lines = pdf_text.split('\n')
        
        # Fatura no anahtar kelimeleri
        invoice_keywords = [
            r'fatura\s*no',
            r'fatura\s*numaras[ıi]',
            r'invoice\s*number',
            r'belge\s*no',
            r'seri\s*no'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in invoice_keywords:
                if re.search(keyword, line_lower):
                    # Bu satırda veya sonraki 2 satırda fatura no ara
                    for j in range(i, min(i+3, len(lines))):
                        # Fatura no pattern: Harfler ve sayılar
                        invoice_match = re.search(r'([A-Z]{3}\d{12,}|[A-Z0-9]{10,})', lines[j])
                        if invoice_match:
                            invoice_no = invoice_match.group(1)
                            logging.debug(f"   📄 Fatura No: {invoice_no}")
                            return invoice_no
        
        return None
    
    def _extract_amount_from_text(self, pdf_text):
        """PDF metninden tutar çıkar - Gelişmiş (Toplam, Matrah, KDV)"""
        if not pdf_text:
            return {'toplam': 0.0, 'matrah': 0.0, 'kdv': 0.0, 'kdv_yuzdesi': 0.0}
        
        lines = pdf_text.split('\n')
        amounts = {
            'toplam': 0.0,
            'matrah': 0.0,
            'kdv': 0.0,
            'kdv_yuzdesi': 0.0
        }
        
        # TOPLAM TUTAR (Ödenecek, Genel Toplam)
        toplam_keywords = [
            r'ödenecek\s*tutar',
            r'genel\s*toplam',
            r'toplam\s*tutar',
            r'vergiler\s*dahil\s*toplam',
            r'total\s*amount',
            r'payable\s*amount'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in toplam_keywords:
                if re.search(keyword, line_lower):
                    # Bu satırda veya sonraki 2 satırda tutar ara
                    for j in range(i, min(i+3, len(lines))):
                        # Tutar pattern: sayılar, nokta, virgül
                        amount_match = re.search(r'([\d.,]+)\s*(?:TL|₺|EUR|USD)?', lines[j])
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                amount = float(amount_str)
                                if amount > 10:  # Mantıklı bir tutar
                                    amounts['toplam'] = amount
                                    logging.debug(f"   💰 Toplam tutar: {amount}")
                                    break
                            except:
                                continue
                    if amounts['toplam'] > 0:
                        break
            if amounts['toplam'] > 0:
                break
        
        # MATRAH (KDV Matrahı)
        matrah_keywords = [
            r'kdv\s*matrah[ıi]?',
            r'matrah',
            r'mal\s*hizmet\s*toplam',
            r'vergiden\s*önceki\s*toplam',
            r'net\s*tutar'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in matrah_keywords:
                if re.search(keyword, line_lower):
                    for j in range(i, min(i+3, len(lines))):
                        amount_match = re.search(r'([\d.,]+)\s*(?:TL|₺|EUR|USD)?', lines[j])
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                amount = float(amount_str)
                                if amount > 0:
                                    amounts['matrah'] = amount
                                    logging.debug(f"   📊 Matrah: {amount}")
                                    break
                            except:
                                continue
                    if amounts['matrah'] > 0:
                        break
            if amounts['matrah'] > 0:
                break
        
        # KDV TUTARI
        kdv_keywords = [
            r'hesaplanan\s*kdv',
            r'kdv\s*tutar[ıi]?',
            r'kdv\s*toplam[ıi]?',
            r'vergi\s*tutar[ıi]?',
            r'tax\s*amount'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in kdv_keywords:
                if re.search(keyword, line_lower):
                    for j in range(i, min(i+3, len(lines))):
                        amount_match = re.search(r'([\d.,]+)\s*(?:TL|₺|EUR|USD)?', lines[j])
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                amount = float(amount_str)
                                if amount > 0:
                                    amounts['kdv'] = amount
                                    logging.debug(f"   🧾 KDV tutarı: {amount}")
                                    break
                            except:
                                continue
                    if amounts['kdv'] > 0:
                        break
            if amounts['kdv'] > 0:
                break
        
        # KDV YÜZDESİ
        kdv_percent_match = re.search(r'%\s*(\d+)', pdf_text)
        if kdv_percent_match:
            amounts['kdv_yuzdesi'] = float(kdv_percent_match.group(1))
            logging.debug(f"   📈 KDV %: {amounts['kdv_yuzdesi']}")
        elif amounts['matrah'] > 0 and amounts['kdv'] > 0:
            amounts['kdv_yuzdesi'] = round((amounts['kdv'] / amounts['matrah']) * 100, 2)
            logging.debug(f"   📈 KDV % (hesaplanan): {amounts['kdv_yuzdesi']}")
        
        # Tutarları doğrula ve düzelt
        if amounts['toplam'] == 0 and amounts['matrah'] > 0 and amounts['kdv'] > 0:
            amounts['toplam'] = amounts['matrah'] + amounts['kdv']
            logging.debug(f"   ✅ Toplam hesaplandı: {amounts['toplam']}")
        
        if amounts['matrah'] == 0 and amounts['toplam'] > 0 and amounts['kdv'] > 0:
            amounts['matrah'] = amounts['toplam'] - amounts['kdv']
            logging.debug(f"   ✅ Matrah hesaplandı: {amounts['matrah']}")
        
        return amounts


# ============================================================================
# TEST ve STANDALONE KULLANIM
# ============================================================================

if __name__ == "__main__":
    print("[*] OPTIMIZE EDILMIS QR SISTEMI")
    print("=" * 50)
    
    # Standalone test
    processor = OptimizedQRProcessor()
    
    klasor = input("[?] Klasor yolu (bos=mevcut): ").strip() or "."
    
    results = processor.process_qr_files_in_folder(klasor, max_workers=6)
    
    if results:
        successful = len([r for r in results if r.get('durum') == 'BAŞARILI'])
        print(f"\n[OK] Islem tamamlandi!")
        print(f"[STATS] Basarili: {successful}/{len(results)}")
        print(f"[STATS] Akilli DPI Istatistikleri:")
        print(f"   - Yuksek Kalite (300): {processor.stats['smart_dpi_300']}")
        print(f"   - Orta Kalite (450): {processor.stats['smart_dpi_450']}")
        print(f"   - Dusuk Kalite (600): {processor.stats['smart_dpi_600']}")
        print(f"   - Fallback: {processor.stats['fallback_scan']}")
        print(f"   - Basarisiz: {processor.stats['failed']}")
    else:
        print("[ERROR] Islem basarisiz")