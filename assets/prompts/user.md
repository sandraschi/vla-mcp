# VLA-MCP User Guide

## Getting Started

VLA-MCP is a bridge for Vision-Language-Action stacks. It orchestrates the full pipeline from fleet simulation through event-joint data collection, dataset management, and DMuon co-training. Start by checking the VLA stack status.

### Checking Stack Status

```
vla_status()
```

Returns a comprehensive status snapshot: Wall-OSS health, WALL-WM health, DMuon health, X-VLA health, HuggingFace model cache status, dataset root path, dataset episode count, compute device, and current phase. Run this first to understand what is available.

### Getting Help

```
vla_help()
```

Returns the help index with available topics. For specific documentation:

```
vla_help(topic="fleet_integration")
vla_help(topic="tools")
vla_help(topic="configuration")
```

## Weight Management

The vla_weights tool manages model checkpoints from HuggingFace.

### Listing Available Models

```
vla_weights(operation="list_models")
```

Returns available models from HuggingFace including wall-oss-0.5 (VLA base) and wall-wm (world action model) variants. Each entry shows model ID, description, and available revisions.

### Checking Local Cache

```
vla_weights(operation="local_status", model_key="wall-oss-0.5")
```

Checks whether the model is cached locally, its version, file sizes, and integrity status. Models must be downloaded before use.

### Downloading Models

```
vla_weights(operation="download", model_key="wall-oss-0.5")
```

Downloads the model weights from HuggingFace to the local cache. For gated models:

```
vla_weights(operation="download", model_key="gated-model", revision="main")
```

Gated models require a HuggingFace token set in the environment. Download progress is streamed; large models may take several minutes.

## Wall-OSS VLA

The vla_wall tool manages Wall-OSS-0.5, a gradient-bridged Mixture of Transformers with flow matching for visuomotor control.

### Health Check

```
vla_wall(operation="health")
```

Returns GPU availability, model load status, and whether the Wall-OSS pipeline is ready.

### Preparing Inference

```
vla_wall(operation="infer_prepare", task_hint="pick_and_place")
```

Prepares the Wall-OSS model for inference on a specific task. Returns the model path, configuration, expected observation format (image dimensions, proprioceptive state), and action space definition.

### Preparing Fine-Tuning

```
vla_wall(operation="finetune_prepare", recipe="tabletop_manipulation")
```

Generates fine-tuning configuration based on a named recipe. Recipes define hyperparameters, data format, and training schedule.

### Edge Deployment

```
vla_wall(operation="edge_prepare", target="raspbot")
```

Prepares a lightweight, quantized version of Wall-OSS for deployment on edge devices (Raspbot, Boomy). Returns the optimized model path and deployment instructions.

### Listing Tasks

```
vla_wall(operation="list_tasks")
```

Lists all pre-trained tasks the model supports. Each task has a description, expected inputs, and output action space.

## X-VLA Edge PEFT

The vla_xvla tool manages X-VLA 0.9B, a smaller flow-matching VLA designed for edge agents with LoRA PEFT.

### Configuration Templates

```
vla_xvla(operation="peft_config_template", target="raspbot", rank=8)
```

Generates a LoRA PEFT configuration template for edge deployment. Rank controls the size of the adaptation matrices (higher = more expressive but larger).

### Preparing PEFT

```
vla_xvla(operation="peft_prepare", target="raspbot", rank=8, write=True)
```

Generates and writes the full PEFT configuration files. With write=True the files are persisted to disk; with write=False they are returned as a preview.

### Edge Inference

```
vla_xvla(operation="infer_prepare", target="raspbot", task_hint="grasp")
```

Prepares the edge agent for online inference. Sets up the model server, input pipeline, and action output format.

## World Action Model

The vla_world_model tool manages WALL-WM, a world action model using Wan as a prior.

### Health Check

```
vla_world_model(operation="health")
```

### Training Preparation

```
vla_world_model(operation="train_prepare", notes="Train on warehouse picking data")
```

Prepares the world model training configuration. Include notes about the dataset characteristics for automated config tuning.

### Prediction

```
vla_world_model(operation="predict_prepare", horizon_steps=32)
```

Prepares the world model for predicting future states. Horizon steps control how many timesteps ahead the model predicts.

### Event Vocabulary

```
vla_world_model(operation="event_vocab")
```

Returns the set of discrete event labels the world model can predict and condition on (e.g., "grasp", "place", "move", "idle").

## Dataset Management

The vla_dataset tool manages event-grounded trajectory data for training.

### Ingesting Episodes

```
vla_dataset(
    operation="ingest_episode",
    source="yahboom_001",
    events=["grasp", "lift", "move", "place"],
    video_paths=["/data/cam_0.mp4", "/data/cam_1.mp4"],
    action_path="/data/actions.npy"
)
```

Ingest a complete trajectory episode with event labels, multiview video, and action sequences. Events mark the boundaries between behavioral segments.

### Segmenting Telemetry

```
vla_dataset(
    operation="segment_telemetry",
    source="yahboom_002",
    telemetry=[
        {"timestamp": 0.0, "velocity": 0.0, "contact_force": 0.0},
        {"timestamp": 0.1, "velocity": 0.5, "contact_force": 0.0},
        {"timestamp": 1.0, "velocity": 0.0, "contact_force": 2.5}
    ],
    video_paths=["/data/episode_002.mp4"]
)
```

Segment raw telemetry (timestamped joint states, velocities, forces, contacts) into discrete event-labeled episodes. The segmentation uses WaLI-based event detection.

### Listing Episodes

```
vla_dataset(operation="list_episodes", limit=20, offset=0)
```

### Exporting for Training

```
vla_dataset(operation="export_numpy_shard", shard_name="train_001", episode_ids=["ep_001", "ep_002", "ep_003"])
```

Export episodes as numpy arrays -- the standard input format for DMuon training. Each shard contains observations, actions, event labels, and metadata.

## DMuon Training

The vla_training tool manages DMuon co-training, which jointly trains the VLA and world model.

### Checking Training Health

```
vla_training(operation="health")
```

### Preparing Training

```
vla_training(operation="co_train_prepare", dataset_shard="train_001")
```

### Launching Training

```
vla_training(operation="launch_co_train", dataset_shard="train_001", confirm=True, dry_run=True)
```

The confirm=True is required -- this is a safety guard against accidental GPU job launches. Use dry_run=True first to preview the command without executing.

When ready:

```
vla_training(operation="launch_co_train", dataset_shard="train_001", confirm=True)
```

### Monitoring Training

```
vla_training(operation="job_status", job_id="job_123")
vla_training(operation="job_log", job_id="job_123", log_offset=0)
```

### Stopping Training

```
vla_training(operation="stop_job", job_id="job_123")
```

## Pipeline

The vla_pipeline tool runs the end-to-end VLA pipeline.

### Running the Full Pipeline

```
vla_pipeline(operation="run", live=True, room_style="cluttered_indoor")
```

This runs the complete pipeline: fleet simulation generates robot trajectories, which are ingested and segmented, exported as numpy shards, and optionally run through a DMuon dry-run. Parameters control whether to use live data or simulation, the room style for world generation, and which boomy agents to include.

### Getting Pipeline Info

```
vla_pipeline(operation="describe")
vla_pipeline(operation="last_run")
```

## Fleet Operations

The vla_fleet tool manages peer MCP server connections.

### Checking Peers

```
vla_fleet(operation="list_peers")
vla_fleet(operation="bridge_status")
```

### Calling Peer Tools

```
vla_fleet(operation="call_peer", peer="worldlabs-mcp", tool_name="generate_world_from_text", arguments={"text_prompt": "A cluttered indoor room"})
```

This bridges to other MCP servers in the fleet for coordinated operations.

## World Generation

The vla_world tool generates 3D rooms for simulation.

```
vla_world(operation="generate", prompt="A cluttered kitchen with countertops, cabinets, and scattered utensils")
```

This bridges to worldlabs-mcp to create a navigable 3D environment for robot simulation. The returned viewer URL opens in a browser for visual inspection.

## Agentic Workflows

For complex multi-step tasks, use the agentic workflow tool:

```
vla_agentic_workflow(goal="Run a complete pipeline: download weights, simulate episodes, segment data, export shards, and launch co-training")
```

This uses LLM sampling to plan and describe the sequence of tool calls needed.

## Event-Joint Segmenter Deep Dive

The event segmenter identifies behavioral transition boundaries from continuous telemetry. It uses a WaLI-inspired algorithm that detects changes in: joint velocity profiles (zero-crossings, acceleration peaks), contact states (gripper open/close transitions, force threshold crossings), spatial relationships (end-effector entering/leaving regions), and task-specific signals (barcode markers, completion flags). Each segment receives a label from the event vocabulary (e.g., "reach", "grasp", "lift", "place", "release", "retract"). The segmenter also computes segment statistics: duration, peak velocity, contact force profile, and gripper trajectory.

For effective segmentation, provide telemetry with the following fields per timestamp: timestamp_seconds (float), joint_positions (list of 6-7 DOF angles in radians), joint_velocities (list of angular velocities), gripper_state (float, 0.0 closed to 1.0 open), contact_force (float, Newtons), end_effector_pose (list of 7: xyz + quaternion), and any task-specific sensor readings. The segmenter first normalizes timestamps to consistent intervals, then applies the segmentation algorithm, and finally validates that each segment meets minimum duration constraints.

## Multiview Validation

When collecting episodes with multiple camera views, validate synchronization before ingestion:

```
vla_dataset(
    operation="validate_multiview",
    video_paths=["/data/cam_0.mp4", "/data/cam_1.mp4", "/data/cam_3.mp4"]
)
```

This checks: frame counts match across all views, timestamps are within tolerance, codec compatibility for each file, and resolution consistency. If validation fails, check that all cameras started recording simultaneously and have the same frame rate.

## Pipeline Stages in Detail

The pipeline runner executes stages sequentially with checkpoint-and-resume capability:

Stage 1 -- Scenario: Generate a fleet scenario brief describing the robot configuration, room layout, and task definition. Parameterized by room_style (cluttered_indoor, kitchen, warehouse, office), include_failures (add failure-mode episodes for robustness training), and agents (list of robot types).

Stage 2 -- Worldgen: Bridge to worldlabs-mcp to generate a 3D room matching the scenario. The room serves as the simulation environment. If worldlabs-mcp is unreachable and fallback_simulate=True, a simulated room is used.

Stage 3 -- Simulation: Bridge to yahboom-mcp for robot fleet simulation. Robots execute tasks in the generated room, collecting egocentric video, proprioception, and action trajectories. Telemetry is streamed back in real-time.

Stage 4 -- Segmentation: Raw telemetry is segmented into event-labeled episodes using the event segmenter. Events are validated against the training requirements.

Stage 5 -- Ingestion: Episodes are ingested into the dataset store with video paths, action files, and metadata.

Stage 6 -- Export: Selected episodes are exported as numpy shards for DMuon training. Including both successful and failure episodes for robustness.

Stage 7 -- Training Preview: Optionally runs a DMuon dry-run to verify the training pipeline before committing to a full training job.

## Multi-Target Fleet Management

When multiple edge agents are involved, manage them through the fleet bridge:

```
vla_fleet(operation="scenario_brief", room_style="warehouse", agents=["raspbot", "boomy"])
vla_fleet(operation="call_peer", peer="yahboom-mcp", tool_name="yahboom_simulate",
    arguments={"episodes": 10, "agents": ["raspbot", "boomy"]})
```

Each agent type (Raspbot = wheeled mobile manipulator, Boomy = legged locomotion) has different capabilities and data formats. The scenario brief accounts for these differences and configures the simulation accordingly.

## Advanced Training Configuration

The DMuon config template includes the following parameter categories:

Data: dataset_path, train_ratio (default 0.9), batch_size (default 64), sequence_length (default 32), shuffle_buffer_size, num_workers, augmentation_pipeline (random crop, color jitter, rotation, Gaussian noise).

Model: policy_encoder (ViT variant), world_model_encoder, latent_dim (default 256), num_transformer_layers (default 6), num_attention_heads (default 8), dropout_rate (default 0.1), activation_function (geglu, relu, gelu).

Training: learning_rate (default 3e-4), optimizer (adamw, adam), weight_decay (default 0.01), gradient_clip_norm (default 1.0), warmup_steps (default 1000), total_steps, checkpoint_interval (default 5000), eval_interval (default 1000), log_interval (default 100), mixed_precision (fp16, bf16, fp32), gradient_accumulation_steps.

Loss: policy_loss_weight (default 1.0), world_model_loss_weight (default 0.5), event_prediction_loss_weight (default 0.2), latent_alignment_weight (default 0.1).

## Fleet Integration Details

VLA-MCP integrates with multiple fleet peers:

yahboom-mcp: Robot fleet simulation -- telemetry collection, episode generation, joint-state streaming, and multi-agent coordination. Provides the simulation environment for VLA data collection.

worldlabs-mcp: 3D room generation -- creates navigable environments from text prompts for simulation scenarios. Rooms are generated via Marble API with collision meshes for physics.

avatarops: Event-joint data pipeline -- telemetry filtering, event boundary detection, and endpoint data export. Connects raw robot telemetry to the event segmentation pipeline.

aiwatcher (via integrations/aiwatcher.py): Fleet event monitoring -- sends pipeline status, training completion, and error events to the central monitoring system.

## Web Dashboard

The VLA-MCP web dashboard (port 11025) provides: pipeline status visualization, episode browser and inspection, training job monitoring with live logs, weight cache management UI, fleet peer status, and REST API access to all tools. Access via http://localhost:11025 when the webapp is running. The dashboard auto-refreshes for live training monitoring.

## Troubleshooting

**Weights download fails:** Check internet connectivity to HuggingFace. For gated models, ensure HF_TOKEN is set. The download may be interrupted -- retry, as downloads resume from the last checkpoint.

**Training job fails to launch:** Verify GPU availability with vla_status(). Check that the dataset shard exists and has valid episodes. Ensure confirm=True is passed.

**Pipeline run fails at simulation stage:** The yahboom-mcp peer may be unreachable. Set fallback_simulate=True to bypass simulation and use pre-recorded data.

**Segmentation produces no events:** The telemetry may be too uniform or noisy. Check that velocity and force data have sufficient variation. Adjust segmentation thresholds if configurable.

**Export shard is empty:** The selected episode IDs may have been filtered by the limit/offset. Verify episodes exist with list_episodes and check their IDs.

## Event Segmentation Parameters

The `segment` operation in vla_events accepts telemetry samples with configurable fields. Each sample should include: timestamp_seconds (float, required), joint_positions (list of 6-7 DOF angles), joint_velocities (list of angular velocities), joint_efforts (list of torque/force readings), end_effector_pose (list of 7 values: xyz position and xyzw quaternion), gripper_state (float, 0.0 fully closed to 1.0 fully open), contact_force (float, in Newtons), and task_specific (dict of any additional sensor readings). The segmenter processes samples in chronological order, detecting event boundaries using velocity zero-crossings, force threshold crossings, gripper state transitions, and spatial region entries/exits. Each detected segment is labeled from the event vocabulary and assigned start/end timestamps. The quality of segmentation depends on sensor sampling rate and signal-to-noise ratio - higher rate telemetry (50+ Hz) produces more accurate event boundaries.

## Training Configuration Templates

The DMuon config template generated by `config_template` includes placeholder values for all training parameters. Key fields to customize: dataset_path (point to your exported shard directory), learning_rate (3e-4 for AdamW, 1e-4 for fine-tuning), batch_size (64 for GPU with 24GB+, 32 for 16GB, 16 for 8GB), sequence_length (32 for most tasks, 64 for long-horizon), num_epochs (100-1000 depending on dataset size), and mixed_precision (bf16 for A100/RTX 4090, fp16 for older GPUs). The introspect_train_args tool shows all available arguments from the underlying training script, including framework-specific options.

## Running the Pipeline with Custom Parameters

The vla_pipeline tool accepts fine-grained control over each stage. The `live` parameter controls whether to use live fleet simulation or pre-recorded data. The `shard_name` parameter specifies the output shard name. The `include_failures` parameter includes failure-mode episodes in the export for robustness training. The `room_style` parameter controls the generated environment (cluttered_indoor, kitchen, warehouse, office, empty_room). The `fallback_simulate` parameter enables simulation-based data when live fleet data is unavailable. The `boomy_demo` parameter selects specific locomotion patterns (walk, trot, turn, navigate). The `generate_world` parameter controls whether to generate a new 3D world for simulation or use an existing one.

## Distributed Training Considerations

DMuon co-training on multiple GPUs requires additional configuration. The framework supports: data parallelism (same model replicated across GPUs with synchronized gradients), model parallelism (model layers split across GPUs), and FSDP (Fully Sharded Data Parallelism for large models). Configure via extra_args: "--num_gpus 4 --strategy fsdp". Multi-GPU training requires NCCL backend and appropriate GPU interconnect (NVLink, PCIe). Monitor GPU utilization during training to verify all GPUs are being utilized. Uneven GPU utilization may indicate data loading bottlenecks or model parallelism inefficiencies.

## REST API Usage Examples

The VLA-MCP REST API is accessible at http://localhost:11024 (backend) and http://localhost:11025 (frontend dashboard). Key REST endpoints for automation:

```
GET /api/status           -> Full VLA stack status JSON
GET /api/pipeline/liveness -> Pipeline health check
POST /api/pipeline/run     -> Trigger pipeline with JSON body
GET /api/episodes          -> List episodes with pagination
GET /api/jobs              -> List training jobs
GET /api/job/log?job_id=X  -> Training job log
```

REST responses mirror MCP tool outputs with success/data/error structure. The REST API is useful for programmatic access from scripts and CI/CD pipelines that cannot use the MCP protocol.

## Multi-Target Scenario Configuration

When running fleet simulations with multiple robot types, configure each agent separately. The scenario brief accepts an agents parameter listing which robot types participate. Each robot type has different capabilities and data formats: Raspbot is a differential-drive wheeled robot with a 6-DOF arm and parallel gripper, Boomy is a 4-DOF legged robot with a simple gripper. Both produce egocentric RGB video, joint state telemetry, and action trajectories. The pipeline handles both data formats and unifies them during export for DMuon training.

## Common Troubleshooting Patterns

When a pipeline run fails, use this troubleshooting checklist: check vla_status for overall stack health, check api_pipeline_liveness for component-level health, verify worldlabs-mcp is reachable for world generation, verify yahboom-mcp is reachable for fleet simulation, check disk space on the dataset root path, verify HuggingFace token is set for gated model downloads, check GPU availability with nvidia-smi, look for error messages in the specific stage's output logs, verify that episode telemetry files are accessible and not corrupted, and check that exported shard files have the expected format and content.

## Edge Agent Preparation Workflow

To deploy Wall-OSS or X-VLA to an edge agent: use vla_wall or vla_xvla with the appropriate edge_prepare operation, specify the target device (raspbot or boomy), the manager generates a deployment bundle containing the quantized model, configuration files, an inference script template, and deployment instructions. The bundle is staged in the configured output directory for manual transfer to the edge device. Edge deployment requires the target device to have the appropriate inference runtime installed (ONNX Runtime, TensorRT, or PyTorch Mobile depending on configuration).

## Dataset Shard Format

Exported numpy shards have a standardized format for DMuon training. Each shard is a directory containing: observations.npy (uint8 array of shape [N, T, C, H, W] where N is number of episodes, T is timesteps, C is channels, H and W are image dimensions), actions.npy (float32 array of shape [N, T-1, D] where D is action dimension), events.npy (int32 array of shape [N, T-1] with event label indices), metadata.json (dict with episode_ids, source names, action_dim, observation_dim, event_vocabulary, and capture parameters), and timestamps.npy (float32 array of shape [N, T] with timestamps). The shard format supports variable-length episodes by padding to the maximum T in the shard and providing a mask.

## World Generation Integration

The vla_world tool generates 3D rooms through worldlabs-mcp. The generated room serves as the simulation environment for robot data collection. Important notes: the generated world must have a collision mesh (GLB) for physics simulation, the room should match the task domain (kitchen for manipulation, warehouse for navigation), and the prompt should specify floor plan, furniture, lighting, and clutter level. Room generation takes 1-3 minutes for marble-1.1. The fleet bridge automatically detects worldlabs-mcp availability and falls back to simulation if unavailable.

## Inference and Edge Deployment

After training, deploy the VLA policy to edge agents. The edge_prepare operations generate: quantized model weights (FP16 or INT8 for edge inference), optimized model graph (TorchScript or ONNX), inference script template (Python for Raspbot, C++ for Boomy), configuration file (model path, input normalization, action scaling), and deployment checklist (dependencies, hardware requirements, installation steps). Edge deployment bundle size varies from 50MB (X-VLA with INT8) to 500MB (Wall-OSS with FP16). Edge inference latency on typical hardware (Raspberry Pi 4, Jetson Nano): 30-100ms for X-VLA, 100-500ms for Wall-OSS.

## Pipeline Error Recovery

When pipeline stages fail, the pipeline runner reports which stage failed and why. Recovery strategies: retry the pipeline with fallback_simulate=True if the fleet simulation is unavailable, regenerate the world with a different prompt if worldlabs generation fails, manually ingest telemetry files if the dataset ingestion stage finds corrupt files, adjust segmentation parameters if event boundaries are not detected, and verify export directory permissions if shard export fails. Failed pipeline runs preserve partial results up to the failure point for manual inspection.

## Episode Replay and Visualization

Ingested episodes can be replayed for inspection. Each episode contains multiview video files and synchronized action trajectories. Replay shows: camera views with overlaid action commands, event boundaries highlighted, gripper state indicated, and task success/failure markers. Use this for: verifying that segmentation correctly identified event boundaries, checking that action trajectories are smooth and complete, confirming that multiview videos are synchronized, and debugging telemetry collection issues before training. Episode replay is available through the web dashboard at port 11025.

## Configuration Reference

Key configuration parameters and their effects: dataset_root (where episodes are stored, affects disk space), cache_root (where model weights are cached, affects startup time), device (cuda or cpu, affects training speed and availability), mount_fleet_proxies (enables peer MCP bridging, affects tool availability), bridge_urls (peer server URLs, affects fleet operations), worldlabs_gen_tool (world generation tool name, affects which worldlabs tool is called), default_wall_model (default Wall-OSS model for training), frontend_port (web dashboard port), and log_level (logging verbosity for debugging). Configuration is loaded from environment variables or default values. Logging output goes to stderr for MCP compatibility.

## Troubleshooting with the Pipeline Liveness Check

The api_pipeline_liveness endpoint provides real-time diagnostics for the entire VLA pipeline. It checks: wall runner (Wall-OSS health), world model runner (WALL-WM health), dmuon runner (DMuon availability), dataset store (filesystem accessibility), fleet bridge peers (worldlabs-mcp, yahboom-mcp connectivity), and disk space on dataset root. Each component is reported as healthy or degraded with a diagnostic message. Use this before starting a pipeline run to ensure all dependencies are available. If a component is degraded, the diagnostic message explains the issue and suggests recovery steps.

## HuggingFace Weight Management

The vla_weights tool manages model checkpoints stored on HuggingFace. Models are identified by their HuggingFace model ID: sandraschi/wall-oss-0.5 for the base VLA policy, sandraschi/wall-wm for the world action model, and sandraschi/wall-oss-0.5-peft for the LoRA adapter. The download operation streams model weights to the local cache directory. The local_status operation reports cache state including file sizes, SHA256 checksums, and version information. Models are stored in the cache directory with subdirectories per model_id and version. The cache is shared across sessions and persists until manually cleared.

## Pipeline Stage Configuration

Each pipeline stage has configurable parameters that affect behavior. The describe operation shows current configuration. Key parameters: live (boolean, use live fleet simulation vs pre-recorded data), shard_name (name for the exported dataset shard), include_failures (include failure-mode episodes in export), room_style (environment type for simulation), fallback_simulate (use simulation when fleet unavailable), boomy_demo (specific locomotion pattern for Boomy agents), boomy_pattern (movement pattern variant), generate_world (create new world vs use existing). The pipeline runner applies these parameters across all stages and reports per-stage results.

## Fleet Bridge Connection Details

The fleet bridge connects to peer MCP servers over HTTP. Each peer exposes an /mcp endpoint for tool calls. Connection parameters: timeout (default 30 seconds, configurable), retry (3 attempts with backoff), authentication (none for localhost, configurable for remote), and health check interval (automatic on each call). When a peer is unreachable, the bridge returns a clear error with the peer name, URL attempted, and failure reason. Bridge status aggregates health across all configured peers for a single overview.

## Dataset Export and Shard Management

Dataset export creates shards in a structured directory format. Each shard contains: a metadata file describing the episode sources, numpy arrays for observations (preprocessed video frames), actions (normalized action vectors), events (event label indices), and timestamps. Shard naming follows the pattern {shard_name}_shard_{index}.npy. Export supports selective inclusion (specific episode IDs) and exclusion (by source or event type). Numpy shards can be inspected with standard numpy tools. Memory-mapped reading is supported for large shards.

## Training and Inference Hardware Requirements

DMuon co-training requires: NVIDIA GPU with at least 16GB VRAM (RTX 4080/4090 or A4000+), CUDA 12+ and compatible PyTorch, 100GB+ free disk space for datasets and checkpoints, and 32GB+ system RAM. Wall-OSS inference requires: GPU with 8GB+ VRAM for FP16, or 16GB+ for FP32. X-VLA edge inference can run on: Raspberry Pi 4/5 with 4GB+ RAM (CPU inference, ~500ms per step), NVIDIA Jetson Nano/Orin (GPU inference, ~50ms per step), or any Linux system with PyTorch installed. Edge deployment size: X-VLA with INT8 quantization is ~100MB, Wall-OSS with FP16 is ~500MB.

## REST API Authentication

The VLA-MCP REST API does not enforce authentication by default for localhost development. For production deployments: use a reverse proxy (nginx, Traefik) with authentication, restrict API access to specific IP ranges, implement API key-based authentication at the proxy level, and use HTTPS for encrypted transport. The REST API exposes all VLA-MCP tools, so appropriate access controls should be implemented for production use. The web dashboard respects the same access controls as the REST API.

## Model Evaluation and Validation

After training, evaluate model performance using validation episodes. The training pipeline reports: policy loss (how well the VLA predicts actions), world model loss (how accurately the world model predicts future observations), event prediction accuracy (how well events are classified), and task success rate (end-to-end task completion). Compare against baseline: pre-trained Wall-OSS performance, previous training runs, and task-specific success thresholds. Use the validation results to decide whether to continue training, adjust hyperparameters, or deploy the model.

## Environment Variables Quick Reference

All VLA-MCP configuration is done through environment variables. Set these before starting the server: VLA_MCP_DATASET_ROOT (path to episode storage), VLA_MCP_CACHE_ROOT (path to model cache), VLA_MCP_DEVICE (cuda or cpu), VLA_MCP_FRONTEND_PORT (web dashboard port), VLA_MCP_LOG_LEVEL (debug/info/warning/error), VLA_MCP_MOUNT_FLEET_PROXIES (1 or 0), VLA_MCP_BRIDGE_URLS (peer server URLs), VLA_MCP_WORLDLABS_GEN_TOOL and VLA_MCP_WORLDLABS_GEN_ARG (world generation configuration), and HF_TOKEN (HuggingFace authentication for gated models). Configuration loads on server startup.

## Integration with External Monitoring

VLA-MCP integrates with the fleet monitoring system via the aiwatcher module. Pipeline health events are posted to the central aiwatcher instance for fleet-wide observability. Events include: pipeline start/completion/failure, training job launch/completion, dataset ingestion completion, and weight download status. The fleet bridge status is also monitored for peer availability. Configure VLA_MCP_AIWATCHER_URL to enable integration. Monitoring events help track fleet-wide VLA pipeline health and identify systemic issues.

## Performance Optimization Tips

For faster pipeline runs: pre-download model weights before running the pipeline, use pre-generated worlds (set generate_world=False), use fallback_simulate=True when fleet simulation is not needed, reduce video resolution for telemetry collection, use smaller episode counts for pipeline testing, increase parallel processing in the dataset export step, and use SSD storage for dataset root and cache directories. For faster training: use mixed precision (bf16), increase batch size to GPU capacity, reduce sequence length if task permits, and use gradient accumulation for effective batch size scaling.

## Multi-Agent Fleet Coordination

When coordinating multiple robot agents in the same simulation, the fleet bridge manages: agent registration (each agent connects with its capabilities), task assignment (agents are assigned subtasks based on their capabilities), data collection (each agent streams telemetry independently), conflict resolution (agents avoid collisions and resource contention), and data aggregation (episodes from all agents are combined for training). The pipeline handles multi-agent data by merging per-agent episodes into a unified training shard. Multi-agent scenarios require careful scenario design to avoid task conflicts.

## Configuration File Editing

VLA-MCP configuration can be customized by setting environment variables before server startup. For persistent configuration, create a .env file in the repo root with key=value pairs. The server loads .env automatically. Configuration takes effect on next server start. Key settings for customization: dataset_root (change if using a different storage location), device (force CPU if GPU is unavailable), mount_fleet_proxies (disable if running standalone), and log_level (set to debug for detailed diagnostics). Incorrect configuration may cause startup errors with clear messages.

## Fleet Scenario Configuration Details

The scenario brief contains: room_style (the 3D environment type), agents (list of robot types with their capabilities), task_definition (description of what the robots should do), episode_count (how many episodes to collect), include_failures (whether to introduce failure modes), and collection_parameters (telemetry rate, video resolution, action recording method). The scenario brief is generated by the fleet bridge based on current fleet configuration and passed to the simulation tool. It ensures consistent data collection across agents.

## Pipeline Stage Dependencies

Pipeline stages have dependencies on external systems. The world generation stage requires worldlabs-mcp to be reachable with valid API credits. The simulation stage requires yahboom-mcp to be reachable. The segmentation and ingestion stages require the dataset store to have disk space. The export stage requires write permissions on the export directory. The training stage requires GPU availability. Check each dependency with the appropriate status tool before starting the pipeline. The pipeline runner checks dependencies at the start of each stage and reports failures with clear dependency descriptions.

## Data Synchronization for Multi-Camera Episodes

When collecting episodes with multiple cameras, ensure all cameras are synchronized. The validate_multiview operation checks: frame counts match across views, timestamps are aligned within tolerance, resolutions are consistent, and codecs are compatible. Post-processing can fix minor synchronization issues: trim excess frames from the longer view, interpolate timestamps for millisecond alignment, and crop or resize mismatched resolutions. Proper synchronization is critical for training models that use multiview observations.

## Sample Workflow: Complete Training Run

1. `vla_status()` -- Verify the stack is healthy
2. `vla_weights(operation="download", model_key="wall-oss-0.5")` -- Ensure model weights are cached
3. `vla_world(operation="generate", prompt="...")` -- Create a simulation environment
4. `vla_dataset(operation="segment_telemetry", source="...", telemetry=[...])` -- Ingest robot data
5. `vla_dataset(operation="export_numpy_shard", shard_name="train_001", episode_ids=[...])` -- Prepare training data
6. `vla_training(operation="co_train_prepare", dataset_shard="train_001")` -- Configure training
7. `vla_training(operation="launch_co_train", dataset_shard="train_001", confirm=True)` -- Launch
8. `vla_training(operation="job_status", job_id="job_123")` -- Monitor progress
