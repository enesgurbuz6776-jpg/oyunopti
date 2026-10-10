# OyunOpti FPS Booster – Windows Beta v0.4

**Windows 10/11** için ücretsiz, açık kaynak, manuel FPS karşılaştırma ve güvenli Windows ayarları uygulaması.

## Özellikler

- Windows Game Mode seçeneğini açma (HKCU\\Software\\Microsoft\\GameBar\\AutoGameModeEnabled).
- İsteğe bağlı Yüksek Performans güç planını seçme (sistemde mevcut olmalıdır).
- Orijinal ayarları değiştirmeden önce `%APPDATA%\\OyunOptiFPSBooster\\state.json` içinde saklama.
- Geri Al ile saklanan ayarları geri yükleme.
- PUBG, CS2 ve diğer oyunlarda kullanıcının girdiği ortalama FPS değerlerini karşılaştırma.
- Son testlerin karşılaştırma grafiği ve CSV rapor dışa aktarımı.
- **Pro beta:** Intel PresentMon CLI kullanarak gerçek kare zamanlarından canlı FPS takibi ve tahmini %1 düşük FPS gösterimi. İsteğe bağlı kayan masaüstü penceresi; oyunların özel tam ekran modlarında görünmeyebilir.
- **Pro optimizasyon:** Oyun Modu ve güç planı ayarlarını güvenli şekilde uygulama, mevcut ayarlar için yedek ve geri alma.
- **Planlanan $10/ay abonelik:** Şu anda ödeme alınmaz. Pro beta özellikleri test amacıyla herkese açıktır. Ücretli erişim ancak ödeme, lisans doğrulama, iptal/yenileme ve tüketici bilgilendirme altyapısı tamamlandıktan sonra açılacaktır.
- Oyun bazlı gelişmiş ayar önerileri ve otomatik lisans doğrulama henüz **planlanan** özelliklerdir.
- İnternet bağlantısı, veri aktarımı, yönetici yetkisi veya oyun dosyası değişikliği gerektirmez.

## Dikkat

Program **FPS artışını garanti etmez** ve **otomatik FPS ölçmez**. Performans ölçümünü oyun içi sayaç veya güvenilir ölçüm aracı ile yapın. Yüksek Performans güç planı ısı ve enerji kullanımını artırabilir. Bazı sistemlerde bu plan devre dışı olabilir.

## Canlı FPS entegrasyonu

1. Resmî Intel PresentMon konsol sürümünü `https://github.com/GameTechDev/PresentMon/releases` adresinden edinin. **PresentMon GUI ile ConsoleApplication farklıdır.** Konsol sürümünü (örn. `PresentMon-2.x-x64.exe`) seçin.
2. OyunOpti → **Canlı FPS Pro** → **EXE Seç** menüsüne konsol aracı yolunu girin.
3. Oyun açıkken hedef oyun EXE adını seçin (`TslGame.exe`, `cs2.exe` vb.). **Ölçümü Başlat** düğmesine basın.
4. Bazı oyunlarda/Windows oturumlarında ETW performans izleme izinleri gerekir. OyunOpti yönetici yetkisi talep etmez; çalışmazsa sahte değer üretmez.
5. Mevcut Pro gösterimi bir **beta test ön izlemesidir**. Henüz abonelik, ücretli lisans veya korunan Pro aktivasyonu uygulanmamıştır.

Kaynak: Intel PresentMon GitHub `README-ConsoleApplication.md`, CLI parametreleri `--process_name`, `--output_stdout` ve `MsBetweenPresents`.

## Çalıştırma

Kaynak kod: Windows ve Python 3.12+ üzerinde `python desktop/oyunopti_booster.py`.

Windows EXE: GitHub Actions'ın **Build OyunOpti FPS Booster** iş akışı Windows üzerinde PyInstaller ile `OyunOpti-FPS-Booster.exe` oluşturur ve beta sürümüne ekler.

Yayınlanan EXE dijital olarak imzalanmamış olabilir. Çalıştırmadan önce GitHub kaynağını ve `SHA256SUMS.txt` bütünlük dosyasını inceleyin. Windows üzerinde gerçek cihaz testi henüz tamamlanmamıştır.
