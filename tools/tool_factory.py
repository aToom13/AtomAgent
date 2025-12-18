"""
Tool Factory - Agent'ın dinamik tool oluşturması
Agent kendi yeteneklerini genişletebilir
"""
import os
import json
import importlib.util
from datetime import datetime
from typing import Optional, List, Dict, Callable
from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field

from config import config
from utils.logger import get_logger

logger = get_logger()

# Custom tools dizini
TOOLS_DIR = os.path.join(config.workspace.base_dir, ".custom_tools")
REGISTRY_FILE = os.path.join(TOOLS_DIR, "registry.json")

# Runtime'da yüklenen custom tool'lar
_custom_tools: Dict[str, StructuredTool] = {}
_tool_registry: Dict[str, dict] = {}

# Tool oluşturma callback'i (agent'a yeni tool eklemek için)
_on_tool_created: Optional[Callable] = None


def _ensure_tools_dir():
    """Tools dizinini oluştur"""
    os.makedirs(TOOLS_DIR, exist_ok=True)


def _load_registry() -> Dict[str, dict]:
    """Tool registry'yi yükle"""
    global _tool_registry
    
    _ensure_tools_dir()
    
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                _tool_registry = json.load(f)
        except:
            _tool_registry = {}
    
    return _tool_registry


def _save_registry():
    """Tool registry'yi kaydet"""
    _ensure_tools_dir()
    
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(_tool_registry, f, ensure_ascii=False, indent=2)


# Sandbox shared dizini
SANDBOX_SHARED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docker", "shared")


def _create_sandbox_tool(name: str, description: str, code: str) -> Optional[StructuredTool]:
    """
    Sandbox'ta çalışacak tool oluştur.
    Kod docker/shared klasörüne yazılır ve sandbox_shell ile çalıştırılır.
    """
    try:
        from tools.sandbox import sandbox_shell, _is_container_running
        
        # Shared dizini oluştur
        os.makedirs(SANDBOX_SHARED_DIR, exist_ok=True)
        
        # Tool dosyasını shared klasöre yaz
        tool_file = os.path.join(SANDBOX_SHARED_DIR, f"{name}.py")
        
        # Wrapper script oluştur - argümanları JSON olarak alır, sonucu JSON olarak döner
        wrapper_code = f'''#!/usr/bin/env python3
"""Sandbox Tool: {name}"""
import sys
import json

{code}

if __name__ == "__main__":
    try:
        # Argümanları JSON olarak al
        if len(sys.argv) > 1:
            args = json.loads(sys.argv[1])
        else:
            args = {{}}
        
        # Fonksiyonu çağır
        result = {name}(**args)
        
        # Sonucu JSON olarak döndür
        print(json.dumps({{"success": True, "result": result}}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e)}}, ensure_ascii=False))
'''
        
        with open(tool_file, "w", encoding="utf-8") as f:
            f.write(wrapper_code)
        
        # Sandbox'ta çalışacak wrapper fonksiyon oluştur
        # name'i closure'a al
        tool_name = name
        tool_desc = description
        
        def sandbox_executor(tool_input: str = "{}") -> str:
            """
            Sandbox tool executor.
            Args:
                tool_input: JSON string olarak argümanlar
            """
            # Sandbox çalışıyor mu kontrol et
            if not _is_container_running():
                return "❌ Sandbox çalışmıyor. Önce sandbox_start() çalıştır."
            
            # tool_input zaten JSON string olabilir veya dict olabilir
            if isinstance(tool_input, dict):
                args_json = json.dumps(tool_input, ensure_ascii=False)
            else:
                args_json = tool_input
            
            # Sandbox'ta çalıştır
            cmd = f"python3 /home/agent/shared/{tool_name}.py '{args_json}'"
            result = sandbox_shell.invoke({"command": cmd})
            
            # Sonucu parse et
            try:
                parsed = json.loads(result)
                if parsed.get("success"):
                    return str(parsed.get("result", ""))
                else:
                    return f"❌ Hata: {parsed.get('error', 'Bilinmeyen hata')}"
            except json.JSONDecodeError:
                # JSON değilse direkt döndür (print çıktısı olabilir)
                return result
        
        # Docstring'i orijinal koddan al
        sandbox_executor.__doc__ = f"{tool_desc}\n\n[Sandbox'ta çalışır]\nArgs: tool_input (JSON string)"
        sandbox_executor.__name__ = tool_name
        
        # StructuredTool oluştur
        tool_instance = StructuredTool.from_function(
            func=sandbox_executor,
            name=name,
            description=f"{description} [SANDBOX]"
        )
        
        logger.info(f"Sandbox tool created: {name}")
        return tool_instance
        
        return tool_instance
        
    except Exception as e:
        logger.error(f"Sandbox tool creation failed: {e}")
        return None


def _create_tool_from_code(name: str, description: str, code: str, 
                           parameters: List[dict] = None) -> Optional[StructuredTool]:
    """
    Python kodundan tool oluştur.
    
    Args:
        name: Tool adı
        description: Tool açıklaması
        code: Python fonksiyon kodu
        parameters: Parametre listesi [{"name": "x", "type": "str", "description": "..."}]
    """
    try:
        # Genişletilmiş namespace - daha fazla modül erişimi
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "bool": bool,
                "tuple": tuple,
                "set": set,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "reversed": reversed,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "any": any,
                "all": all,
                "open": open,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "type": type,
                "hasattr": hasattr,
                "getattr": getattr,
                "setattr": setattr,
                "callable": callable,
                "repr": repr,
                "format": format,
                "input": input,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "RuntimeError": RuntimeError,
                "__import__": __import__,
            },
            # Temel modüller
            "os": __import__("os"),
            "json": __import__("json"),
            "datetime": __import__("datetime"),
            "re": __import__("re"),
            "requests": __import__("requests"),
            # Ek modüller
            "subprocess": __import__("subprocess"),
            "base64": __import__("base64"),
            "hashlib": __import__("hashlib"),
            "urllib": __import__("urllib"),
            "pathlib": __import__("pathlib"),
            "time": __import__("time"),
            "random": __import__("random"),
            "math": __import__("math"),
            "collections": __import__("collections"),
            "itertools": __import__("itertools"),
            "functools": __import__("functools"),
            "typing": __import__("typing"),
        }
        
        # Sandbox shell erişimi ekle (tool'lar sandbox'ta komut çalıştırabilsin)
        try:
            from tools.sandbox import sandbox_shell
            safe_globals["sandbox_shell"] = sandbox_shell
        except:
            pass
        
        # Kodu çalıştır
        local_namespace = {}
        exec(code, safe_globals, local_namespace)
        
        # Fonksiyonu bul
        func = local_namespace.get(name)
        if not func or not callable(func):
            # İlk callable'ı bul
            for key, value in local_namespace.items():
                if callable(value) and not key.startswith("_"):
                    func = value
                    break
        
        if not func:
            logger.error(f"Function not found in code: {name}")
            return None
        
        # StructuredTool oluştur
        tool_instance = StructuredTool.from_function(
            func=func,
            name=name,
            description=description
        )
        
        logger.info(f"Tool created: {name}")
        return tool_instance
        
    except Exception as e:
        logger.error(f"Tool creation failed: {e}")
        return None


def register_tool_callback(callback: Callable):
    """Tool oluşturulduğunda çağrılacak callback"""
    global _on_tool_created
    _on_tool_created = callback


def get_custom_tools() -> List[StructuredTool]:
    """Tüm custom tool'ları döndür"""
    return list(_custom_tools.values())


def get_tool_list() -> List[dict]:
    """Tool listesini döndür (UI için)"""
    _load_registry()
    return [
        {
            "name": name,
            "description": info.get("description", ""),
            "created_at": info.get("created_at", ""),
            "enabled": info.get("enabled", True)
        }
        for name, info in _tool_registry.items()
    ]


@tool
def create_tool(name: str, description: str, python_code: str, run_in_sandbox: bool = False) -> str:
    """
    Yeni bir tool oluşturur. Tool, Python fonksiyonu olarak tanımlanır.
    
    Args:
        name: Tool adı (snake_case, örn: "calculate_sum")
        description: Tool'un ne yaptığını açıklayan metin
        python_code: Python fonksiyon kodu. Fonksiyon adı 'name' ile aynı olmalı.
        run_in_sandbox: True ise tool sandbox container'da çalışır (selenium, playwright vb. için)
    
    Returns:
        Başarı veya hata mesajı
    
    ÖNEMLI - İki mod var:
    
    1. Host modu (run_in_sandbox=False, varsayılan):
       - Hızlı, direkt çalışır
       - Sadece temel Python modülleri (requests, json, os, vb.)
       - Basit işlemler için
    
    2. Sandbox modu (run_in_sandbox=True):
       - Docker container'da çalışır
       - Tüm paketler kullanılabilir (selenium, playwright, pandas, vb.)
       - Browser automation, scraping, ağır işlemler için
       - Paket yoksa: sandbox_shell("pip install paket") ile kur
    
    Example (Host):
        create_tool(
            name="multiply_numbers",
            description="İki sayıyı çarpar",
            python_code='''
def multiply_numbers(a: int, b: int) -> int:
    return a * b
'''
        )
    
    Example (Sandbox - browser için):
        create_tool(
            name="get_page_title",
            description="Web sayfasının başlığını alır",
            run_in_sandbox=True,
            python_code='''
def get_page_title(url: str) -> str:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=opts)
    driver.get(url)
    title = driver.title
    driver.quit()
    return title
'''
        )
    """
    logger.info(f"Creating tool: {name} (sandbox={run_in_sandbox})")
    
    # İsim kontrolü
    if not name.replace("_", "").isalnum():
        return "❌ Tool adı sadece harf, rakam ve alt çizgi içerebilir"
    
    if name in _custom_tools:
        return f"❌ '{name}' adında bir tool zaten var. Önce delete_tool ile silin."
    
    # Tool oluştur
    if run_in_sandbox:
        tool_instance = _create_sandbox_tool(name, description, python_code)
    else:
        tool_instance = _create_tool_from_code(name, description, python_code)
    
    if not tool_instance:
        return "❌ Tool oluşturulamadı. Kod syntax hatası içeriyor olabilir."
    
    # Kaydet
    _custom_tools[name] = tool_instance
    
    _load_registry()
    _tool_registry[name] = {
        "description": description,
        "code": python_code,
        "created_at": datetime.now().isoformat(),
        "enabled": True,
        "sandbox": run_in_sandbox
    }
    _save_registry()
    
    # Dosyaya da kaydet
    tool_file = os.path.join(TOOLS_DIR, f"{name}.py")
    with open(tool_file, "w", encoding="utf-8") as f:
        f.write(f'"""\nCustom Tool: {name}\n{description}\n"""\n\n')
        f.write(python_code)
    
    # Callback çağır
    if _on_tool_created:
        _on_tool_created(name, tool_instance)
    
    return f"""✓ Tool oluşturuldu: {name}

📝 Açıklama: {description}
📁 Dosya: .custom_tools/{name}.py

Tool artık kullanıma hazır!"""


@tool
def list_custom_tools() -> str:
    """
    Oluşturulmuş custom tool'ları listeler.
    
    Returns:
        Tool listesi
    """
    _load_registry()
    
    if not _tool_registry:
        return "Henüz custom tool oluşturulmamış.\n\ncreate_tool() ile yeni tool oluşturabilirsiniz."
    
    lines = ["🔧 Custom Tools:\n"]
    
    for name, info in _tool_registry.items():
        status = "✅" if info.get("enabled", True) else "⏸️"
        desc = info.get("description", "")[:50]
        lines.append(f"{status} {name}")
        lines.append(f"   {desc}")
        lines.append("")
    
    lines.append(f"Toplam: {len(_tool_registry)} tool")
    
    return "\n".join(lines)


@tool
def delete_tool(name: str) -> str:
    """
    Custom tool'u siler.
    
    Args:
        name: Silinecek tool adı
    
    Returns:
        Sonuç mesajı
    """
    _load_registry()
    
    if name not in _tool_registry:
        return f"❌ Tool bulunamadı: {name}"
    
    # Registry'den sil
    del _tool_registry[name]
    _save_registry()
    
    # Memory'den sil
    if name in _custom_tools:
        del _custom_tools[name]
    
    # Dosyayı sil
    tool_file = os.path.join(TOOLS_DIR, f"{name}.py")
    if os.path.exists(tool_file):
        os.remove(tool_file)
    
    logger.info(f"Tool deleted: {name}")
    return f"✓ Tool silindi: {name}"


@tool
def get_tool_code(name: str) -> str:
    """
    Tool'un kaynak kodunu gösterir.
    
    Args:
        name: Tool adı
    
    Returns:
        Python kodu
    """
    _load_registry()
    
    if name not in _tool_registry:
        return f"❌ Tool bulunamadı: {name}"
    
    code = _tool_registry[name].get("code", "")
    
    return f"""📝 Tool: {name}

```python
{code}
```"""


@tool
def test_tool(name: str, test_input: str) -> str:
    """
    Custom tool'u test eder.
    
    Args:
        name: Test edilecek tool adı
        test_input: JSON formatında test girdisi (örn: '{"a": 5, "b": 3}')
    
    Returns:
        Test sonucu
    """
    if name not in _custom_tools:
        # Yüklemeyi dene
        load_custom_tools()
        
        if name not in _custom_tools:
            return f"❌ Tool bulunamadı veya yüklenemedi: {name}"
    
    try:
        # Input'u parse et
        inputs = json.loads(test_input)
        
        # Tool'u çağır
        tool_instance = _custom_tools[name]
        
        # Sandbox tool mu kontrol et
        _load_registry()
        is_sandbox = _tool_registry.get(name, {}).get("sandbox", False)
        
        if is_sandbox:
            # Sandbox tool - JSON string olarak geç
            result = tool_instance.func(tool_input=test_input)
        else:
            # Host tool - dict olarak geç
            result = tool_instance.invoke(inputs)
        
        return f"""✓ Test başarılı!

Input: {test_input}
Output: {result}"""
        
    except json.JSONDecodeError:
        return "❌ Geçersiz JSON formatı. Örnek: '{\"a\": 5, \"b\": 3}'"
    except Exception as e:
        return f"❌ Test hatası: {e}"


def load_custom_tools():
    """Kayıtlı tüm custom tool'ları yükle"""
    global _custom_tools
    
    _load_registry()
    
    for name, info in _tool_registry.items():
        if not info.get("enabled", True):
            continue
        
        if name in _custom_tools:
            continue
        
        code = info.get("code", "")
        description = info.get("description", "")
        is_sandbox = info.get("sandbox", False)
        
        # Sandbox veya host tool olarak yükle
        if is_sandbox:
            tool_instance = _create_sandbox_tool(name, description, code)
        else:
            tool_instance = _create_tool_from_code(name, description, code)
        
        if tool_instance:
            _custom_tools[name] = tool_instance
            mode = "sandbox" if is_sandbox else "host"
            logger.info(f"Loaded custom tool: {name} ({mode})")
    
    logger.info(f"Loaded {len(_custom_tools)} custom tools")


# Başlangıçta tool'ları yükle
load_custom_tools()
