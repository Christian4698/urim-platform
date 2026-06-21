# Messagerie des agents

## Agents
- Orchestrator
- Data Scout
- Data Auditor
- Temporal Guard
- Match Analyst
- Model Agent
- Calibration Agent
- Risk Guardian
- Explanation Agent
- Monitor Agent

## Messages
`DATA_REQUEST`, `DATA_OBSERVATION`, `DATA_CONFLICT`, `FEATURE_SNAPSHOT_READY`, `PREDICTION_PROPOSED`, `TEMPORAL_BLOCK`, `RISK_DECISION`, `EXPLANATION_READY`, `INCIDENT`, `AUDIT_RESULT`.

## Enveloppe
```json
{
  "message_id": "uuid",
  "correlation_id": "uuid",
  "causation_id": "uuid|null",
  "sender": "agent-name",
  "recipient": "agent-name|topic",
  "type": "DATA_REQUEST",
  "created_at": "ISO-8601",
  "expires_at": "ISO-8601|null",
  "schema_version": "1.0",
  "payload": {},
  "evidence_refs": [],
  "signature": "server-generated"
}
```

L’interface montre décisions, preuves, désaccords et blocages. Elle n’expose pas de chaîne de pensée privée.
