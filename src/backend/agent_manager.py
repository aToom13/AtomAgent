#!/usr/bin/env python3
"""
Ajan Yöneticisi - Ajanların oluşturulması, yönetimi ve izlenmesi
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from openai import OpenAI

from crew_tools import ALL_TOOLS, create_sandbox_directory, cleanup_sandbox

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Ajan durumu veri yapısı"""
    id: str
    name: str
    type: str
    model: str
    status: str  # idle, working, completed, error
    current_task: Optional[str] = None
    sandbox_path: Optional[str] = None
    last_activity: Optional[datetime] = None
    performance_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {
                "tasks_completed": 0,
                "errors_encountered": 0,
                "average_response_time": 0,
                "total_tokens_used": 0
            }

class AgentManager:
    """Ajan yönetimi sınıfı"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.openai_client = openai_client
        self.agents: Dict[str, AgentState] = {}
        self.active_crews: Dict[str, Crew] = {}
        self.sandbox_base_path = "/tmp/atomagent_sandboxes"
        
        # Sandbox dizinini oluştur
        os.makedirs(self.sandbox_base_path, exist_ok=True)
        
        # Varsayılan ajan konfigürasyonlarını yükle
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Varsayılan ajanları başlat"""
        default_configs = [
            {
                "id": "chat",
                "name": "Chat Agent",
                "type": "chat",
                "model": "meta-llama/llama-3.1-70b-instruct",
                "description": "Ana sohbet ve istek analizi",
                "system_prompt": "Sen bir yardımcı AI asistanısın. Kullanıcı isteklerini analiz et ve basit/karmaşık olarak sınıflandır."
            },
            {
                "id": "taskmanager",
                "name": "Task Manager",
                "type": "taskmanager",
                "model": "anthropic/claude-3-sonnet",
                "description": "Görev yönetimi ve koordinasyon",
                "system_prompt": "Sen bir proje yöneticisisin. Karmaşık istekleri analiz et, gerekli ajanları belirle ve görevleri dağıt."
            },
            {
                "id": "coder",
                "name": "Coder",
                "type": "coder",
                "model": "qwen/qwen-coder-plus",
                "description": "Kod yazma ve geliştirme",
                "system_prompt": "Sen bir uzman yazılım geliştiricisin. Yüksek kaliteli, temiz ve iyi dokümante edilmiş kod yaz."
            },
            {
                "id": "dbmanager",
                "name": "DB Manager",
                "type": "dbmanager",
                "model": "openai/gpt-4-turbo",
                "description": "Veritabanı yönetimi",
                "system_prompt": "Sen bir veritabanı uzmanısın. Veritabanı tasarımı, optimizasyon ve yönetimi konularında uzmansın."
            },
            {
                "id": "browser",
                "name": "Browser Agent",
                "type": "browser",
                "model": "google/gemini-pro-1.5",
                "description": "Web araştırma ve veri toplama",
                "system_prompt": "Sen bir web araştırma uzmanısın. İnternetten bilgi topla, analiz et ve özetle."
            },
            {
                "id": "filereader",
                "name": "File Reader",
                "type": "filereader",
                "model": "deepseek/deepseek-r1",
                "description": "Dosya okuma ve analiz",
                "system_prompt": "Sen bir dosya analizi uzmanısın. Çeşitli dosya formatlarını oku, analiz et ve özetle."
            },
            {
                "id": "tester",
                "name": "Tester",
                "type": "tester",
                "model": "anthropic/claude-3-sonnet",
                "description": "Test ve kalite kontrolü",
                "system_prompt": "Sen bir yazılım test uzmanısın. Kodları test et, hataları bul ve kalite kontrolü yap."
            },
            {
                "id": "coordinator",
                "name": "Coordinator",
                "type": "coordinator",
                "model": "openai/gpt-4-turbo",
                "description": "Proje koordinasyonu ve finalizasyon",
                "system_prompt": "Sen bir proje koordinatörüsün. Projeleri finalize et, dokümantasyon hazırla ve teslim et."
            }
        ]
        
        for config in default_configs:
            self.create_agent(
                agent_id=config["id"],
                name=config["name"],
                agent_type=config["type"],
                model=config["model"],
                description=config["description"],
                system_prompt=config["system_prompt"]
            )
    
    def create_agent(self, agent_id: str, name: str, agent_type: str, model: str, 
                    description: str, system_prompt: str) -> AgentState:
        """Yeni ajan oluştur"""
        
        # Sandbox dizini oluştur
        sandbox_path = os.path.join(self.sandbox_base_path, agent_id)
        os.makedirs(sandbox_path, exist_ok=True)
        
        # Ajan durumunu oluştur
        agent_state = AgentState(
            id=agent_id,
            name=name,
            type=agent_type,
            model=model,
            status="idle",
            sandbox_path=sandbox_path,
            last_activity=datetime.now()
        )
        
        self.agents[agent_id] = agent_state
        logger.info(f"Ajan oluşturuldu: {name} ({agent_id})")
        
        return agent_state
    
    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """Ajan bilgilerini getir"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[AgentState]:
        """Tüm ajanları listele"""
        return list(self.agents.values())
    
    def update_agent_model(self, agent_id: str, new_model: str) -> bool:
        """Ajan modelini güncelle"""
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id].model = new_model
        self.agents[agent_id].last_activity = datetime.now()
        logger.info(f"Ajan modeli güncellendi: {agent_id} -> {new_model}")
        return True
    
    def update_agent_status(self, agent_id: str, status: str, task: Optional[str] = None):
        """Ajan durumunu güncelle"""
        if agent_id not in self.agents:
            return
        
        self.agents[agent_id].status = status
        self.agents[agent_id].current_task = task
        self.agents[agent_id].last_activity = datetime.now()
        
        if status == "completed":
            self.agents[agent_id].performance_metrics["tasks_completed"] += 1
        elif status == "error":
            self.agents[agent_id].performance_metrics["errors_encountered"] += 1
    
    def create_crewai_agent(self, agent_id: str) -> Optional[Agent]:
        """CrewAI ajan nesnesi oluştur"""
        if agent_id not in self.agents:
            return None
        
        agent_state = self.agents[agent_id]
        
        # Ajan için uygun araçları seç
        agent_tools = self._select_tools_for_agent(agent_state.type)
        
        # CrewAI ajanını oluştur
        crewai_agent = Agent(
            role=agent_state.name,
            goal=agent_state.type,
            backstory=agent_state.performance_metrics,  # Geçici olarak
            tools=agent_tools,
            verbose=True,
            allow_delegation=False,
            llm=self.openai_client
        )
        
        return crewai_agent
    
    def _select_tools_for_agent(self, agent_type: str) -> List[BaseTool]:
        """Ajan tipine göre uygun araçları seç"""
        # Tüm ajanlar için temel araçlar
        basic_tools = [ALL_TOOLS[0], ALL_TOOLS[1]]  # FileOperationTool, TerminalTool
        
        if agent_type == "coder":
            return basic_tools + [ALL_TOOLS[4], ALL_TOOLS[5]]  # CodeExecutionTool, GitTool
        elif agent_type == "dbmanager":
            return basic_tools + [ALL_TOOLS[3]]  # PackageManagerTool
        elif agent_type == "browser":
            return basic_tools + [ALL_TOOLS[2]]  # DockerSandboxTool
        elif agent_type == "filereader":
            return [ALL_TOOLS[0]]  # Sadece FileOperationTool
        elif agent_type == "tester":
            return basic_tools + [ALL_TOOLS[4]]  # CodeExecutionTool
        elif agent_type == "coordinator":
            return basic_tools + [ALL_TOOLS[5]]  # GitTool
        else:
            return basic_tools
    
    def create_crew(self, agent_ids: List[str], project_id: str) -> Optional[Crew]:
        """CrewAI ekibi oluştur"""
        crewai_agents = []
        
        for agent_id in agent_ids:
            crewai_agent = self.create_crewai_agent(agent_id)
            if crewai_agent:
                crewai_agents.append(crewai_agent)
        
        if not crewai_agents:
            return None
        
        # Crew oluştur
        crew = Crew(
            agents=crewai_agents,
            tasks=[],  # Task'lar project_manager tarafından eklenecek
            process=Process.sequential,
            verbose=True
        )
        
        self.active_crews[project_id] = crew
        logger.info(f"Crew oluşturuldu: {project_id} - {len(crewai_agents)} ajan")
        
        return crew
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Ajan performans metriklerini getir"""
        if agent_id not in self.agents:
            return {}
        
        agent_state = self.agents[agent_id]
        return agent_state.performance_metrics
    
    def cleanup_agent_sandbox(self, agent_id: str) -> bool:
        """Ajan sandbox'ını temizle"""
        if agent_id not in self.agents:
            return False
        
        agent_state = self.agents[agent_id]
        if agent_state.sandbox_path and os.path.exists(agent_state.sandbox_path):
            try:
                shutil.rmtree(agent_state.sandbox_path)
                os.makedirs(agent_state.sandbox_path, exist_ok=True)
                logger.info(f"Ajan sandbox temizlendi: {agent_id}")
                return True
            except Exception as e:
                logger.error(f"Sandbox temizleme hatası: {e}")
                return False
        
        return False
    
    def export_agent_data(self, agent_id: str) -> Optional[str]:
        """Ajan verilerini JSON olarak dışa aktar"""
        if agent_id not in self.agents:
            return None
        
        agent_state = self.agents[agent_id]
        data = asdict(agent_state)
        
        # Datetime objelerini string'e çevir
        data['last_activity'] = data['last_activity'].isoformat() if data['last_activity'] else None
        
        return json.dumps(data, indent=2, ensure_ascii=False)
