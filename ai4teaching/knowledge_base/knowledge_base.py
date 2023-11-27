import json
import os
from ai4teaching import log
from ai4teaching import EmbeddingModel
from ai4teaching import LargeLanguageModel
from ai4teaching import DocumentProcessor

class KnowledgeBase:
    
    def __init__(self, index_file_name, embedding_model: EmbeddingModel, llm: LargeLanguageModel):
        self.embedding_model = embedding_model
        self.llm = llm

        self._setup(index_file_name)

    def _setup(self, index_file_name):
        with open(index_file_name, encoding="utf-8") as index_file:
            self.index_file = os.path.abspath(index_file.name)
            self.index_directory = os.path.dirname(self.index_file)
            self.index = json.load(index_file)
        
        # Iterate through all documents in the index and check if they are processed
        if "documents" not in self.index:
            log(f"Knowledge base index does not contain documents. Adding empty list.", type="warning")
            self.index["documents"] = []

        index_documents = self.index["documents"]
        
        # Process the documents in the index (steps are only performed if necessary)
        for document in index_documents:
            document = self._process_document(document)
        
        # Save the index file back to disk
        self._save_index()
        
    def _save_index(self):
        with open(self.index_file, "w", encoding="utf-8") as index_file:
            json.dump(self.index, index_file, indent=4, ensure_ascii=False)
   
    '''
    Check if the output files for a given process step exist.
    Return the list of files if they exist, otherwise return an empty list
    '''
    def _get_output_files_for_process_step(self, step_name):
        output_files = []
        for document in self.index["documents"]:
            if "status" in document:
                if document["status"] == "inactive":
                    continue
            if "processing_outputs" in document:
                if step_name in document["processing_outputs"]:
                    output_files.append(document["processing_outputs"][step_name])
                else:
                    log(f"Knowledge base processing outputs does not contain output for step >{step_name}<", type="warning")
        return output_files
    
    def _get_output_file_for_process_step_and_document_id(self, step_name, document_id):
        # TODO: For this work, all output files need to include the document id
        # TODO: Check for exceptions, such as MP4 files
        # TODO: Does it make sense to include the document id in the output file name? --> Yes    
        pass
    
    def _process_document(self, document):
        if "status" in document:
            if document["status"] == "inactive":
                log(f"Skipping document >{document['title']}< because it is inactive", type="info")
                return document
        
        # Check if processing outputs are present
        if "processing_outputs_path" not in self.index:
            # Get the absolute path of the index_file and add subdirectory "outputs"
            import os
            processing_outputs_path = os.path.join(self.index_directory, "outputs")
            log(f"Knowledge base index does not contain processing outputs path. Adding >{processing_outputs_path}< string.", type="warning")
            self.index["processing_outputs_path"] = processing_outputs_path

        type = document["type"]
        if type == "text/plain":
            return self._process_text_document(document)
        elif type == "video/youtube":
            return self._process_youtube_video(document)
        elif type == "notion/page":
            return self._process_notion_page(document)

    def _process_text_document(self, document, processed_documents_path):
        pass

    def _process_youtube_video(self, document):
        from ai4teaching import VideoProcessor
        processor = VideoProcessor(document, self.index["processing_outputs_path"], self.embedding_model, self.llm)
        processed_document = processor.process()
        return processed_document
    
    def _process_notion_page(self, document):
        from ai4teaching import NotionProcessor
        processor = NotionProcessor(document, self.index["processing_outputs_path"], self.embedding_model)
        processed_document = processor.process()
        return processed_document
        
    def get_embedded_chunks_files(self):
        return self._get_output_files_for_process_step(DocumentProcessor.STEP_EMBED_DOCUMENT_CHUNKS)

    def get_documents(self):
        active_documents = []
        for doc in self.index["documents"]:
            if "status" in doc:
                if doc["status"] == "inactive":
                    continue
            active_documents.append(doc)
            
        return active_documents

    def get_documents_by_type(self, type):
        documents = []
        for doc in self.index["documents"]:
            if doc["type"] == type:
                documents.append(doc)
        return documents

    ''' 
    Lookup the summary for a chunk_id in the summary file of the corresponding document
    '''
    def get_summary_for_chunk_id(self, chunk_id):
        document_id = chunk_id.split("_")[0]
        
        # Get document to get the summary file
        document = self.get_document_by_id(document_id)

        if DocumentProcessor.STEP_SUMMARIZE_DOCUMENT_CHUNKS not in document["processing_outputs"]:
            log(f"Summary file for document >{document_id}< not found in database index", type="warning")
            return None

        summary_file = document["processing_outputs"][DocumentProcessor.STEP_SUMMARIZE_DOCUMENT_CHUNKS]
        
        # If the path is in the index, check wether the file exists
        from pathlib import Path
        summary_file = Path(summary_file)
        if not summary_file.is_file():
            log(f"Summary file >{summary_file}< not found on disk", type="error")
            return None
        
        # Open summary file and get the summary for the chunk_id
        with open(summary_file, "r", encoding="utf-8") as json_file:
            summary_document = json.load(json_file)
            for chunk in summary_document["content"]:
                if chunk["chunk_id"] == chunk_id:
                    return chunk["summary"]

    '''
    Lookup the document in the database index by its id
    The documents contains the URI to all processing outputs
    '''
    def get_document_by_id(self, document_id):
        for document in self.index["documents"]:
            if document["id"] == document_id:
                return document

    '''
    Add and process (if necessary) a YouTube video to the knowledge base

    TODO: This should only add to index, not process. Separate function "process_all" to check if
    processing is necessary and process all documents in the index
    '''
    def add_youtube_video(self, youtube_url):

        log(f"Adding YouTube video >{youtube_url}< to knowledge base", type="info")

        # Get video metadata
        from pytube import YouTube
        yt = YouTube(youtube_url)

        title = yt.title.replace("?", "")

        document = {
            "title" : title,
            "document_uri" : youtube_url,
            "youtube_id" : yt.video_id,
            "type" : "video/youtube"
        }
        
        #processed_document = self._process_youtube_video(document)
        self.index["documents"].append(document)

        # Save the index file back to disk
        self._save_index()
    
    ''' 
    This function checks wether processing for any document in the index is necessary
    and performs the processing if necessary
    '''
    def prcoess_all(self):
        pass