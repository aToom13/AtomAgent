"""
Test Runner Tools - pytest/unittest integration
"""
import subprocess
import os
import json
from langchain_core.tools import tool
from config import config
from utils.logger import get_logger

WORKSPACE_DIR = config.workspace.base_dir
logger = get_logger()


def _run_command(cmd: list, cwd: str = None, timeout: int = 60) -> tuple[int, str, str]:
    """Run command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Test zaman aşımına uğradı"
    except Exception as e:
        return -1, "", str(e)


@tool
def run_tests(path: str = ".", verbose: bool = False) -> str:
    """
    Testleri çalıştırır (pytest kullanarak).
    
    Args:
        path: Test dosyası veya klasörü (varsayılan: tüm workspace)
        verbose: Detaylı çıktı (varsayılan: False)
    
    Returns:
        Test sonuçları özeti
    """
    logger.info(f"Running tests: {path}")
    
    # Build pytest command
    cmd = ["python", "-m", "pytest", path, "--tb=short"]
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    returncode, stdout, stderr = _run_command(cmd, timeout=120)
    
    # Parse results
    output_lines = stdout.split("\n")
    result_parts = ["🧪 Test Sonuçları:", ""]
    
    # Find summary line
    for line in output_lines:
        if "passed" in line or "failed" in line or "error" in line:
            result_parts.append(f"  {line.strip()}")
        elif line.startswith("FAILED") or line.startswith("ERROR"):
            result_parts.append(f"  ❌ {line}")
        elif line.startswith("PASSED"):
            result_parts.append(f"  ✅ {line}")
    
    if returncode == 0:
        result_parts.insert(1, "✅ Tüm testler başarılı!")
        logger.info("All tests passed")
    elif returncode == 1:
        result_parts.insert(1, "❌ Bazı testler başarısız!")
        logger.warning("Some tests failed")
    elif returncode == 5:
        result_parts.insert(1, "⚠️ Test bulunamadı")
    else:
        result_parts.insert(1, f"⚠️ Test hatası (kod: {returncode})")
        if stderr:
            result_parts.append(f"\nHata: {stderr[:500]}")
    
    # Add stdout if verbose or failed
    if verbose or returncode != 0:
        if stdout:
            result_parts.append("\n📋 Detay:")
            result_parts.append(stdout[:1500])
    
    return "\n".join(result_parts)


@tool
def run_single_test(test_path: str) -> str:
    """
    Tek bir test dosyası veya fonksiyonu çalıştırır.
    
    Args:
        test_path: Test yolu. Örnekler:
            - "test_calculator.py" (dosya)
            - "test_calculator.py::test_add" (fonksiyon)
            - "test_calculator.py::TestMath::test_add" (class method)
    """
    logger.info(f"Running single test: {test_path}")
    
    cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=long"]
    returncode, stdout, stderr = _run_command(cmd, timeout=60)
    
    result = ["🧪 Test Sonucu:", ""]
    
    if returncode == 0:
        result.append(f"✅ {test_path} - BAŞARILI")
    else:
        result.append(f"❌ {test_path} - BAŞARISIZ")
    
    result.append("")
    result.append(stdout[:2000] if stdout else stderr[:500])
    
    return "\n".join(result)


@tool
def create_test_file(module_name: str) -> str:
    """
    Bir modül için test dosyası şablonu oluşturur.
    
    Args:
        module_name: Test edilecek modül adı (örn: "calculator")
    
    Returns:
        Oluşturulan test dosyasının yolu
    """
    test_filename = f"test_{module_name}.py"
    test_path = os.path.join(WORKSPACE_DIR, test_filename)
    
    # Check if module exists
    module_path = os.path.join(WORKSPACE_DIR, f"{module_name}.py")
    
    template = f'''"""
Tests for {module_name} module
"""
import pytest
'''
    
    # Try to import and analyze module
    if os.path.exists(module_path):
        template += f"from {module_name} import *\n"
        template += "\n\n"
        template += "# TODO: Add your tests here\n\n"
        template += f'''
class Test{module_name.title().replace("_", "")}:
    """Test class for {module_name}"""
    
    def test_example(self):
        """Example test - replace with real tests"""
        # Arrange
        expected = True
        
        # Act
        result = True  # Replace with actual function call
        
        # Assert
        assert result == expected
    
    def test_another_example(self):
        """Another example test"""
        pass


# Standalone test functions
def test_basic():
    """Basic functionality test"""
    assert True


def test_edge_case():
    """Edge case test"""
    pass
'''
    else:
        template += "\n\n"
        template += f"# Module '{module_name}.py' not found\n"
        template += "# Create the module first, then update these tests\n\n"
        template += '''
def test_placeholder():
    """Placeholder test"""
    assert True
'''
    
    # Write file
    try:
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(template)
        
        logger.info(f"Test file created: {test_filename}")
        return f"✓ Test dosyası oluşturuldu: {test_filename}"
    except Exception as e:
        return f"✗ Hata: {e}"


@tool
def list_tests(path: str = ".") -> str:
    """
    Mevcut testleri listeler.
    
    Args:
        path: Aranacak klasör (varsayılan: workspace)
    """
    cmd = ["python", "-m", "pytest", path, "--collect-only", "-q"]
    returncode, stdout, stderr = _run_command(cmd, timeout=30)
    
    if returncode == 5:
        return "⚠️ Test dosyası bulunamadı"
    
    if returncode != 0 and not stdout:
        return f"✗ Hata: {stderr[:300]}"
    
    lines = stdout.strip().split("\n")
    tests = [line for line in lines if "::" in line]
    
    if not tests:
        return "⚠️ Test bulunamadı"
    
    result = [f"📋 Bulunan Testler ({len(tests)} adet):", ""]
    
    current_file = ""
    for test in tests[:30]:  # Max 30 test göster
        parts = test.split("::")
        file = parts[0]
        
        if file != current_file:
            current_file = file
            result.append(f"\n📄 {file}:")
        
        if len(parts) > 1:
            result.append(f"  • {parts[-1]}")
    
    if len(tests) > 30:
        result.append(f"\n... ve {len(tests) - 30} test daha")
    
    return "\n".join(result)


@tool
def test_coverage(path: str = ".") -> str:
    """
    Test coverage raporu oluşturur.
    
    Args:
        path: Test edilecek klasör
    """
    # Check if coverage is installed
    cmd = ["python", "-m", "pytest", path, "--cov=.", "--cov-report=term-missing", "-q"]
    returncode, stdout, stderr = _run_command(cmd, timeout=120)
    
    if "No module named" in stderr and "coverage" in stderr:
        return "⚠️ Coverage yüklü değil. Yüklemek için: pip install pytest-cov"
    
    if returncode == 5:
        return "⚠️ Test bulunamadı"
    
    result = ["📊 Coverage Raporu:", ""]
    
    # Parse coverage output
    lines = stdout.split("\n")
    in_coverage = False
    
    for line in lines:
        if "TOTAL" in line or "Name" in line or "---" in line:
            in_coverage = True
        if in_coverage and line.strip():
            result.append(line)
        if "passed" in line or "failed" in line:
            result.append("")
            result.append(line)
    
    return "\n".join(result) if len(result) > 2 else stdout[:1500]


@tool
def run_unittest(test_file: str) -> str:
    """
    unittest modülü ile test çalıştırır (pytest yoksa alternatif).
    
    Args:
        test_file: Test dosyası adı
    """
    logger.info(f"Running unittest: {test_file}")
    
    # Remove .py extension if present
    module = test_file.replace(".py", "")
    
    cmd = ["python", "-m", "unittest", module, "-v"]
    returncode, stdout, stderr = _run_command(cmd, timeout=60)
    
    output = stdout + stderr
    
    result = ["🧪 Unittest Sonuçları:", ""]
    
    if "OK" in output:
        result.append("✅ Tüm testler başarılı!")
    elif "FAILED" in output:
        result.append("❌ Bazı testler başarısız!")
    else:
        result.append("⚠️ Test durumu belirsiz")
    
    result.append("")
    result.append(output[:1500])
    
    return "\n".join(result)
