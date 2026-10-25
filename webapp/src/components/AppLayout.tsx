import {
	Activity,
	BookOpen,
	Boxes,
	Brain,
	Download,
	GitBranch,
	Inbox,
	LayoutDashboard,
	LayoutGrid,
	MessageSquare,
	Network,
	NotebookPen,
	ScrollText,
	Settings,
	Sparkles,
	Wrench,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useBackendStatus } from "../lib/useBackendStatus";
import { useZoom } from "../lib/useZoom";
import LoggerModal from "./LoggerModal";

const navItems = [
	{ to: "/", label: "Dashboard", icon: LayoutDashboard },
	{ to: "/inbox", label: "Inbox", icon: Inbox },
	{ to: "/chat", label: "Chat", icon: MessageSquare },
	{ to: "/dataset", label: "Dataset", icon: Boxes },
	{ to: "/pipeline", label: "Pipeline", icon: GitBranch },
	{ to: "/training", label: "Training", icon: Brain },
	{ to: "/weights", label: "Weights", icon: Download },
	{ to: "/notebooks", label: "Notebooks", icon: NotebookPen },
	{ to: "/fleet", label: "Fleet", icon: Network },
	{ to: "/apps", label: "Apps", icon: LayoutGrid },
	{ to: "/tools", label: "Tools", icon: Wrench },
	{ to: "/skills", label: "Skills", icon: Sparkles },
	{ to: "/logs", label: "Logs", icon: ScrollText },
	{ to: "/help", label: "Help", icon: BookOpen },
	{ to: "/settings", label: "Settings", icon: Settings },
	{ to: "/status", label: "Status", icon: Activity },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
	const { reset: resetZoom, level: zoomLevel } = useZoom();
	const [collapsed, setCollapsed] = useState(false);
	const [loggerOpen, setLoggerOpen] = useState(false);
	const backend = useBackendStatus();
	const navigate = useNavigate();

	useEffect(() => {
		const handler = (e: KeyboardEvent) => {
			if (!(e.ctrlKey || e.metaKey)) return;
			if (e.key.toLowerCase() === "l") {
				e.preventDefault();
				setLoggerOpen((v) => !v);
			} else if (e.key.toLowerCase() === "h") {
				e.preventDefault();
				navigate("/help");
			} else if (e.key.toLowerCase() === "k") {
				const input = document.querySelector<HTMLElement>(
					'[data-testid^="search-"] input, input[data-testid^="search-"], [data-testid="search-episodes"], [data-testid="search-tools"], [data-testid="search-inbox"], [data-testid="search-apps"], [data-testid="logger-search"], [data-testid="chat-input"]',
				);
				if (input) {
					e.preventDefault();
					input.focus();
				}
			}
		};
		window.addEventListener("keydown", handler);
		return () => window.removeEventListener("keydown", handler);
	}, [navigate]);

	return (
		<div className="flex h-screen">
			<aside
				className={`bg-gray-900 border-r border-gray-800 transition-all flex flex-col ${collapsed ? "w-14" : "w-56"}`}
			>
				<div className="p-3 border-b border-gray-800 flex items-center gap-2">
					<Brain size={20} className="text-violet-400 shrink-0" />
					{!collapsed && <span className="font-semibold text-sm">VLA-MCP</span>}
				</div>
				<button
					type="button"
					className="w-full p-2 text-sm text-gray-400 hover:text-gray-300 border-b border-gray-800"
					onClick={() => setCollapsed(!collapsed)}
				>
					{collapsed ? ">" : "<"}
				</button>
				<nav className="p-2 space-y-1">
					{navItems.map(({ to, label, icon: Icon }) => (
						<NavLink
							key={to}
							to={to}
							end={to === "/"}
							className={({ isActive }) =>
								`flex items-center gap-2 px-2 py-2 rounded text-sm transition ${
									isActive
										? "bg-violet-900/40 text-violet-300"
										: "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
								}`
							}
						>
							<Icon size={16} className="shrink-0" />
							{!collapsed && <span>{label}</span>}
						</NavLink>
					))}
				</nav>
				<div
					className="mt-auto p-2 border-t border-gray-800"
					data-testid="backend-dot"
				>
					<div className="flex items-center gap-2 text-sm text-gray-400">
						<span
							className={`inline-block w-2 h-2 rounded-full ${
								backend.state === "connected"
									? "bg-green-500"
									: backend.state === "error"
										? "bg-red-500"
										: "bg-yellow-500 animate-pulse"
							}`}
						/>
						{!collapsed && (
							<span>
								{backend.state === "connected" ? "Backend live" : backend.state}
							</span>
						)}
					</div>
					{!collapsed && (
						<button
							type="button"
							data-testid="backend-restart"
							onClick={() => void backend.restart()}
							title={backend.lastError || "Restart backend"}
							className="mt-1 w-full text-sm px-2 py-1 rounded bg-gray-800 text-gray-300 hover:text-gray-100"
						>
							Restart Backend
						</button>
					)}
					{!collapsed && (
						<div className="mt-1 flex items-center gap-1">
							<button
								type="button"
								data-testid="logger-toggle"
								onClick={() => setLoggerOpen(true)}
								title="Server logs (Ctrl+L)"
								className="flex-1 text-sm px-2 py-1 rounded bg-gray-800 text-gray-300 hover:text-gray-100"
							>
								Logs
							</button>
							<button
								type="button"
								onClick={resetZoom}
								title="Reset zoom (Ctrl+0)"
								className="text-sm px-2 py-1 rounded bg-gray-800 text-gray-300 hover:text-gray-100"
							>
								{Math.round(zoomLevel * 100)}%
							</button>
						</div>
					)}
				</div>
			</aside>
			<main className="flex-1 overflow-auto p-6">{children}</main>
			{loggerOpen && <LoggerModal onClose={() => setLoggerOpen(false)} />}
		</div>
	);
}
