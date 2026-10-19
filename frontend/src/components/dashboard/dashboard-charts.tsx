"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Bar,
  BarChart,
} from "recharts";

import type {
  ExpenseCategoryBreakdown,
  MonthlyTrendItem,
} from "@/lib/analytics-api";
import { formatMoney, formatShortMonth } from "@/lib/format";

const chartColors = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
];

export function ExpenseDonutChart({
  categories,
}: {
  categories: ExpenseCategoryBreakdown[];
}) {
  if (categories.length === 0) {
    return <ChartEmpty message="No expenses to chart yet." />;
  }

  const data = categories.map((category) => ({
    name: category.category_name,
    amount: Number(category.amount),
    percentage: category.percentage,
  }));

  return (
    <div className="mt-4 h-72">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="amount"
            nameKey="name"
            innerRadius="58%"
            outerRadius="78%"
            paddingAngle={2}
            stroke="var(--color-surface)"
            strokeWidth={2}
          >
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={chartColors[index % chartColors.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value) => formatMoney(String(value))}
            contentStyle={{ borderRadius: 12, border: "1px solid #e5e7eb" }}
          />
          <Legend
            verticalAlign="bottom"
            formatter={(value) => <span className="text-xs text-text">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
      <p className="sr-only">
        Expense breakdown:{" "}
        {data.map((item) => `${item.name}, ${formatMoney(String(item.amount))}`).join("; ")}
      </p>
    </div>
  );
}

export function MonthlyTrendChart({ months }: { months: MonthlyTrendItem[] }) {
  if (months.length === 0) {
    return <ChartEmpty message="No monthly trend data yet." />;
  }

  const data = months.map((item) => ({
    month: formatShortMonth(item.year, item.month),
    income: Number(item.income),
    expenses: Number(item.expenses),
  }));

  return (
    <div className="mt-4 h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6b7280" }} />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: "#6b7280" }}
            tickFormatter={(value) => `Rs ${Number(value).toLocaleString("en-IN")}`}
          />
          <Tooltip
            formatter={(value) => formatMoney(String(value))}
            contentStyle={{ borderRadius: 12, border: "1px solid #e5e7eb" }}
          />
          <Legend formatter={(value) => <span className="text-xs capitalize text-text">{value}</span>} />
          <Bar dataKey="income" name="Income" fill="#10b981" radius={[6, 6, 0, 0]} />
          <Bar dataKey="expenses" name="Expenses" fill="#f43f5e" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="sr-only">
        Monthly income and expenses chart for {months.length} months.
      </p>
    </div>
  );
}

function ChartEmpty({ message }: { message: string }) {
  return (
    <div className="flex h-72 items-center justify-center text-sm text-text-muted">
      {message}
    </div>
  );
}
