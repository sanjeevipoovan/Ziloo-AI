import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { AuthLayout } from "../components/layout/AuthLayout";
import { Field, TextInput } from "../components/ui/Input";
import { Button } from "../components/ui/Button";
import { ApiError } from "../lib/api";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await register(email, password, fullName || undefined);
      navigate("/chat");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create your account");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout>
      <h1 className="mb-6 text-sm font-medium text-ink-muted">Create your account</h1>
      {error && <div className="mb-3.5 rounded-lg bg-danger/10 px-3 py-2.5 text-sm text-danger">{error}</div>}
      <form onSubmit={handleSubmit}>
        <Field label="Full name" hint="Optional">
          <TextInput value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Ada Lovelace" />
        </Field>
        <Field label="Email">
          <TextInput type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
        </Field>
        <Field label="Password" hint="At least 8 characters">
          <TextInput
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </Field>
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="mt-4 text-center text-xs text-ink-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-primary">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
