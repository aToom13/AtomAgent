"""
Code Highlighter Widget - Chat içindeki kod bloklarını renklendirir
"""
import re
from rich.text import Text
from rich.syntax import Syntax
from rich.console import Console
from io import StringIO


# Dil algılama için pattern'ler
LANGUAGE_PATTERNS = {
    "python": [
        r"^import\s+\w+", r"^from\s+\w+\s+import", r"^def\s+\w+\s*\(",
        r"^class\s+\w+", r"print\(", r"if\s+__name__\s*==",
        r"\.py$", r"self\.", r"async\s+def"
    ],
    "javascript": [
        r"^const\s+\w+", r"^let\s+\w+", r"^var\s+\w+",
        r"^function\s+\w+", r"=>\s*{", r"console\.log",
        r"\.js$", r"require\(", r"module\.exports"
    ],
    "typescript": [
        r":\s*(string|number|boolean|any)", r"interface\s+\w+",
        r"type\s+\w+\s*=", r"\.ts$", r"<\w+>"
    ],
    "html": [
        r"<html", r"<div", r"<span", r"<body", r"<head",
        r"<!DOCTYPE", r"</\w+>", r"\.html$"
    ],
    "css": [
        r"{\s*\w+\s*:", r"@media", r"@import", r"\.css$",
        r"#\w+\s*{", r"\.\w+\s*{"
    ],
    "json": [
        r'^{\s*"', r'^\[\s*{', r'"\s*:\s*["\d\[\{]', r"\.json$"
    ],
    "bash": [
        r"^#!/bin/bash", r"^\$\s+", r"^echo\s+", r"^sudo\s+",
        r"\.sh$", r"^apt\s+", r"^pip\s+", r"^npm\s+"
    ],
    "sql": [
        r"^SELECT\s+", r"^INSERT\s+", r"^UPDATE\s+", r"^DELETE\s+",
        r"^CREATE\s+TABLE", r"\.sql$", r"FROM\s+\w+"
    ],
    "yaml": [
        r"^\w+:\s*$", r"^\s+-\s+\w+", r"\.ya?ml$"
    ],
    "markdown": [
        r"^#+\s+", r"^\*\*\w+", r"^-\s+\[", r"\.md$"
    ]
}


def detect_language(code: str, hint: str = "") -> str:
    """
    Kod dilini algıla.
    
    Args:
        code: Kod içeriği
        hint: Dil ipucu (dosya uzantısı veya belirtilen dil)
    
    Returns:
        Algılanan dil adı
    """
    # Hint varsa önce onu kontrol et
    if hint:
        hint_lower = hint.lower().strip()
        # Yaygın alias'lar
        aliases = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "sh": "bash",
            "shell": "bash",
            "yml": "yaml"
        }
        if hint_lower in aliases:
            return aliases[hint_lower]
        if hint_lower in LANGUAGE_PATTERNS:
            return hint_lower
    
    # Pattern matching ile algıla
    scores = {lang: 0 for lang in LANGUAGE_PATTERNS}
    
    for lang, patterns in LANGUAGE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                scores[lang] += 1
    
    # En yüksek skoru bul
    best_lang = max(scores, key=scores.get)
    if scores[best_lang] > 0:
        return best_lang
    
    return "text"


def highlight_code(code: str, language: str = "") -> Text:
    """
    Kodu syntax highlighting ile renklendir.
    
    Args:
        code: Kod içeriği
        language: Dil (boşsa otomatik algıla)
    
    Returns:
        Rich Text objesi
    """
    if not language:
        language = detect_language(code)
    
    try:
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=False,
            word_wrap=True
        )
        
        # Syntax'ı Text'e çevir
        console = Console(file=StringIO(), force_terminal=True)
        console.print(syntax)
        
        # Rich Text olarak döndür
        return Text.from_markup(f"[dim]```{language}[/dim]\n") + Text(code) + Text("\n[dim]```[/dim]")
    except:
        # Fallback: düz text
        return Text(f"```{language}\n{code}\n```")


def parse_message_with_code(message: str) -> Text:
    """
    Mesajdaki kod bloklarını algıla ve renklendir.
    
    Args:
        message: İşlenecek mesaj
    
    Returns:
        Rich Text objesi
    """
    result = Text()
    
    # Kod bloğu pattern'i: ```language\ncode\n``` veya ```\ncode\n```
    code_block_pattern = r"```(\w*)\n(.*?)```"
    
    last_end = 0
    for match in re.finditer(code_block_pattern, message, re.DOTALL):
        # Kod bloğundan önceki text
        if match.start() > last_end:
            result.append(message[last_end:match.start()])
        
        # Kod bloğu
        language = match.group(1) or ""
        code = match.group(2).strip()
        
        # Dil algıla
        if not language:
            language = detect_language(code)
        
        # Kod bloğunu ekle
        result.append(f"\n[dim]```{language}[/dim]\n", style="dim")
        
        # Basit syntax highlighting
        highlighted = simple_highlight(code, language)
        result.append_text(highlighted)
        
        result.append("\n[dim]```[/dim]\n", style="dim")
        
        last_end = match.end()
    
    # Kalan text
    if last_end < len(message):
        result.append(message[last_end:])
    
    return result


def simple_highlight(code: str, language: str) -> Text:
    """
    Basit syntax highlighting (Rich Syntax kullanmadan).
    Terminal uyumluluğu için.
    
    Args:
        code: Kod
        language: Dil
    
    Returns:
        Rich Text
    """
    text = Text()
    
    # Dile göre keyword'ler
    keywords = {
        "python": ["def", "class", "import", "from", "if", "else", "elif", 
                   "for", "while", "try", "except", "finally", "with", "as",
                   "return", "yield", "raise", "pass", "break", "continue",
                   "and", "or", "not", "in", "is", "None", "True", "False",
                   "async", "await", "lambda", "global", "nonlocal"],
        "javascript": ["function", "const", "let", "var", "if", "else",
                       "for", "while", "do", "switch", "case", "break",
                       "return", "try", "catch", "finally", "throw",
                       "class", "extends", "new", "this", "super",
                       "import", "export", "default", "async", "await",
                       "true", "false", "null", "undefined"],
        "bash": ["if", "then", "else", "fi", "for", "do", "done", "while",
                 "case", "esac", "function", "return", "exit", "echo",
                 "export", "source", "alias"],
    }
    
    lang_keywords = keywords.get(language, [])
    
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if i > 0:
            text.append("\n")
        
        # Yorum satırı
        if line.strip().startswith("#") or line.strip().startswith("//"):
            text.append(line, style="dim green")
            continue
        
        # String'ler
        if '"""' in line or "'''" in line:
            text.append(line, style="yellow")
            continue
        
        # Keyword highlighting
        words = re.split(r'(\s+|[(){}[\]:,.])', line)
        for word in words:
            if word in lang_keywords:
                text.append(word, style="bold magenta")
            elif word.startswith('"') or word.startswith("'"):
                text.append(word, style="yellow")
            elif word.isdigit():
                text.append(word, style="cyan")
            elif word.startswith("@"):
                text.append(word, style="blue")
            else:
                text.append(word)
    
    return text


class CodeBlockWidget:
    """Kod bloğu yönetimi için yardımcı sınıf"""
    
    @staticmethod
    def extract_code_blocks(text: str) -> list:
        """
        Metinden kod bloklarını çıkar.
        
        Returns:
            List of (language, code) tuples
        """
        blocks = []
        pattern = r"```(\w*)\n(.*?)```"
        
        for match in re.finditer(pattern, text, re.DOTALL):
            language = match.group(1) or detect_language(match.group(2))
            code = match.group(2).strip()
            blocks.append((language, code))
        
        return blocks
    
    @staticmethod
    def format_code_block(code: str, language: str = "") -> str:
        """
        Kod bloğunu markdown formatında döndür.
        """
        if not language:
            language = detect_language(code)
        return f"```{language}\n{code}\n```"
