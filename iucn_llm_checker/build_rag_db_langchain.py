from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma

PROJECT_ROOT = Path(__file__).resolve().parents[1]   
PDF_PATH = PROJECT_ROOT / "RL_Standards_Consistency.pdf"
PERSIST_DIR = PROJECT_ROOT / "rag_chroma"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"   
COLLECTION = "iucn_rl_standards"

def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")
    
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    
    loader = PyPDFLoader(str(PDF_PATH))
    docs = loader.load()  # one Document per page, metadata contains 'page'

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    splits = splitter.split_documents(docs)

    emb = FastEmbedEmbeddings(model_name=EMBED_MODEL)

    db = Chroma.from_documents(
        documents=splits,
        embedding=emb,
        collection_name=COLLECTION,
        persist_directory=str(PERSIST_DIR)
    )
    db.persist()
    print(f"Saved Chroma DB to: {PERSIST_DIR}")

if __name__ == "__main__":
    main()
