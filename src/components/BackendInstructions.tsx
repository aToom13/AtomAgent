import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, 
  Download, 
  Play, 
  CheckCircle, 
  AlertCircle, 
  Copy, 
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Code
} from 'lucide-react';

interface BackendInstructionsProps {
  isVisible: boolean;
  onClose: () => void;
}

export const BackendInstructions: React.FC<BackendInstructionsProps> = ({
  isVisible,
  onClose
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null);

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCommand(text);
      setTimeout(() => setCopiedCommand(null), 2000);
    } catch (err) {
      console.error('Kopyalama hatası:', err);
    }
  };

  const steps = [
    {
      title: 'Backend Dosyalarını İndirin',
      description: 'Backend kodları src/backend/ dizininde hazır durumda',
      icon: Download,
      commands: [],
      details: 'AtomAgent backend dosyaları projenizin src/backend/ klasöründe bulunmaktadır.'
    },
    {
      title: 'Backend Dizinine Gidin',
      description: 'Terminal ile backend dizinine geçin',
      icon: Terminal,
      commands: ['cd src/backend'],
      details: 'Backend dosyalarının bulunduğu dizine geçmek için terminal açın.'
    },
    {
      title: 'Python Sanal Ortamı Oluşturun',
      description: 'İzole bir Python ortamı oluşturun',
      icon: Code,
      commands: [
        'python -m venv venv',
        '# Linux/Mac için:',
        'source venv/bin/activate',
        '# Windows için:',
        'venv\\Scripts\\activate'
      ],
      details: 'Sanal ortam, bağımlılıkları izole eder ve sistem Python\'unu karıştırmaz.'
    },
    {
      title: 'Bağımlılıkları Yükleyin',
      description: 'Gerekli Python paketlerini yükleyin',
      icon: Download,
      commands: ['pip install -r requirements.txt'],
      details: 'CrewAI, Flask ve diğer gerekli paketler otomatik olarak yüklenecek.'
    },
    {
      title: 'API Anahtarını Yapılandırın',
      description: 'OpenRouter API anahtarınızı ayarlayın',
      icon: AlertCircle,
      commands: [],
      details: 'Arayüzden Settings > OpenRouter API bölümünden API anahtarınızı girebilirsiniz. Alternatif olarak .env dosyası da oluşturabilirsiniz.'
    },
    {
      title: 'Sunucuyu Başlatın',
      description: 'Backend sunucusunu çalıştırın',
      icon: Play,
      commands: ['python server.py'],
      details: 'Sunucu http://localhost:5000 adresinde çalışmaya başlayacak.'
    }
  ];

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="p-6 border-b border-slate-700/50">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  AtomAgent Backend Kurulumu
                </h2>
                <p className="text-slate-400">
                  CrewAI tabanlı backend sunucusunu çalıştırmak için aşağıdaki adımları takip edin
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-700/50"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex">
            {/* Steps Sidebar */}
            <div className="w-80 border-r border-slate-700/50 p-4 space-y-2 max-h-[70vh] overflow-y-auto">
              {steps.map((step, index) => {
                const IconComponent = step.icon;
                const isActive = activeStep === index;
                const isCompleted = activeStep > index;

                return (
                  <motion.button
                    key={index}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setActiveStep(index)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isActive
                        ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300'
                        : isCompleted
                        ? 'bg-green-500/20 border-green-500/50 text-green-300'
                        : 'bg-slate-700/30 border-slate-600/50 text-slate-300 hover:bg-slate-700/50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        isActive
                          ? 'bg-cyan-500/30'
                          : isCompleted
                          ? 'bg-green-500/30'
                          : 'bg-slate-600/30'
                      }`}>
                        {isCompleted ? (
                          <CheckCircle className="w-5 h-5" />
                        ) : (
                          <IconComponent className="w-5 h-5" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <h3 className="font-medium text-sm mb-1">{step.title}</h3>
                        <p className="text-xs opacity-75">{step.description}</p>
                      </div>
                      
                      <div className="flex-shrink-0">
                        {isActive ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </div>
                    </div>
                  </motion.button>
                );
              })}
            </div>

            {/* Step Details */}
            <div className="flex-1 p-6 max-h-[70vh] overflow-y-auto">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="mb-4">
                    <h3 className="text-xl font-semibold text-white mb-2">
                      {steps[activeStep].title}
                    </h3>
                    <p className="text-slate-300 leading-relaxed">
                      {steps[activeStep].details}
                    </p>
                  </div>

                  {steps[activeStep].commands.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-lg font-medium text-slate-200 mb-3">
                        Komutlar:
                      </h4>
                      
                      {steps[activeStep].commands.map((command, cmdIndex) => {
                        if (command.startsWith('#')) {
                          return (
                            <div key={cmdIndex} className="text-sm text-slate-400 italic">
                              {command}
                            </div>
                          );
                        }

                        return (
                          <div
                            key={cmdIndex}
                            className="bg-slate-900/50 border border-slate-600/50 rounded-lg p-4"
                          >
                            <div className="flex items-center justify-between">
                              <code className="text-cyan-300 font-mono text-sm flex-1">
                                {command}
                              </code>
                              <button
                                onClick={() => copyToClipboard(command)}
                                className="ml-3 p-2 text-slate-400 hover:text-white rounded transition-colors"
                              >
                                {copiedCommand === command ? (
                                  <CheckCircle className="w-4 h-4 text-green-400" />
                                ) : (
                                  <Copy className="w-4 h-4" />
                                )}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Special instructions for API key step */}
                  {activeStep === 4 && (
                    <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-yellow-300 font-medium mb-2">
                            OpenRouter API Anahtarı Gerekli
                          </p>
                          <p className="text-yellow-200/80 text-sm mb-3">
                            AtomAgent çalışması için OpenRouter API anahtarına ihtiyaç var. 
                            Ücretsiz hesap oluşturabilir ve kredi satın alabilirsiniz.
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
                  )}

                  {/* Navigation buttons */}
                  <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700/50">
                    <button
                      onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
                      disabled={activeStep === 0}
                      className="px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-700 transition-colors"
                    >
                      Önceki
                    </button>
                    
                    <span className="text-sm text-slate-400">
                      {activeStep + 1} / {steps.length}
                    </span>
                    
                    <button
                      onClick={() => setActiveStep(Math.min(steps.length - 1, activeStep + 1))}
                      disabled={activeStep === steps.length - 1}
                      className="px-4 py-2 bg-cyan-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-cyan-700 transition-colors"
                    >
                      Sonraki
                    </button>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};