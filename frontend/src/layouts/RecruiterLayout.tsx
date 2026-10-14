import { useState } from "react";
import { Outlet } from "react-router-dom";
import { LayoutDashboard, Briefcase, PlusCircle } from "lucide-react";
import { Sidebar, type NavItem } from "../components/layout/Sidebar";
import { Header } from "../components/layout/Header";

const items: NavItem[] = [
  { to: "/recruiter/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/recruiter/jobs", label: "Jobs", icon: Briefcase },
  { to: "/recruiter/jobs/create", label: "Create Job", icon: PlusCircle },
];

export function RecruiterLayout() {
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
