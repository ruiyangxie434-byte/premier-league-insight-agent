"use client";
import { useEffect, useState } from "react";
import { SiteHeader } from "../../components/system/site-header";
import { hubRequest } from "../../services/hub";
export default function AccountPage() {
  const [user, setUser] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    hubRequest<{ username: string }>("/auth/me", { signal: controller.signal }).then((r) => setUser(r.username)).catch(() => {}).finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => controller.abort();
  }, []);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setMessage("");
    try { const r = await hubRequest<{ username: string }>(`/auth/${mode}`, { method: "POST", body: JSON.stringify({ username, password }) }); setUser(r.username); setPassword(""); }
    catch (e) { setMessage(e instanceof Error ? e.message : "请求失败"); }
    finally { setBusy(false); }
  }
  async function logout() {
    setBusy(true); setMessage("");
    try { await hubRequest("/auth/logout", { method: "POST" }); setUser(null); }
    catch (e) { setMessage(e instanceof Error ? e.message : "退出失败"); }
    finally { setBusy(false); }
  }
  return <main className="page-shell hub-shell"><SiteHeader /><section className="hub-panel account-panel">
    <p className="eyebrow">YOUR ACCOUNT</p><h1>{user ? `欢迎，${user}` : "登录你的英超工作台"}</h1>
    {checking ? <p role="status">正在检查登录状态…</p> : user ? <><p>登录状态已保存，刷新页面仍可使用。</p><button disabled={busy} onClick={logout} className="secondary-button">{busy ? "退出中…" : "退出登录"}</button></> : <>
      <div className="hub-tabs"><button aria-pressed={mode === "login"} disabled={busy} onClick={() => {setMode("login"); setMessage("");}}>登录</button><button aria-pressed={mode === "register"} disabled={busy} onClick={() => {setMode("register"); setMessage("");}}>注册</button></div>
      <form onSubmit={submit} className="account-form"><label>用户名<input required pattern="[A-Za-z0-9_]{3,32}" minLength={3} maxLength={32} autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="3–32 位字母、数字或下划线" /></label><label>密码<input required type="password" minLength={10} maxLength={128} autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="至少 10 位" /></label><button className="primary-button" disabled={busy}>{busy ? "提交中…" : mode === "login" ? "登录" : "创建账户"}</button></form>
    </>}{message && <p role="alert" className="hub-error">{message}</p>}
  </section></main>;
}
