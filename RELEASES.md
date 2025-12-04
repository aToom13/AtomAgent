# AtomAgent Release Notes

## v3.0.0 - Web UI & Canvas 🎨🌐

**Release Date:** Aralık 2025

### 🚀 Büyük Güncelleme
Bu sürüm, AtomAgent'a tamamen yeni bir Web UI ekliyor. Önceki sürümlerde sadece Terminal UI (Textual) mevcuttu.

### ✨ Yeni Özellikler

#### 🌐 Modern Web UI
Sıfırdan tasarlanmış web arayüzü:
- **Bento Style** karanlık tema
- **Sol Panel**: Session geçmişi (daraltılabilir)
- **Orta Panel**: Chat alanı (streaming yanıtlar)
- **Sağ Panel**: Sekmeli araç paneli
- **Responsive** tasarım (PC, tablet, mobil)
- **WebSocket** tabanlı gerçek zamanlı iletişim

#### 🎨 Canvas - Canlı Önizleme
Agent'ın oluşturduğu uygulamaları anında görüntüleme:

**Web Mode:**
- Flask, FastAPI, Node.js sunucularını iframe'de görüntüleme
- Otomatik port algılama
- URL girişi ve yenileme

**HTML Mode:**
- Workspace'deki HTML dosyalarını anında önizleme
- Docker container dosyalarını da destekler

**VNC Mode:**
- GUI uygulamalarını (pygame, tkinter, PyQt) görüntüleme
- noVNC ile web tabanlı uzak masaüstü

**Entegre Terminal:**
- Canvas içinde Docker komutları çalıştırma
- Komut geçmişi (↑/↓ tuşları)

#### 🐳 Docker VNC Desteği
- TigerVNC sunucusu
- noVNC web client (port 16080)
- Xvfb sanal ekran
- GUI uygulamaları için tam destek

#### 🏗️ Modüler JavaScript Mimarisi
```
web/static/js/
├── app.js          # Ana uygulama
├── state.js        # Global state
├── websocket.js    # WebSocket handler
├── chat.js         # Mesajlaşma
├── canvas.js       # Canlı önizleme
├── docker.js       # Docker paneli
├── tools.js        # Araç paneli
├── sessions.js     # Oturum yönetimi
├── settings.js     # Ayarlar
├── files.js        # Dosya yöneticisi
├── attachments.js  # Dosya ekleme
├── browser.js      # Web araçları
├── memory.js       # Hafıza paneli
├── todos.js        # Todo listesi
├── tasks.js        # Görev takibi
├── thinking.js     # Düşünme göstergesi
├── ui.js           # UI yardımcıları
└── utils.js        # Genel yardımcılar
```

#### 🔧 Backend (FastAPI)
- `web/app.py` - FastAPI uygulaması
- `web/websocket.py` - WebSocket chat handler
- `web/state.py` - Global state yönetimi
- `web/routes/` - API endpoint'leri
  - `canvas.py` - Canvas ve VNC API
  - `docker.py` - Docker yönetimi
  - `workspace.py` - Dosya işlemleri

#### 📦 Sağ Panel Sekmeleri
- **Terminal**: Komut çalıştırma
- **Dosyalar**: Workspace dosya yöneticisi
- **Editör**: Kod düzenleme
- **Araçlar**: Tool çağrıları görüntüleme
- **Docker**: Container yönetimi
- **Browser**: Web araştırma sonuçları
- **Canvas**: Canlı önizleme
- **Hafıza**: Agent hafızası
- **Todos**: Görev listesi

#### ⚙️ Ayarlar Popup
- Model seçimi (provider/model)
- System prompt düzenleme
- Özel komutlar
- API key yönetimi

---

## v2.x - Terminal UI (Textual) 🖥️

**Önceki Sürümler**

Terminal tabanlı UI özellikleri:
- Textual framework ile modern terminal arayüzü
- Gruvbox tema
- Session yönetimi
- Multi-provider desteği
- Docker sandbox
- RAG sistemi
- Tool Factory

---

**Repository**: https://github.com/aToom13/AtomAgent
