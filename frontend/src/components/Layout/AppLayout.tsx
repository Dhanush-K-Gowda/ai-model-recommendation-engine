import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function AppLayout() {
    return (
        <div className="flex min-h-screen bg-background text-text-main font-sans selection:bg-primary/30 selection:text-white">
            <div className="fixed inset-0 pointer-events-none bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay z-50"></div>
            <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[150px] pointer-events-none"></div>
            <div className="fixed bottom-[-20%] right-[-10%] w-[40%] h-[40%] bg-secondary/10 rounded-full blur-[150px] pointer-events-none"></div>

            <Sidebar />

            <main className="flex-1 relative overflow-y-auto h-screen scroll-smooth">
                <div className="p-8 max-w-7xl mx-auto pb-20 min-h-full">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
