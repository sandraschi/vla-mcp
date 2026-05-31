import { useEffect, useState } from "react";

type Status = {
  server?: string;
  version?: string;
  uptime_s?: number;
  wall?: { upstream_configured?: boolean; upstream_path?: string | null };
  world_model?: { upstream_configured?: boolean };
  dmuon?: { upstream_configured?: boolean };
  dataset_root?: string;
};

export function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1/status")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setStatus)
      .catch((e: Error) => setErr(e.message));
  }, []);

  return (
    <div style={{ minHeight: "100vh", padding: "2rem 1rem", display: "flex", justifyContent: "center" }}>
      <div
        style={{
          maxWidth: 760,
          width: "100%",
          padding: "1.75rem",
          borderRadius: 16,
          background: "rgba(15, 23, 42, 0.8)",
          border: "1px solid rgba(148, 163, 184, 0.25)",
        }}
      >
        <h1 style={{ margin: "0 0 0.5rem" }}>VLA-MCP</h1>
        <p style={{ color: "#94a3b8", marginTop: 0 }}>
          Wall-OSS-0.5 + WALL-WM + DMuon bridge. Fleet loops with worldlabs, robotics, avatar.
        </p>
        {err && <p style={{ color: "#f87171" }}>API: {err}</p>}
        {status && (
          <dl style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: "0.5rem 1rem", fontSize: "0.9rem" }}>
            <dt style={{ color: "#94a3b8" }}>Server</dt>
            <dd style={{ margin: 0 }}>{status.server} v{status.version}</dd>
            <dt style={{ color: "#94a3b8" }}>Wall-OSS</dt>
            <dd style={{ margin: 0 }}>
              {status.wall?.upstream_configured ? status.wall.upstream_path : "not configured"}
            </dd>
            <dt style={{ color: "#94a3b8" }}>WALL-WM</dt>
            <dd style={{ margin: 0 }}>{status.world_model?.upstream_configured ? "ready" : "not configured"}</dd>
            <dt style={{ color: "#94a3b8" }}>DMuon</dt>
            <dd style={{ margin: 0 }}>{status.dmuon?.upstream_configured ? "ready" : "not configured"}</dd>
            <dt style={{ color: "#94a3b8" }}>Dataset</dt>
            <dd style={{ margin: 0 }}>{status.dataset_root}</dd>
          </dl>
        )}
        <footer style={{ marginTop: "1.5rem", fontSize: "0.8rem", color: "#64748b" }}>
          Backend 11024 - Frontend 11025 - MCP /mcp
        </footer>
      </div>
    </div>
  );
}
