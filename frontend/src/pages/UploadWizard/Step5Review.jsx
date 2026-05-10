import React, { useState } from 'react';
import { useWizard } from './WizardContext';
import { createAutoDrip } from '../../lib/api';
import { CheckCircle2, Edit2, Rocket, Loader2, AlertTriangle } from 'lucide-react';

export default function Step5Review() {
    const { state, dispatch } = useWizard();
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    // Quick edit navigation
    const editStep = (step) => dispatch({ type: 'GO_TO_STEP', payload: step });

    const handleLaunch = async () => {
        setSubmitting(true);
        setError(null);

        try {
            // Assemble the complex payload combining the entire wizard state into the structure expected by the backend
            const payload = {
                targets: state.selectedAccounts.map(a => a.id),
                media_pool: state.selectedMedia.map(m => m.id),
                schedule_config: {
                    timezone: state.scheduleConfig.timezone,
                    frequency: state.scheduleConfig.frequency,
                    time_slots: state.scheduleConfig.slots.length > 0 ? state.scheduleConfig.slots : null,
                    comment_mode: state.scheduleConfig.commentMode,
                    manual_comment: state.scheduleConfig.manualComment,
                },
                metadata_overrides: {
                    mode: state.metadataConfig.mode,
                    custom_title_append: state.metadataConfig.customTitle,
                    custom_description: state.metadataConfig.customDescription,
                    tags: state.metadataConfig.tags,
                    editor_elements: state.editorElements, // Advanced Drag & Drop Overlay JSON
                    add_watermark: state.metadataConfig.addWatermark
                }
            };

            // Assuming backend createAutoDrip can handle this extended payload
            await createAutoDrip(payload);

            setSuccess(true);
            setTimeout(() => {
                dispatch({ type: 'RESET_WIZARD' });
                // Optionally redirect or reset
            }, 3000);

        } catch (err) {
            setError(err.message || "Failed to initialize pipeline.");
        } finally {
            setSubmitting(false);
        }
    };

    if (success) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-center animate-in zoom-in-95 duration-500">
                <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mb-6 ring-4 ring-green-500/30">
                    <CheckCircle2 className="w-10 h-10 text-green-400" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-2">System Initialized!</h2>
                <p className="text-white/60 max-w-md mx-auto">
                    Your videos are currently being rendered with your custom overlays and metadata. They will be progressively published according to your schedule.
                </p>
            </div>
        );
    }

    // Warning for edge cases
    const validationWarnings = [];
    if (state.selectedAccounts.length === 0) validationWarnings.push("No accounts selected in Step 1.");
    if (state.selectedMedia.length === 0) validationWarnings.push("No videos selected in Step 2.");

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto pb-12">
            <div className="flex flex-col gap-2 mb-8">
                <h2 className="text-3xl font-bold text-white">Final Review</h2>
                <p className="text-white/50 text-sm">Verify all configurations before launching the automated pipeline.</p>
            </div>

            {validationWarnings.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-start gap-3 text-red-400">
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                        <h4 className="font-semibold text-sm">Cannot Launch Pipeline</h4>
                        <ul className="list-disc pl-4 text-xs">
                            {validationWarnings.map((warn, i) => <li key={i}>{warn}</li>)}
                        </ul>
                    </div>
                </div>
            )}

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl text-red-400 text-sm">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Step 1 Summary */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 relative group">
                    <button onClick={() => editStep(1)} className="absolute top-4 right-4 text-white/30 hover:text-brand-400 transition-colors opacity-0 group-hover:opacity-100"><Edit2 className="w-4 h-4" /></button>
                    <p className="text-xs text-brand-400 font-semibold tracking-wider uppercase mb-1">Step 1: Targets</p>
                    <div className="flex flex-wrap gap-2 mt-3">
                        {state.selectedAccounts.map(a => (
                            <span key={a.id} className="text-xs font-medium bg-black/30 border border-white/5 px-2 py-1 rounded-md text-white/80">{a.channel_name}</span>
                        ))}
                    </div>
                    <p className="text-white/40 text-xs mt-2">{state.selectedAccounts.length} accounts selected</p>
                </div>

                {/* Step 2 Summary */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 relative group">
                    <button onClick={() => editStep(2)} className="absolute top-4 right-4 text-white/30 hover:text-brand-400 transition-colors opacity-0 group-hover:opacity-100"><Edit2 className="w-4 h-4" /></button>
                    <p className="text-xs text-brand-400 font-semibold tracking-wider uppercase mb-1">Step 2: Media</p>
                    <p className="text-white text-lg font-medium mt-1">{state.selectedMedia.length} Videos queued</p>
                    <p className="text-white/40 text-[10px] mt-1 truncate max-w-[200px]">{state.driveLink || "No Drive link provided"}</p>
                </div>

                {/* Step 3 Summary */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 relative group">
                    <button onClick={() => editStep(3)} className="absolute top-4 right-4 text-white/30 hover:text-brand-400 transition-colors opacity-0 group-hover:opacity-100"><Edit2 className="w-4 h-4" /></button>
                    <p className="text-xs text-brand-400 font-semibold tracking-wider uppercase mb-1">Step 3: Editor & Meta</p>
                    <div className="space-y-1 mt-3 text-sm">
                        <div className="flex justify-between"><span className="text-white/40">Title Mode:</span><span className="text-white font-medium capitalize">{state.metadataConfig.mode}</span></div>
                        <div className="flex justify-between"><span className="text-white/40">Watermark:</span><span className={state.metadataConfig.addWatermark ? "text-green-400 font-medium" : "text-white/50 font-medium"}>{state.metadataConfig.addWatermark ? "Enabled" : "Disabled (Optional)"}</span></div>
                        <div className="flex justify-between"><span className="text-white/40">Active Overlays:</span><span className="text-brand-300 font-medium">{state.editorElements.length} Visual Elements</span></div>
                    </div>
                </div>

                {/* Step 4 Summary */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 relative group">
                    <button onClick={() => editStep(4)} className="absolute top-4 right-4 text-white/30 hover:text-brand-400 transition-colors opacity-0 group-hover:opacity-100"><Edit2 className="w-4 h-4" /></button>
                    <p className="text-xs text-brand-400 font-semibold tracking-wider uppercase mb-1">Step 4: Schedule</p>
                    <div className="space-y-1 mt-3 text-sm">
                        <div className="flex justify-between"><span className="text-white/40">Timezone:</span><span className="text-white font-medium truncate max-w-[150px]">{state.scheduleConfig.timezone}</span></div>
                        <div className="flex justify-between"><span className="text-white/40">Frequency:</span><span className="text-white font-medium">{state.scheduleConfig.frequency} / day / acc</span></div>
                        <div className="flex justify-between"><span className="text-white/40">Comments:</span><span className="text-white font-medium capitalize">{state.scheduleConfig.commentMode.replace('_', ' + ')}</span></div>
                    </div>
                </div>
            </div>

            <div className="flex justify-between items-center pt-8 mt-8 border-t border-white/10">
                <button onClick={() => editStep(4)} disabled={submitting} className="text-white/40 hover:text-white transition-colors text-sm font-medium">
                    ← Back
                </button>

                <button
                    onClick={handleLaunch}
                    disabled={submitting || validationWarnings.length > 0}
                    className="bg-gradient-to-r from-brand-600 to-indigo-500 hover:from-brand-500 hover:to-indigo-400 text-white px-8 py-3 rounded-xl font-bold shadow-[0_0_30px_rgba(99,102,241,0.3)] hover:shadow-[0_0_40px_rgba(99,102,241,0.5)] transition-all flex items-center gap-3 disabled:opacity-50 disabled:grayscale"
                >
                    {submitting ? (
                        <><Loader2 className="w-5 h-5 animate-spin" /> Compiling Assets...</>
                    ) : (
                        <><Rocket className="w-5 h-5" /> Launch Automated Pipeline</>
                    )}
                </button>
            </div>
        </div>
    );
}
