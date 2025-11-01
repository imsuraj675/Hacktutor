import { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import DemoPage from "./DemoPage";
import ChatAssistant from "./components/Chat/chatbot";
import MainLayout from "./components/MainLayout";
function Home() {
  const [count, setCount] = useState(0);

  return (
    <div className="home-page">
      <div className="logos">
        <a href="https://vite.dev" target="_blank" rel="noreferrer">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" rel="noreferrer">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>

      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>

      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>

      <div style={{ marginTop: "1rem" }}>
        <Link to="/demopage" style={{ color: "skyblue", textDecoration: "none" }}>
          ➤ Go to Demo Page
        </Link>
        <br />
        <Link to="/chat" style={{ color: "skyblue", textDecoration: "none" }}>
          💬 Open Chat Assistant
        </Link>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/demopage" element={<DemoPage />} />
          <Route path="/chat" element={<ChatAssistant />} />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;
