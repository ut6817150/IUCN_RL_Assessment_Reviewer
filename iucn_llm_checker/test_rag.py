from pathlib import Path
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma

PROJECT_ROOT = Path(__file__).resolve().parent  # repo root: IUCN_Reviewer/
PERSIST_DIR = PROJECT_ROOT / "rag_chroma"
COLLECTION = "iucn_rl_standards"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

db = Chroma(
    collection_name=COLLECTION,
    persist_directory=str(PERSIST_DIR),
    embedding_function=FastEmbedEmbeddings(model_name=EMBED_MODEL),
)

hits = db.similarity_search("Preferred spelling grey colour centre", k=3)
for i, d in enumerate(hits, 1):
    print(f"\n--- HIT {i} (page={d.metadata.get('page')}) ---\n{d.page_content[:400]}")
