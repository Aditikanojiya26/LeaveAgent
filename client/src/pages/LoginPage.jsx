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
    const loggedInUser = await refreshUser();

    if (loggedInUser.role === "manager") {
      navigate("/manager");
    } else {
      navigate("/chat");
    }
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
    <div className="min-h-screen bg-[#212121] text-white flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-[#171717] border border-white/10 rounded-2xl shadow-xl p-8">
        <h1 className="text-3xl font-semibold text-center mb-2">Login</h1>
        <p className="text-gray-400 text-center mb-8">
          Welcome back to your account
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            className="w-full rounded-xl bg-[#2f2f2f] border border-white/10 px-4 py-3 outline-none placeholder:text-gray-400 focus:border-white/40 transition"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />

          <input
            className="w-full rounded-xl bg-[#2f2f2f] border border-white/10 px-4 py-3 outline-none placeholder:text-gray-400 focus:border-white/40 transition"
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />

          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full rounded-xl bg-white text-black py-3 font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {mutation.isPending ? "Logging in..." : "Login"}
          </button>
        </form>

        {error && (
          <p className="mt-4 rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-300">
            {error}
          </p>
        )}

        <p className="mt-6 text-center text-gray-400">
          No account?{" "}
          <Link to="/register" className="text-white font-medium hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}