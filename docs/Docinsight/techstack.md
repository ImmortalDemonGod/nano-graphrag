DocInsight: Tech Stack Decisions

Core Architecture

1. Document Processing & Analysis

Primary Document Processing: Docling
	•	Multi-format support: PDF, DOCX, PPTX, XLSX, HTML, Markdown
	•	Advanced layout analysis and table recognition
	•	Citation handling and OCR support
	•	Easy RAG integration

Document Acquisition & Research:
	•	PaperScraper for academic sources
	•	Support for PubMed, arXiv, bioRxiv, medRxiv
	•	Automated PDF downloading
	•	Metadata extraction
	•	GPT Researcher for web research
	•	Comprehensive research across 20+ sources
	•	Background processing support
	•	Knowledge gap filling

Core Search & Embedding:
	•	NanoGraphRAG for local document search
	•	Built-in nano-vectordb for vector operations
	•	networkx for graph database
	•	Local disk storage for key-value data
	•	potion-base-8M for embeddings
	•	7.6M parameters for efficient resource usage
	•	500x faster inference than transformers
	•	Proven performance (50.54% avg score)

2. Frontend & Web Framework

Choice: FastHTML
Rationale:
	•	Python-based full-stack development
	•	Built-in HTMX for dynamic updates
	•	Integrated authentication and database features
	•	Perfect fit for MVP timeline (June 1st, 2025)

3. Database Architecture

MVP Phase:
	•	NanoGraphRAG’s built-in components:
	•	nano-vectordb for vector operations
	•	networkx for graph database
	•	Disk storage for key-value data
	•	SQLite for:
	•	User management and authentication
	•	Session tracking
	•	Document metadata
	•	Background task status

Post-MVP Migration:
	•	Supabase as primary database:
	•	PostgreSQL with pgvector support
	•	Built-in authentication system
	•	Real-time capabilities
	•	Enhanced monitoring
	•	Improved concurrency handling
	•	Retain NanoGraphRAG components for specialized operations

4. Observability Stack

MVP Phase:
	•	OpenTelemetry (Core Instrumentation)
	•	Primary instrumentation framework
	•	Language-agnostic tracing across Python stack
	•	Integration with NanoGraphRAG
	•	Automatic instrumentation for dependencies
	•	Prometheus (Metrics & Alerts)
	•	Core metrics collection and storage
	•	Integration with OpenTelemetry via collector
	•	Alert management
	•	Performance metrics monitoring
	•	OpenTelemetry Collector
	•	Bridges OpenTelemetry and Prometheus
	•	Handles data transformation
	•	Routes telemetry data
	•	Provides buffering and retry capabilities

Post-MVP Phase:
	•	Maintain OpenTelemetry instrumentation
	•	Expand Prometheus metrics
	•	Leverage Supabase monitoring features:
	•	Enhanced real-time analytics
	•	Improved concurrent user monitoring
	•	Better audit logging
	•	Integrated authentication monitoring

5. Cache & Queue Architecture

Caching Layer: Redis
	•	Session storage
	•	Query result caching
	•	Rate limiting
	•	Temporary data storage
	•	Configuration:

REDIS_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 0,
    'CACHE_DEFAULT_TIMEOUT': 300
}



Task Queue: Celery + Redis
	•	Background task processing
	•	Async document processing
	•	Scheduled jobs
	•	Configuration:

CELERY_CONFIG = {
    'broker_url': 'redis://localhost:6379/1',
    'result_backend': 'redis://localhost:6379/2',
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json']
}



Processing Pipelines

1. Document Processing

from docling.document_converter import DocumentConverter
from paperscraper.pdf import save_pdf_from_dump

# Document acquisition & processing
papers = save_pdf_from_dump('search_results.jsonl')
converter = DocumentConverter()
doc_results = converter.convert_all(papers)

2. Search & Analysis

# Hybrid search approach
local_results = nano_rag.search(query)
web_results = GPTResearcher(query=query).conduct_research()
final_results = synthesize_results(local_results, web_results)

3. Background Processing
	•	Topic monitoring and new paper detection
	•	Automatic document processing through Docling
	•	Vector store updates
	•	Research summaries via GPT Researcher

Performance Requirements

Response Times
	•	Simple queries: < 60 seconds
	•	Local search: < 2 seconds
	•	Document processing: < 5 seconds per document
	•	Vector operations: < 100ms
	•	Background updates: Every 10 minutes
	•	Cache response time: < 10ms

Quality Targets
	•	Search accuracy: > 95%
	•	Citation accuracy: > 98%
	•	System uptime: > 99.9%
	•	User satisfaction: > 4.5/5
	•	Concurrent users: 50

Implementation Phases

1. MVP Database & Monitoring Layer (By June 1st, 2025)
	•	SQLite + NanoGraphRAG implementation
	•	OpenTelemetry + Prometheus monitoring
	•	Basic user management
	•	Document metadata storage
	•	Vector operations via nano-vectordb

2. Post-MVP Migration
	•	Transition user management to Supabase
	•	Enhanced monitoring capabilities
	•	Improved concurrent user support
	•	Retain NanoGraphRAG for specialized operations
	•	Integration with existing authentication system

3. Authentication System
	•	MVP: MAC address verification via SQLite
	•	Post-MVP: Supabase authentication system
	•	Session management
	•	User authentication

4. Deployment Infrastructure
	•	Load balancing for 50 users
	•	Background processing
	•	System monitoring
	•	Resource scaling
	•	CI/CD Platform: GitHub Actions

Testing Infrastructure

Core Testing Framework: pytest + xdoctest + hypothesis
	•	Primary test runner: pytest
	•	Doctest support: pytest-xdoctest
	•	Property-based testing: hypothesis

Required Plugins:
	1.	Core Infrastructure:

pytest-xdoctest      # Docstring testing
pytest-asyncio       # Async test support
pytest-cov           # Coverage reporting
pytest-timeout       # Test performance requirements 
pytest-randomly      # Test isolation
pytest-hypothesis    # Property-based testing


	2.	Database/Cache Testing:

pytest-sqlite        # SQLite testing (MVP)
pytest-redis         # Redis integration testing
pytest-mock          # Mocking/stubbing
pytest-celery        # Celery task testing
pytest-env           # Environment management


	3.	Vector/RAG Testing:

pytest-benchmark     # Performance testing
pytest-recording     # API interaction recording
pytest-unordered     # Unordered collection comparison


	4.	Monitoring/Reporting:

pytest-html           # HTML reports
pytest-reportlog      # Detailed logs
pytest-sugar          # Better CLI output
pytest-resource-usage # Resource tracking



Test Organization:
	•	Unit tests in tests/unit/
	•	Integration tests in tests/integration/
	•	Performance tests in tests/perf/
	•	Property tests in tests/properties/
	•	Doctests directly in docstrings

Testing Standards:
	1.	All new code requires:
	•	Comprehensive docstring with usage examples
	•	Unit tests
	•	Integration tests for database/external interactions
	•	Property-based tests for complex logic
	2.	Performance Requirements:
	•	Vector operations: < 100ms
	•	Simple queries: < 60 seconds
	•	Document processing: < 5 seconds per document
	•	Background updates: Every 10 minutes
	•	Cache response time: < 10ms
	3.	Coverage Requirements:
	•	Minimum 90% coverage for new code
	•	Maintained through combination of unit tests and doctests

Test Execution:

# Development 
pytest --xdoctest  

# CI Pipeline
pytest --xdoctest --cov --hypothesis-profile=ci --benchmark-only

# Property Testing
pytest --hypothesis-show-statistics

Updates & History
	•	Dec 14, 2024:
	•	Added Docling as document processing engine
	•	Integrated NanoGraphRAG, GPT Researcher, and PaperScraper
	•	Selected FastHTML and potion-base-8M
	•	Finalized database architecture with SQLite + NanoGraphRAG for MVP, Supabase for post-MVP
	•	Added OpenTelemetry + Prometheus observability stack
	•	Added Redis caching and Celery task queue architecture
	•	Enhanced testing infrastructure with hypothesis

Summary

This document outlines the comprehensive tech stack decisions for DocInsight, ensuring a robust and scalable architecture. Key components include advanced document processing with Docling, efficient search and embedding using NanoGraphRAG and potion-base-8M, a Python-based frontend with FastHTML, and a scalable database architecture transitioning from SQLite to Supabase. Additionally, the implementation of an observability stack with OpenTelemetry and Prometheus, a caching and queue system using Redis and Celery, and a thorough testing infrastructure with pytest and related plugins ensures high performance and reliability. The deployment strategy leverages GitHub Actions for CI/CD, aligning with the project’s timeline and quality targets.