import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, system-ui, sans-serif',
  themeVariables: {
    darkMode: true,
    background: '#0B0F17',
    primaryColor: '#4F46E5',
    primaryTextColor: '#FFFFFF',
    primaryBorderColor: '#6366F1',
    lineColor: '#818CF8',
    secondaryColor: '#1E1B4B',
    tertiaryColor: '#0F172A'
  }
});

export default function MermaidDiagram({ chartCode }) {
  const containerRef = useRef(null);
  const [svgContent, setSvgContent] = useState('');
  const [renderError, setRenderError] = useState(false);

  useEffect(() => {
    if (!chartCode) return;

    let isMounted = true;
    const renderChart = async () => {
      try {
        setRenderError(false);
        const id = `mermaid_svg_${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, chartCode);
        if (isMounted) {
          setSvgContent(svg);
        }
      } catch (err) {
        console.error("Mermaid render error:", err);
        if (isMounted) {
          setRenderError(true);
        }
      }
    };

    renderChart();

    return () => {
      isMounted = false;
    };
  }, [chartCode]);

  if (renderError || !svgContent) {
    return (
      <div className="p-4 rounded-xl bg-slate-900 border border-gray-800 text-xs font-mono text-indigo-300 overflow-x-auto">
        <pre className="text-gray-300">{chartCode}</pre>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="p-6 rounded-2xl bg-slate-950/90 border border-indigo-500/20 overflow-x-auto flex justify-center shadow-lg shadow-indigo-950/20 my-4"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
}
