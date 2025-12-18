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


# ============================================
# PERSISTENT LEARNING MEMORY
# Projeler arası öğrenme ve kullanıcı tercihleri
# ============================================

LEARNING_FILE = os.path.join(MEMORY_DIR, "learning.json")
PREFERENCES_FILE = os.path.join(MEMORY_DIR, "preferences.json")
PERFORMANCE_FILE = os.path.join(MEMORY_DIR, "performance.json")


class LearningMemory:
    """
    Projeler arası öğrenme hafızası.
    Kullanıcı tercihlerini, başarılı pattern'leri ve hataları hatırlar.
    """
    
    def __init__(self):
        self.preferences: Dict = {}  # Kullanıcı tercihleri
        self.patterns: List[Dict] = []  # Başarılı pattern'ler
        self.mistakes: List[Dict] = []  # Yapılan hatalar ve çözümleri
        self.tech_stack: Dict = {}  # Proje bazlı teknoloji tercihleri
        self._load()
    
    def _load(self):
        """Öğrenme verisini yükle"""
        try:
            if os.path.exists(LEARNING_FILE):
                with open(LEARNING_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.patterns = data.get("patterns", [])
                    self.mistakes = data.get("mistakes", [])
                    self.tech_stack = data.get("tech_stack", {})
            
            if os.path.exists(PREFERENCES_FILE):
                with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    self.preferences = json.load(f)
        except Exception as e:
            logger.warning(f"Learning memory load failed: {e}")
    
    def _save(self):
        """Öğrenme verisini kaydet"""
        try:
            with open(LEARNING_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "patterns": self.patterns[-100:],  # Son 100 pattern
                    "mistakes": self.mistakes[-50:],  # Son 50 hata
                    "tech_stack": self.tech_stack,
                    "updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Learning memory save failed: {e}")
    
    def learn_preference(self, category: str, preference: str, value: str):
        """Kullanıcı tercihini öğren"""
        if category not in self.preferences:
            self.preferences[category] = {}
        
        self.preferences[category][preference] = {
            "value": value,
            "count": self.preferences[category].get(preference, {}).get("count", 0) + 1,
            "last_used": datetime.now().isoformat()
        }
        self._save()
        logger.info(f"Learned preference: {category}/{preference} = {value}")
    
    def learn_pattern(self, task_type: str, approach: str, success: bool, details: str = ""):
        """Başarılı/başarısız pattern'i öğren"""
        pattern = {
            "task_type": task_type,
            "approach": approach,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.patterns.append(pattern)
        self._save()
        logger.info(f"Learned pattern: {task_type} - {'success' if success else 'fail'}")
    
    def learn_mistake(self, error_type: str, error_msg: str, solution: str):
        """Hatadan öğren"""
        mistake = {
            "error_type": error_type,
            "error_msg": error_msg[:500],
            "solution": solution,
            "timestamp": datetime.now().isoformat()
        }
        self.mistakes.append(mistake)
        self._save()
        logger.info(f"Learned from mistake: {error_type}")
    
    def learn_tech_stack(self, project_type: str, technologies: List[str]):
        """Proje teknoloji tercihini öğren"""
        if project_type not in self.tech_stack:
            self.tech_stack[project_type] = {}
        
        for tech in technologies:
            count = self.tech_stack[project_type].get(tech, 0)
            self.tech_stack[project_type][tech] = count + 1
        
        self._save()
        logger.info(f"Learned tech stack for {project_type}: {technologies}")
    
    def get_preference(self, category: str, preference: str) -> Optional[str]:
        """Tercih al"""
        if category in self.preferences and preference in self.preferences[category]:
            return self.preferences[category][preference]["value"]
        return None
    
    def get_similar_patterns(self, task_type: str, limit: int = 5) -> List[Dict]:
        """Benzer görevlerdeki pattern'leri al"""
        similar = [p for p in self.patterns if task_type.lower() in p["task_type"].lower()]
        return sorted(similar, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_solution_for_error(self, error_msg: str) -> Optional[str]:
        """Benzer hata için çözüm bul"""
        error_lower = error_msg.lower()
        for mistake in reversed(self.mistakes):
            if any(word in error_lower for word in mistake["error_msg"].lower().split()[:5]):
                return mistake["solution"]
        return None
    
    def get_preferred_tech(self, project_type: str) -> List[str]:
        """Proje tipi için tercih edilen teknolojileri al"""
        if project_type not in self.tech_stack:
            return []
        
        techs = self.tech_stack[project_type]
        return sorted(techs.keys(), key=lambda x: techs[x], reverse=True)[:5]
    
    def get_learning_summary(self) -> str:
        """Öğrenme özetini döndür"""
        lines = ["🧠 Öğrenme Hafızası Özeti", "=" * 30]
        
        # Tercihler
        if self.preferences:
            lines.append(f"\n📋 Tercihler ({len(self.preferences)} kategori):")
            for cat, prefs in list(self.preferences.items())[:5]:
                top_pref = max(prefs.items(), key=lambda x: x[1].get("count", 0))
                lines.append(f"  • {cat}: {top_pref[0]} = {top_pref[1]['value']}")
        
        # Pattern'ler
        if self.patterns:
            success_count = sum(1 for p in self.patterns if p["success"])
            lines.append(f"\n📊 Pattern'ler ({len(self.patterns)} toplam):")
            lines.append(f"  • Başarılı: {success_count}")
            lines.append(f"  • Başarısız: {len(self.patterns) - success_count}")
        
        # Hatalar
        if self.mistakes:
            lines.append(f"\n⚠️ Öğrenilen Hatalar: {len(self.mistakes)}")
        
        # Tech stack
        if self.tech_stack:
            lines.append(f"\n🔧 Teknoloji Tercihleri ({len(self.tech_stack)} proje tipi):")
            for proj_type, techs in list(self.tech_stack.items())[:3]:
                top_techs = sorted(techs.keys(), key=lambda x: techs[x], reverse=True)[:3]
                lines.append(f"  • {proj_type}: {', '.join(top_techs)}")
        
        return "\n".join(lines)


# Global learning memory
_learning = LearningMemory()


@tool
def learn_user_preference(category: str, preference: str, value: str) -> str:
    """
    Kullanıcı tercihini öğren ve hatırla.
    
    Args:
        category: Kategori (örn: "coding_style", "framework", "language")
        preference: Tercih adı (örn: "indentation", "frontend", "primary")
        value: Tercih değeri (örn: "4 spaces", "React", "Python")
    
    Returns:
        Onay mesajı
    
    Örnek:
        learn_user_preference("framework", "frontend", "React")
        learn_user_preference("coding_style", "indentation", "4 spaces")
    """
    _learning.learn_preference(category, preference, value)
    return f"✓ Öğrenildi: {category}/{preference} = {value}"


@tool
def recall_preference(category: str, preference: str) -> str:
    """
    Öğrenilmiş tercihi hatırla.
    
    Args:
        category: Kategori
        preference: Tercih adı
    
    Returns:
        Tercih değeri veya bulunamadı mesajı
    """
    value = _learning.get_preference(category, preference)
    if value:
        return f"📝 {category}/{preference}: {value}"
    return f"'{category}/{preference}' için kayıtlı tercih yok"


@tool
def learn_from_task(task_type: str, approach: str, success: bool, details: str = "") -> str:
    """
    Görev sonucundan öğren. Başarılı veya başarısız yaklaşımları hatırla.
    
    Args:
        task_type: Görev tipi (örn: "api_integration", "ui_component", "bug_fix")
        approach: Kullanılan yaklaşım
        success: Başarılı mı?
        details: Ek detaylar
    
    Returns:
        Onay mesajı
    """
    _learning.learn_pattern(task_type, approach, success, details)
    status = "başarılı" if success else "başarısız"
    return f"✓ Öğrenildi: {task_type} görevi için {status} yaklaşım kaydedildi"


@tool
def get_past_approaches(task_type: str) -> str:
    """
    Benzer görevlerde kullanılan geçmiş yaklaşımları getir.
    
    Args:
        task_type: Görev tipi
    
    Returns:
        Geçmiş yaklaşımlar ve sonuçları
    """
    patterns = _learning.get_similar_patterns(task_type)
    
    if not patterns:
        return f"'{task_type}' için geçmiş kayıt yok"
    
    lines = [f"📚 '{task_type}' için geçmiş yaklaşımlar:", ""]
    
    for p in patterns:
        status = "✅" if p["success"] else "❌"
        lines.append(f"{status} {p['approach'][:100]}")
        if p["details"]:
            lines.append(f"   └─ {p['details'][:80]}")
    
    return "\n".join(lines)


@tool
def learn_from_error(error_type: str, error_msg: str, solution: str) -> str:
    """
    Hatadan öğren. Gelecekte benzer hatalar için çözüm öner.
    
    Args:
        error_type: Hata tipi (örn: "import_error", "syntax_error", "api_error")
        error_msg: Hata mesajı
        solution: Uygulanan çözüm
    
    Returns:
        Onay mesajı
    """
    _learning.learn_mistake(error_type, error_msg, solution)
    return f"✓ Hata ve çözümü kaydedildi: {error_type}"


@tool
def suggest_solution(error_msg: str) -> str:
    """
    Benzer hatalar için geçmişte uygulanan çözümü öner.
    
    Args:
        error_msg: Hata mesajı
    
    Returns:
        Önerilen çözüm veya bulunamadı mesajı
    """
    solution = _learning.get_solution_for_error(error_msg)
    
    if solution:
        return f"💡 Önerilen çözüm (geçmiş deneyimden):\n{solution}"
    return "Bu hata için geçmiş çözüm kaydı yok"


def get_learning_memory_content() -> str:
    """Internal function to get learning summary"""
    return _learning.get_learning_summary()

@tool
def get_learning_summary() -> str:
    """
    Tüm öğrenme hafızasının özetini göster.
    
    Returns:
        Öğrenme özeti
    """
    return get_learning_memory_content()


# ============================================
# SELF-IMPROVEMENT / PERFORMANCE TRACKING
# ============================================

class PerformanceTracker:
    """
    Agent performansını takip eder ve iyileştirme önerileri sunar.
    """
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.tool_usage: Dict[str, Dict] = {}
        self.error_frequency: Dict[str, int] = {}
        self.success_rate: float = 0.0
        self._load()
    
    def _load(self):
        """Performans verisini yükle"""
        try:
            if os.path.exists(PERFORMANCE_FILE):
                with open(PERFORMANCE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.tool_usage = data.get("tool_usage", {})
                    self.error_frequency = data.get("error_frequency", {})
        except Exception as e:
            logger.warning(f"Performance data load failed: {e}")
    
    def _save(self):
        """Performans verisini kaydet"""
        try:
            with open(PERFORMANCE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "tasks": self.tasks[-200:],  # Son 200 görev
                    "tool_usage": self.tool_usage,
                    "error_frequency": self.error_frequency,
                    "updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Performance data save failed: {e}")
    
    def record_task(self, task: str, success: bool, duration_sec: float, 
                    tools_used: List[str], error: str = ""):
        """Görev sonucunu kaydet"""
        record = {
            "task": task[:200],
            "success": success,
            "duration": duration_sec,
            "tools_used": tools_used,
            "error": error[:200] if error else "",
            "timestamp": datetime.now().isoformat()
        }
        self.tasks.append(record)
        
        # Tool kullanımını güncelle
        for tool in tools_used:
            if tool not in self.tool_usage:
                self.tool_usage[tool] = {"count": 0, "success": 0, "fail": 0}
            self.tool_usage[tool]["count"] += 1
            if success:
                self.tool_usage[tool]["success"] += 1
            else:
                self.tool_usage[tool]["fail"] += 1
        
        # Hata frekansını güncelle
        if error:
            error_type = self._classify_error(error)
            self.error_frequency[error_type] = self.error_frequency.get(error_type, 0) + 1
        
        self._save()
    
    def _classify_error(self, error: str) -> str:
        """Hatayı sınıflandır"""
        error_lower = error.lower()
        if "syntax" in error_lower:
            return "syntax_error"
        elif "import" in error_lower or "module" in error_lower:
            return "import_error"
        elif "type" in error_lower:
            return "type_error"
        elif "timeout" in error_lower:
            return "timeout"
        elif "rate limit" in error_lower or "429" in error_lower:
            return "rate_limit"
        elif "permission" in error_lower:
            return "permission_error"
        else:
            return "other"
    
    def get_success_rate(self, last_n: int = 50) -> float:
        """Son N görevin başarı oranını hesapla"""
        recent = self.tasks[-last_n:]
        if not recent:
            return 0.0
        return sum(1 for t in recent if t["success"]) / len(recent) * 100
    
    def get_most_used_tools(self, limit: int = 10) -> List[tuple]:
        """En çok kullanılan tool'ları getir"""
        return sorted(
            self.tool_usage.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:limit]
    
    def get_problematic_tools(self) -> List[tuple]:
        """Başarısızlık oranı yüksek tool'ları getir"""
        problematic = []
        for tool, stats in self.tool_usage.items():
            if stats["count"] >= 5:  # En az 5 kullanım
                fail_rate = stats["fail"] / stats["count"] * 100
                if fail_rate > 30:  # %30'dan fazla başarısızlık
                    problematic.append((tool, fail_rate, stats["count"]))
        return sorted(problematic, key=lambda x: x[1], reverse=True)
    
    def get_common_errors(self, limit: int = 5) -> List[tuple]:
        """En sık karşılaşılan hataları getir"""
        return sorted(
            self.error_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
    
    def get_improvement_suggestions(self) -> List[str]:
        """İyileştirme önerileri oluştur"""
        suggestions = []
        
        # Başarı oranı düşükse
        success_rate = self.get_success_rate()
        if success_rate < 70:
            suggestions.append(f"⚠️ Başarı oranı düşük ({success_rate:.1f}%). Görevleri daha küçük parçalara bölmeyi dene.")
        
        # Problemli tool'lar
        problematic = self.get_problematic_tools()
        for tool, fail_rate, count in problematic[:3]:
            suggestions.append(f"🔧 '{tool}' tool'u sık başarısız oluyor ({fail_rate:.0f}%). Alternatif yaklaşım dene.")
        
        # Sık hatalar
        common_errors = self.get_common_errors()
        for error_type, count in common_errors[:3]:
            if count >= 5:
                suggestions.append(f"❌ '{error_type}' hatası sık tekrarlanıyor ({count} kez). Kök nedeni araştır.")
        
        if not suggestions:
            suggestions.append("✅ Performans iyi görünüyor!")
        
        return suggestions
    
    def get_performance_report(self) -> str:
        """Detaylı performans raporu"""
        lines = ["📊 Performans Raporu", "=" * 40]
        
        # Genel istatistikler
        total_tasks = len(self.tasks)
        success_rate = self.get_success_rate()
        lines.append(f"\n📈 Genel:")
        lines.append(f"  • Toplam görev: {total_tasks}")
        lines.append(f"  • Başarı oranı: {success_rate:.1f}%")
        
        # En çok kullanılan tool'lar
        top_tools = self.get_most_used_tools(5)
        if top_tools:
            lines.append(f"\n🔧 En Çok Kullanılan Tool'lar:")
            for tool, stats in top_tools:
                success_pct = stats["success"] / stats["count"] * 100 if stats["count"] > 0 else 0
                lines.append(f"  • {tool}: {stats['count']} kullanım ({success_pct:.0f}% başarı)")
        
        # Sık hatalar
        common_errors = self.get_common_errors()
        if common_errors:
            lines.append(f"\n❌ Sık Karşılaşılan Hatalar:")
            for error_type, count in common_errors:
                lines.append(f"  • {error_type}: {count} kez")
        
        # İyileştirme önerileri
        suggestions = self.get_improvement_suggestions()
        lines.append(f"\n💡 İyileştirme Önerileri:")
        for suggestion in suggestions:
            lines.append(f"  {suggestion}")
        
        return "\n".join(lines)


# Global performance tracker
_performance = PerformanceTracker()


@tool
def record_task_result(task: str, success: bool, tools_used: str, error: str = "") -> str:
    """
    Görev sonucunu kaydet. Self-improvement için kullanılır.
    
    Args:
        task: Görev açıklaması
        success: Başarılı mı?
        tools_used: Kullanılan tool'lar (virgülle ayrılmış)
        error: Hata mesajı (varsa)
    
    Returns:
        Onay mesajı
    """
    tools_list = [t.strip() for t in tools_used.split(",") if t.strip()]
    _performance.record_task(task, success, 0, tools_list, error)
    
    status = "✅ Başarılı" if success else "❌ Başarısız"
    return f"{status} görev kaydedildi"


@tool
def get_performance_report() -> str:
    """
    Agent performans raporunu göster.
    Başarı oranı, sık hatalar ve iyileştirme önerileri içerir.
    
    Returns:
        Detaylı performans raporu
    """
    return _performance.get_performance_report()


@tool
def get_improvement_tips() -> str:
    """
    Performansa dayalı iyileştirme önerileri al.
    
    Returns:
        İyileştirme önerileri listesi
    """
    suggestions = _performance.get_improvement_suggestions()
    
    lines = ["💡 İyileştirme Önerileri:", ""]
    for i, suggestion in enumerate(suggestions, 1):
        lines.append(f"{i}. {suggestion}")
    
    return "\n".join(lines)


# Helper functions for internal use
def record_performance(task: str, success: bool, tools: List[str], error: str = ""):
    """Internal: Performans kaydı"""
    _performance.record_task(task, success, 0, tools, error)


def get_error_solution(error: str) -> Optional[str]:
    """Internal: Hata için çözüm önerisi"""
    return _learning.get_solution_for_error(error)
