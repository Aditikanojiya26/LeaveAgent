import { createContext, useContext, useEffect, useState } from "react";
import { getMe } from "../api/authApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
  try {
    const data = await getMe();
    setUser(data);
    return data;   // ✅ FIX
  } catch {
    setUser(null);
    return null;   // ✅ important
  } finally {
    setLoading(false);
  }
};

  useEffect(() => {
    refreshUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}