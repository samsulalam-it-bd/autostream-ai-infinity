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

    const loadData = async () => {
        try {
            setLoading(true)
            const [accRes, schedRes] = await Promise.all([
                fetchAccounts(),
                fetchSchedules(false) // Get pending schedules only
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
                                <span className={clsx("badge", account.status === 'active' ? "b-green" : "b-red")}>
                                    {account.status}
                                </span>
                            </div>
                        </div>

                        <div className="p-4 space-y-4">
                            <div className="grid grid-cols-4 gap-2">
                                {[
                                    { l: 'Pub', v: account.stats?.published || 0, g: 'var(--g3)' },
                                    { l: 'Pend', v: schedules.filter(s => s.account_id === account.id).length, g: 'var(--g4)' },
                                    { l: 'Fail', v: account.stats?.failed || 0, c: '#3d4666' },
                                    { l: 'Queue', v: account.stats?.queue || 0, g: 'var(--g2)' }
                                ].map((s, i) => (
                                    <div key={i} className="bg-[#131829] rounded-lg p-2 text-center">
                                        <div className="text-[14px] font-bold" style={s.g ? { background: s.g, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' } : { color: s.c }}>{s.v}</div>
                                        <div className="text-[9px] text-[#3d4666] font-bold uppercase">{s.l}</div>
                                    </div>
                                ))}
                            </div>

                            <div className="bg-[#131829] rounded-xl py-2 px-3 text-center text-[11.5px] text-[#7a85b0]">
                                ⏰ Next upload: <b className="text-white ml-1">{account.stats?.next_at || 'Soon'}</b>
                            </div>

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
                                        return (
                                            <div 
                                                key={sched.id} 
                                                className="bg-[#0d1120] border border-white/5 hover:border-white/20 rounded-lg p-1.5 flex items-center justify-between gap-1 group/item cursor-pointer"
                                                onClick={() => handleTriggerSchedule(sched.id)}
                                                title="Click to trigger immediately"
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
