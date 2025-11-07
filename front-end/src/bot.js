import React, { useState } from 'react';
import './bot.css';
import { IoBusinessOutline, IoSend } from 'react-icons/io5';
import { FaMicrophone } from 'react-icons/fa';

const Hotelchat = () => {
  // In a real app, 'messages' would come from state
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: "Hello! 👋 Welcome to Hotel Concierge. I'm here to help you find the perfect stay and plan your travel. How can I assist you today?",
      time: '03:09 PM',
    },
  ]);
  
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (inputText.trim() === '') return;
    
    // Logic to send message would go here
    console.log('Sending:', inputText);
    setInputText('');
  };

  return (
    <div className="chat-page-container">
      <h1 className="main-title">
        Plan your perfect stay with our AI-powered concierge
      </h1>

      <div className="chat-window">
        {/* Chat Header */}
        <header className="chat-header">
          <div className="header-icon">
            <IoBusinessOutline />
          </div>
          <div className="header-text">
            <h2>Hotel Concierge</h2>
            <p>Your personal travel assistant</p>
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

        {/* Input Area */}
        <footer className="chat-input-area">
          <div className="input-wrapper">
            <button className="mic-button">
              <FaMicrophone />
            </button>
            <input
              type="text"
              placeholder="Ask about hotels, bookings, travel plans..."
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