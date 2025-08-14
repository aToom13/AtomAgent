import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Settings, 
  Zap, 
  Bot, 
  Code, 
  Database, 
  Globe, 
  FileText, 
  TestTube, 
  Users,
  Play,
  Square,
  Download,
  Folder,
  Terminal,
  Eye,
  Moon,
  Sun,
  Cpu,
  MessageCircle,
  AlertCircle,
  ExternalLink,
  Server,
  Wifi
} from 'lucide-react';

import { useSocket } from './hooks/useSocket';
import { ConnectionStatus } from './components/ConnectionStatus';
import { BackendInstructions } from './components/BackendInstructions';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  agentType?: string;
  timestamp: Date;
  isStreaming?: boolean;
  classification?: string;
}

interface Agent {
  id: string;
  name: string;
  type: string;
  model: string;
  status: 'idle' | 'working' | 'completed';
  color: string;
  icon: React.ComponentType<any>;
  description: string;
}

interface Project {
  id: string;
  name: string;
  status: 'planning' | 'development' | 'testing' | 'completed';
  progress: number;
  agents: string[];
  files: string[];
}

const AVAILABLE_MODELS: string[] = [];

const AGENTS: Agent[] = [
  {
    id: 'chat',
    name: 'Chat Agent',
    type: 'chat',
    model: 'meta-llama/llama-3.1-70b-instruct',
    status: 'idle',
    color: 'from-blue-500 to-cyan-500',
    icon: MessageCircle,
    description: 'Ana sohbet ve istek analizi'
  },
  {
    id: 'taskmanager',
    name: 'Task Manager',
    type: 'taskmanager',
    model: 'anthropic/claude-3-sonnet',
    status: 'idle',
    color: 'from-purple-500 to-pink-500',
    icon: Users,
    description: 'Görev yönetimi ve koordinasyon'
  },
  {
    id: 'coder',
    name: 'Coder',
    type: 'coder',
    model: 'qwen/qwen-coder-plus',
    status: 'idle',
    color: 'from-green-500 to-emerald-500',
    icon: Code,
    description: 'Kod yazma ve geliştirme'
  },
  {
    id: 'dbmanager',
    name: 'DB Manager',
    type: 'dbmanager',
    model: 'openai/gpt-4-turbo',
    status: 'idle',
    color: 'from-orange-500 to-red-500',
    icon: Database,
    description: 'Veritabanı yönetimi'
  },
  {
    id: 'browser',
    name: 'Browser Agent',
    type: 'browser',
    model: 'google/gemini-pro-1.5',
    status: 'idle',
    color: 'from-indigo-500 to-blue-500',
    icon: Globe,
    description: 'Web araştırma ve veri toplama'
  },
  {
    id: 'filereader',
    name: 'File Reader',
    type: 'filereader',
    model: 'deepseek/deepseek-r1',
    status: 'idle',
    color: 'from-teal-500 to-green-500',
    icon: FileText,
    description: 'Dosya okuma ve analiz'
  },
  {
    id: 'tester',
    name: 'Tester',
    type: 'tester',
    model: 'anthropic/claude-3-sonnet',
    status: 'idle',
    color: 'from-yellow-500 to-orange-500',
    icon: TestTube,
    description: 'Test ve kalite kontrolü'
  },
  {
    id: 'coordinator',
    name: 'Coordinator',
    type: 'coordinator',
    model: 'openai/gpt-4-turbo',
    status: 'idle',
    color: 'from-violet-500 to-purple-500',
    icon: Zap,
    description: 'Proje koordinasyonu ve finalizasyon'
  }
];

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Merhaba! Ben AtomAgent sistemiyim. Size nasıl yardımcı olabilirim?\n\nBasit sorularınızı doğrudan yanıtlayabilirim veya karmaşık projeler için çok-ajanlı geliştirme ekibimi devreye alabilirim.\n\n⚠️ **Backend sunucusu gerekli:** Tam işlevsellik için Python backend sunucusunu başlatmanız gerekiyor.',
      sender: 'agent',
      agentType: 'chat',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'agents' | 'projects' | 'settings'>('chat');
  const [agents, setAgents] = useState<Agent[]>(AGENTS);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [darkMode, setDarkMode] = useState(true);
  const [showBackendInstructions, setShowBackendInstructions] = useState(false);
  const [openrouterApiKey, setOpenrouterApiKey] = useState('');
  const [streamingMessage, setStreamingMessage] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Socket connection
  const { socket, isConnected, sendMessage, lastMessage, connectionError } = useSocket();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Socket message handling
  useEffect(() => {
    if (!lastMessage) return;

    console.log('Socket mesajı alındı:', lastMessage);

    if (lastMessage.message_received || lastMessage.classification) {
      // İstek sınıflandırma bilgisi
      const classificationMessage: Message = {
        id: Date.now().toString(),
        content: `İsteğiniz "${lastMessage.classification}" olarak sınıflandırıldı. ${
          lastMessage.classification === 'basit' 
            ? 'Doğrudan yanıtlıyorum...' 
            : 'Çok-ajanlı takımı devreye alıyorum...'
        }`,
        sender: 'agent',
        agentType: 'chat',
        timestamp: new Date(),
        classification: lastMessage.classification
      };
      
      console.log('Sınıflandırma mesajı eklendi:', classificationMessage);
      setMessages(prev => [...prev, classificationMessage]);
    }

    if (lastMessage.simple_response) {
      // Basit yanıt
      const responseMessage: Message = {
        id: Date.now().toString(),
        content: lastMessage.response || '',
        sender: 'agent',
        agentType: lastMessage.agent || 'chat',
        timestamp: new Date()
      };
      
      console.log('Basit yanıt mesajı eklendi:', responseMessage);
      setMessages(prev => [...prev, responseMessage]);
      setIsLoading(false);
    }

    if (lastMessage.complex_response) {
      // Karmaşık proje yanıtı
      const responseMessage: Message = {
        id: Date.now().toString(),
        content: lastMessage.result || '',
        sender: 'agent',
        agentType: 'taskmanager',
        timestamp: new Date()
      };
      
      console.log('Karmaşık yanıt mesajı eklendi:', responseMessage);
      setMessages(prev => [...prev, responseMessage]);
      setIsLoading(false);
    }

    if (lastMessage.message_stream) {
      // Streaming mesaj
      if (lastMessage.complete) {
        // Streaming tamamlandı
        if (streamingMessage.trim()) {
          const finalMessage: Message = {
            id: Date.now().toString(),
            content: streamingMessage,
            sender: 'agent',
            agentType: lastMessage.agent || 'chat',
            timestamp: new Date()
          };
          
          console.log('Streaming tamamlandı mesajı eklendi:', finalMessage);
          setMessages(prev => [...prev, finalMessage]);
          setStreamingMessage('');
        }
        setIsLoading(false);
      } else {
        // Streaming devam ediyor
        setStreamingMessage(prev => prev + (lastMessage.content || ''));
      }
    }

    if (lastMessage.project_update) {
      // Proje güncellemesi
      const projectMessage: Message = {
        id: Date.now().toString(),
        content: lastMessage.message || 'Proje güncellendi',
        sender: 'agent',
        agentType: 'taskmanager',
        timestamp: new Date()
      };
      
      console.log('Proje güncelleme mesajı eklendi:', projectMessage);
      setMessages(prev => [...prev, projectMessage]);
      
      if (lastMessage.project) {
        setCurrentProject(lastMessage.project);
      }
    }

    if (lastMessage.error) {
      // Hata mesajı
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `❌ Hata: ${lastMessage.message || lastMessage.error}`,
        sender: 'agent',
        agentType: 'chat',
        timestamp: new Date()
      };
      
      console.log('Hata mesajı eklendi:', errorMessage);
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }

  }, [lastMessage, streamingMessage]);

  const getAgentInfo = (agentType?: string) => {
    const agent = agents.find(a => a.type === agentType);
    return agent || agents[0];
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setStreamingMessage('');

    // Backend bağlı ise gerçek mesaj gönder
    if (isConnected && socket) {
      sendMessage(inputValue);
    } else {
      // Backend bağlı değilse mock yanıt
      setTimeout(() => {
        const mockResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: 'Backend sunucusu çalışmıyor. Lütfen backend kurulum talimatlarını takip ederek sunucuyu başlatın.\n\n🔧 Kurulum için "Backend Kurulumu" butonuna tıklayın.',
          sender: 'agent',
          agentType: 'chat',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, mockResponse]);
        setIsLoading(false);
      }, 1000);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const updateAgentModel = (agentId: string, newModel: string) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId ? { ...agent, model: newModel } : agent
    ));
  };

  const handleSaveOpenRouterKey = async () => {
    if (!openrouterApiKey.trim()) {
      alert('Lütfen geçerli bir API anahtarı girin');
      return;
    }

    try {
      const response = await fetch('http://localhost:5001/api/config/openrouter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: openrouterApiKey
        })
      });

      if (response.ok) {
        alert('OpenRouter API anahtarı başarıyla kaydedildi!');
      } else {
        const error = await response.json();
        alert(`Hata: ${error.error}`);
      }
    } catch (error) {
      alert('Backend sunucusuna bağlanılamıyor. Sunucunun çalıştığından emin olun.');
    }
  };

  const renderMessage = (message: Message) => {
    const agent = getAgentInfo(message.agentType);
    const IconComponent = agent.icon;
    
    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`flex gap-4 p-4 rounded-lg ${
          message.sender === 'user' 
            ? 'bg-slate-700/50 ml-12' 
            : 'bg-slate-800/50 mr-12'
        }`}
      >
        {message.sender === 'agent' && (
          <div className={`flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r ${agent.color} flex items-center justify-center`}>
            <IconComponent className="w-5 h-5 text-white" />
          </div>
        )}
        
        <div className="flex-1">
          {message.sender === 'agent' && (
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-semibold text-slate-300">{agent.name}</span>
              <span className="text-xs text-slate-500">{agent.model}</span>
              {message.classification && (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  message.classification === 'karmaşık' 
                    ? 'bg-purple-500/20 text-purple-300' 
                    : 'bg-green-500/20 text-green-300'
                }`}>
                  {message.classification}
                </span>
              )}
            </div>
          )}
          
          <div className="prose prose-slate prose-invert max-w-none">
            <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
          
          <div className="text-xs text-slate-500 mt-2">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
        
        {message.sender === 'user' && (
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-slate-600 to-slate-700 flex items-center justify-center">
            <span className="text-white text-sm font-bold">U</span>
          </div>
        )}
      </motion.div>
    );
  };

  const renderAgentsPanel = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Ajanlar</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">Toplam: {agents.length}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {agents.map((agent) => {
          const IconComponent = agent.icon;
          return (
            <motion.div
              key={agent.id}
              whileHover={{ scale: 1.02 }}
              className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg border border-slate-700/50"
            >
              <div className="flex items-start gap-3">
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${agent.color} flex items-center justify-center flex-shrink-0`}>
                  <IconComponent className="w-6 h-6 text-white" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-white">{agent.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      agent.status === 'working' ? 'bg-yellow-500/20 text-yellow-300' :
                      agent.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                      'bg-slate-500/20 text-slate-300'
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                  
                  <p className="text-sm text-slate-400 mb-3">{agent.description}</p>
                  
                  <div className="space-y-2">
                    <label className="block text-xs font-medium text-slate-300">Model</label>
                    <input
                      type="text"
                      value={agent.model}
                      onChange={(e) => updateAgentModel(agent.id, e.target.value)}
                      placeholder="Örn: meta-llama/llama-3.1-70b-instruct"
                      className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                    />
                    <p className="text-xs text-slate-500">
                      OpenRouter model adını girin. Örnek: meta-llama/llama-3.1-70b-instruct
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );

  const renderProjectsPanel = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Projeler</h2>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg font-medium"
        >
          Yeni Proje
        </motion.button>
      </div>
      
      {currentProject ? (
        <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-lg border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">{currentProject.name}</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              currentProject.status === 'completed' ? 'bg-green-500/20 text-green-300' :
              currentProject.status === 'testing' ? 'bg-yellow-500/20 text-yellow-300' :
              currentProject.status === 'development' ? 'bg-blue-500/20 text-blue-300' :
              'bg-purple-500/20 text-purple-300'
            }`}>
              {currentProject.status}
            </span>
          </div>
          
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">İlerleme</span>
              <span className="text-sm text-slate-300">{currentProject.progress}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <motion.div 
                className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${currentProject.progress}%` }}
                transition={{ duration: 1 }}
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2">Aktif Ajanlar</h4>
              <div className="space-y-1">
                {currentProject.agents.map((agentId) => {
                  const agent = agents.find(a => a.id === agentId);
                  return agent ? (
                    <div key={agentId} className="flex items-center gap-2 text-sm">
                      <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${agent.color}`} />
                      <span className="text-slate-400">{agent.name}</span>
                    </div>
                  ) : null;
                })}
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2">Dosyalar</h4>
              <div className="space-y-1">
                {currentProject.files.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm text-slate-400">
                    <FileText className="w-3 h-3" />
                    <span>{file}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <Folder className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">Henüz aktif proje yok</p>
          <p className="text-sm text-slate-500 mt-2">Karmaşık bir istek göndererek proje başlatın</p>
        </div>
      )}
    </div>
  );

  const renderSettingsPanel = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Ayarlar</h2>
      
      <div className="space-y-4">
        {/* Backend Status */}
        <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-3">Backend Durumu</h3>
          <div className="space-y-3">
            <ConnectionStatus 
              isConnected={isConnected} 
              error={connectionError}
            />
            
            {!isConnected && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowBackendInstructions(true)}
                className="w-full flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-lg font-medium hover:from-cyan-700 hover:to-blue-700 transition-colors"
              >
                <Server className="w-5 h-5" />
                Backend Kurulumu
                <ExternalLink className="w-4 h-4 ml-auto" />
              </motion.button>
            )}
          </div>
        </div>

        {/* OpenRouter API */}
        <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-3">OpenRouter API</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">API Anahtarı</label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={openrouterApiKey}
                  onChange={(e) => setOpenrouterApiKey(e.target.value)}
                  placeholder="OpenRouter API anahtarınızı girin"
                  className="flex-1 bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                />
                <button
                  onClick={handleSaveOpenRouterKey}
                  disabled={!isConnected}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-green-700 transition-colors"
                >
                  Kaydet
                </button>
              </div>
              {!isConnected && (
                <p className="text-xs text-yellow-400 mt-1">
                  ⚠️ API anahtarını kaydetmek için backend bağlantısı gerekli
                </p>
              )}
            </div>
            
            <div className="flex items-start gap-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-blue-300 font-medium text-sm mb-1">
                  OpenRouter Hesabı Gerekli
                </p>
                <p className="text-blue-200/80 text-sm mb-2">
                  AtomAgent çalışması için OpenRouter API anahtarına ihtiyaç var.
                </p>
                <a
                  href="https://openrouter.ai/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 text-sm font-medium"
                >
                  OpenRouter.ai <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        </div>
        
        {/* System Settings */}
        <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-3">Sistem Ayarları</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-300">Karanlık Tema</span>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg ${darkMode ? 'bg-cyan-500' : 'bg-slate-600'} text-white`}
              >
                {darkMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              </motion.button>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Token Limiti (per request)</label>
              <input
                type="number"
                defaultValue="4096"
                className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Sıcaklık (Temperature)</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                defaultValue="0.7"
                className="w-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gradient-to-br from-slate-900 to-slate-800' : 'bg-gradient-to-br from-slate-100 to-slate-200'} flex`}>
      {/* Sidebar */}
      <div className={`w-16 ${darkMode ? 'bg-slate-900/50' : 'bg-white/50'} backdrop-blur-sm border-r ${darkMode ? 'border-slate-700/50' : 'border-slate-300/50'} flex flex-col items-center py-6 space-y-4`}>
        <motion.div
          whileHover={{ scale: 1.1 }}
          className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center"
        >
          <Bot className="w-6 h-6 text-white" />
        </motion.div>
        
        <div className="flex-1 flex flex-col space-y-2">
          {[
            { id: 'chat', icon: MessageCircle, label: 'Chat' },
            { id: 'agents', icon: Users, label: 'Ajanlar' },
            { id: 'projects', icon: Folder, label: 'Projeler' },
            { id: 'settings', icon: Settings, label: 'Ayarlar' }
          ].map((tab) => (
            <motion.button
              key={tab.id}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setActiveTab(tab.id as any)}
              className={`p-3 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-cyan-500/20 text-cyan-400'
                  : darkMode ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <tab.icon className="w-5 h-5" />
            </motion.button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className={`${darkMode ? 'bg-slate-800/50' : 'bg-white/50'} backdrop-blur-sm border-b ${darkMode ? 'border-slate-700/50' : 'border-slate-300/50'} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent`}>
                AtomAgent
              </h1>
              <p className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                CrewAI Tabanlı Çok Ajanlı Geliştirme Ortamı
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <ConnectionStatus 
                isConnected={isConnected} 
                error={connectionError}
                className="hidden md:flex"
              />
              
              <div className="flex items-center gap-2">
                <Cpu className={`w-4 h-4 ${darkMode ? 'text-slate-400' : 'text-slate-600'}`} />
                <span className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                  {agents.filter(a => a.status === 'working').length} ajan aktif
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'chat' && (
              <motion.div
                key="chat"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full flex flex-col"
              >
                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-6">
                  {messages.map(renderMessage)}
                  
                  {/* Streaming message */}
                  {streamingMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-4 p-4 rounded-lg bg-slate-800/50 mr-12"
                    >
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                        <MessageCircle className="w-5 h-5 text-white" />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-semibold text-slate-300">Chat Agent</span>
                          <span className="text-xs text-slate-500">Yazıyor...</span>
                        </div>
                        
                        <div className="prose prose-slate prose-invert max-w-none">
                          <p className="text-slate-200 leading-relaxed">{streamingMessage}</p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                  
                  {/* Loading indicator */}
                  {isLoading && !streamingMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-4 p-4 rounded-lg bg-slate-800/50 mr-12"
                    >
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                        <MessageCircle className="w-5 h-5 text-white" />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-semibold text-slate-300">Sistem</span>
                          <span className="text-xs text-slate-500">İşleniyor...</span>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                          <span className="text-sm text-slate-400">Yanıt hazırlanıyor...</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className={`${darkMode ? 'bg-slate-800/50' : 'bg-white/50'} backdrop-blur-sm rounded-lg border ${darkMode ? 'border-slate-700/50' : 'border-slate-300/50'} p-4`}>
                  <div className="flex items-end gap-3">
                    <textarea
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Projenizi anlatın veya soru sorun..."
                      className={`flex-1 ${darkMode ? 'bg-transparent text-white placeholder-slate-400' : 'bg-transparent text-slate-900 placeholder-slate-500'} resize-none focus:outline-none max-h-32`}
                      rows={1}
                    />
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || isLoading}
                      className="p-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send className="w-5 h-5" />
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'agents' && (
              <motion.div
                key="agents"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {renderAgentsPanel()}
              </motion.div>
            )}

            {activeTab === 'projects' && (
              <motion.div
                key="projects"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {renderProjectsPanel()}
              </motion.div>
            )}

            {activeTab === 'settings' && (
              <motion.div
                key="settings"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {renderSettingsPanel()}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Backend Instructions Modal */}
      <BackendInstructions 
        isVisible={showBackendInstructions}
        onClose={() => setShowBackendInstructions(false)}
      />
    </div>
  );
}

export default App;
