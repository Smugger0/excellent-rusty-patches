use pyo3::prelude::*;
use rxing::BarcodeFormat;
use image::{DynamicImage, GenericImageView};

/// QR tarama sonucunu döndüren yardımcı fonksiyon (Raw Luma)
fn scan_helper_raw(width: u32, height: u32, raw_pixels: Vec<u8>) -> Option<String> {
    // rxing helper fonksiyonunu çağır
    match rxing::helpers::detect_in_luma(raw_pixels, width, height, Some(BarcodeFormat::QR_CODE)) {
        Ok(result) => Some(result.getText().to_string()),
        Err(_) => None,
    }
}

/// QR tarama sonucunu döndüren yardımcı fonksiyon (DynamicImage wrapper)
fn scan_helper(img: &DynamicImage) -> Option<String> {
    let width = img.width();
    let height = img.height();
    
    // Gri tonlamaya (Luma) çevir ve vektöre dönüştür
    let luma_img = img.to_luma8();
    let raw_pixels = luma_img.into_vec();

    scan_helper_raw(width, height, raw_pixels)
}

/// Raw Luma verisinden belirtilen alanı kesip yeni bir vektör döndürür
fn crop_luma_raw(data: &[u8], width: u32, x: u32, y: u32, w: u32, h: u32) -> Vec<u8> {
    let mut cropped = Vec::with_capacity((w * h) as usize);
    for row in 0..h {
        let src_y = y + row;
        let src_start = (src_y * width + x) as usize;
        let src_end = src_start + w as usize;
        
        if src_end <= data.len() {
            cropped.extend_from_slice(&data[src_start..src_end]);
        }
    }
    cropped
}

/// Ham Luma (Gri Tonlama) verisini alıp QR arar (Performans için)
#[pyfunction]
fn scan_raw_luma(py: Python, data: &[u8], width: u32, height: u32) -> PyResult<Option<String>> {
    let data_vec = data.to_vec();
    
    py.allow_threads(move || {
        // --- AŞAMA 1: Tam Resim (Raw Scan) ---
        if let Some(qr) = scan_helper_raw(width, height, data_vec.clone()) {
             return Ok(Some(qr));
        }

        // --- AŞAMA 2: Sağ Üst Köşe + Kontrast (Fallback) ---
        let crop_x = (width as f32 * 0.60) as u32;
        let crop_y = 0;
        let crop_w = width - crop_x;
        let crop_h = (height as f32 * 0.40) as u32;

        let cropped_data = crop_luma_raw(&data_vec, width, crop_x, crop_y, crop_w, crop_h);
        
        if let Some(img_buffer) = image::ImageBuffer::<image::Luma<u8>, _>::from_raw(crop_w, crop_h, cropped_data) {
             let mut gray_img = image::DynamicImage::ImageLuma8(img_buffer).to_luma8();
             image::imageops::contrast(&mut gray_img, 20.0);
             
             if let Some(qr) = scan_helper_raw(crop_w, crop_h, gray_img.into_vec()) {
                 return Ok(Some(qr));
             }
        }

        Ok(None)
    })
}

/// Görüntü baytlarını (bytes) alır ve QR arar
#[pyfunction]
fn scan_image_bytes(py: Python, data: &[u8]) -> PyResult<Option<String>> {
    let data_vec = data.to_vec();
    
    py.allow_threads(move || {
        let img = match image::load_from_memory(&data_vec) {
            Ok(i) => i,
            Err(_) => return Ok(None),
        };

        // --- AŞAMA 1: Hızlı Tarama (Tam Resim) ---
        if let Some(qr) = scan_helper(&img) {
            return Ok(Some(qr));
        }

        // --- AŞAMA 2: Sağ Üst Köşe ---
        let (w, h) = img.dimensions();
        let crop_x = (w as f32 * 0.60) as u32;
        let crop_w = w - crop_x;
        let crop_h = (h as f32 * 0.40) as u32;

        let cropped_img = img.crop_imm(crop_x, 0, crop_w, crop_h);
        if let Some(qr) = scan_helper(&cropped_img) {
            return Ok(Some(qr));
        }

        // --- AŞAMA 3: Derin Tarama (Kontrast Artırma) ---
        let mut gray_img = img.to_luma8();
        
        image::imageops::contrast(&mut gray_img, 20.0);
        
        let enhanced_img = DynamicImage::ImageLuma8(gray_img);
        if let Some(qr) = scan_helper(&enhanced_img) {
            return Ok(Some(qr));
        }

        Ok(None)
    })
}

/// JSON Temizleme Fonksiyonu
#[pyfunction]
fn clean_json_string(text: String) -> PyResult<String> {
    let cleaned: String = text.chars()
        .filter(|&c| !c.is_control())
        .collect();
    
    let cleaned = cleaned.replace("\\x", "")
                         .replace("'", "\"")
                         .replace("“", "\"")
                         .replace("”", "\"");
    
    Ok(cleaned)
}

/// Modül Tanımlaması (PyO3 0.21+ Bound Syntax)
#[pymodule]
fn rust_qr_backend(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(scan_image_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(clean_json_string, m)?)?;
    m.add_function(wrap_pyfunction!(scan_raw_luma, m)?)?;
    Ok(())
}