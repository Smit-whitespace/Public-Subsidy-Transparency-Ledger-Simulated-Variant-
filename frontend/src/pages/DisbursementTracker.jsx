import React, { useState, useEffect, useCallback } from "react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";
import DisbursementChart from "../components/DisbursementChart";
import Loader from "../components/Loader";

import { fetchDisbursements } from "../services/disbursementService";
import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";
import useDebounce from "../hooks/useDebounce";

export default function DisbursementTracker() {

  const { token, isAuthenticated } = useAuth();

  const [filters, setFilters] = useState({});
  const [debouncedFilters, setDebouncedFilters] = useState({});

  // Debounce filter changes to avoid instant API calls
  const debouncedSubsidyId = useDebounce(filters.subsidyId, 500);

  useEffect(() => {
    setDebouncedFilters({
      subsidyId: debouncedSubsidyId
    });
  }, [debouncedSubsidyId]);

  const fetchDisbursementData = useCallback(() => {

    if (!token) {
      return Promise.resolve([]);
    }

    return fetchDisbursements({
      subsidyId: debouncedFilters.subsidyId || null,
      limit: 50,
      offset: 0,
      token
    });

  }, [debouncedFilters, token]);

  const {
    data,
    loading,
    error,
    execute
  } = useFetch(fetchDisbursementData, { immediate: true });

  useEffect(() => {

    if (isAuthenticated && token) {
      execute();
    }

  }, [debouncedFilters, token, isAuthenticated, execute]);

  if (!isAuthenticated) {
    return (
      <div className="disbursement-tracker unauthorized">
        Access denied
      </div>
    );
  }

  if (loading) {
    return <Loader message="Loading disbursements..." />;
  }

  if (error) {
    return (
      <div className="disbursement-tracker error">
        Failed to load disbursements
      </div>
    );
  }

  const disbursements = data?.data || data || [];

  const filterSchema = [
    {
      key: "subsidyId",
      label: "Subsidy ID",
      type: "text"
    }
  ];

  const columns = [
    {
      key: "id",
      label: "ID",
      render: (row) => row.id || "N/A"
    },
    {
      key: "amount",
      label: "Amount",
      render: (row) => row.amount ? String(row.amount) : "N/A"
    },
    {
      key: "date",
      label: "Date",
      render: (row) => {
        try {
          return new Date(row.date).toLocaleDateString();
        } catch (_) {
          return row.date || "N/A";
        }
      }
    },
    {
      key: "subsidy_id",
      label: "Subsidy ID",
      render: (row) => row.subsidy_id || "N/A"
    },
    {
      key: "status",
      label: "Status",
      render: (row) => row.status || "N/A"
    }
  ];

  function handleFilterChange(updatedFilters) {
    setFilters(updatedFilters);
  }

  function handleFilterReset() {
    setFilters({});
  }

  return (
    <div className="disbursement-tracker">

      <Navbar />

      <div className="disbursement-layout">

        <Sidebar />

        <main className="disbursement-content">

          <h1>Disbursement Tracker</h1>
          <p>Track subsidy disbursements over time</p>

          <section>

            <FilterPanel
              filters={filters}
              schema={filterSchema}
              onChange={handleFilterChange}
              onReset={handleFilterReset}
            />

          </section>

          <section>

            <h2>Disbursement Timeline</h2>

            <DisbursementChart
              disbursements={disbursements}
            />

          </section>

          <section>

            <h2>Disbursement Records</h2>

            <DataTable
              columns={columns}
              data={disbursements}
            />

          </section>

        </main>

      </div>

    </div>
  );
}