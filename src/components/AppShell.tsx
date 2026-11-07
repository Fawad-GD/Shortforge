import { Link, useNavigate } from "@tanstack/react-router";
import type { ReactNode } from "react";

import { supabase } from "@/integrations/supabase/client";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/create", label: "Create" },
  { to: "/projects", label: "Projects" },
  { to: "/processing", label: "Processing" },
  { to: "/shorts", label: "Shorts" },
  { to: "/settings", label: "Settings" },
] as const;

export function Logo() {
  return (
    <span className="font-semibold tracking-tight">
      ShortForge<span className="text-primary"> AI</span>
    </span>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-56 shrink-0 border-r bg-sidebar md:flex md:flex-col">
        <div className="px-5 py-5">
          <Link to="/dashboard"><Logo /></Link>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 px-3" aria-label="Main">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
              activeProps={{ className: "bg-sidebar-accent text-sidebar-accent-foreground font-medium" }}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="space-y-1 border-t p-3">
          <Link to="/system" className="block rounded-md px-3 py-2 text-xs text-muted-foreground hover:bg-sidebar-accent">
            System status
          </Link>
          <button
            type="button"
            onClick={async () => {
              await supabase.auth.signOut();
              navigate({ to: "/" });
            }}
            className="w-full rounded-md px-3 py-2 text-left text-xs text-muted-foreground hover:bg-sidebar-accent"
          >
            Sign out
          </button>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <nav className="flex gap-1 overflow-x-auto border-b px-3 py-2 md:hidden" aria-label="Main">
          {NAV.map((item) => (
            <Link key={item.to} to={item.to} className="whitespace-nowrap rounded-md px-3 py-1.5 text-sm text-muted-foreground"
              activeProps={{ className: "bg-secondary text-foreground" }}>
              {item.label}
            </Link>
          ))}
        </nav>
        <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-8 md:px-10">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "completed" ? "bg-success/15 text-success"
    : status === "failed" ? "bg-destructive/15 text-destructive"
    : status === "processing" || status === "rendering" ? "bg-primary/15 text-primary"
    : status === "cancelled" ? "bg-muted text-muted-foreground"
    : "bg-secondary text-secondary-foreground";
  return <span className={`inline-flex rounded px-2 py-0.5 text-xs font-medium capitalize ${tone}`}>{status}</span>;
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="panel flex flex-col items-center px-6 py-16 text-center">
      <h2 className="text-lg font-medium">{title}</h2>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">{body}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
