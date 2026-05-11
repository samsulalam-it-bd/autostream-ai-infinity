import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import ApiVault from './pages/ApiVault'
import UploadZone from './pages/UploadZone'
import AutoPublish from './pages/AutoPublish'
import Engagement from './pages/Engagement'
import Logs from './pages/Logs'
import SystemHealth from './pages/SystemHealth'
import Workspace from './pages/Workspace'

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Navigate to="/overview" replace />} />
                <Route path="overview" element={<Dashboard />} />
                <Route path="accounts" element={<Accounts />} />
                <Route path="autopublish" element={<AutoPublish />} />
                <Route path="upload" element={<UploadZone />} />
                <Route path="wizard" element={<Workspace />} />
                <Route path="vault" element={<ApiVault />} />
                <Route path="engagement" element={<Engagement />} />
                <Route path="logs" element={<Logs />} />
                <Route path="system-health" element={<SystemHealth />} />
                
                {/* Legacy route compatibility */}
                <Route path="workspace/:id" element={<Workspace />} />
            </Route>
        </Routes>
    )
}
