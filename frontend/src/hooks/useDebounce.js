import { useState, useEffect } from "react";

export default function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const validDelay = typeof delay === "number" && delay > 0 ? delay : 300;

    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, validDelay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}