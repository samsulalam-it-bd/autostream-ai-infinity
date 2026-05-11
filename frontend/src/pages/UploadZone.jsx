import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchAccounts, syncAccountNow } from '../lib/api'
import { 
    ChevronDown, Folder, HardDrive, RefreshCw, CheckCircle2, 
    AlertCircle, FileVideo, Wand2, ArrowRight, Play 
} from 'lucide-react'
import clsx from 'clsx'

const PLATFORM_ICONS = {
    youtube: '▶',
    facebook: 'f',
    instagram: '◉'
}

const PLATFORM_BGS = {
    youtube: 'rgba(255, 71, 87, 0.1)',
    facebook: 'rgba(66, 103, 178, 0.1)',
    instagram: 'rgba(232, 67, 147, 0.1)'
}

export default function UploadZone() {
    const [accounts, setAccounts] = useState([])
    const [loading, setLoading] = useState(true)
    const [openIndex, setOpenIndex] = useState(null)
    const [filter, setFilter] = useState('all')

    const stats = {
        pending: accounts.reduce((acc, a) => acc + (a.stats?.pending || 0), 0),
        today: accounts.reduce((acc, a) => acc + (a.stats?.published || 0), 0),
        need_setup: accounts.filter(a => !a.vault_id).length,
        total: accounts.reduce((acc, a) => acc + (a.stats?.published || 0) + (a.stats?.pending || 0), 0)
    }

    const loadData = async () => {
        try {
            const res = await fetchAccounts()
            setAccounts(res.data)
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }

    useEffect(() => { loadData() }, [])

    const handleAction = async (e, id) => {
        if(e) e.stopPropagation()
        try {
            await syncAccountNow(id)
            loadData()
        } catch (e) { console.error(e) }
    }

    return (
        <div className="space-y-6 animate-in">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white">Upload Zone</h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Video queue and Drive sync status per account</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={loadData} className="btn btn-o btn-sm">
                        <RefreshCw className="w-3.5 h-3.5" /> Check All
                    </button>
                    <Link to="/wizard" className="btn btn-g btn-sm">
                        <Wand2 className="w-3.5 h-3.5" /> Setup Wizard
                    </Link>
                </div>
            </div>

            {/* ── Stats Grid ────────────────────────────────────────── */}
            <div className="sg4">
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        {stats.pending}
                    </div>
                    <div className="sl text-[11px] uppercase tracking-wider font-bold">Pending Upload</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g3)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        {stats.today}
                    </div>
                    <div className="sl text-[11px] uppercase tracking-wider font-bold">Uploaded Today</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ color: 'var(--yellow)' }}>
                        {stats.need_setup}
                    </div>
                    <div className="sl text-[11px] uppercase tracking-wider font-bold">Need Setup</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g2)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        {stats.total}
                    </div>
                    <div className="sl text-[11px] uppercase tracking-wider font-bold">Total Videos</div>
                </div>
            </div>

            {/* ── Tabs ────────────────────────────────────────── */}
            <div className="tabs">
                <div className={clsx("tab", filter === 'all' && "on")} onClick={() => setFilter('all')}>All ({accounts.length})</div>
                <div className={clsx("tab", filter === 'setup' && "on")} onClick={() => setFilter('setup')}>⚠️ Not Setup ({stats.need_setup})</div>
                <div className={clsx("tab", filter === 'config' && "on")} onClick={() => setFilter('config')}>✅ Configured ({accounts.length - stats.need_setup})</div>
            </div>

            {/* ── List ────────────────────────────────────────── */}
            <div className="space-y-3">
                {accounts.map((account, idx) => {
                    const isOpen = openIndex === idx
                    const driveVids = account.drive_videos || []

                    return (
                        <div key={account.id} className="bg-[#0d1120] border border-white/5 rounded-2xl overflow-hidden transition-all hover:border-white/10">
                            <div 
                                className="flex items-center gap-4 p-4 cursor-pointer select-none"
                                onClick={() => setOpenIndex(isOpen ? null : idx)}
                            >
                                <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0" style={{ background: PLATFORM_BGS[account.platform] || 'var(--bg3)' }}>
                                    {PLATFORM_ICONS[account.platform] || '👤'}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-bold text-white text-[14px]">{account.name}</div>
                                    <div className="text-[11px] text-[#7a85b0] mt-0.5">
                                        {account.platform} · {driveVids.length} videos in Drive
                                    </div>
                                </div>
                                <div className="hidden md:flex items-center gap-3">
                                    <span className={clsx("badge", driveVids.length > 0 ? "b-purple" : "b-gray")}>
                                        {driveVids.length} videos
                                    </span>
                                    <span className={clsx("badge", account.status === 'active' ? "b-green" : "b-red")}>
                                        {account.status}
                                    </span>
                                    <button onClick={(e) => handleAction(e, account.id)} className="btn btn-o btn-xs">
                                        <RefreshCw className="w-3 h-3" /> Sync
                                    </button>
                                    <button className="btn btn-g btn-xs">
                                        Check
                                    </button>
                                </div>
                                <ChevronDown className={clsx("w-5 h-5 text-[#3d4666] transition-transform", isOpen && "rotate-180")} />
                            </div>

                            {isOpen && (
                                <div className="border-t border-white/5 bg-[#080b1460] animate-in">
                                    <div className="p-4 space-y-1">
                                        {driveVids.length > 0 ? driveVids.map((vid, vIdx) => (
                                            <div key={vIdx} className="flex items-center gap-3 py-2.5 border-b border-white/5 last:border-0">
                                                <FileVideo className="w-4 h-4 text-[#7a85b0]" />
                                                <div className="flex-1 min-w-0">
                                                    <div className="text-[13px] text-white truncate">{vid.name}</div>
                                                </div>
                                                <div className="text-[11px] text-[#3d4666] font-mono">{vid.size || (Math.floor(Math.random() * 50) + 50) + ' MB'}</div>
                                                <span className="badge b-purple !text-[9px] !px-2 !py-0.5">Queued</span>
                                                <button className="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-[#7a85b0] hover:text-white">
                                                    <Play className="w-3.5 h-3.5" />
                                                </button>
                                            </div>
                                        )) : (
                                            <div className="py-10 text-center space-y-3">
                                                <Folder className="w-10 h-10 text-white/5 mx-auto" />
                                                <p className="text-[12px] text-[#3d4666]">No videos found — Add videos to Drive folder</p>
                                                <Link to={`/workspace/${account.id}`} className="inline-flex items-center gap-1.5 text-[11px] text-[#6c5ce7] font-bold hover:underline">
                                                    Setup Drive Folder <ArrowRight size={12} />
                                                </Link>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
