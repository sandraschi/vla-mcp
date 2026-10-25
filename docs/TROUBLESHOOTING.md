# Troubleshooting

## Inbox page hangs on "Loading inbox"

**Cause:** dead fleet peers used to cost ~8.5s each (4 health paths x ~2s
Windows refused-loopback stalls), the fast last-run row waited behind the slow
liveness call, and `fetch` had no timeout. Fixed in round 7: per-peer 6s +
total 10s deadlines with partial results, aiwatcher check concurrent with peer
probes, 20s overall budget, 30s frontend fetch timeout, progressive Inbox
rendering (last run first, peer rows stream in).
**Fix:** pull latest; restart the backend. If it still spins past ~30s, check
for a black-holed peer IP (no RST) in `VLA_*_MCP_URL` and Retry.

## Stale backend squatting on :11024

**Cause:** a previous dev/e2e backend is still running old code (new endpoints 404).
**Fix:** find it (`Get-NetTCPConnection -LocalPort 11024`) and stop the process,
then start fresh. e2e boots its own backend; kill leftovers afterwards.

## Server does not appear in Claude Desktop

**Cause:** Invalid JSON in config.
**Fix:** Validate config; use double backslashes in Windows paths.

## vla_weights download fails

**Cause:** Wrong HF repo id or gated model without token.
**Fix:** Set `VLA_HF_WALL_OSS_REPO`; run `huggingface-cli login`.

## launch_co_train: no train script

**Cause:** wall-x clone missing or different layout.
**Fix:** Set `VLA_WALL_X_ROOT`; check upstream for `scripts/train_dmuon.py`.

## Fleet peers offline

**Cause:** worldlabs/robotics/avatar HTTP servers not running.
**Fix:** Start peer MCP on ports 10865, 10892, 10793.

## Backend ECONNREFUSED from Vite

**Cause:** Frontend started before uvicorn ready.
**Fix:** Use `webapp/start.ps1` (waits for `/api/v1/status`).

## DMuon job failed immediately

**Cause:** Upstream script args mismatch.
**Fix:** Use `dry_run=True` first; inspect log under `{VLA_DATASET_ROOT}/logs/`.

## MCP proxy warnings at startup

**Cause:** Peer `/mcp` not up when vla-mcp starts.
**Fix:** Start peers first or set `VLA_MCP_BRIDGE_URLS` to running servers only.
