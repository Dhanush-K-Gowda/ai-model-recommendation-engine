import { LayoutDashboard } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
];

export default function Sidebar() {
    return (
        <aside className="w-64 h-screen max-h-screen sticky top-0 bg-surface/50 backdrop-blur-xl border-r border-border flex flex-col pt-8">
            <div className="px-6 mb-12">
                <h1 className="text-2xl font-display font-bold tracking-wider bg-gradient-to-r from-primary via-primary-glow to-secondary bg-clip-text text-transparent">
                    MRE
                </h1>
                <p className="text-xs text-text-muted mt-1 tracking-wider uppercase opacity-60">Recommendation Engine</p>
            </div>
            <nav className="flex-1 px-4 space-y-3">
                {navItems.map((item) => (
                    <NavLink
                        key={item.href}
                        to={item.href}
                        className={({ isActive }: { isActive: boolean }) =>
                            cn(
                                "flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-300 group relative overflow-hidden",
                                isActive
                                    ? "bg-primary/10 text-primary border border-primary/20"
                                    : "text-text-muted hover:text-text-main hover:bg-surface-hover/50 hover:border hover:border-border/50 border border-transparent"
                            )
                        }
                    >
                        {({ isActive }: { isActive: boolean }) => (
                            <>
                                <item.icon className={cn("w-5 h-5 transition-colors", isActive ? "text-primary" : "group-hover:text-text-main")} />
                                <span className="font-medium tracking-wide">{item.label}</span>
                                {isActive && (
                                    <motion.div
                                        layoutId="activeNavIndicator"
                                        className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-50"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                    />
                                )}
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 mt-auto">
                <div className="p-4 rounded-xl bg-gradient-to-br from-surface to-surface-hover border border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-xs font-bold text-white">
                            JD
                        </div>
                        <div>
                            <p className="text-sm font-medium text-text-main">John Doe</p>
                            <p className="text-xs text-text-muted">Pro Plan</p>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    );
}
