"""
Enhanced Memory System - Uzun görevlerde context koruma
Conversation summarization ve smart context management
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import config
from utils.logger import get_logger

logger = get_logger()

MEMORY_DIR = os.path.join(config.workspace.base_dir, ".memory")
CONTEXT_FILE = os.path.join(MEMORY_DIR, "context.json")
SUMMARY_FILE = os.path.join(MEMORY_DIR, "summary.json")

# Memory dizinini oluştur
os.makedirs(MEMORY_DIR, exist_ok=True)


class ConversationMemory:
    """Gelişmiş konuşma hafızası"""
    
    def __init__(self, max_messages: int = 20, summary_threshold: int = 15):
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        self.messages: List[Dict] = []
        self.summaries: List[str] = []
        self.context: Dict = {}
        self._load()
    
    def _load(self):
        """Kaydedilmiş hafızayı yükle"""
        try:
            if os.path.exists(CONTEXT_FILE):
                with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])
                    self.context = data.get("context", {})
            
            if os.path.exists(SUMMARY_FILE):
                with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.summaries = data.get("summaries", [])
        except Exception as e:
            logger.warning(f"Memory load failed: {e}")
    
    def _save(self):
        """Hafızayı kaydet"""
        try:
            with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "messages": self.messages[-self.max_messages:],
                    "context": self.context,
                    "updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "summaries": self.summaries[-10:],  # Son 10 özet
                    "updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Memory save failed: {e}")
    
    def add_message(self, role: str, content: str):
        """Mesaj ekle"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Threshold aşıldıysa özetle
        if len(self.messages) >= self.summary_threshold:
            self._summarize_old_messages()
        
        self._save()
    
    def _summarize_old_messages(self):
        """Eski mesajları özetle"""
        if len(self.messages) < self.summary_threshold:
            return
        
        # İlk yarıyı özetle
        half = len(self.messages) // 2
        old_messages = self.messages[:half]
        
        # Basit özet oluştur
        summary_parts = []
        for msg in old_messages:
            role = msg["role"]
            content = msg["content"][:100]
            if role == "human":
                summary_parts.append(f"Kullanıcı: {content}")
            elif role == "ai":
                summary_parts.append(f"Agent: {content}")
        
        summary = " | ".join(summary_parts)
        self.summaries.append({
            "summary": summary,
            "message_count": half,
            "timestamp": datetime.now().isoformat()
        })
        
        # Eski mesajları sil
        self.messages = self.messages[half:]
        logger.info(f"Summarized {half} messages")
    
    def get_context_messages(self) -> List[Dict]:
        """Context için mesajları döndür"""
        context_msgs = []
        
        # Özetleri ekle
        if self.summaries:
            summary_text = "Önceki konuşma özeti:\n"
            for s in self.summaries[-3:]:  # Son 3 özet
                summary_text += f"- {s['summary'][:200]}\n"
            context_msgs.append({
                "role": "system",
                "content": summary_text
            })
        
        # Son mesajları ekle
        context_msgs.extend(self.messages[-self.max_messages:])
        
        return context_msgs
    
    def set_context(self, key: str, value: str):
        """Context bilgisi ekle"""
        self.context[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save()
    
    def get_context(self, key: str) -> Optional[str]:
        """Context bilgisi al"""
        if key in self.context:
            return self.context[key]["value"]
        return None
    
    def clear(self):
        """Hafızayı temizle"""
        self.messages = []
        self.summaries = []
        self.context = {}
        self._save()
        logger.info("Memory cleared")
    
    def get_stats(self) -> Dict:
        """Hafıza istatistikleri"""
        return {
            "message_count": len(self.messages),
            "summary_count": len(self.summaries),
            "context_keys": list(self.context.keys()),
            "estimated_tokens": sum(len(m["content"]) // 4 for m in self.messages)
        }


# Global memory instance
_memory = ConversationMemory()


@tool
def save_context(key: str, value: str) -> str:
    """
    Önemli bilgiyi hafızaya kaydet. Uzun görevlerde context korumak için kullan.
    
    Args:
        key: Bilgi anahtarı (örn: "proje_adi", "kullanilan_teknoloji")
        value: Kaydedilecek değer
    
    Returns:
        Başarı mesajı
    """
    _memory.set_context(key, value)
    logger.info(f"Context saved: {key}")
    return f"✓ '{key}' hafızaya kaydedildi"


@tool
def get_context_info(key: str) -> str:
    """
    Hafızadan bilgi al.
    
    Args:
        key: Bilgi anahtarı
    
    Returns:
        Kaydedilmiş değer veya "bulunamadı"
    """
    value = _memory.get_context(key)
    if value:
        return value
    return f"'{key}' hafızada bulunamadı"


@tool
def get_memory_stats() -> str:
    """
    Hafıza istatistiklerini göster.
    
    Returns:
        Hafıza durumu
    """
    stats = _memory.get_stats()
    return f"""📊 Hafıza Durumu:
- Mesaj sayısı: {stats['message_count']}
- Özet sayısı: {stats['summary_count']}
- Context anahtarları: {', '.join(stats['context_keys']) or 'yok'}
- Tahmini token: ~{stats['estimated_tokens']}"""


@tool
def clear_memory() -> str:
    """
    Hafızayı temizle. Yeni bir göreve başlarken kullan.
    
    Returns:
        Başarı mesajı
    """
    _memory.clear()
    return "✓ Hafıza temizlendi"


def add_to_memory(role: str, content: str):
    """Mesajı hafızaya ekle (internal function)"""
    _memory.add_message(role, content)


def get_memory_context() -> List[Dict]:
    """Hafıza context'ini al (internal function)"""
    return _memory.get_context_messages()


def get_persistent_context() -> str:
    """
    Kalıcı hafızadaki tüm context bilgilerini string olarak döndür.
    Agent'ın system prompt'una eklenebilir.
    """
    if not _memory.context:
        return ""
    
    lines = ["[Hafızadaki Bilgiler]"]
    for key, data in _memory.context.items():
        lines.append(f"- {key}: {data['value']}")
    
    return "\n".join(lines)


class TaskMemory:
    """Görev bazlı hafıza - bir görevin tüm adımlarını takip eder"""
    
    def __init__(self):
        self.current_task: Optional[str] = None
        self.steps: List[Dict] = []
        self.artifacts: Dict[str, str] = {}  # Oluşturulan dosyalar, değişkenler
        self.errors: List[Dict] = []
    
    def start_task(self, task: str):
        """Yeni görev başlat"""
        self.current_task = task
        self.steps = []
        self.artifacts = {}
        self.errors = []
        logger.info(f"Task started: {task[:50]}")
    
    def add_step(self, step: str, result: str = "", success: bool = True):
        """Adım ekle"""
        self.steps.append({
            "step": step,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_artifact(self, name: str, value: str):
        """Artifact ekle (oluşturulan dosya, değişken, vb.)"""
        self.artifacts[name] = value
    
    def add_error(self, error: str, context: str = ""):
        """Hata ekle"""
        self.errors.append({
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> str:
        """Görev özetini döndür"""
        if not self.current_task:
            return "Aktif görev yok"
        
        lines = [f"📋 Görev: {self.current_task}"]
        lines.append(f"Adımlar: {len(self.steps)}")
        
        if self.steps:
            lines.append("\nSon adımlar:")
            for step in self.steps[-5:]:
                status = "✓" if step["success"] else "✗"
                lines.append(f"  {status} {step['step'][:50]}")
        
        if self.artifacts:
            lines.append(f"\nArtifacts: {', '.join(self.artifacts.keys())}")
        
        if self.errors:
            lines.append(f"\nHatalar: {len(self.errors)}")
        
        return "\n".join(lines)
    
    def get_context_for_recovery(self) -> str:
        """Hata kurtarma için context döndür"""
        if not self.errors:
            return ""
        
        last_error = self.errors[-1]
        successful_steps = [s for s in self.steps if s["success"]]
        
        context = f"""Son hata: {last_error['error']}
Başarılı adımlar: {len(successful_steps)}
Oluşturulan dosyalar: {', '.join(self.artifacts.keys()) or 'yok'}
"""
        return context


# Global task memory
_task_memory = TaskMemory()


def start_task_tracking(task: str):
    """Görev takibini başlat"""
    _task_memory.start_task(task)


def track_step(step: str, result: str = "", success: bool = True):
    """Adım takip et"""
    _task_memory.add_step(step, result, success)


def track_artifact(name: str, value: str):
    """Artifact takip et"""
    _task_memory.add_artifact(name, value)


def track_error(error: str, context: str = ""):
    """Hata takip et"""
    _task_memory.add_error(error, context)


def get_task_summary() -> str:
    """Görev özeti al"""
    return _task_memory.get_summary()


def get_recovery_context() -> str:
    """Kurtarma context'i al"""
    return _task_memory.get_context_for_recovery()
