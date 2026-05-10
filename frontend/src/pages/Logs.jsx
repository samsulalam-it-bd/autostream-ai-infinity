import { useState, useEffect, useRef } from 'react'
import { Terminal, Download, Trash2, RefreshCw, Filter, Search } from 'lucide-react'
import clsx from 'clsx'

const MOCK_LOGS = [
    { t: '14:23:05', l: 'success', m: 'AutoStream Studio: "Product_Review_v3.mp4" published to YouTube ✅ (video ID: dQw4w9WgXcQ)' },
    { t: '14:22:47', l: 'info', m: 'Celery Worker: Token refresh completed for AutoStream Studio — new access_token saved' },
    { t: '14:21:30', l: 'info', m: 'Schedule Checker: 112 pending schedules found — next publish at 14:00' },
    { t: '14:20:12', l: 'info', m: 'Drive Sync [AutoStream Studio]: Scanned folder — found 18 new video files' },
    { t: '14:19:55', l: 'warn', m: 'YouTube API: Daily quota usage at 84.7% (847/1000) — approaching limit' },
    { t: '14:18:33', l: 'success', m: 'AutoStream Media: Facebook post published — "Tutorial_Part2.mp4" (post_id: 23456789)' },
    { t: '14:17:20', l: 'success', m: 'Gemini AI: Content generated for "Reel_Tech_01.mp4" — title and description saved' },
    { t: '14:16:08', l: 'error', m: 'autostream_reels: Instagram token expired — account will not publish until reconnected' },
    { t: '14:15:45', l: 'info', m: 'Celery Worker: Heartbeat OK — 4 active tasks, 0 queued' },
    { t: '14:14:22', l: 'debug', m: 'DB Query: SELECT * FROM upload_schedules WHERE is_published=false — 112 rows returned' }
]

export default function Logs() {
    const [logs, setLogs] = useState(MOCK_LOGS)
    const [filter, setFilter] = useState('all')
    const [isLive, setIsLive] = useState(false)
    const scrollRef = useRef()

    const levels = ['all', 'info', 'success', 'warn', 'error', 'debug']

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
                    <button className="btn btn-o btn-sm">
                        <Download size={14} /> Export
                    </button>
                    <button onClick={() => setLogs([])} className="btn btn-red btn-sm">
                        <Trash2 size={14} /> Clear
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
                <div className="max-height-[500px] overflow-y-auto font-mono scrollbar-hide" ref={scrollRef}>
                    {logs.filter(l => filter === 'all' || l.l === filter).map((log, i) => (
                        <div key={i} className="flex gap-4 px-5 py-3 border-b border-white/5 hover:bg-white/[0.02] transition-colors items-start">
                            <span className="text-[#3d4666] text-[11px] pt-1 min-w-[70px]">{log.t}</span>
                            <span className={clsx(
                                "text-[10px] font-bold px-2 py-0.5 rounded uppercase shrink-0",
                                log.l === 'success' ? "bg-[#00b8941a] text-[#00b894]" :
                                log.l === 'error' ? "bg-[#d630311a] text-[#d63031]" :
                                log.l === 'warn' ? "bg-[#fdcb6e1a] text-[#fdcb6e]" :
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
                    {logs.length === 0 && (
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
