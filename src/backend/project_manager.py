#!/usr/bin/env python3
"""
Proje Yöneticisi - Proje oluşturma, takip ve yönetim
"""

import os
import json
import time
import logging
import shutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from crewai import Task, Crew, Process

from agent_manager import AgentManager
from crew_tools import create_sandbox_directory, cleanup_sandbox

logger = logging.getLogger(__name__)

class ProjectStatus(Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ProjectData:
    """Proje veri yapısı"""
    id: str
    name: str
    description: str
    status: ProjectStatus
    progress: int
    active_agents: List[str]
    files: List[str]
    created_at: datetime
    updated_at: datetime
    project_path: str
    tasks: List[str]
    error_log: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "estimated_duration": 0,
                "actual_duration": 0,
                "complexity_score": 0
            }

class ProjectManager:
    """Proje yönetimi sınıfı"""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.projects: Dict[str, ProjectData] = {}
        self.projects_base_path = "/tmp/atomagent_projects"
        
        # Projeler dizinini oluştur
        os.makedirs(self.projects_base_path, exist_ok=True)
    
    def create_project(self, description: str, user_id: str) -> ProjectData:
        """Yeni proje oluştur"""
        project_id = f"project_{len(self.projects) + 1}_{int(time.time())}"
        project_name = f"Proje_{len(self.projects) + 1}"
        
        # Proje dizini oluştur
        project_path = os.path.join(self.projects_base_path, project_id)
        os.makedirs(project_path, exist_ok=True)
        
        # Proje verisi oluştur
        project = ProjectData(
            id=project_id,
            name=project_name,
            description=description,
            status=ProjectStatus.PLANNING,
            progress=0,
            active_agents=[],
            files=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_path=project_path,
            tasks=[],
            error_log=[],
            metadata={}
        )
        
        self.projects[project_id] = project
        logger.info(f"Proje oluşturuldu: {project_name} ({project_id})")
        
        return project
    
    def get_project(self, project_id: str) -> Optional[ProjectData]:
        """Proje bilgilerini getir"""
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> List[ProjectData]:
        """Tüm projeleri listele"""
        return list(self.projects.values())
    
    def update_project_status(self, project_id: str, status: ProjectStatus, progress: int = None):
        """Proje durumunu güncelle"""
        if project_id not in self.projects:
            return
        
        project = self.projects[project_id]
        project.status = status
        project.updated_at = datetime.now()
        
        if progress is not None:
            project.progress = progress
        
        logger.info(f"Proje durumu güncellendi: {project_id} -> {status.value}")
    
    def add_agent_to_project(self, project_id: str, agent_id: str) -> bool:
        """Projeye ajan ekle"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        if agent_id not in project.active_agents:
            project.active_agents.append(agent_id)
            project.updated_at = datetime.now()
            logger.info(f"Ajan projeye eklendi: {agent_id} -> {project_id}")
            return True
        
        return False
    
    def remove_agent_from_project(self, project_id: str, agent_id: str) -> bool:
        """Projeden ajan çıkar"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        if agent_id in project.active_agents:
            project.active_agents.remove(agent_id)
            project.updated_at = datetime.now()
            logger.info(f"Ajan projeden çıkarıldı: {agent_id} <- {project_id}")
            return True
        
        return False
    
    def add_file_to_project(self, project_id: str, file_path: str) -> bool:
        """Projeye dosya ekle"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        if file_path not in project.files:
            project.files.append(file_path)
            project.updated_at = datetime.now()
            logger.info(f"Dosya projeye eklendi: {file_path} -> {project_id}")
            return True
        
        return False
    
    def add_task_to_project(self, project_id: str, task: str) -> bool:
        """Projeye görev ekle"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        project.tasks.append(task)
        project.metadata["total_tasks"] += 1
        project.updated_at = datetime.now()
        logger.info(f"Görev projeye eklendi: {task} -> {project_id}")
        return True
    
    def complete_task(self, project_id: str, task: str) -> bool:
        """Projedeki görevi tamamla"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        if task in project.tasks:
            project.tasks.remove(task)
            project.metadata["completed_tasks"] += 1
            project.updated_at = datetime.now()
            
            # İlerlemeyi güncelle
            total_tasks = project.metadata["total_tasks"]
            completed_tasks = project.metadata["completed_tasks"]
            if total_tasks > 0:
                project.progress = int((completed_tasks / total_tasks) * 100)
            
            logger.info(f"Görev tamamlandı: {task} -> {project_id}")
            return True
        
        return False
    
    def log_error(self, project_id: str, error: str) -> bool:
        """Projeye hata log'u ekle"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        error_entry = f"{datetime.now().isoformat()}: {error}"
        project.error_log.append(error_entry)
        project.metadata["failed_tasks"] += 1
        project.updated_at = datetime.now()
        
        logger.error(f"Proje hatası: {project_id} - {error}")
        return True
    
    def create_project_tasks(self, project_id: str, description: str) -> List[Task]:
        """Proje için CrewAI görevleri oluştur"""
        if project_id not in self.projects:
            return []
        
        project = self.projects[project_id]
        tasks = []
        
        # Task Manager için planlama görevi
        planning_task = Task(
            description=f"Kullanıcı isteğini analiz et ve gerekli ajanları belirle: {description}",
            expected_output="Gerekli ajanların listesi ve görev dağılımı",
            agent=self.agent_manager.create_crewai_agent("taskmanager")
        )
        tasks.append(planning_task)
        
        # Coder için geliştirme görevi
        if "coder" in project.active_agents:
            dev_task = Task(
                description=f"Proje için kod geliştir: {description}",
                expected_output="Çalışan kod dosyaları ve dokümantasyon",
                agent=self.agent_manager.create_crewai_agent("coder")
            )
            tasks.append(dev_task)
        
        # Tester için test görevi
        if "tester" in project.active_agents:
            test_task = Task(
                description="Geliştirilen kodu test et ve hataları raporla",
                expected_output="Test raporu ve hata düzeltmeleri",
                agent=self.agent_manager.create_crewai_agent("tester")
            )
            tasks.append(test_task)
        
        # Coordinator için finalizasyon görevi
        if "coordinator" in project.active_agents:
            final_task = Task(
                description="Projeyi finalize et, dokümantasyon hazırla ve teslimat paketi oluştur",
                expected_output="Tamamlanmış proje dosyaları ve README",
                agent=self.agent_manager.create_crewai_agent("coordinator")
            )
            tasks.append(final_task)
        
        return tasks
    
    def execute_project_workflow(self, project_id: str, description: str) -> bool:
        """Proje iş akışını çalıştır"""
        try:
            if project_id not in self.projects:
                return False
            
            project = self.projects[project_id]
            
            # Proje durumunu güncelle
            self.update_project_status(project_id, ProjectStatus.PLANNING, 10)
            
            # Görevleri oluştur
            tasks = self.create_project_tasks(project_id, description)
            
            if not tasks:
                self.log_error(project_id, "Görevler oluşturulamadı")
                self.update_project_status(project_id, ProjectStatus.ERROR)
                return False
            
            # Crew oluştur
            crew = self.agent_manager.create_crew(project.active_agents, project_id)
            if not crew:
                self.log_error(project_id, "Crew oluşturulamadı")
                self.update_project_status(project_id, ProjectStatus.ERROR)
                return False
            
            # Görevleri crew'e ekle
            crew.tasks = tasks
            
            # Geliştirme aşaması
            self.update_project_status(project_id, ProjectStatus.DEVELOPMENT, 30)
            
            # Crew'i çalıştır
            result = crew.kickoff()
            
            # Test aşaması
            self.update_project_status(project_id, ProjectStatus.TESTING, 80)
            
            # Proje tamamlama
            self.update_project_status(project_id, ProjectStatus.COMPLETED, 100)
            
            logger.info(f"Proje başarıyla tamamlandı: {project_id}")
            return True
            
        except Exception as e:
            self.log_error(project_id, f"Proje iş akışı hatası: {str(e)}")
            self.update_project_status(project_id, ProjectStatus.ERROR)
            return False
    
    def cleanup_project(self, project_id: str) -> bool:
        """Projeyi temizle"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        # Proje dizinini temizle
        if os.path.exists(project.project_path):
            try:
                shutil.rmtree(project.project_path)
                logger.info(f"Proje dizini temizlendi: {project_id}")
            except Exception as e:
                logger.error(f"Proje temizleme hatası: {e}")
                return False
        
        # Projeden çıkar
        del self.projects[project_id]
        logger.info(f"Proje silindi: {project_id}")
        
        return True
    
    def export_project_data(self, project_id: str) -> Optional[str]:
        """Proje verilerini JSON olarak dışa aktar"""
        if project_id not in self.projects:
            return None
        
        project = self.projects[project_id]
        data = asdict(project)
        
        # Enum ve datetime objelerini dönüştür
        data['status'] = data['status'].value
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Proje özetini getir"""
        if project_id not in self.projects:
            return {}
        
        project = self.projects[project_id]
        
        return {
            "id": project.id,
            "name": project.name,
            "status": project.status.value,
            "progress": project.progress,
            "active_agents_count": len(project.active_agents),
            "files_count": len(project.files),
            "tasks_count": len(project.tasks),
            "errors_count": len(project.error_log),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "metadata": project.metadata
        }
