import React, { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import DataTable from "../components/DataTable";
import DisbursementChart from "../components/DisbursementChart";
import AuditTimeline from "../components/AuditTimeline";
import Loader from "../components/Loader";
import SubsidyCard from "../components/SubsidyCard";
import BlockchainProofBadge from "../components/BlockchainProofBadge";
import { fetchSubsidyById } from "../api/subsidies";
import { fetchDisbursements } from "../api/disbursements";
import useAuth from "../hooks/useAuth";
import useFetch from "../hooks/useFetch";

export default function SubsidyDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, token, isAuthenticated } = useAuth();

  const subsidyId = id ? parseInt(id, 10) : null;

  const {
    data: subsidyData,
    loading: subsidyLoading,
    error: subsidyError,
    execute: loadSubsidy
  } = useFetch(
    () => fetchSubsidyById(subsidyId, token),
    { immediate: false }
  );

  const {
    data: disbursementData,
    loading: disbursementsLoading,
    error: disbursementsError,
    execute: loadDisbursements
  } = useFetch(
    () =>
      fetchDisbursements({
        subsidyId,
        limit: 50,
        offset: 0,
        token
      }),
    { immediate: false }
  );

  useEffect(() => {
    if (isAuthenticated && token && subsidyId) {
      loadSubsidy();
      loadDisbursements();
    }
  }, [isAuthenticated, token, subsidyId, loadSubsidy, loadDisbursements]);

  if (!isAuthenticated) {
    return <div className="subsidy-details unauthorized">Access denied</div>;
  }

  if (!subsidyId || isNaN(subsidyId)) {
    return <div className="subsidy-details error">Invalid subsidy ID</div>;
  }

  if (subsidyLoading || disbursementsLoading) {
    return <Loader message="Loading subsidy details..." />;
  }

  if (subsidyError || disbursementsError) {
    return <div className="subsidy-details error">Failed to load subsidy</div>;
  }

  const subsidy = subsidyData || {};
  const disbursements = disbursementData?.data || disbursementData || [];
  const audits = subsidy.audits || [];

  function handleDisbursementClick(row) {
    if (!row?.id) return;
    navigate(`/disbursements`);
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
      <Navbar user={user} />
      <div className="subsidy-layout">
        <Sidebar user={user} />
        <main className="subsidy-content">
          <h1>Subsidy Details</h1>

          <section>
            <h2>Subsidy Summary</h2>
            <SubsidyCard subsidy={subsidy} onClick={() => {}} />
          </section>

          {(subsidy.proofHash || subsidy.proofId) && (
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
            <DisbursementChart disbursements={disbursements} />
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
            <AuditTimeline audits={audits} />
          </section>
        </main>
      </div>
    </div>
  );
}
