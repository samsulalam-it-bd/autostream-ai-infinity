import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
    fetchAccounts, updateWorkspaceSettings, syncAccountNow, pollTaskStatus,
    fetchVideos, createAutoDrip
} from '../lib/api'
import {
    ChevronDown, Folder, HardDrive, RefreshCw, CheckCircle2,
    AlertCircle, FileVideo, Wand2, ArrowRight, Play, Check, ChevronLeft, ChevronRight,
    Settings2, Calendar, Layout, Trash2, Plus, X, Image
} from 'lucide-react'
import clsx from 'clsx'

const STEPS = ['Targets', 'Media', 'Editor', 'Schedule', 'Review']

export default function WorkspaceWizard() {
    const navigate = useNavigate()
    const { id: editId } = useParams()
    const [step, setStep] = useState(1)
    const [activeOverlay, setActiveOverlay] = useState(null)
    const [showAddModal, setShowAddModal] = useState(false)
    const [syncingAll, setSyncingAll] = useState(false)
    const [positioningMode, setPositioningMode] = useState('logo') // 'logo' or 'text'
    const [accounts, setAccounts] = useState([])
    const [selectedAccounts, setSelectedAccounts] = useState([])
    const [driveUrl, setDriveUrl] = useState('')
    const [isSyncing, setIsSyncing] = useState(false)
    const [syncProgress, setSyncProgress] = useState(0)
    const [foundVideos, setFoundVideos] = useState([])

    // Form State
    const [formData, setFormData] = useState({
        title_mode: 'ai_auto',
        format: '9:16',
        overlay_text: '',
        text_pos: 'BC',
        text_color: '#ffffff',
        logo_url: '',
        watermark_pos: 'TR',
        add_watermark: true,
        delete_from_drive: false,
        desc_template: 'Check out our latest content! 🔥 Subscribe for more amazing videos every day!\n\n#autostream #viral #subscribe',
        tags: '#autostream #viral #trending #youtube #2026',
        watermark_opacity: 0.8,
        watermark_size: 15,
        timezone: 'Asia/Dhaka',
        days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        limit: 3,
        slots: ['08:00', '14:00', '21:00'],
        facebook_post_type: 'video'
    })

    useEffect(() => {
        const load = async () => {
            const res = await fetchAccounts()
            setAccounts(res.data)

            if (editId) {
                setSelectedAccounts([editId])
                const target = res.data.find(a => a.id === editId)
                if (target) {
                    setDriveUrl(target.drive_folder_link || '')
                    if (target.automation_settings) {
                        setFormData(prev => ({ ...prev, ...target.automation_settings }))
                    }
                }
            }
        }
        load()
    }, [editId])

    const toggleAccount = (id) => {
        setSelectedAccounts(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        )
    }

    const handleSync = async () => {
        if (!driveUrl || selectedAccounts.length === 0) return
        setIsSyncing(true)
        setSyncProgress(10)

        try {
            // Trigger sync with the folder link
            const res = await syncAccountNow(selectedAccounts[0], driveUrl)
            const taskId = res.data.task_id

            if (!taskId) {
                // Fallback if no task ID (e.g. error)
                setIsSyncing(false)
                return
            }

            // Polling for task status
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await pollTaskStatus(taskId)
                    const { status } = statusRes.data

                    if (status === 'SUCCESS') {
                        clearInterval(pollInterval)
                        setSyncProgress(100)
                        
                        // Small delay for smooth transition
                        setTimeout(async () => {
                            setIsSyncing(false)
                            // Fetch all recent videos (not just unassigned) to ensure the grid is populated
                            const vRes = await fetchVideos(null, false)
                            const videos = vRes.data.slice(0, 24)
                            setFoundVideos(videos)
                            
                            if (videos.length === 0) {
                                alert("No videos found in this folder or database. Please check your Drive link and permissions.")
                            }
                        }, 500)
                    } else if (status === 'FAILURE' || status === 'REVOKED') {
                        clearInterval(pollInterval)
                        setIsSyncing(false)
                        alert("Sync Failed. Please check logs and ensure the folder is shared with your Google Account.")
                    } else {
                        // Increment progress slightly while waiting
                        setSyncProgress(prev => prev < 90 ? prev + 10 : prev)
                    }
                } catch (e) {
                    clearInterval(pollInterval)
                    setIsSyncing(false)
                }
            }, 1500)

        } catch (e) {
            console.error(e)
            setIsSyncing(false)
        }
    }

    const canContinue = () => {
        if (step === 1) return selectedAccounts.length > 0
        if (step === 2) {
            const isImgMode = formData.facebook_post_type === 'image' && selectedAccounts.some(id => accounts.find(a => a.id === id)?.platform === 'facebook');
            const filtered = foundVideos.filter(v => isImgMode ? v.media_type === 'IMAGE' : v.media_type !== 'IMAGE');
            return filtered.length > 0;
        }
        if (step === 3) return formData.desc_template.trim().length > 0
        if (step === 4) return formData.slots.length > 0
        return true
    }

    const handleLaunch = async () => {
        try {
            // 1. Update settings for all targets
            await Promise.all(selectedAccounts.map(id =>
                updateWorkspaceSettings(id, {
                    drive_folder_link: driveUrl,
                    automation_settings: formData
                })
            ))

            const isImgMode = formData.facebook_post_type === 'image' && selectedAccounts.some(id => accounts.find(a => a.id === id)?.platform === 'facebook');
            const filteredMedia = foundVideos.filter(v => isImgMode ? v.media_type === 'IMAGE' : v.media_type !== 'IMAGE');

            // 2. Trigger Auto-Drip scheduling
            await createAutoDrip({
                account_ids: selectedAccounts,
                video_ids: filteredMedia.map(v => v.id),
                settings: {
                    timezone: formData.timezone,
                    time_slots: formData.slots,
                    mode: formData.title_mode === 'ai_auto' ? 'ai' : 'original',
                    custom_description: formData.desc_template,
                    tags: formData.tags,
                    add_watermark: formData.add_watermark
                }
            })

            navigate('/autopublish')
        } catch (e) {
            console.error(e)
            alert('Failed to launch pipeline. Check console for details.')
        }
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

                                {selectedAccounts.some(id => accounts.find(a => a.id === id)?.platform === 'facebook') && (
                                    <div className="bg-[#080b1460] border border-white/5 rounded-2xl p-4 space-y-3 max-w-sm mx-auto text-left animate-in">
                                        <div className="text-[11px] text-[#7a85b0] font-bold uppercase tracking-wider">📘 Facebook Publish Format</div>
                                        <div className="grid grid-cols-2 gap-2">
                                            <button
                                                type="button"
                                                onClick={() => setFormData(prev => ({ ...prev, facebook_post_type: 'video' }))}
                                                className={clsx(
                                                    "px-3 py-2.5 rounded-xl border text-[12px] font-bold transition-all flex items-center justify-center gap-1.5",
                                                    formData.facebook_post_type === 'video'
                                                        ? "bg-[#6c5ce720] border-[#6c5ce7] text-white"
                                                        : "border-white/5 text-[#7a85b0] hover:text-white"
                                                )}
                                            >
                                                🎥 Reels / Video
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setFormData(prev => ({ ...prev, facebook_post_type: 'image' }))}
                                                className={clsx(
                                                    "px-3 py-2.5 rounded-xl border text-[12px] font-bold transition-all flex items-center justify-center gap-1.5",
                                                    formData.facebook_post_type === 'image'
                                                        ? "bg-[#00cec920] border-[#00cec9] text-white"
                                                        : "border-white/5 text-[#7a85b0] hover:text-white"
                                                )}
                                            >
                                                📸 Image / Photo
                                            </button>
                                        </div>
                                    </div>
                                )}

                                <button onClick={handleSync} className="btn btn-g mx-auto">
                                    <RefreshCw className={clsx("w-4 h-4", isSyncing && "animate-spin")} /> Sync Folder
                                </button>
                            </div>
                        </div>
                        {(isSyncing || syncProgress > 0) && (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-xs text-[#7a85b0]">
                                        <span>Scanning Drive folder...</span>
                                        <span>{syncProgress}%</span>
                                    </div>
                                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-[#6c5ce7] to-[#e84393] transition-all" style={{ width: `${syncProgress}%` }} />
                                    </div>
                                </div>

                                {(() => {
                                    const isImgMode = formData.facebook_post_type === 'image' && selectedAccounts.some(id => accounts.find(a => a.id === id)?.platform === 'facebook');
                                    const filteredMedia = foundVideos.filter(v => isImgMode ? v.media_type === 'IMAGE' : v.media_type !== 'IMAGE');
                                    
                                    if (filteredMedia.length === 0) {
                                        return syncProgress === 100 ? (
                                            <div className="py-10 text-center border border-dashed border-white/5 rounded-2xl bg-white/[0.02] animate-in">
                                                <AlertCircle className="mx-auto text-[#ff7675] mb-2" size={24} />
                                                <div className="text-[10px] font-bold text-white uppercase tracking-widest mb-1">
                                                    {isImgMode ? "No Images Found" : "No Videos Found"}
                                                </div>
                                                <div className="text-[10px] text-[#7a85b0]">
                                                    Ensure folder has {isImgMode ? "images (.png, .jpg)" : "videos"} matching sync mode
                                                </div>
                                            </div>
                                        ) : null;
                                    }

                                    return (
                                        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                                            <div className="text-[10px] text-[#6c5ce7] font-bold uppercase tracking-widest mb-3">Detected Media ({filteredMedia.length})</div>
                                            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
                                                {filteredMedia.map(v => (
                                                    <div key={v.id} className="aspect-square bg-[#131829] rounded-xl overflow-hidden border border-white/5 relative group">
                                                        <div className="absolute inset-0 flex items-center justify-center bg-[#6c5ce705]">
                                                            {v.media_type === 'IMAGE' ? (
                                                                <Image size={20} className="text-[#3d4666] group-hover:text-[#00cec9] transition-colors" />
                                                            ) : (
                                                                <FileVideo size={20} className="text-[#3d4666] group-hover:text-[#6c5ce7] transition-colors" />
                                                            )}
                                                        </div>
                                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                                                            <div className="text-[8px] text-white truncate w-full font-medium">{v.original_filename}</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })()}
                            </div>
                        )}
                    </div>
                )}

                {step === 3 && (
                    <div className="animate-in space-y-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-black text-white mb-1">AI Content Editor</h2>
                                <p className="text-sm text-[#7a85b0]">Branding, overlays, and smart formatting</p>
                            </div>
                            <div className="flex gap-2">
                                <div className="px-3 py-1 rounded-full bg-[#6c5ce720] text-[#6c5ce7] text-[10px] font-bold uppercase tracking-widest border border-[#6c5ce740]">Step 3/5</div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                            {/* Left: Metadata & Branding */}
                            <div className="lg:col-span-7 space-y-8">
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em] block">Description Template</label>
                                        <textarea 
                                            className="w-full bg-[#131829] border border-white/5 rounded-2xl px-4 py-3 text-sm outline-none focus:border-[#6c5ce7] h-28 resize-none text-[#7a85b0] leading-relaxed"
                                            value={formData.desc_template}
                                            onChange={(e) => setFormData({...formData, desc_template: e.target.value})}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em] block">Default Tags</label>
                                        <input 
                                            type="text"
                                            placeholder="#autostream #viral"
                                            className="w-full bg-[#131829] border border-white/5 rounded-2xl px-4 py-3 text-sm outline-none focus:border-[#6c5ce7] text-white"
                                            value={formData.tags}
                                            onChange={(e) => setFormData({...formData, tags: e.target.value})}
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    {/* Logo Toggle */}
                                    <div className="p-6 bg-white/[0.02] border border-white/5 rounded-3xl flex items-center justify-between">
                                        <div className="space-y-1">
                                            <div className="text-[12px] font-bold text-white flex items-center gap-2">
                                                <Layout size={16} className="text-[#6c5ce7]" /> Branding
                                            </div>
                                            <div className="text-[10px] text-[#3d4666]">Enable Logo / Watermark</div>
                                        </div>
                                        <button 
                                            onClick={() => setFormData({...formData, add_watermark: !formData.add_watermark})}
                                            className={clsx(
                                                "w-12 h-6 rounded-full transition-all relative p-1",
                                                formData.add_watermark ? "bg-[#6c5ce7]" : "bg-white/10"
                                            )}
                                        >
                                            <div className={clsx("w-4 h-4 bg-white rounded-full transition-all shadow-sm", formData.add_watermark ? "translate-x-6" : "translate-x-0")} />
                                        </button>
                                    </div>
                                    <div className="p-6 bg-white/[0.02] border border-white/5 rounded-3xl flex items-center justify-between">
                                        <div className="space-y-1">
                                            <div className="text-[12px] font-bold text-white flex items-center gap-2">
                                                <Trash2 size={16} className="text-[#ff7675]" /> Storage
                                            </div>
                                            <div className="text-[10px] text-[#3d4666]">Delete from Drive after upload</div>
                                        </div>
                                        <button 
                                            onClick={() => setFormData({...formData, delete_from_drive: !formData.delete_from_drive})}
                                            className={clsx(
                                                "w-12 h-6 rounded-full transition-all relative p-1",
                                                formData.delete_from_drive ? "bg-[#ff7675]" : "bg-white/10"
                                            )}
                                        >
                                            <div className={clsx("w-4 h-4 bg-white rounded-full transition-all shadow-sm", formData.delete_from_drive ? "translate-x-6" : "translate-x-0")} />
                                        </button>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em] block">Title Mode</label>
                                        <select
                                            value={formData.title_mode}
                                            onChange={(e) => setFormData({ ...formData, title_mode: e.target.value })}
                                            className="w-full bg-[#131829] border border-white/5 rounded-2xl px-4 py-3 text-sm outline-none focus:border-[#6c5ce7] text-white"
                                        >
                                            <option value="ai_auto">🤖 AI Auto Generate</option>
                                            <option value="filename">📝 Use File Name</option>
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em] block">Output Size</label>
                                        <select
                                            value={formData.format}
                                            onChange={(e) => setFormData({ ...formData, format: e.target.value })}
                                            className="w-full bg-[#131829] border border-white/5 rounded-2xl px-4 py-3 text-sm outline-none focus:border-[#6c5ce7] text-white"
                                        >
                                            <option value="9:16">📱 Vertical (Reel/Short) 9:16</option>
                                            <option value="16:9">📺 Landscape (Standard) 16:9</option>
                                            <option value="1:1">⬜ Square (Post) 1:1</option>
                                            <option value="4:5">📸 Portrait (IG Feed) 4:5</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em] block">Video Text Overlay</label>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                placeholder="Add text to video... (e.g. Subscribe Now!)"
                                                className="flex-1 bg-[#131829] border border-white/5 rounded-2xl px-4 py-3 text-sm outline-none focus:border-[#6c5ce7] text-white"
                                                value={formData.overlay_text}
                                                onChange={(e) => setFormData({ ...formData, overlay_text: e.target.value })}
                                            />
                                            <input
                                                type="color"
                                                className="w-12 h-12 rounded-xl bg-white/5 border border-white/5 p-1 cursor-pointer"
                                                value={formData.text_color}
                                                onChange={(e) => setFormData({ ...formData, text_color: e.target.value })}
                                            />
                                        </div>
                                    </div>

                                    <div className="p-6 bg-white/[0.02] border border-white/5 rounded-3xl space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="text-[12px] font-bold text-white flex items-center gap-2">
                                                <Layout size={16} className="text-[#6c5ce7]" /> Logo & Text Position
                                            </div>
                                            <button
                                                className="text-[10px] text-[#6c5ce7] font-bold hover:underline"
                                                onClick={() => document.getElementById('logo-up').click()}
                                            >
                                                UPLOAD OVERLAY (ANY FILE)
                                            </button>
                                            <input
                                                type="file" id="logo-up" className="hidden" accept="image/*,video/*,.gif,.webp"
                                                onChange={(e) => {
                                                    const file = e.target.files[0]
                                                    if (file) setFormData({ ...formData, logo_url: URL.createObjectURL(file) })
                                                }}
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-6">
                                            <div>
                                                <label className="text-[9px] text-[#3d4666] font-bold uppercase mb-2 block">Logo Position</label>
                                                <div className="grid grid-cols-3 gap-1">
                                                    {['TL', 'TC', 'TR', 'ML', 'C', 'MR', 'BL', 'BC', 'BR'].map(p => (
                                                        <button
                                                            key={p}
                                                            onClick={() => setFormData({ ...formData, watermark_pos: p })}
                                                            className={clsx(
                                                                "p-2 text-center text-[9px] font-black rounded-lg border transition-all",
                                                                formData.watermark_pos === p ? "border-[#6c5ce7] bg-[#6c5ce715] text-[#6c5ce7]" : "border-white/5 bg-[#131829] text-[#3d4666]"
                                                            )}
                                                        >
                                                            {p}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                            <div>
                                                <label className="text-[9px] text-[#3d4666] font-bold uppercase mb-2 block">Text Position</label>
                                                <div className="grid grid-cols-3 gap-1">
                                                    {['TL', 'TC', 'TR', 'ML', 'C', 'MR', 'BL', 'BC', 'BR'].map(p => (
                                                        <button
                                                            key={p}
                                                            onClick={() => setFormData({ ...formData, text_pos: p })}
                                                            className={clsx(
                                                                "p-2 text-center text-[9px] font-black rounded-lg border transition-all",
                                                                formData.text_pos === p ? "border-[#00b894] bg-[#00b89415] text-[#00b894]" : "border-white/5 bg-[#131829] text-[#3d4666]"
                                                            )}
                                                        >
                                                            {p}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="lg:col-span-5 space-y-6">
                                <div className="flex items-center justify-between">
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-[0.2em] block">Live Frame Preview</label>
                                    <div className="flex items-center gap-1 bg-[#131829] p-1 rounded-lg border border-white/5">
                                        <button
                                            onClick={() => setPositioningMode('logo')}
                                            className={clsx("px-3 py-1 text-[9px] font-bold uppercase rounded-md transition-all", positioningMode === 'logo' ? "bg-[#6c5ce7] text-white" : "text-[#7a85b0] hover:text-white")}
                                        >
                                            Set Logo
                                        </button>
                                        <button
                                            onClick={() => setPositioningMode('text')}
                                            className={clsx("px-3 py-1 text-[9px] font-bold uppercase rounded-md transition-all", positioningMode === 'text' ? "bg-[#00b894] text-white" : "text-[#7a85b0] hover:text-white")}
                                        >
                                            Set Text
                                        </button>
                                    </div>
                                </div>

                                <div className="flex items-center justify-center min-h-[450px] bg-black/20 rounded-[40px] border border-white/5 p-4">
                                    <div
                                        className="relative bg-[#131829] rounded-2xl shadow-2xl overflow-hidden group cursor-crosshair border border-white/10"
                                        style={{
                                            aspectRatio: formData.format.replace(':', '/'),
                                            width: formData.format === '9:16' ? '250px' : '100%',
                                            maxWidth: '400px'
                                        }}
                                        onClick={(e) => {
                                            const rect = e.currentTarget.getBoundingClientRect()
                                            const x = (e.clientX - rect.left) / rect.width
                                            const y = (e.clientY - rect.top) / rect.height

                                            let h = 'C', v = 'M'
                                            if (x < 0.33) h = 'L'; else if (x > 0.66) h = 'R'; else h = 'C'
                                            if (y < 0.33) v = 'T'; else if (y > 0.66) v = 'B'; else v = 'M'

                                            const pos = v === 'M' && h === 'C' ? 'C' : v + h
                                            if (positioningMode === 'logo') {
                                                setFormData({ ...formData, watermark_pos: pos })
                                            } else {
                                                setFormData({ ...formData, text_pos: pos })
                                            }
                                        }}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-br from-[#131829] to-[#1e273e]" />

                                        {/* Logo Rendering */}
                                        <div className={clsx(
                                            "absolute p-4 transition-all duration-300",
                                            formData.watermark_pos === 'TL' && "top-0 left-0",
                                            formData.watermark_pos === 'TC' && "top-0 left-1/2 -translate-x-1/2",
                                            formData.watermark_pos === 'TR' && "top-0 right-0",
                                            formData.watermark_pos === 'ML' && "top-1/2 left-0 -translate-y-1/2",
                                            formData.watermark_pos === 'C' && "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2",
                                            formData.watermark_pos === 'MR' && "top-1/2 right-0 -translate-y-1/2",
                                            formData.watermark_pos === 'BL' && "bottom-0 left-0",
                                            formData.watermark_pos === 'BC' && "bottom-0 left-1/2 -translate-x-1/2",
                                            formData.watermark_pos === 'BR' && "bottom-0 right-0"
                                        )}>
                                            {formData.logo_url ? (
                                                formData.logo_url.match(/\.(mp4|webm|ogg)$/i) || document.getElementById('logo-up')?.files[0]?.type.startsWith('video') ? (
                                                    <video src={formData.logo_url} className="w-16 h-16 object-cover rounded-lg shadow-xl border border-[#6c5ce750]" autoPlay loop muted />
                                                ) : (
                                                    <img src={formData.logo_url} className="w-16 h-16 object-contain rounded-lg shadow-xl" alt="Logo" />
                                                )
                                            ) : (
                                                <div className="w-16 h-16 bg-[#6c5ce740] backdrop-blur-md border border-[#6c5ce740] rounded-lg flex items-center justify-center text-[10px] font-black text-white">LOGO</div>
                                            )}
                                        </div>

                                        {/* Text Overlay Rendering */}
                                        {formData.overlay_text && (
                                            <div className={clsx(
                                                "absolute p-6 transition-all duration-300 whitespace-nowrap z-10",
                                                formData.text_pos === 'TL' && "top-0 left-0",
                                                formData.text_pos === 'TC' && "top-0 left-1/2 -translate-x-1/2",
                                                formData.text_pos === 'TR' && "top-0 right-0",
                                                formData.text_pos === 'ML' && "top-1/2 left-0 -translate-y-1/2",
                                                formData.text_pos === 'C' && "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2",
                                                formData.text_pos === 'MR' && "top-1/2 right-0 -translate-y-1/2",
                                                formData.text_pos === 'BL' && "bottom-0 left-0",
                                                formData.text_pos === 'BC' && "bottom-0 left-1/2 -translate-x-1/2",
                                                formData.text_pos === 'BR' && "bottom-0 right-0"
                                            )}>
                                                <span
                                                    className="px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-sm font-bold text-[14px] shadow-lg border border-white/10"
                                                    style={{ color: formData.text_color }}
                                                >
                                                    {formData.overlay_text}
                                                </span>
                                            </div>
                                        )}

                                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                            <Play size={40} className="text-white/5" />
                                        </div>
                                    </div>
                                </div>
                                <div className="text-center">
                                    <div className="text-[10px] text-[#6c5ce7] font-bold uppercase tracking-widest mb-1">Interactive Preview</div>
                                    <div className="text-[9px] text-[#3d4666]">CLICK ON FRAME TO POSITION LOGO OR TEXT</div>
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
                                    <select 
                                        value={formData.timezone} 
                                        onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                                        className="w-full bg-[#131829] border border-white/10 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#6c5ce7]"
                                    >
                                        <option value="Asia/Dhaka">Asia/Dhaka (UTC+6)</option>
                                        <option value="UTC">UTC</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider block mb-2">Publishing Days</label>
                                    <div className="flex flex-wrap gap-2">
                                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
                                            <div
                                                key={d}
                                                onClick={() => setFormData({ ...formData, days: formData.days.includes(d) ? formData.days.filter(x => x !== d) : [...formData.days, d] })}
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
                                                <X size={12} className="text-[#3d4666] cursor-pointer hover:text-white" onClick={() => setFormData({ ...formData, slots: formData.slots.filter(x => x !== t) })} />
                                            </div>
                                        ))}
                                    </div>
                                    <div className="flex gap-2">
                                        <input type="time" id="new-slot" className="flex-1 bg-[#131829] border border-white/10 rounded-xl px-4 py-2 text-sm outline-none" />
                                        <button className="btn btn-g px-4 py-2" onClick={() => {
                                            const val = document.getElementById('new-slot').value
                                            if (val) setFormData({ ...formData, slots: [...formData.slots, val].sort() })
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
                                        { l: 'Videos Found', v: foundVideos.length || '0' },
                                        { l: 'Daily Slots', v: `${formData.slots.length} per day` },
                                        { l: 'Timezone', v: formData.timezone },
                                        { l: 'Est. Duration', v: `${Math.ceil((foundVideos.length || 1) / formData.slots.length)} days` }
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
                    disabled={!canContinue()}
                    className={clsx(
                        "btn transition-all duration-300", 
                        step === 5 ? "btn-g3" : "btn-g",
                        !canContinue() && "opacity-50 cursor-not-allowed scale-95"
                    )}
                >
                    {step === 5 ? '🚀 Launch Pipeline' : 'Continue →'}
                </button>
            </div>
        </div>
    )
}
