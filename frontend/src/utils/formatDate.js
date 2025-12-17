function formatDate(value, options = {}) {
  if (value === null || value === undefined) {
    return "—";
  }

  const date = new Date(value);

  if (isNaN(date.getTime())) {
    return "—";
  }

  const locale = options.locale || "en-IN";

  const defaultOptions = {
    year: "numeric",
    month: "short",
    day: "2-digit"
  };

  const { locale: _, ...userOptions } = options;

  const formatOptions = {
    ...defaultOptions,
    ...userOptions
  };

  const formatter = new Intl.DateTimeFormat(locale, formatOptions);

  return formatter.format(date);
}

export { formatDate };