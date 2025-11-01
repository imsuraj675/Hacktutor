import React, { useState } from "react";
import MermaidRenderer from "./MermaidRenderer";

const DemoPage = () => {
  const [code, setCode] = useState(`flowchart TD
A[User] --> B[Frontend]
B --> C[Backend]
C --> D[Database]`);

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Mermaid Live Preview</h2>
      <textarea
        rows="6"
        style={{ width: "100%", fontFamily: "monospace" }}
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />
      <MermaidRenderer chartCode={code} />
    </div>
  );
};

export default DemoPage;
