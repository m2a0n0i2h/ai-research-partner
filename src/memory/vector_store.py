# src/memory/vector_store.py
import chromadb
import uuid
import datetime
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

chroma_client = chromadb.PersistentClient(path='./data/chroma')

memory_collection = chroma_client.get_or_create_collection(
    name='research_memory'
)

def add_memory(text: str, category: str = 'CONVERSATION', metadata: dict = {}):
    embedding = embedding_model.encode(text).tolist()
    memory_collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[{
            'category': category,
            'date': str(datetime.date.today()),
            **metadata
        }],
        ids=[str(uuid.uuid4())]
    )

def search_memory(query: str, n_results: int = 5) -> list:
    query_embedding = embedding_model.encode(query).tolist()
    results = memory_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    if results['documents'] and results['documents'][0]:
        return results['documents'][0]
    return []

def build_memory_context(query: str) -> str:
    memories = search_memory(query)
    if not memories:
        return ''
    memory_block = 'RELEVANT MEMORIES FROM PREVIOUS SESSIONS:\n'
    for i, mem in enumerate(memories, 1):
        memory_block += f'{i}. {mem}\n'
    return memory_block