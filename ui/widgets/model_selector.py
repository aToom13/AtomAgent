"""
Model Selector Widget - Modal for selecting LLM provider and model
Supports manual model input, persistent settings, and model testing
"""
import json
import os
import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, Select, Input
from textual.screen import ModalScreen

from core.providers import PROVIDERS, get_provider_names, model_manager, create_llm, check_api_key

# Settings file path
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "../../.atom_settings.json")


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


def get_api_status_text(provider: str) -> str:
    """Get detailed API status text for provider"""
    from core.providers import PROVIDERS, check_api_key, get_api_key_info
    
    config = PROVIDERS.get(provider)
    if not config:
        return "[red]✗[/red] Bilinmeyen"
    
    if provider == "ollama":
        return "[green]✓[/green] Lokal"
    
    if check_api_key(provider):
        info = get_api_key_info(provider)
        if info["total"] > 1:
            return f"[green]✓[/green] Key {info['current']}/{info['total']}"
        return "[green]✓[/green] OK"
    else:
        return f"[red]✗[/red] Key yok"


class ModelSelectorModal(ModalScreen):
    """Modal screen for selecting models for each agent role"""
    
    CSS = """
    ModelSelectorModal {
        align: center middle;
    }
    
    #model-dialog {
        width: 90;
        height: auto;
        max-height: 40;
        background: #282828;
        border: solid #fe8019;
        padding: 1 2;
    }
    
    #model-title {
        text-align: center;
        text-style: bold;
        color: #fe8019;
        padding-bottom: 1;
    }
    
    .role-section {
        height: auto;
        padding: 1 0;
        border-bottom: solid #3c3836;
    }
    
    .role-label {
        color: #b8bb26;
        text-style: bold;
    }
    
    .role-row {
        height: 3;
        layout: horizontal;
        margin-top: 1;
    }
    
    .provider-select {
        width: 22;
        margin-right: 1;
    }
    
    .model-input {
        width: 28;
    }
    
    .api-status {
        width: 18;
        margin-left: 1;
        padding-top: 1;
        color: #928374;
    }
    
    .test-btn {
        width: 10;
        margin-left: 1;
    }
    
    .test-result {
        color: #83a598;
        padding: 0 2;
        height: auto;
        max-height: 3;
    }
    
    #button-row {
        height: 3;
        align: center middle;
        padding-top: 1;
    }
    
    #button-row Button {
        margin: 0 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self._testing_role = None
    
    def compose(self) -> ComposeResult:
        with Vertical(id="model-dialog"):
            yield Static("🤖 Model Ayarları", id="model-title")
            
            for role in model_manager.ROLES:
                config = model_manager.get_config(role)
                role_display = {
                    "supervisor": "🎯 Supervisor",
                    "coder": "💻 Coder", 
                    "researcher": "🔍 Researcher"
                }
                
                with Vertical(classes="role-section"):
                    yield Static(f"{role_display[role]}", classes="role-label")
                    
                    with Horizontal(classes="role-row"):
                        provider_options = [(PROVIDERS[p].name, p) for p in get_provider_names()]
                        yield Select(
                            provider_options,
                            value=config.provider,
                            id=f"provider-{role}",
                            classes="provider-select"
                        )
                        
                        yield Input(
                            value=config.model,
                            placeholder="Model adı...",
                            id=f"model-{role}",
                            classes="model-input"
                        )
                        
                        status_text = get_api_status_text(config.provider)
                        yield Static(status_text, classes="api-status", id=f"api-{role}")
                        
                        yield Button("🧪 Test", id=f"test-{role}", classes="test-btn", variant="primary")
                    
                    # Test sonucu alanı
                    yield Static("", classes="test-result", id=f"result-{role}")
            
            with Horizontal(id="button-row"):
                yield Button("💾 Kaydet", id="btn-save", variant="success")
                yield Button("❌ Çık", id="btn-cancel", variant="error")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        select_id = event.select.id
        
        if not select_id or event.value is None:
            return
            
        if select_id.startswith("provider-"):
            role = select_id.replace("provider-", "")
            new_provider = event.value
            
            status_text = get_api_status_text(new_provider)
            self.query_one(f"#api-{role}", Static).update(status_text)
            # Test sonucunu temizle
            self.query_one(f"#result-{role}", Static).update("")
    
    async def _test_model(self, role: str):
        """Test the model with a simple prompt"""
        provider = self.query_one(f"#provider-{role}", Select).value
        model = self.query_one(f"#model-{role}", Input).value.strip()
        result_widget = self.query_one(f"#result-{role}", Static)
        
        if not provider or not model:
            result_widget.update("[red]Provider veya model seçilmedi[/red]")
            return
        
        result_widget.update("[yellow]⏳ Test ediliyor...[/yellow]")
        
        try:
            # Create LLM instance
            llm = create_llm(provider, model, temperature=0.7)
            
            if not llm:
                result_widget.update("[red]✗ Model oluşturulamadı (API key kontrol edin)[/red]")
                return
            
            # Test prompt
            from langchain_core.messages import HumanMessage
            response = await asyncio.to_thread(
                llm.invoke,
                [HumanMessage(content="Sadece şunu söyle: 'Selam! Ben [model adın] modeliyim ve çalışıyorum!' - Kısa tut.")]
            )
            
            # Show response
            answer = response.content[:100] if len(response.content) > 100 else response.content
            result_widget.update(f"[green]✓[/green] {answer}")
            
        except Exception as e:
            error_msg = str(e)[:60]
            result_widget.update(f"[red]✗ Hata: {error_msg}[/red]")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        # Test butonları
        if btn_id and btn_id.startswith("test-"):
            role = btn_id.replace("test-", "")
            self.run_worker(self._test_model(role))
            return
        
        if btn_id == "btn-save":
            settings = {"models": {}}
            
            for role in model_manager.ROLES:
                provider = self.query_one(f"#provider-{role}", Select).value
                model = self.query_one(f"#model-{role}", Input).value.strip()
                
                if provider and model:
                    model_manager.set_model(role, provider, model)
                    settings["models"][role] = {
                        "provider": provider,
                        "model": model,
                        "temperature": model_manager.get_config(role).temperature
                    }
            
            save_settings(settings)
            self.app.notify("✓ Model ayarları kaydedildi!", severity="information")
            self.dismiss(True)
        
        elif btn_id == "btn-cancel":
            self.dismiss(False)
