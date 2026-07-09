import { useState, useEffect } from 'react'
import { 
    fetchAccounts, triggerPipeline, syncAccountNow, 
    instantPost, fetchSchedules, deleteSchedule 
} from '../lib/api'
import { 
    Zap, RefreshCw, CheckCircle2, XCircle, Clock, 
    Youtube, Facebook, Instagram, Play, Send, Calendar, Trash2, ExternalLink
} from 'lucide-react'
import clsx from 'clsx'

export default function AutoPublish() {
    const [accounts, setAccounts] = useState([])
    const [schedules, setSchedules] = useState([])
    const [loading, setLoading] = useState(true)
    const [currentDate, setCurrentDate] = useState(new Date())
    const [now, setNow] = useState(new Date())

    useEffect(() => {
        const interval = setInterval(() => {
            setNow(new Date())
        }, 1000)
        return () => clearInterval(interval)
    }, [])

    const getCountdown = (account_id) => {
        const accountSchedules = schedules
            .filter(s => s.account_id === account_id && !s.is_published)
            .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
        
        if (accountSchedules.length === 0) return null
        
        const nextSched = accountSchedules[0]
        const diffMs = new Date(nextSched.scheduled_time).getTime() - now.getTime()
        
        if (diffMs <= 0) return "Publishing now..."
        
        const secs = Math.floor(diffMs / 1000)
        const hours = Math.floor(secs / 3600)
        const mins = Math.floor((secs % 3600) / 60)
        const remainingSecs = secs % 60
        
        return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(remainingSecs).padStart(2, '0')}`
    }

    const getTodaySchedules = (account_id) => {
        const todayStr = now.toDateString()
        return schedules.filter(s => {
            if (s.account_id !== account_id) return false
            const sDate = new Date(s.scheduled_time)
            return sDate.toDateString() === todayStr
        }).sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
    }

    const loadData = async () => {
        try {
            setLoading(true)
            const [accRes, schedRes] = await Promise.all([
                fetchAccounts(),
                fetchSchedules() // Get all schedules (both published and pending)
            ])
            setAccounts(accRes.data || [])
            setSchedules(schedRes.data || [])
        } catch (e) { 
            console.error(e) 
        } finally { 
            setLoading(false) 
        }
    }

    useEffect(() => { loadData() }, [])

    const handleAction = async (action, id) => {
        try {
            if (action === 'sync') await syncAccountNow(id)
            if (action === 'run' || action === 'instant') await instantPost(id)
            loadData()
        } catch (e) { console.error(e) }
    }

    const handleTriggerSchedule = async (id) => {
        if (!window.confirm('Trigger this scheduled post immediately?')) return
        try {
            await triggerPipeline(id)
            alert('Video pipeline triggered successfully!')
            loadData()
        } catch (e) {
            console.error(e)
            alert('Failed to trigger schedule.')
        }
    }

    const handleDeleteSchedule = async (id) => {
        if (!window.confirm('Are you sure you want to cancel this scheduled upload?')) return
        try {
            await deleteSchedule(id)
            loadData()
        } catch (e) {
            console.error(e)
        }
    }

    // ── Calendar Calculations ──────────────────────────────────────────────
    const getDaysInMonth = (date) => {
        const year = date.getFullYear()
        const month = date.getMonth()
        const firstDay = new Date(year, month, 1).getDay()
        const totalDays = new Date(year, month + 1, 0).getDate()
        
        // Blank spaces before the first day
        const blanks = Array(firstDay).fill(null)
        // Days of the month
        const days = Array.from({ length: totalDays }, (_, i) => new Date(year, month, i + 1))
        
        return [...blanks, ...days]
    }

    const calendarCells = getDaysInMonth(currentDate)

    const nextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))
    }

    const prevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))
    }

    const formatMonthYear = (date) => {
        return date.toLocaleDateString('default', { month: 'long', year: 'numeric' })
    }

    return (
        <div className="space-y-8 animate-in max-w-6xl mx-auto">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Zap className="text-[#6c5ce7]" /> Auto Publish Monitor
                    </h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Real-time publishing queue across all platforms</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={loadData} className="btn btn-o btn-sm">
                        <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Sync Queue
                    </button>
                    <button onClick={() => alert('All queued items will run in sequence.')} className="btn btn-g btn-sm">
                        <Zap className="w-3.5 h-3.5 mr-1.5" /> Start Auto Engine
                    </button>
                </div>
            </div>

            {/* ── Stats Grid ────────────────────────────────────────── */}
            <div className="sg4">
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g3)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '22px' }}>
                        {accounts.reduce((acc, a) => acc + (a.stats?.published || 0), 0)}
                    </div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Published Total</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '22px' }}>
                        {schedules.length}
                    </div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Upcoming Calendar Queue</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ color: 'var(--red)', fontSize: '22px' }}>
                        {accounts.reduce((acc, a) => acc + (a.stats?.failed || 0), 0)}
                    </div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Retrying / Failed</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g2)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '22px' }}>
                        {accounts.filter(a => a.status === 'active').length}
                    </div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Active Platforms</div>
                </div>
            </div>

            {/* ── Content Grid: Channels ────────────────────────────── */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {accounts.map(account => (
                    <div key={account.id} className="bg-[#0d1120] border border-white/5 rounded-[20px] overflow-hidden transition-all hover:border-white/10 group">
                        <div className="p-4 flex items-center gap-3 border-b border-white/5">
                            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-lg">
                                {account.platform === 'youtube' && <Youtube className="text-red-500 w-5 h-5" />}
                                {account.platform === 'facebook' && <Facebook className="text-blue-500 w-5 h-5" />}
                                {account.platform === 'instagram' && <Instagram className="text-pink-500 w-5 h-5" />}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="text-[14px] font-bold text-white truncate">{account.channel_name || account.name}</div>
                                <div className="text-[11px] text-[#7a85b0] uppercase tracking-wider font-semibold">{account.platform}</div>
                            </div>
                            <div className="flex items-center gap-2">
                                {(() => {
                                    const pendingCount = schedules.filter(s => s.account_id === account.id && !s.is_published).length
                                    const isConfigured = pendingCount > 0
                                    return (
                                        <span className={clsx("badge font-bold flex items-center gap-1", isConfigured ? "b-green" : "b-red")}>
                                            {isConfigured ? "✅ Configured" : "⚠️ Not Setup"}
                                        </span>
                                    )
                                })()}
                            </div>
                        </div>

                        <div className="p-4 space-y-4">
                            <div className="grid grid-cols-4 gap-2">
                                {[
                                    { l: 'Pub', v: account.stats?.published || 0, g: 'var(--g3)' },
                                    { l: 'Pend', v: schedules.filter(s => s.account_id === account.id && !s.is_published).length, g: 'var(--g4)' },
                                    { l: 'Fail', v: account.stats?.failed || 0, c: '#3d4666' },
                                    { l: 'Queue', v: account.stats?.queue || 0, g: 'var(--g2)' }
                                ].map((s, i) => (
                                    <div key={i} className="bg-[#131829] rounded-lg p-2 text-center">
                                        <div className="text-[14px] font-bold" style={s.g ? { background: s.g, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' } : { color: s.c }}>{s.v}</div>
                                        <div className="text-[9px] text-[#3d4666] font-bold uppercase">{s.l}</div>
                                    </div>
                                ))}
                            </div>

                            <div className="bg-[#131829] rounded-xl py-2.5 px-3 flex flex-col gap-1.5 border border-white/5">
                                <div className="flex justify-between items-center text-[11.5px] text-[#7a85b0]">
                                    <span className="flex items-center gap-1">⏰ Next Upload:</span>
                                    <span className="text-white font-bold">
                                        {(() => {
                                            const pending = schedules
                                                .filter(s => s.account_id === account.id && !s.is_published)
                                                .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
                                            if (pending.length > 0) {
                                                return new Date(pending[0].scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                            }
                                            return 'No upcoming schedules'
                                        })()}
                                    </span>
                                </div>
                                {(() => {
                                    const countdown = getCountdown(account.id)
                                    if (countdown) {
                                        return (
                                            <div className="flex justify-between items-center text-[11px] bg-[#1a2035] rounded-lg px-2 py-1 text-[#00cec9] font-mono font-bold tracking-wider">
                                                <span>⏱️ COUNTDOWN:</span>
                                                <span className="animate-pulse">{countdown}</span>
                                            </div>
                                        )
                                    }
                                    return null
                                })()}
                            </div>

                            {/* Today's Schedule Progress Timeline */}
                            {(() => {
                                const todayScheds = getTodaySchedules(account.id)
                                if (todayScheds.length === 0) {
                                    return (
                                        <div className="text-[11px] text-[#4b5563] text-center italic py-2 border-t border-white/5">
                                            No uploads scheduled for today
                                        </div>
                                    )
                                }

                                return (
                                    <div className="border-t border-white/5 pt-3 mt-3 space-y-2">
                                        <div className="text-[10px] font-bold text-[#7a85b0] uppercase tracking-wider flex justify-between items-center">
                                            <span>📅 Today's Queue</span>
                                            <span className="bg-white/5 px-1.5 py-0.5 rounded text-white text-[9px]">{todayScheds.length}</span>
                                        </div>
                                        <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1 custom-scrollbar">
                                            {todayScheds.map(sched => {
                                                const isSuccess = sched.is_published && !sched.error_message
                                                const isFailed = !!sched.error_message
                                                const isPending = !sched.is_published && !sched.error_message

                                                const schedTime = new Date(sched.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                                const filename = sched.video?.original_filename || 'Media file'

                                                return (
                                                    <div key={sched.id} className="flex gap-2 items-start bg-[#131829]/60 p-2 rounded-lg border border-white/5 text-[11px]">
                                                        {/* Left status dot */}
                                                        <div className="mt-1 shrink-0">
                                                            {isSuccess && <span className="flex h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_#10b981]" />}
                                                            {isFailed && <span className="flex h-2 w-2 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444]" />}
                                                            {isPending && <span className="flex h-2 w-2 rounded-full bg-blue-400 shadow-[0_0_8px_#60a5fa] animate-pulse" />}
                                                        </div>

                                                        {/* Main info block */}
                                                        <div className="flex-1 min-w-0 space-y-0.5">
                                                            <div className="flex justify-between items-center gap-2">
                                                                <span className="font-bold text-white">{schedTime}</span>
                                                                <div className="flex items-center gap-1.5">
                                                                    {isSuccess && (
                                                                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-500/10 text-[#00b894] font-bold border border-green-500/20">
                                                                            SUCCESS
                                                                        </span>
                                                                    )}
                                                                    {isFailed && (
                                                                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/10 text-[#ff7675] font-bold border border-red-500/20">
                                                                            FAILED
                                                                        </span>
                                                                    )}
                                                                    {isPending && (
                                                                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-[#74b9ff] font-bold border border-blue-500/20">
                                                                            PENDING
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            <div className="text-[10px] text-[#7a85b0] truncate" title={filename}>
                                                                {filename}
                                                            </div>
                                                            {isFailed && (
                                                                <div className="text-[9px] bg-red-950/40 text-[#ff7675] rounded p-1.5 mt-1 border border-red-500/10 select-text break-words max-h-[60px] overflow-y-auto">
                                                                    ⚠️ {sched.error_message.split('\n')[0] || 'Unknown connection error'}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Action link or trigger */}
                                                        <div className="shrink-0 flex items-center justify-center">
                                                            {isSuccess && sched.published_url && (
                                                                <a 
                                                                    href={sched.published_url} 
                                                                    target="_blank" 
                                                                    rel="noopener noreferrer" 
                                                                    className="p-1 hover:bg-white/5 rounded text-[#00b894] transition-all"
                                                                    title="View Live Post"
                                                                >
                                                                    <ExternalLink size={11} />
                                                                </a>
                                                            )}
                                                            {isPending && (
                                                                <button 
                                                                    onClick={() => handleTriggerSchedule(sched.id)}
                                                                    className="p-1 hover:bg-white/5 rounded text-white/60 hover:text-white transition-all"
                                                                    title="Trigger Immediately"
                                                                >
                                                                    <Play size={11} />
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </div>
                                )
                            })()}

                            <div className="flex gap-1.5">
                                <button onClick={() => handleAction('run', account.id)} className="flex-1 btn btn-o !p-2 text-[11px] gap-1.5 hover:text-[#00b894] hover:border-[#00b894]">
                                    <Play size={12} /> Post Next
                                </button>
                                <button onClick={() => handleAction('sync', account.id)} className="flex-1 btn btn-o !p-2 text-[11px] gap-1.5 hover:text-[#00cec9] hover:border-[#00cec9]">
                                    <RefreshCw size={12} /> Sync Drive
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* ── FEATURE 3: Dynamic Schedule Calendar ─────────────────── */}
            <div className="bg-[#0d1120] border border-white/5 rounded-[24px] p-6 space-y-6">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h2 className="text-[18px] font-bold text-white flex items-center gap-2">
                            <Calendar className="text-[#6c5ce7]" size={20} /> Visual Content Calendar
                        </h2>
                        <p className="text-[12px] text-[#7a85b0] mt-0.5">Drag-and-drop planning & priority execution control</p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button onClick={prevMonth} className="px-3 py-1.5 bg-[#131829] border border-white/5 rounded-xl text-[12px] text-white hover:border-[#6c5ce7] transition-all">
                            ◀ Prev Month
                        </button>
                        <span className="text-[13.5px] font-bold text-white min-w-[120px] text-center">
                            {formatMonthYear(currentDate)}
                        </span>
                        <button onClick={nextMonth} className="px-3 py-1.5 bg-[#131829] border border-white/5 rounded-xl text-[12px] text-white hover:border-[#6c5ce7] transition-all">
                            Next Month ▶
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-7 gap-2">
                    {/* Calendar Day Titles */}
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
                        <div key={d} className="text-center text-[10.5px] font-bold uppercase tracking-wider text-[#3d4666] py-2">
                            {d}
                        </div>
                    ))}

                    {/* Calendar Date Cells */}
                    {calendarCells.map((cell, idx) => {
                        if (!cell) {
                            return <div key={`blank-${idx}`} className="bg-transparent h-28 rounded-2xl border border-transparent" />
                        }

                        const dayNum = cell.getDate()
                        const isToday = cell.toDateString() === new Date().toDateString()
                        
                        // Find schedules on this calendar date
                        const daySchedules = schedules.filter(s => {
                            const sDate = new Date(s.scheduled_time)
                            return sDate.getFullYear() === cell.getFullYear() &&
                                   sDate.getMonth() === cell.getMonth() &&
                                   sDate.getDate() === dayNum
                        })

                        return (
                            <div 
                                key={dayNum} 
                                className={clsx(
                                    "bg-[#13182950] h-32 rounded-2xl border p-2 flex flex-col justify-between transition-all hover:bg-[#131829a0]",
                                    isToday ? "border-[#6c5ce780] shadow-[0_0_15px_#6c5ce710]" : "border-white/5"
                                )}
                            >
                                <div className="flex justify-between items-start">
                                    <span className={clsx(
                                        "text-[12.5px] font-bold px-1.5 py-0.5 rounded-md",
                                        isToday ? "bg-[#6c5ce7] text-white" : "text-[#7a85b0]"
                                    )}>
                                        {dayNum}
                                    </span>
                                    {daySchedules.length > 0 && (
                                        <span className="text-[10px] text-[#00b894] font-bold">
                                            {daySchedules.length} Queued
                                        </span>
                                    )}
                                </div>

                                <div className="flex-1 overflow-y-auto mt-2 space-y-1.5 custom-scrollbar">
                                    {daySchedules.map(sched => {
                                        const chan = accounts.find(a => a.id === sched.account_id)
                                        const isSuccess = sched.is_published && !sched.error_message
                                        const isFailed = !!sched.error_message

                                        return (
                                            <div 
                                                key={sched.id} 
                                                className={clsx(
                                                    "bg-[#0d1120] border rounded-lg p-1.5 flex items-center justify-between gap-1 group/item cursor-pointer",
                                                    isSuccess ? "border-green-500/30 hover:border-green-500/60" :
                                                    isFailed ? "border-red-500/30 hover:border-red-500/60" :
                                                    "border-white/5 hover:border-white/20"
                                                )}
                                                onClick={() => handleTriggerSchedule(sched.id)}
                                                title={isSuccess ? "Published (click to trigger/re-run)" : isFailed ? `Failed: ${sched.error_message.split('\n')[0]}` : "Click to trigger immediately"}
                                            >
                                                <div className="flex items-center gap-1.5 min-w-0">
                                                    {sched.platform === 'youtube' && <Youtube className="text-red-500 w-3 h-3 shrink-0" />}
                                                    {sched.platform === 'facebook' && (
                                                        <div className="flex items-center gap-0.5 shrink-0">
                                                            <Facebook className="text-blue-500 w-3 h-3 shrink-0" />
                                                            {sched.media_type === 'IMAGE' ? (
                                                                <span className="text-[9px]" title="Image Post">📸</span>
                                                            ) : (
                                                                <span className="text-[9px]" title="Reels / Video Post">🎥</span>
                                                            )}
                                                        </div>
                                                    )}
                                                    {sched.platform === 'instagram' && <Instagram className="text-pink-500 w-3 h-3 shrink-0" />}
                                                    <span className="text-[10px] text-white font-medium truncate">
                                                        {new Date(sched.scheduled_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                                    </span>
                                                </div>

                                                <button 
                                                    onClick={(e) => {
                                                        e.stopPropagation()
                                                        handleDeleteSchedule(sched.id)
                                                    }}
                                                    className="opacity-0 group-hover/item:opacity-100 p-0.5 hover:bg-red-500/10 rounded text-[#d63031] transition-all"
                                                >
                                                    <Trash2 size={10} />
                                                </button>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
