import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { registerUser } from "../api/authApi";
import { useQuery } from "@tanstack/react-query";
import { fetchManagers } from "../api/userApi";


export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "",
    manager_id: "",
  });
  const { data: managers = [], isPending } = useQuery({
    queryKey: ["managers"],
    queryFn: fetchManagers,
  });
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: registerUser,
    onSuccess: () => navigate("/login"),
    onError: (err) => {
      setError(err?.response?.data?.detail || "Register failed");
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");

    const payload = {
      ...form,
      manager_id: form.role === "employee" ? form.manager_id : null,
    };

    mutation.mutate(payload);
  };

  return (
    <div className="min-h-screen bg-[#212121] text-white flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-[#171717] border border-white/10 rounded-2xl shadow-xl p-8">
        <h1 className="text-3xl font-semibold text-center mb-2">Register</h1>
        <p className="text-gray-400 text-center mb-8">
          Create your account to get started
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            className="w-full rounded-xl bg-[#2f2f2f] border border-white/10 px-4 py-3 outline-none placeholder:text-gray-400 focus:border-white/40 transition"
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />

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
          <select
            className="w-full rounded-xl bg-[#2f2f2f] border border-white/10 px-4 py-3"
            value={form.role}
            onChange={(e) =>
              setForm({ ...form, role: e.target.value, manager_id: "" })
            }
          >
            <option value="">Please select role</option>
            <option value="employee">Employee</option>
            <option value="manager">Manager</option>
            <option value="hr">HR</option>
          </select>


          {form.role === "employee" && (
            <select
              className="w-full rounded-xl bg-[#2f2f2f] border border-white/10 px-4 py-3"
              value={form.manager_id}
              onChange={(e) =>
                setForm({ ...form, manager_id: e.target.value })
              }
            >
              <option value="">Select Manager</option>

              {managers.map((manager) => (
                <option key={manager.id} value={manager.id}>
                  {manager.name}
                </option>
              ))}
            </select>
          )}

          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full rounded-xl bg-white text-black py-3 font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {mutation.isPending ? "Creating..." : "Register"}
          </button>
        </form>



        <p className="mt-6 text-center text-gray-400">
          Already have an account?{" "}
          <Link to="/login" className="text-white font-medium hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}