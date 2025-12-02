"""
AtomAgent Core - Orchestrator with Memory & RAG
v4.1 - Multi-API Key Support with Auto-Rotation
"""
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from config import config
from core.providers import model_manager, create_llm, is_rate_limit_error, handle_rate_limit
from prompts import load_prompt
from utils.logger import get_logger

from tools.agents import call_coder, call_researcher, create_plan
from tools.files import write_file, read_file, list_files, scan_workspace
from tools.execution import run_terminal_command
from tools.basic import run_neofetch, get_current_time
from tools.todo_tools import update_todo_list, mark_todo_done, get_current_todo, get_next_todo_step
from tools.rag import refresh_memory, search_codebase
from tools.git_tools import git_init, git_status, git_add, git_commit, git_log, git_diff
from tools.test_tools import run_tests, run_single_test, create_test_file, list_tests
from tools.memory import save_context, get_context_info, get_memory_stats, clear_memory, get_persistent_context
from tools.quality import self_evaluate, analyze_error
from tools.sandbox import (
    sandbox_start, sandbox_stop, sandbox_status,
    sandbox_shell, sandbox_upload, sandbox_download
)
from tools.tool_factory import (
    create_tool, list_custom_tools, delete_tool,
    get_tool_code, test_tool, get_custom_tools
)
from tools.session_tools import (
    list_recent_sessions, search_conversations,
    get_session_summary, get_session_stats
)

logger = get_logger()

# Memory
_memory_saver = MemorySaver()

_tools = [
    # Ana agent tool'ları
    call_coder,
    call_researcher,
    create_plan,
    # Todo yönetimi
    get_next_todo_step,
    mark_todo_done,
    get_current_todo,
    update_todo_list,
    # RAG
    search_codebase,
    refresh_memory,
    # Dosya işlemleri
    write_file,
    read_file,
    list_files,
    scan_workspace,
    run_terminal_command,
    # Git
    git_init,
    git_status,
    git_add,
    git_commit,
    git_log,
    git_diff,
    # Test
    run_tests,
    run_single_test,
    create_test_file,
    list_tests,
    # Memory - uzun görevlerde context koruma
    save_context,
    get_context_info,
    get_memory_stats,
    clear_memory,
    # Quality - self-evaluation ve hata analizi
    self_evaluate,
    analyze_error,
    # Sandbox - izole çalışma ortamı
    sandbox_start,
    sandbox_stop,
    sandbox_status,
    sandbox_shell,
    sandbox_upload,
    sandbox_download,
    # Tool Factory - dinamik tool oluşturma
    create_tool,
    list_custom_tools,
    delete_tool,
    get_tool_code,
    test_tool,
    # Session yönetimi
    list_recent_sessions,
    search_conversations,
    get_session_summary,
    get_session_stats,
    # Yardımcı
    get_current_time,
    run_neofetch,
]

def get_agent_executor():
    """Create agent executor with current model settings"""
    # Get LLM from model_manager (uses saved settings)
    llm = model_manager.get_llm("supervisor")
    
    if not llm:
        # Fallback to ollama if model_manager fails
        from langchain_ollama import ChatOllama
        logger.warning("Using fallback Ollama model")
        llm = ChatOllama(model="llama3.2", temperature=0.1)
    
    # Load prompt from JSON file and add persistent memory context
    supervisor_prompt = load_prompt("supervisor")
    
    # Kalıcı hafızadaki bilgileri prompt'a ekle
    persistent_ctx = get_persistent_context()
    if persistent_ctx:
        supervisor_prompt = supervisor_prompt + "\n\n" + persistent_ctx
    
    # Custom tool'ları da ekle
    all_tools = _tools + get_custom_tools()
    
    orchestrator = create_react_agent(
        llm,
        all_tools,
        prompt=supervisor_prompt,
        checkpointer=_memory_saver
    )
    
    supervisor_config = model_manager.get_config("supervisor")
    custom_count = len(get_custom_tools())
    logger.info(f"AtomAgent ready with {supervisor_config.provider}/{supervisor_config.model} ({len(_tools)} + {custom_count} custom tools)")
    return orchestrator, _memory_saver, supervisor_prompt


def get_thread_config(thread_id: str = "default"):
    return {"configurable": {"thread_id": thread_id}}
