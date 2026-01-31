from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

class RAGService:
    def __init__(self, db_path="backend/data/vector_store", doc_path="backend/database/book.pdf"):
        self.db_path = db_path
        self.doc_path = doc_path
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self._initialize_db()

    def _initialize_db(self):
        """
        Initialize ChromaDB. If persistent interaction exists, load it.
        Otherwise, index the PDF document.
        """
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            print(f"Loading existing Vector Store from {self.db_path}")
            self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embedding_function)
        else:
            print(f"Creating new Vector Store from {self.doc_path}")
            if not os.path.exists(self.doc_path):
                print(f"WARNING: Document {self.doc_path} not found. RAG will be empty.")
                return

            loader = PyPDFLoader(self.doc_path)
            documents = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            
            self.vector_store = Chroma.from_documents(
                documents=chunks, 
                embedding=self.embedding_function, 
                persist_directory=self.db_path
            )
            print("Vector Store created and persisted.")

    def search(self, query, k=3):
        """
        Retrieve top-k relevant documents for the query.
        """
        if not self.vector_store:
            return "No knowledge base available."
            
        results = self.vector_store.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])

rag_service = RAGService()
