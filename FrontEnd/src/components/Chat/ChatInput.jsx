// src/components/Chat/ChatInput.jsx
import React, { useState, useEffect } from "react";
import { FaPaperPlane } from "react-icons/fa";
import "../../css/chatbot.css";

const ChatInput = ({ onSend, disabled }) => {
  const [input, setInput] = useState("");

  const handleSend = (type) => {
    if (!input.trim()) return;
    onSend(input, type);
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // const handleDownload = (url) => {
  //   // const video = document.querySelector("video");
  //   // const url = video.src;
  //   const backendUrl = import.meta.env.VITE_BACKEND_URL;
  //   const a = document.createElement("a");
  //   url = `${backendUrl}${path}`
  //   a.href = url;
  //   a.download = "video.mp4";
  //   a.click();
  // };

  return (
    <footer className="chatbot-input">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your question..."
        disabled={disabled}
      />
      <button onClick={() => handleSend('img')} disabled={disabled}>
        <FaPaperPlane style={{ marginRight: "6px" }} /> Send
      </button>
      <button onClick={() => handleSend('vid')} disabled={disabled}>
        <FaPaperPlane style={{ marginRight: "6px" }} /> Generate Video
      </button>
    </footer>
  );
};

export default ChatInput;
