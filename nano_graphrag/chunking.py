# /Volumes/Totallynotaharddrive/nano-graphrag/nano_graphrag/chunking.py

from collections.abc import Callable
from typing import Any

import tiktoken

from ._splitter import SeparatorSplitter
from ._utils import compute_mdhash_id
from .prompt import PROMPTS  # Ensure PROMPTS is defined in constants.py


def chunking_by_token_size(
    tokens_list: list[list[int]],
    doc_keys: list[str],
    tiktoken_model: Any,  # Replace Any with actual type if known
    overlap_token_size: int = 128,
    max_token_size: int = 1024,
) -> list[dict[str, Any]]:
    """
    Splits tokens into chunks based on token size with optional overlap.

    Args:
        tokens_list (List[List[int]]): List of token lists for each document.
        doc_keys (List[str]): Corresponding document keys.
        tiktoken_model (Any): Tokenizer model instance.
        overlap_token_size (int, optional): Number of overlapping tokens. Defaults to 128.
        max_token_size (int, optional): Maximum tokens per chunk. Defaults to 1024.

    Returns:
        List[Dict[str, Any]]: List of chunk dictionaries with metadata.
    """
    results = []
    for index, tokens in enumerate(tokens_list):
        chunk_tokens = []
        lengths = []
        step = max_token_size - overlap_token_size
        for start in range(0, len(tokens), step):
            end = start + max_token_size
            chunk = tokens[start:end]
            chunk_tokens.append(chunk)
            lengths.append(len(chunk))

        # Decode the batch of token chunks into text
        chunk_decoded = tiktoken_model.decode_batch(chunk_tokens)
        for i, chunk in enumerate(chunk_decoded):
            results.append(
                {
                    "tokens": lengths[i],
                    "content": chunk.strip(),
                    "chunk_order_index": i,
                    "full_doc_id": doc_keys[index],
                }
            )
    return results


def chunking_by_seperators(
    tokens_list: list[list[int]],
    doc_keys: list[str],
    tiktoken_model: Any,  # Replace Any with actual type if known
    overlap_token_size: int = 128,
    max_token_size: int = 1024,
) -> list[dict[str, Any]]:
    """
    Splits tokens into chunks based on predefined separators with optional overlap.

    Args:
        tokens_list (List[List[int]]): List of token lists for each document.
        doc_keys (List[str]): Corresponding document keys.
        tiktoken_model (Any): Tokenizer model instance.
        overlap_token_size (int, optional): Number of overlapping tokens. Defaults to 128.
        max_token_size (int, optional): Maximum tokens per chunk. Defaults to 1024.

    Returns:
        List[Dict[str, Any]]: List of chunk dictionaries with metadata.
    """
    separators = [
        tiktoken_model.encode(separator) for separator in PROMPTS["default_text_separator"]
    ]
    splitter = SeparatorSplitter(
        separators=separators,
        chunk_size=max_token_size,
        chunk_overlap=overlap_token_size,
    )
    results = []
    for index, tokens in enumerate(tokens_list):
        chunk_tokens = splitter.split_tokens(tokens)
        lengths = [len(chunk) for chunk in chunk_tokens]

        # Decode the batch of token chunks into text
        chunk_decoded = tiktoken_model.decode_batch(chunk_tokens)
        for i, chunk in enumerate(chunk_decoded):
            results.append(
                {
                    "tokens": lengths[i],
                    "content": chunk.strip(),
                    "chunk_order_index": i,
                    "full_doc_id": doc_keys[index],
                }
            )

    return results


def get_chunks(
    new_docs: dict[str, dict[str, Any]],
    chunk_func: Callable[..., list[dict[str, Any]]] = chunking_by_token_size,
    **chunk_func_params: Any,
) -> dict[str, dict[str, Any]]:
    """
    Processes new documents into chunks using the specified chunking function.

    Args:
        new_docs (Dict[str, Dict[str, Any]]): New documents with content.
        chunk_func (Callable[..., List[Dict[str, Any]]], optional): Chunking function to use. Defaults to chunking_by_token_size.
        **chunk_func_params (Any): Additional parameters for the chunking function.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of chunked data keyed by computed hash IDs.
    """
    inserting_chunks: dict[str, dict[str, Any]] = {}

    new_docs_list = list(new_docs.items())
    docs = [doc["content"] for _, doc in new_docs_list]
    doc_keys = [doc_key for doc_key, _ in new_docs_list]

    # Initialize the encoder for the specified model
    ENCODER = tiktoken.encoding_for_model("gpt-4o")
    tokens = ENCODER.encode_batch(docs, num_threads=16)
    chunks = chunk_func(
        tokens=tokens,
        doc_keys=doc_keys,
        tiktoken_model=ENCODER,
        **chunk_func_params
    )

    for chunk in chunks:
        chunk_id = compute_mdhash_id(chunk["content"], prefix="chunk-")
        inserting_chunks[chunk_id] = chunk

    return inserting_chunks
