from ai4teaching import EmbeddingModel
from ai4teaching.utils import log, make_sure_directory_exists
import json
import os
import uuid
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

class DocumentProcessor:

    # Notion Processor
    STEP_FETCH_CONTENT_FROM_NOTION_API = "fetch_content_from_notion_api"
    STEP_MERGE_NOTION_BLOCKS = "merge_notion_blocks"

    # Video Processor
    STEP_EXTRACT_AUDIO_FROM_YOUTUBE = "extract_audio_from_youtube"
    STEP_TRANSCRIBE_AUDIO = "transcribe_audio"
    STEP_CREATE_TRANSCRIPT_SEGMENTS = "create_transcript_segments"

    # PDF Processor
    STEP_EXTRACT_TEXT_FROM_PDF = "extract_text_from_pdf"

    # All processors
    STEP_CREATE_DOCUMENT_CHUNKS = "create_document_chunks"
    STEP_EMBED_DOCUMENT_CHUNKS = "embed_document_chunks"

    # Summarize each chunk with GPT-3.5/4 to get a version to show to the user
    STEP_SUMMARIZE_DOCUMENT_CHUNKS = "summarize_document_chunks"

    def __init__(self, document, processed_documents_path, embedding_model: EmbeddingModel):
        # The document JSON object
        self.document = document

        # Generate document id if not exists yet
        if "id" not in self.document or self.document["id"] is None:
            self.document["id"] = uuid.uuid4().hex
        
        self.processed_documents_path = processed_documents_path

        assert "title" in self.document, ">title< not found in document"
        assert "document_uri" in self.document, ">document_uri< not found in document"
        
        self.step_ouput_files = {}
        self.embedding_model = embedding_model
        
    def process(self):
        return self.document
    
    def _create_document_chunks(self, previous_step_name=None):
        processing_required = self._prepare_and_check_if_processing_step_required(DocumentProcessor.STEP_CREATE_DOCUMENT_CHUNKS, previous_step_name=previous_step_name)
        
        if not processing_required:
            return
        
        # Read the result from the previous step
        previous_step_result = self._load_json_file_for_step(previous_step_name)

        chunk_size = 1000
        chunk_overlap_pct = 0.1

        text_splitter = CharacterTextSplitter(
            separator = "\n\n",
            chunk_size = chunk_size,
            chunk_overlap  = int(chunk_size * chunk_overlap_pct),
            length_function = len,
            is_separator_regex = False,
        )

        langchain_document = Document(page_content=previous_step_result["text"])
        langchain_document.metadata = previous_step_result["metadata"]
        splits = text_splitter.split_documents([langchain_document])

        chunks_document = { 
            "id" : self.document["id"],
            "document_uri" : self.document["document_uri"],
            "type"  : self.document["type"],
            "title" : self.document["title"],
            "metadata" : previous_step_result["metadata"] if "metadata" in previous_step_result else {},
            "chunks" : [] 
                        }
        
        for i, split in enumerate(splits):
            chunk = { 
                "chunk_id" : f"{chunks_document['id']}_{i}",
                "metadata" : split.metadata,
                "content" : split.page_content
            }

            chunks_document["chunks"].append(chunk)

        self._save_json_file_for_step(DocumentProcessor.STEP_CREATE_DOCUMENT_CHUNKS, chunks_document)
        
    def _embed_document_chunks(self, previous_step_name=None):

        processing_required = self._prepare_and_check_if_processing_step_required(DocumentProcessor.STEP_EMBED_DOCUMENT_CHUNKS, previous_step_name=previous_step_name)

        if not processing_required:
            return
    
        # Load chunks file
        chunks_document = self._load_json_file_for_step(DocumentProcessor.STEP_CREATE_DOCUMENT_CHUNKS)

        # Initialize summary JSON with mandatory fields
        embbeded_chunks_document = self._get_mandatory_document_data()

        # Add additional fields into existing JSON
        embbeded_chunks_document["chunks"] = chunks_document["chunks"]

        docs = [chunk["content"] for chunk in embbeded_chunks_document["chunks"]]
        embeds = self.embedding_model.embed(docs)

        # Add embeddings to chunks
        for i, chunk in enumerate(embbeded_chunks_document["chunks"]):
            chunk["embedding"] = embeds.data[i].embedding
        
        # Write to file
        self._save_json_file_for_step(DocumentProcessor.STEP_EMBED_DOCUMENT_CHUNKS, chunks_document)

    def _prepare_and_check_if_processing_step_required(self, step_name, previous_step_output_created_date=None, previous_step_name=None):
        
        # Create directory for the result of this step if not exists
        directory = os.path.join(self.processed_documents_path, step_name)
        make_sure_directory_exists(directory)

        file_ending = "mp4" if step_name == DocumentProcessor.STEP_EXTRACT_AUDIO_FROM_YOUTUBE else "json" 
        file_name = os.path.join(directory, f"{self._create_file_name(self.document['id'])}_{step_name}.{file_ending}")
        
        # Set the out file name for the step
        self.step_ouput_files[step_name] = file_name

        # Check if file exists
        if not os.path.isfile(file_name):
            log(f"Processing step >{step_name}< is required.", type="debug")
            return True
        
        # If previous step output created time is not None, check if the previous step is newer than the current step
        if previous_step_output_created_date is not None:
            
            # Get the create date of the current step
            current_step_output_create_date = os.path.getmtime(file_name)

            # Check if the previous step is newer than the current step
            if previous_step_output_created_date > current_step_output_create_date:
                log(f"Processing step >{step_name}< is required.", type="debug")
                return True
        
        # Check if the outfile's create date of the previous step is newer than the result of this step
        if previous_step_name is not None:
            previous_processing_output_file_name = self.document["processing_outputs"][previous_step_name]
           
            # Get the create date of the previous step
            previous_processing_output_file_create_date = os.path.getmtime(previous_processing_output_file_name)

            # Get the create date of the current step
            current_processing_output_file_create_date = os.path.getmtime(file_name)
            
            # Check if the previous step is newer than the current step
            if previous_processing_output_file_create_date > current_processing_output_file_create_date:
                log(f"Processing step >{step_name}< is required.", type="debug")
                return True

        log(f"Processing step >{step_name}< is not required.", type="debug")
    
    def _save_json_file_for_step(self, step_name, json_object):
        with open(f"{self.step_ouput_files[step_name]}", "w", encoding="utf-8") as json_file:
            json.dump(json_object, json_file, indent=4, ensure_ascii=False)

    def _load_json_file_for_step(self, step_name):
        with open(self.step_ouput_files[step_name], "r", encoding="utf-8") as json_file:
            file_json = json.load(json_file)
            
        # Check if the document contains an "id" field, as this is the unique identifier for the document
        assert("id" in file_json)
        # Check if the document contains a "type" field
        assert("type" in file_json)
    
        return file_json

    def _get_mandatory_document_data(self):

        # Make sure required fields are present
        assert "id" in self.document, ">id< not found in document"
        assert "document_uri" in self.document, ">document_uri< not found in document"
        assert "type" in self.document, ">type< not found in document"
        assert "title" in self.document, ">title< not found in document"

        return { 
            "id" : self.document["id"],
            "document_uri" : self.document["document_uri"],
            "type" : self.document["type"],
            "title": self.document["title"],
            "metadata" : {}
            }

    def _create_file_name(self, file_name):
        return file_name