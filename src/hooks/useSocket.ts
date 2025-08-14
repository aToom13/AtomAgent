import { useEffect, useState, useCallback } from 'react';
import io, { Socket } from 'socket.io-client';

interface SocketData {
  message?: string;
  classification?: string;
  response?: string;
  result?: string;
  agent?: string;
  timestamp?: string;
  content?: string;
  complete?: boolean;
  project_id?: string;
  project?: any;
  error?: string;
  message_received?: any;
  simple_response?: any;
  complex_response?: any;
  message_stream?: any;
  project_update?: any;
}

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  sendMessage: (message: string) => void;
  lastMessage: SocketData | null;
  connectionError: string | null;
}

export const useSocket = (serverUrl: string = 'http://localhost:5001'): UseSocketReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<SocketData | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    // Socket bağlantısı oluştur
    const newSocket = io(serverUrl, {
      transports: ['websocket', 'polling'],
      timeout: 5000,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    // Bağlantı event'leri
    newSocket.on('connect', () => {
      console.log('Backend bağlantısı başarılı:', newSocket.id);
      setIsConnected(true);
      setConnectionError(null);
    });

    newSocket.on('disconnect', (reason) => {
      console.log('Backend bağlantısı koptu:', reason);
      setIsConnected(false);
    });

    newSocket.on('connect_error', (error) => {
      console.error('Bağlantı hatası:', error);
      setConnectionError('Backend sunucusuna bağlanılamıyor. Sunucunun çalıştığından emin olun.');
      setIsConnected(false);
    });

    // Mesaj event'leri
    newSocket.on('connected', (data: SocketData) => {
      console.log('Backend hazır:', data.message);
      setLastMessage(data);
    });

    newSocket.on('message_received', (data: SocketData) => {
      console.log('Mesaj alındı:', data);
      setLastMessage(data);
    });

    newSocket.on('simple_response', (data: SocketData) => {
      console.log('Basit yanıt:', data);
      setLastMessage(data);
    });

    newSocket.on('complex_response', (data: SocketData) => {
      console.log('Karmaşık yanıt:', data);
      setLastMessage(data);
    });

    newSocket.on('message_stream', (data: SocketData) => {
      console.log('Streaming mesaj:', data);
      setLastMessage(data);
    });

    newSocket.on('project_update', (data: SocketData) => {
      console.log('Proje güncelleme:', data);
      setLastMessage(data);
    });

    newSocket.on('error', (data: SocketData) => {
      console.error('Socket hatası:', data);
      setLastMessage(data);
      setConnectionError(data.message || 'Bilinmeyen hata oluştu');
    });

    setSocket(newSocket);

    // Cleanup
    return () => {
      newSocket.disconnect();
    };
  }, [serverUrl]);

  const sendMessage = useCallback((message: string) => {
    if (socket && isConnected) {
      console.log('Mesaj gönderiliyor:', message);
      socket.emit('send_message', {
        message: message,
        user_id: socket.id,
        timestamp: new Date().toISOString(),
      });
    } else {
      console.warn('Socket bağlı değil, mesaj gönderilemedi');
      setConnectionError('Backend sunucusuna bağlı değil');
    }
  }, [socket, isConnected]);

  return {
    socket,
    isConnected,
    sendMessage,
    lastMessage,
    connectionError,
  };
};
