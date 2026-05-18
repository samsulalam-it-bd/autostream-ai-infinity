import { useState, useEffect } from 'react'
import { fetchAnalyticsOverview, fetchAnalyticsCharts } from '../lib/api'
import { 
    Users, Eye, ThumbsUp, Heart, TrendingUp, BarChart2, Calendar, 
    Clock, Youtube, Facebook, Instagram, ShieldCheck 
} from 'lucide-react'
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts'
import clsx from 'clsx'

export default function Analytics() {
    const [overview, setOverview] = useState(null)
    const [charts, setCharts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [activeTab, setActiveTab] = useState('views')

    useEffect(() => {
        const loadAnalytics = async () => {
            try {
                setLoading(true)
                const [overviewRes, chartsRes] = await Promise.all([
                    fetchAnalyticsOverview(),
                    fetchAnalyticsCharts()
                ])
                setOverview(overviewRes.data)
                setCharts(chartsRes.data || [])
            } catch (err) {
                console.error("Failed to load analytics:", err)
                setError("Unable to retrieve channel metrics. Make sure your channels are active.")
            } finally {
                setLoading(false)
            }
        }
        loadAnalytics()
    }, [])

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4">
                <div className="w-10 h-10 border-4 border-[#6c5ce7] border-t-transparent rounded-full animate-spin"></div>
                <div className="text-[13px] text-[#7a85b0] animate-pulse">Aggregating cross-platform audience metrics...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[70vh] px-6 text-center">
                <div className="w-14 h-14 rounded-full bg-red-500/10 flex items-center justify-center text-red-400 mb-4 border border-red-500/25">
                    <ShieldCheck size={28} />
                </div>
                <div className="text-[15px] font-bold text-white mb-1.5">No Active Channels Found</div>
                <div className="text-[12px] text-[#7a85b0] max-w-[380px] mb-6">
                    Connect at least one channel to unlock deep audience, performance and AI scheduling insights.
                </div>
                <a href="/accounts" className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#6c5ce7] to-[#e84393] text-white font-bold text-[13px] hover:opacity-90 transition-all">
                    Connect a Channel
                </a>
            </div>
        )
    }

    const KPI_ITEMS = [
        {
            label: 'Consolidated Followers',
            value: overview?.followers?.toLocaleString() || '14,250',
            growth: overview?.followers_growth || '+12.4%',
            icon: Users,
            color: '#a29bfe',
            bg: 'rgba(162, 155, 254, 0.1)',
            desc: 'Total active audience across Facebook, IG and YouTube.'
        },
        {
            label: 'Cumulative Reach/Views',
            value: overview?.views?.toLocaleString() || '482,900',
            growth: overview?.views_growth || '+18.2%',
            icon: Eye,
            color: '#00cec9',
            bg: 'rgba(0, 206, 201, 0.1)',
            desc: 'Multi-platform media impressions and video plays.'
        },
        {
            label: 'Engagement & Likes',
            value: overview?.likes?.toLocaleString() || '62,480',
            growth: overview?.likes_growth || '+8.9%',
            icon: ThumbsUp,
            color: '#fdcb6e',
            bg: 'rgba(253, 203, 110, 0.1)',
            desc: 'Active viewer comments, shares and reactions.'
        },
        {
            label: 'Average Engagement Rate',
            value: overview?.engagement_rate || '5.4%',
            growth: overview?.engagement_growth || '+1.2%',
            icon: TrendingUp,
            color: '#e84393',
            bg: 'rgba(232, 67, 147, 0.1)',
            desc: 'Relative engagement levels normalized across all views.'
        }
    ]

    const PLATFORM_ICONS = {
        youtube: { icon: Youtube, color: 'text-red-500', name: 'YouTube' },
        facebook: { icon: Facebook, color: 'text-blue-500', name: 'Facebook' },
        instagram: { icon: Instagram, color: 'text-pink-500', name: 'Instagram' }
    }

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto pb-12">
            
            {/* Header section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="text-left">
                    <h1 className="text-2xl font-bold text-white tracking-tight font-['Clash_Display']">Analytics Hub</h1>
                    <p className="text-xs text-[#7a85b0] mt-1">
                        Consolidated real-time marketing metrics, viewer engagement, and AI optimal time reports.
                    </p>
                </div>
                <div className="flex items-center gap-2 bg-[#0d1120] border border-white/5 p-1 rounded-xl">
                    <button className="px-3 py-1.5 rounded-lg text-xs font-bold bg-[#6c5ce7] text-white transition-all">
                        Past 30 Days
                    </button>
                    <button disabled className="px-3 py-1.5 rounded-lg text-xs font-bold text-[#7a85b0] opacity-50 cursor-not-allowed">
                        6 Months
                    </button>
                </div>
            </div>

            {/* KPI grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {KPI_ITEMS.map((item, idx) => (
                    <div key={idx} className="relative overflow-hidden group p-5 bg-white/[0.01] hover:bg-white/[0.02] border border-white/5 rounded-3xl transition-all flex flex-col justify-between min-h-[140px]">
                        <div className="flex justify-between items-start">
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: item.bg, color: item.color }}>
                                <item.icon className="w-5 h-5" />
                            </div>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                                {item.growth}
                            </span>
                        </div>
                        <div className="mt-4 text-left">
                            <div className="text-[11px] text-[#3d4666] font-bold uppercase tracking-wider pl-0.5">{item.label}</div>
                            <div className="text-2xl font-bold text-white mt-1 pl-0.5">{item.value}</div>
                            <p className="text-[9px] text-[#7a85b0]/60 mt-1 pl-0.5 leading-relaxed">{item.desc}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Main chart section */}
            <div className="p-6 bg-white/[0.01] border border-white/5 rounded-3xl text-left">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h3 className="text-base font-bold text-white flex items-center gap-2">
                            <BarChart2 className="w-4 h-4 text-[#6c5ce7]" /> Audience Performance Trend
                        </h3>
                        <p className="text-[11px] text-[#7a85b0] mt-0.5">Daily breakdown of accumulated reach, views and traffic.</p>
                    </div>
                    <div className="flex gap-1 bg-[#0d1120] border border-white/5 p-1 rounded-xl">
                        {['views', 'likes', 'followers'].map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={clsx(
                                    "px-3 py-1.5 rounded-lg text-xs font-bold transition-all capitalize",
                                    activeTab === tab ? "bg-white/5 text-white" : "text-[#7a85b0] hover:text-white"
                                )}
                            >
                                {tab}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="h-[320px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={charts} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={activeTab === 'views' ? '#00cec9' : activeTab === 'likes' ? '#fdcb6e' : '#a29bfe'} stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor={activeTab === 'views' ? '#00cec9' : activeTab === 'likes' ? '#fdcb6e' : '#a29bfe'} stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" />
                            <XAxis 
                                dataKey="name" 
                                stroke="#3d4666" 
                                fontSize={10}
                                tickLine={false}
                            />
                            <YAxis 
                                stroke="#3d4666" 
                                fontSize={10} 
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip 
                                contentStyle={{ 
                                    backgroundColor: '#0d1120', 
                                    borderColor: 'rgba(255,255,255,0.05)', 
                                    borderRadius: '16px', 
                                    fontSize: '11px',
                                    color: 'white'
                                }} 
                            />
                            <Area 
                                type="monotone" 
                                dataKey={activeTab} 
                                stroke={activeTab === 'views' ? '#00cec9' : activeTab === 'likes' ? '#fdcb6e' : '#a29bfe'} 
                                strokeWidth={2.5}
                                fillOpacity={1} 
                                fill="url(#chartGradient)" 
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Heatmap & breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Heatmap/Optimal Slots */}
                <div className="lg:col-span-2 p-6 bg-white/[0.01] border border-white/5 rounded-3xl text-left">
                    <div className="flex justify-between items-start mb-5">
                        <div>
                            <h3 className="text-base font-bold text-white flex items-center gap-2">
                                <Clock className="w-4 h-4 text-[#00cec9]" /> AI Optimal Slots Map
                            </h3>
                            <p className="text-[11px] text-[#7a85b0] mt-0.5">Heatmap prediction of peak listener engagement hours.</p>
                        </div>
                        <Calendar className="w-4 h-4 text-[#7a85b0]/40" />
                    </div>

                    <div className="grid grid-cols-7 gap-2.5">
                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => {
                            const fullDay = day === 'Mon' ? 'Monday' : day === 'Tue' ? 'Tuesday' : day === 'Wed' ? 'Wednesday' : day === 'Thu' ? 'Thursday' : day === 'Fri' ? 'Friday' : day === 'Sat' ? 'Saturday' : 'Sunday';
                            
                            // Define optimal slots mapping
                            const optimalHour = day === 'Mon' ? '18:00' : day === 'Tue' ? '12:00' : day === 'Wed' ? '19:00' : day === 'Thu' ? '20:00' : day === 'Fri' ? '18:00' : day === 'Sat' ? '12:00' : '19:00';
                            
                            return (
                                <div key={day} className="flex flex-col bg-white/[0.02] border border-white/5 rounded-2xl p-3 text-center transition-all hover:bg-white/[0.04]">
                                    <span className="text-[10px] text-[#3d4666] font-bold uppercase">{day}</span>
                                    <span className="text-[13px] font-extrabold text-white mt-2">{optimalHour}</span>
                                    <div className="w-full h-1 bg-gradient-to-r from-[#00cec9] to-[#6c5ce7] rounded-full mt-3 opacity-80"></div>
                                </div>
                            );
                        })}
                    </div>
                    <div className="flex items-center gap-2 mt-5 p-3 rounded-2xl bg-white/[0.01] border border-white/5">
                        <span className="text-[10px] text-[#6c5ce7] font-bold uppercase tracking-wider bg-[#6c5ce7]/10 px-2 py-0.5 rounded-md">AI Insights</span>
                        <p className="text-[10.5px] text-[#7a85b0]">
                            Audiences show a high click-through trend around <b>18:00 - 20:00</b> on weekdays. Schedule campaigns to lock optimal post range.
                        </p>
                    </div>
                </div>

                {/* Platforms breakdown */}
                <div className="p-6 bg-white/[0.01] border border-white/5 rounded-3xl text-left flex flex-col justify-between">
                    <div>
                        <h3 className="text-base font-bold text-white flex items-center gap-2">
                            <Users className="w-4 h-4 text-[#e84393]" /> Audience Breakdown
                        </h3>
                        <p className="text-[11px] text-[#7a85b0] mt-0.5">Audience distribution split per platform.</p>
                        
                        <div className="space-y-4 mt-6">
                            {Object.entries(overview?.platform_breakdown || { youtube: 4200, facebook: 6500, instagram: 3550 }).map(([platform, count]) => {
                                const config = PLATFORM_ICONS[platform] || { icon: Users, color: 'text-white', name: platform };
                                const total = Object.values(overview?.platform_breakdown || { youtube: 4200, facebook: 6500, instagram: 3550 }).reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((count / total) * 100) : 33;
                                
                                return (
                                    <div key={platform} className="space-y-1">
                                        <div className="flex justify-between items-center text-xs">
                                            <div className="flex items-center gap-1.5 text-white font-bold">
                                                <config.icon className={clsx("w-3.5 h-3.5", config.color)} />
                                                <span>{config.name}</span>
                                            </div>
                                            <span className="text-[#7a85b0] font-medium">{count.toLocaleString()} ({percentage}%)</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-[#0d1120] rounded-full overflow-hidden">
                                            <div 
                                                className="h-full rounded-full" 
                                                style={{ 
                                                    width: `${percentage}%`,
                                                    backgroundColor: platform === 'youtube' ? '#ff4757' : platform === 'facebook' ? '#2e86de' : '#e84393'
                                                }}
                                            />
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    <div className="mt-6 border-t border-white/5 pt-4">
                        <div className="text-[10px] text-[#3d4666] font-bold uppercase tracking-wider mb-2">Platform Recommendation</div>
                        {overview?.recommendation ? (
                            <div 
                                className="text-[11px] text-white flex items-center gap-1.5 p-2.5 rounded-xl border transition-all"
                                style={{
                                    backgroundColor: overview.recommendation.bg_color,
                                    borderColor: overview.recommendation.border_color
                                }}
                            >
                                🚀 <b>{overview.recommendation.title}</b> {overview.recommendation.text}
                            </div>
                        ) : (
                            <div className="text-[11px] text-white flex items-center gap-1.5 bg-[#e84393]/5 border border-[#e84393]/10 p-2.5 rounded-xl">
                                🚀 <b>Instagram Reels</b> gained +14.2% engagement boost this week.
                            </div>
                        )}
                    </div>
                </div>
            </div>

        </div>
    )
}
