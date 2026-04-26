# src/memory/vector_store.py
import chromadb
import uuid
import datetime
import os
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Use in-memory client on Streamlit Cloud, persistent locally
# Streamlit Cloud sets the STREAMLIT_SHARING_MODE environment variable
def _get_chroma_client():
    is_cloud = os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('HOME') == '/home/adminuser'
    if is_cloud:
        print('Using in-memory Chroma (cloud environment)')
        return chromadb.EphemeralClient()
    else:
        print('Using persistent Chroma (local environment)')
        return chromadb.PersistentClient(path='./data/chroma')

chroma_client = _get_chroma_client()

memory_collection = chroma_client.get_or_create_collection(
    name='research_memory'
)

def add_memory(text: str, category: str = 'CONVERSATION', metadata: dict = {}):
    '''Add a piece of information to semantic memory'''
    try:
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
    except Exception as e:
        print(f'Memory add failed (non-critical): {e}')

def search_memory(query: str, n_results: int = 5) -> list:
    '''Find the most relevant memories for a given query'''
    try:
        query_embedding = embedding_model.encode(query).tolist()
        results = memory_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        if results['documents'] and results['documents'][0]:
            return results['documents'][0]
        return []
    except Exception as e:
        print(f'Memory search failed (non-critical): {e}')
        return []

def build_memory_context(query: str) -> str:
    '''Build a memory context block to inject before AI response'''
    memories = search_memory(query)
    if not memories:
        return ''
    memory_block = 'RELEVANT MEMORIES FROM PREVIOUS SESSIONS:\n'
    for i, mem in enumerate(memories, 1):
        memory_block += f'{i}. {mem}\n'
    return memory_block