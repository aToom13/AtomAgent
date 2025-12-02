"""
Multi-Modal Tools - Görsel analiz ve ses işleme
Vision (görüntü analizi) ve Audio (ses) desteği
"""
import os
import base64
from typing import Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from config import config
from utils.logger import get_logger
from core.providers import model_manager, get_api_key

logger = get_logger()

WORKSPACE_DIR = config.workspace.base_dir


def _encode_image(image_path: str) -> Optional[str]:
    """Görüntüyü base64'e encode et"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Image encoding failed: {e}")
        return None


def _get_image_mime_type(image_path: str) -> str:
    """Görüntü MIME tipini belirle"""
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp"
    }
    return mime_types.get(ext, "image/png")


@tool
def analyze_image(image_path: str, question: str = "Bu görselde ne var? Detaylı açıkla.") -> str:
    """
    Bir görüntüyü analiz eder ve açıklama döndürür.
    Vision destekleyen modeller gerektirir (GPT-4V, Claude 3, Gemini Pro Vision).
    
    Args:
        image_path: Görüntü dosyasının yolu (workspace içinde)
        question: Görüntü hakkında sorulacak soru
    
    Returns:
        Görüntü analizi sonucu
    
    Örnek:
        analyze_image("screenshot.png", "Bu ekran görüntüsündeki hata nedir?")
        analyze_image("diagram.png", "Bu diyagramı açıkla")
    """
    
    logger.info(f"Analyzing image: {image_path}")
    
    # Dosya yolunu kontrol et
    full_path = os.path.join(WORKSPACE_DIR, image_path)
    if not os.path.exists(full_path):
        # Mutlak yol dene
        if os.path.exists(image_path):
            full_path = image_path
        else:
            return f"❌ Görüntü bulunamadı: {image_path}"
    
    # Görüntüyü encode et
    image_data = _encode_image(full_path)
    if not image_data:
        return "❌ Görüntü okunamadı"
    
    mime_type = _get_image_mime_type(full_path)
    
    # Vision destekleyen model al (yeni vision rolü)
    llm = model_manager.get_llm("vision")
    
    if not llm:
        return "❌ Vision modeli başlatılamadı. Lütfen :model komutu ile vision ayarlarını kontrol edin."
    
    try:
        # Vision mesajı oluştur
        message = HumanMessage(
            content=[
                {"type": "text", "text": question},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                }
            ]
        )
        
        response = llm.invoke([message])
        
        logger.info("Image analysis completed")
        return f"🖼️ Görüntü Analizi:\n\n{response.content}"
        
    except Exception as e:
        error_str = str(e).lower()
        
        # Fallback dene
        if model_manager.switch_to_fallback("vision"):
             return analyze_image(image_path, question)

        if "vision" in error_str or "image" in error_str or "multimodal" in error_str:
            return """❌ Bu model görüntü analizi desteklemiyor.

Vision destekleyen modeller:
• OpenAI: gpt-4-vision-preview, gpt-4o
• Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku
• Google: gemini-pro-vision, gemini-1.5-pro

:model komutu ile vision destekleyen bir model seçin."""
        
        logger.error(f"Image analysis failed: {e}")
        return f"❌ Analiz hatası: {e}"


@tool
def analyze_screenshot(question: str = "Bu ekran görüntüsünde ne görüyorsun?") -> str:
    """
    Ekran görüntüsü alır ve analiz eder.
    
    Args:
        question: Ekran görüntüsü hakkında soru
    
    Returns:
        Analiz sonucu
    
    Not: Bu fonksiyon pyautogui veya pillow gerektirir.
    """
    try:
        from PIL import ImageGrab
        import tempfile
        
        # Ekran görüntüsü al
        screenshot = ImageGrab.grab()
        
        # Geçici dosyaya kaydet
        temp_path = os.path.join(WORKSPACE_DIR, "_screenshot_temp.png")
        screenshot.save(temp_path)
        
        # Analiz et
        result = analyze_image.invoke({
            "image_path": temp_path,
            "question": question
        })
        
        # Geçici dosyayı sil
        try:
            os.remove(temp_path)
        except:
            pass
        
        return result
        
    except ImportError:
        return """❌ Ekran görüntüsü için gerekli paketler yüklü değil.

Yüklemek için:
pip install pillow

Linux'ta ayrıca:
sudo apt install python3-tk python3-dev"""
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return f"❌ Ekran görüntüsü alınamadı: {e}"


@tool
def describe_code_screenshot(image_path: str) -> str:
    """
    Kod içeren bir ekran görüntüsünü analiz eder.
    Hata mesajları, kod yapısı ve sorunları tespit eder.
    
    Args:
        image_path: Kod ekran görüntüsünün yolu
    
    Returns:
        Kod analizi ve öneriler
    """
    question = """Bu ekran görüntüsündeki kodu analiz et:

1. Hangi programlama dili kullanılmış?
2. Kodun ne yaptığını açıkla
3. Görünen hata mesajları varsa açıkla
4. Potansiyel sorunlar veya iyileştirme önerileri var mı?
5. Eğer bir hata varsa, nasıl düzeltilebilir?

Detaylı ve teknik bir analiz yap."""
    
    return analyze_image.invoke({
        "image_path": image_path,
        "question": question
    })


@tool
def extract_text_from_image(image_path: str) -> str:
    """
    Görüntüden metin çıkarır (OCR).
    
    Args:
        image_path: Görüntü dosyasının yolu
    
    Returns:
        Çıkarılan metin
    """
    question = """Bu görüntüdeki TÜM metni oku ve aynen yaz.
Formatı koru (satır sonları, girintiler).
Sadece metni yaz, yorum ekleme."""
    
    return analyze_image.invoke({
        "image_path": image_path,
        "question": question
    })


@tool
def analyze_diagram(image_path: str) -> str:
    """
    Teknik diyagramı (flowchart, UML, mimari) analiz eder.
    
    Args:
        image_path: Diyagram görüntüsünün yolu
    
    Returns:
        Diyagram açıklaması ve analizi
    """
    question = """Bu teknik diyagramı analiz et:

1. Diyagram tipi nedir? (flowchart, UML, ER diagram, mimari, vb.)
2. Ana bileşenleri listele
3. Bileşenler arası ilişkileri açıkla
4. Veri/kontrol akışını açıkla
5. Varsa eksik veya belirsiz noktaları belirt

Teknik ve detaylı bir analiz yap."""
    
    return analyze_image.invoke({
        "image_path": image_path,
        "question": question
    })


# ============================================
# AUDIO TOOLS (Ses İşleme)
# ============================================

@tool
def transcribe_audio(audio_path: str) -> str:
    """
    Ses dosyasını metne çevirir (Speech-to-Text).
    OpenAI Whisper API veya yerel Whisper modeli kullanır.
    
    Args:
        audio_path: Ses dosyasının yolu (.mp3, .wav, .m4a, .webm)
    
    Returns:
        Transkript metni
    """
    logger.info(f"Transcribing audio: {audio_path}")
    
    # Dosya yolunu kontrol et
    full_path = os.path.join(WORKSPACE_DIR, audio_path)
    if not os.path.exists(full_path):
        if os.path.exists(audio_path):
            full_path = audio_path
        else:
            return f"❌ Ses dosyası bulunamadı: {audio_path}"
    
    # Audio config al
    config = model_manager.get_config("audio")
    provider = config.provider
    
    # OpenAI Whisper API
    if provider == "openai":
        try:
            import openai
            
            api_key = get_api_key("openai")
            if not api_key:
                 return "❌ OpenAI API key bulunamadı."

            client = openai.OpenAI(api_key=api_key)
            
            with open(full_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=config.model, # whisper-1
                    file=audio_file
                )
            
            logger.info("Audio transcription completed (OpenAI)")
            return f"🎤 Transkript:\n\n{transcript.text}"
            
        except Exception as e:
            logger.warning(f"OpenAI Whisper failed: {e}")
            # Fallback
            if model_manager.switch_to_fallback("audio"):
                 return transcribe_audio(audio_path)
            return f"❌ Transkript hatası: {e}"
    
    # Yerel Whisper (ollama veya local provider olarak işaretlenmişse)
    elif provider == "local" or provider == "ollama":
        try:
            import whisper
            
            model_name = "base" # Varsayılan
            if config.model and config.model != "whisper-1":
                 model_name = config.model

            model = whisper.load_model(model_name)
            result = model.transcribe(full_path)
            
            logger.info("Audio transcription completed (local Whisper)")
            return f"🎤 Transkript:\n\n{result['text']}"
            
        except ImportError:
            return """❌ Ses transkripti için gerekli paketler yüklü değil.

Seçenekler:
1. OpenAI API (önerilen):
   - :model audio openai whisper-1

2. Yerel Whisper:
   - pip install openai-whisper
   - İlk kullanımda model indirilecek (~1GB)"""
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return f"❌ Transkript hatası: {e}"

    # Hugging Face Inference API
    elif provider == "huggingface":
        try:
            import requests
            
            api_key = get_api_key("huggingface")
            if not api_key:
                 return "❌ Hugging Face API key bulunamadı (.env dosyasında HUGGINGFACE_API_KEY)."

            model = config.model or "openai/whisper-large-v3"
            api_url = f"https://router.huggingface.co/hf-inference/models/{model}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "audio/flac" # Genelde flac veya wav gönderiyoruz, dosya tipine göre değişebilir ama binary stream önemli
            }

            with open(full_path, "rb") as f:
                data = f.read()

            response = requests.post(api_url, headers=headers, data=data)
            
            if response.status_code != 200:
                return f"❌ Hugging Face API Hatası ({response.status_code}): {response.text}"
            
            result = response.json()
            if "text" in result:
                logger.info(f"Audio transcription completed (HF: {model})")
                return f"🎤 Transkript ({model}):\n\n{result['text']}"
            else:
                return f"❌ Beklenmeyen yanıt: {result}"

        except Exception as e:
            logger.error(f"Hugging Face transcription failed: {e}")
            if model_manager.switch_to_fallback("audio"):
                 return transcribe_audio(audio_path)
            return f"❌ Transkript hatası: {e}"
            
    else:
         return f"❌ Desteklenmeyen audio provider: {provider}"


@tool
def text_to_speech(text: str, output_file: str = "speech.mp3") -> str:
    """
    Metni sese çevirir (Text-to-Speech).
    
    Args:
        text: Sese çevrilecek metin
        output_file: Çıktı dosyası adı
    
    Returns:
        Oluşturulan ses dosyasının yolu
    """
    logger.info(f"Converting text to speech: {text[:50]}...")
    
    output_path = os.path.join(WORKSPACE_DIR, output_file)
    
    # TTS config al
    config = model_manager.get_config("tts")
    provider = config.provider
    
    # OpenAI TTS
    if provider == "openai":
        try:
            import openai
            
            api_key = get_api_key("openai")
            if not api_key:
                 return "❌ OpenAI API key bulunamadı."

            client = openai.OpenAI(api_key=api_key)
            
            response = client.audio.speech.create(
                model=config.model, # tts-1 or tts-1-hd
                voice="alloy",
                input=text
            )
            
            response.stream_to_file(output_path)
            
            logger.info(f"TTS completed: {output_file}")
            return f"🔊 Ses dosyası oluşturuldu: {output_file}"
            
        except Exception as e:
            logger.warning(f"OpenAI TTS failed: {e}")
            if model_manager.switch_to_fallback("tts"):
                 return text_to_speech(text, output_file)
            return f"❌ TTS hatası: {e}"
    
    # Google TTS (gTTS) - local veya google provider
    elif provider == "google" or provider == "local":
        try:
            from gtts import gTTS
            
            tts = gTTS(text=text, lang='tr')
            tts.save(output_path)
            
            logger.info(f"TTS completed (gTTS): {output_file}")
            return f"🔊 Ses dosyası oluşturuldu: {output_file}"
            
        except ImportError:
            return """❌ Text-to-Speech için gerekli paketler yüklü değil.

Seçenekler:
1. OpenAI TTS (yüksek kalite):
   - :model tts openai tts-1

2. Google TTS (ücretsiz):
   - pip install gTTS"""
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return f"❌ TTS hatası: {e}"

    # Hugging Face Inference API
    elif provider == "huggingface":
        try:
            import requests
            
            api_key = get_api_key("huggingface")
            if not api_key:
                 return "❌ Hugging Face API key bulunamadı (.env dosyasında HUGGINGFACE_API_KEY)."

            model = config.model or "facebook/mms-tts-eng" # Varsayılan model
            api_url = f"https://router.huggingface.co/hf-inference/models/{model}"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            payload = {"inputs": text}
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                return f"❌ Hugging Face API Hatası ({response.status_code}): {response.text}"
            
            # Ses dosyasını kaydet
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"TTS completed (HF: {model}): {output_file}")
            return f"🔊 Ses dosyası oluşturuldu ({model}): {output_file}"

        except Exception as e:
            logger.error(f"Hugging Face TTS failed: {e}")
            if model_manager.switch_to_fallback("tts"):
                 return text_to_speech(text, output_file)
            return f"❌ TTS hatası: {e}"
            
    else:
         return f"❌ Desteklenmeyen TTS provider: {provider}"


def check_vision_support() -> dict:
    """Vision desteğini kontrol et (internal)"""
    # Artık doğrudan vision rolünü kontrol ediyoruz
    config = model_manager.get_config("vision")
    if not config:
        return {"supported": False, "reason": "Vision config yok"}
    
    return {"supported": True, "provider": config.provider, "model": config.model}
