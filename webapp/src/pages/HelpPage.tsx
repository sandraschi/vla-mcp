import { useEffect, useState } from "react";
import { AlertTriangle, Book, Box, Cpu, FlaskConical, HelpCircle, Server } from "lucide-react";
import { apiGet } from "../lib/api";

const TABS = [
	{
		id: "overview",
		label: "Overview",
		icon: Book,
		content: () => (
			<div className="space-y-6">
				<div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
					<div className="flex items-start gap-3">
						<AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
						<div>
							<h3 className="font-semibold text-amber-500">Alpha — Preemptive Infrastructure</h3>
							<p className="text-sm text-muted-foreground mt-1">
								vla-mcp is scaffolded for a future robotics training pipeline. No robots have been
								trained with it yet. It exists so the bridge is ready when someone collects
								teleoperation demos and runs DMuon co-training. Until then it's shelfware —
								not broken, just waiting for a robot to train.
							</p>
						</div>
					</div>
				</div>

				<div>
					<h3 className="text-lg font-bold mb-3">What is VLA?</h3>
					<p className="text-sm text-muted-foreground leading-relaxed">
						VLA (Vision-Language-Action) models take camera images + text commands and output
						robot motor commands. Think "pick up the red cube" → joint angle trajectory.
						This server bridges telemetry collection (multiview video, simulation state) to
						co-training jobs (DMuon optimizer on wall-x neural network weights).
					</p>
				</div>

				<div>
					<h3 className="text-lg font-bold mb-3">The intended pipeline</h3>
					<ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
						<li>Record teleoperation demos in MuJoCo sim or on a physical robot</li>
						<li>Segment telemetry into event joints (approach, contact, lift, recovery)</li>
						<li>Export as numpy shards for DMuon training</li>
						<li>Launch co-training job on wall-x Wall-OSS-0.5 or WALL-WM weights</li>
						<li>Deploy the trained policy back on the robot</li>
					</ol>
					<p className="text-xs text-muted-foreground mt-2 italic">
						Steps 1 and 5 are not implemented yet. This server handles steps 2—4.
					</p>
				</div>
			</div>
		),
	},
	{
		id: "fleet",
		label: "Fleet Integration",
		icon: Server,
		content: () => (
			<div className="space-y-4 text-sm text-muted-foreground">
				<p>Peers: <code className="text-violet-300">worldlabs :10865</code> | <code className="text-violet-300">robotics-mcp :10706</code> | <code className="text-violet-300">yahboom :10892</code> | <code className="text-violet-300">avatarops :10793</code></p>
				<p>Pipeline completions push to aiwatcher POST /api/fleet/ingest (source: vla-mcp-pipeline). Surfaces in VLA & Spatial AI bundle when VLA_AIWATCHER_BASE_URL=http://127.0.0.1:10946.</p>
				<p>MCP: <code className="text-violet-300">vla_help(topic="fleet_integration")</code> | <code className="text-violet-300">vla_fleet(operation="bridge_status")</code></p>
			</div>
		),
	},
	{
		id: "tools",
		label: "MCP Tools",
		icon: FlaskConical,
		content: () => (
			<div className="space-y-4 text-sm text-muted-foreground">
				<div className="grid gap-3">
					{[
						{ tool: "vla_weights", ops: "list_models, download, local_status", desc: "Hugging Face weight management for wall-x models" },
						{ tool: "vla_events", ops: "segment, vocab", desc: "Event-joint segmentation from telemetry" },
						{ tool: "vla_dataset", ops: "segment_telemetry, export_numpy_shard", desc: "Dataset registry and numpy export for DMuon" },
						{ tool: "vla_training", ops: "launch_co_train, job_status, stop_job", desc: "DMuon co-training job lifecycle" },
						{ tool: "vla_fleet", ops: "call_peer", desc: "Fleet peer bridge to worldlabs/robotics/avatar" },
						{ tool: "vla_pipeline", ops: "last_run", desc: "Pipeline liveness check" },
						{ tool: "vla_status", desc: "Scenario brief generation" },
						{ tool: "vla_help", desc: "Help system across all topics" },
					].map((t) => (
						<div key={t.tool} className="p-3 rounded-xl border border-border bg-card/40">
							<div className="font-mono text-sm text-violet-300">{t.tool}</div>
							{t.ops && <div className="text-xs text-muted-foreground mt-0.5">Ops: {t.ops}</div>}
							<div className="text-xs text-muted-foreground mt-0.5">{t.desc}</div>
						</div>
					))}
				</div>
			</div>
		),
	},
	{
		id: "config",
		label: "Configuration",
		icon: Cpu,
		content: () => (
			<div className="space-y-4 text-sm text-muted-foreground">
				<p>Key env vars:</p>
				<pre className="bg-black/40 rounded-xl p-4 text-xs font-mono text-green-400 overflow-x-auto">
{`VLA_DEVICE=cuda          # or cpu
VLA_HF_TOKEN=            # Hugging Face token for gated weights
VLA_AIWATCHER_BASE_URL=  # aiwatcher ingest endpoint
VLA_AIWATCHER_API_KEY=   # must match aiwatcher's key (or both empty)
WALLX_REPO_DIR=          # local clone of X-Square-Robot/wall-x`}
				</pre>
				<p className="text-xs">API keys only matter when aiwatcher has AIWATCHER_API_KEY set. Not related to HuggingFace login.</p>
			</div>
		),
	},
	{
		id: "faq",
		label: "FAQ",
		icon: HelpCircle,
		content: () => (
			<div className="space-y-4 text-sm text-muted-foreground">
				<details className="p-3 rounded-xl border border-border bg-card/40">
					<summary className="cursor-pointer font-medium text-foreground">Is this a robot patrolling the premises?</summary>
					<p className="mt-2">No. VLA-mcp is not a security robot. It's a training pipeline for Vision-Language-Action models — software that learns robot motor commands from camera images and text. There is no physical robot attached unless you build one.</p>
				</details>
				<details className="p-3 rounded-xl border border-border bg-card/40">
					<summary className="cursor-pointer font-medium text-foreground">Does this work with a Tapo cam?</summary>
					<p className="mt-2">No. VLA needs robot camera feeds (multiview video from gripper/workspace cams) synchronized with joint-angle action trajectories. A Tapo cam provides neither synchronized joint data nor the action space a VLA model needs.</p>
				</details>
				<details className="p-3 rounded-xl border border-border bg-card/40">
					<summary className="cursor-pointer font-medium text-foreground">Can I use this in Resonite?</summary>
					<p className="mt-2">Not directly. Resonite vbots use C# scripts, not learned VLA policies. VLA models need camera feeds + action spaces (joint angles, gripper state). Resonite is a VR platform, not a robotics simulation.</p>
				</details>
				<details className="p-3 rounded-xl border border-border bg-card/40">
					<summary className="cursor-pointer font-medium text-foreground">Why does this exist if no robot has been trained?</summary>
					<p className="mt-2">Preemptive infrastructure. The MuJoCo sim server, limx-robotics-mcp (Unitree dog), and this VLA bridge were all scaffolded in parallel so that when someone collects teleoperation demos, the pipeline from demo → trained policy is ready to go. It's shelfware, not vaporware.</p>
				</details>
			</div>
		),
	},
];

export default function HelpPage() {
	const [activeTab, setActiveTab] = useState("overview");
	const [slugs, setSlugs] = useState<string[]>([]);
	const [slug, setSlug] = useState("fleet_integration");
	const [content, setContent] = useState("");

	useEffect(() => {
		apiGet<{ slugs?: string[] }>("/api/v1/help").then((d) => setSlugs(d.slugs ?? [])).catch(() => {});
	}, []);

	useEffect(() => {
		apiGet<{ content?: string }>(`/api/v1/help/${slug}`)
			.then((d) => setContent(d.content ?? ""))
			.catch(() => setContent(""));
	}, [slug]);

	const activeContent = TABS.find((t) => t.id === activeTab)?.content;

	return (
		<div className="space-y-6">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-2xl font-bold tracking-tight">Help & Docs</h1>
					<p className="text-muted-foreground text-sm mt-1">VLA pipeline, configuration, and fleet integration reference.</p>
				</div>
				<div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-500 text-xs font-bold uppercase tracking-widest">
					<AlertTriangle className="w-3 h-3" />
					Alpha
				</div>
			</div>

			{/* Horizontal Tabs */}
			<div className="flex gap-1 overflow-x-auto pb-2 border-b border-border">
				{TABS.map((tab) => {
					const Icon = tab.icon;
					return (
						<button
							key={tab.id}
							type="button"
							onClick={() => setActiveTab(tab.id)}
							className={`flex items-center gap-2 px-4 py-3 rounded-t-xl text-sm font-medium transition-all whitespace-nowrap ${
								activeTab === tab.id
									? "bg-card border border-b-0 border-border text-foreground shadow-sm"
									: "text-muted-foreground hover:text-foreground hover:bg-white/5"
							}`}
						>
							<Icon className="w-4 h-4" />
							{tab.label}
						</button>
					);
				})}
			</div>

			{/* Active Tab */}
			<div className="animate-in fade-in zoom-in-95 duration-300">
				{activeContent ? activeContent() : null}
			</div>

			{/* MCP help docs */}
			{slugs.length > 0 && (
				<div className="space-y-3 pt-4 border-t border-border">
					<h3 className="text-sm font-semibold text-muted-foreground">MCP help topics</h3>
					<div className="flex gap-2 flex-wrap">
						{slugs.map((s) => (
							<button key={s} type="button" onClick={() => setSlug(s)}
								className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
									slug === s ? "bg-primary/10 border-primary/30 text-primary" : "bg-card border-border text-muted-foreground hover:text-foreground"
								}`}>
								{s}
							</button>
						))}
					</div>
					{content && (
						<pre className="bg-card border border-border rounded-xl p-4 text-xs whitespace-pre-wrap max-h-[40vh] overflow-y-auto text-muted-foreground">
							{content}
						</pre>
					)}
				</div>
			)}
		</div>
	);
}
