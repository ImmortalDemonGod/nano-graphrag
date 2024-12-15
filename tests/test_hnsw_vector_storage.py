# tests/test_hnsw_vector_storage.py
import os
import shutil
from dataclasses import asdict
from unittest.mock import patch

import numpy as np
import pytest

from nano_graphrag import GraphRAG
from nano_graphrag._storage import HNSWVectorStorage
from nano_graphrag._utils import wrap_embedding_func_with_attrs

WORKING_DIR = "./tests/nano_graphrag_cache_hnsw_vector_storage_test"


@pytest.fixture(scope="function")
def setup_teardown():
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.mkdir(WORKING_DIR)

    yield

    shutil.rmtree(WORKING_DIR)


@wrap_embedding_func_with_attrs(embedding_dim=384, max_token_size=8192)
async def mock_embedding(texts: list[str]) -> np.ndarray:
    return np.random.rand(len(texts), 384)


@pytest.fixture
def rag():
    return GraphRAG(working_dir=WORKING_DIR, embedding_func=mock_embedding)


@pytest.fixture
def hnsw_storage(rag):
    return HNSWVectorStorage(
        namespace="test",
        global_config=asdict(rag),
        embedding_func=mock_embedding,
        meta_fields={"entity_name"},
    )


def generate_test_data(start: int, count: int) -> dict:
    return {
        str(i): {"content": f"Test content {i}", "entity_name": f"Entity {i}"}
        for i in range(start, start + count)
    }


def assert_query_results(results, expected_count, entity_names=None):
    assert len(results) == expected_count
    assert all(isinstance(result, dict) for result in results)
    assert all(
        "id" in result and "distance" in result and "similarity" in result
        for result in results
    )
    if entity_names:
        assert all(result["entity_name"] in entity_names for result in results)


@pytest.mark.asyncio
async def test_upsert_and_query(hnsw_storage):
    test_data = generate_test_data(1, 2)
    await hnsw_storage.upsert(test_data)

    results = await hnsw_storage.query("Test query", top_k=2)
    assert_query_results(results, expected_count=2)
    assert all(result["id"] in test_data for result in results)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "namespace, data_start, data_count, max_elements, query, top_k, expected_count, expected_entity_names",
    [
        (
            "test",
            1,
            1,
            None,
            "Test query",
            1,
            1,
            {"Entity 1"},
        ),
        (
            "test_large",
            0,
            1000,
            10000,
            "Test query",
            500,
            500,
            None,
        ),
    ],
)
async def test_persistence(
    setup_teardown,
    rag,
    namespace,
    data_start,
    data_count,
    max_elements,
    query,
    top_k,
    expected_count,
    expected_entity_names,
):
    storage = HNSWVectorStorage(
        namespace=namespace,
        global_config=asdict(rag),
        embedding_func=mock_embedding,
        meta_fields={"entity_name"},
        max_elements=max_elements,
    )

    test_data = generate_test_data(data_start, data_count)
    await storage.upsert(test_data)
    await storage.index_done_callback()

    new_storage = HNSWVectorStorage(
        namespace=namespace,
        global_config=asdict(rag),
        embedding_func=mock_embedding,
        meta_fields={"entity_name"},
        max_elements=max_elements,
    )

    results = await new_storage.query(query, top_k=top_k)
    assert_query_results(
        results, expected_count=expected_count, entity_names=expected_entity_names
    )

    if expected_entity_names:
        assert all(result["id"] in test_data for result in results)
        assert results[0]["id"] == str(data_start)


@pytest.mark.asyncio
async def test_upsert_with_existing_ids(hnsw_storage):
    initial_data = generate_test_data(1, 2)
    await hnsw_storage.upsert(initial_data)

    updated_data = {
        "1": {"content": "Updated content 1", "entity_name": "Updated Entity 1"},
        "3": {"content": "Test content 3", "entity_name": "Entity 3"},
    }
    await hnsw_storage.upsert(updated_data)

    results = await hnsw_storage.query("Updated", top_k=3)
    assert_query_results(
        results,
        expected_count=3,
        entity_names={"Updated Entity 1", "Entity 2", "Entity 3"},
    )

    # Specific assertions
    assert any(
        result["id"] == "1" and result["entity_name"] == "Updated Entity 1"
        for result in results
    )
    assert any(
        result["id"] == "2" and result["entity_name"] == "Entity 2"
        for result in results
    )
    assert any(
        result["id"] == "3" and result["entity_name"] == "Entity 3"
        for result in results
    )


@pytest.mark.asyncio
async def test_large_batch_upsert(hnsw_storage):
    batch_size = 30
    large_data = generate_test_data(0, batch_size)
    await hnsw_storage.upsert(large_data)

    results = await hnsw_storage.query("Test query", top_k=batch_size)
    assert_query_results(results, expected_count=batch_size)
    assert all(result["id"] in large_data for result in results)


@pytest.mark.asyncio
async def test_empty_data_insertion(hnsw_storage):
    empty_data = {}
    await hnsw_storage.upsert(empty_data)

    results = await hnsw_storage.query("Test query", top_k=1)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_query_with_no_results(hnsw_storage):
    # Initial query with no data
    results = await hnsw_storage.query("Non-existent query", top_k=5)
    assert len(results) == 0

    # Insert data and query again
    test_data = generate_test_data(1, 1)
    await hnsw_storage.upsert(test_data)

    results = await hnsw_storage.query("Non-existent query", top_k=5)
    assert_query_results(results, expected_count=1, entity_names={"Entity 1"})
    assert all(0 <= result["similarity"] <= 1 for result in results)
    assert "entity_name" in results[0]


@pytest.mark.asyncio
async def test_index_done_callback(hnsw_storage):
    test_data = generate_test_data(1, 1)
    await hnsw_storage.upsert(test_data)

    with patch("hnswlib.Index.save_index") as mock_save_index:
        await hnsw_storage.index_done_callback()
        mock_save_index.assert_called_once()


@pytest.mark.asyncio
async def test_max_elements_limit(setup_teardown, rag):
    max_elements = 10
    small_storage = HNSWVectorStorage(
        namespace="test_small",
        global_config=asdict(rag),
        embedding_func=mock_embedding,
        meta_fields={"entity_name"},
        max_elements=max_elements,
        M=50,
    )

    data = generate_test_data(0, max_elements)
    await small_storage.upsert(data)

    with pytest.raises(
        ValueError,
        match=f"Cannot insert 1 elements. Current: {max_elements}, Max: {max_elements}",
    ):
        await small_storage.upsert(
            {
                str(max_elements): {
                    "content": "Overflow",
                    "entity_name": "Overflow Entity",
                }
            }
        )

    # Test with larger max_elements
    large_max_elements = 100
    large_storage = HNSWVectorStorage(
        namespace="test_large",
        global_config=asdict(rag),
        embedding_func=mock_embedding,
        meta_fields={"entity_name"},
        max_elements=large_max_elements,
    )

    initial_data_size = int(large_max_elements * 0.3)
    initial_data = generate_test_data(0, initial_data_size)
    await large_storage.upsert(initial_data)

    results = await large_storage.query("Test query", top_k=initial_data_size)
    assert_query_results(results, expected_count=initial_data_size)


@pytest.mark.asyncio
async def test_ef_search_values(setup_teardown, rag):
    storage = HNSWVectorStorage(
        namespace="test_ef",
        global_config=asdict(rag),
        embedding_func=mock_embedding,
        meta_fields={"entity_name"},
        ef_search=10,
    )

    data = generate_test_data(0, 20)
    await storage.upsert(data)

    results_default = await storage.query("Test query", top_k=5)
    assert_query_results(results_default, expected_count=5)

    # Update ef_search parameter
    storage._index.set_ef(20)
    results_higher_ef = await storage.query("Test query", top_k=15)
    assert_query_results(results_higher_ef, expected_count=15)
