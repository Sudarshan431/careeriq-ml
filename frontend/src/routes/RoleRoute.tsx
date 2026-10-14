import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { Role } from "../types/auth";

export function RoleRoute({ allow }: { allow: Role[] }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!allow.includes(user.role)) {
    const home = user.role === "RECRUITER" ? "/recruiter/dashboard" : user.role === "ADMIN" ? "/admin/dashboard" : "/candidate/dashboard";
    return <Navigate to={home} replace />;
  }
  return <Outlet />;
}
