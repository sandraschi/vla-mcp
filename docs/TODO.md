# vla-mcp — Assessment & TODO (round 3)

**Updated:** 2026-05-31
**Version:** 0.3.0
**Verified against:** FastMCP 3.3.1, prefab-ui 0.20.1 (clean-venv introspection); X-VLA upstream checked on the web.

## Where it stands

The scaffold is solid and the round-1 and round-2 issues are closed. The demoable spine is in place: an end-to-end `vla_pipeline` (simulated + live, provenance-logged), an event-joint timeline on the dashboard, in-chat Prefab status and run cards, a worldlabs 3D-room hook, persistent jobs with SSE log streaming, and a one-command `-Demo` launcher. X-VLA is correctly attributed (2toinf).

What's left is not bug-fixing — it's (a) confirming the live peer tool names so a real-robot run works at the venue, (b) syncing the manifest/docs to the actual tool surface, and (c) the headline demo upgrades (live Raspbot, LeRobot export). Estimates below are AI-assisted day-scale.

## Resolved (rounds 1–3)

All of: prefab card dead-import + empty-render; `job_status` Task-serialization crash; HF slug mismatch; faked `arrays_written`; open REST control + `CORS *`; non-atomic `index.json`; proxies mounted in stdio; wrong peer name (`robotics-mcp`→`yahboom-mcp`); agentic-over-REST; deprecated `local_dir_use_symlinks`; sequential peer probes; in-memory jobs; **X-VLA attributed to THUDM/Tsinghua → corrected to 2toinf**; Prefab card rendering empty (`view=Card`→`view=card`). Plus implemented: train-arg introspection, X-VLA edge path, e2e pipeline, SSE log streaming, event-joint timeline, demo mode, pipeline run-card, worldlabs hook.

## This session (round 3)

- X-VLA attribution corrected everywhere (`config.py`, `xvla_adapter.py`, `hf_weights.py`, `server.py`, `.env.example`, `CONFIGURATION.md`); `*.bak` added to `.gitignore`.
- Prefab status card now captures its built tree (`with Card(...) as card`).
- Event-joint timeline: segments threaded through `segment_and_ingest` → `vla_pipeline run` payload → `EventTimeline.tsx` (SVG, color-per-event) on the Pipeline page.
- Demo mode: `start.ps1 -Demo` (+ `just demo`) seeds runs and opens `/pipeline`.
- Pipeline run-card: `show_pipeline_run_card` (Metric tiles + Mermaid loop + DMuon command).
- worldlabs hook: `vla_world` tool + `FleetBridge.generate_world`/`find_viewer_url`, env-configurable peer tool/arg, "Generate 3D room" panel on the Pipeline page.

## Open items

| # | Sev | Area | One-liner |
|---|-----|------|-----------|
| NEW-C | Med (live demo) | pipeline_runner.py, xvla_adapter.py | Live peer tool names still partly guessed; verify against real `yahboom-mcp`/`worldlabs-mcp` |
| NEW-D | Low–Med | manifest.json, README, TOOLS.md, PRD | Tool surface is now 12 tools + 2 cards; `manifest.json` still lists 9 at v0.2.0 |
| NEW-E | Low | dmuon_runner.py | `introspect_train_args` runs `--help` on every prepare/launch; cache per script |
| 9 | Low | server.py | Full FastAPI/HTTP app built at import even for stdio |
| 10 | Low | web.py | No `StaticFiles` mount — built frontend only served by `vite dev` |

### NEW-C — confirm live peer tool names (do before a live run)

Worldlabs is now env-configurable (`VLA_WORLDLABS_GEN_TOOL` / `VLA_WORLDLABS_GEN_ARG`) — set them to whatever `worldlabs-mcp` actually exposes and `vla_world generate` works with no code change. Still hardcoded: the pipeline's yahboom calls (`yahboom_tool` with `health_check`/`read_imu`) and `xvla_adapter.edge_prepare`'s `robotics_system`. Hit each peer's `/api/v1/tools`, reconcile the names, and make the pipeline and `edge_prepare` agree. The simulated path doesn't depend on this; only a *live* fleet run does. **~0.5 day.**

### NEW-D — sync manifest/docs to the real surface

Tools are now `vla_status, vla_weights, vla_wall, vla_xvla, vla_pipeline, vla_world_model, vla_dataset, vla_events, vla_training, vla_fleet, vla_world, vla_agentic_workflow` (12) plus Prefab cards `show_vla_status_card`, `show_pipeline_run_card`. `manifest.json` still lists the original 9 at v0.2.0 and is what `/.well-known/mcp/manifest.json` serves; `TOOLS.md` lacks `vla_world`; PRD REQ rows can mostly flip to Done. Update manifest tools+version, add `vla_world` to TOOLS.md, refresh README features. **~0.5 day.**

NEW-E / #9 / #10 are low priority; the launcher runs `vite dev` + backend so the dashboard works for a live demo as-is.

## Demo — what runs now, what's next

**Runs today (one command):** `just demo` → seeds pipeline runs → opens `/pipeline` showing the event-joint timeline, a 3D-room generator, and live run output. In Claude Desktop, `vla_pipeline(operation='run')` then `show_pipeline_run_card` gives the in-chat visual; `vla_world(operation='generate', prompt=...)` returns a clickable Marble link once the worldlabs peer tool is set. Simulated path is CI-safe and needs no fleet peers — the safe default for a venue with flaky network.

**Headline upgrades (priority order):**

1. **Live Boomy/Raspbot run** (~1–2 days) — physical Raspbot does a short task ("find Benny"), telemetry streams via `call_peer`, segments live, ingests, exports, and the DMuon command appears with the SSE log tailing. Gated on NEW-C; always keep the simulated fallback as the safety net.
2. **worldlabs in the loop** (~0.5 day once NEW-C done) — generate the room at the *start* of a live pipeline run and stash `world_viewer_url` in the run payload + run-card, so the 3D world and the data loop are one story.
3. **LeRobot-native export** (~1–2 days) — X-VLA ships in LeRobot; exporting episodes in the LeRobot dataset layout lets the HF/LeRobot crowd actually fine-tune from your shards. Investigate the dataset schema first.

**Cheaper polish that lands well:**

- Parametric telemetry generator (task = pick_place/pour/stack, tunable slip/collision) so repeated demo runs look varied on the timeline (~0.5 day).
- "Proof it's real" panel surfacing the actual artifacts each run wrote — episode JSON, numpy shapes, manifest, provenance — with sizes (~0.5 day).
- `resource://vla/architecture` Mermaid + a canned `vla_agentic_workflow` demo goal so an operator types one line and the audience watches plan → execution (~0.5 day).

## Pre-demo checklist

1. `just lint` + `just test` green (not run from the review session — no Windows exec tool there). The launcher's import smoke test gates startup.
2. `tsc -b` in `webapp/` (the new `EventTimeline.tsx` and Pipeline-page edits weren't type-checked here).
3. Set `VLA_WORLDLABS_GEN_TOOL` / `VLA_WORLDLABS_GEN_ARG` to the real worldlabs-mcp tool; confirm yahboom tool names (NEW-C) if doing a live run.
4. Sync `manifest.json` (NEW-D) before pushing — it's the public/glama-facing surface.
5. `just demo` once on the demo machine to confirm seed + dashboard land clean.
