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
| Chat Agent | Ana sohbet ve istek analizi | LLaMA 3.1 70B |
| Task Manager | Görev yönetimi ve koordinasyon | Claude 3 Sonnet |
| Coder | Kod yazma ve geliştirme | Qwen Coder Plus |
| DB Manager | Veritabanı yönetimi | GPT-4 Turbo |
| Browser Agent | Web araştırma | Gemini Pro 1.5 |
| File Reader | Dosya analizi | DeepSeek R1 |
| Tester | Test ve kalite kontrolü | Claude 3 Sonnet |
| Coordinator | Proje finalizasyonu | GPT-4 Turbo |

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
1. Python sunucusunun çalıştığını kontrol edin: `http://localhost:5000`
2. CORS ayarlarını kontrol edin
3. Firewall ayarlarını kontrol edin

### API Anahtarı Sorunları
1. OpenRouter hesabınızda kredi olduğunu kontrol edin
2. API anahtarının doğru girildiğini kontrol edin
3. Model limitlerinizi kontrol edin

### Performans Sorunları
1. Streaming yanıtları kapatmayı deneyin
2. Token limitlerini düşürün
3. Daha hızlı modeller seçin

## 📈 Gelecek Özellikler

- [ ] Dosya yükleme ve analiz
- [ ] Git entegrasyonu
- [ ] Docker containerization
- [ ] Çoklu proje desteği
- [ ] Ajan chat history
- [ ] Custom ajan oluşturma
- [ ] API rate limiting
- [ ] Kullanıcı yetkilendirmesi

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun: `git checkout -b feature/AmazingFeature`
3. Değişiklikleri commit edin: `git commit -m 'Add AmazingFeature'`
4. Branch'i push edin: `git push origin feature/AmazingFeature`
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 🆘 Destek

Sorunlar için GitHub Issues kullanın veya [iletişim] bölümünden ulaşın.

---

**AtomAgent** ile yazılım geliştirme süreçlerinizi hızlandırın ve AI'ın gücünü deneyimleyin! 🚀
