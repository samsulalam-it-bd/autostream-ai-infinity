import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
    fetchAccounts, deleteAccount, updateAccount, syncAccountNow, 
    instantPost, triggerPipeline, listApiKeys, clearQueueByAccounts
} from '../lib/api'
import { 
    Youtube, Facebook, Instagram, Trash2, Edit2, RefreshCw, 
    Zap, Play, MoreVertical, X, Check, AlertTriangle, ShieldCheck, Plus, ExternalLink,
    Eraser, Settings
} from 'lucide-react'
import clsx from 'clsx'

const PLATFORM_CONFIG = {
    youtube: { icon: Youtube, color: 'var(--yt)', bg: 'rgba(255, 71, 87, 0.1)' },
    facebook: { icon: Facebook, color: 'var(--fb)', bg: 'rgba(66, 103, 178, 0.1)' },
    instagram: { icon: Instagram, color: 'var(--ig)', bg: 'rgba(232, 67, 147, 0.1)' }
}

export default function Accounts() {
    const navigate = useNavigate()
    const [accounts, setAccounts] = useState([])
    const [vaultKeys, setVaultKeys] = useState([])
    const [filter, setFilter] = useState('all')
    const [loading, setLoading] = useState(true)
    const [activeOverlay, setActiveOverlay] = useState(null)
    const [showAddModal, setShowAddModal] = useState(false)
    const [showSettingsModal, setShowSettingsModal] = useState(null)
    const [syncingAll, setSyncingAll] = useState(false)
    const [now, setNow] = useState(new Date())

    useEffect(() => {
        const interval = setInterval(() => {
            setNow(new Date())
        }, 1000)
        return () => clearInterval(interval)
    }, [])

    const getAccountCountdown = (account) => {
        if (!account.next_publish_iso) return null
        
        const nextTime = new Date(account.next_publish_iso)
        const diffMs = nextTime.getTime() - now.getTime()
        
        if (diffMs <= 0) return "Publishing now..."
        
        const secs = Math.floor(diffMs / 1000)
        const hours = Math.floor(secs / 3600)
        const mins = Math.floor((secs % 3600) / 60)
        const remainingSecs = secs % 60
        
        return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(remainingSecs).padStart(2, '0')}`
    }

    // Auto-comment & AI Time Predictor states
    const [editAutoComment, setEditAutoComment] = useState(false)
    const [editCommentText, setEditCommentText] = useState('')
    const [editAiTimePredictor, setEditAiTimePredictor] = useState(false)
    const [editOptimalSlots, setEditOptimalSlots] = useState({})
    const [savingSettings, setSavingSettings] = useState(false)

    const handleSaveSettings = async (accountId) => {
        setSavingSettings(true)
        try {
            await updateAccount(accountId, {
                auto_comment: editAutoComment,
                auto_comment_text: editCommentText,
                ai_time_predictor: editAiTimePredictor,
                optimal_slots: editOptimalSlots
            })
            alert('✅ Settings saved successfully!')
            setActiveOverlay(null)
            setShowSettingsModal(null)
            loadAccounts()
        } catch (e) {
            console.error(e)
            alert('Failed to save settings')
        } finally {
            setSavingSettings(false)
        }
    }

    const loadAccounts = async () => {
        setLoading(true)
        try {
            const res = await fetchAccounts(filter === 'all' ? null : filter)
            setAccounts(res.data)
        } catch (e) { console.error(e) }
        finally { 
            // Small delay to make it feel real
            setTimeout(() => setLoading(false), 500)
        }
    }

    const loadVaultKeys = async () => {
        try {
            const res = await listApiKeys()
            setVaultKeys(res.data)
        } catch (e) { console.error(e) }
    }

    useEffect(() => { loadAccounts() }, [filter])
    useEffect(() => { loadVaultKeys() }, [])

    const handleDelete = async (id, name) => {
        if (!window.confirm(`⚠️ ARE YOU SURE?\n\nYou are about to delete "${name}". This will stop all active automations for this channel.`)) return
        try {
            await deleteAccount(id)
            setAccounts(accounts.filter(a => a.id !== id))
            setActiveOverlay(null)
            setShowSettingsModal(null)
        } catch (e) { alert('Failed to delete') }
    }

    const handleAction = async (action, account) => {
        try {
            if (action === 'sync') {
                await syncAccountNow(account.id)
                alert('🔄 Channel sync triggered successfully!')
            }
            if (action === 'run' || action === 'instant') {
                const res = await instantPost(account.id)
                alert(`⚡ Instant post triggered successfully!\n\nTask ID: ${res.data.task_id || 'N/A'}`)
                setActiveOverlay(null)
            }
            loadAccounts()
        } catch (e) {
            console.error(e)
            const errMsg = e.response?.data?.detail || e.message || 'Unknown error occurred'
            alert(`❌ Action Failed:\n\n${errMsg}`)
        }
    }

    const handleClearQueue = async (account) => {
        if (!window.confirm(`🧹 Clear Pending Queue?\n\nYou are about to cancel all scheduled/pending uploads for "${account.channel_name}". Published videos will not be affected.`)) return
        try {
            const res = await clearQueueByAccounts([account.id])
            alert(`✅ ${res.data.message || 'Queue cleared successfully!'}`)
            loadAccounts()
            setActiveOverlay(null)
            setShowSettingsModal(null)
        } catch (e) {
            console.error(e)
            alert('Failed to clear queue')
        }
    }


    const handleSyncAll = async () => {
        if (accounts.length === 0) return
        setSyncingAll(true)
        try {
            await Promise.all(accounts.map(a => syncAccountNow(a.id)))
            alert(`✅ Sync triggered for ${accounts.length} channels!`)
            loadAccounts()
        } catch (e) { 
            console.error(e)
            alert('Sync All failed for some accounts')
        } finally {
            setSyncingAll(false)
        }
    }

    const initiateOAuth = async (platform, vaultId = null) => {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
        const endpoint = platform === 'youtube' ? '/api/v1/accounts/oauth/google/init' : '/api/v1/accounts/oauth/meta/init'
        const url = new URL(endpoint, API_BASE || window.location.origin)
        if (vaultId) url.searchParams.append('vault_id', vaultId)
        
        try {
            const res = await fetch(url.toString())
            const data = await res.json()
            if (data.auth_url) window.location.href = data.auth_url
        } catch (e) { alert('OAuth failed to start') }
    }

    return (
        <div className="space-y-6 animate-in">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white">Connected Channels</h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Manage your social media accounts and publishing settings</p>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={handleSyncAll} 
                        disabled={syncingAll || accounts.length === 0}
                        className={clsx("btn btn-o btn-sm", syncingAll && "opacity-50")}
                    >
                        <RefreshCw className={clsx("w-3.5 h-3.5", syncingAll && "animate-spin")} /> 
                        {syncingAll ? 'Syncing...' : 'Sync All Channels'}
                    </button>
                    <button onClick={loadAccounts} className="btn btn-o btn-sm">
                        <RefreshCw className={clsx("w-3.5 h-3.5", loading && "animate-spin")} /> Refresh UI
                    </button>
                    <button onClick={() => setShowAddModal(true)} className="btn btn-g btn-sm">
                        <Plus className="w-3.5 h-3.5" /> Add Account
                    </button>
                </div>
            </div>

            {/* ── Tabs & Status ──────────────────────────────────── */}
            <div className="flex items-center justify-between">
                <div className="tabs">
                    {['all', 'youtube', 'facebook', 'instagram'].map(f => (
                        <div 
                            key={f}
                            className={clsx("tab", filter === f && "on")}
                            onClick={() => setFilter(f)}
                        >
                            <span className="capitalize">{f}</span>
                            <span className="ml-1.5 opacity-50 text-[11px]">
                                ({f === 'all' ? accounts.length : accounts.filter(a => a.platform === f).length})
                            </span>
                        </div>
                    ))}
                </div>
                <div className="flex items-center gap-3">
                    <span className="badge b-green">● {accounts.filter(a => a.status === 'active').length} Active</span>
                    <span className="badge b-red">● {accounts.filter(a => a.status === 'expired').length} Expired</span>
                </div>
            </div>

            {/* ── Grid ─────────────────────────────────────────── */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {accounts.map(account => {
                    const cfg = PLATFORM_CONFIG[account.platform] || { icon: ShieldCheck, color: 'var(--p)', bg: 'var(--bg3)' }
                    const Icon = cfg.icon
                    const isOverlayActive = activeOverlay?.id === account.id

                    return (
                        <div key={account.id} className="cc group relative overflow-hidden bg-[#0d1120] border border-white/5 rounded-[20px] transition-all hover:-translate-y-1 hover:shadow-2xl">
                            <div className="h-1" style={{ background: cfg.color }}></div>
                            
                            <div className="p-5">
                                {/* Top Info */}
                                <div className="flex items-start gap-3 mb-4">
                                    <div className="relative w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0" style={{ background: cfg.bg }}>
                                        <Icon className="w-6 h-6" style={{ color: cfg.color }} />
                                        <div className={clsx(
                                            "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[#0d1120]",
                                            account.status === 'active' ? "bg-[#00b894]" : "bg-[#d63031]"
                                        )} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-bold text-white text-[15px] truncate">{account.channel_name}</div>
                                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                                            <span className={clsx("badge text-[9px] py-0.5 px-1.5 font-bold shrink-0 flex items-center gap-1", ((account.stats?.pending || 0) > 0 || (account.stats?.queue || 0) > 0) ? "b-green" : "b-red")}>
                                                {((account.stats?.pending || 0) > 0 || (account.stats?.queue || 0) > 0) ? "✅ Configured" : "⚠️ Not Setup"}
                                            </span>
                                            <span className="text-[10px] text-[#7a85b0] uppercase tracking-wider font-semibold">
                                                {account.platform}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <div className="text-[13px] font-bold" style={{ background: cfg.color, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                                            {account.subscriber_count || '0'}
                                        </div>
                                        <div className="text-[9px] text-[#3d4666] uppercase font-bold tracking-wider">
                                            {account.platform.toLowerCase() === 'youtube' ? 'Subscribers' : 'Followers'}
                                        </div>
                                    </div>
                                </div>

                                {/* Stats Grid */}
                                <div className="grid grid-cols-4 gap-2 mb-4">
                                    {[
                                        { label: 'Published', val: account.stats?.published || 0, grad: 'var(--g3)' },
                                        { label: 'Pending', val: account.stats?.pending || 0, grad: 'var(--g4)' },
                                        { label: 'Failed', val: account.stats?.failed || 0, color: account.stats?.failed > 0 ? '#d63031' : '#3d4666' },
                                        { label: 'Queue', val: account.stats?.queue || 0, grad: 'var(--g2)' }
                                    ].map((s, i) => (
                                        <div key={i} className="bg-[#131829] rounded-xl p-2 text-center">
                                            <div className="text-[14px] font-bold" style={s.grad ? { background: s.grad, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' } : { color: s.color }}>
                                                {s.val}
                                            </div>
                                            <div className="text-[9px] text-[#3d4666] font-bold uppercase">{s.label}</div>
                                        </div>
                                    ))}
                                </div>

                                <div className="bg-[#131829] rounded-xl py-2 px-4 mb-4 text-center text-[12px] text-[#7a85b0] flex items-center justify-center gap-1.5 flex-wrap">
                                    <span>⏰ Next:</span>
                                    <span className="font-bold" style={{ color: cfg.color }}>
                                        {account.next_publish_time ? (
                                            <span className="flex items-center gap-1.5">
                                                <span>{account.next_publish_time}</span>
                                                {getAccountCountdown(account) && (
                                                    <span className="font-mono text-[10px] bg-white/5 border border-white/5 text-[#00cec9] py-0.5 px-1.5 rounded-md font-medium tracking-wide">
                                                        ({getAccountCountdown(account)})
                                                    </span>
                                                )}
                                            </span>
                                        ) : (
                                            'No Schedule'
                                        )}
                                    </span>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-1.5">
                                    <button onClick={() => handleAction('run', account)} className="flex-1 bg-[#131829] hover:bg-[#00b8941a] border border-white/5 hover:border-[#00b894] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#00b894]" title="Run Now">
                                        <Play className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => handleAction('sync', account)} className="flex-1 bg-[#131829] hover:bg-[#00cec91a] border border-white/5 hover:border-[#00cec9] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#00cec9]" title="Sync Drive">
                                        <RefreshCw className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => navigate(`/workspace/${account.id}`)} className="flex-1 bg-[#131829] hover:bg-[#6c5ce71a] border border-white/5 hover:border-[#6c5ce7] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#6c5ce7]" title="Setup Wizard">
                                        <Edit2 className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => {
                                        setEditAutoComment(account.auto_comment || false)
                                        setEditCommentText(account.auto_comment_text || '')
                                        setEditAiTimePredictor(account.ai_time_predictor || false)
                                        setEditOptimalSlots(account.optimal_slots || {})
                                        setShowSettingsModal(account)
                                    }} className="flex-1 bg-[#131829] hover:bg-[#a29bfe1a] border border-white/5 hover:border-[#a29bfe] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#a29bfe]" title="Channel Settings">
                                        <Settings className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => setActiveOverlay({ type: 'inst', id: account.id })} className="flex-1 bg-[#131829] hover:bg-[#fdcb6e1a] border border-white/5 hover:border-[#fdcb6e] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#fdcb6e]" title="Instant Post">
                                        <Zap className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => setActiveOverlay({ type: 'clear', id: account.id })} className="flex-1 bg-[#131829] hover:bg-[#ff76751a] border border-white/5 hover:border-[#ff7675] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#ff7675]" title="Clear Queue">
                                        <Eraser className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => handleDelete(account.id, account.channel_name)} className="flex-1 bg-[#131829] hover:bg-[#d630311a] border border-white/5 hover:border-[#d63031] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#d63031]" title="Delete">
                                        <Trash2 className="w-4 h-4 mx-auto" />
                                    </button>
                                </div>
                            </div>

                            {/* ── Overlays ─────────────────────────────────── */}
                            {isOverlayActive && (
                                <div className="absolute inset-0 z-10 bg-[#080b14f0] backdrop-blur-md flex flex-col items-center justify-center p-6 text-center animate-in">
                                    <button onClick={() => setActiveOverlay(null)} className="absolute top-4 right-4 p-1 text-[#3d4666] hover:text-white transition-colors">
                                        <X size={18} />
                                    </button>

                                    {activeOverlay.type === 'del' && (
                                        <>
                                            <div className="w-14 h-14 rounded-full bg-[#d630311a] flex items-center justify-center text-[#d63031] mb-4">
                                                <AlertTriangle size={28} />
                                            </div>
                                            <div className="text-[16px] font-bold text-white mb-2">Delete Channel?</div>
                                            <div className="text-[12px] text-[#7a85b0] mb-6 px-4">
                                                "{account.channel_name}" will be removed. All pending schedules will be cancelled.
                                            </div>
                                            <div className="flex gap-2 w-full">
                                                <button onClick={() => setActiveOverlay(null)} className="flex-1 py-2 rounded-xl bg-[#131829] text-[#7a85b0] font-bold text-[13px] border border-white/5">Cancel</button>
                                                <button onClick={() => handleDelete(account.id, account.channel_name)} className="flex-1 py-2 rounded-xl bg-[#d6303120] text-[#d63031] font-bold text-[13px] border border-[#d6303140] hover:bg-[#d63031]">Yes, Delete</button>
                                            </div>
                                        </>
                                    )}

                                    {activeOverlay.type === 'inst' && (
                                        <>
                                            <div className="w-14 h-14 rounded-full bg-[#fdcb6e1a] flex items-center justify-center text-[#fdcb6e] mb-4">
                                                <Zap size={28} />
                                            </div>
                                            <div className="text-[16px] font-bold text-white mb-2">Instant Post</div>
                                            <div className="text-[12px] text-[#7a85b0] mb-6">
                                                Skip the queue and publish the next video from "{account.channel_name}" immediately?
                                            </div>
                                            <div className="flex gap-2 w-full">
                                                <button onClick={() => setActiveOverlay(null)} className="flex-1 py-2 rounded-xl bg-[#131829] text-[#7a85b0] font-bold text-[13px] border border-white/5">Cancel</button>
                                                <button onClick={() => handleAction('instant', account)} className="flex-1 py-2 rounded-xl bg-gradient-to-r from-[#fdcb6e] to-[#e17055] text-white font-bold text-[13px]">⚡ Post Now</button>
                                            </div>
                                        </>
                                    )}

                                    {activeOverlay.type === 'clear' && (
                                        <>
                                            <div className="w-14 h-14 rounded-full bg-[#ff76751a] flex items-center justify-center text-[#ff7675] mb-4">
                                                <Eraser size={28} />
                                            </div>
                                            <div className="text-[16px] font-bold text-white mb-2">Clear Queue</div>
                                            <div className="text-[12px] text-[#7a85b0] mb-6 px-4">
                                                Cancel and delete all pending/scheduled uploads for "{account.channel_name}"? Published videos will not be affected.
                                            </div>
                                            <div className="flex gap-2 w-full">
                                                <button onClick={() => setActiveOverlay(null)} className="flex-1 py-2 rounded-xl bg-[#131829] text-[#7a85b0] font-bold text-[13px] border border-white/5">Cancel</button>
                                                <button onClick={() => handleClearQueue(account)} className="flex-1 py-2 rounded-xl bg-gradient-to-r from-[#ff7675] to-[#d63031] text-white font-bold text-[13px]">🧹 Clear Queue</button>
                                            </div>
                                        </>
                                    )}

                                </div>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* ── Add Account Modal ─────────────────────────────────── */}
            {showAddModal && (
                <div 
                    className="fixed inset-0 z-[100] grid place-items-start justify-center bg-[#080b14fb] backdrop-blur-2xl overflow-y-auto px-4 py-10 sm:py-20"
                    style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh' }}
                >
                    <div className="bg-[#0d1120] border border-white/10 w-full max-w-5xl rounded-[32px] overflow-hidden shadow-2xl flex flex-col mb-20 relative min-h-[600px]">
                        <div className="p-6 sm:p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                            <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-3">
                                <div className="p-2 bg-[#6c5ce720] rounded-xl text-[#6c5ce7]">
                                    <Plus size={24} />
                                </div>
                                Connect New Account
                            </h2>
                            <button onClick={() => setShowAddModal(false)} className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-[#7a85b0] hover:text-white hover:bg-white/10 transition-all">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-8 overflow-y-auto flex-1 custom-scrollbar">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                                {/* Left Side: Steps & Platform Selection */}
                                <div className="space-y-8">
                                    <div className="p-6 bg-gradient-to-br from-[#6c5ce710] to-transparent border border-[#6c5ce720] rounded-[24px] space-y-4">
                                        <h3 className="text-[#a29bfe] font-bold flex items-center gap-2">
                                            <ShieldCheck size={18} /> Connection Guide:
                                        </h3>
                                        <ul className="space-y-3">
                                            {[
                                                "Pick your platform (YouTube or Meta).",
                                                "Sign in and grant permissions.",
                                                "The system will sync your channel data.",
                                                "Automation starts immediately after sync."
                                            ].map((txt, i) => (
                                                <li key={i} className="flex gap-3 text-[12px] text-[#7a85b0]">
                                                    <span className="w-5 h-5 rounded-full bg-[#6c5ce720] flex items-center justify-center text-[#6c5ce7] text-[10px] font-bold shrink-0">{i+1}</span>
                                                    {txt}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em]">1. Select Platform</label>
                                            <span className="text-[10px] text-[#00b894] font-bold bg-[#00b89410] px-2 py-0.5 rounded-full">RECOMMENDED</span>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            {[
                                                { id: 'youtube', label: 'YouTube / Google', icon: Youtube, color: '#ff4757', desc: 'Sync videos via Drive' },
                                                { id: 'facebook', label: 'Meta (FB / IG)', icon: Facebook, color: '#3498db', desc: 'Post to Pages & IG' }
                                            ].map(p => (
                                                <button 
                                                    key={p.id}
                                                    onClick={() => initiateOAuth(p.id)}
                                                    className="group relative flex flex-col items-center justify-center gap-3 p-8 rounded-[24px] bg-[#131829] border border-white/5 hover:border-[#6c5ce7] hover:bg-[#6c5ce708] transition-all text-center"
                                                >
                                                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-4xl bg-white/5 group-hover:scale-110 transition-transform" style={{ color: p.color }}>
                                                        <p.icon size={40} />
                                                    </div>
                                                    <div>
                                                        <div className="font-black text-white text-[16px]">{p.label}</div>
                                                        <div className="text-[11px] text-[#3d4666] font-bold uppercase tracking-wider mt-1">{p.desc}</div>
                                                    </div>
                                                    <div className="mt-4 px-4 py-1.5 rounded-full bg-white/5 text-[11px] text-[#7a85b0] group-hover:bg-[#6c5ce7] group-hover:text-white transition-all font-bold">Connect Now</div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Right Side: Advanced Vault Selection */}
                                <div className="space-y-6 border-l border-white/5 pl-10 hidden lg:block">
                                    <div className="flex items-center justify-between">
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em]">2. Specific Project</label>
                                        <span className="text-[9px] bg-[#6c5ce720] text-[#6c5ce7] px-2 py-0.5 rounded-full font-bold">MANUAL OVERRIDE</span>
                                    </div>
                                    <p className="text-[11px] text-[#7a85b0] leading-relaxed">
                                        Optional: Choose a specific API project from your Vault if you want to use a particular quota limit.
                                    </p>
                                    <div className="max-h-[350px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                                        {vaultKeys.length > 0 ? vaultKeys.filter(k => k.service_name !== 'gemini').map(k => (
                                            <div 
                                                key={k.id} 
                                                onClick={() => initiateOAuth(k.service_name, k.id)}
                                                className="p-4 rounded-2xl bg-[#131829] border border-white/5 hover:border-[#6c5ce7] cursor-pointer group transition-all"
                                            >
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="text-[13px] font-bold text-white group-hover:text-[#6c5ce7] transition-colors">{k.project_name}</span>
                                                    <span className="text-[9px] text-[#3d4666] font-bold uppercase px-2 py-0.5 bg-white/5 rounded-md">{k.service_name}</span>
                                                </div>
                                                <div className="flex items-center justify-between text-[10px]">
                                                    <span className="text-[#3d4666]">Quota Status</span>
                                                    <span className={clsx("font-bold", k.is_locked ? "text-[#d63031]" : "text-[#00b894]")}>
                                                        {Math.round((k.daily_usage / k.daily_limit) * 100)}% Used
                                                    </span>
                                                </div>
                                            </div>
                                        )) : (
                                            <div className="text-center py-20 bg-white/2 rounded-[30px] border border-dashed border-white/5">
                                                <ShieldCheck size={40} className="mx-auto mb-3 text-[#131829]" />
                                                <div className="text-[11px] text-[#3d4666] font-bold uppercase tracking-widest">No Projects in Vault</div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="p-8 bg-[#131829]/50 border-t border-white/5 flex justify-end">
                            <button onClick={() => setShowAddModal(false)} className="px-8 py-3 rounded-2xl bg-[#131829] text-[#7a85b0] font-bold">Close</button>
                        </div>
                    </div>
                </div>
            )}
        
            {/* ── Settings Modal ─────────────────────────────────── */}
            {showSettingsModal && (
                <div 
                    className="fixed inset-0 z-[100] grid place-items-center justify-center bg-[#080b14fb] backdrop-blur-2xl px-4 py-10"
                    style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh' }}
                >
                    <div className="bg-[#0d1120] border border-white/10 w-full max-w-2xl rounded-[32px] overflow-hidden shadow-2xl flex flex-col relative animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                            <h2 className="text-xl font-black text-white flex items-center gap-3">
                                <div className="p-2 bg-[#a29bfe20] rounded-xl text-[#a29bfe]">
                                    <Settings size={24} />
                                </div>
                                Channel Settings
                            </h2>
                            <button onClick={() => setShowSettingsModal(null)} className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-[#7a85b0] hover:text-white hover:bg-white/10 transition-all">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 sm:p-8 overflow-y-auto max-h-[70vh] custom-scrollbar space-y-8">
                            <div className="text-[14px] text-[#7a85b0] bg-[#6c5ce710] p-4 rounded-2xl border border-[#6c5ce720]">
                                Configure automated branding and Call-to-Actions for <strong className="text-white">"{showSettingsModal.channel_name}"</strong>.
                            </div>

                            {/* Auto-comment toggle */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between w-full p-5 rounded-2xl bg-white/[0.02] border border-white/5 transition-all hover:bg-white/[0.04] gap-4">
                                <div className="text-left">
                                    <div className="text-[15px] font-bold text-white flex items-center gap-2">
                                        💬 Auto-Comment on Post
                                    </div>
                                    <div className="text-[12px] text-[#7a85b0] mt-1">Post a custom first comment immediately after uploading.</div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer shrink-0">
                                    <input 
                                        type="checkbox" 
                                        checked={editAutoComment} 
                                        onChange={(e) => setEditAutoComment(e.target.checked)} 
                                        className="sr-only peer" 
                                    />
                                    <div className="w-12 h-7 bg-[#1b223c] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#7a85b0] after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-[#6c5ce7] peer-checked:after:bg-white"></div>
                                </label>
                            </div>

                            {/* Auto-comment text area */}
                            {editAutoComment && (
                                <div className="w-full space-y-2 text-left animate-in fade-in slide-in-from-top-4">
                                    <div className="text-[12px] text-[#a29bfe] font-bold uppercase tracking-wider pl-1">Comment Message</div>
                                    <textarea
                                        value={editCommentText}
                                        onChange={(e) => setEditCommentText(e.target.value)}
                                        placeholder="Write your Call-to-Action comment here... Supports emojis! 🚀"
                                        rows={4}
                                        className="w-full p-4 rounded-2xl bg-[#080b14] border border-white/10 text-white text-[14px] placeholder:text-[#3d4666] focus:outline-none focus:border-[#6c5ce7] transition-all resize-none custom-scrollbar shadow-inner"
                                    />
                                </div>
                            )}

                            <div className="h-px w-full bg-white/5"></div>

                            {/* AI Time Optimizer Toggle */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between w-full p-5 rounded-2xl bg-white/[0.02] border border-white/5 transition-all hover:bg-white/[0.04] gap-4">
                                <div className="text-left">
                                    <div className="text-[15px] font-bold text-white flex items-center gap-2">
                                        📈 AI Optimal Posting Time
                                    </div>
                                    <div className="text-[12px] text-[#7a85b0] mt-1">Shift schedules dynamically to target peak audience activity.</div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer shrink-0">
                                    <input 
                                        type="checkbox" 
                                        checked={editAiTimePredictor} 
                                        onChange={(e) => setEditAiTimePredictor(e.target.checked)} 
                                        className="sr-only peer" 
                                    />
                                    <div className="w-12 h-7 bg-[#1b223c] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#7a85b0] after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-[#00cec9] peer-checked:after:bg-white"></div>
                                </label>
                            </div>

                            {/* Display predicted optimal times if enabled */}
                            {editAiTimePredictor && (
                                <div className="w-full p-5 rounded-2xl bg-[#00cec9]/5 border border-[#00cec9]/15 text-left animate-in fade-in slide-in-from-top-4">
                                    <div className="text-[12px] font-bold text-[#00cec9] uppercase tracking-wider mb-3 pl-1 flex items-center gap-2">
                                        🧠 Calculated Peak Hours (AI)
                                    </div>
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[13px] text-[#7a85b0]">
                                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => {
                                            const fullDay = day === 'Mon' ? 'Monday' : day === 'Tue' ? 'Tuesday' : day === 'Wed' ? 'Wednesday' : day === 'Thu' ? 'Thursday' : day === 'Fri' ? 'Friday' : day === 'Sat' ? 'Saturday' : 'Sunday';
                                            const time = editOptimalSlots[fullDay] || '18:00';
                                            return (
                                                <div key={day} className="bg-[#080b14] border border-white/5 rounded-xl p-3 text-center shadow-inner">
                                                    <div className="text-[11px] text-[#3d4666] font-bold uppercase">{day}</div>
                                                    <div className="text-white font-bold mt-1 text-[15px]">{time}</div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="p-6 border-t border-white/5 bg-white/[0.01] flex flex-col sm:flex-row gap-3">
                            <button 
                                onClick={() => {
                                    setShowSettingsModal(null)
                                    navigate(`/workspace/${showSettingsModal.id}`)
                                }} 
                                className="flex-1 py-3.5 rounded-xl bg-white/5 hover:bg-white/10 text-white font-bold text-[14px] border border-white/5 transition-all flex items-center justify-center gap-2"
                            >
                                ⚙️ Open Workspace Wizard
                            </button>
                            <div className="flex gap-3 flex-1">
                                <button 
                                    onClick={() => setShowSettingsModal(null)} 
                                    className="flex-1 py-3.5 rounded-xl bg-[#131829] text-[#7a85b0] font-bold text-[14px] border border-white/5 transition-all hover:bg-[#131829]/80"
                                >
                                    Cancel
                                </button>
                                <button 
                                    onClick={() => handleSaveSettings(showSettingsModal.id)} 
                                    disabled={savingSettings}
                                    className="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-[#6c5ce7] to-[#00cec9] text-white font-bold text-[14px] disabled:opacity-50 transition-all hover:opacity-90 shadow-[0_0_20px_rgba(108,92,231,0.2)]"
                                >
                                    {savingSettings ? 'Saving...' : 'Save Settings'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}