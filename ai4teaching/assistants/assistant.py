import os
import json
from ai4teaching.utils import log

class Assistant:
    def __init__(self, config_file, depending_on_assistant=None):
        self.config_file = config_file

        # Validate expected properties in config file
        expected_properties = ["assistant_type", "assistant_name"]
        self._check_if_expected_properties_exist_in_config(expected_properties)
        
        self.root_path = os.path.dirname(os.path.abspath(config_file)) if config_file is not None else ""
        self.depending_on_assistant = depending_on_assistant
        self._setup()
    
    def _setup(self):
        
        if "embedding_model" in self.config:
            if self.config["embedding_model"] == "text-embedding-ada-002":
                # Set up the embedding model
                from ai4teaching import EmbeddingModel
                self.embedding_model = EmbeddingModel()
            else:
                log(f"Unsupported embedding model '{self.config['embedding_model']}'.", type="error")

        if "large_language_model" in self.config:
            if self.config["large_language_model"] in ["gpt-3.5-turbo-1106", "gpt-4-1106-preview"]:
                # Set up the large language model
                from ai4teaching import LargeLanguageModel
                self.llm = LargeLanguageModel(model_name=self.config["large_language_model"])
            else:
                log(f"Unsupported large language model '{self.config['large_language_model']}'.", type="error")

        # Reference the knowledge base and vector database, if this assistant depends on another assistant
        if self.depending_on_assistant is not None:
            # Reference the knowledge base and vector database from the depending assistant
            self.knowledge_base = self.depending_on_assistant.knowledge_base
            self.vector_db = self.depending_on_assistant.vector_db
            return

        # Set up the knowledge base
        if "knowledge_base" in self.config:
            knowledge_base_index_file = self.config["knowledge_base"]["index_file"]
            from ai4teaching import KnowledgeBase
            self.knowledge_base = KnowledgeBase(knowledge_base_index_file, self.embedding_model, self.llm)

         # Set up the vector database
        if "vector_db" in self.config:
            vector_db_type = self.config["vector_db"]["type"]
            vector_db_path = self.config["vector_db"]["path"]
            if vector_db_type == "chromadb":
                from ai4teaching import ChromaDB
                self.vector_db = ChromaDB(vector_db_path, self.embedding_model, reset=True)
            
            embedded_chunks_file_list = self.knowledge_base.get_embedded_chunks_files()
            for embedded_chunks_file in embedded_chunks_file_list:
                self.vector_db.add_embedded_document_chunks(embedded_chunks_file)
            
            log(f"Added {self.vector_db.get_documents_count()} document chunks to {vector_db_type}.", type="success")

    def _check_if_expected_properties_exist_in_config(self, expected_properties):
        # Read the config JSON file
        with open(self.config_file, encoding="utf-8") as config_file:
            self.config = json.load(config_file)

        for property in expected_properties:
            if property not in self.config:
                log(f"Property '{property}' not found in config file '{self.config_file}'.", type="warning")


    def get_list_of_knowledge_base_documents(self):
        if self.knowledge_base is None:
            log(f"Assistant does not have a knowledge base.", type="warning")
            return None
        
        return self.knowledge_base.get_documents()
    
    def who_are_you(self):
        return {
            "assistant_type": self.config['assistant_type'],
            "assistant_name": self.config['assistant_name']
        }
    
    def get_list_of_vector_db_documents(self):
        if self.vector_db is None:
            log(f"Assistant does not have a vector database.", type="warning")
            return None
        
        return self.vector_db.get_documents()