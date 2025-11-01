// src/components/Chat/ChatMessage.jsx
import React from "react";
import "../../css/chatbot.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";

const ChatMessage = ({ sender, text }) => (
  <div className={`message ${sender} prose max-w-none`}>
    <ReactMarkdown
        children={text}
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        style={{textAlign: "left", justifyItems: "left"}}

    />
  </div>
);

export default ChatMessage;
