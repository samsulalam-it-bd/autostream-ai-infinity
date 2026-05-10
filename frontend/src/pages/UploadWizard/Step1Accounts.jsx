import React, { useState, useEffect } from 'react';
import { useWizard } from './WizardContext';
import { fetchAccounts, fetchGroups } from '../../lib/api';
import { Search, Filter, Users, User, CheckCircle2, Circle } from 'lucide-react';

export default function Step1Accounts() {
    const { state, dispatch } = useWizard();
    const [accounts, setAccounts] = useState([]);
    const [groups, setGroups] = useState([]);
    const [loading, setLoading] = useState(true);

    // Local filters
    const [searchTerm, setSearchTerm] = useState('');
    const [platformFilter, setPlatformFilter] = useState('all');
    const [selectionMode, setSelectionMode] = useState('multi'); // 'single', 'multi', 'group'

    useEffect(() => {
        async function load() {
            try {
                const [accRes, grpRes] = await Promise.all([fetchAccounts(), fetchGroups()]);
                const rawAcc = accRes?.data || [];
                const rawGrp = grpRes?.data || [];
                setAccounts(Array.isArray(rawAcc) ? rawAcc : []);
                setGroups(Array.isArray(rawGrp) ? rawGrp : []);
            } catch (err) {
                console.error("Failed to load accounts", err);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const filteredAccounts = accounts.filter(acc => {
        if (!acc) return false;
        const name = acc.channel_name || acc.name || 'Unknown Account';
        const matchSearch = name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchPlatform = platformFilter === 'all' || acc.platform === platformFilter;
        const isActive = acc.status ? acc.status === 'active' : true;
        return matchSearch && matchPlatform && isActive;
    });

    const handleToggleAccount = (acc) => {
        if (selectionMode === 'single') {
            dispatch({ type: 'SET_ACCOUNTS', payload: [acc] });
        } else {
            const isSelected = state.selectedAccounts.some(a => a.id === acc.id);
            if (isSelected) {
                dispatch({ type: 'SET_ACCOUNTS', payload: state.selectedAccounts.filter(a => a.id !== acc.id) });
            } else {
                dispatch({ type: 'SET_ACCOUNTS', payload: [...state.selectedAccounts, acc] });
            }
        }
    };

    const handleSelectGroup = (group) => {
        setSelectionMode('group');
        dispatch({ type: 'SET_ACCOUNTS', payload: group.accounts || [] });
        dispatch({ type: 'SET_GROUP_NAME', payload: group.name });
    };

    const selectAllFiltered = () => {
        const newSelected = [...state.selectedAccounts];
        filteredAccounts.forEach(acc => {
            if (!newSelected.some(a => a.id === acc.id)) {
                newSelected.push(acc);
            }
        });
        dispatch({ type: 'SET_ACCOUNTS', payload: newSelected });
    };

    const clearSelection = () => {
        dispatch({ type: 'SET_ACCOUNTS', payload: [] });
        dispatch({ type: 'SET_GROUP_NAME', payload: '' });
    };

    if (loading) return <div className="p-8 text-center text-white/50 animate-pulse">Loading connected accounts...</div>;

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col gap-2">
                <h2 className="text-2xl font-bold text-white">Step 1 — Target Accounts</h2>
                <p className="text-white/50 text-sm">Select where you want your videos to be published.</p>
            </div>

            {/* Control Bar */}
            <div className="flex flex-col md:flex-row gap-4 justify-between bg-white/5 p-4 rounded-xl border border-white/10">
                <div className="flex bg-white/5 rounded-lg p-1 w-fit">
                    <button onClick={() => setSelectionMode('single')} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${selectionMode === 'single' ? 'bg-brand-600 text-white shadow-lg' : 'text-white/60 hover:text-white'}`}>Single</button>
                    <button onClick={() => setSelectionMode('multi')} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${selectionMode === 'multi' ? 'bg-brand-600 text-white shadow-lg' : 'text-white/60 hover:text-white'}`}>Multiple</button>
                    <button onClick={() => setSelectionMode('group')} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${selectionMode === 'group' ? 'bg-brand-600 text-white shadow-lg' : 'text-white/60 hover:text-white'}`}>Groups</button>
                </div>

                <div className="flex gap-2 flex-1 md:max-w-md">
                    <div className="relative flex-1">
                        <Search className="w-4 h-4 text-white/40 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                            type="text"
                            placeholder="Search accounts..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="input pl-9 w-full h-9 text-sm"
                        />
                    </div>
                    <select
                        value={platformFilter}
                        onChange={(e) => setPlatformFilter(e.target.value)}
                        className="input h-9 text-sm px-3 bg-slate-800"
                    >
                        <option value="all">All Platforms</option>
                        <option value="youtube">YouTube</option>
                        <option value="facebook">Facebook</option>
                        <option value="instagram">Instagram</option>
                    </select>
                </div>
            </div>

            {/* Selection Area */}
            {selectionMode !== 'group' ? (
                <div className="space-y-3">
                    {selectionMode === 'multi' && (
                        <div className="flex justify-between items-center px-2">
                            <span className="text-sm text-brand-300 font-medium">{state.selectedAccounts.length} selected</span>
                            <div className="flex gap-2">
                                <button onClick={selectAllFiltered} className="text-xs text-white/60 hover:text-white transition-colors">Select Visible</button>
                                <span className="text-white/20">|</span>
                                <button onClick={clearSelection} className="text-xs text-red-400 hover:text-red-300 transition-colors">Clear All</button>
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {filteredAccounts.map(acc => {
                            const isSelected = state.selectedAccounts.some(a => a.id === acc.id);
                            return (
                                <div
                                    key={acc.id}
                                    onClick={() => handleToggleAccount(acc)}
                                    className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200
                    ${isSelected ? 'bg-brand-600/20 border-brand-500/50 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10'}`}
                                >
                                    <div className={`shrink-0 ${isSelected ? 'text-brand-400' : 'text-white/30'}`}>
                                        {isSelected ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5" />}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="text-sm font-medium text-white truncate">{acc.channel_name || acc.name || 'Unknown Account'}</p>
                                        <p className="text-xs text-white/50 capitalize flex items-center gap-1">
                                            {acc.platform === 'youtube' ? '🎬' : acc.platform === 'facebook' ? '📘' : '📸'} {acc.platform || 'General'}
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                        {filteredAccounts.length === 0 && (
                            <div className="col-span-full p-8 text-center text-white/40 border border-dashed border-white/10 rounded-xl">
                                No active accounts found matching your filters.
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {groups.map(grp => {
                        const isSelected = state.groupName === grp.name;
                        return (
                            <div
                                key={grp.id}
                                onClick={() => handleSelectGroup(grp)}
                                className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all
                  ${isSelected ? 'bg-brand-600/20 border-brand-500/50 shadow-lg' : 'bg-white/5 border-white/10 hover:bg-white/10'}`}
                            >
                                <div className={`p-3 rounded-lg ${isSelected ? 'bg-brand-500/20 text-brand-400' : 'bg-white/10 text-white/50'}`}>
                                    <Users className="w-6 h-6" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="font-semibold text-white text-lg truncate">{grp.name}</p>
                                    <p className="text-sm text-white/50">{grp.accounts?.length || 0} accounts bundled</p>
                                </div>
                                {isSelected && <CheckCircle2 className="w-6 h-6 text-brand-400 shrink-0" />}
                            </div>
                        );
                    })}
                    {groups.length === 0 && (
                        <div className="col-span-full p-8 text-center text-white/40 border border-dashed border-white/10 rounded-xl">
                            No groups created yet. Head over to the Accounts tab to bundle accounts.
                        </div>
                    )}
                </div>
            )}

            {/* Next Step Nav */}
            <div className="flex justify-end pt-6 border-t border-white/10">
                <button
                    onClick={() => dispatch({ type: 'GO_TO_STEP', payload: 2 })}
                    disabled={state.selectedAccounts.length === 0}
                    className="btn-primary"
                >
                    Continue to Link Drive
                </button>
            </div>
        </div>
    );
}
