import { useState, useEffect } from 'react'
import { 
    fetchAccounts, deleteAccount, updateAccount, syncAccountNow, 
    instantPost, triggerPipeline 
} from '../lib/api'
import { 
    Youtube, Facebook, Instagram, Trash2, Edit2, RefreshCw, 
    Zap, Play, MoreVertical, X, Check, AlertTriangle, ShieldCheck
} from 'lucide-react'
import clsx from 'clsx'

const PLATFORM_CONFIG = {
    youtube: { icon: Youtube, color: 'var(--yt)', bg: 'rgba(255, 71, 87, 0.1)' },
    facebook: { icon: Facebook, color: 'var(--fb)', bg: 'rgba(66, 103, 178, 0.1)' },
    instagram: { icon: Instagram, color: 'var(--ig)', bg: 'rgba(232, 67, 147, 0.1)' }
}

export default function Accounts() {
    const [accounts, setAccounts] = useState([])
    const [filter, setFilter] = useState('all')
    const [loading, setLoading] = useState(true)
    const [activeOverlay, setActiveOverlay] = useState(null) // { type: 'edit'|'del'|'inst', id: null }

    const loadAccounts = async () => {
        try {
            const res = await fetchAccounts(filter === 'all' ? null : filter)
            setAccounts(res.data)
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }

    useEffect(() => { loadAccounts() }, [filter])

    const handleDelete = async (id) => {
        try {
            await deleteAccount(id)
            setAccounts(accounts.filter(a => a.id !== id))
            setActiveOverlay(null)
        } catch (e) { alert('Failed to delete') }
    }

    const handleAction = async (action, account) => {
        try {
            if (action === 'sync') await syncAccountNow(account.id)
            if (action === 'run') await triggerPipeline(account.id)
            if (action === 'instant') await instantPost(account.id)
            loadAccounts()
        } catch (e) { console.error(e) }
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
                    <button onClick={loadAccounts} className="btn btn-o btn-sm">
                        <RefreshCw className="w-3.5 h-3.5" /> Refresh All
                    </button>
                    <button className="btn btn-g btn-sm">
                        + Add Account
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
                                        <div className="font-bold text-white text-[15px] truncate">{account.name}</div>
                                        <div className="text-[11px] text-[#7a85b0] mt-0.5 uppercase tracking-wide">
                                            {account.platform} · {account.handle || account.platform_id}
                                        </div>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <div className="text-[13px] font-bold" style={{ background: cfg.color, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                                            {account.subscribers_count || '0'}
                                        </div>
                                        <div className="text-[9px] text-[#3d4666] uppercase font-bold tracking-wider">Followers</div>
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

                                <div className="bg-[#131829] rounded-xl py-2 px-4 mb-4 text-center text-[12px] text-[#7a85b0]">
                                    ⏰ Next: <span className="font-bold" style={{ color: cfg.color }}>{account.next_publish_time || 'No Schedule'}</span>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-1.5">
                                    <button onClick={() => handleAction('run', account)} className="flex-1 bg-[#131829] hover:bg-[#00b8941a] border border-white/5 hover:border-[#00b894] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#00b894]" title="Run Now">
                                        <Play className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => handleAction('sync', account)} className="flex-1 bg-[#131829] hover:bg-[#00cec91a] border border-white/5 hover:border-[#00cec9] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#00cec9]" title="Sync Drive">
                                        <RefreshCw className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => setActiveOverlay({ type: 'edit', id: account.id })} className="flex-1 bg-[#131829] hover:bg-[#6c5ce71a] border border-white/5 hover:border-[#6c5ce7] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#6c5ce7]" title="Edit">
                                        <Edit2 className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => setActiveOverlay({ type: 'inst', id: account.id })} className="flex-1 bg-[#131829] hover:bg-[#fdcb6e1a] border border-white/5 hover:border-[#fdcb6e] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#fdcb6e]" title="Instant Post">
                                        <Zap className="w-4 h-4 mx-auto" />
                                    </button>
                                    <button onClick={() => setActiveOverlay({ type: 'del', id: account.id })} className="flex-1 bg-[#131829] hover:bg-[#d630311a] border border-white/5 hover:border-[#d63031] p-2 rounded-lg transition-all text-[#7a85b0] hover:text-[#d63031]" title="Delete">
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
                                                "{account.name}" will be removed. All pending schedules will be cancelled.
                                            </div>
                                            <div className="flex gap-2 w-full">
                                                <button onClick={() => setActiveOverlay(null)} className="flex-1 py-2 rounded-xl bg-[#131829] text-[#7a85b0] font-bold text-[13px] border border-white/5">Cancel</button>
                                                <button onClick={() => handleDelete(account.id)} className="flex-1 py-2 rounded-xl bg-[#d6303120] text-[#d63031] font-bold text-[13px] border border-[#d6303140] hover:bg-[#d63031]">Yes, Delete</button>
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
                                                Skip the queue and publish the next video from "{account.name}" immediately?
                                            </div>
                                            <div className="flex gap-2 w-full">
                                                <button onClick={() => setActiveOverlay(null)} className="flex-1 py-2 rounded-xl bg-[#131829] text-[#7a85b0] font-bold text-[13px] border border-white/5">Cancel</button>
                                                <button onClick={() => handleAction('instant', account)} className="flex-1 py-2 rounded-xl bg-gradient-to-r from-[#fdcb6e] to-[#e17055] text-white font-bold text-[13px]">⚡ Post Now</button>
                                            </div>
                                        </>
                                    )}

                                    {activeOverlay.type === 'edit' && (
                                        <div className="w-full h-full flex flex-col pt-4">
                                            <div className="text-[16px] font-bold text-white mb-4">✏️ Edit {account.name}</div>
                                            <div className="space-y-3 flex-1 text-left px-2">
                                                <div>
                                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">Display Name</label>
                                                    <input className="w-full bg-[#1a2035] border border-white/10 rounded-lg px-3 py-2 text-white text-[13px]" defaultValue={account.name} />
                                                </div>
                                                <div>
                                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">Daily Post Limit</label>
                                                    <input type="number" className="w-full bg-[#1a2035] border border-white/10 rounded-lg px-3 py-2 text-white text-[13px]" defaultValue="3" />
                                                </div>
                                                <div>
                                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">Timezone</label>
                                                    <select className="w-full bg-[#1a2035] border border-white/10 rounded-lg px-3 py-2 text-white text-[13px]">
                                                        <option>Asia/Dhaka (UTC+6)</option>
                                                        <option>UTC</option>
                                                    </select>
                                                </div>
                                            </div>
                                            <div className="flex gap-2 w-full mt-4">
                                                <button onClick={() => setActiveOverlay(null)} className="flex-1 py-2 rounded-xl bg-[#131829] text-[#7a85b0] font-bold text-[13px] border border-white/5">Cancel</button>
                                                <button onClick={() => setActiveOverlay(null)} className="flex-1 py-2 rounded-xl bg-gradient-to-r from-[#6c5ce7] to-[#e84393] text-white font-bold text-[13px]">Save Changes</button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
