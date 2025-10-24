# Data Contract

## 1. Purpose and Scope
This contract defines the obligations, guarantees, and conditions under which a data producer makes a data product available to data consumers. It covers schema and semantics, service levels, quality requirements, privacy and security controls, access and delivery, change management, retention, compliance, support, and termination. The contract applies to all assets and interfaces explicitly identified in Section 4 and Section 7.

## 2. Roles and Responsibilities
- **Data Producer**: Publishes and maintains the data product; ensures agreed quality, availability, and security; manages changes and deprecations; provides support.  
- **Data Consumer**: Uses the data in accordance with this contract; implements consumer-side controls (e.g., caching, retries); monitors usage limits; reports incidents.  
- **Stewardship & Governance**: Oversees metadata accuracy, policy alignment, and compliance; reviews changes that affect business meaning or regulatory posture.  
- **Security & Privacy**: Defines and audits access controls, encryption, masking, and privacy engineering practices.  
- **Platform/Operations**: Ensures platform reliability, observability tooling, and incident response processes.

## 3. Definitions
- **Data Product**: A curated, reusable collection of data and/or related assets made available through one or more interfaces.  
- **Dataset**: A concrete, queryable collection (e.g., table, view, file set, API resource).  
- **SLA**: Service Level Agreement for availability and delivery.  
- **SLO**: Service Level Objective for data quality metrics (freshness, completeness, etc.).  
- **Breaking Change**: A change that invalidates existing consumer integrations without action on their side (schema removals/renames, semantic shifts).  
- **Minor/Non-Breaking Change**: Additive fields, stricter validation that does not invalidate existing values, or performance improvements.

## 4. Data Product Overview
- **Description**: A curated, domain-agnostic data product intended for analytical, operational, and data-science use. It may contain tabular datasets, time-series, files, or API-derived resources.  
- **Intended Use**: Business analytics, reporting, ML feature sourcing, operational dashboards, and data exchange across teams.  
- **Out of Scope**: Real-time control loops and safety-critical actuation that require hard real-time guarantees beyond the SLA stated here.  
- **Dependencies (non-exhaustive)**: Upstream source systems, reference/master data, identity and access infrastructure, and platform services needed to deliver interfaces in Section 7.

## 5. Data Schema and Semantics
- **Schema Publication**: The authoritative schema is versioned and machine-readable (e.g., JSON Schema, OpenAPI, Avro, or DDL).  
- **Data Types**: Use stable, explicit types; avoid ambiguous encodings (e.g., timestamps are ISO-8601 with timezone or epoch seconds).  
- **Primary Keys & Uniqueness**: Each dataset declares keys and duplicate handling rules.  
- **Referential Rules**: Cross-dataset relationships are documented, including nullability and join cardinality.  
- **Semantic Clarity**: Each field includes a concise definition, units, valid ranges, and allowed enumerations where applicable.  
- **Backward Compatibility**: Additive fields are allowed; renames/removals are treated as breaking (see Section 12).

## 6. Data Quality Requirements (SLOs)
Quality is continuously measured and surfaced through scorecards. Targets below are default, domain-agnostic baselines.

| Metric | Description | Target |
|--------|--------------|--------|
| **Freshness** | New data visible within 24 hours of source availability (P95) | ≤ 24h |
| **Completeness** | Required fields populated per load window | ≥ 99.0% |
| **Accuracy/Validity** | Values meeting declared validation rules | ≥ 98.0% |
| **Consistency** | Referential integrity errors per window | ≤ 0.5% |
| **Load Timeliness** | Scheduled load completion on time | ≥ 95% |
| **Observability** | Quality metrics and assertions published | Continuous |

## 7. Access and Delivery
- **Interfaces**: SQL query endpoints, REST/GraphQL APIs, message topics/queues, or file/object delivery.  
- **Authentication & Authorization**: Strong authentication and least-privilege authorization (role- or attribute-based).  
- **Encryption**: TLS in transit and platform-native encryption at rest.  
- **Performance Envelope**:
  - Interactive queries: P95 ≤ 5s for typical filters and aggregations.  
  - Batch exports: Delivered within scheduled batch windows.  
- **Quotas & Fair Use**: The producer may rate-limit or throttle abusive workloads; consumers should implement backoff/retry logic.

## 8. Privacy, Security, and Sensitive Data Controls
- **Classification**: Each dataset carries a classification (e.g., Public, Internal, Confidential, Restricted).  
- **Minimization & Masking**: Sensitive data minimized, masked, tokenized, or anonymized as required.  
- **Access Reviews**: Periodic access recertification is mandatory.  
- **Auditability**: Access logs retained; lineage tracks data propagation.  
- **Regulatory Posture**: Processing aligns with applicable privacy and data-protection laws.

## 9. Service Levels (SLA)
- **Availability**: 99.5% monthly for read access; planned maintenance announced ≥ 72h in advance.  
- **Support Response**:
  - P1 (critical outage): initial response ≤ 2 business hours.  
  - P2 (material degradation): initial response ≤ 8 business hours.  
  - P3 (general queries): response ≤ 3 business days.  
- **Recovery Objectives**: RPO ≤ 24h; RTO ≤ 8h for critical incidents.

## 10. Lifecycle, Retention, and Archival
- **Retention**: Default retention is 24 months for primary datasets.  
- **Archival**: Older data may move to lower-cost storage with consistent schema.  
- **Deletion**: Deletion or anonymization performed per policy and lawful requests.  
- **Non-Production Data**: Synthetic or masked data only.

## 11. Observability, Monitoring, and Incident Management
- **Monitoring**: Automated checks for freshness, volume drift, schema drift, and failures.  
- **Alerting**: Alerts route to on-call operations by severity.  
- **Runbooks**: Standardized recovery and rollback procedures.  
- **Incident Reviews**: Root cause, timeline, and corrective actions documented.

## 12. Change Management and Versioning
- **Versioning**: Semantic Versioning (MAJOR.MINOR.PATCH).  
- **Non-Breaking Changes**: Additive or performance improvements.  
- **Breaking Changes**: Removals/renames; deprecation period ≥ 90 days.  
- **Communication**: Changes announced via release notes and migration guidance.

## 13. Lineage and Transformations
- **Provenance**: Lineage traces sources, transformations, and sinks.  
- **Transform Semantics**: Business rules, aggregations, and filters documented and version-controlled.  
- **Evidence**: Lineage views and transformation logic are reviewable for audits.

## 14. Usage Terms and Acceptable Use
- **Permitted Use**: Analytics, reporting, ML/AI, and operational decision support.  
- **Prohibited Use**: Illegal or policy-violating activities, re-identification, or control bypass.  
- **Attribution & Redistribution**: Must preserve metadata, classifications, and contract terms.  
- **Open/Shared Assets**: License terms documented (e.g., permissive data license).

## 15. Cost, Quotas, and Fair Usage
- **Cost Model**: May include metered compute, egress, or storage.  
- **Quotas**: Default concurrency limits protect platform stability.  
- **Consumer Responsibilities**: Efficient queries and responsible usage.

## 16. Acceptance and Fitness
- **Fitness for Use**: Data provided “as-is” under Sections 6 and 9.  
- **UAT/Certification**: Consumers may certify use cases against versioned snapshots.

## 17. Audit and Compliance
- **Evidence**: Lineage, logs, quality scorecards, and compliance mappings.  
- **Reviews**: Periodic governance and security assessments.

## 18. Term, Suspension, and Termination
- **Term**: Valid while data product is published and accessible.  
- **Suspension**: Possible for security threats or misuse.  
- **Termination/Deprecation**: Advance notice and withdrawal plan provided.

## 19. Communication Channels
- **Operational Notifications**: Status page and automated alerts.  
- **Change Announcements**: Release notes and deprecation notices.  
- **Support Requests**: Ticketing system or designated inbox.

## 20. Changelog
- **Release Notes**: Document schema and semantic changes per release.  
- **Archive**: Maintain history of prior versions for auditability.

---

### How to Use This Contract
- Publish alongside the data product’s catalog entry.  
- Keep schemas version-controlled and linked to Section 5.  
- Automate checks for SLOs in Sections 6 and 11.  
- Treat Section 12 (change management) as mandatory for consumer protection.
