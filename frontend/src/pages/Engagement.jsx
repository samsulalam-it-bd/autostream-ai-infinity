import { useState, useRef, useEffect } from 'react'
import { Bot, Send, Trash2, Sparkles, Wand2, Copy, Check, MessageSquare } from 'lucide-react'
import clsx from 'clsx'

export default function Engagement() {
    const [messages, setMessages] = useState([
        { role: 'bot', text: "👋 Hi! I'm your AutoStream AI. I can generate video titles, descriptions, tags & hashtags for YouTube, Facebook, and Instagram. What would you like to create today?" }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [qResult, setQResult] = useState(null)
    const scrollRef = useRef()

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }, [messages])

    const handleSend = async (text = input) => {
        if (!text.trim()) return
        const userMsg = { role: 'user', text: text.trim() }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)

        // Mock AI thinking
        setTimeout(() => {
            setMessages(prev => [...prev, { role: 'bot', text: "I've generated some optimized tags for your video topic: #viral #tech #automation #trending2024" }])
            setLoading(false)
        }, 1000)
    }

    const quickPrompts = [
        { icon: '🔥', label: 'Viral Title', prompt: 'Generate a viral YouTube title for a product review video' },
        { icon: '📸', label: 'IG Caption', prompt: 'Write an Instagram Reel caption with hashtags for a tutorial video' },
        { icon: '🏷️', label: 'Hashtags', prompt: 'Generate 15 trending hashtags for a tech video in 2024' },
        { icon: '📝', label: 'Description', prompt: 'Write a compelling YouTube video description for a how-to guide' }
    ]

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in max-w-6xl mx-auto">
            {/* ── AI Chat ────────────────────────────────────────── */}
            <div className="space-y-6">
                <div className="sec-hd">
                    <div>
                        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                            <Bot className="text-[#6c5ce7]" /> AI Content Assistant
                        </h1>
                        <p className="text-[13px] text-[#7a85b0] mt-1">Powered by Gemini AI — Generate titles, descriptions & tags</p>
                    </div>
                </div>

                <div className="bg-[#0d1120] border border-white/5 rounded-[20px] overflow-hidden flex flex-col h-[500px]">
                    <div className="p-4 border-b border-white/5 bg-gradient-to-r from-[#6c5ce710] to-[#e8439305] flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#6c5ce7] to-[#e84393] flex items-center justify-center text-white">
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
                                m.role === 'user' ? "bg-gradient-to-r from-[#6c5ce7] to-[#e84393] text-white self-end ml-auto rounded-tr-none" : "bg-[#131829] text-[#dde3f5] self-start mr-auto rounded-tl-none border border-white/5"
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

            {/* ── Quick Gen ────────────────────────────────────────── */}
            <div className="space-y-6">
                <div className="bg-[#0d1120] border border-white/5 rounded-[20px] p-6 space-y-6">
                    <div className="flex items-center gap-2 text-lg font-bold text-white">
                        <Sparkles className="text-[#fdcb6e]" size={20} /> ⚡ Quick Generate
                    </div>
                    
                    <div className="space-y-4">
                        <div>
                            <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Video Topic / Filename</label>
                            <input className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#6c5ce7]" placeholder="e.g. iPhone 16 Pro Max Review 2024" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Platform</label>
                                <select className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-[#7a85b0] outline-none">
                                    <option>YouTube</option><option>Facebook</option><option>Instagram</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Style</label>
                                <select className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-[#7a85b0] outline-none">
                                    <option>🔥 Viral</option><option>💼 Professional</option>
                                </select>
                            </div>
                        </div>
                        <button className="w-full btn btn-g justify-center py-3">
                            🚀 Generate Full Content Pack
                        </button>
                    </div>

                    {qResult && (
                        <div className="bg-[#131829] rounded-2xl p-5 border border-white/5 animate-in">
                            {/* Result content would go here */}
                        </div>
                    )}
                </div>

                <div className="bg-[#0d1120] border border-white/5 rounded-[20px] p-6 space-y-4">
                    <div className="text-[15px] font-bold text-white flex items-center gap-2">
                        <Sparkles size={16} className="text-[#6c5ce7]" /> AI Settings
                    </div>
                    <div className="space-y-3">
                        {[
                            'AI Auto Title Generation',
                            'AI Auto Description',
                            'Auto Hashtag Generation',
                            'AI Audience Engagement'
                        ].map((s, i) => (
                            <div key={s} className="flex items-center justify-between group">
                                <span className="text-[13px] text-[#7a85b0] group-hover:text-white transition-colors">{s}</span>
                                <div className="w-9 h-5 bg-[#00b89420] rounded-full relative cursor-pointer">
                                    <div className={clsx("absolute top-0.5 w-4 h-4 rounded-full transition-all", i < 3 ? "right-0.5 bg-[#00b894]" : "left-0.5 bg-[#3d4666]")} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
