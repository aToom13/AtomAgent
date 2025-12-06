# AtomAgent v3.0

AI-Powered Development Assistant

## Nedir?

AtomAgent, doğal dil ile verdiğiniz görevleri anlayan ve çözen tam otonom bir AI asistanıdır. v3.0 ile tamamen yeni bir Web UI eklendi - kod yazma, dosya yönetimi, web araştırması, Docker sandbox ve canlı önizleme (Canvas) desteği sunar.

## Kurulum

```bash
pip install -r requirements.txt
```

`.env` dosyası oluşturup API key'lerinizi ekleyin:
```
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
OPENROUTER_API_KEY=your_key
GROQ_API_KEY=your_key
# Birden fazla key için virgülle ayırın:
# OPENAI_API_KEY=key1,key2,key3
```

## Kullanım

### Web UI (Önerilen)
```bash
python web_main.py
```
Tarayıcınızda `http://localhost:8000` adresine gidin.

### Terminal UI (Textual)
```bash
python main.py
```

## v3.0 Yeni Özellikler

### 🌐 Tamamen Yeni Web UI
v3.0 ile sıfırdan tasarlanmış modern web arayüzü:
- **Bento Style** karanlık tema
- **Sol Panel**: Session geçmişi
- **Orta Panel**: Chat (streaming yanıtlar)
- **Sağ Panel**: Terminal, Dosyalar, Editör, Araçlar, Docker, Canvas
- **WebSocket** tabanlı gerçek zamanlı iletişim
- **Responsive** tasarım

### 🎨 Canvas - Canlı Önizleme
- **Web Mode**: Sunucu uygulamalarını iframe'de görüntüleme
- **HTML Mode**: Workspace'deki HTML dosyalarını anında önizleme
- **VNC Mode**: GUI uygulamalarını (pygame, tkinter) noVNC ile görüntüleme
- **Entegre Terminal**: Canvas içinde Docker komutları çalıştırma

### 🐳 Docker VNC Desteği
- TigerVNC + noVNC ile GUI uygulama görüntüleme
- Otomatik sunucu algılama (Flask, FastAPI, Node.js)

### 🔄 Multi-Provider & Fallback Sistemi
10 farklı AI sağlayıcısı desteği:
- Ollama (yerel), OpenAI, Anthropic, Google, OpenRouter
- Groq, Together AI, Cerebras, xAI, HuggingFace

### 💾 Session Management
- SQLite veritabanına otomatik kayıt
- Geçmiş konuşmalara geri dönme

### 🛠️ Modüler JavaScript Mimarisi
Web UI tamamen modüler yapıya geçirildi (20+ JS modülü)

### 📱 Mobile UI & PWA Desteği
- **Progressive Web App**: Mobil cihazlarda uygulama gibi kurulabilir
- **Responsive Mobile UI**: Mobil cihazlar için optimize edilmiş arayüz
- **WebSocket wss:// Desteği**: Güvenli bağlantı desteği
- **Event-based Sync**: Tools ve Browser panelleri için gerçek zamanlı senkronizasyon
- **Offline Capable**: Service Worker ile çevrimdışı çalışabilme

> **Not**: Mobil PWA arayüzü ileride yeniden yapılandırılabilir veya doğrudan APK paketine geçilebilir.

## Web UI Özellikleri

- 🌙 Modern karanlık tema (Bento style)
- 💬 Sol panel: Sohbet geçmişi (daraltılabilir)
- 🤖 Orta panel: Ana chat alanı (streaming yanıtlar)
- 🛠️ Sağ panel: Terminal, Dosya yöneticisi, Editör, Araçlar, Canvas
- ⚙️ Ayarlar popup: Model, prompt, komut ve API key yönetimi
- 📱 Responsive tasarım

## Proje Yapısı

```
AtomAgent/
├── main.py                 # Terminal UI entry point
├── web_main.py             # Web UI entry point
├── config.py               # Merkezi konfigürasyon
├── core/                   # Agent ve provider yönetimi
├── tools/                  # Agent araçları
├── web/
│   ├── app.py              # FastAPI backend
│   ├── websocket.py        # WebSocket handler
│   ├── routes/             # API routes
│   └── static/             # Web UI (HTML, CSS, JS)
│       ├── css/mobile.css  # Mobile UI stilleri
│       ├── js/mobile.js    # Mobile UI JavaScript
│       ├── manifest.json   # PWA manifest
│       └── sw.js           # Service Worker
├── docker/                 # VNC destekli container
└── utils/                  # Yardımcı modüller
```

## Gereksinimler

- Python 3.10+
- Docker (sandbox ve VNC için)
- Ollama (yerel model için opsiyonel)

## Lisans

MIT License
