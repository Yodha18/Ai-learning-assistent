import re
from typing import List


def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace and normalizing."""
    # Remove multiple consecutive spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove multiple consecutive newlines
    text = re.sub(r'\n+', '\n', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def chunk_text_by_tokens(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """
    Split text into chunks based on approximate token count.
    
    Args:
        text: The text to chunk
        chunk_size: Approximate number of tokens per chunk
        overlap: Number of tokens to overlap between chunks
    
    Returns:
        List of text chunks
    """
    # Simple approximation: 1 token ≈ 4 characters
    char_chunk_size = chunk_size * 4
    char_overlap = overlap * 4
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + char_chunk_size
        
        # Try to break at a sentence boundary
        if end < text_length:
            # Look for sentence endings within the last 100 characters
            sentence_end = text.rfind('.', end - 100, end)
            if sentence_end != -1:
                end = sentence_end + 1
            else:
                # Look for other punctuation
                for punct in ['!', '?', '\n']:
                    punct_end = text.rfind(punct, end - 50, end)
                    if punct_end != -1:
                        end = punct_end + 1
                        break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - char_overlap
        
        # Ensure we're making progress
        if start <= end - char_chunk_size:
            start = end
    
    return chunks


def chunk_text_by_sentences(text: str, sentences_per_chunk: int = 5) -> List[str]:
    """
    Split text into chunks based on sentences.
    
    Args:
        text: The text to chunk
        sentences_per_chunk: Number of sentences per chunk
    
    Returns:
        List of text chunks
    """
    # Split by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    
    for sentence in sentences:
        current_chunk.append(sentence)
        if len(current_chunk) >= sentences_per_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks