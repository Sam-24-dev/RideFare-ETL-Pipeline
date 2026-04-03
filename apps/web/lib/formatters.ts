const currencyFormatter = new Intl.NumberFormat("es-EC", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("es-EC", {
  maximumFractionDigits: 0,
});

const decimalFormatter = new Intl.NumberFormat("es-EC", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
});

const longDateFormatter = new Intl.DateTimeFormat("es-EC", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

export function formatInteger(value: number): string {
  return integerFormatter.format(value);
}

export function formatMultiplier(value: number): string {
  return `${decimalFormatter.format(value)}x`;
}

export function formatCompactDate(value: string | null): string {
  if (!value) {
    return "Sin fecha";
  }
  return longDateFormatter.format(new Date(value));
}

export function formatPercentage(value: number): string {
  return `${integerFormatter.format(value * 100)}%`;
}
