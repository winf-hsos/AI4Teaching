from ai4teaching import DocumentReader
from ai4teaching import log

class TextReader(DocumentReader):
    def __init__(self):
        super().__init__()
        self.step_name = "read_from_text"
        self.original_document_type = "text_file"
    
    def read(self, txt_uri):
        log(f"Reading text from >{txt_uri}<", type="debug")

        # File or URL?
        # TODO: Implement URL
        txt_file = txt_uri
        
        # Read the text from the file
        with open(txt_file, "r") as f:
            text = f.read()

        output_json = self._get_json_output_template(txt_uri, self.original_document_type, self.step_name)
        output_json["text"] = text
        output_json["metadata"]["file_size_in_kb"] = self._get_file_size_in_kb(txt_file)
        output_json["metadata"]["created"] = self._get_created_date(txt_file)
        output_json["metadata"]["last_edited"] = self._get_last_edited(txt_file)

        return output_json
    
    

        


