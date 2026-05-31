# Configuration

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VLA_WALL_X_ROOT` | — | Clone of github.com/X-Square-Robot/wall-x |
| `VLA_WALL_WM_ROOT` | falls back to wall-x | WALL-WM subtree |
| `VLA_DMUON_ROOT` | falls back to wall-x | DMuon training scripts |
| `VLA_CHECKPOINT` | — | Local weights file for infer |
| `VLA_DATASET_ROOT` | `%TEMP%\vla_mcp_data` | Episodes + exports + logs |
| `VLA_HF_CACHE_DIR` | `{dataset}/hf_cache` | Hugging Face download cache |
| `VLA_HF_WALL_OSS_REPO` | `X-Square-Robot/Wall-OSS-0.5` | HF repo id |
| `VLA_XVLA_ROOT` | — | Clone of github.com/THUDM/X-VLA |
| `VLA_XVLA_PEFT_ADAPTER` | — | Trained LoRA adapter directory |
| `VLA_XVLA_PEFT_DIR` | `{dataset}/peft/xvla` | PEFT config output |
| `VLA_XVLA_EDGE_DEVICE` | `cpu` | Edge infer device (Pi5 / Raspbot) |
| `VLA_HF_XVLA_REPO` | `THUDM/X-VLA` | HF repo id |
| `VLA_DEVICE` | `cuda:0` | Torch device string |
| `VLA_DMUON_VRAM_SHARDS` | `1` | DMuon matrix shard count |
| `VLA_API_PORT` | `11024` | Backend port |
| `VLA_FRONTEND_PORT` | `11025` | Vite port |
| `VLA_WORLDLABS_MCP_URL` | `http://127.0.0.1:10865` | worldlabs-mcp HTTP |
| `VLA_YAHBOOM_MCP_URL` | `http://127.0.0.1:10892` | yahboom-mcp HTTP (Raspbot bridge) |
| `VLA_ROBOTICS_MCP_URL` | alias → yahboom | Legacy env name |
| `VLA_AVATAR_MCP_URL` | `http://127.0.0.1:10793` | avatarops HTTP |
| `VLA_MCP_BRIDGE_URLS` | auto from peers | Comma MCP HTTP URLs for proxy |
| `VLA_MOUNT_FLEET_PROXIES` | `0` | Mount fleet MCP proxies (HTTP mode only) |
| `VLA_PREFAB_APPS` | `1` | Register Prefab cards |
| `MCP_TRANSPORT` | `stdio` | stdio or http |

## Claude Desktop

```json
{
  "mcpServers": {
    "vla-mcp": {
      "env": {
        "VLA_WALL_X_ROOT": "D:\\Dev\\repos\\external\\wall-x",
        "VLA_DATASET_ROOT": "D:\\Dev\\data\\vla_mcp"
      }
    }
  }
}
```

## Hugging Face

For gated models: `huggingface-cli login` before `vla_weights download`.

Override repo ids if X Square publishes under different names on HF.
