import React, { useEffect, useRef } from "react";
import mermaid from "mermaid";

const MermaidRenderer = ({ chartCode }) => {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartCode) return;

    // Initialize Mermaid once
    mermaid.initialize({ startOnLoad: false, theme: "default" });

    const renderDiagram = async () => {
      try {
        // Generate a unique ID for each render
        const id = "mermaid-" + Math.random().toString(36).substr(2, 9);
        const { svg } = await mermaid.render(id, chartCode);
        if (chartRef.current) chartRef.current.innerHTML = svg;
      } catch (err) {
        chartRef.current.innerHTML = `<pre style="color: red;">${err.message}</pre>`;
      }
    };

    renderDiagram();
  }, [chartCode]);

  return (
    <div
      ref={chartRef}
      style={{
        overflowX: "auto",
        backgroundColor: "#f9f9f9",
        padding: "1rem",
        borderRadius: "8px",
        minHeight: "100px",
      }}
    />
  );
};

export default MermaidRenderer;
