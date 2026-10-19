export default function CategoriesLoading() {
  return (
    <div className="space-y-5" aria-label="Loading categories">
      <div className="h-12 w-64 animate-pulse rounded-control bg-border" />
      <div className="h-28 animate-pulse rounded-card bg-surface shadow-card" />
      <div className="h-72 animate-pulse rounded-card bg-surface shadow-card" />
    </div>
  );
}
