import { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import "./App.css";
import DemoPage from "./DemoPage";
import ChatAssistant from "./components/Chat/chatbot";
import HomePage from "./components/HomePage";
import MainLayout from "./components/MainLayout";

function App() {
  const backendUrl = import.meta.env.VITE_BACKEND_URL;
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/demopage" element={<DemoPage />} />
          <Route path="/chat" element={<ChatAssistant />} />
          <Route path="/chat/:sessionId" element={<ChatAssistant />} />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;
