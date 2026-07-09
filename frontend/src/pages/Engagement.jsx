import { useState, useRef, useEffect } from 'react'
import { 
    Bot, Send, Trash2, Sparkles, Wand2, Copy, Check, 
    MessageSquare, Play, RefreshCw, Settings2, History, 
    Power, ShieldAlert, Cpu, BotMessageSquare, AlertCircle
} from 'lucide-react'
import api, { aiChat, quickGen, fetchAccounts } from '../lib/api'
import clsx from 'clsx'

export default function Engagement() {
    const [activeTab, setActiveTab] = useState('assistant') // assistant, rules, logs

    // ── Tab 1: AI Assistant States ───────────────────────────────────────
    const [messages, setMessages] = useState([
        { role: 'bot', text: "👋 Hi! I'm your AutoStream AI. I can generate video titles, descriptions, tags & hashtags for YouTube, Facebook, and Instagram. What would you like to create today?" }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [qLoading, setQLoading] = useState(false)
    const [qResult, setQResult] = useState(null)
    const [qForm, setQForm] = useState({ topic: '', platform: 'YouTube', style: '🔥 Viral' })
    const scrollRef = useRef()

    // ── Tab 2 & 3: Comment Automation States ──────────────────────────────
    const [accounts, setAccounts] = useState([])
    const [rules, setRules] = useState([])
    const [logs, setLogs] = useState([])
    const [rulesLoading, setRulesLoading] = useState(false)
    const [selectedAccountId, setSelectedAccountId] = useState('')
    const [keywords, setKeywords] = useState('')
    const [persona, setPersona] = useState('Helpful and friendly, use emojis. Keep it short.')
    const [replyType, setReplyType] = useState('ai') // 'ai' or 'static'
    const [customReplyText, setCustomReplyText] = useState('')
    const [autoReply, setAutoReply] = useState(true)
    const [autoDm, setAutoDm] = useState(false)
    const [saving, setSaving] = useState(false)

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }, [messages])

    // Load setup data
    const loadRulesData = async () => {
        try {
            setRulesLoading(true)
            const [accRes, rulesRes, logsRes] = await Promise.all([
                fetchAccounts(),
                api.get('/comments/rules'),
                api.get('/comments/logs?limit=50')
            ])
            setAccounts(Array.isArray(accRes.data) ? accRes.data.filter(a => a.status === 'active' || a.status === 'ACTIVE') : [])
            setRules(rulesRes.data || [])
            setLogs(logsRes.data || [])
        } catch (e) {
            console.error('Failed to load comment rules/logs:', e)
        } finally {
            setRulesLoading(false)
        }
    }

    useEffect(() => {
        if (activeTab !== 'assistant') {
            loadRulesData()
        }
    }, [activeTab])

    // Find existing rule if user selects an account
    useEffect(() => {
        if (selectedAccountId) {
            const existing = rules.find(r => r.account_id === selectedAccountId)
            if (existing) {
                setKeywords(existing.custom_keywords?.join(', ') || '')
                setPersona(existing.ai_persona || '')
                setCustomReplyText(existing.custom_reply_text || '')
                setReplyType(existing.custom_reply_text ? 'static' : 'ai')
                setAutoReply(existing.auto_reply_enabled)
                setAutoDm(existing.auto_dm_enabled)
            } else {
                setKeywords('')
                setPersona('Helpful and friendly, use emojis. Keep it short.')
                setCustomReplyText('')
                setReplyType('ai')
                setAutoReply(true)
                setAutoDm(false)
            }
        }
    }, [selectedAccountId, rules])

    // Actions
    const handleSend = async (text = input) => {
        if (!text.trim()) return
        const userMsg = { role: 'user', text: text.trim() }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)

        try {
            const res = await aiChat(text.trim())
            setMessages(prev => [...prev, { role: 'bot', text: res.data.reply }])
        } catch (e) {
            console.error(e)
            setMessages(prev => [...prev, { role: 'bot', text: "⚠️ Failed to connect to AI. Please check backend." }])
        } finally {
            setLoading(false)
        }
    }

    const handleQuickGen = async () => {
        if (!qForm.topic.trim()) return
        setQLoading(true)
        try {
            const res = await quickGen(qForm.topic, qForm.platform, qForm.style)
            setQResult(res.data)
        } catch (e) {
            console.error(e)
        } finally {
            setQLoading(false)
        }
    }

    const handleSaveRule = async (e) => {
        e.preventDefault()
        if (!selectedAccountId) return
        setSaving(true)
        try {
            const payload = {
                account_id: selectedAccountId,
                custom_keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
                auto_reply_enabled: autoReply,
                auto_dm_enabled: autoDm,
                ai_persona: replyType === 'ai' ? persona : '',
                custom_reply_text: replyType === 'static' ? customReplyText : null
            }
            await api.post('/comments/rules', payload)
            loadRulesData()
            setSelectedAccountId('')
        } catch (err) {
            console.error(err)
        } finally {
            setSaving(false)
        }
    }

    const handleDeleteRule = async (id) => {
        if (!window.confirm('Are you sure you want to delete this rule?')) return
        try {
            await api.delete(`/comments/rules/${id}`)
            loadRulesData()
        } catch (err) {
            console.error(err)
        }
    }

    const quickPrompts = [
        { icon: '🔥', label: 'Viral Title', prompt: 'Generate a viral YouTube title for a product review video' },
        { icon: '📸', label: 'IG Caption', prompt: 'Write an Instagram Reel caption with hashtags for a tutorial video' },
        { icon: '🏷️', label: 'Hashtags', prompt: 'Generate 15 trending hashtags for a tech video in 2024' },
        { icon: '📝', label: 'Description', prompt: 'Write a compelling YouTube video description for a how-to guide' }
    ]

    return (
        <div className="space-y-6 max-w-6xl mx-auto">
            {/* ── Tabs Navigation ──────────────────────────────────── */}
            <div className="flex gap-2 border-b border-white/5 pb-2">
                <button
                    onClick={() => setActiveTab('assistant')}
                    className={clsx(
                        "flex items-center gap-2 px-4 py-2 font-medium rounded-xl transition-all text-[13px]",
                        activeTab === 'assistant' 
                            ? "bg-[#6c5ce724] text-white border border-[#6c5ce733] shadow-[0_0_12px_#6c5ce710]" 
                            : "text-[#7a85b0] hover:text-white hover:bg-white/[0.02]"
                    )}
                >
                    <Bot size={15} /> 🤖 AI Assistant
                </button>
                <button
                    onClick={() => setActiveTab('rules')}
                    className={clsx(
                        "flex items-center gap-2 px-4 py-2 font-medium rounded-xl transition-all text-[13px]",
                        activeTab === 'rules' 
                            ? "bg-[#6c5ce724] text-white border border-[#6c5ce733] shadow-[0_0_12px_#6c5ce710]" 
                            : "text-[#7a85b0] hover:text-white hover:bg-white/[0.02]"
                    )}
                >
                    <Settings2 size={15} /> 💬 Auto-Responder Rules
                </button>
                <button
                    onClick={() => setActiveTab('logs')}
                    className={clsx(
                        "flex items-center gap-2 px-4 py-2 font-medium rounded-xl transition-all text-[13px]",
                        activeTab === 'logs' 
                            ? "bg-[#6c5ce724] text-white border border-[#6c5ce733] shadow-[0_0_12px_#6c5ce710]" 
                            : "text-[#7a85b0] hover:text-white hover:bg-white/[0.02]"
                    )}
                >
                    <History size={15} /> 📜 Engagement Logs
                </button>
            </div>

            {/* ── TAB 1: AI Assistant ──────────────────────────────── */}
            {activeTab === 'assistant' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in">
                    {/* AI Chat */}
                    <div className="space-y-6">
                        <div className="bg-[#0d1120] border border-white/5 rounded-[20px] overflow-hidden flex flex-col h-[500px]">
                            <div className="p-4 border-b border-white/5 bg-gradient-to-r from-[#6c5ce710] to-[#e8439305] flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#6c5ce7] to-[#e84393] flex items-center justify-center text-white shadow-glow-brand">
                                        <Bot size={20} />
                                    </div>
                                    <div>
                                        <div className="text-[14px] font-bold text-white">AutoStream AI</div>
                                        <div className="text-[10px] text-[#00b894] font-bold flex items-center gap-1">
                                            <div className="w-1.5 h-1.5 rounded-full bg-[#00b894] shadow-[0_0_5px_#00b894]" /> Online — Gemini Powered
                                        </div>
                                    </div>
                                </div>
                                <button onClick={() => setMessages([messages[0]])} className="p-2 text-[#3d4666] hover:text-white transition-colors">
                                    <Trash2 size={18} />
                                </button>
                            </div>

                            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
                                {messages.map((m, i) => (
                                    <div key={i} className={clsx(
                                        "max-w-[85%] p-3.5 rounded-2xl text-[13.5px] leading-relaxed animate-in",
                                        m.role === 'user' ? "bg-gradient-to-r from-[#6c5ce7] to-[#e84393] text-white self-end ml-auto rounded-tr-none shadow-glow-brand" : "bg-[#131829] text-[#dde3f5] self-start mr-auto rounded-tl-none border border-white/5"
                                    )}>
                                        {m.text}
                                    </div>
                                ))}
                                {loading && (
                                    <div className="bg-[#131829] text-[#7a85b0] self-start mr-auto p-3.5 rounded-2xl rounded-tl-none border border-white/5 animate-pulse text-[13px]">
                                        AI is thinking...
                                    </div>
                                )}
                            </div>

                            <div className="p-4 border-t border-white/5 flex gap-3">
                                <input 
                                    className="flex-1 bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#6c5ce7] transition-all"
                                    placeholder="Ask AI to generate content..."
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                />
                                <button onClick={() => handleSend()} className="w-12 h-12 bg-gradient-to-r from-[#6c5ce7] to-[#e84393] rounded-xl flex items-center justify-center text-white shadow-glow-brand transition-transform active:scale-95">
                                    <Send size={20} />
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-3">Quick Prompts</label>
                            <div className="flex flex-wrap gap-2">
                                {quickPrompts.map(p => (
                                    <button 
                                        key={p.label}
                                        onClick={() => handleSend(p.prompt)}
                                        className="px-4 py-2 bg-[#0d1120] border border-white/5 rounded-full text-[12px] text-[#7a85b0] hover:border-[#6c5ce7] hover:text-[#a29bfe] transition-all flex items-center gap-2"
                                    >
                                        <span>{p.icon}</span> {p.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Quick Gen */}
                    <div className="space-y-6">
                        <div className="bg-[#0d1120] border border-white/5 rounded-[20px] p-6 space-y-6">
                            <div className="flex items-center gap-2 text-lg font-bold text-white">
                                <Sparkles className="text-[#fdcb6e]" size={20} /> ⚡ Quick Generate
                            </div>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Video Topic / Filename</label>
                                    <input 
                                        className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#6c5ce7]" 
                                        placeholder="e.g. iPhone 16 Pro Max Review 2024" 
                                        value={qForm.topic}
                                        onChange={(e) => setQForm({...qForm, topic: e.target.value})}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Platform</label>
                                        <select 
                                            className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-[#7a85b0] outline-none"
                                            value={qForm.platform}
                                            onChange={(e) => setQForm({...qForm, platform: e.target.value})}
                                        >
                                            <option>YouTube</option><option>Facebook</option><option>Instagram</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Style</label>
                                        <select 
                                            className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-[#7a85b0] outline-none"
                                            value={qForm.style}
                                            onChange={(e) => setQForm({...qForm, style: e.target.value})}
                                        >
                                            <option>🔥 Viral</option><option>💼 Professional</option>
                                        </select>
                                    </div>
                                </div>
                                <button 
                                    onClick={handleQuickGen}
                                    disabled={qLoading}
                                    className="w-full btn btn-g justify-center py-3"
                                >
                                    {qLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : '🚀 Generate Full Content Pack'}
                                </button>
                            </div>

                            {qResult && (
                                <div className="bg-[#131829] rounded-2xl p-5 border border-white/5 animate-in space-y-4">
                                    <div>
                                        <div className="text-[10px] text-[#3d4666] font-bold uppercase mb-1">Title</div>
                                        <div className="text-[13px] text-white font-medium">{qResult.title}</div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-[#3d4666] font-bold uppercase mb-1">Description</div>
                                        <div className="text-[12px] text-[#7a85b0] leading-relaxed">{qResult.description}</div>
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {qResult.hashtags.map(h => (
                                            <span key={h} className="text-[11px] text-[#6c5ce7] font-bold">{h}</span>
                                        ))}
                                    </div>
                                    <button className="w-full btn btn-o btn-sm gap-2 justify-center" onClick={() => {
                                        navigator.clipboard.writeText(`${qResult.title}\n\n${qResult.description}\n\n${qResult.hashtags.join(' ')}`)
                                    }}>
                                        <Copy size={14} /> Copy All
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ── TAB 2: Auto-Responder Rules ───────────────────────── */}
            {activeTab === 'rules' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in">
                    {/* Setup Form */}
                    <div className="bg-[#0d1120] border border-white/5 rounded-[20px] p-6 space-y-6">
                        <div className="flex items-center gap-2 text-lg font-bold text-white">
                            <Settings2 className="text-[#6c5ce7]" size={20} /> AI Auto-Reply Setup
                        </div>

                        <form onSubmit={handleSaveRule} className="space-y-5">
                            <div>
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Target Account</label>
                                <select
                                    required
                                    value={selectedAccountId}
                                    onChange={(e) => setSelectedAccountId(e.target.value)}
                                    className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#6c5ce7]"
                                >
                                    <option value="">-- Select Active Account --</option>
                                    {accounts.map(acc => (
                                        <option key={acc.id} value={acc.id}>
                                            {acc.platform.toUpperCase()} - {acc.channel_name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">Keywords Trigger (Optional)</label>
                                <p className="text-[10.5px] text-[#5c678a] mb-2">Separate with commas. If empty, AI replies to all comments.</p>
                                <input
                                    type="text"
                                    value={keywords}
                                    onChange={(e) => setKeywords(e.target.value)}
                                    placeholder="e.g. price, link, details, buy"
                                    className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#6c5ce7]"
                                />
                            </div>

                            <div>
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Response Mode</label>
                                <div className="grid grid-cols-2 gap-3 mb-4">
                                    <button
                                        type="button"
                                        onClick={() => setReplyType('ai')}
                                        className={clsx(
                                            "py-2.5 px-4 rounded-xl text-[12px] font-bold border transition-all flex items-center justify-center gap-2",
                                            replyType === 'ai'
                                                ? "bg-[#6c5ce724] text-white border-[#6c5ce7] shadow-[0_0_12px_#6c5ce710]"
                                                : "bg-[#131829] text-[#7a85b0] border-white/5 hover:border-white/10"
                                        )}
                                    >
                                        🤖 AI Responder (Gemini)
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setReplyType('static')}
                                        className={clsx(
                                            "py-2.5 px-4 rounded-xl text-[12px] font-bold border transition-all flex items-center justify-center gap-2",
                                            replyType === 'static'
                                                ? "bg-[#6c5ce724] text-white border-[#6c5ce7] shadow-[0_0_12px_#6c5ce710]"
                                                : "bg-[#131829] text-[#7a85b0] border-white/5 hover:border-white/10"
                                        )}
                                    >
                                        ✍️ Custom Static Reply
                                    </button>
                                </div>
                            </div>

                            {replyType === 'ai' ? (
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">AI Persona prompt context</label>
                                    <p className="text-[10.5px] text-[#5c678a] mb-2">Instruct the Gemini agent on how to speak and behave.</p>
                                    <textarea
                                        required
                                        rows="4"
                                        value={persona}
                                        onChange={(e) => setPersona(e.target.value)}
                                        placeholder="e.g. You are a tech reviewer. Speak highly enthusiastically, use viral emojis, and suggest checking the link."
                                        className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#6c5ce7] resize-none"
                                    />
                                </div>
                            ) : (
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-1">Custom Reply Text</label>
                                    <p className="text-[10.5px] text-[#5c678a] mb-2">Enter the exact static text the bot will reply with to every comment.</p>
                                    <textarea
                                        required
                                        rows="4"
                                        value={customReplyText}
                                        onChange={(e) => setCustomReplyText(e.target.value)}
                                        placeholder="e.g. Thanks for the comment! Check out our website link in the bio for more details."
                                        className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#6c5ce7] resize-none"
                                    />
                                </div>
                            )}

                            <div className="flex gap-6 pt-2">
                                <label className="flex items-center cursor-pointer select-none">
                                    <div className="relative">
                                        <input type="checkbox" className="sr-only" checked={autoReply} onChange={(e) => setAutoReply(e.target.checked)} />
                                        <div className={clsx("block w-10 h-6 rounded-full transition-colors", autoReply ? 'bg-[#00b894]' : 'bg-[#3d4666]')} />
                                        <div className={clsx("absolute left-0.5 top-0.5 bg-white w-5 h-5 rounded-full transition-transform", autoReply && 'transform translate-x-4')} />
                                    </div>
                                    <span className="ml-3 text-[12.5px] font-bold text-white uppercase tracking-wider">Auto Reply</span>
                                </label>

                                <label className="flex items-center cursor-pointer select-none">
                                    <div className="relative">
                                        <input type="checkbox" className="sr-only" checked={autoDm} onChange={(e) => setAutoDm(e.target.checked)} />
                                        <div className={clsx("block w-10 h-6 rounded-full transition-colors", autoDm ? 'bg-[#00cec9]' : 'bg-[#3d4666]')} />
                                        <div className={clsx("absolute left-0.5 top-0.5 bg-white w-5 h-5 rounded-full transition-transform", autoDm && 'transform translate-x-4')} />
                                    </div>
                                    <span className="ml-3 text-[12.5px] font-bold text-white uppercase tracking-wider">Auto DM</span>
                                </label>
                            </div>

                            <button 
                                type="submit" 
                                disabled={saving}
                                className="w-full btn btn-g justify-center py-3 mt-4"
                            >
                                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : '🚀 Activate AI Responder'}
                            </button>
                        </form>
                    </div>

                    {/* Active Rules List */}
                    <div className="space-y-6">
                        <div className="text-lg font-bold text-white flex items-center gap-2">
                            <BotMessageSquare className="text-[#00cec9]" size={20} /> Active Automation Rules
                        </div>

                        {rulesLoading ? (
                            <div className="text-center py-12 text-[#7a85b0]">Loading active rules...</div>
                        ) : rules.length === 0 ? (
                            <div className="bg-[#0d1120] border border-dashed border-white/10 rounded-[20px] p-8 text-center flex flex-col items-center justify-center h-64">
                                <ShieldAlert size={32} className="text-[#3d4666] mb-3" />
                                <div className="text-[13px] text-[#7a85b0]">No active rules on any channel yet.</div>
                                <div className="text-[11px] text-[#3d4666] mt-1">Configure one using the setup wizard on the left.</div>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {rules.map(rule => {
                                    const acc = accounts.find(a => a.id === rule.account_id)
                                    return (
                                        <div key={rule.id} className="bg-[#0d1120] border border-white/5 rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden group">
                                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-[#6c5ce7] to-[#e84393]" />
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h4 className="text-[14.5px] font-bold text-white uppercase">
                                                        {acc ? `${acc.platform} — ${acc.channel_name}` : 'Channel'}
                                                    </h4>
                                                    {rule.custom_reply_text ? (
                                                        <p className="text-[12px] text-[#00cec9] mt-1 italic font-medium">✍️ Custom: "{rule.custom_reply_text}"</p>
                                                    ) : (
                                                        <p className="text-[12px] text-[#7a85b0] mt-1 italic">🤖 AI: "{rule.ai_persona}"</p>
                                                    )}
                                                </div>
                                                <button onClick={() => handleDeleteRule(rule.id)} className="p-1.5 text-[#d63031] hover:bg-[#d6303114] rounded-lg transition-all">
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                            <div className="flex gap-2 flex-wrap">
                                                {rule.auto_reply_enabled && <span className="badge b-green !text-[9px]">Reply ON</span>}
                                                {rule.auto_dm_enabled && <span className="badge b-purple !text-[9px]">DM ON</span>}
                                                {rule.custom_keywords && rule.custom_keywords.length > 0 && (
                                                    <span className="badge b-gray !text-[9px]">{rule.custom_keywords.length} Keywords</span>
                                                )}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── TAB 3: Engagement Logs ───────────────────────────── */}
            {activeTab === 'logs' && (
                <div className="bg-[#0d1120] border border-white/5 rounded-[20px] p-6 space-y-6 animate-in">
                    <div className="flex justify-between items-center">
                        <div className="text-lg font-bold text-white flex items-center gap-2">
                            <History className="text-[#fdcb6e]" size={20} /> AI Engagement Monitor
                        </div>
                        <button onClick={loadRulesData} className="btn btn-o btn-sm">
                            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Sync Logs
                        </button>
                    </div>

                    {rulesLoading ? (
                        <div className="text-center py-12 text-[#7a85b0]">Loading audit logs...</div>
                    ) : logs.length === 0 ? (
                        <div className="text-center py-12 text-[#3d4666]">
                            No active comment replies logged yet.
                        </div>
                    ) : (
                        <div className="overflow-x-auto rounded-xl border border-white/5">
                            <table className="w-full text-left text-[13px]">
                                <thead className="bg-[#131829] text-[#7a85b0] text-[11px] font-bold uppercase tracking-wider border-b border-white/5">
                                    <tr>
                                        <th className="px-6 py-4">Time</th>
                                        <th className="px-6 py-4">Viewer</th>
                                        <th className="px-6 py-4">Comment</th>
                                        <th className="px-6 py-4">AI generated response</th>
                                        <th className="px-6 py-4">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5 text-white">
                                    {logs.map(log => (
                                        <tr key={log.id} className="hover:bg-white/[0.01]">
                                            <td className="px-6 py-4 whitespace-nowrap text-[#7a85b0]">
                                                {new Date(log.created_at).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 font-bold">
                                                {log.author_name}
                                                <span className="text-[10px] text-[#3d4666] block uppercase tracking-wider font-normal mt-0.5">{log.platform}</span>
                                            </td>
                                            <td className="px-6 py-4 max-w-xs truncate" title={log.comment_text}>
                                                {log.comment_text}
                                            </td>
                                            <td className="px-6 py-4 text-[#dde3f5] max-w-xs" title={log.ai_reply_text}>
                                                <div className="flex items-start gap-1.5">
                                                    <Cpu size={14} className="text-[#6c5ce7] mt-0.5 shrink-0" />
                                                    <span className="line-clamp-2">{log.ai_reply_text || '—'}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {log.dm_sent ? (
                                                    <span className="badge b-purple !text-[9px]">DM Sent</span>
                                                ) : (
                                                    <span className="badge b-green !text-[9px]">Replied</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
