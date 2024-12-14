DocInsight Unified System Architecture

Introduction

DocInsight is a research assistance platform designed to help researchers ingest documents, derive insights, and retrieve contextually relevant answers enriched by a knowledge graph and embeddings. The architecture aims to support scalability, reliability, security, maintainability, and comprehensive observability while mapping directly to the project’s user stories and specifications.

Architectural Goals
	1.	Scalability: Support growing datasets, user bases, and query complexity without performance degradation.
	2.	Reliability & Availability: Maintain high uptime, fault-tolerance, and resilience under varying loads.
	3.	Security & Compliance: Enforce robust authentication, authorization, encryption, and auditing for data integrity and privacy.
	4.	Maintainability & Extensibility: Employ modular, microservices-inspired design and clear API contracts, enabling rapid feature evolution.
	5.	Observability & Operational Excellence: Offer comprehensive logging, metrics, tracing, and alerting for quick diagnosis and continuous optimization.
	6.	Research Quality & Accuracy: Integrate Retrieval-Augmented Generation (RAG) principles to provide accurate, verifiable, and source-cited answers.

Core Architectural Principles
	•	Layered Microservices: Divide the system into layers (Document Processing, Query Processing, Knowledge Management, Security & Access, Observability & Management) to isolate concerns and simplify scaling.
	•	Retrieval-Augmented Generation: Use LLM-based embeddings and a knowledge graph to enrich query results, ensuring answers are contextual and sourced.
	•	Multi-Store Strategy: Combine a vector database for embeddings, a relational/document store for metadata and configurations, a knowledge graph for semantic relationships, and a caching layer for performance.
	•	Security by Design: Integrate OAuth 2.0/JWT, role-based access control, MAC whitelisting, encryption, and detailed auditing from inception.
	•	Comprehensive Observability: Implement logging, metrics, traces, dashboards, and alerting to support proactive operations and continuous improvement.

Mapping to User Stories and Specifications

The architecture directly aligns with the defined user stories and acceptance criteria:
	•	Document Analysis (DOC-001, DOC-002): Document Processing Layer supports multi-format ingestion, quick indexing, and metadata extraction.
	•	Search & Analysis (SEARCH-001, SEARCH-002, SEARCH-003): Query Processing Layer integrates NLP-driven query understanding, vector searches, and citation support. Background processing handles ongoing research queries.
	•	Knowledge Organization (KNOW-001, KNOW-002): Knowledge Management Layer uses a knowledge graph and research context tracking to categorize results and maintain a knowledge base.
	•	System Management (SYS-001): Observability & Management Layer provides dashboards, metrics, and alerting for administrators.
	•	Security Management (SEC-001, SEC-002, SEC-003, SEC-004): Security & Access Layer enforces authentication, authorization, auditing, encryption, and MAC-based device verification.
	•	Future Enhancements (COLLAB, QA, INTEL): The modular design enables adding collaboration features, quality checks, and research intelligence analytics without significant redesign.

Layers and Responsibilities

1. Document Processing Layer
	•	Document Ingestion Service: Handles uploads (PDF, DOCX, TXT, MD), validates formats, extracts metadata.
	•	Content Chunking & Embedding Service: Breaks documents into chunks, generates embeddings, stores them in the vector database.
	•	Index Maintenance Service: Updates indexing structures and supports background reprocessing for coverage improvement.

Data Flow:
Document → Ingestion (parse, metadata) → Chunking/Embedding (embeddings to Vector DB, metadata to Relational DB) → Indexed and ready for queries.

2. Query Processing Layer
	•	Query Understanding Service: Uses NLP to parse queries, identify intent, and extract entities.
	•	Search Orchestration Service: Directs queries to vector searches, knowledge graphs, and relational stores; aggregates and ranks results.
	•	Background Processing Service: Handles long-running queries, scheduled indexing updates, and coverage expansions.

Data Flow:
User Query → Query Understanding (NLP) → Search Orchestration (vector DB similarity, knowledge graph lookups) → Aggregation and LLM-based synthesis → Results with citations returned to user.

3. Knowledge Management Layer
	•	Knowledge Graph Service: Maintains entities, relationships, and semantic context for richer, more contextual answers.
	•	Research Context Service: Tracks ongoing research sessions, identifies topic clusters, and suggests additional documents.

Data Flow:
Document/Entity Ingestion → Knowledge Graph Update → Contextualization of Search Results → Enhanced answers with semantic links.

4. Security & Access Layer
	•	Authentication & Authorization Service: Uses OAuth 2.0/JWT, role-based access control, and MAC whitelisting to control system access.
	•	Audit & Compliance Service: Logs every access attempt, user action, and administrative event, maintaining audit trails and compliance records.

Data Flow:
User Request → Auth Check (credentials, MAC, roles) → Allowed Access → Requests processed further; all actions logged.

5. Observability & Management Layer
	•	Logging & Monitoring Service: Centralized logs, metrics (Prometheus), and dashboards (Grafana).
	•	Alert & Incident Response Service: Sets SLOs, triggers alerts, and integrates with on-call systems.
	•	Performance & Capacity Planning: Uses distributed tracing (OpenTelemetry) and metrics to identify bottlenecks and guide scaling.

Data Flow:
Services Emit Logs/Metrics/Traces → Central Aggregation → Dashboards, Alerts, and Capacity Adjustments.

Data Stores
	•	Vector Database (LanceDB/Nano-VectorDB): For embeddings and semantic similarity searches.
	•	Relational/Document Store: For user profiles, system configuration, indexing states.
	•	Knowledge Graph Database: For entities, relationships, and semantic links.
	•	Caching Layer (Redis): For frequently accessed queries and computed results, reducing latency.

Security & Compliance
	•	Authentication (OAuth 2.0) and Authorization (RBAC) at the gateway.
	•	MAC address whitelisting for device-based access control.
	•	Encryption at rest and in transit (TLS, disk-level encryption).
	•	Comprehensive auditing for compliance and traceability.

Observability & Operations
	•	Metrics (Prometheus) and dashboards (Grafana) for real-time performance monitoring.
	•	Distributed tracing (OpenTelemetry) to pinpoint bottlenecks in query or ingestion flows.
	•	Alerting and on-call integration for rapid incident response.
	•	CI/CD pipelines (Jenkins, GitHub Actions, etc.) for automated testing, deployment, and integration.

Scalability & Evolution
	•	Horizontal scaling of stateless services behind load balancers.
	•	Partitioning and sharding for vector and knowledge graph data as datasets grow.
	•	Auto-scaling policies triggered by resource usage, latency, and coverage thresholds.
	•	Modular architecture allows adding collaboration features, QA checks, and analytics in future phases without major refactoring.

Testing & Quality Assurance
	•	Unit, integration, and end-to-end tests aligned with user stories.
	•	Performance, load, and security testing integrated into CI/CD.
	•	Continuous feedback loop from observability data to refine embeddings, improve coverage, and enhance citation accuracy.

Conclusion

This unified system architecture leverages the best concepts from previous drafts, aligns tightly with user stories, and provides a clear, actionable blueprint for developers. It outlines layered services, data stores, security measures, and observability practices necessary to build a scalable, secure, and user-focused research assistance platform.

Finalized High-Level Architectural Diagram

Below is a Mermaid code snippet you can use to visualize the architecture. Paste this into the Mermaid Live Editor or any Mermaid-compatible tool to generate the diagram.

---
config:
  theme: neo-dark
  layout: fixed
  look: neo
---
flowchart TD
 subgraph Clients["Clients"]
        R["Researcher"]
        A["System Administrator"]
  end
 subgraph Security_Access_Layer["Security_Access_Layer"]
        AA["Auth & AuthZ Service"]
        AC["Audit & Compliance Service"]
  end
 subgraph Query_Processing_Layer["Query_Processing_Layer"]
        QU["Query Understanding Service"]
        SO["Search Orchestration Service"]
        BP["Background Processing Service"]
  end
 subgraph Document_Processing_Layer["Document_Processing_Layer"]
        DI["Document Ingestion Service"]
        CE["Content Chunking and Embedding Service"]
        IM["Index Maintenance Service"]
  end
 subgraph Knowledge_Management_Layer["Knowledge_Management_Layer"]
        KG["Knowledge Graph Service"]
        RC["Research Context Service"]
  end
 subgraph Observability_Management_Layer["Observability_Management_Layer"]
        LM["Logging & Monitoring Service"]
        AI["Alert & Incident Response Service"]
        PC["Performance & Capacity Planning"]
  end
 subgraph Data_Stores["Data_Stores"]
        VDB["Vector DB - LanceDB/Nano-VectorDB"]
        RDB["Relational/Document Store"]
        KGD["Knowledge Graph DB"]
        Cache["Cache Layer - Redis"]
  end
 subgraph External_Systems["External_Systems"]
        MB["Message Bus - Kafka/NATS"]
        CICD["CI/CD Pipeline"]
  end
    R -- Uploads Docs, Queries --> AA
    A -- Admin Config, Monitoring --> AA
    AA -- Auth Logs --> AC
    AA -- Authenticated Requests --> QU
    QU --> SO & LM
    SO --> BP & KG & VDB & RDB & Cache & LM
    BP --> IM & LM & MB
    DI --> CE & RDB & LM
    KG --> RC & KGD & KGD & LM
    CE --> VDB & LM
    IM --> RDB & LM
    AA --> LM
    LM --> AI & PC & MB
    AI -- "Alerts On-Call" --> A
    PC -- Scaling Decisions --> RDB & VDB & KGD & Cache
    SO -- Answers & Citations --> QU
    QU -- Processed Answer --> R
    AI --> MB
    CICD --> DI & QU & SO & KG & AA & LM
    classDef layer fill:#f9f,stroke:#333,stroke-width:2px


How to Use:
	•	Open the Mermaid Live Editor and paste the code above.
	•	Adjust styling, positioning, or labels as needed.
	•	The diagram shows how clients interact via Security & Access, flow into Query and Document layers, leverage the Knowledge Management layer, and rely on Data Stores. The Observability & Management layer ties it all together, ensuring insights for operations and scalability.

