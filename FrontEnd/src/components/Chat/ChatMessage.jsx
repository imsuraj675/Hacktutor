import React from "react";
import "../../css/chatbot.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";

const ChatMessage = ({ sender, text }) => {
  // console.log("Rendering message from:", sender);
  // console.log("Message text:", text);
  return (
    <div className={`message ${sender} prose max-w-none`}>
      {sender === "ai" && text? (
        text.map((seg, idx) => {
          if (seg.type === "markdown") {
            return (
              <ReactMarkdown
                key={idx}
                children={seg.content}
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw, rehypeSanitize]}
                style={{ textAlign: "left" }}
              />
            );
          } else if (seg.type === "svg") {
            return (
              <div
                key={idx}
                dangerouslySetInnerHTML={{ __html: seg.content }}
              />
            );
          } else if (seg.type === "img") {
            return (
              <div
                key={idx}
                className="chat-image"
                dangerouslySetInnerHTML={{ __html: seg.content }}
              />
            );
          }else if (seg.type === "error") {
            return (
              <div key={idx} style={{ color: "red" }}>
                ⚠️ Error rendering diagram: {seg.content}
              </div>
            );
          } else {
            return null;
          }
        })
      ) : (
        // Normal user message
        <ReactMarkdown
          children={text}
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw, rehypeSanitize]}
          style={{ textAlign: "left" }}
        />
      )}
    </div>
  );
};

export default ChatMessage;
