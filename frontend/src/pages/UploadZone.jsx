import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api, { fetchAccounts, syncAccountNow, fetchVideos } from '../lib/api'
import { 
    ChevronDown, Folder, HardDrive, RefreshCw, CheckCircle2, 
    AlertCircle, FileVideo, Wand2, ArrowRight, Play, Copy, Calendar, RefreshCcw, Trash2, Image
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
    const [activeTab, setActiveTab] = useState('sync') // sync, vault
    const [accounts, setAccounts] = useState([])
    const [videos, setVideos] = useState([])
    const [loading, setLoading] = useState(true)
    const [openIndex, setOpenIndex] = useState(null)
    const [syncFilter, setSyncFilter] = useState('all')

    // Remix / Reschedule Form State
    const [remixVideoId, setRemixVideoId] = useState(null)
    const [remixAccountId, setRemixAccountId] = useState('')
    const [remixTime, setRemixTime] = useState('')
    const [scheduling, setScheduling] = useState(false)

    const stats = {
        pending: accounts.reduce((acc, a) => acc + (a.stats?.pending || 0), 0),
        today: accounts.reduce((acc, a) => acc + (a.stats?.published || 0), 0),
        need_setup: accounts.filter(a => !a.vault_id).length,
        total: accounts.reduce((acc, a) => acc + (a.stats?.published || 0) + (a.stats?.pending || 0), 0)
    }

    const loadData = async () => {
        try {
            setLoading(true)
            const [accRes, vidRes] = await Promise.all([
                fetchAccounts(),
                fetchVideos()
            ])
            setAccounts(accRes.data || [])
            setVideos(vidRes.data || [])
        } catch (e) { 
            console.error(e) 
        } finally { 
            setLoading(false) 
        }
    }

    useEffect(() => { loadData() }, [])

    const handleAction = async (e, id) => {
        if(e) e.stopPropagation()
        try {
            await syncAccountNow(id)
            loadData()
        } catch (e) { console.error(e) }
    }

    const handleRemixSubmit = async (e, videoId) => {
        e.preventDefault()
        if (!remixAccountId || !remixTime) return
        setScheduling(true)
        try {
            const payload = {
                video_id: videoId,
                account_id: remixAccountId,
                scheduled_time: new Date(remixTime).toISOString(),
                add_watermark: true,
                auto_comment: false
            }
            await api.post('/schedules/', payload)
            alert('Remixed video scheduled successfully!')
            setRemixVideoId(null)
            setRemixAccountId('')
            setRemixTime('')
            loadData()
        } catch (err) {
            console.error(err)
            alert('Failed to schedule remix.')
        } finally {
            setScheduling(false)
        }
    }

    const handleDeleteVideo = async (id) => {
        if (!window.confirm('Are you sure you want to permanently delete this video from the Vault?')) return
        try {
            await api.delete(`/videos/${id}`)
            alert('Video deleted successfully!')
            loadData()
        } catch (e) {
            console.error(e)
            alert('Failed to delete video. Please check backend connection.')
        }
    }

    const filteredAccounts = accounts.filter(a => {
        if (syncFilter === 'setup') return !a.vault_id
        if (syncFilter === 'config') return !!a.vault_id
        return true
    })

    return (
        <div className="space-y-6 animate-in max-w-6xl mx-auto">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Folder className="text-[#6c5ce7]" /> Upload & Assets Center
                    </h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Manage video queue, Google Drive syncs, and persistent media assets</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={loadData} className="btn btn-o btn-sm">
                        <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Refresh Assets
                    </button>
                    <Link to="/wizard" className="btn btn-g btn-sm">
                        <Wand2 className="w-3.5 h-3.5 mr-1.5" /> Setup Wizard
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
                        {videos.length}
                    </div>
                    <div className="sl text-[11px] uppercase tracking-wider font-bold">Vault Assets</div>
                </div>
            </div>

            {/* ── Tabs Navigation ──────────────────────────────────── */}
            <div className="flex gap-2 border-b border-white/5 pb-2">
                <button
                    onClick={() => setActiveTab('sync')}
                    className={clsx(
                        "flex items-center gap-2 px-4 py-2 font-medium rounded-xl transition-all text-[13px]",
                        activeTab === 'sync' 
                            ? "bg-[#6c5ce724] text-white border border-[#6c5ce733]" 
                            : "text-[#7a85b0] hover:text-white hover:bg-white/[0.02]"
                    )}
                >
                    <RefreshCw size={14} /> 🔄 Channel Folders & Sync
                </button>
                <button
                    onClick={() => setActiveTab('vault')}
                    className={clsx(
                        "flex items-center gap-2 px-4 py-2 font-medium rounded-xl transition-all text-[13px]",
                        activeTab === 'vault' 
                            ? "bg-[#6c5ce724] text-white border border-[#6c5ce733]" 
                            : "text-[#7a85b0] hover:text-white hover:bg-white/[0.02]"
                    )}
                >
                    <Folder size={14} /> 📁 Persistent Assets Vault ({videos.length})
                </button>
            </div>

            {/* ── TAB 1: Channel Folders & Sync ─────────────────────── */}
            {activeTab === 'sync' && (
                <div className="space-y-4">
                    {/* Tabs */}
                    <div className="tabs">
                        <div className={clsx("tab", syncFilter === 'all' && "on")} onClick={() => setSyncFilter('all')}>All ({accounts.length})</div>
                        <div className={clsx("tab", syncFilter === 'setup' && "on")} onClick={() => setSyncFilter('setup')}>⚠️ Not Setup ({stats.need_setup})</div>
                        <div className={clsx("tab", syncFilter === 'config' && "on")} onClick={() => setSyncFilter('config')}>✅ Configured ({accounts.length - stats.need_setup})</div>
                    </div>

                    <div className="space-y-3">
                        {filteredAccounts.map((account, idx) => {
                            const isOpen = openIndex === idx
                            const driveVids = account.drive_videos || []

                            return (
                                <div key={account.id} className="bg-[#0d1120] border border-white/5 rounded-2xl overflow-hidden transition-all hover:border-white/10">
                                    <div 
                                        className="flex items-center gap-4 p-4 cursor-pointer select-none"
                                        onClick={() => setOpenIndex(isOpen ? null : idx)}
                                    >
                                        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0" style={{ background: PLATFORM_BGS[account.platform] || 'var(--bg3)' }}>
                                            {account.platform === 'youtube' && <Play className="w-5 h-5 text-red-500" />}
                                            {account.platform === 'facebook' && <span className="text-blue-500 font-bold text-lg">f</span>}
                                            {account.platform === 'instagram' && <span className="text-pink-500 font-bold text-lg">◉</span>}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-bold text-white text-[14px]">{account.channel_name || account.name}</div>
                                            <div className="text-[11px] text-[#7a85b0] mt-0.5">
                                                {account.platform} · {driveVids.length} videos found in folder
                                            </div>
                                        </div>
                                        <div className="hidden md:flex items-center gap-3">
                                            <span className={clsx("badge", driveVids.length > 0 ? "b-purple" : "b-gray")}>
                                                {driveVids.length} files
                                            </span>
                                            <span className={clsx("badge", account.status === 'active' ? "b-green" : "b-red")}>
                                                {account.status}
                                            </span>
                                            <button onClick={(e) => handleAction(e, account.id)} className="btn btn-o btn-xs">
                                                <RefreshCw className="w-3 h-3 mr-1" /> Sync
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
                                                        <div className="text-[11px] text-[#3d4666] font-mono">{vid.size || 'Queued'}</div>
                                                        <span className="badge b-purple !text-[9px] !px-2 !py-0.5">Ready to publish</span>
                                                    </div>
                                                )) : (
                                                    <div className="py-10 text-center space-y-3">
                                                        <Folder className="w-10 h-10 text-white/5 mx-auto" />
                                                        <p className="text-[12px] text-[#3d4666]">No videos found — Add files to your Drive folder</p>
                                                        <Link to={`/workspace/${account.id}`} className="inline-flex items-center gap-1.5 text-[11px] text-[#6c5ce7] font-bold hover:underline">
                                                            Configure Drive Connection <ArrowRight size={12} />
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
            )}

            {/* ── TAB 2: Persistent Assets Vault & Remix Engine ─────── */}
            {activeTab === 'vault' && (
                <div className="space-y-6">
                    {videos.length === 0 ? (
                        <div className="bg-[#0d1120] border border-dashed border-white/10 rounded-[20px] p-12 text-center flex flex-col items-center justify-center">
                            <Folder size={40} className="text-[#3d4666] mb-3" />
                            <div className="text-[14px] text-white font-bold">Your Asset Vault is empty.</div>
                            <div className="text-[12px] text-[#7a85b0] max-w-sm mt-1">
                                Sync folders in the "Channel Folders" tab to download, render, and persist source videos in the Vault.
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {videos.map(video => (
                                <div key={video.id} className="bg-[#0d1120] border border-white/5 rounded-2xl p-5 flex flex-col justify-between hover:border-white/10 transition-all relative group overflow-hidden">
                                    <div className="absolute top-0 left-0 w-1.5 h-full bg-[#6c5ce7]" />
                                    
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-start">
                                            <div className="flex items-start gap-3">
                                                <div className={clsx(
                                                    "w-10 h-10 rounded-xl flex items-center justify-center shrink-0",
                                                    video.media_type === 'image' ? "bg-[#00cec91a] text-[#00cec9]" : "bg-[#6c5ce71a] text-[#6c5ce7]"
                                                )}>
                                                    {video.media_type === 'image' ? <Image size={20} /> : <FileVideo size={20} />}
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h4 className="text-[14px] font-bold text-white line-clamp-1" title={video.ai_title || video.original_filename}>
                                                            {video.ai_title || video.original_filename}
                                                        </h4>
                                                        <span className={clsx(
                                                            "badge !text-[9px] !px-1.5 !py-0.5",
                                                            video.media_type === 'image' ? "!bg-[#00cec920] !text-[#00cec9] !border-[#00cec930]" : "b-purple"
                                                        )}>
                                                            {video.media_type === 'image' ? 'Photo' : 'Video'}
                                                        </span>
                                                    </div>
                                                    <span className="text-[10px] text-[#3d4666] font-mono block mt-0.5">ID: {video.id.substring(0,8)}...</span>
                                                </div>
                                            </div>

                                            <button 
                                                onClick={() => handleDeleteVideo(video.id)}
                                                className="p-1.5 text-red-400 hover:bg-red-500/10 hover:text-red-300 rounded-lg transition-all"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>

                                        <div className="space-y-2">
                                            <div className="bg-[#131829] rounded-xl p-3 border border-white/5 text-[11.5px] text-[#7a85b0]">
                                                <span className="font-bold text-white block mb-0.5">Original Filename:</span>
                                                {video.original_filename}
                                            </div>
                                            
                                            {video.ai_description && (
                                                <div className="text-[11.5px] text-[#7a85b0] line-clamp-2" title={video.ai_description}>
                                                    <span className="font-bold text-white mr-1">AI Description:</span>
                                                    {video.ai_description}
                                                </div>
                                            )}
                                        </div>

                                        {/* Dynamic Remix Drawer */}
                                        {remixVideoId === video.id ? (
                                            <form onSubmit={(e) => handleRemixSubmit(e, video.id)} className="bg-[#131829] rounded-xl p-4 border border-[#6c5ce733] space-y-3 animate-in">
                                                <div className="text-[11.5px] font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                                                    <RefreshCcw size={12} className="text-[#6c5ce7]" /> A/B Remix Schedule
                                                </div>
                                                
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                    <div>
                                                        <label className="text-[9.5px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">Target Account</label>
                                                        <select
                                                            required
                                                            value={remixAccountId}
                                                            onChange={(e) => setRemixAccountId(e.target.value)}
                                                            className="w-full bg-[#0d1120] border border-white/10 rounded-lg p-2 text-[12px] text-white outline-none"
                                                        >
                                                            <option value="">-- Select Channel --</option>
                                                            {accounts.filter(a => a.status === 'active').map(acc => (
                                                                <option key={acc.id} value={acc.id}>
                                                                    {acc.platform.toUpperCase()} - {acc.channel_name}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label className="text-[9.5px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">Schedule Time</label>
                                                        <input
                                                            required
                                                            type="datetime-local"
                                                            value={remixTime}
                                                            onChange={(e) => setRemixTime(e.target.value)}
                                                            className="w-full bg-[#0d1120] border border-white/10 rounded-lg p-1.5 text-[12px] text-white outline-none"
                                                        />
                                                    </div>
                                                </div>

                                                <div className="flex gap-2 pt-1">
                                                    <button 
                                                        type="submit" 
                                                        disabled={scheduling}
                                                        className="flex-1 btn btn-g btn-xs justify-center py-2"
                                                    >
                                                        {scheduling ? 'Scheduling...' : 'Confirm Re-schedule'}
                                                    </button>
                                                    <button 
                                                        type="button" 
                                                        onClick={() => setRemixVideoId(null)}
                                                        className="btn btn-o btn-xs"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </form>
                                        ) : (
                                            <button 
                                                onClick={() => {
                                                    setRemixVideoId(video.id)
                                                    setRemixAccountId('')
                                                    setRemixTime('')
                                                }}
                                                className="w-full btn btn-o btn-sm gap-2 justify-center py-2.5 hover:text-[#6c5ce7] hover:border-[#6c5ce7]"
                                            >
                                                <RefreshCcw size={14} /> 🔄 Remix & Re-schedule (A/B Test)
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
