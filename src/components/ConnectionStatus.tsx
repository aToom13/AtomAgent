import React from 'react';
import { motion } from 'framer-motion';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';

interface ConnectionStatusProps {
  isConnected: boolean;
  error?: string | null;
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ 
  isConnected, 
  error, 
  className = "" 
}) => {
  if (isConnected && !error) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`flex items-center gap-2 px-3 py-2 bg-green-500/20 border border-green-500/30 rounded-lg ${className}`}
      >
        <Wifi className="w-4 h-4 text-green-400" />
        <span className="text-sm text-green-300 font-medium">Backend Bağlı</span>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`flex items-center gap-2 px-3 py-2 bg-red-500/20 border border-red-500/30 rounded-lg ${className}`}
      >
        <AlertCircle className="w-4 h-4 text-red-400" />
        <div className="flex flex-col">
          <span className="text-sm text-red-300 font-medium">Bağlantı Hatası</span>
          <span className="text-xs text-red-400">{error}</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex items-center gap-2 px-3 py-2 bg-yellow-500/20 border border-yellow-500/30 rounded-lg ${className}`}
    >
      <WifiOff className="w-4 h-4 text-yellow-400" />
      <span className="text-sm text-yellow-300 font-medium">Bağlanıyor...</span>
    </motion.div>
  );
};