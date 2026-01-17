import { Activity, CreditCard, Layers } from 'lucide-react';
import { StatCard } from '../components/UI/StatCard';
import { Card, CardHeader, CardBody } from '../components/UI/Card';
import { Search, Filter, Plus, MoreHorizontal, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { cn } from '../lib/utils';
import { Zap, DollarSign, Clock, CheckCircle2 } from 'lucide-react';

const apps = [
    { id: 1, name: 'Application 1', model: 'GPT-4 Turbo', status: 'Active', usage: '2.4M', cost: '$45.20', trend: '+12%' },
    { id: 2, name: 'Application 2', model: 'Claude 3 Opus', status: 'Active', usage: '1.1M', cost: '$89.00', trend: '+5%' },
    { id: 3, name: 'Application 3', model: 'Llama 3 70B', status: 'Inactive', usage: '0', cost: '$0.00', trend: '0%' },
    { id: 4, name: 'Application 4', model: 'Mistral Large', status: 'Active', usage: '500k', cost: '$12.50', trend: '-2%' },
    { id: 5, name: 'Application 5', model: 'GPT-4o', status: 'Active', usage: '120k', cost: '$5.60', trend: '+8%' },
    { id: 6, name: 'Application 6', model: 'Gemini 1.5 Pro', status: 'Active', usage: '890k', cost: '$18.90', trend: '+1%' },
];

const recommendations = [
    {
        name: 'Mistral Large',
        provider: 'Mistral AI',
        score: 98,
        cost: '$8.00',
        speed: '120 t/s',
        features: ['Open Source', 'High Reasoning', '128k Context'],
        bestFor: 'Complex reasoning tasks & coding',
    },
    {
        name: 'GPT-4 Turbo',
        provider: 'OpenAI',
        score: 95,
        cost: '$10.00',
        speed: '90 t/s',
        features: ['SoTA Knowledge', 'Function Calling', 'JSON Mode'],
        bestFor: 'General purpose & instruction following',
    },
    {
        name: 'Claude 3 Haiku',
        provider: 'Anthropic',
        score: 88,
        cost: '$0.25',
        speed: '200 t/s',
        features: ['Extremely Fast', 'Vision Capable', 'Cheap'],
        bestFor: 'High volume simple tasks',
    }
];

export default function Dashboard() {
    const [expandedApps, setExpandedApps] = useState<Set<number>>(new Set());
    const [selectedTask, setSelectedTask] = useState('generation');

    const toggleApp = (appId: number) => {
        const newExpanded = new Set(expandedApps);
        if (newExpanded.has(appId)) {
            newExpanded.delete(appId);
        } else {
            newExpanded.add(appId);
        }
        setExpandedApps(newExpanded);
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
                        value="$1,240.50"
                        trend="12%"
                        trendUp={true}
                        icon={CreditCard}
                        color="primary"
                    />
                    <StatCard
                        label="Token Usage"
                        value="45.2M"
                        trend="8%"
                        trendUp={true}
                        icon={Activity}
                        color="secondary"
                    />
                    <StatCard
                        label="Active Apps"
                        value="12"
                        trend="0%"
                        trendUp={false}
                        icon={Layers}
                        color="accent"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                    <div className="lg:col-span-2">
                        <Card className="h-full">
                            <CardHeader>
                                <h2 className="text-xl font-bold font-display">Usage Trends</h2>
                            </CardHeader>
                            <CardBody>
                                <div className="h-64 flex items-center justify-center text-text-muted bg-background/50 rounded-xl border border-dashed border-border">
                                    Chart Placeholder (Recharts)
                                </div>
                            </CardBody>
                        </Card>
                    </div>
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

            {/* Applications Section */}
            <div>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h2 className="text-3xl font-display font-bold">Applications</h2>
                        <p className="text-text-muted mt-2">Manage your AI-powered services.</p>
                    </div>
                    <button className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-glow/80 transition-all font-medium cursor-pointer w-fit">
                        <Plus className="w-5 h-5" />
                        <span>New Application</span>
                    </button>
                </div>

                {/* Filters */}
                <div className="flex items-center gap-4 bg-surface p-2 rounded-2xl border border-border w-fit mb-6">
                    <div className="relative">
                        <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                        <input type="text" placeholder="Search apps..." className="bg-transparent border-none pl-10 pr-4 py-2 text-sm focus:outline-none text-text-main w-64 placeholder:text-text-muted/50" />
                    </div>
                    <div className="w-px h-6 bg-border" />
                    <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-muted hover:text-text-main transition-colors cursor-pointer">
                        <Filter className="w-4 h-4" />
                        <span>Filter</span>
                    </button>
                </div>

                {/* Applications List */}
                <div className="space-y-4">
                    {apps.map(app => {
                        const isExpanded = expandedApps.has(app.id);
                        return (
                            <Card key={app.id} hoverEffect className="group">
                                <CardBody>
                                    <div 
                                        className="flex items-center justify-between cursor-pointer"
                                        onClick={() => toggleApp(app.id)}
                                    >
                                        <div className="flex items-center gap-4 flex-1">
                                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border border-white/5">
                                                <span className="text-xl font-bold bg-gradient-to-br from-primary to-secondary bg-clip-text text-transparent">{app.id}</span>
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="text-xl font-bold mb-1">{app.name}</h3>
                                                <div className="flex items-center gap-4 text-sm">
                                                    <span className="text-text-muted">Model: <span className="text-text-main font-medium">{app.model}</span></span>
                                                    <span className={`font-medium text-xs flex items-center gap-1.5 ${app.status === 'Active' ? 'text-emerald-400' : 'text-text-muted'}`}>
                                                        <span className={`w-1.5 h-1.5 rounded-full ${app.status === 'Active' ? 'bg-emerald-400' : 'bg-text-muted'}`}></span>
                                                        {app.status}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-6 text-sm">
                                                <div>
                                                    <p className="text-[10px] uppercase tracking-wider text-text-muted font-bold">Usage</p>
                                                    <p className="font-medium text-text-main mt-0.5">{app.usage}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] uppercase tracking-wider text-text-muted font-bold">Cost</p>
                                                    <p className="font-medium text-text-main mt-0.5">{app.cost}</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 ml-4">
                                            <button 
                                                className="text-text-muted hover:text-text-main p-1 hover:bg-white/5 rounded-lg transition-colors"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                }}
                                            >
                                                <MoreHorizontal className="w-5 h-5" />
                                            </button>
                                            {isExpanded ? (
                                                <ChevronUp className="w-5 h-5 text-text-muted ml-2" />
                                            ) : (
                                                <ChevronDown className="w-5 h-5 text-text-muted ml-2" />
                                            )}
                                        </div>
                                    </div>

                                    {/* Recommendations Section - Expandable */}
                                    {isExpanded && (
                                        <div className="mt-6 pt-6 border-t border-border">
                                            <div className="mb-6">
                                                <h4 className="text-lg font-bold mb-4">Model Recommendations</h4>
                                                
                                                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                                                    {/* Input Form */}
                                                    <div className="lg:col-span-4">
                                                        <Card>
                                                            <CardBody className="space-y-6">
                                                                <div>
                                                                    <label className="block text-sm font-medium mb-3">Task Type</label>
                                                                    <div className="grid grid-cols-2 gap-3">
                                                                        {['generation', 'summarization', 'coding', 'chat'].map(t => (
                                                                            <button
                                                                                key={t}
                                                                                onClick={() => setSelectedTask(t)}
                                                                                className={cn(
                                                                                    "px-4 py-3 rounded-xl border text-sm font-medium transition-all capitalize",
                                                                                    selectedTask === t
                                                                                        ? "bg-primary/20 border-primary text-primary"
                                                                                        : "bg-surface-hover/30 border-border text-text-muted hover:border-text-muted/50"
                                                                                )}
                                                                            >
                                                                                {t}
                                                                            </button>
                                                                        ))}
                                                                    </div>
                                                                </div>

                                                                <div>
                                                                    <label className="block text-sm font-medium mb-3">Priorities</label>
                                                                    <div className="space-y-3">
                                                                        {[
                                                                            { icon: DollarSign, label: 'Low Cost' },
                                                                            { icon: Clock, label: 'Low Latency' },
                                                                            { icon: Zap, label: 'High Quality' }
                                                                        ].map(p => (
                                                                            <div key={p.label} className="flex items-center justify-between p-3 rounded-xl bg-surface-hover/30 border border-border">
                                                                                <div className="flex items-center gap-3">
                                                                                    <p.icon className="w-4 h-4 text-text-muted" />
                                                                                    <span className="text-sm font-medium">{p.label}</span>
                                                                                </div>
                                                                                <input type="range" className="w-24 accent-primary h-1 bg-surface-hover rounded-lg appearance-none cursor-pointer" />
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>

                                                                <button className="w-full py-3.5 bg-gradient-to-r from-primary to-secondary rounded-xl font-bold text-white transition-all hover:opacity-90 active:scale-[0.98]">
                                                                    Generate Recommendations
                                                                </button>
                                                            </CardBody>
                                                        </Card>
                                                    </div>

                                                    {/* Results */}
                                                    <div className="lg:col-span-8 space-y-4">
                                                        <div className="flex items-center justify-between mb-4">
                                                            <h5 className="text-lg font-bold">Top Picks</h5>
                                                            <span className="text-sm text-text-muted">Based on your criteria</span>
                                                        </div>

                                                        {recommendations.map((model, i) => (
                                                            <Card key={model.name} hoverEffect className={cn("border-l-4", i === 0 ? "border-l-primary" : "border-l-transparent")}>
                                                                <CardBody className="p-0">
                                                                    <div className="p-6 grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
                                                                        <div className="md:col-span-1">
                                                                            <div className="flex items-center gap-2 mb-1">
                                                                                {i === 0 && <span className="bg-primary/20 text-primary text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">Best Match</span>}
                                                                            </div>
                                                                            <h3 className="text-lg font-bold">{model.name}</h3>
                                                                            <p className="text-sm text-text-muted">{model.provider}</p>
                                                                        </div>

                                                                        <div className="md:col-span-2 grid grid-cols-3 gap-4">
                                                                            <div className="text-center p-2 rounded-lg bg-surface-hover/30">
                                                                                <div className="text-xs text-text-muted mb-1">Match</div>
                                                                                <div className="font-bold text-primary">{model.score}%</div>
                                                                            </div>
                                                                            <div className="text-center p-2 rounded-lg bg-surface-hover/30">
                                                                                <div className="text-xs text-text-muted mb-1">Cost/1M</div>
                                                                                <div className="font-bold">{model.cost}</div>
                                                                            </div>
                                                                            <div className="text-center p-2 rounded-lg bg-surface-hover/30">
                                                                                <div className="text-xs text-text-muted mb-1">Speed</div>
                                                                                <div className="font-bold">{model.speed}</div>
                                                                            </div>
                                                                        </div>

                                                                        <div className="md:col-span-1 text-right">
                                                                            <button className="px-5 py-2 rounded-lg border border-border hover:bg-white/5 font-medium text-sm transition-colors">
                                                                                Select
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                    <div className="bg-surface-hover/20 px-6 py-3 border-t border-border flex flex-wrap gap-4 text-xs">
                                                                        <span className="text-text-muted flex items-center gap-2">
                                                                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                                                            Best for: <span className="text-text-main">{model.bestFor}</span>
                                                                        </span>
                                                                    </div>
                                                                </CardBody>
                                                            </Card>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </CardBody>
                            </Card>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
