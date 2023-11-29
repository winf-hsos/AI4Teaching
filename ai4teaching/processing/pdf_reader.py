from ai4teaching import DocumentReader
from ai4teaching import log

class PDFReader(DocumentReader):
    def __init__(self):
        super().__init__()
        self.step_name = "read_from_pdf"
        self.original_document_type = "pdf_file"
    
    def read(self, pdf_uri):
        log(f"Reading text from >{pdf_uri}<", type="debug")

        # File or URL?
        # TODO: Implement URL
        pdf_file = pdf_uri

        # Read the text from the file using unstructured library
        from unstructured.partition.auto import partition
        elements = partition(filename=pdf_file)
        all_elements = self._process_elements(elements)

        output_json = self._get_json_output_template(pdf_uri, self.original_document_type, self.step_name)
        output_json["text"] = self._get_text_from_relevant_elements(all_elements)
        output_json["all_elements"] = all_elements
        output_json["metadata"]["file_size_in_kb"] = self._get_file_size_in_kb(pdf_file)
        output_json["metadata"]["created"] = self._get_created_date(pdf_file)
        output_json["metadata"]["last_edited"] = self._get_last_edited(pdf_file)
        
        return output_json

    def _process_elements(self, elements):
        processed_elements = []


        for element in elements:
            processed_element = { "text" : f"{element}", "type" : type(element).__name__ }
            processed_elements.append(processed_element)

        return processed_elements

    def _get_text_from_relevant_elements(self, all_elements):
        relevant_elements = ["Title", "Text", "NarrativeText"]
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