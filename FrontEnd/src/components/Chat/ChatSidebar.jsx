// src/components/Chat/ChatSidebar.jsx
import React from "react";
import { FaPlus, FaClock } from "react-icons/fa";
import "../../css/chatbot.css";

const ChatSidebar = () => {
  const recentChats = ["AI Basics", "React Roadmap", "Data Science Path"];

  return (
    <div className="sidebar-container">
      <div className="sidebar-header">
        <span>Recent Chats</span>
        <FaPlus className="sidebar-add" />
      </div>

      <div className="sidebar-list">
        {recentChats.map((chat, i) => (
          <div key={i} className="sidebar-item">
            <FaClock style={{ marginRight: "8px" }} /> {chat}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatSidebar;
