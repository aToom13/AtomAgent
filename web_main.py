"""
AtomAgent Web UI - Entry Point
Web arayüzünü başlatmak için bu dosyayı çalıştırın.
"""
import argparse
import webbrowser
import threading
import time

def open_browser(port: int):
    """Tarayıcıyı otomatik aç"""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{port}")

def main():
    parser = argparse.ArgumentParser(description="AtomAgent Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    args = parser.parse_args()
    
    print(f"""
    ╔═══════════════════════════════════════════════════╗
    ║           🤖 AtomAgent Web UI                     ║
    ║                                                   ║
    ║   URL: http://localhost:{args.port}                    ║
    ║                                                   ║
    ║   Ctrl+C ile durdurun                             ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    if not args.no_browser:
        threading.Thread(target=open_browser, args=(args.port,), daemon=True).start()
    
    from web.app import run_server
    run_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
