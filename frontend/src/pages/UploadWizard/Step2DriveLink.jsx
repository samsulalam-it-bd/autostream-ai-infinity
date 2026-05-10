import React, { useState, useCallback } from 'react';
import { useWizard } from './WizardContext';
import debounce from 'lodash.debounce';
import { syncDriveFolder, fetchVideos } from '../../lib/api';
import { Link2, Loader2, Play, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';

export default function Step2DriveLink() {
    const { state, dispatch } = useWizard();
    const [localLink, setLocalLink] = useState(state.driveLink || '');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [videos, setVideos] = useState(state.fetchedMedia || []);

    const loadVideosManually = async () => {
        try {
            setError(null);
            const res = await fetchVideos(undefined, true);
            const list = Array.isArray(res?.data) ? res.data : [];
            if (list.length > 0) {
                const firstPage = list.slice(0, 20);
                setVideos(firstPage);
                dispatch({ type: 'UPDATE_DRIVE_DATA', payload: { link: localLink, media: firstPage } });
                dispatch({ type: 'SET_SELECTED_MEDIA', payload: firstPage });
            } else {
                setError('No videos found yet. Sync may still be running — wait 30s and try again.');
            }
        } catch (err) {
            setError('Failed to load videos: ' + err.message);
        }
    };

    const pollForVideos = () => {
        let attempts = 0;
        const interval = setInterval(async () => {
            attempts++;
            try {
                const res = await fetchVideos(undefined, true);
                const list = Array.isArray(res?.data) ? res.data : [];
                if (list.length > 0) {
                    const firstPage = list.slice(0, 20);
                    setVideos(firstPage);
                    dispatch({ type: 'UPDATE_DRIVE_DATA', payload: { link: localLink, media: firstPage } });
                    dispatch({ type: 'SET_SELECTED_MEDIA', payload: firstPage });
                    clearInterval(interval);
                    setLoading(false);
                }
            } catch (err) {
                console.error('Poll error:', err);
            }
            if (attempts >= 36) {
                clearInterval(interval);
                setLoading(false);
                if (videos.length === 0) setError('Sync is taking longer than expected. Click "Reload Videos" below to check again.');
            }
        }, 2500);
    };

    const executeSync = async (link) => {
        if (!link || !link.includes('drive.google.com')) {
            setError('Please enter a valid Google Drive folder URL.');
            return;
        }
        setError(null);
        setLoading(true);
        setVideos([]);
        try {
            const anchorAccount = state.selectedAccounts[0];
            if (!anchorAccount) throw new Error('No account selected in Step 1. Go back and select an account.');
            await syncDriveFolder(anchorAccount.id, link);
            setTimeout(() => pollForVideos(), 3000);
        } catch (err) {
            const msg = err?.response?.data?.detail || err.message || 'Sync failed. Try again.';
            setError(msg);
            setLoading(false);
        }
    };

    const debouncedSync = useCallback(
        debounce((link) => { if (link.length > 10) executeSync(link); }, 1500),
        [state.selectedAccounts]
    );

    const handleLinkChange = (e) => {
        const val = e.target.value;
        setLocalLink(val);
        debouncedSync(val);
    };

    const toggleVideoSelection = (vid) => {
        const isSelected = state.selectedMedia.some(v => v.id === vid.id);
        if (isSelected) {
            dispatch({ type: 'SET_SELECTED_MEDIA', payload: state.selectedMedia.filter(v => v.id !== vid.id) });
        } else {
            dispatch({ type: 'SET_SELECTED_MEDIA', payload: [...state.selectedMedia, vid] });
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col gap-2">
                <h2 className="text-2xl font-bold text-white">Step 2 — Connect Google Drive</h2>
                <p className="text-white/50 text-sm">Paste a public Google Drive folder link. We'll automatically fetch the videos.</p>
            </div>

            <div className="bg-white/5 p-6 rounded-xl border border-white/10 space-y-4">
                {state.selectedAccounts.length > 0 && (
                    <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/10 overflow-x-auto">
                        <span className="text-xs text-white/40 uppercase tracking-wider shrink-0">Publishing to:</span>
                        {state.selectedAccounts.map(acc => (
                            <span key={acc.id} className="badge-blue text-xs whitespace-nowrap">{acc.channel_name || acc.name}</span>
                        ))}
                    </div>
                )}

                <div className="relative flex items-center gap-2">
                    <Link2 className="w-5 h-5 text-white/40 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                        type="text"
                        placeholder="https://drive.google.com/drive/folders/..."
                        value={localLink}
                        onChange={handleLinkChange}
                        className="input w-full pl-12 pr-28 h-14 text-base bg-black/20 border-white/10 focus:border-brand-500 transition-colors"
                    />
                    {loading ? (
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2 text-brand-400 pointer-events-none">
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span className="text-sm font-medium">Fetching…</span>
                        </div>
                    ) : (
                        <button
                            onClick={() => executeSync(localLink)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 btn-primary h-9 px-4 text-sm flex items-center gap-1.5"
                        >
                            <RefreshCw className="w-3.5 h-3.5" /> Sync
                        </button>
                    )}
                </div>

                {error && (
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20 text-sm">
                            <AlertCircle className="w-4 h-4 shrink-0" />
                            {error}
                        </div>
                        <button
                            onClick={loadVideosManually}
                            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-brand-600/20 hover:bg-brand-600/30 text-brand-300 border border-brand-600/20 text-sm font-medium transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" /> Reload Videos
                        </button>
                    </div>
                )}
            </div>

            {videos.length > 0 && (
                <div className="space-y-3">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-white font-semibold">Available Media Form Folder</h3>
                        <div className="flex gap-2 text-xs">
                            <span className="text-white/50 bg-black/50 px-3 py-1.5 rounded-full">
                                {state.selectedMedia.length} / {videos.length} selected
                            </span>
                            <button
                                onClick={() => {
                                    if (state.selectedMedia.length === videos.length) {
                                        dispatch({ type: 'SET_SELECTED_MEDIA', payload: [] });
                                    } else {
                                        dispatch({ type: 'SET_SELECTED_MEDIA', payload: videos });
                                    }
                                }}
                                className="bg-brand-500/20 text-brand-300 hover:bg-brand-500/30 px-3 py-1.5 rounded-full transition-colors flex items-center gap-1"
                            >
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                {state.selectedMedia.length === videos.length ? "Deselect All" : "Select All"}
                            </button>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                        {videos.map(vid => {
                            const isSelected = state.selectedMedia.some(v => v.id === vid.id);
                            return (
                                <div
                                    key={vid.id}
                                    onClick={() => toggleVideoSelection(vid)}
                                    className={`group relative aspect-video bg-black/40 rounded-xl border overflow-hidden cursor-pointer transition-all duration-200
                    ${isSelected ? 'border-brand-500 ring-2 ring-brand-500/50 shadow-[0_0_20px_rgba(99,102,241,0.2)]' : 'border-white/10 hover:border-white/30'}`}
                                >
                                    <div className="absolute inset-0 flex items-center justify-center text-white/20">
                                        <Play className="w-10 h-10" />
                                    </div>
                                    <div className="absolute inset-0 flex flex-col justify-end p-3 bg-gradient-to-t from-black/80 via-black/20 to-transparent">
                                        <p className="text-white text-xs font-medium truncate">{vid.original_filename || vid.drive_file_id}</p>
                                        <p className="text-white/50 text-[10px]">
                                            {vid.file_size_bytes ? ((vid.file_size_bytes) / (1024 * 1024)).toFixed(1) + ' MB' : ''}
                                        </p>
                                    </div>

                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-sm gap-3">
                                        <button
                                            className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                                            title="Preview in Drive"
                                            onClick={(e) => { e.stopPropagation(); window.open(vid.drive_view_link || `https://drive.google.com/file/d/${vid.drive_file_id}/view`, '_blank'); }}
                                        >
                                            <Play className="w-4 h-4 ml-0.5" />
                                        </button>
                                    </div>

                                    <div className={`absolute top-2 left-2 transition-transform duration-200 ${isSelected ? 'scale-100' : 'scale-0'}`}>
                                        <div className="bg-brand-500 text-white rounded-full"><CheckCircle2 className="w-5 h-5" /></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            <div className="flex justify-between pt-6 border-t border-white/10">
                <button onClick={() => dispatch({ type: 'GO_TO_STEP', payload: 1 })} className="btn-secondary">Back to Accounts</button>
                <button
                    onClick={() => dispatch({ type: 'GO_TO_STEP', payload: 3 })}
                    disabled={state.selectedMedia.length === 0}
                    className="btn-primary"
                >
                    Continue to Metadata &amp; Editor
                </button>
            </div>
        </div>
    );
}
