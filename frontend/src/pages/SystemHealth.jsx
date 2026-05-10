import { useState, useEffect } from 'react'
import { 
    Activity, CheckCircle2, HardDrive, Cpu, 
    Database, Network, Zap, RefreshCw, BarChart3 
} from 'lucide-react'
import clsx from 'clsx'

export default function SystemHealth() {
    const [metrics, setMetrics] = useState({
        cpu: 34,
        ram: 62,
        disk: 45
    })

    const CIRCLE_CONFIG = {
        radius: 33,
        stroke: 7,
        get circ() { return 2 * Math.PI * this.radius }
    }

    const Gauge = ({ val, label, grad, colors }) => {
        const offset = CIRCLE_CONFIG.circ * (1 - val / 100)
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
                        <div className="text-[16px] font-bold text-white">{val}%</div>
                    </div>
                </div>
                <div className="text-[11.5px] text-[#7a85b0] font-bold uppercase tracking-wider">{label}</div>
            </div>
        )
    }

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
                    <button onClick={() => window.location.reload()} className="btn btn-o btn-sm">
                        <RefreshCw size={14} /> Refresh
                    </button>
                    <button className="btn btn-g btn-sm">
                        <BarChart3 size={14} /> Full Report
                    </button>
                </div>
            </div>

            {/* ── Gauges ────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <Gauge val={metrics.cpu} label="CPU Usage" grad="gr1" colors={['#6c5ce7', '#e84393']} />
                <Gauge val={metrics.ram} label="RAM Usage" grad="gr2" colors={['#00cec9', '#6c5ce7']} />
                <Gauge val={metrics.disk} label="Disk Usage" grad="gr3" colors={['#00b894', '#00cec9']} />
            </div>

            {/* ── Detailed Stats ─────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Containers */}
                <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                    <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">🐳 Docker Containers</div>
                    <div className="space-y-2">
                        {[
                            'autostream_backend', 'autostream_frontend', 'autostream_db', 
                            'autostream_redis', 'autostream_worker', 'autostream_flower'
                        ].map(s => (
                            <div key={s} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0 group">
                                <span className="text-[13px] text-[#7a85b0] group-hover:text-white transition-colors flex items-center gap-2">
                                    <Zap size={14} className="text-[#6c5ce7]" /> {s}
                                </span>
                                <span className="badge b-green !py-0.5 !px-2.5">Running ✓</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Service Connections */}
                <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                    <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">🔌 Service Connections</div>
                    <div className="space-y-2">
                        {[
                            { l: 'Backend API :8000', s: 'Connected' },
                            { l: 'PostgreSQL :5432', s: 'Connected' },
                            { l: 'Redis :6379', s: 'Connected' },
                            { l: 'Celery Worker', s: 'Online' },
                            { l: 'Frontend :5173', s: 'Online' },
                            { l: 'Flower :5555', s: 'Active' }
                        ].map(s => (
                            <div key={s.l} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0 group">
                                <span className="text-[13px] text-[#7a85b0] group-hover:text-white transition-colors flex items-center gap-2">
                                    <Network size={14} className="text-[#00cec9]" /> {s.l}
                                </span>
                                <span className="badge b-green !py-0.5 !px-2.5">{s.s} ✓</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Bottom Row ────────────────────────────────────── */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                    <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">📊 Database Stats</div>
                    <div className="space-y-3 text-[13px]">
                        {[
                            { l: 'Accounts', v: '6' },
                            { l: 'Source Videos', v: '72' },
                            { l: 'Schedules', v: '112' },
                            { l: 'DB Size', v: '128 MB' }
                        ].map(item => (
                            <div key={item.l} className="flex justify-between border-b border-white/5 pb-2">
                                <span className="text-[#7a85b0]">{item.l}</span>
                                <span className="text-white font-bold">{item.v}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                    <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">⏰ Background Tasks</div>
                    <div className="space-y-2">
                        {[
                            { l: 'Schedule Checker', s: 'Every 5m' },
                            { l: 'Token Refresh', s: 'Every 30m' },
                            { l: 'Auto Schedule', s: 'Every 1hr' },
                            { l: 'Drive Sync', s: 'On-demand' }
                        ].map(t => (
                            <div key={t.l} className="flex justify-between items-center py-1">
                                <span className="text-[13px] text-[#7a85b0]">{t.l}</span>
                                <span className="badge b-cyan !text-[9px]">{t.s}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6">
                    <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[2px] mb-6">🌐 External API Status</div>
                    <div className="grid grid-cols-3 gap-3">
                        {[
                            { i: '▶', l: 'YouTube', s: '847/10k' },
                            { i: 'f', l: 'Meta API', s: 'Active' },
                            { i: '🤖', l: 'Gemini', s: '85% used' }
                        ].map(a => (
                            <div key={a.l} className="bg-[#131829] p-3 rounded-xl text-center border border-white/5">
                                <div className="text-lg mb-1">{a.i}</div>
                                <div className="text-[10px] font-bold text-white mb-1 uppercase tracking-tight">{a.l}</div>
                                <div className="text-[9px] text-[#00b894] font-bold">{a.s}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
