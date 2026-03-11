import React from "react";

export default function BlockchainProof({ proof }) {

  if (!proof) {
    return <p>No proof recorded</p>;
  }

  return (
    <div className="blockchain-proof">

      <h4>Blockchain Proof</h4>

      <div>
        <strong>Hash:</strong> {proof.hash}
      </div>

      <div>
        <strong>Timestamp:</strong>{" "}
        {new Date(proof.created_at).toLocaleString()}
      </div>

      <div>
        <strong>Network:</strong> {proof.network}
      </div>

    </div>
  );
}