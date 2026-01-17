import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';
import type { HTMLMotionProps } from 'framer-motion';
import React from 'react';

interface CardProps extends Omit<HTMLMotionProps<"div">, 'children'> {
    hoverEffect?: boolean;
    children?: React.ReactNode;
}

export function Card({ className, children, hoverEffect = false, ...props }: CardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className={cn(
                "bg-surface border border-border rounded-2xl overflow-hidden relative backdrop-blur-sm",
                hoverEffect && "hover:border-primary/30 transition-all duration-300 group",
                className
            )}
            {...props}
        >
            {children}
            {hoverEffect && (
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            )}
        </motion.div>
    );
}

export function CardHeader({ className, children }: React.HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("p-6 pb-2", className)}>{children}</div>;
}

export function CardBody({ className, children }: React.HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("p-6 pt-2", className)}>{children}</div>;
}
