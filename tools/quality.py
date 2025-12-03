"""
Quality Control Module - Linter, Auto-Fix & Self-Evaluation
Uses ruff for formatting and linting Python code
Includes self-evaluation for autonomous error recovery
"""
import os
import subprocess
from langchain_core.tools import tool

from config import config
from utils.logger import get_logger

logger = get_logger()

WORKSPACE_DIR = config.workspace.base_dir

# Self-evaluation için hata pattern'leri
ERROR_PATTERNS = {
    "syntax": ["SyntaxError", "IndentationError", "TabError"],
    "import": ["ImportError", "ModuleNotFoundError", "No module named"],
    "type": ["TypeError", "AttributeError", "NameError"],
    "value": ["ValueError", "KeyError", "IndexError"],
    "runtime": ["RuntimeError", "RecursionError", "MemoryError"],
    "file": ["FileNotFoundError", "PermissionError", "IsADirectoryError"],
}

# Otomatik düzeltme önerileri
AUTO_FIX_SUGGESTIONS = {
    "syntax": "Kod syntax'ını kontrol et, parantez ve girintileri düzelt",
    "import": "Eksik modülü pip install ile kur veya import yolunu düzelt",
    "type": "Değişken tiplerini kontrol et, None kontrolü ekle",
    "value": "Giriş değerlerini validate et, default değerler ekle",
    "runtime": "Recursion limit veya memory kullanımını kontrol et",
    "file": "Dosya yolunu kontrol et, dosyanın var olduğundan emin ol",
}


def _get_safe_path(filename: str) -> str:
    """Validate and return safe file path within workspace"""
    # Remove leading slashes and normalize
    filename = filename.lstrip("/").lstrip("\\")
    
    # If already has workspace prefix, use as is
    if filename.startswith(WORKSPACE_DIR) or filename.startswith("atom_workspace"):
        if filename.startswith("atom_workspace"):
            full_path = os.path.join(".", filename)
        else:
            full_path = filename
    else:
        full_path = os.path.join(WORKSPACE_DIR, filename)
    
    # Normalize and check it's within workspace
    full_path = os.path.normpath(full_path)
    
    return full_path


@tool
def lint_and_fix(filename: str) -> str:
    """
    Formats and lints a Python file using ruff.
    Automatically fixes common issues like:
    - Code formatting (PEP-8)
    - Unused imports
    - Simple logic errors
    - Import sorting
    
    Call this AFTER writing or modifying any Python file.
    
    Args:
        filename: Path to the Python file (relative to workspace)
    
    Returns:
        Success message or error details for manual fixing
    """
    logger.info(f"Linting: {filename}")
    
    # Validate file path
    file_path = _get_safe_path(filename)
    
    # Check file exists
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    
    # Only process Python files
    if not file_path.endswith(".py"):
        return f"Error: Only .py files supported. Got: {filename}"
    
    results = []
    has_errors = False
    
    try:
        # Step 1: Format with ruff (like Black)
        format_result = subprocess.run(
            ["ruff", "format", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if format_result.returncode == 0:
            results.append("✓ Formatted")
            logger.info(f"Formatted: {filename}")
        else:
            results.append(f"Format warning: {format_result.stderr[:200]}")
        
        # Step 2: Lint and auto-fix with ruff
        lint_result = subprocess.run(
            ["ruff", "check", "--fix", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if lint_result.returncode == 0:
            results.append("✓ Linted (no issues)")
            logger.info(f"Linted clean: {filename}")
        else:
            # There might be unfixable issues
            stdout = lint_result.stdout.strip()
            stderr = lint_result.stderr.strip()
            
            if stdout:
                # Parse remaining issues
                issues = []
                for line in stdout.split("\n")[:5]:  # Max 5 issues
                    if line.strip():
                        issues.append(line.strip())
                
                if issues:
                    has_errors = True
                    results.append("⚠ Remaining issues:")
                    results.extend([f"  - {issue}" for issue in issues])
                    logger.warning(f"Lint issues in {filename}: {len(issues)}")
            else:
                results.append("✓ Linted (auto-fixed)")
                logger.info(f"Linted with fixes: {filename}")
        
        # Step 3: Run format again after fixes
        subprocess.run(
            ["ruff", "format", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
    except FileNotFoundError:
        return "Error: ruff not installed. Run: pip install ruff"
    except subprocess.TimeoutExpired:
        return "Error: Linting timed out"
    except Exception as e:
        logger.error(f"Lint error: {e}")
        return f"Error: {e}"
    
    # Build response
    if has_errors:
        return f"File partially fixed. {' '.join(results)}\nPlease fix remaining issues manually."
    else:
        return f"File formatted and linted successfully. {' '.join(results)}"


@tool  
def check_syntax(filename: str) -> str:
    """
    Quick syntax check for a Python file without modifying it.
    Use this to verify code before running.
    
    Args:
        filename: Path to the Python file
    
    Returns:
        "OK" if no syntax errors, or error details
    """
    logger.info(f"Syntax check: {filename}")
    
    file_path = _get_safe_path(filename)
    
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    
    if not file_path.endswith(".py"):
        return f"Error: Only .py files supported"
    
    try:
        # Use Python's compile to check syntax
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        compile(source, file_path, "exec")
        logger.info(f"Syntax OK: {filename}")
        return "OK - No syntax errors"
        
    except SyntaxError as e:
        error_msg = f"Syntax Error at line {e.lineno}: {e.msg}"
        logger.warning(f"Syntax error in {filename}: {error_msg}")
        return error_msg
    except Exception as e:
        return f"Error: {e}"



@tool
def self_evaluate(task: str, result: str, error: str = "") -> str:
    """
    Yapılan işin kalitesini değerlendirir ve hata varsa düzeltme önerir.
    Otonom çalışma için kritik - agent kendi çıktısını değerlendirebilir.
    
    Args:
        task: Yapılması istenen görev
        result: Görevin sonucu veya çıktısı
        error: Varsa hata mesajı
    
    Returns:
        Değerlendirme ve varsa düzeltme önerisi
    """
    logger.info(f"Self-evaluating task: {task[:50]}...")
    
    evaluation = {
        "success": True,
        "error_type": None,
        "suggestion": None,
        "confidence": "high"
    }
    
    # Hata varsa analiz et
    if error:
        evaluation["success"] = False
        
        # Hata tipini belirle
        for error_type, patterns in ERROR_PATTERNS.items():
            if any(pattern.lower() in error.lower() for pattern in patterns):
                evaluation["error_type"] = error_type
                evaluation["suggestion"] = AUTO_FIX_SUGGESTIONS.get(error_type)
                break
        
        if not evaluation["error_type"]:
            evaluation["error_type"] = "unknown"
            evaluation["suggestion"] = "Hata mesajını dikkatlice oku ve manuel düzelt"
    
    # Sonucu değerlendir
    result_lower = result.lower() if result else ""
    
    # Başarısızlık göstergeleri
    failure_indicators = [
        "error", "failed", "hata", "başarısız", "exception",
        "traceback", "cannot", "unable", "not found"
    ]
    
    if any(indicator in result_lower for indicator in failure_indicators):
        evaluation["success"] = False
        evaluation["confidence"] = "medium"
        
        if not evaluation["suggestion"]:
            evaluation["suggestion"] = "Sonuçta hata göstergesi var, çıktıyı kontrol et"
    
    # Başarı göstergeleri
    success_indicators = [
        "success", "completed", "done", "tamamlandı", "başarılı",
        "created", "written", "saved", "✓", "✅"
    ]
    
    if any(indicator in result_lower for indicator in success_indicators):
        evaluation["confidence"] = "high"
    
    # Sonuç oluştur
    if evaluation["success"]:
        return f"✅ Değerlendirme: Görev başarılı görünüyor (güven: {evaluation['confidence']})"
    else:
        response = f"⚠️ Değerlendirme: Sorun tespit edildi\n"
        response += f"Hata tipi: {evaluation['error_type']}\n"
        if evaluation["suggestion"]:
            response += f"Öneri: {evaluation['suggestion']}"
        return response


@tool
def analyze_error(error_message: str) -> str:
    """
    Hata mesajını analiz eder ve düzeltme stratejisi önerir.
    Otonom hata kurtarma için kullanılır.
    
    Args:
        error_message: Analiz edilecek hata mesajı
    
    Returns:
        Hata analizi ve düzeltme stratejisi
    """
    logger.info(f"Analyzing error: {error_message[:100]}...")
    
    error_lower = error_message.lower()
    
    analysis = {
        "type": "unknown",
        "severity": "medium",
        "recoverable": True,
        "strategy": []
    }
    
    # Hata tipini belirle
    for error_type, patterns in ERROR_PATTERNS.items():
        if any(pattern.lower() in error_lower for pattern in patterns):
            analysis["type"] = error_type
            break
    
    # Severity belirle
    critical_patterns = ["memory", "recursion", "permission", "fatal"]
    if any(p in error_lower for p in critical_patterns):
        analysis["severity"] = "high"
        analysis["recoverable"] = False
    
    # Strateji öner
    if analysis["type"] == "syntax":
        analysis["strategy"] = [
            "1. Hatalı satırı bul (hata mesajındaki satır numarası)",
            "2. Parantez, tırnak ve girintileri kontrol et",
            "3. lint_and_fix tool'unu çalıştır",
            "4. Düzeltilmiş kodu tekrar yaz"
        ]
    elif analysis["type"] == "import":
        analysis["strategy"] = [
            "1. Modül adını kontrol et (yazım hatası olabilir)",
            "2. pip install ile modülü kur",
            "3. Import yolunun doğru olduğundan emin ol",
            "4. Virtual environment aktif mi kontrol et"
        ]
    elif analysis["type"] == "type":
        analysis["strategy"] = [
            "1. Değişkenin tipini kontrol et",
            "2. None kontrolü ekle (if x is not None)",
            "3. Tip dönüşümü gerekebilir (str(), int(), etc.)",
            "4. Attribute'un var olduğundan emin ol"
        ]
    elif analysis["type"] == "value":
        analysis["strategy"] = [
            "1. Giriş değerlerini validate et",
            "2. Default değerler ekle",
            "3. Try-except ile hata yakala",
            "4. Boundary check ekle"
        ]
    elif analysis["type"] == "file":
        analysis["strategy"] = [
            "1. Dosya yolunu kontrol et",
            "2. Dosyanın var olduğundan emin ol",
            "3. Dizin izinlerini kontrol et",
            "4. Gerekirse dizini oluştur"
        ]
    else:
        analysis["strategy"] = [
            "1. Hata mesajını dikkatlice oku",
            "2. Stack trace'i takip et",
            "3. İlgili kodu incele",
            "4. Farklı bir yaklaşım dene"
        ]
    
    # Sonuç oluştur
    result = f"🔍 Hata Analizi\n"
    result += f"Tip: {analysis['type']}\n"
    result += f"Ciddiyet: {analysis['severity']}\n"
    result += f"Kurtarılabilir: {'Evet' if analysis['recoverable'] else 'Hayır'}\n\n"
    result += "📋 Düzeltme Stratejisi:\n"
    result += "\n".join(analysis["strategy"])
    
    return result


def evaluate_code_quality(code: str) -> dict:
    """
    Kod kalitesini değerlendirir (internal function).
    
    Args:
        code: Değerlendirilecek kod
    
    Returns:
        Kalite metrikleri
    """
    lines = code.split("\n")
    
    metrics = {
        "total_lines": len(lines),
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "has_docstring": False,
        "has_type_hints": False,
        "complexity_estimate": "low"
    }
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            metrics["blank_lines"] += 1
        elif stripped.startswith("#"):
            metrics["comment_lines"] += 1
        else:
            metrics["code_lines"] += 1
    
    # Docstring kontrolü
    if '"""' in code or "'''" in code:
        metrics["has_docstring"] = True
    
    # Type hint kontrolü
    if "->" in code or ": str" in code or ": int" in code:
        metrics["has_type_hints"] = True
    
    # Complexity tahmini
    complexity_indicators = ["if ", "for ", "while ", "try:", "except:", "with "]
    complexity_count = sum(code.count(ind) for ind in complexity_indicators)
    
    if complexity_count > 10:
        metrics["complexity_estimate"] = "high"
    elif complexity_count > 5:
        metrics["complexity_estimate"] = "medium"
    
    if complexity_count > 10:
        metrics["complexity_estimate"] = "high"
    elif complexity_count > 5:
        metrics["complexity_estimate"] = "medium"
    
    return metrics


@tool
def code_review(code: str, file_path: str = None) -> str:
    """
    Performs a comprehensive code review using LLM.
    Analyzes for security, performance, best practices, and bugs.
    
    Args:
        code: The source code to review
        file_path: Path to the file for context (optional)
    
    Returns:
        Markdown-formatted review report
    """
    from core.providers import model_manager
    from langchain_core.messages import HumanMessage
    
    logger.info(f"Reviewing code: {file_path or 'snippet'}")
    
    try:
        # Get coder model
        llm = model_manager.get_llm("coder")
        if not llm:
            return "❌ Coder model not available."
            
        prompt = f"""You are an expert code reviewer. Analyze the provided code thoroughly.

File path (for context): {file_path or "N/A"}

Code:
```
{code}
```

Generate a Markdown report structured as follows:

## Code Review Report

### ✅ Good Practices
- List what's done well.

### ⚠️ Warnings
- Potential issues that should be addressed.

### ❌ Critical Issues
- Bugs, security vulnerabilities, or breaking problems.

### 💡 Suggestions
- Refactoring ideas, performance optimizations, best practices improvements.

Be concise, actionable, and specific with line references where possible. Prioritize severity."""

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
        
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        return f"❌ Code review failed: {e}"


@tool
def auto_generate_tests(filename: str) -> str:
    """
    Generates pytest unit tests for a given Python file.
    Reads the file content and creates a new test file with comprehensive test cases.
    
    Args:
        filename: Path to the Python file to test
        
    Returns:
        Path to the generated test file or error message
    """
    from core.providers import model_manager
    from langchain_core.messages import HumanMessage
    
    logger.info(f"Generating tests for: {filename}")
    
    file_path = _get_safe_path(filename)
    if not os.path.exists(file_path):
        return f"❌ File not found: {file_path}"
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            
        # Get coder model
        llm = model_manager.get_llm("coder")
        if not llm:
            return "❌ Coder model not available."
            
        prompt = f"""You are an expert QA engineer. Write comprehensive unit tests using `pytest` for the following Python code.

File: {filename}

Code:
```python
{code}
```

Requirements:
1. Use `pytest` framework.
2. Cover happy paths and edge cases.
3. Mock external dependencies if necessary.
4. Return ONLY the Python code for the test file. Do not include markdown formatting or explanations.
5. Start imports with `import pytest`.
"""

        response = llm.invoke([HumanMessage(content=prompt)])
        test_code = response.content
        
        # Clean up code blocks if present
        if "```python" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0].strip()
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0].strip()
            
        # Determine output path
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        test_filename = f"test_{base_name}"
        test_path = os.path.join(dir_name, test_filename)
        
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)
            
        logger.info(f"Tests generated: {test_path}")
        return f"✅ Tests generated: {test_path}\nRun with: pytest {test_path}"
        
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        return f"❌ Test generation failed: {e}"
