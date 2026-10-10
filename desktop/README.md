# OyunOpti FPS Booster – Windows Beta

**Windows 10/11** için ücretsiz, açık kaynak, manuel FPS karşılaştırma ve güvenli Windows ayarları uygulaması.

## Özellikler

- Windows Game Mode seçeneğini açma (HKCU\\Software\\Microsoft\\GameBar\\AutoGameModeEnabled).
- İsteğe bağlı Yüksek Performans güç planını seçme (sistemde mevcut olmalıdır).
- Orijinal ayarları değiştirmeden önce `%APPDATA%\\OyunOptiFPSBooster\\state.json` içinde saklama.
- Geri Al ile saklanan ayarları geri yükleme.
- PUBG, CS2 ve diğer oyunlarda kullanıcının girdiği ortalama FPS değerlerini karşılaştırma.
- İnternet bağlantısı, veri aktarımı, yönetici yetkisi veya oyun dosyası değişikliği gerektirmez.

## Dikkat

Program **FPS artışını garanti etmez** ve **otomatik FPS ölçmez**. Performans ölçümünü oyun içi sayaç veya güvenilir ölçüm aracı ile yapın. Yüksek Performans güç planı ısı ve enerji kullanımını artırabilir. Bazı sistemlerde bu plan devre dışı olabilir.

## Çalıştırma

Kaynak kod: Windows ve Python 3.12+ üzerinde `python desktop/oyunopti_booster.py`.

Windows EXE: GitHub Actions'ın **Build OyunOpti FPS Booster** iş akışı Windows üzerinde PyInstaller ile `OyunOpti-FPS-Booster.exe` oluşturur ve beta sürümüne ekler.

Yayınlanan EXE dijital olarak imzalanmamış olabilir. Çalıştırmadan önce GitHub kaynağını ve `SHA256SUMS.txt` bütünlük dosyasını inceleyin. Windows üzerinde gerçek cihaz testi henüz tamamlanmamıştır.
