# OyunOpti Pro — Otomatik Shopier lisans teslimatı

Bu klasör OyunOpti Pro v1.x için **sunucu tarafında** çalışır. GitHub Pages yalnızca
ön yüzü barındırır; Shopier doğrulaması, sipariş kayıtları ve Ed25519 anahtarları
her zaman özel sunucuda tutulur.

## Hazırlanan müşteri akışı
1. Uygulamadaki **Lisansım → Pro Lisans Satın Al** düğmesi cihaz kodunu
   `https://oyunopti.com/pro-satin-al.html?device=...` sayfasına aktarır.
2. Müşteri e-posta adresini girer, sunucu benzersiz Shopier ürünü/ödeme URL'si üretir.
3. Shopier **order.created** imzalı webhook gönderir.
4. Sunucu HMAC imzasını doğrular, ayrıca **Shopier API'den siparişi tekrar okur**.
   Ödeme `paid`, tutar, döviz, ürün kimliği ve miktarı eşleşmiyorsa lisans **VERMEZ**.
5. Uygun ödeme **yalnız bir kere** işlenir. Cihaz koduna ve siparişe imzalı 30 günlük
   lisans yazılır; aktif lisans yenileniyorsa mevcut sürenin sonuna 30 gün eklenir.
6. Aynı tarayıcıdaki satın alma sayfası, gizli işlem anahtarıyla lisansı otomatik alır.
   Müşteri lisansı kopyalayıp uygulamadaki **Lisansı Doğrula** alanına yapıştırır.

Bu akış, **her yeni ödeme üzerine otomatik 30 günlük lisans düzenler**. Shopier'in
müşteri kartından **otomatik tekrarlayan tahsilat** özelliği bu üründe kurulmuş değildir;
müşteri yenilemek için tekrar Shopier ödemesi yapar.

## Render bağlantısı ve güvenli deneme kurulumu

GitHub kökündeki `render.yaml`, Node.js servisiyle PostgreSQL'i birlikte
tanımlar ve bağlantı adresini `fromDatabase` üzerinden otomatik geçirir.
Ödeme **başlangıçta `SALE_ENABLED=false`** olduğu için bu taslağı yüklemek
müşterilere tahsilat açmaz. Sunucu `schema.sql` tablolarını başlangıçta
güvenli biçimde oluşturur.

**Uyarı:** Taslakta yalnız kurulum testi için Render **Free** planı kullanılır.
Render Free PostgreSQL **30 gün sonra sona erer** ve yedek sunmaz; müşterilerle
gerçekten satış yapmak ve lisans kayıtlarını korumak için kalıcı/ücretli
veritabanına ve güvenilir çalışan hizmete geçmek gerekir. Bu yükseltme maliyet
oluşturabilir; onay olmadan açılmaz.

Gizli dört ayar (Shopier PAT, webhook imzası, mağaza slug ve lisans özel anahtarı)
Render ortamına kullanıcı tarafından güvenli biçimde girilmelidir. **Özel
imzalama anahtarı hiçbir zaman GitHub dosyalarına veya tarayıcıya konmaz.**
Özel anahtar, uygulamaya gömülü açık anahtarla eşleşmedikçe backend ödeme
aktifleştirmeyi reddeder. API ayakta olmadan sitenin satış düğmesi kapalı kalır.

## Bağlamadan önce gerekli bileşenler

- Shopier satıcı hesabından **PAT (kişisel erişim anahtarı)**, mağaza slug bilgisi ve
  `order.created` webhook kaydının sunduğu **imza anahtarı/token**.
- HTTPS Node.js 22 barındırma (ör. Render) ve **kalıcı PostgreSQL**.
  Uykuya geçen ücretsiz bir servis webhook cevap süresini kaçırabilir.
- `OyunOpti_Pro_Ozel_Lisans_Paneli.zip` içindeki **özel Ed25519 anahtarını**
  sadece sunucunun şifrelenmiş `LICENSE_PRIVATE_KEY_PEM` ortam değişkenine koy.
  **Asla GitHub, site, istemci, ekran görüntüsü veya sohbet mesajına yapıştırma.**
  Halihazırda yayımlanan Windows uygulamasına gömülü karşılık gelen
  **public key** ile eşleşmelidir.
- Shopier test siparişi ve gerçek `order.created` örnek verisiyle ürün/tutar/kimlik
  eşleşme kontrolü. Shopier alan şeması farklıysa `inspectShopierOrder` güvenli biçimde
  işlemi reddeder; para kesilen ancak lisans çıkmayan sipariş destekten incelenmelidir.
- Türkiye tüketicilerine vergiler dahil toplam TL fiyatı, iptal ve yenileme koşullarını
  ödeme öncesinde göster. `$10/30 gün` burada **hedef konfigürasyon**;
  Shopier'in USD satışı desteklediği gerçek hesapta ayrıca doğrulanmalıdır.

## Kurulum

```bash
cd pro-backend
npm install
npm test
# PostgreSQL bağlantısıyla bir kez:
psql "$DATABASE_URL" -f schema.sql
npm start
```

Değişkenler (`.env.example` örneğine bak):

| Ad | Açıklama |
|---|---|
| `DATABASE_URL` | Kalıcı PostgreSQL bağlantısı |
| `DATABASE_SSL` | TLS gerekiyorsa `true` |
| `SITE_ORIGIN` | Tam olarak `https://oyunopti.com` |
| `SHOPIER_PAT` | Yalnız sunucuda saklanan Shopier PAT |
| `SHOPIER_SHOP_SLUG` | Shopier mağaza slug |
| `SHOPIER_WEBHOOK_TOKEN` | Shopier webhook HMAC doğrulama anahtarı |
| `LICENSE_PRIVATE_KEY_PEM` | Şifreli ortam değişkeninde sunulan PKCS#8 Ed25519 PEM |
| `PRO_PRICE` | Örn. `10.00` |
| `PRO_CURRENCY` | `USD` (Shopier hesabında kontrol edilmeli) |
| `SALE_ENABLED` | **Testler tamamlanmadan `false` bırak.** |

Sertleştirme:
- `SHOPIER_PAT`, `SHOPIER_WEBHOOK_TOKEN`, imzalama anahtarı *web sitesine* konmaz.
- Webhook yalnızca imza + Shopier API teyidi sonrası lisans verir.
- `pro_orders` tablosunda sipariş numarası ve Shopier ürün kimliği benzersizdir,
  tekrar gelen webhook ikinci lisans üretmez.
- İade/chargeback durumunda mevcut **çevrimdışı** imzalı lisans süresi bitene
  dek yerel çalışmaya devam edebilir; anında iptal için gelecekte sunucu tarafı
  çevrimiçi lisans kontrolü gerekecek.
- Müşteri başka tarayıcı/cihazdan dönerse gizli işlem anahtarı bulunmadığından
  otomatik anahtar sayfası açılamaz; destekten siparişi doğrulanarak teslim edilir.
- E-posta otomatik gönderimi için ayrıca bir işlemsel posta sağlayıcısı gerekir;
  bu sürüm lisansı aynı tarayıcıda teslim eder.

## Mağaza ve dağıtım bağlantıları

1. Sunucu URL'si örn. `https://api.oyunopti.com` olarak yayınlanır.
2. Shopier webhook URL: `https://api.oyunopti.com/api/shopier/webhook`,
   olay: `order.created`. Shopier'in verdiği gizli imza tokenı sunucuya kaydedilir.
3. `https://oyunopti.com/pro-config.js` içindeki **yalnız herkese açık API URL'si**
   gerçek sunucu adresine çevrilir.
4. Sağlık endpoint'i `GET /api/health`, `paymentsEnabled:true` dönene kadar
   satın alma formu pasif kalır. `SALE_ENABLED=true` **en son** verilir.
5. Shopier'den önce küçük bir gerçek siparişle ödeme, teslim, yenileme ve
   hatalı sipariş kontrolleri yapılır. Bu testlerdeki harcamalar gerçek olabilir.

API:
- `GET /api/health`: satış açık mı ve sabit fiyat
- `POST /api/checkout`: cihaz kodu + e-postayla tekil ödeme oturumu
- `POST /api/shopier/webhook`: Shopier imzalı sipariş bildirimi (müşteri kullanamaz)
- `POST /api/claim`: aynı tarayıcıda işlem sırrıyla lisans teslimi

**Şu anda gizli anahtarlar ve canlı API barındırması bağlı olmadığı için gerçek ödeme
ve otomatik Pro teslimatı henüz aktif değildir.** Bu kodu hazır altyapı olarak
değerlendir; tüketicilerden gerçek para almadan önce Shopier canlı entegrasyonu ve
uçtan uca sipariş testi yapılmalıdır.
