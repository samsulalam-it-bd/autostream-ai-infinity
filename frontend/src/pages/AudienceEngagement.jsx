import { useState, useEffect } from 'react';
import { BotMessageSquare, Settings2, History, Power, ShieldAlert, Cpu } from 'lucide-react';
import api from '../lib/api';

export default function AudienceEngagement() {
    const [activeTab, setActiveTab] = useState('rules'); // rules, logs
    const [accounts, setAccounts] = useState([]);
    const [rules, setRules] = useState([]);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    // Form State
    const [selectedAccountId, setSelectedAccountId] = useState('');
    const [keywords, setKeywords] = useState('');
    const [persona, setPersona] = useState('Helpful and friendly, use emojis. Keep it short.');
    const [autoReply, setAutoReply] = useState(true);
    const [autoDm, setAutoDm] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [accRes, rulesRes, logsRes] = await Promise.all([
                api.getAccounts(),
                api.client.get('/comments/rules'),
                api.client.get('/comments/logs?limit=50')
            ]);
            setAccounts(accRes.filter(a => a.status === 'active' || a.status === 'ACTIVE'));
            setRules(rulesRes.data);
            setLogs(logsRes.data);
        } catch (err) {
            alert('Failed to load engagement data');
        } finally {
            setLoading(false);
        }
    };

    const handleSaveRule = async (e) => {
        e.preventDefault();
        if (!selectedAccountId) {
            alert('Please select an account first');
            return;
        }
        setSaving(true);
        try {
            const payload = {
                account_id: selectedAccountId,
                custom_keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
                auto_reply_enabled: autoReply,
                auto_dm_enabled: autoDm,
                ai_persona: persona
            };
            await api.client.post('/comments/rules', payload);
            alert('Engagement rule saved successfully!');
            fetchData(); // Refresh list
        } catch (err) {
            alert('Failed to save rule');
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteRule = async (id) => {
        if (!window.confirm('Are you sure you want to delete this rule?')) return;
        try {
            await api.client.delete(`/comments/rules/${id}`);
            alert('Rule deleted');
            fetchData();
        } catch (err) {
            alert('Failed to delete rule');
        }
    }

    // Find existing rule if user selects an account
    useEffect(() => {
        if (selectedAccountId) {
            const existing = rules.find(r => r.account_id === selectedAccountId);
            if (existing) {
                setKeywords(existing.custom_keywords?.join(', ') || '');
                setPersona(existing.ai_persona || '');
                setAutoReply(existing.auto_reply_enabled);
                setAutoDm(existing.auto_dm_enabled);
            } else {
                setKeywords('');
                setPersona('Helpful and friendly, use emojis. Keep it short.');
                setAutoReply(true);
                setAutoDm(false);
            }
        }
    }, [selectedAccountId, rules]);

    if (loading) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-7xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                    <BotMessageSquare className="w-8 h-8 text-indigo-500" />
                    AI Audience Engagement
                </h1>
                <p className="text-gray-400">
                    Automatically reply to comments and send DMs using Google Gemini UI. Real-time engagement boosts algorithm reach.
                </p>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-gray-800 pb-2">
                <button
                    onClick={() => setActiveTab('rules')}
                    className={`flex items-center gap-2 px-4 py-2 font-medium rounded-t-lg transition-colors ${activeTab === 'rules' ? 'bg-indigo-500/10 text-indigo-400 border-b-2 border-indigo-500' : 'text-gray-400 hover:text-white hover:bg-gray-800'
                        }`}
                >
                    <Settings2 className="w-5 h-5" />
                    Rules & Setup
                </button>
                <button
                    onClick={() => setActiveTab('logs')}
                    className={`flex items-center gap-2 px-4 py-2 font-medium rounded-t-lg transition-colors ${activeTab === 'logs' ? 'bg-indigo-500/10 text-indigo-400 border-b-2 border-indigo-500' : 'text-gray-400 hover:text-white hover:bg-gray-800'
                        }`}
                >
                    <History className="w-5 h-5" />
                    Engagement Logs
                </button>
            </div>

            {/* Tab Content */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                {activeTab === 'rules' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                        {/* Left Col: Setup Form */}
                        <div>
                            <h2 className="text-xl font-semibold text-white mb-6">Configure AI Auto-Reply</h2>
                            <form onSubmit={handleSaveRule} className="space-y-5">

                                {/* Account Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Target Account</label>
                                    <select
                                        required
                                        value={selectedAccountId}
                                        onChange={(e) => setSelectedAccountId(e.target.value)}
                                        className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                                    >
                                        <option value="">-- Select an Active Account --</option>
                                        {accounts.map(acc => (
                                            <option key={acc.id} value={acc.id}>
                                                {acc.platform.toUpperCase()} - {acc.channel_name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                {/* Keywords Toggle (Optional) */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Trigger Keywords (Optional)</label>
                                    <p className="text-xs text-gray-500 mb-2">If empty, AI replies to ALL comments. Comma separated (e.g., price, link, how to)</p>
                                    <input
                                        type="text"
                                        value={keywords}
                                        onChange={(e) => setKeywords(e.target.value)}
                                        placeholder="e.g. price, interested, detail"
                                        className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                                    />
                                </div>

                                {/* AI Persona Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">AI Persona (System Prompt)</label>
                                    <p className="text-xs text-gray-500 mb-2">How should the AI behave when replying?</p>
                                    <textarea
                                        required
                                        rows="3"
                                        value={persona}
                                        onChange={(e) => setPersona(e.target.value)}
                                        className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                                        placeholder="e.g. Very enthusiastic, use fire emojis..."
                                    />
                                </div>

                                {/* Toggles */}
                                <div className="flex gap-6 pt-2">
                                    <label className="flex items-center cursor-pointer">
                                        <div className="relative">
                                            <input type="checkbox" className="sr-only" checked={autoReply} onChange={(e) => setAutoReply(e.target.checked)} />
                                            <div className={`block w-14 h-8 rounded-full transition-colors ${autoReply ? 'bg-indigo-600' : 'bg-gray-700'}`}></div>
                                            <div className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${autoReply ? 'transform translate-x-6' : ''}`}></div>
                                        </div>
                                        <div className="ml-3 text-white font-medium flex items-center gap-2">
                                            <BotMessageSquare className="w-4 h-4 text-gray-400" />
                                            Enable Auto Reply
                                        </div>
                                    </label>

                                    <label className="flex items-center cursor-pointer">
                                        <div className="relative">
                                            <input type="checkbox" className="sr-only" checked={autoDm} onChange={(e) => setAutoDm(e.target.checked)} />
                                            <div className={`block w-14 h-8 rounded-full transition-colors ${autoDm ? 'bg-emerald-600' : 'bg-gray-700'}`}></div>
                                            <div className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${autoDm ? 'transform translate-x-6' : ''}`}></div>
                                        </div>
                                        <div className="ml-3 text-white font-medium flex items-center gap-2">
                                            <Settings2 className="w-4 h-4 text-gray-400" />
                                            Enable Auto DM
                                        </div>
                                    </label>
                                </div>

                                <div className="pt-4">
                                    <button
                                        type="submit"
                                        disabled={saving}
                                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                    >
                                        {saving ? 'Saving...' : 'Save Rule & Activate AI'}
                                    </button>
                                </div>
                            </form>
                        </div>

                        {/* Right Col: Active Rules Table */}
                        <div>
                            <h2 className="text-xl font-semibold text-white mb-6">Active AI Rules</h2>
                            {rules.length === 0 ? (
                                <div className="flex flex-col items-center justify-center bg-gray-800/50 rounded-xl p-8 border border-dashed border-gray-700 h-64">
                                    <ShieldAlert className="w-12 h-12 text-gray-500 mb-3" />
                                    <p className="text-gray-400">No automation rules active yet.</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {rules.map(rule => {
                                        const acc = accounts.find(a => a.id === rule.account_id);
                                        return (
                                            <div key={rule.id} className="bg-gray-800 border border-gray-700 rounded-lg p-5 flex flex-col gap-3 relative overflow-hidden group">
                                                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <h4 className="text-white font-medium text-lg">
                                                            {acc ? `${acc.platform.toUpperCase()} - ${acc.channel_name}` : 'Unknown Account'}
                                                        </h4>
                                                        <p className="text-sm text-gray-400 mt-1 line-clamp-1">Persona: {rule.ai_persona}</p>
                                                    </div>
                                                    <button onClick={() => handleDeleteRule(rule.id)} className="text-red-400 hover:text-red-300 text-sm">Delete</button>
                                                </div>
                                                <div className="flex gap-2">
                                                    {rule.auto_reply_enabled && <span className="bg-indigo-500/20 text-indigo-300 text-xs px-2 py-1 rounded">Auto-Reply ON</span>}
                                                    {rule.auto_dm_enabled && <span className="bg-emerald-500/20 text-emerald-300 text-xs px-2 py-1 rounded">Auto-DM ON</span>}
                                                    {rule.custom_keywords && rule.custom_keywords.length > 0 && (
                                                        <span className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded">{rule.custom_keywords.length} Keywords</span>
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

                {/* Logs Tab */}
                {activeTab === 'logs' && (
                    <div>
                        <div className="flex justify-between items-end mb-6">
                            <h2 className="text-xl font-semibold text-white">Recent AI Engagement Logs</h2>
                            <button onClick={fetchData} className="text-sm text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                                <Power className="w-4 h-4" /> Refresh Logs
                            </button>
                        </div>

                        {logs.length === 0 ? (
                            <div className="text-center py-12 text-gray-500 bg-gray-800/30 rounded-lg">
                                <p>No engagement logs recorded yet.</p>
                                <p className="text-sm mt-2">Logs will appear here when the AI replies to a comment.</p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm text-gray-400">
                                    <thead className="text-xs text-gray-500 uppercase bg-gray-800">
                                        <tr>
                                            <th className="px-6 py-4 rounded-tl-lg">Time</th>
                                            <th className="px-6 py-4">User</th>
                                            <th className="px-6 py-4">Original Comment</th>
                                            <th className="px-6 py-4">AI Reply</th>
                                            <th className="px-6 py-4 rounded-tr-lg">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {logs.map(log => (
                                            <tr key={log.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    {new Date(log.created_at).toLocaleString()}
                                                </td>
                                                <td className="px-6 py-4 font-medium text-white">
                                                    {log.author_name || 'Unknown'} <span className="text-xs text-gray-500 block">{log.platform}</span>
                                                </td>
                                                <td className="px-6 py-4 max-w-xs truncate" title={log.comment_text}>
                                                    {log.comment_text}
                                                </td>
                                                <td className="px-6 py-4 max-w-xs text-gray-300" title={log.ai_reply_text}>
                                                    <div className="flex items-start gap-2">
                                                        <Cpu className="w-4 h-4 mt-0.5 text-indigo-400 shrink-0" />
                                                        <span className="line-clamp-2">{log.ai_reply_text || 'Skipped / Failed'}</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    {log.dm_sent ? (
                                                        <span className="text-xs font-medium px-2.5 py-0.5 rounded bg-emerald-900 text-emerald-300 border border-emerald-800">DM Sent</span>
                                                    ) : (
                                                        <span className="text-xs font-medium px-2.5 py-0.5 rounded bg-gray-800 text-gray-400">Public Reply</span>
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
        </div>
    );
}
