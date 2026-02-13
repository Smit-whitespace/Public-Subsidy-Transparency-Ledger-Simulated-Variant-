import React from "react";
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

export default function SubsidyDetails({ subsidyId = null }) {
  const { user, token, isAuthenticated } = useAuth();

  const {
    data: subsidyData,
    loading: subsidyLoading,
    error: subsidyError
  } = useFetch(
    () => (subsidyId ? fetchSubsidyById(subsidyId, token) : null),
    {
      immediate: isAuthenticated && subsidyId
    }
  );

  const {
    data: disbursementData,
    loading: disbursementsLoading,
    error: disbursementsError
  } = useFetch(
    () =>
      subsidyId
        ? fetchDisbursements({ subsidyId, limit: 50, offset: 0, token })
        : null,
    {
      immediate: isAuthenticated && subsidyId
    }
  );

  if (!isAuthenticated || !subsidyId) {
    return <div className="subsidy-details error">Invalid access</div>;
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
            <DataTable columns={columns} data={disbursements} />
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