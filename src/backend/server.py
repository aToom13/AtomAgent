#!/usr/bin/env python3
"""
AtomAgent Backend Server
CrewAI tabanlı çok-ajanlı geliştirme ortamı backend sunucusu
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from agent_manager import AgentManager
from project_manager import ProjectManager
from crew_tools import ALL_TOOLS

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'atomagent-secret-key')
CORS(app, origins=["http://localhost:5173"])
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', port=5001)

# Global state
openrouter_client = None
agent_manager = None
project_manager = None

# OpenRouter API istemcisini başlat
def initialize_openrouter(api_key: str):
    global openrouter_client
    openrouter_client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # Agent ve Project Manager'ları başlat
    global agent_manager, project_manager
    agent_manager = AgentManager(openrouter_client)
    project_manager = ProjectManager(agent_manager)

# İstek sınıflandırma fonksiyonu
async def classify_request(prompt: str) -> str:
    """Kullanıcı isteğini basit/karmaşık olarak sınıflandır"""
    
    if not openrouter_client:
        return "basit"  # API key yoksa varsayılan
    
    try:
        classification_prompt = f"""
        Kullanıcı isteğini analiz et ve 'basit' veya 'karmaşık' olarak sınıflandır.
        
        BASIT: Genel sorular, açıklamalar, küçük kod parçacıkları
        KARMAŞIK: Tam proje geliştirme, çok dosyalı sistemler, karmaşık uygulamalar
        
        Kullanıcı isteği: "{prompt}"
        
        Sadece 'basit' veya 'karmaşık' olarak yanıtla.
        """
        
        response = openrouter_client.chat.completions.create(
            model="meta-llama/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": classification_prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().lower()
        return "karmaşık" if "karmaşık" in result else "basit"
        
    except Exception as e:
        logger.error(f"Sınıflandırma hatası: {e}")
        return "basit"

# Basit yanıt fonksiyonu
async def generate_simple_response(prompt: str) -> str:
    """Basit istekler için doğrudan yanıt üret"""
    
    if not openrouter_client:
        return "OpenRouter API anahtarı yapılandırılmamış. Lütfen ayarlar kısmından API anahtarınızı girin."
    
    try:
        response = openrouter_client.chat.completions.create(
            model="meta-llama/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
            stream=True
        )
        
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                # Gerçek zamanlı streaming
                socketio.emit('message_stream', {
                    'content': content,
                    'agent': 'chat',
                    'complete': False
                })
                await asyncio.sleep(0.01)  # Streaming hızını kontrol et
        
        socketio.emit('message_stream', {
            'content': '',
            'agent': 'chat', 
            'complete': True
        })
        
        return full_response
        
    except Exception as e:
        logger.error(f"Basit yanıt hatası: {e}")
        return f"Yanıt oluşturulurken hata oluştu: {str(e)}"

# Karmaşık proje işleme fonksiyonu
async def process_complex_project(prompt: str, user_id: str) -> str:
    """Karmaşık istekler için çok-ajanlı işlem başlat"""
    
    try:
        if not agent_manager or not project_manager:
            return "Sistem henüz hazır değil. Lütfen OpenRouter API anahtarını yapılandırın."
        
        # Yeni proje oluştur
        project = project_manager.create_project(prompt, user_id)
        
        # Task Manager ajanını aktive et
        agent_manager.update_agent_status("taskmanager", "working", "Proje planlama")
        project_manager.add_agent_to_project(project.id, "taskmanager")
        
        # İlerlemeyi bildir
        socketio.emit('project_update', {
            'project_id': project.id,
            'project': asdict(project),
            'message': 'Proje başlatılıyor, Task Manager aktif edildi...'
        })
        
        # Gerekli ajanları belirle ve ekle
        required_agents = ["coder", "tester", "coordinator"]
        for agent_id in required_agents:
            agent_manager.update_agent_status(agent_id, "working", f"Proje geliştirme: {project.id}")
            project_manager.add_agent_to_project(project.id, agent_id)
        
        # Proje iş akışını çalıştır
        success = project_manager.execute_project_workflow(project.id, prompt)
        
        if success:
            # Ajanları tamamlandı olarak işaretle
            for agent_id in project.active_agents:
                agent_manager.update_agent_status(agent_id, "completed")
            
            return f"Proje başarıyla tamamlandı! Proje ID: {project.id}"
        else:
            # Hata durumunda ajanları error durumuna getir
            for agent_id in project.active_agents:
                agent_manager.update_agent_status(agent_id, "error")
            
            return f"Proje işlenirken hata oluştu. Proje ID: {project.id}"
        
    except Exception as e:
        logger.error(f"Karmaşık proje hatası: {e}")
        return f"Proje işleme hatası: {str(e)}"

# REST API endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/config/openrouter', methods=['POST'])
def configure_openrouter():
    data = request.get_json()
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API anahtarı gerekli"}), 400
    
    try:
        initialize_openrouter(api_key)
        return jsonify({"message": "OpenRouter API başarıyla yapılandırıldı"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/agents', methods=['GET'])
def get_agents():
    if not agent_manager:
        return jsonify({"error": "Agent Manager başlatılmadı"}), 500
    
    agents_data = []
    for agent in agent_manager.get_all_agents():
        agent_dict = asdict(agent)
        agent_dict['last_activity'] = agent_dict['last_activity'].isoformat() if agent_dict['last_activity'] else None
        agents_data.append(agent_dict)
    
    return jsonify({"agents": agents_data})

@app.route('/api/agents/<agent_id>/model', methods=['PUT'])
def update_agent_model(agent_id):
    if not agent_manager:
        return jsonify({"error": "Agent Manager başlatılmadı"}), 500
    
    data = request.get_json()
    new_model = data.get('model')
    
    if not new_model:
        return jsonify({"error": "Model bilgisi gerekli"}), 400
    
    success = agent_manager.update_agent_model(agent_id, new_model)
    if success:
        return jsonify({"message": f"Ajan {agent_id} modeli {new_model} olarak güncellendi"})
    else:
        return jsonify({"error": "Ajan bulunamadı"}), 404

@app.route('/api/projects', methods=['GET'])
def get_projects():
    if not project_manager:
        return jsonify({"error": "Project Manager başlatılmadı"}), 500
    
    projects_data = []
    for project in project_manager.get_all_projects():
        project_dict = asdict(project)
        project_dict['status'] = project_dict['status'].value
        project_dict['created_at'] = project_dict['created_at'].isoformat()
        project_dict['updated_at'] = project_dict['updated_at'].isoformat()
        projects_data.append(project_dict)
    
    return jsonify({"projects": projects_data})

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    if not project_manager:
        return jsonify({"error": "Project Manager başlatılmadı"}), 500
    
    project = project_manager.get_project(project_id)
    if not project:
        return jsonify({"error": "Proje bulunamadı"}), 404
    
    project_dict = asdict(project)
    project_dict['status'] = project_dict['status'].value
    project_dict['created_at'] = project_dict['created_at'].isoformat()
    project_dict['updated_at'] = project_dict['updated_at'].isoformat()
    
    return jsonify({"project": project_dict})

@app.route('/api/projects/<project_id>/summary', methods=['GET'])
def get_project_summary(project_id):
    if not project_manager:
        return jsonify({"error": "Project Manager başlatılmadı"}), 500
    
    summary = project_manager.get_project_summary(project_id)
    if not summary:
        return jsonify({"error": "Proje bulunamadı"}), 404
    
    return jsonify({"summary": summary})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print(f'Client bağlandı: {request.sid}')
    join_room('general')
    emit('connected', {'message': 'AtomAgent backend bağlantısı başarılı'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client ayrıldı: {request.sid}')
    leave_room('general')

@socketio.on('send_message')
def handle_message(data):
    prompt = data.get('message', '').strip()
    user_id = data.get('user_id', request.sid)
    
    if not prompt:
        emit('error', {'message': 'Boş mesaj gönderilemez'})
        return
    
    # Async işlem için thread başlat
    socketio.start_background_task(process_message, prompt, user_id)

def process_message(prompt: str, user_id: str):
    """Mesaj işleme async fonksiyonu"""
    
    async def _process():
        try:
            # İstek sınıflandırması
            classification = await classify_request(prompt)
            
            socketio.emit('message_received', {
                'message': prompt,
                'classification': classification,
                'timestamp': datetime.now().isoformat()
            })
            
            if classification == "basit":
                # Basit yanıt
                response = await generate_simple_response(prompt)
                socketio.emit('simple_response', {
                    'response': response,
                    'agent': 'chat',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                # Karmaşık proje işleme
                result = await process_complex_project(prompt, user_id)
                socketio.emit('complex_response', {
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {e}")
            socketio.emit('error', {
                'message': f'Mesaj işleme hatası: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
    
    # Event loop oluştur ve async fonksiyonu çalıştır
    import threading
    
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_process())
        loop.close()
    
    thread = threading.Thread(target=run_async)
    thread.start()

if __name__ == '__main__':
    print("AtomAgent Backend Server başlatılıyor...")
    print("Frontend URL: http://localhost:5173")
    print("Backend URL: http://localhost:5001")
    
    # Eğer .env dosyasında API anahtarı varsa başlangıçta yapılandır
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key and api_key != 'your_openrouter_api_key_here':
        initialize_openrouter(api_key)
        print("OpenRouter API otomatik yapılandırıldı.")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
