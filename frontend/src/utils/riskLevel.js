export function getRiskLevel(score) {
  const num = parseFloat(score);
  if (num >= 70) return "high";
  if (num >= 40) return "medium";
  return "low";
}
