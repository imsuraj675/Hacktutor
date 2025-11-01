// src/components/Chat/Chatbot.jsx
import React, { useState, useEffect, useRef } from "react";
import { Box, CircularProgress } from "@mui/material";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import ChatHeader from "./ChatHeader";
import "../../css/chatbot.css";


const Chatbot = () => {
  const [messages, setMessages] = useState([
    { sender: "ai", text: "👋 Hi! I'm your AI tutor. What topic would you like to explore today?" },
  ]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (text) => {
    if (!text.trim()) return;

    const newMessages = [...messages, { sender: "user", text }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text }),
      });
      const data = await res.json();
      const aiReply = data.message || "Hmm, I didn’t quite catch that.";
      setMessages([...newMessages, { sender: "ai", text: aiReply }]);
    } catch {
      setMessages([...newMessages, { sender: "ai", text: "⚠️ Error: Unable to reach backend." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box className="chatbot-container">
      {/* <ChatHeader /> */}
      <Box className="chatbot-messages">
        {messages.map((msg, i) => (
          <ChatMessage key={i} sender={msg.sender} text={msg.text} />
        ))}
        {loading && (
          <Box className="message ai">
            <CircularProgress size={16} sx={{ color: "#b0b8ff", mr: 1 }} /> Thinking...
          </Box>
        )}
        <div ref={chatEndRef} />
      </Box>
      <ChatInput onSend={handleSend} disabled={loading} />
    </Box>
  );
};

export default Chatbot;
