// src/components/Chat/ChatInput.jsx
import React, { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";
import "../../css/chatbot.css";

const ChatInput = ({ onSend, disabled }) => {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <footer className="chatbot-input">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your question..."
        disabled={disabled}
      />
      <button onClick={handleSend} disabled={disabled}>
        <FaPaperPlane style={{ marginRight: "6px" }} /> Send
      </button>
    </footer>
  );
};

export default ChatInput;
