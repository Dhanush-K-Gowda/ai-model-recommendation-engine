import { Activity, CreditCard, Layers } from 'lucide-react';
import { StatCard } from '../components/UI/StatCard';
import { Card, CardHeader, CardBody } from '../components/UI/Card';
import { Search, Filter, Plus, MoreHorizontal, ChevronDown, ChevronUp } from 'lucide-react';
import { useState, useEffect } from 'react';
import { cn } from '../lib/utils';
import { apiClient, type Application, type DashboardStats } from '../lib/api';

export default function Dashboard() {
    const [expandedApps, setExpandedApps] = useState<Set<string>>(new Set());
    const [apps, setApps] = useState<Application[]>([]);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [appsResponse, statsResponse] = await Promise.all([
                apiClient.getApplications(),
                apiClient.getDashboardStats()
            ]);

            if (appsResponse.status === 'success' && appsResponse.data) {
                setApps(appsResponse.data.applications || []);
            }

            if (statsResponse.status === 'success' && statsResponse.data) {
                setStats(statsResponse.data);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    const toggleApp = (appId: string) => {
        const newExpanded = new Set(expandedApps);
        if (newExpanded.has(appId)) {
            newExpanded.delete(appId);
        } else {
            newExpanded.add(appId);
        }
        setExpandedApps(newExpanded);
    };

    const formatNumber = (num: number): string => {
        if (num >= 1000000) {
            return `${(num / 1000000).toFixed(1)}M`;
        } else if (num >= 1000) {
            return `${(num / 1000).toFixed(1)}k`;
        }
        return num.toString();
    };

    const formatCost = (cost: number): string => {
        return `$${cost.toFixed(2)}`;
    };

    return (
        <div className="space-y-8 animate-fade-in text-text-main pb-10">
            {/* Overview Section */}
            <div>
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-4xl font-display font-bold text-text-main tracking-tight">Overview</h1>
                        <p className="text-text-muted mt-2">Welcome back to your model command center.</p>
                    </div>
                    <div className="flex gap-2">
                        <button className="px-4 py-2 bg-primary/10 text-primary border border-primary/20 rounded-lg hover:bg-primary/15 transition-colors text-sm font-medium">Download Report</button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    <StatCard
                        label="Total Cost"
                        value={stats ? formatCost(stats.total_cost) : '$0.00'}
                        trend=""
                        trendUp={true}
                        icon={CreditCard}
                        color="primary"
                    />
                    <StatCard
                        label="Token Usage"
                        value={stats ? formatNumber(stats.total_tokens) : '0'}
                        trend=""
                        trendUp={true}
                        icon={Activity}
                        color="secondary"
                    />
                    <StatCard
                        label="Active Apps"
                        value={stats ? stats.total_applications.toString() : '0'}
                        trend=""
                        trendUp={false}
                        icon={Layers}
                        color="accent"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                    <div>
                        <Card className="h-full">
                            <CardHeader>
                                <h2 className="text-xl font-bold font-display">Top Models by Cost</h2>
                            </CardHeader>
                            <CardBody className="space-y-4">
                                {['GPT-4 Turbo', 'Claude 3 Opus', 'Llama 3 70B', 'Mistral Large'].map((model) => (
                                    <div key={model} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-hover/50 transition-colors cursor-pointer group">
                                        <div className="flex items-center gap-3">
                                            <div className="w-2 h-2 rounded-full bg-primary/50 group-hover:bg-primary transition-all" />
                                            <span className="font-medium">{model}</span>
                                        </div>
                                        <span className="text-sm text-text-muted">$340.00</span>
                                    </div>
                                ))}
                            </CardBody>
                        </Card>
                    </div>
                </div>
            </div>


        </div>
    );
}
