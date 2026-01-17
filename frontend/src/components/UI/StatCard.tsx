import { Card, CardBody } from './Card';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
    label: string;
    value: string;
    trend?: string;
    trendUp?: boolean;
    icon: LucideIcon;
    color?: 'primary' | 'secondary' | 'accent';
}

export function StatCard({ label, value, trend, trendUp, icon: Icon, color = 'primary' }: StatCardProps) {
    const colorStyles = {
        primary: 'text-primary bg-primary/10',
        secondary: 'text-secondary bg-secondary/10',
        accent: 'text-accent bg-accent/10',
    };

    return (
        <Card hoverEffect>
            <CardBody className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-text-muted font-medium tracking-wide uppercase text-[10px]">{label}</p>
                    <h3 className="text-3xl font-bold text-text-main mt-1 font-display tracking-tight">{value}</h3>
                    {trend && (
                        <div className="flex items-center gap-1.5 mt-2 bg-white/5 w-fit px-2 py-1 rounded-md">
                            <span className={`text-xs font-bold ${trendUp ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {trendUp ? '↑' : '↓'} {trend}
                            </span>
                            <span className="text-[10px] text-text-muted">vs last month</span>
                        </div>
                    )}
                </div>
                <div className={`p-3 rounded-xl ${colorStyles[color]} ring-1 ring-inset ring-white/5`}>
                    <Icon className="w-6 h-6" />
                </div>
            </CardBody>
        </Card>
    );
}
