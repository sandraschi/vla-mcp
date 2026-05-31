import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

export default function ToolsPage() {
  const [tools, setTools] = useState<string[]>([]);

  useEffect(() => {
    apiGet<{ tools?: string[] }>("/api/v1/tools").then((d) => setTools(d.tools ?? [])).catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Tools</h1>
      <p className="text-gray-400 text-sm mb-6">{tools.length} portmanteau MCP tools</p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {tools.map((t) => (
          <code key={t} className="text-xs bg-gray-900 border border-gray-800 px-2 py-2 rounded text-violet-200">
            {t}
          </code>
        ))}
      </div>
    </div>
  );
}
