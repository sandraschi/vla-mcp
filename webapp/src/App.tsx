import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import AppsPage from "./pages/AppsPage";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import DatasetPage from "./pages/DatasetPage";
import FleetPage from "./pages/FleetPage";
import HelpPage from "./pages/HelpPage";
import InboxPage from "./pages/InboxPage";
import LogsPage from "./pages/LogsPage";
import NotebooksPage from "./pages/NotebooksPage";
import PipelinePage from "./pages/PipelinePage";
import SettingsPage from "./pages/SettingsPage";
import SkillsPage from "./pages/SkillsPage";
import StatusPage from "./pages/StatusPage";
import ToolsPage from "./pages/ToolsPage";
import TrainingPage from "./pages/TrainingPage";
import WeightsPage from "./pages/WeightsPage";

export default function App() {
	return (
		<AppLayout>
			<Routes>
				<Route path="/" element={<Dashboard />} />
				<Route path="/dataset" element={<DatasetPage />} />
				<Route path="/training" element={<TrainingPage />} />
				<Route path="/weights" element={<WeightsPage />} />
				<Route path="/fleet" element={<FleetPage />} />
				<Route path="/tools" element={<ToolsPage />} />
				<Route path="/help" element={<HelpPage />} />
				<Route path="/pipeline" element={<PipelinePage />} />
				<Route path="/notebooks" element={<NotebooksPage />} />
				<Route path="/status" element={<StatusPage />} />
				<Route path="/chat" element={<ChatPage />} />
				<Route path="/inbox" element={<InboxPage />} />
				<Route path="/skills" element={<SkillsPage />} />
				<Route path="/apps" element={<AppsPage />} />
				<Route path="/logs" element={<LogsPage />} />
				<Route path="/settings" element={<SettingsPage />} />
			</Routes>
		</AppLayout>
	);
}
