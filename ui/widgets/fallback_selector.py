"""
Fallback Selector Widget - Clean Modal for Fallback Configuration
v2.1 - Reads from .atom_fallback.json, all 6 roles, 5 fallbacks each
"""
import json
import os
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Select, Input

from core.providers import PROVIDERS, get_provider_names, model_manager

# Fallback file in project root (not workspace)
FALLBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".atom_fallback.json")


def load_fallbacks() -> dict:
    """Load fallbacks from .atom_fallback.json"""
    try:
        if os.path.exists(FALLBACK_FILE):
            with open(FALLBACK_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_fallbacks_to_file(data: dict):
    """Save fallbacks to .atom_fallback.json"""
    try:
        with open(FALLBACK_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Fallback save error: {e}")


def get_role_fallbacks(role: str) -> list:
    """Get fallback list for a role from .atom_fallback.json"""
    data = load_fallbacks()
    if role in data and "fallbacks" in data[role]:
        return data[role]["fallbacks"]
    return []


def get_primary_model(role: str) -> str:
    """Get primary model info for display"""
    cfg = model_manager.get_config(role)
    if cfg:
        model_short = cfg.model[:25] + "..." if len(cfg.model) > 25 else cfg.model
        return f"{cfg.provider}/{model_short}"
    return "?"


ROLE_INFO = {
    "supervisor": ("🎯", "Supervisor"),
    "coder": ("💻", "Coder"),
    "researcher": ("🔍", "Researcher"),
    "vision": ("👁️", "Vision"),
    "audio": ("🎤", "Audio"),
    "tts": ("🔊", "TTS")
}

# Tüm roller
ALL_ROLES = ["supervisor", "coder", "researcher", "vision", "audio", "tts"]
MAX_FALLBACKS = 5


class FallbackSelectorModal(ModalScreen):
    """Modern modal for fallback configuration - all 6 roles, 5 fallbacks each"""
    
    BINDINGS = [("escape", "cancel", "Kapat")]
    
    def compose(self) -> ComposeResult:
        with Vertical(id="fallback-modal"):
            # Header
            with Horizontal(id="fallback-modal-header"):
                yield Static("🔄 Yedek Model Ayarları", id="fallback-modal-title")
                yield Button("✕", id="btn-close", variant="error")
            
            # Info
            yield Static(
                "[dim]Ana model başarısız olursa sırayla yedek modeller denenir. Ayarlar .atom_fallback.json'a kaydedilir.[/dim]",
                id="fallback-modal-info"
            )
            
            with VerticalScroll(id="fallback-list"):
                for role in ALL_ROLES:
                    fallbacks = get_role_fallbacks(role)
                    icon, name = ROLE_INFO[role]
                    primary = get_primary_model(role)
                    
                    with Vertical(classes="fallback-card"):
                        # Card Header - Ana model bilgisi
                        with Horizontal(classes="fallback-card-header"):
                            yield Static(f"{icon} {name}", classes="fallback-card-title")
                            yield Static(f"[dim]Ana: {primary}[/dim]", classes="fallback-primary-info")
                        
                        # 5 Fallback Rows
                        for i in range(MAX_FALLBACKS):
                            fb_provider = fallbacks[i]["provider"] if i < len(fallbacks) else "ollama"
                            fb_model = fallbacks[i]["model"] if i < len(fallbacks) else ""
                            
                            with Horizontal(classes="fallback-row"):
                                yield Static(f"#{i+1}", classes="fallback-index")
                                
                                provider_opts = [(PROVIDERS[p].name, p) for p in get_provider_names()]
                                yield Select(
                                    provider_opts,
                                    value=fb_provider,
                                    id=f"fb-provider-{role}-{i}",
                                    classes="fallback-select"
                                )
                                
                                yield Input(
                                    value=fb_model,
                                    placeholder="Model adı (boş = devre dışı)",
                                    id=f"fb-model-{role}-{i}",
                                    classes="fallback-input"
                                )
            
            # Footer
            with Horizontal(id="fallback-modal-footer"):
                yield Button("💾 Kaydet", id="btn-save", variant="success")
                yield Button("🗑️ Temizle", id="btn-reset", variant="warning")
                yield Button("İptal", id="btn-cancel", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "btn-save":
            self._save_fallbacks()
            self.app.notify("✓ Yedek model ayarları kaydedildi!", severity="information")
            self.dismiss(True)
        
        elif btn_id == "btn-reset":
            self._reset_fallbacks()
            self.app.notify("Yedek ayarları temizlendi", severity="warning")
        
        elif btn_id in ["btn-cancel", "btn-close"]:
            self.dismiss(False)
    
    def action_cancel(self):
        self.dismiss(False)
    
    def _save_fallbacks(self):
        """Tüm fallback ayarlarını .atom_fallback.json'a kaydet"""
        data = {}
        
        for role in ALL_ROLES:
            fallbacks = []
            
            for i in range(MAX_FALLBACKS):
                try:
                    provider = self.query_one(f"#fb-provider-{role}-{i}", Select).value
                    model = self.query_one(f"#fb-model-{role}-{i}", Input).value.strip()
                    
                    # Sadece model belirtilmişse ekle
                    if model:
                        fallbacks.append({"provider": provider, "model": model})
                except:
                    pass
            
            data[role] = {"fallbacks": fallbacks}
            
            # model_manager'a da uygula
            model_manager.set_fallbacks(role, [(f["provider"], f["model"]) for f in fallbacks])
        
        save_fallbacks_to_file(data)
    
    def _reset_fallbacks(self):
        """Tüm fallback inputlarını temizle"""
        for role in ALL_ROLES:
            for i in range(MAX_FALLBACKS):
                try:
                    self.query_one(f"#fb-provider-{role}-{i}", Select).value = "ollama"
                    self.query_one(f"#fb-model-{role}-{i}", Input).value = ""
                except:
                    pass
            
            model_manager.set_fallbacks(role, [])
