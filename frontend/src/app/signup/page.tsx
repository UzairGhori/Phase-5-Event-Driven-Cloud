"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) {
      const data = await res.json();
      setError(data.detail || "Signup failed");
      return;
    }
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSignup} className="bg-white p-8 rounded-lg shadow-md w-80 space-y-4">
        <h1 className="text-2xl font-bold text-center">Sign Up</h1>
        {error && <p className="text-red-500 text-sm text-center">{error}</p>}
        <input className="w-full border rounded px-3 py-2" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
        <input className="w-full border rounded px-3 py-2" placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="w-full border rounded px-3 py-2" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">Create Account</button>
        <p className="text-xs text-center text-gray-500">
          Have an account? <a href="/login" className="text-blue-600 hover:underline">Login</a>
        </p>
      </form>
    </div>
  );
}
