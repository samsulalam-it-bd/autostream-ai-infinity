// ── Wizard Navigation ──────────────────────────────────────────────────
const nextStep = () => setCurrentStep(p => Math.min(4, p + 1))
const prevStep = () => setCurrentStep(p => Math.max(1, p - 1))

const STEPS = [
    { num: 1, title: 'Link Folders', icon: FolderOpen },
    { num: 2, title: 'Select Targets', icon: LayoutGrid },
    { num: 3, title: 'Choose Videos', icon: Film },
    { num: 4, title: 'Schedule', icon: Calendar },
]

return (
    <div className="space-y-6 max-w-5xl mx-auto pb-20">
        <Toast toasts={toasts} />
        <AiPreviewModal video={previewVideo} onClose={() => setPreviewVideo(null)} />
        <ScheduleSummaryModal
            summary={showSummary}
            onConfirm={handleConfirmSchedule}
            onCancel={() => setShowSummary(null)}
            scheduling={scheduling}
        />

        <div>
            <h1 className="text-2xl font-bold text-white">Upload Zone</h1>
            <p className="text-white/40 text-sm mt-1">Configure your uploads step by step.</p>
        </div>

        {/* Stepper Header */}
        <div className="flex items-center justify-between relative mb-8">
            <div className="absolute top-1/2 left-0 w-full h-[2px] bg-white/5 -translate-y-1/2 z-0" />
            <div className="absolute top-1/2 left-0 h-[2px] bg-brand-500 -translate-y-1/2 z-0 transition-all duration-300"
                style={{ width: `${((currentStep - 1) / 3) * 100}%` }} />

            {STEPS.map((step) => {
                const isActive = currentStep === step.num
                const isPassed = currentStep > step.num
                return (
                    <div key={step.num} className="relative z-10 flex flex-col items-center gap-2">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors duration-300
                                ${isActive ? 'bg-brand-600 border-brand-500 text-white shadow-[0_0_15px_rgba(139,92,246,0.5)]'
                                : isPassed ? 'bg-brand-500 border-brand-500 text-white'
                                    : 'bg-gray-900 border-white/10 text-white/40'}`}>
                            {isPassed ? <Check className="w-5 h-5" /> : <step.icon className="w-4 h-4" />}
                        </div>
                        <span className={`text-xs font-medium ${isActive ? 'text-brand-300' : isPassed ? 'text-white/80' : 'text-white/40'}`}>
                            {step.title}
                        </span>
                    </div>
                )
            })}
        </div>

        {/* Main Card Container */}
        <div className="card p-6 min-h-[400px] flex flex-col">

            {/* STEP 1: FOLDERS */}
            {currentStep === 1 && (
                <div className="flex-1 animate-in fade-in slide-in-from-right-4 duration-300">
                    <h2 className="text-xl font-semibold text-white mb-2">Step 1 — Link Drive Folders</h2>
                    <p className="text-white/50 text-sm mb-6">Assign a Google Drive folder to each account. Click Sync to import videos from that folder.</p>
                    <AccountFolderManager accounts={accounts} onSync={handleSync} syncing={syncing} syncTarget={syncTarget} />
                </div>
            )}

            {/* STEP 2: TARGETS */}
            {currentStep === 2 && (
                <div className="flex-1 animate-in fade-in slide-in-from-right-4 duration-300">
                    <h2 className="text-xl font-semibold text-white mb-2">Step 2 — Select Destination</h2>
                    <p className="text-white/50 text-sm mb-6">Where do you want to upload these videos?</p>

                    <div className="flex bg-white/5 p-1 rounded-xl mb-6 w-max mx-auto border border-white/10">
                        {MODE_TABS.map(tab => (
                            <button key={tab.id} onClick={() => setSchedMode(tab.id)}
                                className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${schedMode === tab.id ? 'bg-brand-600 text-white shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}>
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    <div className="max-w-2xl mx-auto mt-8">
                        {schedMode === 'single' && (
                            <div className="space-y-3">
                                <label className="text-sm font-medium text-white/70 block">Select Account</label>
                                <select className="input w-full p-3" value={selectedAccount} onChange={e => setSelectedAccount(e.target.value)}>
                                    <option value="">-- Choose Account --</option>
                                    {accounts.filter(a => a.status === 'active').map(a => (
                                        <option key={a.id} value={a.id}>{a.channel_name} ({a.platform})</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {schedMode === 'multiple' && (
                            <div className="space-y-3">
                                <label className="text-sm font-medium text-white/70 block flex justify-between">
                                    Select Multiple Accounts ({selectedAccounts.length} selected)
                                    <button onClick={() => setSelectedAccounts(accounts.filter(a => a.status === 'active').map(a => a.id))} className="text-brand-400 text-xs hover:underline">Select All</button>
                                </label>
                                <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                                    {accounts.filter(a => a.status === 'active').map(a => (
                                        <label key={a.id} className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${selectedAccounts.includes(a.id) ? 'bg-brand-600/20 border-brand-500/50' : 'bg-white/5 border-white/5 hover:bg-white/10'}`}>
                                            <div className={`w-5 h-5 rounded border flex items-center justify-center shrink-0 ${selectedAccounts.includes(a.id) ? 'bg-brand-600 border-brand-600' : 'border-white/20'}`}>
                                                {selectedAccounts.includes(a.id) && <Check className="w-3.5 h-3.5 text-white" />}
                                            </div>
                                            <span className="text-sm text-white truncate">{a.channel_name} <span className="text-white/30 text-xs">({a.platform})</span></span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        )}

                        {schedMode === 'group' && (
                            <div className="space-y-3">
                                <label className="text-sm font-medium text-white/70 block">Select Channel Group</label>
                                <select className="input w-full p-3" value={targetGroupId} onChange={e => setTargetGroupId(e.target.value)}>
                                    <option value="">-- Choose Group --</option>
                                    {groups.map(g => (
                                        <option key={g.id} value={g.id}>{g.name} ({g.platform})</option>
                                    ))}
                                </select>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* STEP 3: VIDEOS */}
            {currentStep === 3 && (
                <div className="flex-1 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-xl font-semibold text-white mb-1">Step 3 — Select Videos</h2>
                            <p className="text-white/50 text-sm">Choose the videos to upload.</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="text-sm text-brand-300 bg-brand-400/10 px-3 py-1.5 rounded-lg border border-brand-400/20">{selectedVideos.length} Selected</span>
                            <button onClick={() => setSelectedVideos(videos.map(v => v.id))} className="text-sm text-white/50 hover:text-white transition-colors">Select All</button>
                            <button onClick={() => setSelectedVideos([])} className="text-sm text-white/50 hover:text-white transition-colors">Clear</button>
                        </div>
                    </div>

                    {videos.length === 0 ? (
                        <div className="text-center py-12 bg-white/5 rounded-xl border border-white/5">
                            <Film className="w-12 h-12 text-white/20 mx-auto mb-3" />
                            <p className="text-white/60">No videos found. Go back to Step 1 and click Sync.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar content-start">
                            {videos.map(v => {
                                const isSelected = selectedVideos.includes(v.id)
                                return (
                                    <div key={v.id} className={`group relative rounded-xl border overflow-hidden transition-all duration-200 cursor-pointer ${isSelected ? 'border-brand-500 ring-2 ring-brand-500/50 bg-brand-900/20' : 'border-white/10 bg-white/5 hover:border-white/30'}`} onClick={() => toggleVideo(v.id)}>
                                        <div className="absolute top-2 left-2 z-10 w-6 h-6 rounded border bg-black/50 backdrop-blur-md flex items-center justify-center transition-colors">
                                            <div className={`w-4 h-4 rounded-sm flex items-center justify-center transition-colors ${isSelected ? 'bg-brand-500' : 'bg-transparent border border-white/50 group-hover:border-white'}`}>
                                                {isSelected && <Check className="w-3 h-3 text-white" />}
                                            </div>
                                        </div>
                                        <div className="absolute top-2 right-2 flex gap-1 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={(e) => { e.stopPropagation(); setPreviewVideo(v) }} className="p-1.5 bg-black/60 hover:bg-brand-600 text-white rounded backdrop-blur-md transition-colors" title="View AI Data">
                                                <BookOpen className="w-3.5 h-3.5" />
                                            </button>
                                            <a href={v.drive_view_link} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="p-1.5 bg-black/60 hover:bg-blue-600 text-white rounded backdrop-blur-md transition-colors" title="Open in Drive">
                                                <Link2 className="w-3.5 h-3.5" />
                                            </a>
                                            <button onClick={(e) => { e.stopPropagation(); handleDeleteVideo(v.id) }} className="p-1.5 bg-black/60 hover:bg-red-600 text-white rounded backdrop-blur-md transition-colors" title="Delete">
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                        <div className="aspect-video bg-black/40 flex items-center justify-center relative">
                                            <Film className="w-8 h-8 text-white/20" />
                                            {v.status === 'processing' && (
                                                <div className="absolute inset-0 bg-brand-900/60 flex items-center justify-center">
                                                    <RefreshCw className="w-6 h-6 text-brand-400 animate-spin" />
                                                </div>
                                            )}
                                            {v.status === 'ready' && <div className="absolute top-1 right-2 text-xs font-bold text-green-400 tracking-wider">READY</div>}
                                        </div>
                                        <div className="p-3">
                                            <p className="text-xs text-white/80 font-medium truncate" title={v.original_filename}>{v.original_filename || v.drive_file_id}</p>
                                            <div className="flex justify-between items-center mt-2">
                                                <p className="text-[10px] text-white/40">{(v.file_size_bytes / 1024 / 1024).toFixed(1)} MB</p>
                                                {v.ai_title && <span className="text-[10px] bg-brand-500/20 text-brand-300 px-1.5 py-0.5 rounded border border-brand-500/30 font-medium">AI Ready</span>}
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* STEP 4: SCHEDULE */}
            {currentStep === 4 && (
                <div className="flex-1 animate-in fade-in slide-in-from-right-4 duration-300">
                    <h2 className="text-xl font-semibold text-white mb-2">Step 4 — Options & Schedule</h2>
                    <p className="text-white/50 text-sm mb-6">Finalize how and when the videos are published.</p>

                    <div className="max-w-3xl mx-auto space-y-6 bg-white/5 p-6 rounded-2xl border border-white/5">

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="md:col-span-1">
                                <label className="text-xs font-medium text-white/60 uppercase tracking-wider mb-2 block">Start Date & Time</label>
                                <input type="datetime-local" className="input w-full h-[42px]" value={startDateTime} onChange={e => setStartDateTime(e.target.value)} />
                            </div>
                            <div className="md:col-span-1">
                                <label className="text-xs font-medium text-white/60 uppercase tracking-wider mb-2 block flex items-center gap-1">
                                    Span (Days)
                                    <span className="text-[10px] text-white/30 truncate" title="Drip feed these videos over X days">Hover</span>
                                </label>
                                <input type="number" className="input w-full h-[42px]" min="1" max="365" value={dripDays} onChange={e => setDripDays(e.target.value)} />
                            </div>
                            <div className="md:col-span-1">
                                <label className="text-xs font-medium text-white/60 uppercase tracking-wider mb-2 block">Daily Max (Optional)</label>
                                <input type="number" className="input w-full h-[42px]" min="1" max="50" placeholder="No limit" value={dailyLimitPerAccount} onChange={e => setDailyLimitPerAccount(e.target.value)} />
                            </div>
                        </div>

                        <div className="pt-4 border-t border-white/10">
                            <label className="text-xs font-medium text-white/60 uppercase tracking-wider mb-3 block flex items-center gap-2">
                                <Clock className="w-3.5 h-3.5" />
                                Specific Daily Time Slots <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded normal-case tracking-normal">Optional</span>
                            </label>
                            <div className="flex flex-wrap gap-2 items-center">
                                {dailyTimeSlots.map(t => (
                                    <div key={t} className="badge-blue flex items-center gap-1.5 py-1 px-2.5 shadow-sm">
                                        {t}
                                        <button onClick={() => setDailyTimeSlots(dailyTimeSlots.filter(x => x !== t))} className="opacity-60 hover:opacity-100 hover:text-white transition-opacity"><X className="w-3.5 h-3.5" /></button>
                                    </div>
                                ))}
                                <div className="flex gap-2">
                                    <input type="time" className="input !py-1 text-sm w-28 h-[32px]" value={newTimeSlot} onChange={e => setNewTimeSlot(e.target.value)} />
                                    <button onClick={() => {
                                        if (newTimeSlot && !dailyTimeSlots.includes(newTimeSlot)) {
                                            setDailyTimeSlots([...dailyTimeSlots, newTimeSlot].sort())
                                            setNewTimeSlot('')
                                        }
                                    }} className="btn-secondary !py-1 px-3 text-xs h-[32px]">Add Time</button>
                                </div>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-white/10 flex items-center gap-8">
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <div className={`w-5 h-5 rounded border transition-all flex items-center justify-center ${addWatermark ? 'bg-brand-600 border-brand-500 shadow-[0_0_10px_rgba(139,92,246,0.5)]' : 'border-white/20 group-hover:border-white/40 bg-black/20'}`} onClick={() => setAddWatermark(!addWatermark)}>
                                    {addWatermark && <Check className="w-3.5 h-3.5 text-white" />}
                                </div>
                                <span className="text-sm font-medium text-white/80 group-hover:text-white transition-colors">Add Watermark</span>
                            </label>
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <div className={`w-5 h-5 rounded border transition-all flex items-center justify-center ${autoComment ? 'bg-brand-600 border-brand-500 shadow-[0_0_10px_rgba(139,92,246,0.5)]' : 'border-white/20 group-hover:border-white/40 bg-black/20'}`} onClick={() => setAutoComment(!autoComment)}>
                                    {autoComment && <Check className="w-3.5 h-3.5 text-white" />}
                                </div>
                                <span className="text-sm font-medium text-white/80 group-hover:text-white transition-colors">Auto-Comment</span>
                            </label>
                        </div>

                    </div>
                </div>
            )}

            {/* Step Controls (Bottom of Wizard) */}
            <div className="mt-8 pt-6 border-t border-white/10 flex justify-between items-center mt-auto">
                <button
                    onClick={prevStep}
                    className={`btn-secondary min-w-[120px] ${currentStep === 1 ? 'opacity-0 pointer-events-none' : ''}`}>
                    Back
                </button>

                {currentStep < 4 ? (
                    <button onClick={nextStep} className="btn-primary min-w-[120px]">
                        Next Step <ChevronRight className="w-4 h-4" />
                    </button>
                ) : (
                    <button onClick={buildSummary} className="btn-primary min-w-[200px] shadow-lg shadow-brand-500/20">
                        <Droplets className="w-4 h-4 mr-2" />
                        Preview & Schedule
                    </button>
                )}
            </div>
        </div>

        {/* Pending Schedules (Below Wizard) */}
        {schedules.length > 0 && (
            <div className="card overflow-hidden mt-12 animate-in fade-in slide-in-from-bottom-8">
                <div className="flex items-center gap-3 p-5 border-b border-white/5 bg-white/[0.02]">
                    <div className="p-2 bg-brand-500/20 rounded-lg border border-brand-500/30">
                        <Calendar className="w-5 h-5 text-brand-400" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-white text-lg leading-tight">Pending Schedules</h2>
                        <p className="text-xs text-white/40">{schedules.length} active jobs in queue</p>
                    </div>

                    <div className="ml-auto flex items-center gap-3">
                        {selectedSchedules.length > 0 ? (
                            <>
                                <span className="text-sm text-brand-300 font-medium bg-brand-500/10 px-3 py-1.5 rounded-lg border border-brand-500/20">{selectedSchedules.length} selected</span>
                                <button onClick={() => setSelectedSchedules([])} className="btn-secondary py-1.5 px-3 text-sm">Deselect</button>
                                <button onClick={handleBulkDelete} disabled={bulkDeleting} className="btn-danger py-1.5 px-4 text-sm shadow-lg shadow-red-500/20">
                                    {bulkDeleting ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Trash2 className="w-4 h-4 mr-1.5" />}
                                    Cancel Selected
                                </button>
                            </>
                        ) : (
                            <button onClick={() => setSelectedSchedules(schedules.map(s => s.id))} className="btn-secondary py-1.5 px-4 text-sm">Select All</button>
                        )}
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-xs text-white/40 uppercase tracking-wider bg-black/20 border-b border-white/5">
                                <th className="px-5 py-4 text-left w-12 text-center">Sel</th>
                                <th className="px-5 py-4 text-left font-medium">Video ID</th>
                                <th className="px-5 py-4 text-left font-medium">Scheduled Time</th>
                                <th className="px-5 py-4 text-left font-medium">Target Account</th>
                                <th className="px-5 py-4 text-center font-medium">Watermark</th>
                                <th className="px-5 py-4 text-right font-medium">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {schedules.slice(0, 30).map(s => {
                                const isFailed = s.celery_task_id && !s.is_published && s.retry_count > 0
                                const isSelected = selectedSchedules.includes(s.id)
                                const acc = accounts.find(a => a.id === s.account_id)
                                return (
                                    <tr key={s.id} className={`border-b border-white/5 hover:bg-white/[0.04] transition-colors ${isSelected ? 'bg-brand-500/10' : ''}`}>
                                        <td className="px-5 py-3.5 text-center">
                                            <div onClick={() => toggleSchedule(s.id)} className={`w-4 h-4 rounded border flex items-center justify-center cursor-pointer mx-auto transition-colors ${isSelected ? 'bg-brand-500 border-brand-500' : 'border-white/30 hover:border-white/60 bg-black/20'}`}>
                                                {isSelected && <Check className="w-3 h-3 text-white" />}
                                            </div>
                                        </td>
                                        <td className="px-5 py-3.5">
                                            <div className="font-mono text-white/80 bg-white/5 px-2 py-1 rounded inline-block text-xs">{s.video_id.slice(0, 8)}...</div>
                                            {s.error_message && (
                                                <div className="text-[11px] text-red-400 mt-1.5 flex gap-1.5 items-start bg-red-500/10 p-2 rounded-lg border border-red-500/20 max-w-xs leading-tight">
                                                    <AlertCircle className="w-3 h-3 shrink-0 mt-0.5" />
                                                    <span className="line-clamp-2" title={s.error_message}>{s.error_message}</span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-5 py-3.5">
                                            <div className="text-white font-medium">{new Date(s.scheduled_time).toLocaleDateString()}</div>
                                            <div className="text-white/50 text-xs mt-0.5">{new Date(s.scheduled_time).toLocaleTimeString()}</div>
                                            {isFailed && <span className="text-[10px] text-red-400 font-bold tracking-wider inline-block mt-1 uppercase">Failed ({s.retry_count})</span>}
                                        </td>
                                        <td className="px-5 py-3.5 text-white/70">
                                            {s.target_group_id
                                                ? <span className="badge-blue"><LayoutGrid className="w-3 h-3 mr-1" />Group</span>
                                                : acc
                                                    ? <div className="flex items-center gap-2"><div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[10px]">{acc.platform[0].toUpperCase()}</div><span className="font-medium truncate max-w-[140px]">{acc.channel_name}</span></div>
                                                    : <span className="text-white/20">—</span>
                                            }
                                        </td>
                                        <td className="px-5 py-3.5 text-center">
                                            {s.add_watermark ? <span className="w-2 h-2 rounded-full bg-green-500 inline-block shadow-[0_0_8px_rgba(34,197,94,0.6)]" title="Watermark Enabled" /> : <span className="w-2 h-2 rounded-full bg-white/20 inline-block" title="No Watermark" />}
                                        </td>
                                        <td className="px-5 py-3.5">
                                            <div className="flex items-center justify-end gap-2">
                                                <button onClick={() => handleTrigger(s.id)} className={`py-1.5 px-3 flex items-center gap-1.5 text-xs rounded-lg font-medium transition-colors ${isFailed ? 'bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30' : 'bg-white/10 hover:bg-white/20 text-white'}`} title={isFailed ? 'Retry Now' : 'Run Now'}>
                                                    <Play className="w-3 h-3" /> {isFailed ? 'Retry' : 'Run'}
                                                </button>
                                                <button onClick={() => handleDeleteSchedule(s.id)} className="p-1.5 text-white/40 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors" title="Cancel Schedule">
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
                {schedules.length > 30 && (
                    <div className="bg-black/20 p-3 text-center border-t border-white/5">
                        <p className="text-xs text-white/40">Showing 30 of {schedules.length}. Older schedules hidden to improve performance.</p>
                    </div>
                )}
            </div>
        )}
    </div>
)
}
