# AtomAgent Release Notes

## v4.2.0 - Session Tools & Stability 🔧

**Release Date:** December 2025

### Yenilikler
- Session tools agent'a eklendi (list_recent_sessions, search_conversations, get_session_summary, get_session_stats)
- Agent artık geçmiş konuşmaları arayabilir ve özetleyebilir

### Düzeltmeler
- Kullanılmayan dosyalar temizlendi (dev_mode.py, ide_styles.py)

---

## v4.1.0 - Tool Factory & Sandbox 🐳

**Release Date:** December 2025

### ✨ Öne Çıkan Özellikler

#### 🔧 Tool Factory
Agent kendi yeteneklerini genişletebilir:
- `create_tool` - Runtime'da yeni Python tool oluşturma
- Host veya Sandbox modunda çalıştırma seçeneği
- Kalıcı tool registry (.custom_tools/)
- `list_custom_tools`, `delete_tool`, `test_tool` araçları

#### 🐳 Docker Sandbox
İzole çalışma ortamı:
- Ubuntu 22.04 container
- Selenium, Playwright, Chromium kurulu
- Sudo yetkili, kısıtlamasız komut çalıştırma
- `/home/agent/shared` klasörü host ile senkron
- `sandbox_start`, `sandbox_stop`, `sandbox_shell`, `sandbox_upload`, `sandbox_download`

#### 💾 Session Management
- SQLite tabanlı kalıcı konuşma geçmişi
- Session sidebar (Ctrl+B ile aç/kapat)
- Session arama ve filtreleme
- JSON export/import
- Otomatik başlık oluşturma

#### 🧠 Memory Sistemi
- Uzun görevlerde context koruma
- `save_context`, `get_context_info` araçları
- Otomatik conversation summarization
- Task tracking

---

## v4.0.0 - Multi-Provider & Fallback 🔄

**Release Date:** December 2025

### ✨ Öne Çıkan Özellikler

#### 🤖 10 AI Provider Desteği
- Ollama (yerel)
- OpenAI
- Anthropic (Claude)
- Google (Gemini)
- OpenRouter
- Groq
- Together AI
- Cerebras
- xAI (Grok)
- HuggingFace

#### 🔄 Akıllı API Key Rotasyonu
- Birden fazla API key desteği (virgülle ayrılmış)
- Rate limit durumunda otomatik key rotasyonu
- Provider fallback sistemi

#### 🎨 Textual UI
- Modern terminal arayüzü (Gruvbox tema)
- Tabbed interface (Dashboard, Editor, Sandbox, Tools, Debug)
- Session sidebar
- Kod highlighting
- Debug paneli

---

## v3.0.0 - RAG & Quality Tools 🧠

### Özellikler
- RAG sistemi (ChromaDB + Ollama embeddings)
- `search_codebase` - Anlamsal kod araması
- `refresh_memory` - Kod tabanı indeksleme
- `lint_and_fix` - Ruff ile otomatik formatlama
- `check_syntax` - Python syntax kontrolü
- `self_evaluate`, `analyze_error` - Otonom hata kurtarma

---

## v2.0.0 - Complete CLI Rewrite 🚀

**Release Date:** December 2025

Bu sürüm, AtomAgent'ın tamamen sıfırdan yeniden yazılmış versiyonudur.

### 🛠️ Araç Sistemi

#### Dosya İşlemleri
- `write_file`, `read_file`, `list_files`, `scan_workspace`
- `create_directory`, `delete_file`, `delete_directory`

#### Terminal Yürütme
- Güvenli komut çalıştırma (whitelist sistemi)
- Tehlikeli pattern engelleme
- Timeout koruması

#### Git Entegrasyonu
- `git_init`, `git_status`, `git_add`, `git_commit`
- `git_log`, `git_diff`, `git_branch`, `git_stash`, `git_reset`

#### Web Araçları
- `web_search` - DuckDuckGo araması
- `quick_answer` - Hızlı cevap
- `visit_webpage` - Sayfa içeriği çıkarma
- `search_docs` - Dokümantasyon araması

#### Test Araçları
- `run_tests`, `run_single_test`
- `create_test_file`, `list_tests`
- `test_coverage`

#### Todo Yönetimi
- `create_plan`, `update_todo_list`
- `mark_todo_done`, `get_next_todo_step`

### 🔒 Güvenlik
- Workspace sandbox
- Komut whitelist sistemi
- Path traversal koruması
- API key'lerin .env'de güvenli saklanması

---

## Gereksinimler

```
langchain>=0.3.0
langgraph>=0.2.0
langchain-ollama>=0.2.0
langchain-openai>=0.2.0
langchain-anthropic>=0.3.0
langchain-google-genai>=2.0.0
langchain-groq>=0.2.0
langchain-huggingface>=0.1.0
langchain-chroma>=0.1.0
chromadb>=0.5.0
textual>=0.89.0
rich>=13.0.0
duckduckgo-search>=6.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
python-dotenv>=1.0.0
ruff>=0.8.0
pydantic>=2.0.0
```

---

**Repository**: https://github.com/aToom13/AtomAgent
