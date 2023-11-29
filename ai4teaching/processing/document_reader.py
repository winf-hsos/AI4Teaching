from ai4teaching import log
import magic
import os
from datetime import datetime

class DocumentReader:
    def __init__(self):
        pass

    def read(self, input_uri):
        pass

    def get_mime_type(self, file):
        # Check if file exists
        if not os.path.isfile(file):
            raise FileNotFoundError(f"Input file >{file}< does not exist")

        # Check the mime type of the file
        mime_type = magic.from_file(file, mime=True)

        return mime_type
    
    def _get_json_output_template(self, document_uri, original_document_type, step_name):
        return {
            "uri": document_uri,
            "read_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "original_document_type": original_document_type,
            "step_name": step_name,
            "metadata": {},
            "text": ""
        }
    
    def _get_file_size_in_kb(self, file):
        import os
        return os.path.getsize(file) / 1024
    
    def _get_created_date(self, file):
        import os
        from datetime import datetime
        return datetime.fromtimestamp(os.path.getctime(file)).strftime("%Y-%m-%d %H:%M:%S")

    def _get_last_edited(self, file):
        import os
        from datetime import datetime
        return datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d %H:%M:%S")

        