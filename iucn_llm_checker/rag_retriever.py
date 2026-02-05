from pathlib import Path
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma

SCRIPT_DIR = Path(__file__).resolve().parent.parent  # IUCN_Reviewer/
PERSIST_DIR = SCRIPT_DIR / "rag_chroma"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION = "iucn_rl_standards"  # consistent with collection in build_rag_db_langchain.py

_emb = FastEmbedEmbeddings(model_name=EMBED_MODEL)
_db = Chroma(
    collection_name=COLLECTION,
    persist_directory=str(PERSIST_DIR),
    embedding_function=_emb,
)

def retrieve_context(query: str, top_k: int = 4) -> str:
    hits = _db.similarity_search(query, k=top_k)
    blocks = []
    for d in hits:
        page = d.metadata.get("page", "NA")
        blocks.append(f"[Source: RL_Standards_Consistency | page={page}]\n{d.page_content}")
    return "\n\n---\n\n".join(blocks)
