import React, { useState } from 'react';
import { useWizard } from './WizardContext';
import { Calendar, Clock, MessageCircle, Info, Plus, X } from 'lucide-react';

export default function Step4Schedule() {
    const { state, dispatch } = useWizard();
    const config = state.scheduleConfig;

    // Derive local states for fast changing
    const [slotInput, setSlotInput] = useState('14:00');

    const updateConfig = (key, val) => {
        dispatch({ type: 'SET_SCHEDULE', payload: { [key]: val } });
    };

    const addTimeSlot = () => {
        if (slotInput && !config.slots.includes(slotInput)) {
            updateConfig('slots', [...config.slots, slotInput].sort());
        }
    };

    const removeTimeSlot = (slot) => {
        updateConfig('slots', config.slots.filter(s => s !== slot));
    };

    // Pre-fill some common timezones
    const commonTimezones = [
        Intl.DateTimeFormat().resolvedOptions().timeZone,
        'America/New_York', 'America/Los_Angeles', 'Europe/London',
        'Asia/Kolkata', 'Asia/Dhaka', 'Asia/Singapore', 'Australia/Sydney'
    ];

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
            <div className="flex flex-col gap-2 mb-6">
                <h2 className="text-2xl font-bold text-white">Step 4 — Schedule & Engagement</h2>
                <p className="text-white/50 text-sm">Define when your videos go live and how the system interacts with viewers.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left Column: Timing */}
                <div className="space-y-6 bg-white/5 p-6 rounded-xl border border-white/10">
                    <div className="flex items-center gap-2 mb-4">
                        <Clock className="w-5 h-5 text-brand-400" />
                        <h3 className="font-semibold text-white">Publishing Timeline</h3>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Timezone</label>
                        <select
                            value={config.timezone}
                            onChange={(e) => updateConfig('timezone', e.target.value)}
                            className="input w-full text-sm bg-slate-800"
                        >
                            {[...new Set(commonTimezones)].map(tz => (
                                <option key={tz} value={tz}>{tz}</option>
                            ))}
                        </select>
                        <p className="text-[10px] text-white/30 mt-1">Defaults to your browser's current timezone.</p>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Daily Frequency</label>
                        <p className="text-xs text-brand-300 mb-2 bg-brand-500/10 p-2 rounded-lg inline-block border border-brand-500/20">
                            Total {state.selectedMedia.length} videos will be spread out across these rules.
                        </p>
                        <input
                            type="number"
                            min="1" max="10"
                            value={config.frequency}
                            onChange={(e) => updateConfig('frequency', parseInt(e.target.value) || 1)}
                            className="input w-32 text-sm text-center block"
                        />
                        <span className="text-xs text-white/40 mt-1 block">videos per day per account.</span>
                    </div>

                    <div className="pt-4 border-t border-white/10">
                        <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Specific Time Slots (Optional)</label>
                        <div className="flex gap-2 mb-3">
                            <input
                                type="time"
                                value={slotInput}
                                onChange={(e) => setSlotInput(e.target.value)}
                                className="input w-32 text-sm"
                            />
                            <button onClick={addTimeSlot} className="btn-secondary py-1 px-3 text-sm flex gap-1 items-center">
                                <Plus className="w-4 h-4" /> Add Slot
                            </button>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {config.slots.map(s => (
                                <div key={s} className="badge-blue flex items-center gap-1.5 pl-3 pr-1.5 py-1">
                                    <span className="text-sm font-medium">{s}</span>
                                    <button onClick={() => removeTimeSlot(s)} className="text-brand-300 hover:text-white transition-colors">
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            ))}
                            {config.slots.length === 0 && (
                                <span className="text-xs text-white/30 italic">No specific slots set. System will calculate even intervals.</span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column: Comments & Overrides */}
                <div className="space-y-6">
                    <div className="bg-white/5 p-6 rounded-xl border border-white/10">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <MessageCircle className="w-5 h-5 text-brand-400" />
                                <h3 className="font-semibold text-white">Automated First Comment</h3>
                            </div>
                        </div>

                        <p className="text-xs text-white/50 mb-4 leading-relaxed">
                            Boost your video reach by automatically placing a pinned or first comment with links, hashtags, or AI-generated engaging questions.
                        </p>

                        <div className="space-y-3">
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="radio"
                                    name="commentMode"
                                    checked={config.commentMode === 'none'}
                                    onChange={() => updateConfig('commentMode', 'none')}
                                    className="w-4 h-4 text-brand-500 bg-white/5 border-white/20 focus:ring-brand-500"
                                />
                                <span className="text-sm text-white group-hover:text-brand-300 transition-colors">Disabled</span>
                            </label>

                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="radio"
                                    name="commentMode"
                                    checked={config.commentMode === 'auto'}
                                    onChange={() => updateConfig('commentMode', 'auto')}
                                    className="w-4 h-4 text-brand-500 bg-white/5 border-white/20 focus:ring-brand-500"
                                />
                                <span className="text-sm text-white group-hover:text-brand-300 transition-colors">AI Auto Engage (Questions/Emojis)</span>
                            </label>

                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="radio"
                                    name="commentMode"
                                    checked={config.commentMode === 'manual'}
                                    onChange={() => updateConfig('commentMode', 'manual')}
                                    className="w-4 h-4 text-brand-500 bg-white/5 border-white/20 focus:ring-brand-500"
                                />
                                <span className="text-sm text-white group-hover:text-brand-300 transition-colors">Strict Manual Link/Text</span>
                            </label>

                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="radio"
                                    name="commentMode"
                                    checked={config.commentMode === 'auto_manual'}
                                    onChange={() => updateConfig('commentMode', 'auto_manual')}
                                    className="w-4 h-4 text-brand-500 bg-white/5 border-white/20 focus:ring-brand-500"
                                />
                                <span className="text-sm text-white group-hover:text-brand-300 transition-colors">Manual Text + AI Hashtags</span>
                            </label>
                        </div>

                        {['manual', 'auto_manual'].includes(config.commentMode) && (
                            <div className="mt-4 pt-4 border-t border-white/10 animate-in fade-in duration-300">
                                <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Custom Comment Content</label>
                                <textarea
                                    value={config.manualComment}
                                    onChange={(e) => updateConfig('manualComment', e.target.value)}
                                    placeholder="Check out the full link in my bio! 👇"
                                    className="input w-full h-20 py-2 text-sm"
                                />
                            </div>
                        )}
                    </div>

                    <div className="bg-white/5 p-6 rounded-xl border border-white/10 border-dashed hover:border-solid transition-all cursor-pointer group">
                        <div className="flex items-center gap-3 text-white/40 group-hover:text-brand-400 transition-colors">
                            <Calendar className="w-5 h-5 flex-shrink-0" />
                            <div>
                                <span className="text-sm font-medium block text-white/60 group-hover:text-white transition-colors">Override with Specific Calendar Dates</span>
                                <span className="text-xs">Advanced feature coming soon. Stick to frequency rules for now.</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex justify-between pt-6 mt-6 border-t border-white/10">
                <button onClick={() => dispatch({ type: 'GO_TO_STEP', payload: 3 })} className="btn-secondary">Back to Metadata</button>
                <button onClick={() => dispatch({ type: 'GO_TO_STEP', payload: 5 })} className="btn-primary">
                    Proceed to Final Review
                </button>
            </div>
        </div>
    );
}
