import { useState, useEffect, useRef, useCallback } from "react";

export default function useFetch(fetchFunction, options = {}) {

  const { immediate = false } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);

  const isMounted = useRef(true);
  const fetchRef = useRef(fetchFunction);

  useEffect(() => {
    fetchRef.current = fetchFunction;
  }, [fetchFunction]);

  const execute = useCallback(async () => {

    setLoading(true);
    setError(null);

    try {

      const result = await fetchRef.current();

      if (isMounted.current) {
        setData(result);
      }

    } catch (err) {

      if (isMounted.current) {
        setError(err);
      }

    } finally {

      if (isMounted.current) {
        setLoading(false);
      }

    }

  }, []);

  useEffect(() => {

    isMounted.current = true;

    if (immediate) {
      execute();
    }

    return () => {
      isMounted.current = false;
    };

  }, [immediate, execute]);

  return {
    data,
    loading,
    error,
    execute
  };

}