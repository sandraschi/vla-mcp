import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

export default function HelpPage() {
  const [slug, setSlug] = useState("tools");
  const [content, setContent] = useState("");
  const [slugs, setSlugs] = useState<string[]>([]);

  useEffect(() => {
    apiGet<{ slugs?: string[] }>("/api/v1/help").then((d) => setSlugs(d.slugs ?? [])).catch(console.error);
  }, []);

  useEffect(() => {
    apiGet<{ content?: string }>(`/api/v1/help/${slug}`)
      .then((d) => setContent(d.content ?? ""))
      .catch(() => setContent("Doc not found."));
  }, [slug]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Help</h1>
      <div className="flex gap-2 mb-4 flex-wrap">
        {slugs.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSlug(s)}
            className={`text-xs px-2 py-1 rounded ${slug === s ? "bg-violet-700" : "bg-gray-800"}`}
          >
            {s}
          </button>
        ))}
      </div>
      <pre className="bg-gray-900 border border-gray-800 rounded p-4 text-xs whitespace-pre-wrap max-h-[70vh] overflow-y-auto">
        {content}
      </pre>
    </div>
  );
}
