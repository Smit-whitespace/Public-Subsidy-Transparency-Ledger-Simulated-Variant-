import React, { useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import DataTable from "../components/DataTable";
import DisbursementChart from "../components/DisbursementChart";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";
import SubsidyCard from "../components/SubsidyCard";
import BlockchainProofBadge from "../components/BlockchainProofBadge";

import { fetchSubsidyById } from "../services/subsidyService";
import { fetchDisbursements } from "../services/disbursementService";

import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";

export default function SubsidyDetails() {

  const { id } = useParams();
  const navigate = useNavigate();

  const { token, isAuthenticated } = useAuth();

  const subsidyId = id ? parseInt(id, 10) : null;

  const fetchSubsidy = useCallback(() => {

    if (!token || !subsidyId) {
      return Promise.resolve(null);
    }

    return fetchSubsidyById(subsidyId, token);

  }, [subsidyId, token]);

  const fetchSubsidyDisbursements = useCallback(() => {

    if (!token || !subsidyId) {
      return Promise.resolve([]);
    }

    return fetchDisbursements({
      subsidyId,
      limit: 50,
      offset: 0,
      token
    });

  }, [subsidyId, token]);

  const {
    data: subsidyData,
    loading: subsidyLoading,
    error: subsidyError,
    execute: loadSubsidy
  } = useFetch(fetchSubsidy, { immediate: false });

  const {
    data: disbursementData,
    loading: disbursementsLoading,
    error: disbursementsError,
    execute: loadDisbursements
  } = useFetch(fetchSubsidyDisbursements, { immediate: false });

  useEffect(() => {

    if (isAuthenticated && token && subsidyId) {
      loadSubsidy();
      loadDisbursements();
    }

  }, [isAuthenticated, token, subsidyId, loadSubsidy, loadDisbursements]);

  if (!isAuthenticated) {
    return (
      <div className="subsidy-details unauthorized">
        Access denied
      </div>
    );
  }

  if (!subsidyId || isNaN(subsidyId)) {
    return (
      <div className="subsidy-details error">
        Invalid subsidy ID
      </div>
    );
  }

  if (subsidyLoading || disbursementsLoading) {
    return <Loader message="Loading subsidy details..." />;
  }

  if (subsidyError || disbursementsError) {
    return (
      <div className="subsidy-details error">
        Failed to load subsidy
      </div>
    );
  }

  const subsidy = subsidyData || {};
  const disbursements = disbursementData?.data || disbursementData || [];
  const audits = subsidy?.audits || [];

  function handleDisbursementClick(row) {
    if (!row?.id) return;
    navigate("/disbursements");
  }

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
      key: "status",
      label: "Status",
      render: (row) => row.status || "N/A"
    }
  ];

  return (
    <div className="subsidy-details">

      <Navbar />

      <div className="subsidy-layout">

        <Sidebar />

        <main className="subsidy-content">

          <h1>Subsidy Details</h1>

          <section>

            <h2>Subsidy Summary</h2>

            <SubsidyCard
              subsidy={subsidy}
              onClick={() => {}}
            />

          </section>

          {(subsidy?.proofHash || subsidy?.proofId) && (

            <section>

              <h2>Blockchain Proof</h2>

              <BlockchainProofBadge
                proofHash={subsidy.proofHash}
                proofId={subsidy.proofId}
                verified={subsidy.proofVerified}
              />

            </section>

          )}

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
              onRowClick={handleDisbursementClick}
            />

          </section>

          <section>

            <h2>Audit Timeline</h2>

            <AuditTimeline
              audits={audits}
            />

          </section>

        </main>

      </div>

    </div>
  );
}