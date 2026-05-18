import { useState, useEffect, useRef } from 'react'
import { Terminal, Download, Trash2, RefreshCw, Filter, Search } from 'lucide-react'
import { fetchLogs } from '../lib/api'
import clsx from 'clsx'

export default function Logs() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')
    const [isLive, setIsLive] = useState(true)
    const scrollRef = useRef()

    const levels = ['all', 'info', 'success', 'warn', 'error', 'debug']

    const loadLogs = async () => {
        try {
            const res = await fetchLogs(100)
            const mapped = res.data.map(l => ({
                t: new Date(l.created_at).toLocaleTimeString([], { hour12: false }),
                l: l.level.toLowerCase(),
                m: l.message
            }))
            setLogs(mapped)
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }

    useEffect(() => {
        loadLogs()
        let timer;
        if (isLive) {
            timer = setInterval(loadLogs, 5000)
        }
        return () => clearInterval(timer)
    }, [isLive])

    return (
        <div className="space-y-6 animate-in">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Terminal className="text-[#6c5ce7]" /> Live Logs
                    </h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Real-time system activity and error tracking</p>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={() => setIsLive(!isLive)}
                        className={clsx(
                            "btn btn-o btn-sm flex items-center gap-2",
                            isLive && "border-[#d63031] text-[#d63031]"
                        )}
                    >
                        <div className={clsx("w-2 h-2 rounded-full", isLive ? "bg-[#d63031] animate-pulse" : "bg-[#3d4666]")} />
                        {isLive ? 'Stop Live' : 'Start Live'}
                    </button>
                    <button onClick={loadLogs} className="btn btn-o btn-sm">
                        <RefreshCw size={14} className={clsx(loading && "animate-spin")} /> Refresh
                    </button>
                </div>
            </div>

            {/* ── Tabs & Info ────────────────────────────────────── */}
            <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="tabs">
                    {levels.map(l => (
                        <div 
                            key={l}
                            className={clsx("tab uppercase", filter === l && "on")}
                            onClick={() => setFilter(l)}
                        >
                            {l} {l === 'all' && <span className="opacity-50 text-[10px]">({logs.length})</span>}
                        </div>
                    ))}
                </div>
                <div className="flex items-center gap-4 text-[12px] text-[#7a85b0]">
                    <div className="flex items-center gap-2">
                        <span className="text-[#3d4666]">Status:</span>
                        <span className={isLive ? "text-[#d63031]" : "text-[#3d4666]"}>● Live {isLive ? 'on' : 'off'}</span>
                    </div>
                    <div className="w-px h-3 bg-white/5" />
                    <span>{logs.length} entries</span>
                </div>
            </div>

            {/* ── Log Box ───────────────────────────────────────── */}
            <div className="bg-[#0d1120] border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
                <div className="max-h-[500px] overflow-y-auto font-mono scrollbar-hide p-2" ref={scrollRef}>
                    {logs.filter(l => filter === 'all' || l.l === filter).map((log, i) => (
                        <div key={i} className="flex gap-4 px-5 py-3 border-b border-white/5 hover:bg-white/[0.02] transition-colors items-start">
                            <span className="text-[#3d4666] text-[11px] pt-1 min-w-[70px]">{log.t}</span>
                            <span className={clsx(
                                "text-[10px] font-bold px-2 py-0.5 rounded uppercase shrink-0",
                                log.l === 'success' ? "bg-[#00b8941a] text-[#00b894]" :
                                log.l === 'error' ? "bg-[#d630311a] text-[#d63031]" :
                                log.l === 'warn' || log.l === 'warning' ? "bg-[#fdcb6e1a] text-[#fdcb6e]" :
                                log.l === 'info' ? "bg-[#00cec91a] text-[#00cec9]" :
                                "bg-[#6c5ce71a] text-[#a29bfe]"
                            )}>
                                {log.l}
                            </span>
                            <span className="text-[#dde3f5] text-[13px] leading-relaxed flex-1 break-words">
                                {log.m}
                            </span>
                        </div>
                    ))}
                    {logs.length === 0 && !loading && (
                        <div className="p-20 text-center space-y-3">
                            <Terminal className="w-12 h-12 text-white/5 mx-auto" />
                            <p className="text-[#3d4666] text-sm italic">No log entries found. Waiting for activity...</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
