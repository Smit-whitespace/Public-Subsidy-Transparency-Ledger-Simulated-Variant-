export function formatCurrency(value) {

  if (value === null || value === undefined) {
    return "₹0";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return "₹0";
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(number);
}