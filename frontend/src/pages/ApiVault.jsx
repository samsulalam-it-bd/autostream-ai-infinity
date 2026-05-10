import { useState, useEffect } from 'react'
import { 
    Key, ShieldCheck, Zap, Bot, Send, Eye, EyeOff, Save, 
    RefreshCw, AlertCircle, CheckCircle2 
} from 'lucide-react'
import clsx from 'clsx'

export default function ApiVault() {
    const [showKeys, setShowKeys] = useState({})
    const [saving, setSaving] = useState(false)
    
    const toggleKey = (id) => setShowKeys(prev => ({ ...prev, [id]: !prev[id] }))

    const VAULT_ITEMS = [
        {
            id: 'gemini',
            icon: Bot,
            bg: 'rgba(232, 67, 147, 0.1)',
            name: 'Gemini AI API',
            sub: 'Video content generation • AI titles & descriptions',
            usage: 85,
            usageText: '850 / 1000 daily requests used',
            status: 'Ready',
            statusColor: 'b-green',
            dot: 'sdot-ok'
        },
        {
            id: 'google',
            icon: ShieldCheck,
            bg: 'rgba(0, 184, 148, 0.1)',
            name: 'Google OAuth',
            sub: 'YouTube upload + Drive read access • Refresh token saved',
            usage: 8,
            usageText: '847 / 10,000 YouTube API quota used',
            status: 'Connected',
            statusColor: 'b-green',
            dot: 'sdot-ok'
        },
        {
            id: 'meta',
            icon: Zap,
            bg: 'rgba(66, 103, 178, 0.1)',
            name: 'Meta (Facebook / Instagram)',
            sub: 'Facebook pages + Instagram content publishing',
            usage: 32,
            usageText: '320 / 1,000 Meta API calls today',
            status: 'Active',
            statusColor: 'b-green',
            dot: 'sdot-ok'
        }
    ]

    return (
        <div className="space-y-8 animate-in max-w-5xl mx-auto">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white">🔑 API Vault</h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Secure credential management and system configuration</p>
                </div>
            </div>

            {/* ── Vault Items ─────────────────────────────────────── */}
            <div className="space-y-3">
                {VAULT_ITEMS.map(item => (
                    <div key={item.id} className="bg-[#0d1120] border border-white/5 rounded-2xl p-5 flex items-center gap-5 hover:border-white/10 transition-all">
                        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0" style={{ background: item.bg }}>
                            <item.icon className="w-6 h-6" style={{ color: item.id === 'gemini' ? '#e84393' : item.id === 'google' ? '#00b894' : '#6c5ce7' }} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="font-bold text-white text-[15px]">{item.name}</div>
                            <div className="text-[12px] text-[#7a85b0] mt-0.5">{item.sub}</div>
                            <div className="mt-2 w-24 h-1 bg-[#131829] rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-[#6c5ce7] to-[#e84393]" style={{ width: `${item.usage}%` }} />
                            </div>
                            <div className="text-[10px] text-[#3d4666] font-bold mt-1 uppercase tracking-wider">{item.usageText}</div>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                            <div className={clsx("w-2 h-2 rounded-full", item.dot === 'sdot-ok' ? "bg-[#00b894] shadow-[0_0_8px_#00b894]" : "bg-[#d63031]")} />
                            <span className={clsx("badge", item.statusColor)}>{item.status}</span>
                            <button className="btn btn-o btn-xs !px-3">Test</button>
                        </div>
                    </div>
                ))}
                
                {/* Expired Item Example */}
                <div className="bg-[#0d1120] border border-[#fdcb6e20] rounded-2xl p-5 flex items-center gap-5">
                    <div className="w-12 h-12 rounded-xl bg-[#fdcb6e10] flex items-center justify-center text-[#fdcb6e] shrink-0 text-xl">
                        ⚠️
                    </div>
                    <div className="flex-1">
                        <div className="font-bold text-white text-[15px]">autostream_reels Token</div>
                        <div className="text-[12px] text-[#7a85b0] mt-0.5">Instagram account token has expired — reconnect required</div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-[#fdcb6e] shadow-[0_0_8px_#fdcb6e]" />
                        <span className="badge b-yellow">Expired</span>
                        <button className="btn btn-g btn-xs !bg-gradient-to-r from-[#fdcb6e] to-[#e17055] !border-none">Reconnect</button>
                    </div>
                </div>
            </div>

            <div className="h-px bg-white/5 my-8" />

            {/* ── System Config ────────────────────────────────────── */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Settings2 className="w-5 h-5 text-[#6c5ce7]" /> System Configuration (.env)
                    </h2>
                    <button className="btn btn-o btn-sm">
                        <Save className="w-3.5 h-3.5" /> Save All
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {[
                        { label: 'Google Client ID', id: 'gci', val: '483920174856-abc...apps.googleusercontent.com' },
                        { label: 'Google Client Secret', id: 'gcs', val: 'GOCSPX-ABC123XYZ...', secret: true },
                        { label: 'Meta App ID', id: 'maid', val: '1234567890123456' },
                        { label: 'Meta App Secret', id: 'mas', val: 'def456...', secret: true },
                        { label: 'Gemini API Key', id: 'gai', val: 'AIzaSyB...', secret: true },
                        { label: 'Telegram Bot Token', id: 'tg', val: '712345:AAF...', secret: true },
                    ].map(field => (
                        <div key={field.id} className="space-y-2">
                            <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider">{field.label}</label>
                            <div className="relative group">
                                <input 
                                    type={field.secret && !showKeys[field.id] ? 'password' : 'text'}
                                    className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-[13px] font-mono text-white outline-none focus:border-[#6c5ce7] transition-all"
                                    defaultValue={field.val}
                                />
                                {field.secret && (
                                    <button 
                                        onClick={() => toggleKey(field.id)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#3d4666] hover:text-[#7a85b0] transition-colors"
                                    >
                                        {showKeys[field.id] ? <EyeOff size={16} /> : <Eye size={16} />}
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="bg-[#00b89408] border border-[#00b89415] rounded-2xl p-4 text-[13px] text-[#7a85b0] flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-[#00b894] shrink-0" />
                    <div>
                        <strong className="text-white">Tip:</strong> After saving, run <code className="bg-[#1a2035] px-1.5 py-0.5 rounded text-[#00cec9] font-mono mx-1">docker-compose down && docker-compose up -d</code> to apply changes to the background workers.
                    </div>
                </div>
            </div>
        </div>
    )
}

function Settings2(props) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M20 7h-9" />
            <path d="M14 17H5" />
            <circle cx="17" cy="17" r="3" />
            <circle cx="7" cy="7" r="3" />
        </svg>
    )
}
