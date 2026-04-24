import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./pages/Dashboard";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div style={{ background: "#020817", height: "100vh", display: "flex", alignItems: "center", justifyContent: "center", color: "#38bdf8", fontFamily: "monospace" }}>
      Loading...
    </div>
  );
  return user ? children : <Navigate to="/login" />;
}

function LoginPage() {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(form.email, form.password);
      window.location.href = "/";
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: "#020817", minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "monospace" }}>
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "16px", padding: "40px", width: "360px" }}>
        <h1 style={{ color: "#38bdf8", margin: "0 0 8px", fontSize: "24px", fontWeight: 700 }}>⚡ FMWP</h1>
        <p style={{ color: "#64748b", margin: "0 0 32px", fontSize: "13px" }}>Finance Management Platform</p>
        {error && <p style={{ color: "#f87171", fontSize: "13px", marginBottom: "16px" }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          {["email", "password"].map((field) => (
            <div key={field} style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: "11px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }}>{field}</label>
              <input
                type={field}
                value={form[field]}
                onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                style={{ width: "100%", background: "#020817", border: "1px solid #1e293b", borderRadius: "8px", padding: "10px 12px", color: "#e2e8f0", fontSize: "14px", boxSizing: "border-box" }}
                required
              />
            </div>
          ))}
          <button type="submit" disabled={loading} style={{ width: "100%", background: "#38bdf8", color: "#020817", border: "none", borderRadius: "8px", padding: "12px", fontWeight: 700, fontSize: "14px", cursor: "pointer", marginTop: "8px" }}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" toastOptions={{ style: { background: "#0f172a", color: "#e2e8f0", border: "1px solid #1e293b" } }} />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}