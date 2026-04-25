import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { registerUser } from "../api/authApi";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
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
    mutation.mutate(form);
  };

  return (
    <div>
      <h1>Register</h1>
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
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
          {mutation.isPending ? "Creating..." : "Register"}
        </button>
      </form>
      {error && <p>{error}</p>}
      <p>
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </div>
  );
}