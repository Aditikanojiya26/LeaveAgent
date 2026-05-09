import { useAuth } from "../context/AuthContext";
import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  // Wait until auth check finishes
  if (loading) {
    return 
  }

  // Not logged in
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Role check
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/chat" replace />;
  }

  return children;
}