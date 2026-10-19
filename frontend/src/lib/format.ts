const moneyFormatter = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatMoney(amount: string): string {
  return `Rs ${moneyFormatter.format(Number(amount))}`;
}

export function formatMonth(year: number, month: number): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    year: "numeric",
  }).format(new Date(year, month - 1, 1));
}

export function formatShortMonth(year: number, month: number): string {
  return new Intl.DateTimeFormat("en-US", { month: "short" }).format(
    new Date(year, month - 1, 1),
  );
}
