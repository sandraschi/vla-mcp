# vla-mcp — Assessment & TODO

**Reviewed:** 2026-05-31  
**Last updated:** 2026-05-31 (v0.2.1 adapter + audit fixes)  
**Version:** 0.2.1

## Verdict

Solid scaffold with honest upstream-not-configured responses. v0.2.1 adds **X-VLA PEFT edge adapter** (`vla_xvla`, `vla_wall edge_prepare`) and closes most audit items from the initial review.

---

## Fixed in v0.2.1

| # | Fix |
|---|-----|
| 1 | Prefab card rewritten for prefab-ui 0.20 (`PrefabApp(view=Card)`) |
| 2 | `job_status` excludes non-serializable drain tasks |
| 3 | Unified HF `_slug()` across list/download/local_status |
| 4 | `export_numpy_shard` copies `.npy` / writes inline `actions` |
| 5 | CORS restricted to frontend origin; mutating REST needs `X-VLA-Confirm: 1` |
| 6 | Atomic `index.json` writes + threading lock |
| 7 | Fleet proxies gated by `VLA_MOUNT_FLEET_PROXIES` (default off) |
| 8 | Default peer is `yahboom-mcp:10892` (not robotics-mcp) |
| 10 | REQ-10: `vla_xvla` + edge_prepare |
| 11 | `vla_agentic_workflow` blocked on generic REST route |
| 12 | justfile `VER` aligned to 0.2.1 |
| 13 | Removed deprecated `local_dir_use_symlinks` from HF download |
| 14 | Parallel fleet peer probes via `asyncio.gather` |
| 16 | Tests for slug, numpy export, job_status JSON, REST policy, xvla |

---

## Remaining (low / polish)

| # | Sev | Area | One-liner |
|---|-----|------|-----------|
| 9 | Low | server.py | Full FastAPI stack still built at import in stdio mode |
| 10 | Low | web.py | No StaticFiles mount for production `webapp/dist` |
| 15 | Low | dmuon_runner.py | Jobs in-memory only; not persisted across restart |
| — | Low | dmuon_runner.py | `stop_job` is Windows-only (`taskkill`) |

---

## Ideas (additive)

- Introspect upstream train args from `--help` instead of guessing CLI flags
- zarr / LanceDB shard format for large multiview datasets
- Event segmenter threshold calibration via tool args
- Live DMuon log SSE to Training dashboard
- End-to-end `--live` smoke: worldlabs → yahboom → ingest → export → dry_run
- Provenance note per co-train run (advanced-memory)

---

## Suggested next order

1. StaticFiles prod mount (#10) if single-port deploy matters
2. Persist job registry (#15) if Training dashboard is daily-use
3. Lazy HTTP app init (#9) for stdio-only clients
