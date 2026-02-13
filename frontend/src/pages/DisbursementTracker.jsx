import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";
import DisbursementChart from "../components/DisbursementChart";
import Loader from "../components/Loader";
import { fetchDisbursements } from "../api/disbursements";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";

export default function DisbursementTracker() {
  const { user, token, isAuthenticated } = useAuth();
  const [filters, setFilters] = useState({});

  const { data, loading, error, execute } = useFetch(
    () =>
      fetchDisbursements({
        subsidyId: filters.subsidyId || null,
        limit: 50,
        offset: 0,
        token
      }),
    { immediate: true }
  );

  useEffect(() => {
    if (isAuthenticated && token) {
      execute();
    }
  }, [filters, token, isAuthenticated, execute]);

  if (!isAuthenticated) {
    return (
      <div className="disbursement-tracker unauthorized">Access denied</div>
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
      render: (row) => (row.amount ? String(row.amount) : "N/A")
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
      <Navbar user={user} />
      <div className="disbursement-layout">
        <Sidebar user={user} />
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
            <DisbursementChart disbursements={disbursements} />
          </section>

          <section>
            <h2>Disbursement Records</h2>
            <DataTable columns={columns} data={disbursements} />
          </section>
        </main>
      </div>
    </div>
  );
}