import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchAccounts, updateWorkspaceSettings, syncAccountNow } from '../lib/api'
import { 
    Check, ChevronLeft, ChevronRight, HardDrive, Wand2, 
    Settings2, Calendar, Layout, Trash2, Plus, Play
} from 'lucide-react'
import clsx from 'clsx'

const STEPS = ['Targets', 'Media', 'Editor', 'Schedule', 'Review']

export default function WorkspaceWizard() {
    const navigate = useNavigate()
    const [step, setStep] = useState(1)
    const [accounts, setAccounts] = useState([])
    const [selectedAccounts, setSelectedAccounts] = useState([])
    const [driveUrl, setDriveUrl] = useState('')
    const [isSyncing, setIsSyncing] = useState(false)
    const [syncProgress, setSyncProgress] = useState(0)
    
    // Form State
    const [formData, setFormData] = useState({
        title_mode: 'ai_auto',
        desc_template: 'Check out our latest content! 🔥 Subscribe for more amazing videos every day!\n\n#autostream #viral #subscribe',
        tags: '#autostream #viral #trending #youtube #2024',
        format: '16:9',
        watermark_pos: 'BR',
        timezone: 'Asia/Dhaka',
        days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        limit: 3,
        slots: ['08:00', '14:00', '21:00']
    })

    useEffect(() => {
        const load = async () => {
            const res = await fetchAccounts()
            setAccounts(res.data)
        }
        load()
    }, [])

    const toggleAccount = (id) => {
        setSelectedAccounts(prev => 
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        )
    }

    const handleSync = () => {
        if (!driveUrl) return
        setIsSyncing(true)
        let p = 0
        const iv = setInterval(() => {
            p += Math.random() * 20
            if (p >= 100) {
                p = 100
                clearInterval(iv)
                setIsSyncing(false)
            }
            setSyncProgress(Math.round(p))
        }, 300)
    }

    const handleLaunch = async () => {
        // In a real app, we'd save settings for each selected account
        try {
            await Promise.all(selectedAccounts.map(id => 
                updateWorkspaceSettings(id, {
                    ...formData,
                    drive_url: driveUrl
                })
            ))
            navigate('/autopublish')
        } catch (e) { console.error(e) }
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Wand2 className="text-[#6c5ce7]" /> Upload Wizard
                    </h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Set up your automated publishing pipeline in 5 steps</p>
                </div>
            </div>

            {/* ── Stepper ────────────────────────────────────────── */}
            <div className="wiz-steps flex items-center justify-between relative px-4">
                {STEPS.map((s, i) => {
                    const n = i + 1
                    const isDone = step > n
                    const isCurrent = step === n
                    return (
                        <div key={s} className="flex flex-col items-center z-10">
                            <div className={clsx(
                                "ws-n w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all border-2",
                                isDone ? "bg-gradient-to-r from-[#6c5ce7] to-[#e84393] border-transparent text-white" :
                                isCurrent ? "border-[#6c5ce7] text-white shadow-[0_0_15px_rgba(108,92,231,0.3)] bg-[#0d1120]" :
                                "border-white/5 text-[#3d4666] bg-[#0d1120]"
                            )}>
                                {isDone ? <Check size={18} /> : n}
                            </div>
                            <span className={clsx("mt-2 text-[11px] font-bold uppercase tracking-wider", isCurrent ? "text-white" : "text-[#3d4666]")}>
                                {s}
                            </span>
                        </div>
                    )
                })}
                {/* Connector Lines */}
                <div className="absolute top-5 left-10 right-10 h-[2px] bg-white/5 -z-0">
                    <div className="h-full bg-gradient-to-r from-[#6c5ce7] to-[#e84393] transition-all duration-500" style={{ width: `${((step - 1) / (STEPS.length - 1)) * 100}%` }} />
                </div>
            </div>

            {/* ── Wizard Box ─────────────────────────────────────── */}
            <div className="bg-[#0d1120] border border-white/5 rounded-[20px] p-8 min-h-[400px]">
                {step === 1 && (
                    <div className="animate-in space-y-6">
                        <div>
                            <h2 className="text-lg font-bold text-white mb-1">Select Target Accounts</h2>
                            <p className="text-sm text-[#7a85b0]">Choose which accounts to publish to</p>
                        </div>
                        <div className="space-y-3">
                            {accounts.map(acc => (
                                <div 
                                    key={acc.id}
                                    onClick={() => toggleAccount(acc.id)}
                                    className={clsx(
                                        "po p-4 rounded-2xl border-2 cursor-pointer transition-all flex items-center gap-4",
                                        selectedAccounts.includes(acc.id) ? "border-[#6c5ce7] bg-[#6c5ce710]" : "border-white/5 bg-[#131829] hover:border-white/10"
                                    )}
                                >
                                    <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-xl">
                                        {acc.platform === 'youtube' ? '▶' : acc.platform === 'facebook' ? 'f' : '◉'}
                                    </div>
                                    <div className="flex-1">
                                        <div className="font-bold text-white">{acc.name}</div>
                                        <div className="text-xs text-[#7a85b0]">{acc.platform} · {acc.subscribers_count || 0} followers</div>
                                    </div>
                                    <div className={clsx(
                                        "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all",
                                        selectedAccounts.includes(acc.id) ? "bg-[#6c5ce7] border-transparent text-white" : "border-white/10 text-transparent"
                                    )}>
                                        <Check size={14} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {step === 2 && (
                    <div className="animate-in space-y-6">
                        <div>
                            <h2 className="text-lg font-bold text-white mb-1">Connect Google Drive</h2>
                            <p className="text-sm text-[#7a85b0]">Link your Drive folder containing video files</p>
                        </div>
                        <div className="border-2 border-dashed border-white/10 rounded-2xl p-12 text-center space-y-6 hover:border-[#6c5ce720] transition-colors">
                            <div className="w-16 h-16 bg-[#6c5ce710] text-[#6c5ce7] rounded-full flex items-center justify-center mx-auto">
                                <HardDrive size={32} />
                            </div>
                            <div className="max-w-md mx-auto space-y-4">
                                <div className="font-bold text-white">Paste Drive Folder Link</div>
                                <input 
                                    className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-center text-sm outline-none focus:border-[#6c5ce7]" 
                                    placeholder="https://drive.google.com/drive/folders/..."
                                    value={driveUrl}
                                    onChange={(e) => setDriveUrl(e.target.value)}
                                />
                                <button onClick={handleSync} className="btn btn-g mx-auto">
                                    <RefreshCw className={clsx("w-4 h-4", isSyncing && "animate-spin")} /> Sync Folder
                                </button>
                            </div>
                        </div>
                        {(isSyncing || syncProgress > 0) && (
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs text-[#7a85b0]">
                                    <span>Scanning Drive folder...</span>
                                    <span>{syncProgress}%</span>
                                </div>
                                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-gradient-to-r from-[#6c5ce7] to-[#e84393] transition-all" style={{ width: `${syncProgress}%` }} />
                                </div>
                                {syncProgress === 100 && (
                                    <div className="text-[#00b894] text-xs font-bold flex items-center gap-1.5 animate-in">
                                        <Check size={14} /> Found 18 videos ready to process!
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {step === 3 && (
                    <div className="animate-in space-y-8">
                        <div>
                            <h2 className="text-lg font-bold text-white mb-1">AI Content Editor</h2>
                            <p className="text-sm text-[#7a85b0]">Configure how AI generates content for your videos</p>
                        </div>
                        <div className="grid grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Title Mode</label>
                                    <select className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#6c5ce7]">
                                        <option>🤖 AI Auto Generate</option>
                                        <option>📝 Use File Name</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Description Template</label>
                                    <textarea 
                                        className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-3 text-sm outline-none focus:border-[#6c5ce7] h-32 resize-none"
                                        value={formData.desc_template}
                                        onChange={(e) => setFormData({...formData, desc_template: e.target.value})}
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Default Tags</label>
                                    <input className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#6c5ce7]" value={formData.tags} />
                                </div>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Video Format Preset</label>
                                    <select className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#6c5ce7]">
                                        <option>📺 YouTube 16:9 (1920×1080)</option>
                                        <option>📱 Instagram Reel 9:16 (1080×1920)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Watermark Position</label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['↖ TL', '↑ TC', '↗ TR', '← ML', '⊙ C', '→ MR', '↙ BL', '↓ BC', '↘ BR'].map(p => (
                                            <div 
                                                key={p} 
                                                onClick={() => setFormData({...formData, watermark_pos: p.split(' ')[1]})}
                                                className={clsx(
                                                    "p-2 text-center text-[11px] rounded-lg border transition-all cursor-pointer",
                                                    formData.watermark_pos === p.split(' ')[1] ? "border-[#6c5ce7] bg-[#6c5ce71a] text-white" : "border-white/5 bg-[#131829] text-[#7a85b0]"
                                                )}
                                            >
                                                {p}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {step === 4 && (
                    <div className="animate-in space-y-8">
                        <div>
                            <h2 className="text-lg font-bold text-white mb-1">Publishing Schedule</h2>
                            <p className="text-sm text-[#7a85b0]">Set when your content goes live automatically</p>
                        </div>
                        <div className="grid grid-cols-2 gap-8">
                            <div className="space-y-6">
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Timezone</label>
                                    <select className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#6c5ce7]">
                                        <option>Asia/Dhaka (UTC+6)</option>
                                        <option>UTC</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Publishing Days</label>
                                    <div className="flex flex-wrap gap-2">
                                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
                                            <div 
                                                key={d}
                                                onClick={() => setFormData({...formData, days: formData.days.includes(d) ? formData.days.filter(x => x !== d) : [...formData.days, d]})}
                                                className={clsx(
                                                    "px-3 py-1.5 rounded-lg border text-xs font-bold cursor-pointer transition-all",
                                                    formData.days.includes(d) ? "bg-[#6c5ce715] border-[#6c5ce7] text-white" : "bg-[#131829] border-white/5 text-[#3d4666]"
                                                )}
                                            >
                                                {d}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 bg-[#131829] p-4 rounded-2xl border border-white/5">
                                    <Calendar className="text-[#fdcb6e]" />
                                    <div>
                                        <div className="text-xs text-white font-bold">Auto Publish Active</div>
                                        <div className="text-[10px] text-[#7a85b0] mt-0.5">Pipeline will start after launch</div>
                                    </div>
                                    <div className="ml-auto">
                                        <div className="w-10 h-5 bg-[#00b89420] rounded-full relative">
                                            <div className="absolute right-0.5 top-0.5 w-4 h-4 bg-[#00b894] rounded-full" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Scheduled Times</label>
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {formData.slots.map((t, i) => (
                                            <div key={i} className="flex items-center gap-2 bg-[#131829] border border-white/5 px-3 py-1.5 rounded-full text-xs font-bold text-white group">
                                                {t}
                                                <X size={12} className="text-[#3d4666] cursor-pointer hover:text-white" onClick={() => setFormData({...formData, slots: formData.slots.filter(x => x !== t)})} />
                                            </div>
                                        ))}
                                    </div>
                                    <div className="flex gap-2">
                                        <input type="time" id="new-slot" className="flex-1 bg-[#131829] border border-white/10 rounded-xl px-4 py-2 text-sm outline-none" />
                                        <button className="btn btn-g px-4 py-2" onClick={() => {
                                            const val = document.getElementById('new-slot').value
                                            if(val) setFormData({...formData, slots: [...formData.slots, val].sort()})
                                        }}><Plus size={18} /></button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {step === 5 && (
                    <div className="animate-in space-y-8">
                        <div>
                            <h2 className="text-lg font-bold text-white mb-1">Review & Launch</h2>
                            <p className="text-sm text-[#7a85b0]">Confirm everything before starting the pipeline</p>
                        </div>
                        <div className="grid grid-cols-2 gap-8">
                            <div className="bg-[#131829] rounded-2xl p-6 border border-white/5">
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-4">Target Accounts ({selectedAccounts.length})</label>
                                <div className="space-y-3">
                                    {accounts.filter(a => selectedAccounts.includes(a.id)).map(a => (
                                        <div key={a.id} className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-xs">
                                                {a.platform === 'youtube' ? '▶' : 'f'}
                                            </div>
                                            <div>
                                                <div className="text-[13px] font-bold text-white">{a.name}</div>
                                                <div className="text-[10px] text-[#3d4666]">{a.platform}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="bg-[#131829] rounded-2xl p-6 border border-white/5 space-y-4">
                                <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Pipeline Summary</label>
                                <div className="space-y-3">
                                    {[
                                        { l: 'Videos Found', v: '18' },
                                        { l: 'Daily Slots', v: `${formData.slots.length} per day` },
                                        { l: 'Timezone', v: formData.timezone },
                                        { l: 'Est. Duration', v: `${Math.ceil(18/formData.slots.length)} days` }
                                    ].map(item => (
                                        <div key={item.l} className="flex justify-between items-center text-[13px]">
                                            <span className="text-[#7a85b0]">{item.l}</span>
                                            <span className="text-white font-bold">{item.v}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div className="bg-[#00b89408] border border-[#00b89415] rounded-2xl p-6 text-center">
                            <div className="text-[#00b894] font-bold mb-1 flex items-center justify-center gap-2">
                                <Check size={18} /> Ready to Launch!
                            </div>
                            <p className="text-[13px] text-[#7a85b0]">All settings configured. Click Launch to start the automated pipeline.</p>
                        </div>
                    </div>
                )}
            </div>

            {/* ── Nav ────────────────────────────────────────────── */}
            <div className="flex justify-between items-center pt-4">
                <button 
                    onClick={() => setStep(s => Math.max(1, s - 1))}
                    disabled={step === 1}
                    className={clsx("btn btn-o", step === 1 && "opacity-0")}
                >
                    <ChevronLeft size={18} /> Back
                </button>
                <button 
                    onClick={() => step === 5 ? handleLaunch() : setStep(s => s + 1)}
                    className={clsx("btn", step === 5 ? "btn-g3" : "btn-g")}
                >
                    {step === 5 ? '🚀 Launch Pipeline' : 'Continue →'}
                </button>
            </div>
        </div>
    )
}
