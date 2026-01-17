
import { Zap, DollarSign, Clock, CheckCircle2 } from 'lucide-react';
import { Card, CardBody } from '../components/UI/Card';
import { useState } from 'react';
import { cn } from '../lib/utils';

export default function Recommendations() {
    const [selectedTask, setSelectedTask] = useState('generation');

    const recommendations = [
        {
            name: 'Mistral Large',
            provider: 'Mistral AI',
            score: 98,
            cost: '$8.00',
            speed: '120 t/s',
            features: ['Open Source', 'High Reasoning', '128k Context'],
            bestFor: 'Complex reasoning tasks & coding',
            color: 'text-purple-400 border-purple-400/20 bg-purple-400/5'
        },
        {
            name: 'GPT-4 Turbo',
            provider: 'OpenAI',
            score: 95,
            cost: '$10.00',
            speed: '90 t/s',
            features: ['SoTA Knowledge', 'Function Calling', 'JSON Mode'],
            bestFor: 'General purpose & instruction following',
            color: 'text-emerald-400 border-emerald-400/20 bg-emerald-400/5'
        },
        {
            name: 'Claude 3 Haiku',
            provider: 'Anthropic',
            score: 88,
            cost: '$0.25',
            speed: '200 t/s',
            features: ['Extremely Fast', 'Vision Capable', 'Cheap'],
            bestFor: 'High volume simple tasks',
            color: 'text-orange-400 border-orange-400/20 bg-orange-400/5'
        }
    ];

    return (
        <div className="space-y-8 animate-fade-in text-text-main pb-20">
            <div>
                <h1 className="text-4xl font-display font-bold">Model Recommendations</h1>
                <p className="text-text-muted mt-2">Find the perfect model for your specific use-case.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Input Form */}
                <div className="lg:col-span-4 space-y-6">
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
                <div className="lg:col-span-8 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold">Top Picks</h2>
                        <span className="text-sm text-text-muted">Based on your criteria</span>
                    </div>

                    <div className="space-y-4">
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
    );
}
