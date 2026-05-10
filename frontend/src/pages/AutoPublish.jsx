import { useState, useEffect } from 'react'
import { fetchAccounts, triggerPipeline, syncAccountNow } from '../lib/api'
import { 
    Zap, RefreshCw, CheckCircle2, XCircle, Clock, 
    Youtube, Facebook, Instagram, Play, Send 
} from 'lucide-react'
import clsx from 'clsx'

export default function AutoPublish() {
    const [accounts, setAccounts] = useState([])
    const [loading, setLoading] = useState(true)

    const loadData = async () => {
        try {
            const res = await fetchAccounts()
            setAccounts(res.data)
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }

    useEffect(() => { loadData() }, [])

    return (
        <div className="space-y-6 animate-in">
            {/* ── Header ────────────────────────────────────────── */}
            <div className="sec-hd">
                <div>
                    <h1 className="text-2xl font-bold text-white">Auto Publish Monitor</h1>
                    <p className="text-[13px] text-[#7a85b0] mt-1">Real-time publishing queue across all platforms</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={loadData} className="btn btn-o btn-sm">
                        <RefreshCw className="w-3.5 h-3.5" /> Sync All
                    </button>
                    <button className="btn btn-g btn-sm">
                        <Zap className="w-3.5 h-3.5" /> Publish All Now
                    </button>
                </div>
            </div>

            {/* ── Stats Grid ────────────────────────────────────────── */}
            <div className="sg4">
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g3)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '22px' }}>18</div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Published Today</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '22px' }}>112</div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Pending Queue</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ color: 'var(--red)', fontSize: '22px' }}>6</div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Failed (retry)</div>
                </div>
                <div className="sc">
                    <div className="sv" style={{ background: 'var(--g2)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '22px' }}>4</div>
                    <div className="sl text-[10px] font-bold uppercase tracking-wider">Active Pipelines</div>
                </div>
            </div>

            {/* ── Grid ─────────────────────────────────────────── */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {accounts.map(account => (
                    <div key={account.id} className="bg-[#0d1120] border border-white/5 rounded-[20px] overflow-hidden transition-all hover:border-white/10 group">
                        <div className="p-4 flex items-center gap-3 border-b border-white/5">
                            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-xl">
                                {account.platform === 'youtube' ? '▶' : account.platform === 'facebook' ? 'f' : '◉'}
                            </div>
                            <div className="flex-1">
                                <div className="text-[14px] font-bold text-white">{account.name}</div>
                                <div className="text-[11px] text-[#7a85b0]">{account.platform}</div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={clsx("badge", account.status === 'active' ? "b-green" : "b-red")}>
                                    {account.status}
                                </span>
                                <div className="w-8 h-4 bg-[#00b89410] rounded-full relative">
                                    <div className={clsx("absolute top-0.5 w-3 h-3 rounded-full", account.status === 'active' ? "right-0.5 bg-[#00b894]" : "left-0.5 bg-[#3d4666]")} />
                                </div>
                            </div>
                        </div>

                        <div className="p-4 space-y-4">
                            <div className="grid grid-cols-4 gap-2">
                                {[
                                    { l: 'Pub', v: 42, g: 'var(--g3)' },
                                    { l: 'Pend', v: 18, g: 'var(--g4)' },
                                    { l: 'Fail', v: 0, c: '#3d4666' },
                                    { l: 'Queue', v: 12, g: 'var(--g2)' }
                                ].map((s, i) => (
                                    <div key={i} className="bg-[#131829] rounded-lg p-2 text-center">
                                        <div className="text-[14px] font-bold" style={s.g ? { background: s.g, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' } : { color: s.c }}>{s.v}</div>
                                        <div className="text-[9px] text-[#3d4666] font-bold uppercase">{s.l}</div>
                                    </div>
                                ))}
                            </div>

                            <div className="bg-[#131829] rounded-xl py-2 px-3 text-center text-[11px] text-[#7a85b0]">
                                ⏰ Next publish: <b className="text-white ml-1">2h 15m</b>
                            </div>

                            <div className="flex gap-1.5">
                                <button className="flex-1 btn btn-o !p-2 text-[11px] gap-1.5 hover:text-[#00b894] hover:border-[#00b894]">
                                    <Play size={12} /> Publish Now
                                </button>
                                <button className="flex-1 btn btn-o !p-2 text-[11px] gap-1.5 hover:text-[#00cec9] hover:border-[#00cec9]">
                                    <RefreshCw size={12} /> Sync
                                </button>
                                <button className="flex-1 btn btn-o !p-2 text-[11px] gap-1.5 hover:text-[#fdcb6e] hover:border-[#fdcb6e]">
                                    <Send size={12} /> Instant
                                </button>
                            </div>
                        </div>

                        <div className="p-3 border-t border-white/5 flex justify-between items-center text-[11px] text-[#3d4666]">
                            <div>Drive videos: <span className="text-[#7a85b0] font-bold">18 ready</span></div>
                            <div>Last sync: 5m ago</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
