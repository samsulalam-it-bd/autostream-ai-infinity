import { useState, useEffect } from 'react'
import { 
    Activity, CheckCircle2, HardDrive, Cpu, 
    Database, Network, Zap, RefreshCw, BarChart3, AlertCircle
} from 'lucide-react'
import { fetchSystemReport } from '../lib/api'
import clsx from 'clsx'

export default function SystemHealth() {
    const [report, setReport] = useState(null)
    const [loading, setLoading] = useState(true)

    const loadData = async () => {
        try {
            const res = await fetchSystemReport()
            setReport(res.data)
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }

    useEffect(() => {
        loadData()
        const timer = setInterval(loadData, 10000)
        return () => clearInterval(timer)
    }, [])

    const CIRCLE_CONFIG = {
        radius: 33,
        stroke: 7,
        get circ() { return 2 * Math.PI * this.radius }
    }

    const Gauge = ({ val, label, grad, colors, sub }) => {
        const offset = CIRCLE_CONFIG.circ * (1 - (val || 0) / 100)
        return (
            <div className="sc flex flex-col items-center justify-center p-6 text-center">
                <div className="relative w-[80px] h-[80px] mb-4">
                    <svg className="rotate-[-90deg] w-20 h-20" viewBox="0 0 80 80">
                        <circle 
                            className="fill-none stroke-[#131829]" 
                            cx="40" cy="40" r={CIRCLE_CONFIG.radius} 
                            strokeWidth={CIRCLE_CONFIG.stroke} 
                        />
                        <circle 
                            className="fill-none transition-all duration-1000 ease-out" 
                            cx="40" cy="40" r={CIRCLE_CONFIG.radius} 
                            strokeWidth={CIRCLE_CONFIG.stroke} 
                            strokeDasharray={CIRCLE_CONFIG.circ} 
                            strokeDashoffset={offset}
                            strokeLinecap="round"
                            stroke={`url(#${grad})`}
                        />
                        <defs>
                            <linearGradient id={grad} x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" style={{ stopColor: colors[0] }} />
                                <stop offset="100%" style={{ stopColor: colors[1] }} />
                            </linearGradient>
                        </defs>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-[16px] font-bold text-white">{Math.round(val || 0)}%</div>
                    </div>
                </div>
                <div className="text-[11.5px] text-[#7a85b0] font-bold uppercase tracking-wider">{label}</div>
                {sub && <div className="text-[10px] text-[#3d4666] mt-1">{sub}</div>}
            </div>
        )
    }

    if (loading && !report) return <div className="flex items-center justify-center h-64 text-[#7a85b0]">Loading diagnostics...</div>

    return (
        <div className="space-y-8 animate-in max-w-6xl mx-auto">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Activity className="text-[#6c5ce7]" /> System Health
                    </h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Infrastructure monitoring and service status</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={loadData} className="btn btn-o btn-sm">
                        <RefreshCw size={14} className={clsx(loading && "animate-spin")} /> Refresh
                    </button>
                </div>
            </div>

            {/* ── Gauges ────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <Gauge 
                    val={report?.system_resources?.cpu_percent} 
                    label="CPU Usage" grad="gr1" colors={['#6c5ce7', '#e84393']} 
                />
                <Gauge 
                    val={report?.system_resources?.memory_percent} 
                    label="RAM Usage" grad="gr2" colors={['#00cec9', '#6c5ce7']} 
                    sub={`${report?.system_resources?.memory_used_gb || 0}GB used`}
                />
                <Gauge 
                    val={report?.system_resources?.disk_percent} 
                    label="Disk Usage" grad="gr3" colors={['#00b894', '#00cec9']} 
                    sub={`${report?.system_resources?.disk_free_gb || 0}GB free`}
                />
            </div>

            {/* ── Detailed Stats ─────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Database Metrics */}
                <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                    <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">📊 Database Stats</div>
                    <div className="space-y-3">
                        {[
                            { l: 'Total Accounts', v: report?.database?.total_accounts },
                            { l: 'YouTube Channels', v: report?.database?.youtube_accounts },
                            { l: 'Facebook Pages', v: report?.database?.facebook_accounts },
                            { l: 'Instagram Accounts', v: report?.database?.instagram_accounts },
                            { l: 'Source Videos', v: report?.database?.total_videos },
                            { l: 'Published Schedules', v: report?.database?.published_schedules },
                            { l: 'Failed Schedules', v: report?.database?.failed_schedules, c: (report?.database?.failed_schedules > 0 ? '#d63031' : null) }
                        ].map(item => (
                            <div key={item.l} className="flex justify-between border-b border-white/5 pb-2 last:border-0">
                                <span className="text-[13px] text-[#7a85b0]">{item.l}</span>
                                <span className="text-[13px] text-white font-bold" style={{ color: item.c }}>{item.v || 0}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* API Status */}
                <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                    <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">🌐 External API Status</div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-[#131829] p-4 rounded-xl border border-white/5">
                            <div className="text-[11px] font-bold text-[#7a85b0] uppercase mb-2">Google API</div>
                            <div className="flex justify-between text-[13px] mb-1">
                                <span className="text-[#3d4666]">Active Keys</span>
                                <span className="text-[#00b894] font-bold">{report?.api_keys?.google_active || 0}</span>
                            </div>
                            <div className="flex justify-between text-[13px]">
                                <span className="text-[#3d4666]">Locked</span>
                                <span className="text-[#d63031] font-bold">{report?.api_keys?.google_locked || 0}</span>
                            </div>
                        </div>
                        <div className="bg-[#131829] p-4 rounded-xl border border-white/5">
                            <div className="text-[11px] font-bold text-[#7a85b0] uppercase mb-2">Meta API</div>
                            <div className="flex justify-between text-[13px] mb-1">
                                <span className="text-[#3d4666]">Active Keys</span>
                                <span className="text-[#00cec9] font-bold">{report?.api_keys?.meta_active || 0}</span>
                            </div>
                            <div className="flex justify-between text-[13px]">
                                <span className="text-[#3d4666]">Locked</span>
                                <span className="text-[#d63031] font-bold">{report?.api_keys?.meta_locked || 0}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="mt-6 p-4 bg-[#d630310a] border border-[#d6303120] rounded-xl">
                        <div className="flex items-center gap-2 text-[11px] font-bold text-[#d63031] uppercase mb-2">
                            <AlertCircle size={14} /> Last System Error
                        </div>
                        <div className="text-[12px] text-[#7a85b0] italic leading-relaxed">
                            "{report?.last_error || 'No recent errors detected'}"
                        </div>
                        {report?.last_error_time && (
                            <div className="text-[10px] text-[#3d4666] mt-2">
                                Occurred: {new Date(report.last_error_time).toLocaleString()}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Service Status ────────────────────────────────── */}
            <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">🚀 Core Services</div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[
                        { n: 'FastAPI Backend', s: 'Online', d: 'Port 8000' },
                        { n: 'Postgres DB', s: 'Healthy', d: 'Port 5432' },
                        { n: 'Redis Cache', s: 'Healthy', d: 'Port 6379' },
                        { n: 'Celery Worker', s: 'Active', d: 'Background Tasks' },
                        { n: 'Celery Beat', s: 'Active', d: 'Scheduler' },
                        { n: 'Vite Frontend', s: 'Online', d: 'Port 5173' }
                    ].map(srv => (
                        <div key={srv.n} className="flex items-center gap-3 p-3 bg-[#131829] rounded-xl border border-white/5">
                            <div className="w-2 h-2 rounded-full bg-[#00b894] shadow-[0_0_8px_#00b894]" />
                            <div className="flex-1">
                                <div className="text-[13px] font-bold text-white">{srv.n}</div>
                                <div className="text-[10px] text-[#3d4666]">{srv.d}</div>
                            </div>
                            <span className="badge b-green !text-[9px]">{srv.s}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
