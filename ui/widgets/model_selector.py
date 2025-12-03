"""
Model Selector Widget - Clean Modal for LLM Configuration
v2.1 - Reads from .atom_settings.json, all 6 roles
"""
import json
import os
import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Select, Input
from textual.screen import ModalScreen

from core.providers import PROVIDERS, get_provider_names, model_manager, create_llm, check_api_key

# Settings file in project root (not workspace)
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".atom_settings.json")


def load_settings() -> dict:
    """Load settings from JSON file"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_settings(settings: dict):
    """Save settings to JSON file"""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Settings save error: {e}")


def apply_saved_settings():
    """Apply saved settings to model_manager on startup"""
    settings = load_settings()
    models = settings.get("models", {})
    
    for role in model_manager.ROLES:
        if role in models:
            cfg = models[role]
            model_manager.set_model(
                role, 
                cfg.get("provider", "ollama"),
                cfg.get("model", "llama3.2"),
                cfg.get("temperature", 0.0)
            )


def get_model_from_settings(role: str) -> tuple:
    """Get provider and model from .atom_settings.json"""
    settings = load_settings()
    models = settings.get("models", {})
    if role in models:
        return models[role].get("provider", "ollama"), models[role].get("model", "llama3.2")
    # Fallback to model_manager defaults
    cfg = model_manager.get_config(role)
    return cfg.provider, cfg.model


def get_api_status(provider: str) -> tuple:
    """Get API status icon and text"""
    from core.providers import get_api_key_info
    
    if provider == "ollama":
        return "🟢", "Lokal"
    
    if check_api_key(provider):
        info = get_api_key_info(provider)
        if info["total"] > 1:
            return "🟢", f"Key {info['current']}/{info['total']}"
        return "🟢", "OK"
    return "🔴", "Key yok"


ROLE_INFO = {
    "supervisor": ("🎯", "Supervisor", "Ana koordinatör"),
    "coder": ("💻", "Coder", "Kod yazma"),
    "researcher": ("🔍", "Researcher", "Araştırma"),
    "vision": ("👁️", "Vision", "Görüntü analizi"),
    "audio": ("🎤", "Audio", "Ses tanıma"),
    "tts": ("🔊", "TTS", "Metin okuma")
}

# Tüm roller
ALL_ROLES = ["supervisor", "coder", "researcher", "vision", "audio", "tts"]


class ModelSelectorModal(ModalScreen):
    """Modern modal for model selection - all 6 roles"""
    
    BINDINGS = [("escape", "cancel", "Kapat")]
    
    def compose(self) -> ComposeResult:
        with Vertical(id="model-modal"):
            # Header
            with Horizontal(id="model-modal-header"):
                yield Static("🤖 Model Ayarları", id="model-modal-title")
                yield Button("✕", id="btn-close", variant="error")
            
            # Info
            yield Static(
                "[dim]Her rol için provider ve model seçin. Ayarlar .atom_settings.json'a kaydedilir.[/dim]",
                id="model-modal-info"
            )
            
            # Model List - All 6 roles
            with VerticalScroll(id="model-list"):
                for role in ALL_ROLES:
                    provider, model = get_model_from_settings(role)
                    icon, name, desc = ROLE_INFO[role]
                    status_icon, status_text = get_api_status(provider)
                    
                    # Multimodal roller için farklı stil
                    card_class = "model-card" if role in ["supervisor", "coder", "researcher"] else "model-card model-card-secondary"
                    
                    with Vertical(classes=card_class):
                        # Card Header
                        with Horizontal(classes="model-card-header"):
                            yield Static(f"{icon} {name}", classes="model-card-title")
                            yield Static(f"{status_icon} {status_text}", id=f"status-{role}", classes="model-card-status")
                        
                        # Provider Row
                        with Horizontal(classes="model-card-row"):
                            yield Static("Provider:", classes="model-label")
                            provider_opts = [(PROVIDERS[p].name, p) for p in get_provider_names()]
                            yield Select(
                                provider_opts,
                                value=provider,
                                id=f"provider-{role}",
                                classes="model-select"
                            )
                        
                        # Model Row
                        with Horizontal(classes="model-card-row"):
                            yield Static("Model:", classes="model-label")
                            yield Input(
                                value=model,
                                placeholder="Model adı...",
                                id=f"model-{role}",
                                classes="model-input"
                            )
                        
                        # Test Button (sadece ana roller için)
                        if role in ["supervisor", "coder", "researcher"]:
                            with Horizontal(classes="model-card-actions"):
                                yield Button("🧪 Test", id=f"test-{role}", variant="default", classes="test-btn")
                                yield Static("", id=f"result-{role}", classes="test-result")
            
            # Footer Buttons
            with Horizontal(id="model-modal-footer"):
                yield Button("💾 Kaydet", id="btn-save", variant="success")
                yield Button("İptal", id="btn-cancel", variant="default")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Provider değiştiğinde status güncelle"""
        if not event.select.id or not event.select.id.startswith("provider-"):
            return
        
        role = event.select.id.replace("provider-", "")
        provider = event.value
        
        # Status güncelle
        status_icon, status_text = get_api_status(provider)
        try:
            self.query_one(f"#status-{role}", Static).update(f"{status_icon} {status_text}")
            # Test sonucunu temizle
            result = self.query_one(f"#result-{role}", Static)
            result.update("")
        except:
            pass
        
        # Default model öner (sadece boşsa)
        provider_cfg = PROVIDERS.get(provider)
        if provider_cfg and provider_cfg.default_model:
            try:
                model_input = self.query_one(f"#model-{role}", Input)
                if not model_input.value:
                    model_input.value = provider_cfg.default_model
            except:
                pass
    
    async def _test_model(self, role: str):
        """Model bağlantısını test et"""
        try:
            provider = self.query_one(f"#provider-{role}", Select).value
            model = self.query_one(f"#model-{role}", Input).value.strip()
            result_widget = self.query_one(f"#result-{role}", Static)
        except:
            return
        
        if not provider or not model:
            self.app.notify("Provider veya model eksik", severity="error")
            return
        
        result_widget.update("⏳")
        
        try:
            llm = create_llm(provider, model, temperature=0.7)
            if not llm:
                result_widget.update("❌")
                self.app.notify("Model oluşturulamadı", severity="error")
                return
            
            from langchain_core.messages import HumanMessage
            response = await asyncio.to_thread(
                llm.invoke,
                [HumanMessage(content="Say 'OK' only.")]
            )
            
            result_widget.update("✅")
            self.app.notify(f"✓ {role}: {response.content.strip()[:30]}", severity="information")
            
        except Exception as e:
            result_widget.update("❌")
            self.app.notify(f"Hata: {str(e)[:80]}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        # Test butonları
        if btn_id and btn_id.startswith("test-"):
            role = btn_id.replace("test-", "")
            self.run_worker(self._test_model(role))
            return
        
        if btn_id == "btn-save":
            self._save_settings()
        elif btn_id in ["btn-cancel", "btn-close"]:
            self.dismiss(False)
    
    def action_cancel(self):
        self.dismiss(False)
    
    def _save_settings(self):
        """Ayarları .atom_settings.json'a kaydet"""
        # Mevcut ayarları yükle (temperature gibi değerleri korumak için)
        settings = load_settings()
        if "models" not in settings:
            settings["models"] = {}
        
        for role in ALL_ROLES:
            try:
                provider = self.query_one(f"#provider-{role}", Select).value
                model = self.query_one(f"#model-{role}", Input).value.strip()
            except:
                continue
            
            if provider and model:
                # Mevcut temperature'ı koru
                old_temp = settings.get("models", {}).get(role, {}).get("temperature", 0.0)
                
                model_manager.set_model(role, provider, model)
                settings["models"][role] = {
                    "provider": provider,
                    "model": model,
                    "temperature": old_temp
                }
        
        save_settings(settings)
        self.app.notify("✓ Model ayarları kaydedildi!", severity="information")
        self.dismiss(True)
