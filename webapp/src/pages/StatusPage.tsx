import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

export default function StatusPage() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    apiGet("/api/v1/status").then(setStatus).catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Status</h1>
      <pre className="bg-gray-900 border border-gray-800 rounded p-4 text-xs overflow-x-auto">
        {JSON.stringify(status, null, 2)}
      </pre>
    </div>
  );
}
