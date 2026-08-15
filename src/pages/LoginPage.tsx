import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { AuthLayout } from "../components/layout/AuthLayout";
import { Field, TextInput } from "../components/ui/Input";
import { Button } from "../components/ui/Button";
import { ApiError } from "../lib/api";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/chat");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout>
      <h1 className="mb-6 text-sm font-medium text-ink-muted">Sign in to continue</h1>
      {error && <div className="mb-3.5 rounded-lg bg-danger/10 px-3 py-2.5 text-sm text-danger">{error}</div>}
      <form onSubmit={handleSubmit}>
        <Field label="Email">
          <TextInput type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
        </Field>
        <Field label="Password">
          <TextInput type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
        </Field>
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      <p className="mt-4 text-center text-xs text-ink-muted">
        No account?{" "}
        <Link to="/register" className="font-medium text-primary">
          Create one
        </Link>
      </p>
    </AuthLayout>
  );
}
