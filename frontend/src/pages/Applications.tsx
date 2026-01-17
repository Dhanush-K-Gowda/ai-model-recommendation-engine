
import { Search, Filter, Plus, MoreHorizontal } from 'lucide-react';
import { Card, CardBody } from '../components/UI/Card';

const apps = [
    { id: 1, name: 'Application 1', model: 'GPT-4 Turbo', status: 'Active', usage: '2.4M', cost: '$45.20', trend: '+12%' },
    { id: 2, name: 'Application 2', model: 'Claude 3 Opus', status: 'Active', usage: '1.1M', cost: '$89.00', trend: '+5%' },
    { id: 3, name: 'Application 3', model: 'Llama 3 70B', status: 'Inactive', usage: '0', cost: '$0.00', trend: '0%' },
    { id: 4, name: 'Application 4', model: 'Mistral Large', status: 'Active', usage: '500k', cost: '$12.50', trend: '-2%' },
    { id: 5, name: 'Application 5', model: 'GPT-4o', status: 'Active', usage: '120k', cost: '$5.60', trend: '+8%' },
    { id: 6, name: 'Application 6', model: 'Gemini 1.5 Pro', status: 'Active', usage: '890k', cost: '$18.90', trend: '+1%' },
];

export default function Applications() {
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
                    <input type="text" placeholder="Search apps..." className="bg-transparent border-none pl-10 pr-4 py-2 text-sm focus:outline-none text-text-main w-64 placeholder:text-text-muted/50" />
                </div>
                <div className="w-px h-6 bg-border" />
                <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-muted hover:text-text-main transition-colors cursor-pointer">
                    <Filter className="w-4 h-4" />
                    <span>Filter</span>
                </button>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {apps.map(app => (
                    <Card key={app.id} hoverEffect className="group cursor-pointer">
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
                                <div className="flex justify-between text-sm">
                                    <span className="text-text-muted">Status</span>
                                    <span className={`font-medium text-xs flex items-center gap-1.5 ${app.status === 'Active' ? 'text-emerald-400' : 'text-text-muted'}`}>
                                        <span className={`w-1.5 h-1.5 rounded-full ${app.status === 'Active' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 'bg-text-muted'}`}></span>
                                        {app.status}
                                    </span>
                                </div>
                            </div>

                            <div className="pt-4 border-t border-border flex items-center justify-between">
                                <div>
                                    <p className="text-[10px] uppercase tracking-wider text-text-muted font-bold">Usage</p>
                                    <p className="font-medium text-sm text-text-main mt-0.5">{app.usage}</p>
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
        </div>
    );
}
