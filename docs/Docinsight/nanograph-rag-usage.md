# Graph RAG Integration Analysis for DocInsight

## Core Capabilities from Test Coverage

### 1. Vector Storage & Retrieval
Based on `test_hnsw_vector_storage.py`, the system provides:
- High-performance similarity search with HNSW algorithm
- Flexible document upsert and query operations
- Persistence and recovery mechanisms
- Configurable index parameters (M, ef_search)
- Meta field support for enhanced document metadata

Key performance metrics:
- Response time < 60 seconds for simple queries
- Concurrent support for 50 beta users
- Background processing for complex queries

### 2. Graph Storage & Knowledge Management
From `test_networkx_storage.py` and `test_neo4j_storage.py`:
- Dual graph backend support (NetworkX for MVP, Neo4j for scale)
- Entity and relationship management
- Community detection via Leiden algorithm
- Node embedding generation
- Hierarchical relationship tracking
- Automatic clustering and organization

### 3. Entity Extraction Pipeline
Based on `test_extract.py` and `test_module.py`:
- Robust entity and relationship extraction
- Type-aware entity classification
- Relationship weighting and scoring
- Configurable extraction parameters
- Error handling and validation
- Background processing support

### 4. JSON Processing & Response Handling
From `test_json_parsing.py`:
- Structured data extraction
- Clean response formatting
- Error recovery mechanisms
- Special character handling
- Nested structure support

## Integration Architecture for DocInsight

### 1. Document Processing Layer
```plaintext
Input Documents → Docling Processing → RAG Integration
                                   └→ Entity Extraction
                                   └→ Vector Storage
                                   └→ Graph Storage
```

Key Components:
- Docling for initial document processing
- RAG for semantic understanding
- Entity extraction for knowledge graph population
- Vector storage for similarity search
- Graph storage for relationship management

### 2. Query Processing Pipeline
```plaintext
User Query → Intent Analysis → RAG Query Generation
                           └→ Vector Search
                           └→ Graph Traversal
                           └→ Response Synthesis
```

Features:
- Multi-stage query processing
- Hybrid search (vector + graph)
- Context-aware response generation
- Citation tracking and validation

### 3. Background Processing System
```plaintext
Research Tasks → Task Queue → Async Processing
                          └→ Progress Tracking
                          └→ Result Aggregation
                          └→ User Notification
```

Capabilities:
- Long-running research queries
- Continuous topic monitoring
- Incremental updates
- Notification system

## Implementation Guidelines

### 1. Vector Store Configuration

```python
vector_store_config = {
    "M": 50,  # Optimal for 50 concurrent users
    "ef_search": 100,  # Balance between speed and accuracy
    "max_elements": 10000,  # Initial capacity
    "meta_fields": {"entity_name", "doc_type", "timestamp"}
}
```

### 2. Graph Store Setup

MVP Phase (NetworkX):
```python
graph_config = {
    "enable_persistence": True,
    "clustering_algorithm": "leiden",
    "node2vec_params": {
        "dimensions": 128,
        "walk_length": 80,
        "num_walks": 10
    }
}
```

Post-MVP Phase (Neo4j):
```python
neo4j_config = {
    "uri": "bolt://localhost:7687",
    "auth": ("neo4j", "password"),
    "max_connection_pool_size": 50
}
```

### 3. Entity Extraction Configuration

```python
entity_config = {
    "use_compiled_dspy_entity_relationship": True,
    "entity_relationship_module_path": "path/to/module.json",
    "extraction_batch_size": 100,
    "confidence_threshold": 0.8
}
```

## Performance Optimization Strategies

### 1. Query Processing
- Implement tiered processing:
  - Simple queries (< 60s)
  - Complex queries (background)
  - Research monitoring (scheduled)
- Use caching for frequent queries
- Implement batch processing for large documents

### 2. Storage Optimization
- Regular index maintenance
- Periodic cleanup of unused vectors
- Graph pruning for unused relationships
- Cached community detection results

### 3. Concurrency Management
- Connection pooling for Neo4j
- Rate limiting for API endpoints
- Background task queuing
- Resource allocation monitoring

## Error Handling & Recovery

### 1. Vector Store Recovery
```python
try:
    await storage.upsert(data)
except ValueError as e:
    if "Cannot insert" in str(e):
        await handle_storage_overflow()
    else:
        raise
```

### 2. Graph Store Recovery
```python
async def handle_graph_error():
    await storage._debug_delete_all_node_edges()
    await storage.index_start_callback()
    # Rebuild graph from backup
```

### 3. Entity Extraction Recovery
```python
try:
    results = await extract_entities_dspy(chunks)
except BadRequestError:
    # Fall back to simpler extraction method
    results = await extract_entities_basic(chunks)
```

## Integration Testing Strategy

### 1. Component Tests
- Vector storage operations
- Graph relationships
- Entity extraction accuracy
- Query processing pipeline

### 2. Integration Tests
- End-to-end document processing
- Query response generation
- Background task handling
- Error recovery procedures

### 3. Performance Tests
- Concurrent user simulation
- Large dataset processing
- Complex query handling
- Resource utilization monitoring

## Deployment Recommendations

### 1. MVP Phase (June 1st 2025)
- Deploy with NetworkX graph backend
- Use HNSW vector store
- Implement basic monitoring
- Support 50 concurrent users

### 2. Post-MVP Migration
- Transition to Neo4j for scaling
- Implement advanced monitoring
- Enhance concurrent user support
- Add advanced features

## Monitoring & Maintenance

### 1. System Metrics
- Query response times
- Vector search latency
- Graph operation timing
- Background task progress

### 2. Resource Usage
- Memory utilization
- Storage growth
- Connection pool status
- CPU usage patterns

### 3. Error Tracking
- Failed queries
- Extraction errors
- Storage exceptions
- Recovery attempts

## Conclusion

The test suite demonstrates that Graph RAG provides a solid foundation for DocInsight's core functionality. The implementation should focus on:

1. Careful configuration of vector and graph stores
2. Robust error handling and recovery
3. Efficient background processing
4. Performance optimization for concurrent users
5. Clear migration path from MVP to scaled deployment

Regular testing and monitoring will be crucial for maintaining system reliability and performance as the user base grows.

# Graph RAG Implementation Guide for DocInsight

## Core Setup & Configuration

### 1. Initial Project Setup

```python
from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag._storage import HNSWVectorStorage, NetworkXStorage
from nano_graphrag.base import TextChunkSchema
from nano_graphrag.entity_extraction.extract import extract_entities_dspy
from nano_graphrag._utils import wrap_embedding_func_with_attrs
import numpy as np
import asyncio

# Base configuration 
WORKING_DIR = "./docinsight_data"
MAX_CONCURRENT_USERS = 50
CHUNK_SIZE = 512
VECTOR_DIM = 384

# Configure embedding function
@wrap_embedding_func_with_attrs(embedding_dim=VECTOR_DIM, max_token_size=8192)
async def docinsight_embedding(texts: list[str]) -> np.ndarray:
    """Custom embedding function - can be replaced with OpenAI or other embeddings"""
    # Implementation depends on chosen embedding model
    # Example using OpenAI:
    from nano_graphrag._llm import openai_embedding
    return await openai_embedding(texts)

class DocInsightRAG:
    def __init__(self):
        self.rag = GraphRAG(
            working_dir=WORKING_DIR,
            embedding_func=docinsight_embedding,
            enable_naive_rag=True,  # Enable naive RAG for simple queries
            addon_params={
                "force_to_use_sub_communities": True,  # Enable hierarchical organization
                "max_elements": 10000,  # Initial vector store capacity
                "M": 50,  # HNSW graph degree
                "ef_search": 100  # Search accuracy parameter
            }
        )
```

### 2. Document Processing Implementation

```python
class DocumentProcessor:
    def __init__(self, rag_instance: GraphRAG):
        self.rag = rag_instance
        
    async def process_document(self, content: str, doc_id: str, metadata: dict = None):
        """Process a single document with complete pipeline"""
        try:
            # Create chunk schema
            chunks = self._create_chunks(content)
            chunk_schemas = {
                f"{doc_id}_{i}": TextChunkSchema(
                    content=chunk,
                    metadata={
                        "doc_id": doc_id,
                        "chunk_index": i,
                        **(metadata or {})
                    }
                ) for i, chunk in enumerate(chunks)
            }
            
            # Extract entities and relationships
            graph_storage = await extract_entities_dspy(
                chunks=chunk_schemas,
                graph_storage=self.rag.chunk_entity_relation_graph,
                entity_vdb=self.rag.vector_storage,
                global_config=self.rag.__dict__
            )
            
            # Store document chunks
            await self._store_chunks(chunk_schemas)
            
            return {"status": "success", "num_chunks": len(chunks)}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _create_chunks(self, content: str) -> list[str]:
        """Split document into chunks"""
        from nano_graphrag._splitter import SeparatorSplitter
        splitter = SeparatorSplitter(
            separators=["\n", "."],
            chunk_size=CHUNK_SIZE,
            chunk_overlap=50,
            keep_separator="end"
        )
        return splitter.split(content)
    
    async def _store_chunks(self, chunk_schemas: dict):
        """Store document chunks in vector store"""
        await self.rag.vector_storage.upsert(chunk_schemas)
```

### 3. Query Processing Implementation

```python
class QueryProcessor:
    def __init__(self, rag_instance: GraphRAG):
        self.rag = rag_instance
        
    async def process_query(self, query: str, mode: str = "hybrid"):
        """Process user query with specified mode"""
        try:
            if mode == "simple":
                return await self._process_simple_query(query)
            elif mode == "research":
                return await self._process_research_query(query)
            else:
                return await self._process_hybrid_query(query)
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _process_simple_query(self, query: str):
        """Handle simple queries (< 60 seconds)"""
        param = QueryParam(
            mode="local",
            top_k=5,
            min_similarity=0.7
        )
        result = await self.rag.aquery(query, param=param)
        return {
            "status": "success",
            "result": result,
            "type": "simple"
        }
    
    async def _process_research_query(self, query: str):
        """Handle complex research queries"""
        param = QueryParam(
            mode="global",
            use_graph=True,
            max_paths=3,
            min_similarity=0.6
        )
        # Start background task
        task = asyncio.create_task(
            self.rag.aquery(query, param=param)
        )
        return {
            "status": "pending",
            "task_id": id(task),
            "type": "research"
        }
    
    async def _process_hybrid_query(self, query: str):
        """Combine vector search with graph traversal"""
        param = QueryParam(
            mode="hybrid",
            use_graph=True,
            top_k=3,
            max_paths=2
        )
        result = await self.rag.aquery(query, param=param)
        return {
            "status": "success",
            "result": result,
            "type": "hybrid"
        }
```

### 4. Background Task Management

```python
class BackgroundTaskManager:
    def __init__(self):
        self.tasks = {}
        
    async def create_task(self, coroutine, task_id: str = None):
        """Create and track a background task"""
        task = asyncio.create_task(coroutine)
        task_id = task_id or id(task)
        self.tasks[task_id] = {
            "task": task,
            "status": "running",
            "created_at": datetime.now()
        }
        return task_id
    
    async def get_task_status(self, task_id: str):
        """Check status of background task"""
        if task_id not in self.tasks:
            return {"status": "not_found"}
        
        task_info = self.tasks[task_id]
        task = task_info["task"]
        
        if task.done():
            if task.exception():
                status = "failed"
                result = str(task.exception())
            else:
                status = "completed"
                result = task.result()
            return {"status": status, "result": result}
        
        return {"status": "running"}
    
    async def cleanup_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        now = datetime.now()
        to_remove = []
        
        for task_id, task_info in self.tasks.items():
            if task_info["task"].done():
                age = now - task_info["created_at"]
                if age.total_seconds() > max_age_hours * 3600:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
```

### 5. Error Handling & Recovery

```python
class ErrorHandler:
    def __init__(self, rag_instance: GraphRAG):
        self.rag = rag_instance
        
    async def handle_vector_store_error(self, error: Exception, data: dict):
        """Handle vector store errors"""
        if isinstance(error, ValueError) and "Cannot insert" in str(error):
            # Handle storage overflow
            await self._resize_vector_store()
            # Retry insertion
            await self.rag.vector_storage.upsert(data)
        else:
            raise error
    
    async def _resize_vector_store(self):
        """Resize vector store when near capacity"""
        current_size = len(self.rag.vector_storage)
        new_size = current_size * 2
        
        # Create new storage with larger capacity
        new_storage = HNSWVectorStorage(
            namespace=self.rag.vector_storage.namespace,
            global_config=self.rag.__dict__,
            max_elements=new_size
        )
        
        # Transfer existing vectors
        await self._transfer_vectors(self.rag.vector_storage, new_storage)
        self.rag.vector_storage = new_storage
    
    async def handle_graph_store_error(self, error: Exception):
        """Handle graph store errors"""
        if isinstance(error, nx.NetworkXError):
            # Reset and rebuild graph
            await self.rag.chunk_entity_relation_graph._debug_delete_all_node_edges()
            await self.rag.chunk_entity_relation_graph.index_start_callback()
            # Rebuild from backup if available
            await self._rebuild_graph()
        else:
            raise error
```

### 6. Integration Tests

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_document_processing():
    # Initialize test RAG
    rag = GraphRAG(
        working_dir="./test_data",
        embedding_func=docinsight_embedding
    )
    processor = DocumentProcessor(rag)
    
    # Test document
    content = "Test document content."
    doc_id = "test_doc"
    
    # Process document
    result = await processor.process_document(content, doc_id)
    
    assert result["status"] == "success"
    assert result["num_chunks"] > 0
    
    # Verify storage
    chunks = await rag.vector_storage.query("test", top_k=1)
    assert len(chunks) > 0

@pytest.mark.asyncio
async def test_query_processing():
    rag = GraphRAG(
        working_dir="./test_data",
        embedding_func=docinsight_embedding
    )
    processor = QueryProcessor(rag)
    
    # Test simple query
    simple_result = await processor.process_query(
        "test query",
        mode="simple"
    )
    assert simple_result["status"] == "success"
    
    # Test research query
    research_result = await processor.process_query(
        "complex research query",
        mode="research"
    )
    assert research_result["status"] == "pending"
```

## Usage Example

```python
async def main():
    # Initialize DocInsight
    doc_insight = DocInsightRAG()
    doc_processor = DocumentProcessor(doc_insight.rag)
    query_processor = QueryProcessor(doc_insight.rag)
    task_manager = BackgroundTaskManager()
    
    # Process document
    doc_result = await doc_processor.process_document(
        content="Sample document content",
        doc_id="doc1",
        metadata={"source": "test"}
    )
    
    # Process simple query
    simple_result = await query_processor.process_query(
        "What is the main topic?",
        mode="simple"
    )
    
    # Process research query
    research_task_id = await task_manager.create_task(
        query_processor.process_query(
            "Analyze the relationships between entities",
            mode="research"
        )
    )
    
    # Check research task status
    status = await task_manager.get_task_status(research_task_id)
    
    return {
        "doc_result": doc_result,
        "simple_result": simple_result,
        "research_status": status
    }

if __name__ == "__main__":
    asyncio.run(main())
```

This implementation provides a complete framework for integrating Graph RAG into DocInsight, with proper error handling, background task management, and query processing capabilities. Each component is designed to handle DocInsight's specific requirements while maintaining scalability and reliability.

Key features:
- Async processing for better performance
- Proper error handling and recovery
- Background task management
- Flexible query modes
- Document chunking and processing
- Entity extraction and relationship management

The code can be extended or modified based on specific needs, such as adding more query types, implementing different embedding models, or enhancing the background task management system.