# AtomAgent - CrewAI Tabanlı Çok Ajanlı Geliştirme Ortamı

AtomAgent, kullanıcıların doğal dil ile yazılım geliştirme süreçlerini başlatabileceği, yönlendirebileceği ve takip edebileceği **çok ajanlı bir geliştirme ortamı**dır.

## 🚀 Özellikler

- **Akıllı İstek Sınıflandırması**: Basit soruları doğrudan yanıtlar, karmaşık projeleri çok-ajanlı takıma iletir
- **8 Uzman Ajan**: Her ajan farklı uzmanlık alanında ve farklı AI modellerle çalışır
- **Gerçek Zamanlı Streaming**: Token-by-token canlı yanıt akışı
- **Modern Arayüz**: Manus AI benzeri karanlık tema ve smooth animasyonlar
- **Model Yönetimi**: Her ajana farklı LLM modeli atayabilme
- **Proje Takibi**: Gerçek zamanlı proje durumu ve ilerleme gösterimi
- **Sandbox Ortamları**: Her ajanın kendine ait çalışma dizini

## 🎯 Ajan Sistemi

| Ajan | Uzmanlık Alanı | Varsayılan Model |
|------|---------------|------------------|
| Chat Agent | Ana sohbet ve istek analizi | |
| Task Manager | Görev yönetimi ve koordinasyon | |
| Coder | Kod yazma ve geliştirme | |
| DB Manager | Veritabanı yönetimi | |
| Browser Agent | Web araştırma | |
| File Reader | Dosya analizi | |
| Tester | Test ve kalite kontrolü | |
| Coordinator | Proje finalizasyonu | |

## 📋 Gereksinimler

### Frontend
- Node.js 18+
- npm veya yarn

### Backend
- Python 3.8+
- pip (Python package manager)
- OpenRouter API anahtarı

## 🛠 Kurulum

### 1. Frontend Kurulumu (Otomatik)
Frontend zaten hazır durumda. Geliştirme sunucusu çalışıyor.

### 2. Backend Kurulumu

#### Adım 1: Backend dizinine geçin
```bash
cd src/backend
```

#### Adım 2: Sanal ortam oluşturun
```bash
# Python sanal ortamı oluştur
python -m venv venv

# Linux/Mac için aktive et:
source venv/bin/activate

# Windows için aktive et:
venv\Scripts\activate
```

#### Adım 3: Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

#### Adım 4: Sunucuyu başlatın
```bash
python server.py
```

#### Alternatif olarak frontend ve backend aynı anda başlatın
```bash
python app.py
```

### 3. API Anahtarı Yapılandırması

1. [OpenRouter.ai](https://openrouter.ai/) hesabı oluşturun
2. API anahtarınızı alın
3. AtomAgent arayüzünde **Settings > OpenRouter API** bölümünden anahtarınızı girin

## 🚀 Kullanım

### Basit Sorgular
- Genel programlama soruları
- Kod örnekleri
- Açıklamalar

**Örnek**: "Python'da liste nasıl sıralanır?"

### Karmaşık Projeler
- Tam stack web uygulamaları
- Çoklu dosya projeleri
- Veritabanı entegrasyonları

**Örnek**: "Python Flask backend ile e-ticaret sitesi istiyorum. PostgreSQL veritabanı, ödeme sistemi ve admin paneli olsun."


## Proje ile ilgili görseller:


## 🔧 Geliştirme

### Yeni Ajan Ekleme

1. `AGENTS` listesine yeni ajan ekleyin
2. Backend'de `AgentConfig` oluşturun
3. Gerekli araçları (tools) tanımlayın
4. Sandbox dizini oluşturun

### Model Ekleme

`AVAILABLE_MODELS` listesine yeni modeli ekleyin. OpenRouter'da desteklenen tüm modelleri kullanabilirsiniz.

## 🔒 Güvenlik

- API anahtarları backend'de güvenli şekilde saklanır
- Her ajan kendi sandbox ortamında çalışır
- Dosya işlemleri izole edilmiştir
- Terminal komutları sınırlı yetkilerle çalışır

## 🐛 Sorun Giderme

### Backend Bağlantı Sorunu
1. Python sunucusunun çalıştığını kontrol edin: `http://localhost:5001`
2. CORS ayarlarını kontrol edin
3. Firewall ayarlarını kontrol edin

## 📈 Gelecek Özellikler


- [X] OpenRooter iletişim sağlanması
- [X] Backend kurulumu
- [X] Frontend kurulumu
- [X] Backend - Frontend entegrasyonu
- [X] Websoket bağlantısı
- [ ] Agent ların sistem promptlarını yapılandırma
- [ ] Artifacts paneli
- [ ] API keylerini saklama
- [ ] Sohbet çıktı optimizasyonu
- [ ] MCP server desteği
- [ ] Dosya yükleme ve analiz
- [ ] Git entegrasyonu
- [ ] Docker containerization
- [ ] Çoklu proje desteği
- [ ] Ajan chat history
- [ ] Custom ajan oluşturma
- [ ] API rate limiting
- [ ] Kullanıcı yetkilendirmesi


## Projenin şu anki durumu:
  ### Proje şu an 2. versiyonunda olup daha geliştirme aşamasındadır. Arayüz üzerinden API a bağlanarak modellere veri gönderimi ve alımı sağlanabilmektedir. Bir sonraki versiyonda API keylerini, model seçimlerini ve sistem promptlarını kaydetme özellikleri eklemek hedeflenmektedir. Şu an API ile modellerden alınan cevapları web konsolu aracılığıyla görebilmekteyiz fakat arayüzde çıktı almakta problemler yaşanmakta. En kısa sürede bu sorunlar çözülüp v3 paylaşılacaktır.
