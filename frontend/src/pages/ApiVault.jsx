import { useState, useEffect } from 'react'
import { 
    Key, ShieldCheck, Zap, Bot, Send, Eye, EyeOff, Save, 
    RefreshCw, AlertCircle, CheckCircle2, Youtube, Facebook, Instagram, 
    Settings2, Plus, Trash2, Unlock, ExternalLink, UploadCloud, X, Loader2, Play, Globe
} from 'lucide-react'
import { 
    listApiKeys, deleteApiKey, unlockApiKey, testApiKey, 
    uploadGoogleKeys, addMetaKey, addCustomKey, testTelegram 
} from '../lib/api'
import clsx from 'clsx'

export default function ApiVault() {
    const [keys, setKeys] = useState([])
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState('google')
    const [showAddModal, setShowAddModal] = useState(false)
    const [isUploading, setIsUploading] = useState(false)
    const [testingTg, setTestingTg] = useState(false)
    const [tgStatus, setTgStatus] = useState(null)

    // Form states
    const [newKey, setNewKey] = useState({ 
        service: 'gemini', project: '', key: '', 
        appId: '', appSecret: '', accessToken: '' 
    })

    const loadKeys = async () => {
        try {
            const res = await listApiKeys()
            setKeys(res.data)
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }

    useEffect(() => { loadKeys() }, [])

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this API key?')) return
        try {
            await deleteApiKey(id)
            setKeys(keys.filter(k => k.id !== id))
        } catch (e) { alert('Delete failed') }
    }

    const handleUnlock = async (id) => {
        try {
            await unlockApiKey(id)
            loadKeys()
        } catch (e) { alert('Unlock failed') }
    }

    const handleTest = async (id) => {
        try {
            const res = await testApiKey(id)
            alert(res.data.valid ? '✅ API Key is Valid!' : '❌ API Key Invalid: ' + (res.data.detail || 'Unknown error'))
        } catch (e) { alert('Test failed') }
    }

    const handleFileUpload = async (e) => {
        const files = Array.from(e.target.files)
        if (files.length === 0) return
        setIsUploading(true)
        try {
            const res = await uploadGoogleKeys(files)
            alert(`Added ${res.data.added} keys. Skipped ${res.data.skipped}.`)
            loadKeys()
        } catch (e) { alert('Upload failed') }
        finally { setIsUploading(false) }
    }

    const handleAddCustom = async () => {
        if (!newKey.project || !newKey.key) return alert('Fill all fields')
        try {
            await addCustomKey({
                service_name: newKey.service,
                project_name: newKey.project,
                api_key: newKey.key
            })
            setShowAddModal(false)
            loadKeys()
        } catch (e) { alert('Failed to add key') }
    }

    const handleAddMeta = async () => {
        if (!newKey.project || !newKey.appId || !newKey.appSecret || !newKey.accessToken) return alert('Fill all fields')
        try {
            await addMetaKey({
                app_name: newKey.project,
                app_id: newKey.appId,
                app_secret: newKey.appSecret,
                access_token: newKey.accessToken
            })
            setShowAddModal(false)
            loadKeys()
        } catch (e) { alert('Failed to add meta key') }
    }

    const handleTestTelegram = async () => {
        setTestingTg(true)
        setTgStatus(null)
        try {
            const res = await testTelegram("Test alert from AutoStream AI Infinity Vault 🔑")
            setTgStatus(res.data.status === 'ok' ? 'success' : 'error')
        } catch (e) { setTgStatus('error') }
        finally { setTestingTg(false) }
    }

    const filteredKeys = keys.filter(k => k.service_name === activeTab)

    return (
        <div className="space-y-8 animate-in max-w-6xl mx-auto pb-20">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Key className="text-[#6c5ce7]" /> API Vault & Rotation
                    </h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Manage multiple API keys to prevent quota limits and ensure 24/7 uptime</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={loadKeys} className="btn btn-o btn-sm">
                        <RefreshCw size={14} className={clsx(loading && "animate-spin")} /> Refresh
                    </button>
                    <button onClick={() => setShowAddModal(true)} className="btn btn-g btn-sm">
                        <Plus size={14} /> Add New Key
                    </button>
                </div>
            </div>

            {/* ── Rotation Health System ───────────────────────── */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in slide-in-from-bottom-4 duration-700">
                <div className="bg-gradient-to-br from-[#6c5ce715] to-transparent border border-[#6c5ce720] rounded-3xl p-6 relative overflow-hidden group">
                    <div className="absolute top-[-20%] right-[-10%] w-32 h-32 bg-[#6c5ce720] blur-[60px] rounded-full group-hover:bg-[#6c5ce730] transition-all" />
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-2xl bg-[#6c5ce720] flex items-center justify-center text-[#a29bfe]">
                            <Zap size={20} />
                        </div>
                        <h3 className="font-bold text-white text-[15px]">Active Rotation</h3>
                    </div>
                    <div className="text-3xl font-black text-white mb-1">
                        {keys.filter(k => !k.is_locked).length} <span className="text-[14px] text-[#7a85b0] font-medium tracking-normal">Keys Ready</span>
                    </div>
                    <p className="text-[11px] text-[#7a85b0]">System is balanced and monitoring {keys.length} total endpoints</p>
                </div>

                <div className="bg-[#0d1120] border border-white/5 rounded-3xl p-6 relative overflow-hidden">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-2xl bg-[#00cec910] flex items-center justify-center text-[#00cec9]">
                            <ShieldCheck size={20} />
                        </div>
                        <h3 className="font-bold text-white text-[15px]">Vault Integrity</h3>
                    </div>
                    <div className="text-3xl font-black text-white mb-1">
                        100% <span className="text-[14px] text-[#00b894] font-medium tracking-normal">Secure</span>
                    </div>
                    <p className="text-[11px] text-[#7a85b0]">All credentials are encrypted using AES-256 (Fernet)</p>
                </div>

                <div className="bg-[#0d1120] border border-white/5 rounded-3xl p-6 relative overflow-hidden">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-2xl bg-[#d6303110] flex items-center justify-center text-[#d63031]">
                            <AlertCircle size={20} />
                        </div>
                        <h3 className="font-bold text-white text-[15px]">Blocked Quota</h3>
                    </div>
                    <div className="text-3xl font-black text-white mb-1 text-[#d63031]">
                        {keys.filter(k => k.is_locked).length} <span className="text-[14px] text-[#7a85b0] font-medium tracking-normal">Restricted</span>
                    </div>
                    <p className="text-[11px] text-[#7a85b0]">Keys currently cooling down or hit provider limits</p>
                </div>
            </div>

            {/* ── Tabs ─────────────────────────────────────────── */}
            <div className="tabs">
                {[
                    { id: 'google', label: 'Google / YouTube', icon: Youtube },
                    { id: 'meta', label: 'Meta (FB/IG)', icon: Facebook },
                    { id: 'gemini', label: 'Gemini AI', icon: Bot },
                    { id: 'openrouter', label: 'OpenRouter', icon: Globe },
                ].map(t => (
                    <div key={t.id} className={clsx("tab", activeTab === t.id && "on")} onClick={() => setActiveTab(t.id)}>
                        <t.icon size={14} className="mr-2" /> {t.label}
                        <span className="ml-2 opacity-50 text-[10px]">({keys.filter(k => k.service_name === t.id).length})</span>
                    </div>
                ))}
            </div>

            {/* ── List ─────────────────────────────────────────── */}
            <div className="space-y-4">
                {filteredKeys.length > 0 ? filteredKeys.map(k => (
                    <div key={k.id} className="bg-[#0d1120] border border-white/5 rounded-2xl p-5 flex items-center gap-6 hover:border-white/10 transition-all group">
                        <div className={clsx(
                            "w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0",
                            k.is_locked ? "bg-[#d630311a] text-[#d63031]" : "bg-[#00b8941a] text-[#00b894]"
                        )}>
                            {k.service_name === 'google' ? <Youtube size={24} /> : k.service_name === 'meta' ? <Facebook size={24} /> : k.service_name === 'openrouter' ? <Globe size={24} /> : <Bot size={24} />}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="font-bold text-white text-[15px]">{k.project_name}</span>
                                {k.is_locked && <span className="badge b-red !text-[9px]">Quota Locked</span>}
                                {k.is_system && <span className="badge b-blue !text-[9px] !bg-[#0984e320] !text-[#0984e3] !border-[#0984e330]">System Default</span>}
                            </div>
                            <div className="flex items-center gap-4 mt-1">
                                <div className="text-[11px] text-[#3d4666] font-mono uppercase tracking-wider">ID: {k.id.slice(0,8)}...</div>
                                <div className="text-[11px] text-[#7a85b0]">Status: {k.is_system ? 'Active in .env' : 'Dynamic Vault'}</div>
                            </div>
                            <div className="mt-3 flex items-center gap-4">
                                <div className="flex-1 max-w-[200px]">
                                    <div className="flex justify-between text-[9px] text-[#3d4666] font-bold uppercase mb-1">
                                        <span>Daily Quota Usage</span>
                                        <span>{Math.round((k.daily_usage / k.daily_limit) * 100)}%</span>
                                    </div>
                                    <div className="h-1.5 bg-[#131829] rounded-full overflow-hidden">
                                        <div 
                                            className={clsx("h-full transition-all duration-1000", k.is_locked ? "bg-[#d63031]" : "bg-gradient-to-r from-[#6c5ce7] to-[#e84393]")}
                                            style={{ width: `${Math.min(100, (k.daily_usage / k.daily_limit) * 100)}%` }}
                                        />
                                    </div>
                                </div>
                                <div className="text-[11px] text-[#7a85b0]">{k.daily_usage} / {k.daily_limit}</div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {!k.is_system && (
                                <button onClick={() => handleTest(k.id)} className="btn btn-o btn-xs !px-3" title="Test Key">
                                    <Play size={12} />
                                </button>
                            )}
                            {k.is_locked && (
                                <button onClick={() => handleUnlock(k.id)} className="btn btn-o btn-xs !px-3 !text-[#00cec9] !border-[#00cec930]" title="Reset Quota">
                                    <Unlock size={12} />
                                </button>
                            )}
                            {!k.is_system && (
                                <button onClick={() => handleDelete(k.id)} className="btn btn-o btn-xs !px-3 !text-[#d63031] !border-[#d6303130] opacity-0 group-hover:opacity-100 transition-opacity" title="Delete">
                                    <Trash2 size={12} />
                                </button>
                            )}
                        </div>
                    </div>
                )) : (
                    <div className="bg-[#0d1120] border border-dashed border-white/10 rounded-2xl p-20 text-center">
                        <div className="w-16 h-16 bg-[#131829] rounded-full flex items-center justify-center mx-auto mb-4 text-[#3d4666]">
                            <Key size={32} />
                        </div>
                        <h3 className="text-white font-bold mb-1">No API keys added yet</h3>
                        <p className="text-[13px] text-[#7a85b0] mb-6">Add keys to enable automatic rotation and prevent quota limits.</p>
                        {activeTab === 'google' && (
                            <label className="btn btn-g btn-sm cursor-pointer inline-flex">
                                <UploadCloud size={14} className="mr-2" /> 
                                {isUploading ? 'Uploading...' : 'Bulk Upload JSONs'}
                                <input type="file" multiple accept=".json" className="hidden" onChange={handleFileUpload} disabled={isUploading} />
                            </label>
                        )}
                    </div>
                )}
            </div>

            {/* ── Telegram Test Row ─────────────────────────────────── */}
            <div className="bg-[#0d1120] border border-white/5 rounded-2xl p-6 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#00cec910] flex items-center justify-center text-[#00cec9]">
                        <Send size={20} />
                    </div>
                    <div>
                        <div className="font-bold text-white">Telegram Notifications</div>
                        <div className="text-[12px] text-[#7a85b0]">Verify your bot and chat ID configuration</div>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    {tgStatus && (
                        <div className={clsx(
                            "text-[12px] flex items-center gap-2",
                            tgStatus === 'success' ? "text-[#00b894]" : "text-[#d63031]"
                        )}>
                            {tgStatus === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                            {tgStatus === 'success' ? 'Sent OK' : 'Failed'}
                        </div>
                    )}
                    <button onClick={handleTestTelegram} disabled={testingTg} className="btn btn-o btn-sm">
                        {testingTg ? <Loader2 size={14} className="animate-spin" /> : 'Send Test Alert'}
                    </button>
                </div>
            </div>

            {/* ── Add Key Modal ─────────────────────────────────────── */}
            {showAddModal && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-[#080b14f0] backdrop-blur-md animate-in fade-in">
                    <div className="bg-[#0d1120] border border-white/10 w-full max-w-lg rounded-[30px] overflow-hidden shadow-2xl">
                        <div className="p-8 border-b border-white/5 flex items-center justify-between">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <Plus className="text-[#6c5ce7]" /> Add API Key
                            </h2>
                            <button onClick={() => setShowAddModal(false)} className="text-[#3d4666] hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-8 space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider">Service Type</label>
                                <div className="grid grid-cols-3 gap-2">
                                    {['gemini', 'meta', 'google', 'openrouter'].map(s => (
                                        <button 
                                            key={s} 
                                            onClick={() => setNewKey({...newKey, service: s})}
                                            className={clsx(
                                                "py-2 rounded-xl text-[12px] font-bold border transition-all",
                                                newKey.service === s ? "bg-[#6c5ce720] border-[#6c5ce7] text-white" : "bg-[#131829] border-white/5 text-[#7a85b0]"
                                            )}
                                        >
                                            {s.toUpperCase()}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {newKey.service === 'google' ? (
                                <div className="p-6 bg-[#6c5ce70a] border border-dashed border-[#6c5ce730] rounded-2xl text-center">
                                    <UploadCloud size={32} className="mx-auto mb-4 text-[#6c5ce7]" />
                                    <p className="text-[13px] text-[#7a85b0] mb-4">Upload your Google Cloud project credentials JSON files for YouTube automation.</p>
                                    <label className="btn btn-g btn-sm cursor-pointer inline-flex">
                                        Select Files
                                        <input type="file" multiple accept=".json" className="hidden" onChange={handleFileUpload} />
                                    </label>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider">Project / App Name</label>
                                        <input 
                                            className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-[14px] text-white outline-none focus:border-[#6c5ce7] transition-all"
                                            placeholder="e.g. My AI App"
                                            value={newKey.project}
                                            onChange={e => setNewKey({...newKey, project: e.target.value})}
                                        />
                                    </div>
                                    {newKey.service === 'meta' ? (
                                        <>
                                            <div className="space-y-2">
                                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider">App ID</label>
                                                <input 
                                                    className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-[14px] text-white outline-none focus:border-[#6c5ce7] transition-all"
                                                    placeholder="123456789..."
                                                    value={newKey.appId}
                                                    onChange={e => setNewKey({...newKey, appId: e.target.value})}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider">App Secret</label>
                                                <input 
                                                    type="password"
                                                    className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-[14px] text-white outline-none focus:border-[#6c5ce7] transition-all"
                                                    value={newKey.appSecret}
                                                    onChange={e => setNewKey({...newKey, appSecret: e.target.value})}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider">Short-lived Access Token</label>
                                                <input 
                                                    type="password"
                                                    className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-[14px] text-white outline-none focus:border-[#6c5ce7] transition-all"
                                                    value={newKey.accessToken}
                                                    onChange={e => setNewKey({...newKey, accessToken: e.target.value})}
                                                />
                                            </div>
                                        </>
                                    ) : (
                                        <div className="space-y-2">
                                            <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider">API Key</label>
                                            <input 
                                                type="password"
                                                className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-[14px] text-white outline-none focus:border-[#6c5ce7] transition-all"
                                                placeholder="AIzaSy..."
                                                value={newKey.key}
                                                onChange={e => setNewKey({...newKey, key: e.target.value})}
                                            />
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                        <div className="p-8 bg-[#131829]/50 border-t border-white/5 flex gap-3">
                            <button onClick={() => setShowAddModal(false)} className="flex-1 py-3 rounded-2xl bg-[#131829] text-[#7a85b0] font-bold">Cancel</button>
                            <button 
                                onClick={newKey.service === 'meta' ? handleAddMeta : handleAddCustom} 
                                disabled={newKey.service === 'google'}
                                className={clsx("flex-1 py-3 rounded-2xl bg-gradient-to-r from-[#6c5ce7] to-[#e84393] text-white font-bold shadow-lg shadow-[#6c5ce730]", newKey.service === 'google' && "opacity-50")}
                            >
                                Save API Key
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
