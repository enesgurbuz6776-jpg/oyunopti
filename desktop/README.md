# OyunOpti Pro v1.2.0 — Lisanslı Windows Uygulaması

**Windows 10/11** için lisans doğrulamalı oyun performans uygulaması. **Ücretsiz kullanım veya deneme lisansı yoktur.**

## Lisans
- İlk açılışta **Lisansım** sayfası görünür. FPS, optimizasyon, oyun profili ve raporlara erişmek için geçerli cihaz koduna özel **Ed25519 imzalı Pro lisansı** zorunludur.
- Satıcının özel anahtarı **asla** bu GitHub reposuna veya uygulamaya konmaz. Uygulama yalnızca doğrulama için herkese açık anahtarı içerir.
- Lisans standart **30 gün geçerlidir** ve süresi dolunca yeniden düzenlenmesi gerekir. Tam otomatik abonelik/ödeme entegrasyonu henüz hazır değildir.
- Satış için planlanan fiyat **$10/ay**. Türkiye'de ücretli satışa geçmeden önce vergiler dâhil TL fiyatı, yenileme/iptal koşulları ve ödeme sağlayıcısı netleştirilmelidir.
- **Geri Al** özelliği güvenlik nedeniyle lisans süresi bitmişse de kullanılabilir.

## Lisanslı özellikler
- Windows Oyun Modu ve seçime bağlı Yüksek Performans güç planını değiştirme (gerekli yedek ve geri alma ile).
- Intel PresentMon CLI kullanılarak ölçülen canlı FPS ve yaklaşık %1 low görüntüleme (üçüncü taraf konsol aracı ayrıca indirilir).
- Kullanıcının aynı koşullarda topladığı manuel FPS önce/sonra karşılaştırması.
- FPS grafiği, CSV rapor ve oyun profili.

**FPS artışı garanti edilmez.** Güç planı cihazın ısınmasını ve elektrik tüketimini artırabilir. Oyun içi tam ekran overlay çalışması oyuna göre farklılık gösterebilir.

## Derleme
GitHub Actions: .github/workflows/build-fps-booster.yml Windows PyInstaller EXE'sini üretir; imzalı lisans doğrulama testleri, açılış testi ve EXE içindeki OyunOpti logosunun PE kaynak kontrolünü çalıştırır.

## Operatör lisans paneli
Özel Ed25519 anahtarı GitHub'a yüklenmez. Ticari müşteriye lisans göndermeden **önce gerçek ödeme satıcı panelinden teyit edilmelidir**. Manuel lisans üretmek için gizli operatör paketini güvenli yerde kullan.

## Güvenlik kısıtlamaları
Bu sürüm **offline lisans doğrulaması** kullanır. Ürün dosyasını değiştirebilen veya eski sürümleri saklayan kişiler için mutlak korsan koruması sunmaz. Özellikle önceki GitHub yayınları hâlâ indirilebiliyorsa kaldırılması gerekir. Daha güçlü üyelik ve otomatik ödeme yönetimi için sunucu tarafı doğrulama/ödeme entegrasyonu önerilir.

## Önemli: İmzalama anahtarı yenileme (2026-10-10)

Eski lisans imzalama anahtarı bir ekran görüntüsünde ifşa edildiğinden kullanılmamalıdır.
Yeni Pro v1.2.0 uygulaması yenilenen açık doğrulama anahtarını taşır.
Özel PEM dosyası ve içerikleri yalnızca sahipte ve Render ortam değişkeninde
tutulmalıdır; GitHub deposuna, ekran görüntülerine veya sohbete yüklenmemelidir.
Eski EXE sürümleri çevrimdışı olduğundan geçmiş kopyalar uzaktan kapatılamaz.
Eski sürümler GitHub Releases üzerinden ayrıca kaldırılmalı, tek başına
uygulama sürümünü değiştirmek geçmiş lisansları iptal etmez.
