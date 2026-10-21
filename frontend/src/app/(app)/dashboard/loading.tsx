export default function DashboardLoading() {
  return (
    <div className="space-y-5" aria-label="Loading dashboard">
      <div className="h-12 w-64 animate-pulse rounded-control bg-border" />
      <div className="h-48 animate-pulse rounded-modal bg-primary-tint" />
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="h-96 animate-pulse rounded-card bg-surface shadow-card" />
        <div className="h-96 animate-pulse rounded-card bg-surface shadow-card" />
      </div>
      <div className="h-72 animate-pulse rounded-card bg-surface shadow-card" />
    </div>
  );
}
