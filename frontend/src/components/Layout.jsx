import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
    LayoutDashboard, Users, KeyRound, Upload, Terminal,
    Activity, Zap, HeartPulse, BotMessageSquare, RefreshCw, Send, Monitor, Wand2
} from 'lucide-react'
import clsx from 'clsx'

const NAV_ITEMS = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', section: 'Main' },
    { to: '/accounts', icon: Users, label: 'Channels', badge: '6', section: 'Main' },
    { to: '/autopublish', icon: Zap, label: 'Auto Publish', section: 'Main' },
    { to: '/upload', icon: Upload, label: 'Upload Zone', section: 'Main' },
    { to: '/wizard', icon: Wand2, label: 'Upload Wizard', section: 'Tools' },
    { to: '/api-vault', icon: KeyRound, label: 'API Vault', section: 'Tools' },
    { to: '/engagement', icon: BotMessageSquare, label: 'AI Assistant', section: 'Tools' },
    { to: '/logs', icon: Terminal, label: 'Live Logs', badge: '3', badgeColor: 'bg-orange-500', section: 'Monitor' },
    { to: '/system-health', icon: HeartPulse, label: 'System Health', section: 'Monitor' },
]

export default function Layout() {
    const location = useLocation();
    
    // Map path to titles like in the provided HTML
    const TITLES = {
        '/dashboard': 'Dashboard',
        '/accounts': 'Channels',
        '/autopublish': 'Auto Publish',
        '/upload': 'Upload Zone',
        '/wizard': 'Upload Wizard',
        '/api-vault': 'API Vault',
        '/engagement': 'AI Assistant',
        '/logs': 'Live Logs',
        '/system-health': 'System Health'
    };

    const currentTitle = TITLES[location.pathname] || 'Infinity Command';

    return (
        <div className="flex min-h-screen">
            {/* ── Sidebar (sb) ──────────────────────────────────────────── */}
            <aside className="w-[240px] fixed left-0 top-0 h-screen bg-[#0d1120] border-r border-white/5 flex flex-col z-[200]">
                <div className="p-5 border-b border-white/5">
                    <div className="text-[17px] font-bold bg-gradient-to-r from-[#6c5ce7] to-[#e84393] bg-clip-text text-transparent font-['Clash_Display']">
                        AutoStream AI
                    </div>
                    <div className="text-[10px] text-[#3d4666] tracking-[2px] uppercase mt-1">Infinity Platform</div>
                </div>

                <div className="flex-1 overflow-y-auto py-2">
                    {['Main', 'Tools', 'Monitor'].map(section => (
                        <div key={section}>
                            <div className="text-[9.5px] text-[#3d4666] tracking-[2.5px] uppercase px-4 py-3 font-bold">{section}</div>
                            {NAV_ITEMS.filter(i => i.section === section).map(item => (
                                <NavLink
                                    key={item.to}
                                    to={item.to}
                                    className={({ isActive }) => clsx(
                                        "flex items-center gap-2 px-4 py-2 mx-2 rounded-xl text-[13px] font-medium transition-all group relative",
                                        isActive ? "bg-[#6c5ce724] text-white" : "text-[#7a85b0] hover:bg-white/[0.04] hover:text-white"
                                    )}
                                >
                                    {({ isActive }) => (
                                        <>
                                            {isActive && <div className="absolute left-0 top-[20%] h-[60%] w-[3px] bg-gradient-to-b from-[#6c5ce7] to-[#e84393] rounded-r-full" />}
                                            <item.icon className={clsx("w-4 h-4", isActive ? "text-[#a29bfe]" : "text-[#7a85b0] group-hover:text-white")} />
                                            <span>{item.label}</span>
                                            {item.badge && (
                                                <span className={clsx(
                                                    "ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full text-white",
                                                    item.badgeColor || "bg-gradient-to-r from-[#6c5ce7] to-[#e84393]"
                                                )}>
                                                    {item.badge}
                                                </span>
                                            )}
                                        </>
                                    )}
                                </NavLink>
                            ))}
                        </div>
                    ))}
                </div>

                <div className="p-3 border-t border-white/5">
                    <div className="bg-[#00b89414] border border-[#00b8942e] rounded-xl p-3">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-[#00b894] shadow-[0_0_8px_#00b894]" />
                            <span className="text-[11px] text-[#00b894] font-bold">System Online</span>
                        </div>
                        <div className="text-[10px] text-[#3d4666] mt-1">6 containers running</div>
                    </div>
                </div>
            </aside>

            {/* ── Main Content (main) ─────────────────────────────────────── */}
            <main className="ml-[240px] flex-1 min-h-screen bg-[#080b14]">
                {/* Topbar */}
                <header className="sticky top-0 z-[100] bg-[#080b14e0] backdrop-blur-3xl border-b border-white/5 px-6 py-3 flex items-center gap-4">
                    <div className="flex-1 text-[17px] font-bold font-['Clash_Display'] text-white">{currentTitle}</div>
                    
                    <div className="flex items-center gap-3">
                        <div className="hidden md:flex items-center gap-2 bg-[#00b8941a] border border-[#00b89433] text-[#00b894] px-3 py-1 rounded-full text-[11px] font-bold">
                            <div className="w-1.5 h-1.5 rounded-full bg-[#00b894] animate-pulse" />
                            Auto Publish Active
                        </div>
                        <button className="text-[12px] text-[#7a85b0] hover:text-white bg-transparent border border-white/10 px-3 py-1.5 rounded-xl transition-all">
                            <RefreshCw className="w-3.5 h-3.5 inline mr-1.5" /> Refresh
                        </button>
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#6c5ce7] to-[#e84393] flex items-center justify-center text-xs font-bold text-white shadow-glow-brand cursor-pointer">
                            A
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div className="p-6">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
