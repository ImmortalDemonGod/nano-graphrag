# /Volumes/Totallynotaharddrive/nano-graphrag/nano_graphrag/chunking.py

from collections.abc import Callable
from typing import Any

import tiktoken

from ._splitter import SeparatorSplitter
from ._utils import compute_mdhash_id
from .prompt import PROMPTS  # Ensure PROMPTS is defined in constants.py


def chunking_by_token_size(
    tokens_list: list[list[int]],
    doc_keys,
    tiktoken_model,
    overlap_token_size=128,
    max_token_size=1024,
):

    results = []
    for index, tokens in enumerate(tokens_list):
        chunk_token = []
        lengths = []
        for start in range(0, len(tokens), max_token_size - overlap_token_size):

            chunk_token.append(tokens[start : start + max_token_size])
            lengths.append(min(max_token_size, len(tokens) - start))

        # here somehow tricky, since the whole chunk tokens is list[list[list[int]]] for corpus(doc(chunk)),so it can't be decode entirely
        chunk_token = tiktoken_model.decode_batch(chunk_token)
        for i, chunk in enumerate(chunk_token):

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
    doc_keys,
    tiktoken_model,
    overlap_token_size=128,
    max_token_size=1024,
):

    splitter = SeparatorSplitter(
        separators=[
            tiktoken_model.encode(s) for s in PROMPTS["default_text_separator"]
        ],
        chunk_size=max_token_size,
        chunk_overlap=overlap_token_size,
    )
    results = []
    for index, tokens in enumerate(tokens_list):
        chunk_token = splitter.split_tokens(tokens)
        lengths = [len(c) for c in chunk_token]

        # here somehow tricky, since the whole chunk tokens is list[list[list[int]]] for corpus(doc(chunk)),so it can't be decode entirely
        chunk_token = tiktoken_model.decode_batch(chunk_token)
        for i, chunk in enumerate(chunk_token):

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
