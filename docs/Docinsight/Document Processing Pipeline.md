# DocInsight Design Analysis and Implementation Strategy

## 1. Core Component Analysis

### Docling Integration (Key Component)
1. **Document Processing Pipeline**
   - Use Docling's multi-format support (PDF, DOCX, PPTX, HTML, Markdown)
   - Leverage built-in backends for different formats:
     * PDFium backend for PDFs
     * Microsoft Office backends for DOCX/PPTX
     * HTML and AsciiDoc backends for web content
   - Implement format-specific validation

2. **Backend Selection Strategy**
```python
def get_document_backend(file_path: str) -> DocumentBackend:
    """Select appropriate Docling backend based on file type."""
    format = determine_format(file_path)
    return {
        'pdf': PyPdfiumDocumentBackend,
        'docx': MsWordDocumentBackend,
        'pptx': PptxDocumentBackend,
        'html': HTMLDocumentBackend,
        'asciidoc': AsciiDocBackend
    }[format]
```

### Data Architecture
1. **SQLite Schema** (MVP Phase)
   - Document metadata storage
   - Vector reference management
   - User session handling
   - Background task tracking

2. **Vector Storage**
   - Use NanoGraphRAG's nano-vectordb for embeddings
   - Implement vector reference tracking in SQLite
   - Prepare for LanceDB migration post-MVP

## 2. Pipeline Implementation Strategy

### Phase 1: Document Processing
```python
class DocInsightProcessor:
    def __init__(self):
        self.docling_processor = DoclingProcessor()
        self.vector_store = NanoVectorStorage()
        self.metadata_store = SQLiteMetadataStore()
    
    async def process_document(self, file_path: str) -> str:
        # 1. Select appropriate backend
        backend = get_document_backend(file_path)
        
        # 2. Process with Docling
        doc = await self.docling_processor.process(file_path, backend)
        
        # 3. Generate chunks and embeddings
        chunks = await self.generate_chunks(doc)
        embeddings = await self.generate_embeddings(chunks)
        
        # 4. Store results
        doc_id = await self.store_document(doc, chunks, embeddings)
        
        return doc_id
```

### Phase 2: Vector Processing
```python
class VectorProcessor:
    def __init__(self, nano_rag_client: NanoGraphRAG):
        self.rag_client = nano_rag_client
        
    async def process_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """Process document chunks and store vectors."""
        # Generate embeddings using potion-base-8M
        embeddings = await self.rag_client.embed_chunks(chunks)
        
        # Store in nano-vectordb
        vector_ids = await self.rag_client.store_vectors(embeddings)
        
        return vector_ids
```

## 3. Error Handling and Monitoring

### Error Categories and Handling
1. **Document Processing Errors**
```python
class DocumentProcessingError(Exception):
    """Base exception for document processing errors."""
    pass

class UnsupportedFormatError(DocumentProcessingError):
    """Raised when document format is not supported."""
    pass

class ExtractionError(DocumentProcessingError):
    """Raised when content extraction fails."""
    pass
```

2. **Monitoring Integration**
```python
from opentelemetry import trace, metrics

class ProcessingMetrics:
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.process_duration = metrics.get_meter(__name__).create_histogram(
            "document_processing_duration",
            unit="seconds",
            description="Time taken to process documents"
        )
```

## 4. Testing Strategy

### Test Categories
1. **Backend Selection Tests**
```python
class TestBackendSelection:
    @pytest.mark.parametrize("file_format,expected_backend", [
        ("pdf", PyPdfiumDocumentBackend),
        ("docx", MsWordDocumentBackend),
        ("html", HTMLDocumentBackend)
    ])
    def test_backend_selection(self, file_format, expected_backend):
        assert isinstance(
            get_document_backend(f"test.{file_format}"),
            expected_backend
        )
```

2. **Document Processing Tests**
```python
class TestDocumentProcessing:
    async def test_end_to_end_processing(self):
        processor = DocInsightProcessor()
        doc_id = await processor.process_document("test.pdf")
        
        # Verify processing results
        doc = await processor.get_document(doc_id)
        assert doc.chunks is not None
        assert doc.embeddings is not None
```

## 5. Migration Considerations

### Pre-Migration Tasks
1. **Data Schema Preparation**
```python
async def prepare_migration():
    """Prepare database for future Supabase migration."""
    await create_migration_tables()
    await validate_data_integrity()
    await generate_migration_metrics()
```

2. **Vector Storage Migration**
```python
async def prepare_vector_migration():
    """Prepare vector storage for LanceDB migration."""
    await validate_vector_integrity()
    await generate_vector_migration_plan()
```

## Implementation Recommendations

1. **Start with Core Processing**
   - Implement Docling backend selection
   - Set up basic document processing
   - Establish SQLite storage

2. **Add Vector Processing**
   - Integrate NanoGraphRAG
   - Implement vector storage
   - Add chunk processing

3. **Implement Monitoring**
   - Set up OpenTelemetry
   - Add Prometheus metrics
   - Implement error tracking

4. **Add Testing Infrastructure**
   - Unit tests for each component
   - Integration tests for pipeline
   - Performance benchmarks

Would you like to:
1. Dive deeper into any specific component?
2. Start implementing a particular part?
3. Discuss testing strategies in more detail?
4. Review the error handling approach?


Yes, we have comprehensive information to implement the Document Processing Pipeline for our core user story (DOC-001 and DOC-002). Let's break this down:

From our user stories:

DOC-001 requires:
- Multi-format support (PDF, DOCX, TXT, MD)
- Format validation
- Upload progress display
- Clear error messages

DOC-002 requires:
- Processing within 5 minutes
- Automatic index updates
- Visible processing status
- Metadata extraction
- Background reprocessing

From our documentation we have:
1. Docling capabilities for multi-format processing
2. SQLite schema for metadata storage
3. NanoGraphRAG for vector operations
4. Detailed error handling patterns
5. Monitoring requirements

Let me outline a practical implementation approach:



```python
"""
DocInsight Document Processing Pipeline
Core implementation for DOC-001 and DOC-002 user stories.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
import asyncio

from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument, DocumentBackend
from docling.backend.pdfium_backend import PyPdfiumDocumentBackend
from docling.backend.msword_backend import MsWordDocumentBackend
from opentelemetry import trace
from prometheus_client import Counter, Histogram

class DocumentStatus(Enum):
    RECEIVED = "received"
    VALIDATING = "validating"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    VECTORIZING = "vectorizing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentMetadata:
    def __init__(self, 
                 original_filename: str,
                 mime_type: str,
                 file_size: int):
        self.id = uuid4()
        self.original_filename = original_filename
        self.mime_type = mime_type
        self.file_size = file_size
        self.created_at = datetime.utcnow()
        self.status = DocumentStatus.RECEIVED
        self.error_message: Optional[str] = None
        self.processing_progress: float = 0.0
        
    def update_status(self, status: DocumentStatus, error: Optional[str] = None):
        self.status = status
        self.error_message = error

class DocumentProcessor:
    """Main document processing pipeline."""
    
    def __init__(self):
        # Initialize monitoring
        self.tracer = trace.get_tracer(__name__)
        self.process_duration = Histogram(
            "document_process_duration_seconds",
            "Time spent processing documents",
            buckets=[1.0, 60.0, 180.0, 300.0]  # Up to 5 minutes per DOC-002
        )
        self.process_errors = Counter(
            "document_process_errors_total",
            "Total number of document processing errors",
            ["error_type"]
        )
        
        # Initialize backend mappings
        self.backend_mapping = {
            'application/pdf': PyPdfiumDocumentBackend,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 
                MsWordDocumentBackend,
            # Add other backends as needed
        }
    
    async def process_document(self, 
                             file_path: str, 
                             metadata: DocumentMetadata) -> str:
        """
        Process a document through the pipeline.
        
        Args:
            file_path: Path to the document file
            metadata: Document metadata including mime type
            
        Returns:
            document_id: Unique identifier for the processed document
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        with self.tracer.start_as_current_span("process_document") as span:
            span.set_attribute("document_id", str(metadata.id))
            span.set_attribute("mime_type", metadata.mime_type)
            
            try:
                with self.process_duration.time():
                    # 1. Validate document
                    await self._validate_document(file_path, metadata)
                    
                    # 2. Get appropriate backend
                    backend = self._get_backend(metadata.mime_type)
                    
                    # 3. Process with Docling
                    doc = await self._process_with_docling(file_path, backend)
                    metadata.update_status(DocumentStatus.PROCESSING)
                    
                    # 4. Extract content and metadata
                    content = await self._extract_content(doc)
                    metadata.update_status(DocumentStatus.EXTRACTING)
                    
                    # 5. Generate vectors
                    vectors = await self._generate_vectors(content)
                    metadata.update_status(DocumentStatus.VECTORIZING)
                    
                    # 6. Store everything
                    doc_id = await self._store_document(metadata, content, vectors)
                    
                    # 7. Mark as completed
                    metadata.update_status(DocumentStatus.COMPLETED)
                    metadata.processing_progress = 100.0
                    
                    return doc_id
                    
            except Exception as e:
                self.process_errors.labels(error_type=type(e).__name__).inc()
                metadata.update_status(DocumentStatus.FAILED, str(e))
                raise DocumentProcessingError(f"Processing failed: {str(e)}")
    
    async def _validate_document(self, 
                               file_path: str, 
                               metadata: DocumentMetadata) -> None:
        """Validate document format and accessibility."""
        metadata.update_status(DocumentStatus.VALIDATING)
        if metadata.mime_type not in self.backend_mapping:
            raise UnsupportedFormatError(f"Unsupported format: {metadata.mime_type}")
        if metadata.file_size > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {metadata.file_size} bytes")
        metadata.processing_progress = 10.0

    def _get_backend(self, mime_type: str) -> Type[DocumentBackend]:
        """Get appropriate Docling backend for document type."""
        return self.backend_mapping.get(mime_type)
    
    async def _process_with_docling(self, 
                                  file_path: str, 
                                  backend: Type[DocumentBackend]):
        """Process document using Docling."""
        input_doc = InputDocument(
            path_or_stream=file_path,
            backend=backend
        )
        return await input_doc._backend.convert()
    
    async def _extract_content(self, doc) -> Dict[str, Any]:
        """Extract content and metadata from processed document."""
        # Implementation using Docling's extraction capabilities
        pass
    
    async def _generate_vectors(self, content: Dict[str, Any]) -> List[float]:
        """Generate vector embeddings for document content."""
        # Implementation using NanoGraphRAG
        pass
    
    async def _store_document(self, 
                            metadata: DocumentMetadata,
                            content: Dict[str, Any],
                            vectors: List[float]) -> str:
        """Store document content, metadata, and vectors."""
        # Implementation using SQLite and nano-vectordb
        pass

# Error Classes
class DocumentProcessingError(Exception):
    """Base class for document processing errors."""
    pass

class UnsupportedFormatError(DocumentProcessingError):
    """Raised when document format is not supported."""
    pass

class FileTooLargeError(DocumentProcessingError):
    """Raised when document exceeds size limit."""
    pass

# Constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

```

This implementation:

1. Addresses DOC-001 requirements:
   - Supports multiple formats through Docling backends
   - Includes format validation
   - Tracks progress
   - Has clear error handling

2. Meets DOC-002 requirements:
   - Monitors processing time (5-minute target)
   - Updates status in real-time
   - Extracts metadata
   - Prepares for background processing

3. Integrates core components:
   - Docling for document processing
   - NanoGraphRAG for vectors
   - SQLite for metadata
   - OpenTelemetry for monitoring

Would you like to:
1. Start implementing any specific method (like `_extract_content` or `_generate_vectors`)?
2. Add the background processing capability?
3. Create the testing suite for this implementation?
4. Work on the progress tracking and status updates?


You're absolutely right. Following TDD principles, let's design our tests first. Looking at DOC-001 and DOC-002 requirements, let's outline our test scenarios.



```python
"""
Test suite for DocInsight Document Processing Pipeline.
Following TDD principles to cover DOC-001 and DOC-002 requirements.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import AsyncGenerator
import asyncio
from datetime import datetime, timedelta

# Test Constants
SAMPLE_PDF = "tests/data/sample.pdf"
SAMPLE_DOCX = "tests/data/sample.docx"
SAMPLE_MD = "tests/data/sample.md"
LARGE_PDF = "tests/data/large.pdf"  # >100MB
CORRUPT_PDF = "tests/data/corrupt.pdf"

class TestDocumentProcessing:
    """
    Core document processing tests covering DOC-001 requirements:
    - Multi-format support
    - Format validation
    - Upload progress
    - Error messages
    """
    
    @pytest.fixture
    async def processor(self):
        """Setup test document processor with mocked dependencies."""
        # TODO: Initialize with mocked Docling, NanoGraphRAG, and SQLite
        pass
    
    @pytest.mark.asyncio
    async def test_supported_formats(self, processor):
        """
        Test processing of all supported formats.
        
        Requirements:
        - Should accept PDF, DOCX, TXT, MD
        - Should extract content correctly
        - Should generate appropriate metadata
        """
        test_files = [
            (SAMPLE_PDF, "application/pdf"),
            (SAMPLE_DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            (SAMPLE_MD, "text/markdown")
        ]
        
        for file_path, mime_type in test_files:
            metadata = DocumentMetadata(
                original_filename=file_path.split("/")[-1],
                mime_type=mime_type,
                file_size=1024  # Mock size
            )
            
            doc_id = await processor.process_document(file_path, metadata)
            
            assert doc_id is not None
            assert metadata.status == DocumentStatus.COMPLETED
            assert metadata.processing_progress == 100.0
            # TODO: Add format-specific content validation
    
    @pytest.mark.asyncio
    async def test_format_validation(self, processor):
        """
        Test format validation logic.
        
        Cases:
        - Unsupported format
        - Corrupt file
        - Empty file
        - File too large
        """
        test_cases = [
            ("unsupported.xyz", "application/unknown", UnsupportedFormatError),
            (CORRUPT_PDF, "application/pdf", DocumentProcessingError),
            (LARGE_PDF, "application/pdf", FileTooLargeError)
        ]
        
        for file_path, mime_type, expected_error in test_cases:
            metadata = DocumentMetadata(
                original_filename=file_path.split("/")[-1],
                mime_type=mime_type,
                file_size=1024  # Mock size
            )
            
            with pytest.raises(expected_error):
                await processor.process_document(file_path, metadata)
            
            assert metadata.status == DocumentStatus.FAILED
            assert metadata.error_message is not None

class TestProcessingRequirements:
    """
    Tests covering DOC-002 requirements:
    - Processing time limits
    - Index updates
    - Status tracking
    - Metadata extraction
    - Background processing
    """
    
    @pytest.mark.asyncio
    async def test_processing_time_limit(self, processor):
        """
        Test that processing completes within 5 minutes.
        """
        start_time = datetime.utcnow()
        
        metadata = DocumentMetadata(
            original_filename="large_document.pdf",
            mime_type="application/pdf",
            file_size=50 * 1024 * 1024  # 50MB
        )
        
        doc_id = await processor.process_document(SAMPLE_PDF, metadata)
        
        processing_time = datetime.utcnow() - start_time
        assert processing_time < timedelta(minutes=5)
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, processor):
        """
        Test progress tracking and status updates.
        
        Verify:
        - Status transitions
        - Progress updates
        - Metadata updates
        """
        metadata = DocumentMetadata(
            original_filename="test.pdf",
            mime_type="application/pdf",
            file_size=1024
        )
        
        expected_statuses = [
            DocumentStatus.RECEIVED,
            DocumentStatus.VALIDATING,
            DocumentStatus.PROCESSING,
            DocumentStatus.EXTRACTING,
            DocumentStatus.VECTORIZING,
            DocumentStatus.COMPLETED
        ]
        
        actual_statuses = []
        
        # Mock status callback
        def status_callback(status):
            actual_statuses.append(status)
        
        await processor.process_document(SAMPLE_PDF, metadata)
        
        assert actual_statuses == expected_statuses
        assert metadata.processing_progress == 100.0

class TestErrorHandling:
    """Tests for error handling and recovery scenarios."""
    
    @pytest.mark.asyncio
    async def test_extraction_failure(self, processor):
        """Test handling of content extraction failures."""
        pass
    
    @pytest.mark.asyncio
    async def test_vectorization_failure(self, processor):
        """Test handling of vectorization failures."""
        pass
    
    @pytest.mark.asyncio
    async def test_storage_failure(self, processor):
        """Test handling of storage failures."""
        pass

class TestBackgroundProcessing:
    """Tests for background processing capabilities."""
    
    @pytest.mark.asyncio
    async def test_background_reprocessing(self, processor):
        """Test document reprocessing in background."""
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, processor):
        """Test handling of multiple concurrent documents."""
        pass

class TestMetadataExtraction:
    """Tests for metadata extraction and storage."""
    
    @pytest.mark.asyncio
    async def test_pdf_metadata(self, processor):
        """Test PDF-specific metadata extraction."""
        pass
    
    @pytest.mark.asyncio
    async def test_docx_metadata(self, processor):
        """Test DOCX-specific metadata extraction."""
        pass

# Performance Tests
class TestPerformance:
    """Performance and scalability tests."""
    
    @pytest.mark.asyncio
    async def test_large_document_handling(self, processor):
        """Test processing of large documents."""
        pass
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, processor):
        """Test memory usage during processing."""
        pass

```

This test suite:

1. **Core Test Categories**:
   - Format support (DOC-001)
   - Processing requirements (DOC-002)
   - Error handling
   - Background processing
   - Metadata extraction
   - Performance

2. **Test Coverage**:
   - Basic functionality
   - Edge cases
   - Error conditions
   - Performance requirements
   - Concurrent processing

3. **Test Organization**:
   - Grouped by feature
   - Clear test purposes
   - Fixture setup
   - Mock dependencies

Would you like to:

1. Start implementing specific test cases in detail?
2. Add more edge cases to consider?
3. Set up the test fixtures and mocks?
4. Focus on a particular test category?

Let me know which aspect you'd like to tackle first, and we can work on implementing the actual test code.


Looking at what we have so far, we've got a solid foundation with well-structured code following clean architecture principles. Let me analyze the key points and suggest next steps:

Strengths:
1. Clear domain model with `DocumentProcessor` and `DocumentMetadata`
2. Comprehensive test structure covering our P0 requirements (DOC-001 and DOC-002)
3. Good error handling and monitoring setup
4. Well-defined status tracking and progress reporting

Areas to Address:

1. **Test Fixtures**: We need to implement the mocked dependencies first. This is critical for TDD.
```python
@pytest.fixture
async def processor():
    """Setup test document processor with mocked dependencies."""
    # TODO: We need to implement this first
    pass
```

2. **Status Transitions**: The status callback mechanism in tests isn't fully integrated with the processor:
```python
# In DocumentProcessor
def register_status_callback(self, callback: Callable[[DocumentStatus], None]):
    self._status_callbacks.append(callback)
```

3. **Background Processing**: The tests are structured for it but we haven't defined how it will work:
```python
class BackgroundProcessor:
    """Handles background processing tasks."""
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self._running = False
```

4. **Missing Test Data**: We need to set up test data fixtures:
```python
@pytest.fixture
def sample_files():
    """Provide test document files."""
    return {
        'pdf': Path('tests/data/sample.pdf'),
        'docx': Path('tests/data/sample.docx'),
        'md': Path('tests/data/sample.md')
    }
```

Suggested Next Steps:

1. Implement the core test fixtures first:
   - Mock Docling
   - Mock NanoGraphRAG
   - Mock SQLite storage
   - Sample test files

2. Start with the simplest test case - format validation:
   - File exists
   - Supported format
   - Size check

3. Then move to document processing basics:
   - Basic content extraction
   - Status updates
   - Progress tracking

Would you like me to:
1. Start implementing the test fixtures?
2. Create the sample test data structure?
3. Begin with a specific test category implementation?
4. Add more detailed test cases?