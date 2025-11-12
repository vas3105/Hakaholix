import React, { useState } from 'react';
import './bot.css';
import { IoBusinessOutline, IoSend } from "react-icons/io5";
import { FaMicrophone } from "react-icons/fa";
import Results from "./Results";

const Hotelchat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: "Hello! 👋 Welcome to Kerala Travel Assistant. I'm here to help you find the perfect stay and plan your travel. How can I assist you today?",
      time: '03:09 PM',
    },
  ]);
  
  const [inputText, setInputText] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [activeTab, setActiveTab] = useState('hotels');

  const handleSend = async () => {
    if (inputText.trim() === '') return;

    // Add user message
    setMessages(prev => [...prev, {
      id: Date.now(),
      sender: 'user',
      text: inputText,
      time: new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit'
      })
    }]);

    try {
      // Make API call to your backend (use relative path so Vite proxy can forward to backend)
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: inputText,
          user_id: 'default'
        })
      });

      const data = await response.json();

      // Add bot response
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.response,
        time: new Date().toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })
      }]);

      // If there are hotels or attractions in the response, update the results
      if (data.hotels || data.attractions) {
        setSearchResults({
          hotels: data.hotels,
          attractions: data.attractions
        });
      }
    } catch (error) {
      console.error('Error:', error);
      // Add error message
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'bot',
        text: "I'm sorry, but I'm having trouble connecting to the server. Please try again later.",
        time: new Date().toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })
      }]);
    }

    setInputText('');
  };

  return (
    <div className="chat-page-container">
      <h1 className="main-title">
        Plan your perfect Kerala getaway with our AI-powered travel assistant
      </h1>

      <div className="chat-window">
        {/* Chat Header */}
        <header className="chat-header">
          <div className="header-icon">
            <IoBusinessOutline />
          </div>
          <div className="header-text">
            <h2>Kerala Travel Assistant</h2>
            <p>Your personal travel companion</p>
          </div>
        </header>

        {/* Message List */}
        <main className="message-list">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-bubble ${msg.sender}`}>
              <p>{msg.text}</p>
              <span className="timestamp">{msg.time}</span>
            </div>
          ))}
        </main>

        {/* Results Section */}
        {searchResults && (
          <Results 
            hotels={searchResults.hotels}
            attractions={searchResults.attractions}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        )}

        {/* Input Area */}
        <footer className="chat-input-area">
          <div className="input-wrapper">
            <button className="mic-button">
              <FaMicrophone />
            </button>
            <input
              type="text"
              placeholder="Ask about hotels, attractions, travel plans..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="send-button" onClick={handleSend}>
              <IoSend />
            </button>
          </div>
          <p className="input-hint">
            Type your message or <FaMicrophone size={12} /> use voice chat to
            get started
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Hotelchat;