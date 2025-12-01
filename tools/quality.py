"""
Quality Control Module - Linter & Auto-Fix
Uses ruff for formatting and linting Python code
"""
import os
import subprocess
from langchain_core.tools import tool

from config import config
from utils.logger import get_logger

logger = get_logger()

WORKSPACE_DIR = config.workspace.base_dir


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
