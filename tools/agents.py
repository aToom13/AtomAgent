"""
Agent Tools - Sub-agent'lari tool olarak cagirir
Error Recovery, Retry mekanizmasi ve RAG destegi ile
v4.3 - Enhanced Retry with Telemetry
"""
import time
import asyncio
import concurrent.futures
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from core.providers import model_manager, create_llm, is_rate_limit_error, is_fallback_needed, handle_rate_limit, rotate_api_key
from prompts import load_prompt
from utils.logger import get_logger
from utils.retry import retry_with_backoff, RetryContext, is_retryable_error
from utils.telemetry import trace_tool_call, get_debug_context
from tools.files import (
    write_file, read_file, list_files, create_directory,
    delete_file, delete_directory, scan_workspace
)
from tools.execution import run_terminal_command
from tools.web import web_search, visit_webpage, quick_answer, search_docs
from tools.todo_tools import update_todo_list, mark_todo_step
from tools.git_tools import git_status, git_add, git_commit, git_diff
from tools.test_tools import run_tests, run_single_test, create_test_file

# RAG tools - lazy import to avoid circular dependency
def _get_rag_tools():
    from tools.rag import search_codebase, refresh_memory
    return search_codebase, refresh_memory


# Quality tools - lazy import
def _get_quality_tools():
    from tools.quality import lint_and_fix, check_syntax
    return lint_and_fix, check_syntax


logger = get_logger()


# ============================================
# DYNAMIC SUB-AGENTS (Model Manager Integration)
# ============================================

# Cache for sub-agents - cleared when model changes
_agent_cache = {
    "coder": None,
    "researcher": None,
    "coder_config": None,
    "researcher_config": None,
}


def _get_coder_agent():
    """Get or create coder agent with current model settings"""
    global _agent_cache
    
    # Check if model config changed
    current_config = model_manager.get_config("coder")
    cached_config = _agent_cache.get("coder_config")
    
    if cached_config and _agent_cache["coder"]:
        # Check if config is same
        if (cached_config.provider == current_config.provider and 
            cached_config.model == current_config.model):
            return _agent_cache["coder"]
    
    # Create new agent with current model
    llm = model_manager.get_llm("coder")
    if not llm:
        # Fallback
        from langchain_ollama import ChatOllama
        logger.warning("Coder: Using fallback Ollama model")
        llm = ChatOllama(model="llama3.2", temperature=0)
    
    search_codebase, refresh_memory = _get_rag_tools()
    lint_and_fix, check_syntax = _get_quality_tools()
    
    # Load prompt from JSON
    coder_prompt = load_prompt("coder")
    
    agent = create_react_agent(
        llm,
        [write_file, read_file, list_files, create_directory, delete_file,
         delete_directory, run_terminal_command, scan_workspace,
         search_codebase, refresh_memory, lint_and_fix, check_syntax,
         # Git tools
         git_status, git_add, git_commit, git_diff,
         # Test tools
         run_tests, run_single_test, create_test_file],
        prompt=coder_prompt
    )
    
    # Cache agent and config
    _agent_cache["coder"] = agent
    _agent_cache["coder_config"] = AgentConfigSnapshot(
        current_config.provider, current_config.model
    )
    
    logger.info(f"Coder agent created: {current_config.provider}/{current_config.model}")
    return agent


def _get_researcher_agent():
    """Get or create researcher agent with current model settings"""
    global _agent_cache
    
    # Check if model config changed
    current_config = model_manager.get_config("researcher")
    cached_config = _agent_cache.get("researcher_config")
    
    if cached_config and _agent_cache["researcher"]:
        if (cached_config.provider == current_config.provider and 
            cached_config.model == current_config.model):
            return _agent_cache["researcher"]
    
    # Create new agent with current model
    llm = model_manager.get_llm("researcher")
    if not llm:
        from langchain_ollama import ChatOllama
        logger.warning("Researcher: Using fallback Ollama model")
        llm = ChatOllama(model="llama3.2", temperature=0)
    
    search_codebase, _ = _get_rag_tools()
    
    # Load prompt from JSON
    researcher_prompt = load_prompt("researcher")
    
    agent = create_react_agent(
        llm,
        [quick_answer, web_search, search_docs, visit_webpage, read_file, search_codebase],
        prompt=researcher_prompt
    )
    
    _agent_cache["researcher"] = agent
    _agent_cache["researcher_config"] = AgentConfigSnapshot(
        current_config.provider, current_config.model
    )
    
    logger.info(f"Researcher agent created: {current_config.provider}/{current_config.model}")
    return agent


class AgentConfigSnapshot:
    """Simple config snapshot for cache comparison"""
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model


def clear_agent_cache():
    """Clear all cached agents - call when models change"""
    global _agent_cache
    _agent_cache = {
        "coder": None,
        "researcher": None,
        "coder_config": None,
        "researcher_config": None,
    }
    logger.info("Agent cache cleared")


def is_server_error(error: Exception) -> bool:
    """Check if error is a server error (500, 502, 503, etc.)"""
    error_str = str(error).lower()
    return any(x in error_str for x in ["500", "502", "503", "504", "internal server error", "bad gateway", "service unavailable"])


# ============================================
# AGENT TOOLS WITH ERROR RECOVERY
# ============================================

@tool
def call_coder(task: str) -> str:
    """
    KOD YAZMA VE DÜZENLEME İÇİN KULLAN.
    
    KULLAN:
    - Yeni dosya oluşturma (Python, JS, HTML, CSS, vb.)
    - Mevcut kodu düzenleme veya refactoring
    - Bug fix ve hata düzeltme
    - Test yazma
    - Kod kalitesi iyileştirme
    
    KULLANMA:
    - Web araştırması için (call_researcher kullan)
    - Sadece bilgi almak için (direkt cevap ver)
    - Dosya okumak için (read_file kullan)
    
    ÖNEMLİ: Görevi detaylı ve spesifik ver!
    KÖTÜ: "Login sayfası yap"
    İYİ: "React ile login sayfası oluştur: email/password inputları, 
         validation, submit butonu, hata gösterimi, Tailwind CSS"
    
    Args:
        task: Yapılacak görev (detaylı olmalı)
    """
    logger.info(f"Coder: {task[:50]}...")
    debug_ctx = get_debug_context()
    
    with RetryContext(max_attempts=10, base_delay=1.0) as ctx:
        while ctx.should_retry():
            # Her denemede agent'ı yeniden al (key değişmiş olabilir)
            coder = _get_coder_agent()
            
            try:
                with trace_tool_call("call_coder", {"task": task[:100]}):
                    result = coder.invoke({"messages": [HumanMessage(content=task)]})
                    output = str(result["messages"][-1].content)
                    
                    mark_todo_step("Kod", completed=True)
                    debug_ctx.log_tool_call("call_coder", {"task": task[:50]}, output[:100], True)
                    ctx.success()
                    return output
                
            except Exception as e:
                debug_ctx.log_error(str(e), {"tool": "call_coder", "attempt": ctx.attempt})
                
                # Server error (500, 502, etc.) - bekle ve tekrar dene
                if is_server_error(e):
                    logger.info(f"Server error, waiting and retrying...")
                    ctx.failed(e)
                    continue
                
                # Fallback gerekip gerekmediğini kontrol et
                if is_fallback_needed(e):
                    config = model_manager.get_config("coder")
                    provider = config.provider if config else "unknown"
                    logger.info(f"Coder: Fallback needed for {provider}")
                    
                    # Fallback'e geç
                    if model_manager.switch_to_fallback("coder"):
                        clear_agent_cache()
                        logger.info(f"Coder: Switched to fallback provider")
                        ctx.failed(e)
                        continue
                
                # Retryable error check
                if is_retryable_error(e):
                    ctx.failed(e)
                    continue
                
                # Non-retryable error
                ctx.failed(e)
                break
    
    logger.error(f"Coder failed: {ctx.last_error}")
    return f"Coder hatasi: {ctx.last_error}. Gorevi basitlestirip tekrar deneyin."


@tool
def call_researcher(query: str) -> str:
    """
    WEB ARAŞTIRMASI VE BİLGİ TOPLAMA İÇİN KULLAN.
    
    KULLAN:
    - Güncel teknoloji bilgisi gerektiğinde
    - API dokümantasyonu araştırması
    - Best practice ve pattern araştırması
    - Hata mesajı çözümü araştırması
    - Kütüphane/framework karşılaştırması
    
    KULLANMA:
    - Temel programlama bilgisi için (zaten biliyorsun)
    - Kod yazmak için (call_coder kullan)
    - Yerel kod aramak için (search_codebase kullan)
    
    ÖNEMLİ: Spesifik sorgular daha iyi sonuç verir!
    KÖTÜ: "React"
    İYİ: "React useEffect cleanup function best practices 2024"
    
    Args:
        query: Araştırılacak konu (spesifik olmalı)
    """
    logger.info(f"Researcher: {query[:50]}...")
    debug_ctx = get_debug_context()
    
    queries_to_try = [query, f"{query} tutorial", f"{query} example"]
    
    with RetryContext(max_attempts=10, base_delay=1.0) as ctx:
        while ctx.should_retry():
            researcher = _get_researcher_agent()
            q = queries_to_try[ctx.attempt] if ctx.attempt < len(queries_to_try) else query
            
            try:
                with trace_tool_call("call_researcher", {"query": q[:100]}):
                    result = researcher.invoke({"messages": [HumanMessage(content=q)]})
                    output = str(result["messages"][-1].content)
                    
                    # Check result quality
                    if "basarisiz" in output.lower() or "hata" in output.lower() or len(output) < 50:
                        if ctx.attempt < 3:
                            logger.warning(f"Researcher got poor results, trying alternative query")
                            ctx.failed(Exception("Poor results"))
                            continue
                    
                    mark_todo_step("Arastir", completed=True)
                    debug_ctx.log_tool_call("call_researcher", {"query": q[:50]}, output[:100], True)
                    ctx.success()
                    return output
                
            except Exception as e:
                debug_ctx.log_error(str(e), {"tool": "call_researcher", "attempt": ctx.attempt})
                
                # Server error - bekle ve tekrar dene
                if is_server_error(e):
                    logger.info(f"Server error, waiting and retrying...")
                    ctx.failed(e)
                    continue
                
                # Fallback gerekip gerekmediğini kontrol et
                if is_fallback_needed(e):
                    config = model_manager.get_config("researcher")
                    provider = config.provider if config else "unknown"
                    logger.info(f"Researcher: Fallback needed for {provider}")
                    
                    if model_manager.switch_to_fallback("researcher"):
                        clear_agent_cache()
                        logger.info(f"Researcher: Switched to fallback provider")
                        ctx.failed(e)
                        continue
                
                if is_retryable_error(e):
                    ctx.failed(e)
                    continue
                
                ctx.failed(e)
                break
    
    logger.error(f"Researcher failed: {ctx.last_error}")
    return f"Arastirma basarisiz: {ctx.last_error}. Farkli anahtar kelimeler deneyin."


@tool
def create_plan(task_description: str) -> str:
    """
    Gorev icin detayli plan olusturur ve Todo'ya kaydeder.
    
    Args:
        task_description: Yapilacak isin aciklamasi
    """
    logger.info(f"Plan olusturuluyor: {task_description[:50]}...")
    
    # Use supervisor model for planning
    llm = model_manager.get_llm("supervisor")
    if not llm:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model="llama3.2", temperature=0.3)
    
    # Load planner prompt
    planner_prompt = load_prompt("planner")
    
    plan_prompt = f"""Asagidaki gorev icin detayli bir plan olustur.

GOREV: {task_description}

FORMAT:
# Gorev: [Kisa baslik]

**Hedef:** [Hedefin kisa aciklamasi]

## Adimlar

- [ ] [Spesifik adim 1]
- [ ] [Spesifik adim 2]
- [ ] [Spesifik adim 3]
- [ ] [Gerekirse daha fazla adim]
- [ ] Test et

KURALLAR:
- Her adim spesifik olmali
- 4-7 adim olmali
- Checkbox formati kullan: - [ ]
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content=planner_prompt),
            HumanMessage(content=plan_prompt)
        ])
        
        plan = response.content
        update_todo_list.invoke({"content": plan})
        logger.info("Plan olusturuldu")
        return "Plan olusturuldu ve Todo'ya kaydedildi"
        
    except Exception as e:
        logger.error(f"Plan error: {e}")
        fallback = f"""# Gorev: {task_description[:50]}

## Adimlar

- [ ] Arastirma yap
- [ ] Gelistirme yap
- [ ] Test et
"""
        update_todo_list.invoke({"content": fallback})
        return "Basit plan olusturuldu"
