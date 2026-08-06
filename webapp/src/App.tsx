import { Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import DatasetPage from "./pages/DatasetPage";
import TrainingPage from "./pages/TrainingPage";
import WeightsPage from "./pages/WeightsPage";
import FleetPage from "./pages/FleetPage";
import ToolsPage from "./pages/ToolsPage";
import HelpPage from "./pages/HelpPage";
import StatusPage from "./pages/StatusPage";
import PipelinePage from "./pages/PipelinePage";
import NotebooksPage from "./pages/NotebooksPage";

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
      </Routes>
    </AppLayout>
  );
}
