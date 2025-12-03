# AtomAgent

AI-Powered Development Assistant

## Nedir?

AtomAgent, doğal dil ile verdiğiniz görevleri anlayan ve çözen tam otonom bir AI asistanıdır. Textual tabanlı modern terminal arayüzü ile kod yazma, dosya yönetimi, web araştırması ve Docker sandbox desteği sunar.

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

```bash
python main.py
```

## Özellikler

### 🤖 Multi-Agent Sistemi
- **Supervisor**: Ana orchestrator, görevleri yönetir ve koordine eder
- **Coder**: Kod yazma, düzenleme, test ve lint
- **Researcher**: Web araştırması ve bilgi toplama

### 🔄 Multi-Provider & Fallback Sistemi
10 farklı AI sağlayıcısı desteği:
- Ollama (yerel), OpenAI, Anthropic, Google, OpenRouter
- Groq, Together AI, Cerebras, xAI, HuggingFace

Özellikler:
- Birden fazla API key desteği (virgülle ayrılmış)
- Rate limit durumunda otomatik key rotasyonu
- Provider fallback - bir provider başarısız olursa otomatik geçiş

### 💾 Session Management
- Tüm konuşmalar SQLite veritabanına otomatik kaydedilir
- Geçmiş konuşmalara geri dönebilme
- Session arama ve filtreleme
- JSON export/import desteği

### 🐳 Docker Sandbox
İzole çalışma ortamı:
- Ubuntu container ile tam terminal erişimi
- Selenium, Playwright kurulu (web scraping)
- Sudo yetkili, kısıtlamasız komut çalıştırma
- Host ile senkronize shared klasör

### 🔧 Tool Factory
Agent kendi yeteneklerini genişletebilir:
- Runtime'da yeni tool oluşturma
- Host veya Sandbox modunda çalıştırma
- Kalıcı tool registry

### 🧠 RAG Sistemi
- Kod tabanını vektör veritabanına indeksleme
- Anlamsal kod araması
- ChromaDB + Ollama embeddings

### 📊 Diğer Özellikler
- Git entegrasyonu (init, status, add, commit, log, diff, branch, stash)
- Test runner (pytest)
- Kod kalite kontrolü (ruff ile lint ve format)
- Todo/Plan yönetimi
- Debug paneli
- Kod highlighting

## Kısayollar

| Kısayol | Açıklama |
|---------|----------|
| `Ctrl+C` | Çıkış (2 kez bas) |
| `Ctrl+S` | Dosya kaydet |
| `Ctrl+L` | Chat temizle / Yeni session |
| `Ctrl+R` | Workspace yenile |
| `Ctrl+Y` | Son yanıtı kopyala |
| `Ctrl+D` | Debug paneli |
| `Ctrl+H` | Konuşma geçmişi |
| `Ctrl+N` | Yeni session |
| `Ctrl+B` | Sidebar aç/kapat |
| `F5` | Dosya çalıştır |

## Özel Komutlar

| Komut | Açıklama |
|-------|----------|
| `:model` | Model ayarları |
| `:fallback` | Yedek provider ayarları |
| `:keys` | API key durumu |
| `:reset` | Tüm provider'ları sıfırla |
| `:history` | Konuşma geçmişi |
| `:new` | Yeni session |
| `:rename <başlık>` | Session yeniden adlandır |
| `:export` | Session'ı JSON export |
| `:sandbox` | Sandbox paneli |
| `:tools` | Tool Factory paneli |
| `:memory` | Hafıza durumu |
| `:help` | Yardım |

## Proje Yapısı

```
AtomAgent/
├── main.py                 # Giriş noktası
├── config.py               # Merkezi konfigürasyon
├── core/
│   ├── agent.py            # Ana agent orchestrator
│   ├── providers.py        # LLM provider yönetimi
│   └── session_manager.py  # Session yönetimi (SQLite)
├── tools/
│   ├── agents.py           # Sub-agent tool'ları
│   ├── files.py            # Dosya işlemleri
│   ├── execution.py        # Terminal komutları
│   ├── web.py              # Web araştırma
│   ├── rag.py              # RAG sistemi
│   ├── git_tools.py        # Git entegrasyonu
│   ├── test_tools.py       # Test runner
│   ├── quality.py          # Lint ve kalite
│   ├── memory.py           # Context hafızası
│   ├── sandbox.py          # Docker sandbox
│   ├── tool_factory.py     # Dinamik tool oluşturma
│   ├── session_tools.py    # Session araçları
│   └── todo_tools.py       # Plan/Todo yönetimi
├── prompts/                # Agent prompt'ları (TXT/JSON)
├── ui/
│   ├── app.py              # Ana Textual uygulaması
│   ├── styles.py           # Gruvbox tema
│   ├── handlers/           # Event handler'lar
│   └── widgets/            # UI widget'ları
├── docker/
│   ├── Dockerfile          # Sandbox container
│   ├── docker-compose.yml
│   └── shared/             # Host-container senkron klasör
└── utils/
    └── logger.py           # Loglama sistem
```

## Gereksinimler

- Python 3.10+
- Docker (sandbox için opsiyonel)
- Ollama (yerel model için opsiyonel)
