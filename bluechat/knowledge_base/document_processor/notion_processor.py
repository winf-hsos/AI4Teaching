from bluechat import DocumentProcessor
from bluechat import EmbeddingModel
from bluechat.utils import log
from datetime import datetime
import requests

class NotionProcessor(DocumentProcessor):
    def __init__(self, document, processed_documents_path, embedding_model: EmbeddingModel):
        log("Initializing NotionProcessor")

        # Fetch title so that we name files
        assert "notion_page_block_id" in document, ">notion_page_block_id< not found in document"
        
        self.notion_api_key = document["notion_api_key"]
        document["title"] = self._get_title_by_notion_page_id(document["notion_page_block_id"])

        super().__init__(document, processed_documents_path, embedding_model)
        
        
    def process(self):
        log(f"Processing notion pages from >{self.document['document_uri']}<", type="info")

        self._fetch_content_from_notion_api()

        self._merge_notion_blocks()

        self._create_document_chunks(DocumentProcessor.STEP_MERGE_NOTION_BLOCKS)

        self._embed_document_chunks(DocumentProcessor.STEP_CREATE_DOCUMENT_CHUNKS)

        self.document["processing_outputs"] = self.step_ouput_files

        log(f"✔ Done processing notion pages from >{self.document['document_uri']}<", type="success")
        return self.document

    def _fetch_content_from_notion_api(self):
        processing_required = self._prepare_and_check_if_processing_step_required(
            DocumentProcessor.STEP_FETCH_CONTENT_FROM_NOTION_API, 
            previous_step_output_created_date=self._get_last_edited_time(self.document["notion_page_block_id"])
        )

        if not processing_required:
            return
        
        # Initialize summary JSON with mandatory fields
        notion_document = self._get_mandatory_document_data()

        # Add additional fields to exsitng JSON^
        notion_document["metadata"]["notion_page_block_id"] = self.document["notion_page_block_id"]

        # Get and add text blocks from Notion document
        notion_text_blocks = self._get_text_blocks_by_notion_page_id(self.document["notion_page_block_id"])
        notion_document["content"] = notion_text_blocks
        
        # Save output to file
        self._save_json_file_for_step(DocumentProcessor.STEP_FETCH_CONTENT_FROM_NOTION_API, notion_document)
    
    def _merge_notion_blocks(self):
        processing_required = self._prepare_and_check_if_processing_step_required(DocumentProcessor.STEP_MERGE_NOTION_BLOCKS, previous_step_name=DocumentProcessor.STEP_FETCH_CONTENT_FROM_NOTION_API)

        if not processing_required:
            return
        
        # Load chunks file
        notion_document = self._load_json_file_for_step(DocumentProcessor.STEP_FETCH_CONTENT_FROM_NOTION_API)

        # Add additional fields into existing JSON
        merged_notion_document = notion_document.copy()
        merged_notion_document["content"] = []

        # Merge blocks
        merged_block = ""
        for block in notion_document["content"]:
            merged_block += f'{block["text"]}\n'
        
        merged_notion_document["content"].append(
            {
                "text" : merged_block, 
                "metadata" : { "type" : "notion", "notion_page_id" : notion_document["metadata"]["notion_page_block_id"] } 
            }
            )

        # Save output to file
        self._save_json_file_for_step(DocumentProcessor.STEP_MERGE_NOTION_BLOCKS, merged_notion_document)

    def _get_last_edited_time(self, block_id):
        url = f'https://api.notion.com/v1/pages/{block_id}'

        headers = {
            'Notion-Version': '2022-06-28',
            'Authorization': f'Bearer {self.notion_api_key}',
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            resp_json = response.json()
            last_edited_time = datetime.fromisoformat(resp_json["last_edited_time"])
            timestamp = last_edited_time.timestamp()
            return timestamp
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
            return "ERROR"

    def _get_title_by_notion_page_id(self, block_id):
        url = f'https://api.notion.com/v1/pages/{block_id}'

        headers = {
            'Notion-Version': '2022-06-28',
            'Authorization': f'Bearer {self.notion_api_key}',
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            resp_json = response.json()
            return resp_json["properties"]["title"]["title"][0]["plain_text"]
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
            return "ERROR"

    def _get_text_blocks_by_notion_page_id(self, block_id):
        #block_id = "8fed511c-977d-4ed2-b055-2e45fa9b7583"
        url = f'https://api.notion.com/v1/blocks/{block_id}/children?page_size=100'
        #print(url)
        
        headers = {
            'Notion-Version': '2022-06-28',
            'Authorization': f'Bearer {self.notion_api_key}',
        }

        response = requests.get(url, headers=headers)

        notion_text_blocks = []
        if response.status_code == 200:
            # You can access the response content using response.text or response.json()
            resp_json = response.json()
            for block in resp_json["results"]:

                #print(f"Processing block of type >{block['type']}<")
                #print(block)

                # TODO: Do we need other block types?
                if block["type"] in ["paragraph", "bulleted_list_item", "numbered_list_item", "heading_1", "heading_2", "heading_3"]:
                    plain = ""

                    print(block["type"])
                    for rt in block[block["type"]]["rich_text"]:
                        plain += rt["plain_text"]         
                    
                    prefixes = { "paragraph" : "", "bulleted_list_item" : "- ", "numbered_list_item" : "- ", "heading_1" : "# ", "heading_2" : "## ", "heading_3" : "### " }
                    notion_text_blocks.append({"text" : f"{prefixes[block['type']]}{plain}\n", "metadata" : { "type" : block["type"], "block_id" : block["id"] }})
                    
            
            return notion_text_blocks
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
            return "ERROR"