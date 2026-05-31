import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  BookOpen,
  Boxes,
  Brain,
  Download,
  LayoutDashboard,
  Network,
  Wrench,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/dataset", label: "Dataset", icon: Boxes },
  { to: "/training", label: "Training", icon: Brain },
  { to: "/weights", label: "Weights", icon: Download },
  { to: "/fleet", label: "Fleet", icon: Network },
  { to: "/tools", label: "Tools", icon: Wrench },
  { to: "/help", label: "Help", icon: BookOpen },
  { to: "/status", label: "Status", icon: Activity },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen">
      <aside
        className={`bg-gray-900 border-r border-gray-800 transition-all ${collapsed ? "w-14" : "w-56"}`}
      >
        <div className="p-3 border-b border-gray-800 flex items-center gap-2">
          <Brain size={20} className="text-violet-400 shrink-0" />
          {!collapsed && <span className="font-semibold text-sm">VLA-MCP</span>}
        </div>
        <button
          type="button"
          className="w-full p-2 text-xs text-gray-500 hover:text-gray-300 border-b border-gray-800"
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
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
