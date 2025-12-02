"""
Fallback Selector Widget - Modal for configuring fallback providers
"""
import json
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Select, Input, Label
from textual.screen import ModalScreen

from core.providers import PROVIDERS, get_provider_names, model_manager, check_api_key


class FallbackSelectorModal(ModalScreen):
    """Modal for configuring fallback providers for each role"""
    
    CSS = """
    FallbackSelectorModal {
        align: center middle;
    }
    
    #fallback-dialog {
        width: 95;
        height: auto;
        max-height: 70;
        background: #282828;
        border: solid #d79921;
        padding: 1 2;
        overflow-y: auto;
    }
    
    #fallback-title {
        text-align: center;
        text-style: bold;
        color: #d79921;
        padding-bottom: 1;
    }
    
    .role-section {
        height: auto;
        padding: 1 0;
        border-bottom: solid #3c3836;
    }
    
    .role-header {
        color: #b8bb26;
        text-style: bold;
    }
    
    .primary-info {
        color: #83a598;
        padding: 0 2;
    }
    
    .fallback-row {
        height: 3;
        layout: horizontal;
        margin-top: 1;
    }
    
    .fallback-label {
        width: 12;
        padding-top: 1;
        color: #fabd2f;
    }
    
    .fb-provider-select {
        width: 22;
        margin-right: 1;
    }
    
    .fb-model-input {
        width: 30;
    }
    
    .fb-status {
        width: 15;
        margin-left: 1;
        padding-top: 1;
    }
    
    #button-row {
        height: 3;
        align: center middle;
        padding-top: 1;
    }
    
    #button-row Button {
        margin: 0 1;
    }
    
    .hint-text {
        color: #928374;
        text-style: italic;
        padding: 1 0;
    }
    """
    
    MAX_FALLBACKS = 6  # Maximum fallback providers per role
    
    def compose(self) -> ComposeResult:
        with Vertical(id="fallback-dialog"):
            yield Static("🔄 Yedek Provider Ayarları", id="fallback-title")
            yield Static(
                "Ana provider hata verdiğinde sırayla yedeklere geçilir",
                classes="hint-text"
            )
            
            for role in model_manager.ROLES:
                config = model_manager.get_config(role)
                fallbacks = model_manager.get_fallbacks(role)
                role_display = {
                    "supervisor": "🎯 Supervisor",
                    "coder": "💻 Coder",
                    "researcher": "🔍 Researcher",
                    "vision": "👁️ Vision",
                    "audio": "🎤 Audio",
                    "tts": "🗣️ TTS"
                }
                
                with Vertical(classes="role-section"):
                    yield Static(f"{role_display[role]}", classes="role-header")
                    yield Static(
                        f"  Ana: {config.provider}/{config.model}",
                        classes="primary-info"
                    )
                    
                    # Fallback rows
                    for i in range(self.MAX_FALLBACKS):
                        fb_provider = fallbacks[i].provider if i < len(fallbacks) else "ollama"
                        fb_model = fallbacks[i].model if i < len(fallbacks) else ""
                        
                        with Horizontal(classes="fallback-row"):
                            yield Static(f"Yedek {i+1}:", classes="fallback-label")
                            
                            provider_options = [(PROVIDERS[p].name, p) for p in get_provider_names()]
                            yield Select(
                                provider_options,
                                value=fb_provider,
                                id=f"fb-provider-{role}-{i}",
                                classes="fb-provider-select"
                            )
                            
                            yield Input(
                                value=fb_model,
                                placeholder="Model adı (boş = devre dışı)",
                                id=f"fb-model-{role}-{i}",
                                classes="fb-model-input"
                            )
                            
                            status = self._get_status(fb_provider)
                            yield Static(status, classes="fb-status", id=f"fb-status-{role}-{i}")
            
            with Horizontal(id="button-row"):
                yield Button("💾 Kaydet", id="btn-save", variant="success")
                yield Button("🔄 Sıfırla", id="btn-reset", variant="warning")
                yield Button("❌ Çık", id="btn-cancel", variant="error")
    
    def _get_status(self, provider: str) -> str:
        from core.providers import get_api_key_info
        
        if provider == "ollama":
            return "[green]✓[/green] Lokal"
        if check_api_key(provider):
            info = get_api_key_info(provider)
            if info["total"] > 1:
                return f"[green]✓[/green] {info['total']} key"
            return "[green]✓[/green] OK"
        return "[red]✗[/red] Yok"
    
    def on_select_changed(self, event: Select.Changed) -> None:
        select_id = event.select.id
        if not select_id or not select_id.startswith("fb-provider-"):
            return
        
        # Parse: fb-provider-{role}-{index}
        parts = select_id.replace("fb-provider-", "").rsplit("-", 1)
        if len(parts) != 2:
            return
        
        role, idx = parts[0], parts[1]
        new_provider = event.value
        
        # Update status
        status = self._get_status(new_provider)
        try:
            self.query_one(f"#fb-status-{role}-{idx}", Static).update(status)
        except:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "btn-save":
            self._save_fallbacks()
            self.app.notify("✓ Yedek provider ayarları kaydedildi!", severity="information")
            self.dismiss(True)
        
        elif btn_id == "btn-reset":
            self._reset_fallbacks()
            self.app.notify("Yedek ayarları sıfırlandı", severity="warning")
        
        elif btn_id == "btn-cancel":
            self.dismiss(False)
    
    def _save_fallbacks(self):
        """Save fallback settings for all roles"""
        for role in model_manager.ROLES:
            fallbacks = []
            
            for i in range(self.MAX_FALLBACKS):
                try:
                    provider = self.query_one(f"#fb-provider-{role}-{i}", Select).value
                    model = self.query_one(f"#fb-model-{role}-{i}", Input).value.strip()
                    
                    # Only add if model is specified
                    if model:
                        fallbacks.append((provider, model))
                except:
                    pass
            
            model_manager.set_fallbacks(role, fallbacks)
    
    def _reset_fallbacks(self):
        """Reset all fallback inputs"""
        for role in model_manager.ROLES:
            for i in range(self.MAX_FALLBACKS):
                try:
                    self.query_one(f"#fb-provider-{role}-{i}", Select).value = "ollama"
                    self.query_one(f"#fb-model-{role}-{i}", Input).value = ""
                    self.query_one(f"#fb-status-{role}-{i}", Static).update("[green]✓[/green] Lokal")
                except:
                    pass
            
            model_manager.set_fallbacks(role, [])
