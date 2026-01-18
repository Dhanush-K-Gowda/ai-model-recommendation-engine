import { CheckCircle2, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { Card, CardBody } from '../components/UI/Card';
import { useState, useEffect } from 'react';
import { cn } from '../lib/utils';
import { apiClient, type Recommendation, type Application } from '../lib/api';

interface ApplicationWithRecommendations extends Application {
    recommendations: Recommendation[];
}

export default function Recommendations() {
    const [appsWithRecs, setAppsWithRecs] = useState<ApplicationWithRecommendations[]>([]);
    const [expandedApps, setExpandedApps] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generating, setGenerating] = useState<Set<string>>(new Set());
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // Load applications and their recommendations on mount
    useEffect(() => {
        loadRecommendations();
    }, []);

    const loadRecommendations = async () => {
        setLoading(true);
        setError(null);

        try {
            // Get all applications
            const appsResponse = await apiClient.getApplications();

            if (appsResponse.status !== 'success' || !appsResponse.data) {
                setError(appsResponse.message || 'Failed to load applications');
                return;
            }

            const applications = appsResponse.data.applications || [];

            // Load recommendations for each application
            const appsWithRecommendations = await Promise.all(
                applications.map(async (app) => {
                    const recsResponse = await apiClient.getRecommendations(app.application_id);
                    const recommendations =
                        recsResponse.status === 'success' && recsResponse.data
                            ? recsResponse.data.recommendations || []
                            : [];

                    return {
                        ...app,
                        recommendations
                    };
                })
            );

            // Show all applications (including those without recommendations)
            setAppsWithRecs(appsWithRecommendations);

            // Auto-expand first application with recommendations if any
            const firstAppWithRecs = appsWithRecommendations.find(app => app.recommendations.length > 0);
            if (firstAppWithRecs) {
                setExpandedApps(new Set([firstAppWithRecs.application_id]));
            } else if (appsWithRecommendations.length > 0) {
                // If no apps have recommendations, expand the first one anyway
                setExpandedApps(new Set([appsWithRecommendations[0].application_id]));
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
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

    const formatCost = (cost: number): string => {
        return `$${cost.toFixed(2)}`;
    };

    const generateRecommendations = async (applicationId: string) => {
        setGenerating(prev => new Set(prev).add(applicationId));
        setError(null);
        setSuccessMessage(null);

        try {
            const response = await apiClient.generateRecommendationsForApp(applicationId);

            if (response.status === 'success' && response.data) {
                // Update the specific application's recommendations in state
                setAppsWithRecs(prev => prev.map(app => {
                    if (app.application_id === applicationId) {
                        return {
                            ...app,
                            recommendations: response.data.recommendations || []
                        };
                    }
                    return app;
                }));
                
                // Show success message
                const appName = appsWithRecs.find(a => a.application_id === applicationId)?.name || applicationId;
                const count = response.data.new_recommendations_generated || response.data.count || 0;
                setSuccessMessage(`Successfully generated ${count} recommendation${count !== 1 ? 's' : ''} for ${appName}`);
                
                // Auto-expand the application to show new recommendations
                setExpandedApps(prev => new Set(prev).add(applicationId));
                
                // Clear success message after 5 seconds
                setTimeout(() => setSuccessMessage(null), 5000);
            } else {
                setError(response.message || 'Failed to generate recommendations');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setGenerating(prev => {
                const newSet = new Set(prev);
                newSet.delete(applicationId);
                return newSet;
            });
        }
    };

    const totalRecommendations = appsWithRecs.reduce((sum, app) => sum + app.recommendations.length, 0);

    return (
        <div className="space-y-8 animate-fade-in text-text-main pb-20">
            <div>
                <h1 className="text-4xl font-display font-bold">Model Recommendations</h1>
                <p className="text-text-muted mt-2">AI model recommendations for each application.</p>
            </div>

            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold">Recommendations by Application</h2>
                    <span className="text-sm text-text-muted">
                        {appsWithRecs.length} applications • {totalRecommendations} recommendations
                    </span>
                </div>

                {error && (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
                        {error}
                    </div>
                )}

                {successMessage && (
                    <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                        {successMessage}
                    </div>
                )}

                {loading && (
                    <div className="text-center py-12 text-text-muted">
                        Loading recommendations...
                    </div>
                )}

                {!loading && !error && appsWithRecs.length === 0 && (
                    <div className="text-center py-12 text-text-muted">
                        No recommendations found for any applications.
                    </div>
                )}

                {!loading && appsWithRecs.length > 0 && (
                    <div className="space-y-4">
                        {appsWithRecs.map((app) => {
                            const isExpanded = expandedApps.has(app.application_id);
                            return (
                                <Card key={app.application_id} hoverEffect>
                                    <CardBody className="p-0">
                                        {/* Application Header */}
                                        <div
                                            className="p-6 cursor-pointer border-b border-border"
                                            onClick={() => toggleApp(app.application_id)}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4 flex-1">
                                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border border-white/5">
                                                        <span className="text-xl font-bold bg-gradient-to-br from-primary to-secondary bg-clip-text text-transparent">
                                                            {app.id}
                                                        </span>
                                                    </div>
                                                    <div className="flex-1">
                                                        <h3 className="text-xl font-bold mb-1">{app.name}</h3>
                                                        <div className="flex items-center gap-4 text-sm flex-wrap">
                                                            <span className="text-text-muted">
                                                                Model: <span className="text-text-main font-medium">{app.model}</span>
                                                            </span>
                                                            {(app.categories && app.categories.length > 0) && (
                                                                <span className="text-text-muted">
                                                                    Category: 
                                                                    <div className="inline-flex flex-wrap gap-1 ml-1">
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
                                                                </span>
                                                            )}
                                                            <span className={`font-medium text-xs flex items-center gap-1.5 ${app.is_active ? 'text-emerald-400' : 'text-text-muted'}`}>
                                                                <span className={`w-1.5 h-1.5 rounded-full ${app.is_active ? 'bg-emerald-400' : 'bg-text-muted'}`}></span>
                                                                {app.is_active ? 'Active' : 'Inactive'}
                                                            </span>
                                                            <span className={cn(
                                                                "text-text-muted",
                                                                app.recommendations.length === 0 && "text-text-muted/60"
                                                            )}>
                                                                {app.recommendations.length > 0
                                                                    ? `${app.recommendations.length} recommendation${app.recommendations.length !== 1 ? 's' : ''}`
                                                                    : 'No recommendations'
                                                                }
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 ml-4">
                                                    {app.recommendations.length > 0 && (
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                generateRecommendations(app.application_id);
                                                            }}
                                                            disabled={generating.has(app.application_id)}
                                                            className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary border border-primary/20 rounded-lg hover:bg-primary/15 transition-colors text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            <Sparkles className="w-3 h-3" />
                                                            {generating.has(app.application_id) ? 'Generating...' : 'Regenerate'}
                                                        </button>
                                                    )}
                                                    {isExpanded ? (
                                                        <ChevronUp className="w-5 h-5 text-text-muted" />
                                                    ) : (
                                                        <ChevronDown className="w-5 h-5 text-text-muted" />
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Recommendations List */}
                                        {isExpanded && (
                                            <div className="p-6 space-y-4">
                                                {app.recommendations.length === 0 ? (
                                                    <div className="text-center py-8">
                                                        <p className="mb-4 text-text-muted">No recommendations available for this application yet.</p>
                                                        <button
                                                            onClick={() => generateRecommendations(app.application_id)}
                                                            disabled={generating.has(app.application_id)}
                                                            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed mx-auto"
                                                        >
                                                            <Sparkles className="w-4 h-4" />
                                                            {generating.has(app.application_id) ? 'Generating...' : 'Generate Recommendations'}
                                                        </button>
                                                        <p className="text-xs text-text-muted mt-3">This will analyze your usage data and generate model recommendations.</p>
                                                    </div>
                                                ) : (
                                                    app.recommendations.map((rec, i) => (
                                                        <Card
                                                        key={rec.id}
                                                        hoverEffect
                                                        className={cn("border-l-4", i === 0 ? "border-l-primary" : "border-l-transparent")}
                                                    >
                                                        <CardBody className="p-0">
                                                            <div className="p-6 grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
                                                                <div className="md:col-span-1">
                                                                    <div className="flex items-center gap-2 mb-1">
                                                                        {i === 0 && (
                                                                            <span className="bg-primary/20 text-primary text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                                                                                Best Match
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    <h3 className="text-lg font-bold">{rec.recommended_model || 'Unknown Model'}</h3>
                                                                    <p className="text-sm text-text-muted">{rec.provider || 'Unknown Provider'}</p>
                                                                </div>

                                                                <div className="md:col-span-2 grid grid-cols-3 gap-4">
                                                                    <div className="text-center p-2 rounded-lg bg-surface-hover/30">
                                                                        <div className="text-xs text-text-muted mb-1">Confidence</div>
                                                                        <div className="font-bold text-primary">{Math.round(rec.confidence_score)}%</div>
                                                                    </div>
                                                                    <div className="text-center p-2 rounded-lg bg-surface-hover/30">
                                                                        <div className="text-xs text-text-muted mb-1">Cost Savings</div>
                                                                        <div className="font-bold text-emerald-400">{rec.cost_savings_percent.toFixed(1)}%</div>
                                                                    </div>
                                                                    <div className="text-center p-2 rounded-lg bg-surface-hover/30">
                                                                        <div className="text-xs text-text-muted mb-1">Monthly Savings</div>
                                                                        <div className="font-bold">{formatCost(rec.monthly_savings)}</div>
                                                                    </div>
                                                                </div>

                                                                <div className="md:col-span-1 text-right">
                                                                    {/* <button className="px-5 py-2 rounded-lg border border-border hover:bg-white/5 font-medium text-sm transition-colors">
                                                                        Select
                                                                    </button> */}
                                                                </div>
                                                            </div>
                                                            <div className="bg-surface-hover/20 px-6 py-3 border-t border-border flex flex-wrap gap-4 text-xs">
                                                                <span className="text-text-muted flex items-center gap-2">
                                                                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                                                    Current: <span className="text-text-main">{rec.current_model}</span>
                                                                </span>
                                                                {rec.reasoning && (
                                                                    <span className="text-text-muted">
                                                                        {rec.reasoning}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </CardBody>
                                                        </Card>
                                                    ))
                                                )}
                                            </div>
                                        )}
                                    </CardBody>
                                </Card>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
