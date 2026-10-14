import { useState } from "react";
import { Outlet } from "react-router-dom";
import { LayoutDashboard, User, FileUp, Briefcase, Target, FileText, Route as RouteIcon, Sparkles } from "lucide-react";
import { Sidebar, type NavItem } from "../components/layout/Sidebar";
import { Header } from "../components/layout/Header";

const items: NavItem[] = [
  { to: "/candidate/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/candidate/profile", label: "Profile", icon: User },
  { to: "/candidate/resume", label: "Resume", icon: FileUp },
  { to: "/candidate/jobs", label: "Jobs", icon: Briefcase },
  { to: "/candidate/applications", label: "Applications", icon: FileText },
  { to: "/candidate/skills", label: "Skill Gap", icon: Target },
  { to: "/candidate/career-plans", label: "Career Plans", icon: RouteIcon },
  { to: "/candidate/assistant", label: "AI Assistant", icon: Sparkles },
];

export function CandidateLayout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar items={items} open={open} onClose={() => setOpen(false)} />
      <div className="flex flex-1 flex-col">
        <Header onMenuClick={() => setOpen(true)} />
        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
