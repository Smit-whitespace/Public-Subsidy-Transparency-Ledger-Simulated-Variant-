import React from "react";

export default function BlockchainProofBadge({
  proofHash = null,
  proofId = null,
  verified = false,
  loading = false,
  error = null
}) {
  if (loading) {
    return <span className="proof-badge loading">Verifying on-chain…</span>;
  }

  if (error) {
    return <span className="proof-badge error">Proof verification failed</span>;
  }

  if (verified && proofId) {
    return (
      <span className="proof-badge verified">
        On-chain ✓ (ID: {proofId})
      </span>
    );
  }

  if (!verified && proofHash) {
    return <span className="proof-badge pending">Not anchored</span>;
  }

  return <span className="proof-badge none">No proof</span>;
}