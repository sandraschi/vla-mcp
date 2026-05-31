# vla-mcp — Assessment & TODO

**Reviewed:** 2026-05-31 (Opus 4.8 initial audit)  
**Last updated:** 2026-05-31 (v0.3.0 — Composer)  
**Version:** 0.3.0

## Verdict

The repo graduated from “honest scaffold” to **runnable loop**. `vla_pipeline` executes fleet → ingest → numpy export → DMuon dry_run with provenance. Original Opus audit items #1–#8, #11–#16 are closed; #9–#10 remain polish.

---

## Original audit — status

| # | Sev | Area | Status |
|---|-----|------|--------|
| 1 | Critical | prefab.py | ✅ v0.2.1 — PrefabApp(view=Card) |
| 2 | High | dmuon_runner job_status JSON | ✅ v0.2.1 — drain tasks excluded |
| 3 | Medium | hf_weights slug mismatch | ✅ v0.2.1 — unified `_slug()` |
| 4 | Medium | export_numpy_shard honesty | ✅ v0.2.1 — copy/write arrays |
| 5 | Medium | REST + CORS | ✅ v0.2.1 — origin lock + X-VLA-Confirm |
| 6 | Medium | dataset index atomicity | ✅ v0.2.1 — tmp + os.replace + lock |
| 7 | Medium | fleet proxies unconditional | ✅ v0.2.1 — VLA_MOUNT_FLEET_PROXIES |
| 8 | Medium | peer names/ports | ✅ v0.2.1 — yahboom-mcp:10892 |
| 9 | Low | HTTP stack at stdio import | ⬜ open |
| 10 | Low | StaticFiles prod mount | ⬜ open |
| 11 | Low | agentic over REST | ✅ v0.2.1 — blocked 403 |
| 12 | Low | version drift | ✅ v0.2.1 / v0.3.0 aligned |
| 13 | Low | hf local_dir_use_symlinks | ✅ v0.2.1 — removed |
| 14 | Low | sequential fleet probes | ✅ v0.2.1 — asyncio.gather |
| 15 | Low | in-memory jobs only | ✅ v0.3.0 — logs/jobs.json |
| 16 | Low | test gaps | ✅ v0.2.1 + v0.3.0 — pipeline tests added |

### PRD requirements

| REQ | Topic | Status |
|-----|-------|--------|
| REQ-06 | Prefab status card | ✅ v0.2.1 |
| REQ-09 | numpy shard writer | ✅ v0.2.1 |
| REQ-10 | X-VLA PEFT edge path | ✅ v0.2.1 |
| REQ-14 | E2E pipeline | ✅ v0.3.0 |

---

## Shipped in v0.3.0

- [x] **`vla_pipeline`** — `describe`, `run`, `last_run`
- [x] Simulated + live fleet modes (worldlabs `health`, yahboom `read_imu`)
- [x] Provenance JSON under `logs/pipeline/run_*.json`
- [x] Job persistence `logs/jobs.json`
- [x] Log tail REST + SSE on Training page
- [x] `introspect_train_args` + dry_run without upstream
- [x] Dashboard `/pipeline` route
- [x] `tests/test_pipeline.py` (28 tests total)

---

## Remaining (low / polish)

- [ ] **#9** Lazy HTTP app init for stdio-only clients (`server.py`)
- [ ] **#10** Mount `webapp/dist` via StaticFiles for single-port prod
- [ ] **stop_job** — document Windows-only; add POSIX kill path if Linux runner needed

---

## Ideas (next — for Opus / v0.4+)

### High value

- [ ] **Full live motion loop** — yahboom `forward` + `read_imu` trajectory → real action `.npy`; attach worldlabs `list_worlds` world_id in episode metadata
- [ ] **Pipeline pytest marker `@pytest.mark.live`** — skips unless `VLA_LIVE_FLEET=1`; catches peer contract drift
- [ ] **DMuon log viewer SSE in webapp** — wire Training page to `/log/stream` instead of poll-only

### Data path

- [ ] zarr / LanceDB shard format for multiview (ARCHITECTURE Phase 2)
- [ ] Event segmenter thresholds as tool args + calibration from labelled sample
- [ ] `ingest_episode` video path copy into dataset root (provenance bundle)

### Fleet / ops

- [ ] Register 11024/11025 in `mcp-central-docs/operations/WEBAPP_PORTS.md` if not done
- [ ] Provenance note per co-train → advanced-memory / memops (`tags: vla-mcp, dmuon, training`)
- [ ] `VLA_DMUON_LAUNCH_CMD` env override for non-standard upstream layouts

### UX

- [ ] Pipeline page: step progress UI (not raw JSON only)
- [ ] Dashboard card: last pipeline run status + shard name
- [ ] Weights page: one-click `x-vla` download for edge path

---

## Suggested order (v0.4)

1. `@pytest.mark.live` + full live motion loop (proves fleet contracts)
2. StaticFiles prod mount (#10) if single-port deploy matters
3. Lazy stdio init (#9)
4. zarr/LanceDB when multiview episodes exceed JSON comfort
