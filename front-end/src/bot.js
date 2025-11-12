import React, { useState, useEffect, useRef } from 'react';
import './bot.css';
import { IoBusinessOutline, IoSend } from 'react-icons/io5';
import { FaMicrophone, FaStar } from 'react-icons/fa';

// This is a new sub-component to render the JSON response
// It's clean to keep this logic separate.
const BotMessage = ({ message }) => {
  const { text, data, time } = message;

  // This is a simple text message (like the intro)
  if (text) {
    return (
      <div className="message-bubble bot">
        <p>{text}</p>
        <span className="timestamp">{time}</span>
      </div>
    );
  }

  // This is a JSON response!
  // We'll check its 'type' to decide how to render it.
  if (data) {
    switch (data.type) {
      case 'hotel_recommendation':
      case 'restaurant_recommendation':
        return (
          <div className="message-bubble bot">
            <p>{data.text}</p> {/* The text from the JSON */}
            
            {/* Here we render the structured JSON data */}
            <div className="hotel-card">
              <h4>{data.details.name}</h4>
              <p>
                <FaStar className="star-icon" /> {data.details.star_rating}
              </p>
              <div className="price">{data.details.base_price_inr}</div>
            </div>
            
            <span className="timestamp">{time}</span>
          </div>
        );

      // You could add more 'case' statements for other JSON types
      // case 'booking_confirmation':
      //   return <BookingConfirmation data={data} />;
        
      default:
        // A fallback in case the JSON 'type' isn't recognized
        return (
          <div className="message-bubble bot">
            <p>{data.text || 'I have some information for you:'}</p>
            <pre className="json-fallback">{JSON.stringify(data.details, null, 2)}</pre>
            <span className="timestamp">{time}</span>
          </div>
        );
    }
  }

  return null; // Should not happen
};


// Main Chat Component
const Hotelchat = () => {
  // Updated initial message state
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: "Hello! 👋 Welcome to Hotel Concierge. I'm here to help you find the perfect stay and plan your travel. How can I assist you today?",
      time: '03:09 PM',
    },
  ]);
  
  const [inputText, setInputText] = useState('');
  const [isBotTyping, setIsBotTyping] = useState(false);
  
  // A ref to auto-scroll to the bottom
  const messageListRef = useRef(null);

  // Auto-scroll effect
  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages, isBotTyping]);


  // --- This is the new logic ---
  
  // 1. Simulates the LLM JSON response
  const simulateLlmResponse = () => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // This is the MOCK JSON your LLM would send
    const mockJsonData = {
      type: 'hotel_recommendation',
      text: "I've found a fantastic 5-star hotel that matches your request:",
      details: {
        name: "The Grand React Hotel",
        rating: 4.8,
        price: "$250/night",
      }
    };
    
    const botMessage = {
      id: Date.now(),
      sender: 'bot',
      data: mockJsonData, // We put the JSON object in 'data'
      time: time,
    };

    // Add the bot's JSON message to the chat
    setMessages((prevMessages) => [...prevMessages, botMessage]);
    setIsBotTyping(false);
  };

  // 2. Handles sending the user's message
  const handleSend = () => {
    if (inputText.trim() === '') return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: inputText,
      time: time,
    };

    // Add the user's message to the chat
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputText('');
    setIsBotTyping(true);
    
    // Trigger the bot's response after 1 second
    setTimeout(simulateLlmResponse, 1000);
  };
  
  // --- End of new logic ---


  return (
    <div className="chat-page-container">
      <h1 className="main-title">
        Plan your perfect stay with our AI-powered concierge
      </h1>

      <div className="chat-window">
        {/* Chat Header (no change) */}
        <header className="chat-header">
          <div className="header-icon">
            <IoBusinessOutline />
          </div>
          <div className="header-text">
            <h2>Hotel Concierge</h2>
            <p>Your personal travel assistant</p>
          </div>
        </header>

        {/* Message List (updated) */}
        <main className="message-list" ref={messageListRef}>
          {messages.map((msg) => 
            msg.sender === 'user' ? (
              // User Message
              <div key={msg.id} className="message-bubble user">
                <p>{msg.text}</p>
                <span className="timestamp">{msg.time}</span>
              </div>
            ) : (
              // Bot Message (uses our new component)
              <BotMessage key={msg.id} message={msg} />
            )
          )}
          
          {/* Show a "typing..." indicator */}
          {isBotTyping && (
             <div className="message-bubble bot typing-indicator">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
          )}
        </main>

        {/* Input Area (no change in structure) */}
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
