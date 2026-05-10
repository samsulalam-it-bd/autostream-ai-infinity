import React, { useState } from 'react';
import { useWizard } from './WizardContext';
import AdvancedMediaEditor from './AdvancedMediaEditor';
import { Sparkles, Type, FileImage, Settings2, Plus } from 'lucide-react';

export default function Step3MetadataEditor() {
    const { state, dispatch } = useWizard();
    const config = state.metadataConfig;

    // For preview, we just show the first selected video
    const previewVideo = state.selectedMedia[0];
    const videoSrc = previewVideo ? `https://drive.google.com/uc?id=${previewVideo.drive_file_id}` : null;

    const handleConfigChange = (key, value) => {
        dispatch({ type: 'SET_METADATA_CONFIG', payload: { [key]: value } });
    };

    const addTextElement = () => {
        dispatch({
            type: 'ADD_EDITOR_ELEMENT',
            payload: {
                id: Date.now().toString(),
                type: 'text',
                content: 'Double Tap to Edit',
                x: 50, y: 50, width: 200, height: 60,
                color: '#ffffff', bgColor: 'transparent'
            }
        });
    };

    const addLogoElement = () => {
        // In a real scenario, this would trigger a file picker or predefined asset gallery.
        // For now, we add a placeholder image that can be customized.
        const logoUrl = prompt("Enter Logo URL (or leave blank for placeholder):") || "https://placehold.co/150x150/png?text=LOGO";

        dispatch({
            type: 'ADD_EDITOR_ELEMENT',
            payload: {
                id: Date.now().toString(),
                type: 'logo',
                content: logoUrl,
                x: 20, y: 20, width: 100, height: 100
            }
        });
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col gap-2 mb-6">
                <h2 className="text-2xl font-bold text-white">Step 3 — Metadata & Visual Editor</h2>
                <p className="text-white/50 text-sm">Configure how your videos are titled and edit their visual overlays.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Pane: Metadata */}
                <div className="lg:col-span-5 space-y-6 bg-white/5 p-6 rounded-xl border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                        <Settings2 className="w-5 h-5 text-brand-400" />
                        <h3 className="font-semibold text-white">Title Generation Mode</h3>
                    </div>

                    <div className="flex gap-2 p-1 bg-black/20 rounded-lg">
                        <button
                            onClick={() => handleConfigChange('mode', 'auto')}
                            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md transition-all text-sm font-medium
                ${config.mode === 'auto' ? 'bg-brand-600 text-white shadow-lg' : 'text-white/50 hover:text-white'}`}
                        >
                            <Sparkles className="w-4 h-4" /> AI Auto
                        </button>
                        <button
                            onClick={() => handleConfigChange('mode', 'manual')}
                            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md transition-all text-sm font-medium
                ${config.mode === 'manual' ? 'bg-white/10 text-white shadow-lg' : 'text-white/50 hover:text-white'}`}
                        >
                            <Type className="w-4 h-4" /> File Name
                        </button>
                        <button
                            onClick={() => handleConfigChange('mode', 'none')}
                            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md transition-all text-sm font-medium
                ${config.mode === 'none' ? 'bg-red-500/20 text-red-400' : 'text-white/50 hover:text-white'}`}
                        >
                            None
                        </button>
                    </div>

                    {config.mode !== 'none' && (
                        <div className="space-y-4 pt-4 border-t border-white/10">
                            <div>
                                <label className="block text-xs text-white/40 uppercase tracking-wider mb-2">Append Custom Title (Optional)</label>
                                <input
                                    type="text"
                                    value={config.customTitle}
                                    onChange={(e) => handleConfigChange('customTitle', e.target.value)}
                                    placeholder="e.g., | Exclusive Edit"
                                    className="input w-full text-sm"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-white/40 uppercase tracking-wider mb-2">Master Description</label>
                                <textarea
                                    value={config.customDescription}
                                    onChange={(e) => handleConfigChange('customDescription', e.target.value)}
                                    placeholder="This description will be merged with the generated body..."
                                    className="input w-full h-24 text-sm py-2"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-white/40 uppercase tracking-wider mb-2">Global #Tags</label>
                                <input
                                    type="text"
                                    value={config.tags}
                                    onChange={(e) => handleConfigChange('tags', e.target.value)}
                                    placeholder="e.g., #viral, #trending"
                                    className="input w-full text-sm"
                                />
                            </div>
                        </div>
                    )}

                    <div className="pt-6 mt-4 border-t border-white/10">
                        <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={config.addWatermark || false}
                                onChange={(e) => handleConfigChange('addWatermark', e.target.checked)}
                                className="w-4 h-4 text-brand-500 bg-white/5 border-white/20 focus:ring-brand-500 rounded"
                            />
                            <div className="flex flex-col">
                                <span className="text-sm font-medium text-white group-hover:text-brand-300 transition-colors">Apply AutoStream Watermark</span>
                                <span className="text-xs text-white/40">Optional. Helps deter content theft when distributing across networks.</span>
                            </div>
                        </label>
                    </div>
                </div>

                {/* Right Pane: Media Editor */}
                <div className="lg:col-span-7 space-y-4">
                    <div className="flex justify-between items-end">
                        <div>
                            <h3 className="font-semibold text-white flex items-center gap-2">
                                <FileImage className="w-5 h-5 text-brand-400" /> Live Preview
                            </h3>
                            <p className="text-xs text-white/50 mt-1">Drag and resize elements directly on the canvas.</p>
                        </div>

                        <div className="flex gap-2">
                            <button onClick={addTextElement} className="btn-secondary py-1.5 px-3 text-xs flex gap-1 items-center">
                                <Plus className="w-3 h-3" /> Text
                            </button>
                            <button onClick={addLogoElement} className="btn-secondary py-1.5 px-3 text-xs flex gap-1 items-center">
                                <Plus className="w-3 h-3" /> Logo
                            </button>
                        </div>
                    </div>

                    {/* The Drag & Drop Visual Canvas */}
                    <AdvancedMediaEditor videoSrc={videoSrc} selectedVideoId={previewVideo?.id} />

                    <div className="flex gap-2 pt-2 text-xs text-white/40">
                        * Overlays applied here will be rendered onto all selected videos during the processing phase.
                    </div>
                </div>
            </div>

            {/* Nav */}
            <div className="flex justify-between pt-6 mt-6 border-t border-white/10">
                <button onClick={() => dispatch({ type: 'GO_TO_STEP', payload: 2 })} className="btn-secondary">Back to Videos</button>
                <div className="flex gap-3">
                    <button onClick={() => {
                        // Clear visual overlays to assure clean skip
                        state.editorElements.forEach(el => dispatch({ type: 'REMOVE_EDITOR_ELEMENT', payload: el.id }));
                        dispatch({ type: 'GO_TO_STEP', payload: 4 });
                    }} className="btn-secondary hidden sm:block">
                        Skip Editor
                    </button>
                    <button onClick={() => dispatch({ type: 'GO_TO_STEP', payload: 4 })} className="btn-primary">
                        Continue to Schedule
                    </button>
                </div>
            </div>
        </div>
    );
}
