import chromadb
import chromadb.config
from bluechat import VectorDB
from bluechat.utils import log

class ChromaDB(VectorDB):
    def __init__(self, path, embedding_model, reset=True):
        super().__init__(embedding_model)
        self.client = chromadb.PersistentClient(path=path, settings=chromadb.config.Settings(allow_reset=True))
        if reset == True:
            self.client.reset()

    def add_embedded_document_chunks(self, embedded_chunks_file_name, collection_name="documents"):

        import json
        with open(embedded_chunks_file_name, encoding="utf-8") as embedded_chunks_file:
            embedded_chunks = json.load(embedded_chunks_file)

        num_chunks = len(embedded_chunks["chunks"])
        if num_chunks == 0:
            log(f"No chunks found in >{embedded_chunks_file_name}<, skipping adding to ChromaDB", type="warning")
            return
        
        log(f"Adding {num_chunks} chunks from >{embedded_chunks_file_name}< to ChromaDB", type="info")

        collection = self._get_collection(collection_name)
        
        for chunk in embedded_chunks["chunks"]:
            collection.add(
                documents=[chunk["content"]],
                embeddings=[chunk["embedding"]],
                metadatas=[chunk["metadata"]],
                ids=[chunk["chunk_id"]]
                )

    def _get_collection(self, collection_name):
        collections = self.client.list_collections()
        collection_names = [collection.name for collection in collections]

        if collection_name in collection_names:
            collection = self.client.get_collection(collection_name)
        else:
            collection = self.client.create_collection(collection_name)

        return collection
            
    def get_documents_count(self, collection_name="documents"):
        collection = self._get_collection(collection_name)
        content = collection.get()
        return len(content["ids"])
    
    def get_documents(self, collection_name="documents"):
        collection = self._get_collection(collection_name)
        content = collection.get()
        return content
    
    def query(self, query_prompt, n_results=2, collection_name="documents"):
          query_prompt_embedding = self.embedding_model.embed(query_prompt).data[0].embedding

          collection = self._get_collection(collection_name)

          results = collection.query(
               query_embeddings=[query_prompt_embedding],
               n_results=n_results,
               include=["distances", "documents", "metadatas"]
          ) 
          return results
