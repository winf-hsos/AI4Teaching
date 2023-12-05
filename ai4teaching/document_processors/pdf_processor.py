from ai4teaching import DocumentProcessor
from ai4teaching import EmbeddingModel
from ai4teaching.utils import log

class PDFProcessor(DocumentProcessor):
    def __init__(self, document, processed_documents_path, embedding_model: EmbeddingModel):
        log("Initializing PDFProcessor")

        super().__init__(document, processed_documents_path, embedding_model)

    def process(self):
        log(f"Processing PDF from >{self.document['document_uri']}<", type="info")

        self._extract_text_from_pdf()

        self._create_document_chunks(DocumentProcessor.STEP_EXTRACT_TEXT_FROM_PDF)

        self._embed_document_chunks(DocumentProcessor.STEP_CREATE_DOCUMENT_CHUNKS)

        self.document["processing_outputs"] = self.step_ouput_files

        log(f"✔ Done processing PDF from >{self.document['document_uri']}<", type="success")
        return self.document
    
    def _extract_text_from_pdf(self):
        processing_required = self._prepare_and_check_if_processing_step_required(
            DocumentProcessor.STEP_EXTRACT_TEXT_FROM_PDF, 
            previous_step_output_created_date=self._get_last_edited_time(self.document["document_uri"])
        )

        if not processing_required:
            return
        
        # Initialize summary JSON with mandatory fields
        pdf_document = self._get_mandatory_document_data()

        # Add additional fields to exsitng JSON
        pdf_document["metadata"]["pdf_file"] = self.document["document_uri"]

        # Get and add text blocks from Notion document
        pdf_text_elements = self._get_text_elements_from_pdf(self.document["document_uri"])

        pdf_document["text"] = self._get_text_from_relevant_elements(pdf_text_elements)
        pdf_document["content"] = pdf_text_elements
        
        # Save output to file
        self._save_json_file_for_step(DocumentProcessor.STEP_EXTRACT_TEXT_FROM_PDF, pdf_document)

    def _get_text_elements_from_pdf(self, pdf_file):
        # Read the text from the file using unstructured library
        from unstructured.partition.auto import partition
        elements = partition(filename=pdf_file)
        all_elements = self._process_elements(elements, pdf_file)
        return all_elements
    
    def _get_text_from_relevant_elements(self, all_elements):
        relevant_elements = ["Title", "Text", "NarrativeText", "ListItem"]
        text = ""
        for element in all_elements:
            if element["type"] in relevant_elements:
                if element["type"] == "Title":
                    text += f"# {element['text']}\n\n"
                if element["type"] in ["NarrativeText", "Text"]:
                    text += f"{element['text']}\n\n"
            else:
                log(f"Skipping element of type >{element['type']}<", type="debug")
        return text

    def _process_elements(self, elements, pdf_file):
        processed_elements = []

        # Get the file name without the path
        import os
        pdf_file_name = os.path.basename(pdf_file)

        for element in elements:

            processed_element = { "text" : f"{element}", "type" : type(element).__name__, "metadata" : { "pdf_file_name" : pdf_file_name} }
            processed_elements.append(processed_element)

        return processed_elements

    def _get_last_edited_time(self, file):
        import os
        from datetime import datetime
        return os.path.getmtime(file)