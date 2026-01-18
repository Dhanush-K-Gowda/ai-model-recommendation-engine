import { Search, Filter, Plus, MoreHorizontal } from 'lucide-react';
import { Card, CardBody } from '../components/UI/Card';
import { useState, useEffect } from 'react';
import { apiClient, type Application } from '../lib/api';

export default function Applications() {
    const [apps, setApps] = useState<Application[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        loadApplications();
    }, []);

    const loadApplications = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.getApplications();
            if (response.status === 'success' && response.data) {
                setApps(response.data.applications || []);
            } else {
                setError(response.message || 'Failed to load applications');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load applications');
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num: number): string => {
        if (num >= 1000000) {
            return `${(num / 1000000).toFixed(1)}M`;
        } else if (num >= 1000) {
            return `${(num / 1000).toFixed(1)}k`;
        }
        return num.toString();
    };

    const filteredApps = apps.filter(app => 
        app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.application_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (app.categories && app.categories.some(cat => cat.toLowerCase().includes(searchQuery.toLowerCase())))
    );

    return (
        <div className="space-y-8 animate-fade-in text-text-main pb-10">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-display font-bold">Applications</h1>
                    <p className="text-text-muted mt-2">Manage your AI-powered services.</p>
                </div>
                <button className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-glow/80 transition-all font-medium cursor-pointer">
                    <Plus className="w-5 h-5" />
                    <span>New Application</span>
                </button>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4 bg-surface p-2 rounded-2xl border border-border w-fit">
                <div className="relative">
                    <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                    <input 
                        type="text" 
                        placeholder="Search apps..." 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="bg-transparent border-none pl-10 pr-4 py-2 text-sm focus:outline-none text-text-main w-64 placeholder:text-text-muted/50" 
                    />
                </div>
                <div className="w-px h-6 bg-border" />
                <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-muted hover:text-text-main transition-colors cursor-pointer">
                    <Filter className="w-4 h-4" />
                    <span>Filter</span>
                </button>
            </div>

            {loading && (
                <div className="text-center py-12 text-text-muted">
                    Loading applications...
                </div>
            )}

            {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
                    {error}
                </div>
            )}

            {!loading && filteredApps.length === 0 && (
                <div className="text-center py-12 text-text-muted">
                    {searchQuery ? 'No applications found matching your search.' : 'No applications found.'}
                </div>
            )}

            {/* Grid */}
            {!loading && filteredApps.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredApps.map(app => (
                        <Card key={app.application_id} hoverEffect className="group cursor-pointer">
                            <CardBody>
                                <div className="flex justify-between items-start mb-6">
                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border border-white/5 group-hover:scale-110 transition-transform duration-300">
                                        <span className="text-xl font-bold bg-gradient-to-br from-primary to-secondary bg-clip-text text-transparent">{app.id}</span>
                                    </div>
                                    <button className="text-text-muted hover:text-text-main p-1 hover:bg-white/5 rounded-lg transition-colors"><MoreHorizontal className="w-5 h-5" /></button>
                                </div>

                                <h3 className="text-xl font-bold mb-2 group-hover:text-primary transition-colors">{app.name}</h3>

                                <div className="space-y-3 mb-6">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-text-muted">Model</span>
                                        <span className="font-medium bg-white/5 px-2 py-0.5 rounded text-xs border border-white/5 text-text-main">{app.model}</span>
                                    </div>
                                    {(app.categories && app.categories.length > 0) && (
                                        <div className="flex justify-between text-sm">
                                            <span className="text-text-muted">Category</span>
                                            <div className="flex flex-wrap gap-1 justify-end">
                                                {app.categories.slice(0, 2).map((cat, idx) => (
                                                    <span key={idx} className="font-medium bg-primary/10 text-primary px-2 py-0.5 rounded text-xs border border-primary/20">
                                                        {cat}
                                                    </span>
                                                ))}
                                                {app.categories.length > 2 && (
                                                    <span className="font-medium bg-white/5 px-2 py-0.5 rounded text-xs border border-white/5 text-text-muted">
                                                        +{app.categories.length - 2}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                    <div className="flex justify-between text-sm">
                                        <span className="text-text-muted">Status</span>
                                        <span className={`font-medium text-xs flex items-center gap-1.5 ${app.is_active ? 'text-emerald-400' : 'text-text-muted'}`}>
                                            <span className={`w-1.5 h-1.5 rounded-full ${app.is_active ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 'bg-text-muted'}`}></span>
                                            {app.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-border flex items-center justify-between">
                                    <div>
                                        <p className="text-[10px] uppercase tracking-wider text-text-muted font-bold">Usage</p>
                                        <p className="font-medium text-sm text-text-main mt-0.5">{formatNumber(app.total_requests)}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[10px] uppercase tracking-wider text-text-muted font-bold">Cost</p>
                                        <p className="font-medium text-sm text-text-main mt-0.5">{app.cost}</p>
                                    </div>
                                </div>
                            </CardBody>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
