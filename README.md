# AtomAgent

AI-Powered Development Assistant

## Nedir?

AtomAgent, doğal dil ile verdiğiniz görevleri anlayan ve çözen bir AI asistanıdır. Gradio tabanlı arayüz ile kod yazma, dosya yönetimi ve web araştırması yapabilir.

## Kurulum

```bash
pip install -r requirements.txt
```

`.env` dosyası oluşturup `OPENROUTER_API_KEY` ekleyin.

## Kullanım

```bash
python main.py
```

## Yapı

- `core/` - Agent sistemi
- `tools/` - Dosya, kod, web araçları
- `prompts/` - Agent prompt'ları
- `ui/` - Gradio arayüzü

