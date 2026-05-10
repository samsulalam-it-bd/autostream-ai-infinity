import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    fetchStats, fetchUploadChart, fetchPublishedHistory, testTelegram
} from '../lib/api'
import {
    Upload, KeyRound, Clock, Users, Film, Send, CheckCircle, XCircle, 
    AlertCircle, TrendingUp, RefreshCw, Zap, Youtube, Facebook, Instagram,
    ChevronRight, Eye, Heart, MessageSquare
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis } from 'recharts'

export default function Dashboard() {
    const [stats, setStats] = useState(null)
    const [chartData, setChartData] = useState([])
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)

    const loadData = async () => {
        try {
            const [s, c, hist] = await Promise.all([
                fetchStats(), fetchUploadChart(), fetchPublishedHistory(5)
            ])
            setStats(s.data)
            setChartData(c.data)
            setHistory(hist.data)
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }

    useEffect(() => { loadData() }, [])

    return (
        <div className="space-y-6 animate-in">
            {/* ── Hero Banner ────────────────────────────────────────── */}
            <div className="hero">
                <div className="relative z-10">
                    <h1 className="text-white">Welcome back, Admin 👋</h1>
                    <p className="text-[#7a85b0] text-sm max-w-2xl">
                        Your automated pipeline is running — {stats?.total_accounts || 0} accounts active, 
                        {stats?.pending_schedules || 0} videos queued across platforms
                    </p>
                    <div className="flex gap-6 mt-4 flex-wrap">
                        <div className="flex items-center gap-2 text-[12.5px] text-[#7a85b0]">
                            <strong className="text-white">{stats?.total_uploads_today || 0}</strong> published today
                        </div>
                        <div className="flex items-center gap-2 text-[12.5px] text-[#7a85b0]">
                            <strong className="text-white">{stats?.pending_schedules || 0}</strong> scheduled
                        </div>
                        <div className="flex items-center gap-2 text-[12.5px] text-[#7a85b0]">
                            <strong className="text-white">3</strong> platforms active
                        </div>
                    </div>
                    <div className="flex gap-2 mt-4 flex-wrap">
                        <div className="bg-[#ff475714] text-[#ff6b81] border border-[#ff475733] px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5">
                            <Youtube size={12} /> YouTube Active
                        </div>
                        <div className="bg-[#4267b214] text-[#74b9ff] border border-[#4267b233] px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5">
                            <Facebook size={12} /> Facebook Active
                        </div>
                        <div className="bg-[#e8439314] text-[#e84393] border border-[#e8439333] px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5">
                            <Instagram size={12} /> Instagram Active
                        </div>
                    </div>
                </div>
                <div className="absolute right-6 top-1/2 -translate-y-1/2 text-[90px] font-bold text-white opacity-[0.03] pointer-events-none select-none">
                    ∞
                </div>
            </div>

            {/* ── Stats Grid ────────────────────────────────────────── */}
            <div className="sg4">
                <div className="sc">
                    <div className="text-[22px] mb-1">📤</div>
                    <div className="sv bg-gradient-to-r from-[#6c5ce7] to-[#e84393] bg-clip-text text-transparent">
                        {stats?.total_uploads_today || 0}
                    </div>
                    <div className="text-[11.5px] text-[#7a85b0]">Uploads Today</div>
                    <div className="text-[10.5px] text-[#3d4666] mt-1 flex items-center gap-1">
                        <TrendingUp size={10} className="text-[#00b894]" /> +3 from yesterday
                    </div>
                </div>
                <div className="sc">
                    <div className="text-[22px] mb-1">🔑</div>
                    <div className="sv bg-gradient-to-r from-[#00cec9] to-[#6c5ce7] bg-clip-text text-transparent">
                        4
                    </div>
                    <div className="text-[11.5px] text-[#7a85b0]">Active API Keys</div>
                    <div className="text-[10.5px] text-[#3d4666] mt-1">All operational</div>
                </div>
                <div className="sc">
                    <div className="text-[22px] mb-1">⏳</div>
                    <div className="sv bg-gradient-to-r from-[#00b894] to-[#00cec9] bg-clip-text text-transparent">
                        {stats?.pending_schedules || 0}
                    </div>
                    <div className="text-[11.5px] text-[#7a85b0]">Pending Schedules</div>
                    <div className="text-[10.5px] text-[#3d4666] mt-1">Next: 2:00 PM</div>
                </div>
                <div className="sc">
                    <div className="text-[22px] mb-1">📺</div>
                    <div className="sv bg-gradient-to-r from-[#fdcb6e] to-[#e17055] bg-clip-text text-transparent">
                        {stats?.total_accounts || 0}
                    </div>
                    <div className="text-[11.5px] text-[#7a85b0]">Total Accounts</div>
                    <div className="text-[10.5px] text-[#3d4666] mt-1">YT:1 FB:3 IG:2</div>
                </div>
            </div>

            {/* ── Middle Row ────────────────────────────────────────── */}
            <div className="g2">
                {/* Chart */}
                <div>
                    <div className="sec-hd">
                        <div className="sec-title flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-[#6c5ce7]" /> 📊 Upload Activity (7 Days)
                        </div>
                    </div>
                    <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-5">
                        <ResponsiveContainer width="100%" height={120}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6c5ce7" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#6c5ce7" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <Tooltip 
                                    contentStyle={{ background: '#131829', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area type="monotone" dataKey="uploads" stroke="#6c5ce7" fillOpacity={1} fill="url(#chartGrad)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                        <div className="flex justify-between text-[10.5px] text-[#3d4666] mt-3">
                            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
                        </div>
                        <div className="flex gap-4 mt-4 text-[12px] text-[#7a85b0]">
                            <span>📈 Total: <strong className="text-white">108</strong></span>
                            <span>✅ Success: <strong className="text-[#00b894]">102</strong></span>
                            <span>❌ Failed: <strong className="text-[#d63031]">6</strong></span>
                        </div>
                    </div>
                </div>

                {/* Telegram Monitor */}
                <div>
                    <div className="sec-hd">
                        <div className="sec-title flex items-center gap-2">
                            <Send className="w-4 h-4 text-[#00cec9]" /> 📱 Telegram Monitor
                        </div>
                    </div>
                    <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-5">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-xl bg-[#00cec91a] flex items-center justify-center text-[#00cec9]">
                                <Send size={20} />
                            </div>
                            <div className="flex-1">
                                <div className="text-[13.5px] font-semibold text-white">@autostream_bot</div>
                                <div className="flex items-center gap-1.5 mt-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-[#00b894] shadow-[0_0_8px_#00b894]" />
                                    <span className="text-[10px] font-bold text-[#00b894] uppercase tracking-wider">Connected</span>
                                </div>
                            </div>
                            <button 
                                className="btn btn-g3 py-1 px-3 text-[11px]"
                                onClick={() => testTelegram('Test from Dashboard')}
                            >
                                Send Test
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {['/stats', '/channels', '/pending', '/health', '/report', '/failed'].map(cmd => (
                                <span key={cmd} className="px-2 py-1 bg-[#131829] border border-[#00cec926] rounded-md text-[11px] font-mono text-[#00cec9]">
                                    {cmd}
                                </span>
                            ))}
                        </div>
                    </div>
                    <div className="mt-4">
                        <div className="text-[13.5px] font-semibold text-white mb-2">🔔 Recent Alerts</div>
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 text-[12.5px] text-[#7a85b0]">
                                <div className="w-4 h-4 rounded-full bg-[#00b8941a] text-[#00b894] flex items-center justify-center text-[10px]">✓</div>
                                <span className="flex-1 truncate">AutoStream Studio: "Reel_03.mp4" published</span>
                                <span className="text-[11px] text-[#3d4666]">2m ago</span>
                            </div>
                            <div className="flex items-center gap-2 text-[12.5px] text-[#7a85b0]">
                                <div className="w-4 h-4 rounded-full bg-[#d630311a] text-[#d63031] flex items-center justify-center text-[10px]">✕</div>
                                <span className="flex-1 truncate">autostream_reels: Token expired</span>
                                <span className="text-[11px] text-[#3d4666]">14m ago</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Bottom Row ────────────────────────────────────────── */}
            <div className="mt-6">
                <div className="sec-hd">
                    <div className="sec-title flex items-center gap-2">
                        <Clock className="w-4 h-4 text-[#fdcb6e]" /> ⏰ Upcoming Schedules
                    </div>
                    <Link to="/upload" className="text-[12px] text-[#7a85b0] hover:text-white transition-colors">
                        View All →
                    </Link>
                </div>
                <div className="space-y-2">
                    {history.length > 0 ? history.map((h, i) => (
                        <div key={h.id} className="bg-[#0d1120] border border-white/5 rounded-xl p-3 flex items-center gap-4 hover:border-white/10 transition-all">
                            <div className="text-[14.5px] font-bold w-20 bg-gradient-to-r from-[#6c5ce7] to-[#e84393] bg-clip-text text-transparent">
                                {new Date(h.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                            <div className="flex-1">
                                <div className="text-[13px] font-medium text-white truncate max-w-md">{h.video_title}</div>
                                <div className="text-[11px] text-[#7a85b0] mt-0.5 flex items-center gap-1.5">
                                    {h.platform === 'youtube' && <Youtube size={10} className="text-red-400" />}
                                    {h.platform === 'facebook' && <Facebook size={10} className="text-blue-400" />}
                                    {h.platform === 'instagram' && <Instagram size={10} className="text-pink-400" />}
                                    {h.channel_name} ({h.platform})
                                </div>
                            </div>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#00b8941a] text-[#00b894] border border-[#00b89433]">
                                ✅ Success
                            </span>
                        </div>
                    )) : (
                        <div className="text-center py-8 text-[#3d4666] text-sm">No recent activity found.</div>
                    )}
                </div>
            </div>
        </div>
    )
}
