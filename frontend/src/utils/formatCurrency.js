function formatCurrency(value, options = {}) {
  if (value === null || value === undefined) {
    return "—";
  }

  const numValue = typeof value === "string" ? parseFloat(value) : value;

  if (isNaN(numValue)) {
    return "—";
  }

  const locale = options.locale || "en-IN";
  const currency = options.currency || "INR";
  const minimumFractionDigits = options.minimumFractionDigits !== undefined ? options.minimumFractionDigits : 0;
  const maximumFractionDigits = options.maximumFractionDigits !== undefined ? options.maximumFractionDigits : 2;

  const formatter = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
    minimumFractionDigits: minimumFractionDigits,
    maximumFractionDigits: maximumFractionDigits
  });

  return formatter.format(numValue);
}

export { formatCurrency };