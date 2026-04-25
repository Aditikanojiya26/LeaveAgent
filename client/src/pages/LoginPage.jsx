import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { loginUser } from "../api/authApi";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: loginUser,
    onSuccess: async () => {
      await refreshUser();
      navigate("/chat");
    },
    onError: (err) => {
      setError(err?.response?.data?.detail || "Login failed");
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");
    mutation.mutate(form);
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Logging in..." : "Login"}
        </button>
      </form>
      {error && <p>{error}</p>}
      <p>
        No account? <Link to="/register">Register</Link>
      </p>
    </div>
  );
}