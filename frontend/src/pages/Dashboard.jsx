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
import clsx from 'clsx'

export default function Dashboard() {
    const [stats, setStats] = useState({
        total_uploads_today: 0,
        active_api_keys: 0,
        pending_schedules: 0,
        total_accounts: 0,
        active_platforms: [],
        daily_trend: '0',
        api_breakdown: {},
        account_breakdown: {},
        recent_alerts: []
    })
    const [chartData, setChartData] = useState([])
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const loadData = async () => {
        try {
            setError(null)
            const [s, c, hist] = await Promise.all([
                fetchStats(), fetchUploadChart(), fetchPublishedHistory(5)
            ])
            if (s.data) setStats(s.data)
            if (c.data) setChartData(c.data)
            if (hist.data) setHistory(hist.data)
        } catch (e) { 
            console.error(e)
            setError("Failed to sync dashboard data. Check backend connection.")
        }
        finally { setLoading(false) }
    }

    useEffect(() => { loadData() }, [])

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <RefreshCw className="w-10 h-10 text-[#6c5ce7] animate-spin" />
                    <div className="text-[13px] text-[#7a85b0] font-medium">Syncing Infinity Dashboard...</div>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <div className="flex flex-col items-center gap-4 bg-[#d630310a] p-8 rounded-3xl border border-[#d6303126]">
                    <AlertCircle className="w-12 h-12 text-[#d63031]" />
                    <div className="text-[14px] text-[#7a85b0] font-medium text-center">{error}</div>
                    <button onClick={loadData} className="btn btn-o btn-sm mt-2">Retry Sync</button>
                </div>
            </div>
        )
    }

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
                            <strong className="text-white">{(stats?.active_platforms || []).length}</strong> platforms active
                        </div>
                    </div>
                    <div className="flex gap-2 mt-4 flex-wrap">
                        {Array.isArray(stats?.active_platforms) && stats.active_platforms.includes('youtube') && (
                            <div className="bg-[#ff475714] text-[#ff6b81] border border-[#ff475733] px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5">
                                <Youtube size={12} /> YouTube Active
                            </div>
                        )}
                        {Array.isArray(stats?.active_platforms) && stats.active_platforms.includes('facebook') && (
                            <div className="bg-[#4267b214] text-[#74b9ff] border border-[#4267b233] px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5">
                                <Facebook size={12} /> Facebook Active
                            </div>
                        )}
                        {Array.isArray(stats?.active_platforms) && stats.active_platforms.includes('instagram') && (
                            <div className="bg-[#e8439314] text-[#e84393] border border-[#e8439333] px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5">
                                <Instagram size={12} /> Instagram Active
                            </div>
                        )}
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
                        <TrendingUp size={10} className={clsx(typeof stats?.daily_trend === 'string' && stats.daily_trend.startsWith('+') ? "text-[#00b894]" : "text-[#d63031]")} /> 
                        {stats?.daily_trend} from yesterday
                    </div>
                </div>
                <div className="sc">
                    <div className="text-[22px] mb-1">🔑</div>
                    <div className="sv bg-gradient-to-r from-[#00cec9] to-[#6c5ce7] bg-clip-text text-transparent">
                        {stats?.active_api_keys || 0}
                    </div>
                    <div className="text-[11.5px] text-[#7a85b0]">Active API Keys</div>
                    <div className="text-[10.5px] text-[#3d4666] mt-1">
                        {stats?.api_breakdown?.google || 0} G · {stats?.api_breakdown?.meta || 0} M
                    </div>
                </div>
                <div className="sc">
                    <div className="text-[22px] mb-1">⏳</div>
                    <div className="sv bg-gradient-to-r from-[#00b894] to-[#00cec9] bg-clip-text text-transparent">
                        {stats?.pending_schedules || 0}
                    </div>
                    <div className="text-[11.5px] text-[#7a85b0]">Pending Schedules</div>
                    <div className="text-[10.5px] text-[#3d4666] mt-1">Next: {stats?.next_schedule_time || 'None'}</div>
                </div>
                <div className="sc">
                    <div className="text-[22px] mb-1">📺</div>
                    <div className="sv bg-gradient-to-r from-[#fdcb6e] to-[#e17055] bg-clip-text text-transparent">
                        {stats?.total_accounts || 0}
                    </div>
                    <div className="text-[11.5px] text-[#7a85b0]">Total Accounts</div>
                    <div className="text-[10.5px] text-[#3d4666] mt-1">
                        YT:{stats?.account_breakdown?.youtube || 0} FB:{stats?.account_breakdown?.facebook || 0} IG:{stats?.account_breakdown?.instagram || 0}
                    </div>
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
                        <div className="flex justify-between text-[10.5px] text-[#3d4666] mt-3 px-2">
                            {(chartData || []).map(d => <span key={d.date}>{d.day}</span>)}
                        </div>
                        <div className="flex gap-4 mt-4 text-[12px] text-[#7a85b0]">
                            <span>📈 Total: <strong className="text-white">{(chartData || []).reduce((acc, d) => acc + (d.uploads || 0), 0)}</strong></span>
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
                            {(stats?.recent_alerts || []).length > 0 ? (stats.recent_alerts || []).map((a, i) => (
                                <div key={i} className="flex items-center gap-2 text-[12.5px] text-[#7a85b0]">
                                    <div className={clsx(
                                        "w-4 h-4 rounded-full flex items-center justify-center text-[10px]",
                                        a.type === 'error' ? "bg-[#d630311a] text-[#d63031]" : "bg-[#00b8941a] text-[#00b894]"
                                    )}>
                                        {a.type === 'error' ? '✕' : '✓'}
                                    </div>
                                    <span className="flex-1 truncate">{a.message}</span>
                                    <span className="text-[11px] text-[#3d4666]">
                                        {a.time ? new Date(a.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'recently'}
                                    </span>
                                </div>
                            )) : (
                                <div className="text-[11px] text-[#3d4666]">No recent alerts.</div>
                            )}
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
                    {(history || []).length > 0 ? (history || []).map((h, i) => (
                        <div key={h.id} className="bg-[#0d1120] border border-white/5 rounded-xl p-3 flex items-center gap-4 hover:border-white/10 transition-all">
                            <div className="text-[14.5px] font-bold w-20 bg-gradient-to-r from-[#6c5ce7] to-[#e84393] bg-clip-text text-transparent">
                                {h.published_at ? new Date(h.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}
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
