#!/usr/bin/env python3
"""
AtomAgent Backend Kurulum Scripti
"""

import os
import sys
import subprocess
import venv

def create_virtual_environment():
    """Sanal ortam oluştur"""
    venv_path = "venv"
    
    if os.path.exists(venv_path):
        print("Sanal ortam zaten mevcut.")
        return venv_path
    
    print("Sanal ortam oluşturuluyor...")
    venv.create(venv_path, with_pip=True)
    print(f"Sanal ortam oluşturuldu: {venv_path}")
    return venv_path

def install_requirements():
    """Gerekli paketleri yükle"""
    print("Gerekli paketler yükleniyor...")
    
    # Pip'i güncelle
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Requirements.txt'den yükle
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("Tüm paketler başarıyla yüklendi!")

def create_env_file():
    """Örnek .env dosyası oluştur"""
    env_content = """# AtomAgent Environment Variables
OPENROUTER_API_KEY=your_openrouter_api_key_here
FLASK_ENV=development
SECRET_KEY=atomagent-secret-key-change-in-production
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print(".env dosyası oluşturuldu. Lütfen API anahtarlarınızı güncelleyin.")
    else:
        print(".env dosyası zaten mevcut.")

def create_directories():
    """Gerekli dizinleri oluştur"""
    directories = [
        '/tmp/chat_agent',
        '/tmp/task_manager', 
        '/tmp/coder',
        '/tmp/db_manager',
        '/tmp/browser_agent',
        '/tmp/file_reader',
        '/tmp/tester',
        '/tmp/coordinator',
        'projects',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("Sandbox dizinleri oluşturuldu.")

def main():
    """Ana kurulum fonksiyonu"""
    print("AtomAgent Backend Kurulum Başlıyor...")
    print("=" * 50)
    
    try:
        # Sanal ortam oluştur
        venv_path = create_virtual_environment()
        
        # Gerekli paketleri yükle
        install_requirements()
        
        # Env dosyası oluştur
        create_env_file()
        
        # Dizinleri oluştur
        create_directories()
        
        print("\n" + "=" * 50)
        print("✅ Kurulum tamamlandı!")
        print("\nBaşlatma komutları:")
        print("1. Sanal ortamı aktive edin:")
        print("   Linux/Mac: source venv/bin/activate")
        print("   Windows: venv\\Scripts\\activate")
        print("\n2. .env dosyasında OpenRouter API anahtarınızı güncelleyin")
        print("\n3. Sunucuyu başlatın:")
        print("   python server.py")
        print("\nFrontend'i başlatmak için ana dizinde:")
        print("   npm run dev")
        
    except Exception as e:
        print(f"❌ Kurulum hatası: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()