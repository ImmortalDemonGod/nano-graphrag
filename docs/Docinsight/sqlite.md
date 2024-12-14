Let me help you analyze how to effectively implement SQLite within DocInsight, based on the provided documentation. I'll focus on key implementation considerations that align with DocInsight's requirements.





# SQLite Implementation Guide for DocInsight

## Overview
This guide outlines the SQLite implementation strategy for DocInsight's MVP phase (targeting June 1st, 2025), focusing on efficient document management, user authentication, and query processing.

## 1. Database Architecture

### Core Schema Design
```sql
-- Document Management
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    format TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Vector Storage Reference
CREATE TABLE vector_references (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_id TEXT NOT NULL,
    vector_store_key TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    UNIQUE (document_id, chunk_id)
);

-- User Management
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    mac_address TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Session Management
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Query History
CREATE TABLE queries (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    query_text TEXT NOT NULL,
    query_type TEXT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT NOT NULL,
    results_cache_key TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Background Tasks
CREATE TABLE background_tasks (
    id INTEGER PRIMARY KEY,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    parameters JSON,
    result JSON
);
```

## 2. Connection Management

### Connection Pool Implementation
```python
import sqlite3
from contextlib import contextmanager
from threading import Lock

class SQLiteConnectionPool:
    def __init__(self, database_path, max_connections=10):
        self.database_path = database_path
        self.max_connections = max_connections
        self.connections = []
        self.lock = Lock()
        
    @contextmanager
    def get_connection(self):
        with self.lock:
            if len(self.connections) < self.max_connections:
                conn = sqlite3.connect(
                    self.database_path,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
                )
                conn.row_factory = sqlite3.Row
                self.connections.append(conn)
            else:
                conn = self.connections.pop(0)
                
        try:
            yield conn
        finally:
            with self.lock:
                if len(self.connections) < self.max_connections:
                    self.connections.append(conn)
                else:
                    conn.close()

# Usage
pool = SQLiteConnectionPool("docinsight.db")

with pool.get_connection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents")
```

## 3. Query Optimization

### Index Creation
```sql
-- Document retrieval optimization
CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_documents_format ON documents(format);

-- Vector reference lookup optimization
CREATE INDEX idx_vector_refs_document ON vector_references(document_id);
CREATE INDEX idx_vector_refs_store_key ON vector_references(vector_store_key);

-- User authentication optimization
CREATE INDEX idx_users_mac_address ON users(mac_address);
CREATE INDEX idx_users_username ON users(username);

-- Session management optimization
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_user_expiry ON sessions(user_id, expires_at);

-- Query history optimization
CREATE INDEX idx_queries_user_time ON queries(user_id, start_time);
CREATE INDEX idx_queries_status ON queries(status);
```

## 4. Transaction Management

### Transaction Wrapper
```python
from functools import wraps
from sqlite3 import Error

def transaction(func):
    @wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except Error as e:
            conn.rollback()
            raise DatabaseError(f"Transaction failed: {str(e)}")
    return wrapper

# Usage example
@transaction
def store_document(conn, title, content_hash, file_path, format, metadata):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO documents (title, content_hash, file_path, format, metadata)
        VALUES (?, ?, ?, ?, json(?))
    """, (title, content_hash, file_path, format, json.dumps(metadata)))
    return cur.lastrowid
```

## 5. Background Task Management

### Task Queue Integration
```python
class BackgroundTaskManager:
    def __init__(self, pool):
        self.pool = pool
    
    @transaction
    def create_task(self, conn, task_type, parameters):
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO background_tasks (task_type, status, parameters)
            VALUES (?, 'pending', json(?))
        """, (task_type, json.dumps(parameters)))
        return cur.lastrowid
    
    @transaction
    def update_task_status(self, conn, task_id, status, result=None):
        cur = conn.cursor()
        if status == 'completed':
            cur.execute("""
                UPDATE background_tasks
                SET status = ?, completed_at = CURRENT_TIMESTAMP, result = json(?)
                WHERE id = ?
            """, (status, json.dumps(result), task_id))
        else:
            cur.execute("""
                UPDATE background_tasks
                SET status = ?, started_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, task_id))

# Usage
task_manager = BackgroundTaskManager(pool)
with pool.get_connection() as conn:
    task_id = task_manager.create_task(conn, 'document_processing', {
        'document_id': 123,
        'options': {'chunk_size': 1000}
    })
```

## 6. Performance Monitoring

### Query Performance Tracking
```python
import time
from contextlib import contextmanager

@contextmanager
def query_performance_tracker(conn, query_type):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO query_performance (query_type, duration)
            VALUES (?, ?)
        """, (query_type, duration))
        conn.commit()

# Usage
with pool.get_connection() as conn:
    with query_performance_tracker(conn, 'document_search'):
        cur = conn.cursor()
        cur.execute("SELECT * FROM documents WHERE format = ?", ('pdf',))
```

## 7. Migration Strategy

### Schema Version Control
```python
def initialize_schema_version(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
def get_current_version(conn):
    cur = conn.execute("SELECT MAX(version) FROM schema_version")
    result = cur.fetchone()[0]
    return result or 0

def apply_migration(conn, version, sql):
    cur = conn.cursor()
    cur.executescript(sql)
    cur.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()

# Usage
migrations = {
    1: "CREATE TABLE documents ...",
    2: "ALTER TABLE documents ADD COLUMN metadata JSON"
}

def migrate_database(conn):
    initialize_schema_version(conn)
    current_version = get_current_version(conn)
    
    for version in sorted(migrations.keys()):
        if version > current_version:
            apply_migration(conn, version, migrations[version])
```

## 8. Security Considerations

### Access Control Implementation
```python
def verify_mac_address(mac_address):
    with pool.get_connection() as conn:
        cur = conn.execute("""
            SELECT id FROM users 
            WHERE mac_address = ? AND role != 'disabled'
        """, (mac_address,))
        return cur.fetchone() is not None

def create_session(user_id, duration_hours=24):
    with pool.get_connection() as conn:
        token = secrets.token_urlsafe(32)
        conn.execute("""
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (?, ?, datetime('now', ?))
        """, (user_id, token, f'+{duration_hours} hours'))
        conn.commit()
        return token

def verify_session(token):
    with pool.get_connection() as conn:
        cur = conn.execute("""
            SELECT user_id FROM sessions
            WHERE token = ? AND expires_at > datetime('now')
        """, (token,))
        return cur.fetchone()
```

## Best Practices

1. **Connection Management**
   - Use connection pooling
   - Implement proper connection cleanup
   - Handle connection timeouts

2. **Transaction Handling**
   - Use transactions for data consistency
   - Implement proper error handling
   - Consider transaction isolation levels

3. **Query Optimization**
   - Create appropriate indexes
   - Use prepared statements
   - Monitor query performance

4. **Security**
   - Implement MAC address verification
   - Manage sessions securely
   - Use parameterized queries

5. **Maintenance**
   - Regular VACUUM operations
   - Monitor database size
   - Implement backup procedures

## Performance Targets

- Query response time: < 100ms for simple queries
- Concurrent connections: Support for 50 users
- Background task processing: < 5 minutes
- Session verification: < 10ms


This implementation guide provides a solid foundation for using SQLite in DocInsight's MVP phase. The design prioritizes performance, security, and maintainability while meeting the project's requirements for document processing and user management. Would you like me to elaborate on any particular aspect or provide additional examples for specific features?