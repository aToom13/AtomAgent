# AtomAgent Release Notes

## v2.0.0 - Complete CLI Rewrite 🚀

**Release Date:** December 2024

Bu sürüm, AtomAgent'ın tamamen sıfırdan yeniden yazılmış, CLI odaklı versiyonudur. Daha stabil, modüler ve genişletilebilir bir mimari ile geliştirilmiştir.

---

### ✨ Öne Çıkan Özellikler

#### 🤖 Çoklu AI Provider Desteği
AtomAgent artık 10 farklı AI sağlayıcısını destekliyor:
- **OpenAI** (GPT-4, GPT-4o)
- **Anthropic** (Claude 3.5 Sonnet)
- **Google** (Gemini 1.5)
- **OpenRouter** (100+ model erişimi)
- **Cerebras** (Ultra-hızlı inference)
- **xAI** (Grok)
- **Groq** (Düşük latency)
- **Together AI**
- **HuggingFace**
- **Ollama** (Yerel modeller)

#### 🔄 Akıllı API Key Rotasyonu
- Birden fazla API key desteği (virgülle ayrılmış)
- Rate limit durumunda otomatik key rotasyonu
- Fallback provider sistemi - bir provider başarısız olursa otomatik geçiş

#### 🧠 Multi-Agent Mimarisi
Üç özelleşmiş agent ile görev dağılımı:
- **Supervisor**: Ana orkestratör, görevleri yönetir ve koordine eder
- **Coder**: Kod yazma, dosya işlemleri, test ve lint
- **Researcher**: Web araştırması, dokümantasyon tarama, RAG sorguları

---

### 🛠️ Araç Sistemi (Tools)

#### Dosya İşlemleri (`tools/files.py`)
- `write_file` - Dosya oluşturma/güncelleme
- `read_file` - Dosya okuma
- `list_files` - Dizin listeleme
- `scan_workspace` - Workspace tarama (ağaç görünümü)
- `create_directory` - Klasör oluşturma
- `delete_file` / `delete_directory` - Silme işlemleri

#### Terminal Yürütme (`tools/execution.py`)
- Güvenli komut çalıştırma sistemi
- İzin verilen komutlar whitelist'i
- Tehlikeli pattern engelleme
- Timeout koruması
- Runtime'da izin ekleme desteği

#### Git Entegrasyonu (`tools/git_tools.py`)
- `git_init`, `git_status`, `git_add`, `git_commit`
- `git_log`, `git_diff`, `git_branch`
- `git_stash`, `git_reset`
- Türkçe durum mesajları

#### Web Araçları (`tools/web.py`)
- `web_search` - DuckDuckGo ile web araması
- `quick_answer` - Hızlı cevap API'si
- `visit_webpage` - Sayfa içeriği çıkarma
- `search_docs` - Dokümantasyon araması (Python, MDN, npm, GitHub)
- Güvenilir kaynak önceliklendirme
- Spam site filtreleme

#### RAG Sistemi (`tools/rag.py`)
- `refresh_memory` - Kod tabanını vektör veritabanına indeksleme
- `search_codebase` - Anlamsal kod araması
- ChromaDB + Ollama embeddings (nomic-embed-text)
- Desteklenen formatlar: `.py`, `.js`, `.ts`, `.md`, `.json`, `.yaml`, `.html`, `.css`

#### Test Araçları (`tools/test_tools.py`)
- `run_tests` - pytest ile test çalıştırma
- `run_single_test` - Tekil test çalıştırma
- `create_test_file` - Test şablonu oluşturma
- `list_tests` - Mevcut testleri listeleme
- `test_coverage` - Coverage raporu

#### Kalite Kontrol (`tools/quality.py`)
- `lint_and_fix` - Ruff ile otomatik formatlama ve lint
- `check_syntax` - Python syntax kontrolü
- PEP-8 uyumlu kod formatlama

#### Todo Yönetimi (`tools/todo_tools.py`)
- `create_plan` - Görev planı oluşturma
- `update_todo_list` - Todo güncelleme
- `mark_todo_done` - Adım tamamlama
- `get_next_todo_step` - Sıradaki adımı gösterme
- Markdown checkbox formatı

---

### ⚙️ Teknik Detaylar

#### Mimari
```
AtomAgent/
├── main.py              # Giriş noktası
├── config.py            # Merkezi konfigürasyon
├── core/
│   ├── agent.py         # Ana agent orchestrator
│   └── providers.py     # LLM provider yönetimi
├── tools/               # Modüler araç sistemi
├── prompts/             # JSON tabanlı prompt'lar
├── ui/                  # Gradio arayüzü
└── utils/               # Logger ve yardımcılar
```

#### Kullanılan Teknolojiler
- **LangChain** - LLM framework
- **LangGraph** - Agent orchestration
- **Gradio** - Web UI
- **ChromaDB** - Vektör veritabanı
- **Ruff** - Python linter/formatter
- **DuckDuckGo Search** - Web araması
- **BeautifulSoup** - HTML parsing

#### Konfigürasyon Sistemi (`config.py`)
- Dataclass tabanlı tip güvenli konfigürasyon
- Model, execution, workspace, memory ve UI ayarları
- Merkezi yönetim

#### Prompt Yönetimi
- JSON dosyalarında saklanan prompt'lar
- Versiyon takibi
- Kolay güncelleme ve özelleştirme

---

### 🔒 Güvenlik Özellikleri

- Workspace sandbox - dosya işlemleri sadece belirlenen dizinde
- Komut whitelist sistemi
- Tehlikeli pattern engelleme (`rm -rf /`, `sudo`, vb.)
- API key'lerin `.env` dosyasında güvenli saklanması
- Path traversal koruması

---

### 📋 Gereksinimler

```
langchain>=0.3.0
langgraph>=0.2.0
langchain-ollama
langchain-openai
langchain-anthropic
langchain-google-genai
langchain-groq
langchain-chroma
gradio>=4.0.0
duckduckgo-search
beautifulsoup4
requests
python-dotenv
ruff
pytest
```

---

### 🚀 Hızlı Başlangıç

1. Repoyu klonlayın
2. `.env.example` dosyasını `.env` olarak kopyalayın
3. API key'lerinizi ekleyin
4. `pip install -r requirements.txt`
5. `python main.py`

---

### 🔮 Gelecek Planları

- [ ] Daha fazla provider desteği
- [ ] Plugin sistemi
- [ ] Proje şablonları
- [ ] Gelişmiş memory yönetimi
- [ ] Multi-modal destek (görsel analiz)

---

### 📝 Notlar

- Ollama kurulu ise yerel modeller ücretsiz kullanılabilir
- OpenRouter ile 100+ modele tek API key ile erişim
- Rate limit durumunda otomatik fallback çalışır
- Workspace dışına dosya erişimi engellenir

---

**Full Changelog**: İlk major release - Complete rewrite from scratch

