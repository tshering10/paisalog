export default function TransactionsLoading() {
  return (
    <div className="space-y-5" aria-label="Loading transactions">
      <div className="h-12 w-64 animate-pulse rounded-control bg-border" />
      <div className="h-32 animate-pulse rounded-card bg-surface shadow-card" />
      <div className="h-96 animate-pulse rounded-card bg-surface shadow-card" />
    </div>
  );
}
