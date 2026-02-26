"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const res = await fetch("/api/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      setError("Invalid credentials");
      return;
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded-lg shadow-md w-80 space-y-4">
        <h1 className="text-2xl font-bold text-center">Login</h1>
        {error && <p className="text-red-500 text-sm text-center">{error}</p>}
        <input className="w-full border rounded px-3 py-2" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        <input className="w-full border rounded px-3 py-2" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">Sign In</button>
        <p className="text-xs text-center text-gray-500">
          No account? <a href="/signup" className="text-blue-600 hover:underline">Sign up</a>
        </p>
      </form>
    </div>
  );
}
