"""
Web Tools - Optimized web search and content extraction
"""
import json
import time
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from utils.logger import get_logger

logger = get_logger()

# Güvenilir siteler - öncelikli
TRUSTED_DOMAINS = [
    # Kod & Geliştirici
    "github.com", "gitlab.com", "bitbucket.org",
    "stackoverflow.com", "stackexchange.com", "superuser.com",
    "dev.to", "medium.com", "hashnode.dev", "freecodecamp.org",
    
    # Python
    "docs.python.org", "pypi.org", "realpython.com", "pythonbasics.org",
    "learnpython.org", "python.org", "peps.python.org",
    
    # JavaScript/Web
    "developer.mozilla.org", "javascript.info", "nodejs.org",
    "npmjs.com", "yarnpkg.com", "reactjs.org", "vuejs.org",
    "angular.io", "typescriptlang.org", "nextjs.org",
    
    # Genel Programlama
    "w3schools.com", "geeksforgeeks.org", "tutorialspoint.com",
    "javatpoint.com", "programiz.com", "codecademy.com",
    "hackerrank.com", "leetcode.com", "codewars.com",
    
    # Cloud & DevOps
    "docs.microsoft.com", "learn.microsoft.com", "azure.microsoft.com",
    "cloud.google.com", "firebase.google.com",
    "aws.amazon.com", "docs.aws.amazon.com",
    "digitalocean.com", "heroku.com", "vercel.com", "netlify.com",
    "docker.com", "kubernetes.io", "terraform.io",
    
    # Veritabanı
    "postgresql.org", "mysql.com", "mongodb.com", "redis.io",
    "sqlite.org", "mariadb.org",
    
    # AI/ML
    "huggingface.co", "pytorch.org", "tensorflow.org",
    "scikit-learn.org", "keras.io", "openai.com",
    
    # Diğer Faydalı
    "wikipedia.org", "wikimedia.org", "arxiv.org",
    "readthedocs.io", "gitbook.io", "notion.so"
]

# Kaçınılacak siteler - spam, reklam dolu
BLOCKED_DOMAINS = [
    "pinterest.com", "facebook.com", "twitter.com", "instagram.com",
    "tiktok.com", "linkedin.com", "quora.com", "reddit.com",
    "youtube.com", "vimeo.com", "dailymotion.com"
]


def _is_trusted(url: str) -> bool:
    """Check if URL is from a trusted domain"""
    return any(domain in url.lower() for domain in TRUSTED_DOMAINS)


def _is_blocked(url: str) -> bool:
    """Check if URL should be blocked"""
    return any(domain in url.lower() for domain in BLOCKED_DOMAINS)


def _clean_text(text: str, max_length: int = 500) -> str:
    """Clean and truncate text"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text


@tool
def web_search(query: str, max_results: int = 8) -> str:
    """
    Web'de arama yapar ve özet sonuçlar döndürür.
    Sayfaları ziyaret ETMEZ, sadece arama sonuçlarını listeler.
    
    Args:
        query: Arama sorgusu
        max_results: Maksimum sonuç sayısı (varsayılan 8)
    
    Returns:
        Arama sonuçları özeti
    """
    logger.info(f"Web search: {query}")
    
    try:
        # DuckDuckGo ile arama - daha fazla sonuç al
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(
                query, 
                max_results=max_results * 3,  # Daha fazla al, sonra filtrele
                region='wt-wt',  # Worldwide
                safesearch='moderate'
            ))
        
        if not raw_results:
            # Alternatif: news araması dene
            logger.info("Text search empty, trying news...")
            with DDGS() as ddgs:
                raw_results = list(ddgs.news(query, max_results=max_results))
        
        if not raw_results:
            return f"'{query}' için sonuç bulunamadı. Farklı anahtar kelimeler deneyin."
        
        # Filter and sort results
        results = []
        seen_urls = set()
        
        for r in raw_results:
            url = r.get('href', r.get('url', ''))
            
            # Skip duplicates
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Skip blocked domains
            if _is_blocked(url):
                continue
            
            # Skip empty results
            title = r.get('title', '')
            snippet = r.get('body', r.get('description', ''))
            if not title or not snippet:
                continue
            
            # Prioritize trusted domains
            is_trusted = _is_trusted(url)
            
            results.append({
                "title": title[:120],
                "url": url,
                "snippet": _clean_text(snippet, 250),
                "trusted": is_trusted
            })
        
        # Sort: trusted first, then by title length (longer = more descriptive)
        results.sort(key=lambda x: (not x['trusted'], -len(x['snippet'])))
        results = results[:max_results]
        
        if not results:
            return f"'{query}' için uygun sonuç bulunamadı. Sorguyu değiştirmeyi deneyin."
        
        # Format output - daha detaylı
        output = [f"🔍 '{query}' için {len(results)} sonuç bulundu:\n"]
        
        for i, r in enumerate(results, 1):
            trust_icon = "⭐" if r['trusted'] else "•"
            output.append(f"{trust_icon} [{i}] {r['title']}")
            output.append(f"   🔗 {r['url']}")
            output.append(f"   📝 {r['snippet']}\n")
        
        output.append("\n💡 Detaylı bilgi için visit_webpage(url) kullanın.")
        
        logger.info(f"Found {len(results)} results for '{query}'")
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Arama hatası: {e}. Lütfen tekrar deneyin."


@tool
def quick_answer(question: str) -> str:
    """
    Hızlı cevap almak için kullan. Sayfa ziyaret etmeden
    DuckDuckGo instant answer API kullanır.
    
    Args:
        question: Soru (örn: "Python version", "React nedir")
    
    Returns:
        Kısa cevap veya "Cevap bulunamadı"
    """
    logger.info(f"Quick answer: {question}")
    
    try:
        # Try instant answers first
        with DDGS() as ddgs:
            answers = list(ddgs.answers(question))
            if answers:
                answer = answers[0]
                text = answer.get('text', '')
                url = answer.get('url', '')
                if text:
                    result = f"💡 {text}"
                    if url:
                        result += f"\n🔗 {url}"
                    return result
        
        # Try Wikipedia-style search
        wiki_query = f"{question} site:wikipedia.org"
        with DDGS() as ddgs:
            results = list(ddgs.text(wiki_query, max_results=1))
            if results:
                r = results[0]
                return f"📚 {r.get('title', '')}\n{_clean_text(r.get('body', ''), 400)}\n🔗 {r.get('href', '')}"
        
        # Fallback to regular search
        with DDGS() as ddgs:
            results = list(ddgs.text(question, max_results=3))
            if results:
                output = []
                for r in results[:2]:
                    output.append(f"📝 {r.get('title', '')}")
                    output.append(f"   {_clean_text(r.get('body', ''), 200)}")
                return "\n".join(output)
        
        return f"'{question}' için cevap bulunamadı. web_search() ile detaylı arama yapabilirsiniz."
        
    except Exception as e:
        logger.error(f"Quick answer failed: {e}")
        return f"Hata: {e}"


@tool
def visit_webpage(url: str) -> str:
    """
    Bir web sayfasını ziyaret eder ve içeriğini çıkarır.
    SADECE güvenilir kaynaklardan bilgi almak için kullan.
    Token tasarrufu için içerik kısaltılır.
    
    Args:
        url: Ziyaret edilecek URL
    
    Returns:
        Sayfa içeriği (kısaltılmış)
    """
    logger.info(f"Visiting: {url}")
    
    # Warn if not trusted
    if _is_blocked(url):
        return f"⚠️ Bu site ({url}) engellendi. Farklı kaynak kullanın."
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header", 
                         "aside", "form", "button", "iframe", "noscript"]):
            tag.decompose()
        
        # Try to find main content
        main_content = (
            soup.find("main") or 
            soup.find("article") or 
            soup.find(class_=["content", "post", "entry", "article-body"]) or
            soup.find("body")
        )
        
        if not main_content:
            main_content = soup
        
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        
        # Clean up
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        # Remove very short lines (likely menu items)
        lines = [line for line in lines if len(line) > 20 or line.endswith(':')]
        text = '\n'.join(lines)
        
        # Truncate - daha kısa limit
        max_length = 3000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n...[Kısaltıldı]"
        
        if not text.strip():
            return "Sayfa içeriği çıkarılamadı."
        
        trust_note = "⭐ Güvenilir kaynak" if _is_trusted(url) else ""
        return f"{trust_note}\n📄 {url}\n\n{text}"
        
    except requests.Timeout:
        return f"⏱️ Zaman aşımı: {url}"
    except requests.RequestException as e:
        return f"❌ Bağlantı hatası: {e}"
    except Exception as e:
        logger.error(f"Visit failed: {e}")
        return f"❌ Hata: {e}"


@tool
def search_docs(query: str, site: str = "python") -> str:
    """
    Belirli dokümantasyon sitelerinde arama yapar.
    
    Args:
        query: Arama sorgusu
        site: Hedef site - "python", "mdn", "npm", "github"
    
    Returns:
        Arama sonuçları
    """
    site_map = {
        "python": "site:docs.python.org",
        "mdn": "site:developer.mozilla.org",
        "npm": "site:npmjs.com",
        "github": "site:github.com",
        "stackoverflow": "site:stackoverflow.com",
        "pypi": "site:pypi.org"
    }
    
    site_filter = site_map.get(site.lower(), "")
    full_query = f"{query} {site_filter}".strip()
    
    logger.info(f"Docs search: {full_query}")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(full_query, max_results=3))
        
        if not results:
            return f"'{query}' için {site} dokümanlarında sonuç bulunamadı."
        
        output = [f"📚 {site.upper()} Dokümanları - '{query}':\n"]
        
        for i, r in enumerate(results, 1):
            output.append(f"[{i}] {r.get('title', '')[:80]}")
            output.append(f"    {r.get('href', '')}")
            output.append(f"    {_clean_text(r.get('body', ''), 150)}\n")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Docs search failed: {e}")
        return f"Arama hatası: {e}"


@tool
def get_page_title(url: str) -> str:
    """
    Web sayfasının başlığını alır.
    
    Args:
        url: Sayfa URL'i
    
    Returns:
        Sayfa başlığı veya hata mesajı
    """
    try:
        if _is_blocked(url):
            return f"⚠️ Bu site ({url}) engellendi."
            
    except Exception as e:
        return f"❌ Hata: {str(e)}"


@tool
def browse_site(url: str) -> str:
    """
    Opens a URL in a browser inside the Docker sandbox.
    The browser runs inside VNC so you can see and interact with it.
    
    Args:
        url: URL to visit
        
    Returns:
        Status message
    """
    import subprocess
    from tools.sandbox import _is_container_running, DOCKER_DIR
    
    logger.info(f"Browsing in VNC: {url}")
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Check if container is running
    if not _is_container_running():
        return "❌ Sandbox is not running. Use sandbox_start first."
    
    try:
        # Start VNC if not already running
        subprocess.run(
            ["docker", "exec", "atomagent-sandbox", "bash", "-c", 
             "pgrep -x Xvfb || /home/agent/start-vnc.sh"],
            capture_output=True, text=True, timeout=15, cwd=DOCKER_DIR
        )
        
        # Open URL in Chromium inside Docker - fullscreen mode
        # Kill existing browser first, then open new one in fullscreen
        subprocess.run(
            ["docker", "exec", "atomagent-sandbox", "bash", "-c", 
             f'pkill -f chromium || true; sleep 0.5; DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu --disable-software-rasterizer --start-fullscreen --start-maximized "{url}" &'],
            capture_output=True, text=True, timeout=10, cwd=DOCKER_DIR
        )
        
        return f"🌐 Browser opened at {url} in VNC. (View in Preview tab - VNC mode will activate)"
        
    except subprocess.TimeoutExpired:
        return f"⚠️ Timeout starting browser, but VNC may still work. URL: {url}"
    except Exception as e:
        logger.error(f"browse_site error: {e}")
        return f"❌ Error: {str(e)}"

