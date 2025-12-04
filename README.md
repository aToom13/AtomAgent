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

### Terminal UI (Textual)
```bash
python main.py
```

### Web UI (Modern Dark Theme)
```bash
python web_main.py
```
Tarayıcınızda `http://localhost:8000` adresine gidin.

Web UI özellikleri:
- 🌙 Modern karanlık tema (Bento style)
- 💬 Sol panel: Sohbet geçmişi (daraltılabilir)
- 🤖 Orta panel: Ana chat alanı (streaming yanıtlar)
- 🛠️ Sağ panel: Terminal, Dosya yöneticisi, Editör, Araçlar
- ⚙️ Ayarlar popup: Model, prompt, komut ve API key yönetimi
- 📱 Responsive tasarım (PC, tablet, mobil uyumlu)

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

### 🧪 Auto-Test Generation
- Modül analizi ile otomatik test oluşturma
- Coverage analizi ve raporlama
- pytest entegrasyonu

### 🧠 Persistent Learning Memory
- Projeler arası öğrenme
- Kullanıcı tercihlerini hatırlama
- Başarılı/başarısız pattern'leri kaydetme
- Hatalardan öğrenme ve çözüm önerisi

### 📈 Self-Improvement
- Performans takibi ve raporlama
- Başarı oranı analizi
- İyileştirme önerileri

### 🖼️ Multi-Modal Destek
- Görüntü analizi (Vision API)
- Ekran görüntüsü analizi
- Diyagram ve kod screenshot analizi
- Ses transkripti (Whisper)
- Text-to-Speech

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
├── web/
│   ├── api.py              # FastAPI backend
│   └── static/             # Web UI dosyaları
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── web_main.py             # Web UI entry point
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

## Changelog

### v4.3 (Aralık 2024)

#### Yeni Özellikler

**1. Gelişmiş Prompt Engineering**
- Chain of Thought (CoT) yaklaşımı eklendi
- Hata kurtarma stratejileri prompt'a entegre edildi
- Öğrenme ve performans takibi talimatları eklendi

**2. Streaming & Async Desteği**
- `utils/streaming.py`: Async streaming response desteği
- Daha iyi UX için token-by-token streaming
- Paralel görev çalıştırma desteği

**3. Context Window Yönetimi**
- `utils/context_manager.py`: Akıllı context sıkıştırma
- Model bazlı token limitleri
- Otomatik mesaj özetleme
- Tool output truncation

**4. Gelişmiş Retry Mekanizması**
- `utils/retry.py`: Exponential backoff ile retry
- Tenacity entegrasyonu (opsiyonel)
- Rate limit ve server error handling
- RetryContext context manager

**5. Response Caching**
- `utils/cache.py`: LLM response caching
- Embedding cache (maliyet azaltma)
- TTL ve LRU eviction
- Persistent cache (disk'e kayıt)

**6. Gelişmiş RAG (Hybrid Search)**
- Semantic + Keyword hybrid search
- Cross-encoder reranking (opsiyonel)
- Kod elementi extraction (functions, classes)
- Cached embeddings
- `search_functions` tool eklendi

**7. İyileştirilmiş Tool Descriptions**
- Daha spesifik kullanım talimatları
- KULLAN/KULLANMA örnekleri
- Daha iyi tool seçimi için rehberlik

**8. Telemetry & Observability**
- `utils/telemetry.py`: Distributed tracing
- Performance monitoring
- Debug context
- Tool call tracing

**9. Test Coverage**
- `tests/` dizini eklendi
- Provider testleri
- Tool testleri
- Utility testleri
- pytest fixtures

#### Yeni Dosyalar
```
utils/
├── __init__.py
├── cache.py           # Response & embedding cache
├── context_manager.py # Context window management
├── retry.py           # Retry with backoff
├── streaming.py       # Async streaming support
└── telemetry.py       # Tracing & monitoring

tests/
├── __init__.py
├── conftest.py        # Pytest fixtures
├── test_agent.py
├── test_providers.py
├── test_utils.py
└── test_tools/
    ├── __init__.py
    ├── test_files.py
    └── test_execution.py
```

#### Yeni Bağımlılıklar
```
tenacity>=8.2.0              # Retry with exponential backoff
tiktoken>=0.5.0              # Token counting
sentence-transformers>=2.2.0 # Reranking (optional)
pytest>=7.0.0                # Testing
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
```
