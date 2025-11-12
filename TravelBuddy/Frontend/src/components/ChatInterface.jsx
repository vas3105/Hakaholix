import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send } from 'lucide-react';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const userId = 'user123'; // temporary — replace later with real auth

  // ✅ Connect to backend WebSocket (proxy handles /ws)
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8001/ws/voice');

    websocket.onopen = () => {
      console.log('✅ WebSocket connected');
      setWs(websocket);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'transcription') {
        addMessage(data.text, 'user');
      } else if (data.type === 'response') {
        addMessage(data.data.message, 'assistant', data.data);
      } else if (data.type === 'audio_response') {
        playAudio(data.audio);
      }
    };

    websocket.onerror = (err) => console.error('❌ WebSocket error:', err);

    return () => {
      websocket.close();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addMessage = (text, role, data = null) => {
    setMessages((prev) => [...prev, { text, role, data, timestamp: new Date() }]);
  };

  // ✅ Send text to backend chat endpoint via /api/chat
  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage = input;
    setInput('');
    addMessage(userMessage, 'user');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, user_id: userId })
      });

      const data = await response.json();
      addMessage(
        data.message || "I'm here! How can I assist you today?",
        'assistant',
        data
      );

    } catch (error) {
      console.error('Error:', error);
      addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
      setIsLoading(false);
    }
  };

  // 🎤 Recording logic (unchanged)
  const startRecording = async () => {
    console.log("🎙️ Mic button clicked — startRecording() triggered"); // add this
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          if (ws && ws.readyState === WebSocket.OPEN) {
            const reader = new FileReader();
            reader.onload = () => {
              const base64 = btoa(
                new Uint8Array(reader.result).reduce((data, byte) => data + String.fromCharCode(byte), '')
              );
              ws.send(JSON.stringify({ type: 'audio_chunk', audio: base64 }));
            };
            reader.readAsArrayBuffer(event.data);
          }
        }
      };

      mediaRecorder.start(100);
      setIsRecording(true);

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'start_recording', user_id: userId }));
      }
    } catch (error) {
      console.error('Recording error:', error);
    }
  };

  const stopRecording = () => {
    console.log("🛑 Mic button clicked — stopRecording() triggered"); // add this
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'stop_recording', user_id: userId }));
      }

      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const playAudio = (base64Audio) => {
    const audioBlob = base64ToBlob(base64Audio, 'audio/wav');
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
  };

  const base64ToBlob = (base64, mimeType) => {
    const byteCharacters = atob(base64);
    const byteArrays = [];
    for (let offset = 0; offset < byteCharacters.length; offset += 512) {
      const slice = byteCharacters.slice(offset, offset + 512);
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) byteNumbers[i] = slice.charCodeAt(i);
      byteArrays.push(new Uint8Array(byteNumbers));
    }
    return new Blob(byteArrays, { type: mimeType });
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-md p-4">
        <h1 className="text-2xl font-bold text-indigo-600">Kerala Travel Assistant</h1>
        <p className="text-gray-600 text-sm">Your AI-powered travel companion</p>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-lg p-4 shadow ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-800'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {msg.data?.recommendations && (
                <div className="mt-3 space-y-2">
                  {msg.data.recommendations.hotels?.slice(0, 3).map((hotel, i) => (
                    <div key={i} className="bg-indigo-50 p-2 rounded text-sm">
                      <p className="font-semibold text-indigo-800">{hotel.metadata.name}</p>
                      <p className="text-gray-600">₹{hotel.metadata.price}/night</p>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-xs mt-2 opacity-70">
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-lg p-4 shadow">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask me anything about Kerala..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={isLoading || isRecording}
          />

          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`p-2 rounded-lg ${
              isRecording ? 'bg-red-500 hover:bg-red-600 animate-pulse' : 'bg-indigo-600 hover:bg-indigo-700'
            } text-white transition`}
          >
            {isRecording ? <MicOff size={24} /> : <Mic size={24} />}
          </button>

          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="bg-indigo-600 text-white p-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            <Send size={24} />
          </button>
        </div>

        {isRecording && (
          <p className="text-sm text-red-500 mt-2 text-center animate-pulse">
            Recording... Click microphone to stop
          </p>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
