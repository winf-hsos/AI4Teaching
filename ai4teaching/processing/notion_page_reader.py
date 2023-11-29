from ai4teaching import log
from ai4teaching import DocumentReader
import requests
from datetime import datetime

class NotionPageReader(DocumentReader):
    def __init__(self):
        super().__init__()
        self.step_name = "notion_page_reader"
        self.original_document_type = "notion_page"
        self.notion_api_key = None

    def read(self, notion_page_url):
        # Check if API key is set
        if self.notion_api_key is None:
            log(f"Please set the Notion API key first using the set_notion_api_key() method", type="error")
            return

        log(f"Reading content from notion page >{notion_page_url}<", type="debug")

        # Extract block id from notion page url
        notion_page_block_id = self._extract_notion_page_block_id(notion_page_url)
        log(f"Extracted notion page block id >{notion_page_block_id}<", type="debug")

        # Fetch all blocks from the Notion API
        all_blocks = self._get_all_blocks_from_notion_page(notion_page_block_id)

        # Extract only text content blocks from Notion API
        text_blocks = self._filter_blocks_and_extract_text(all_blocks)
        
        # Merge text blocks into one string
        markdown_string = self._merge_text_blocks_to_markdown(text_blocks)

        output_json = self._get_json_output_template(notion_page_url, self.original_document_type, self.step_name)

        output_json["all_blocks"] = all_blocks
        output_json["text_blocks"] = text_blocks
        output_json["text"] = markdown_string
        output_json["metadata"]["notion_page_block_id"] = notion_page_block_id
        output_json["metadata"]["notion_page_url"] = notion_page_url
        output_json["metadata"] = output_json["metadata"] | self._get_notion_page_title_and_last_edit(notion_page_block_id)
        
        return output_json

    def set_notion_api_key(self, notion_api_key):
        self.notion_api_key = notion_api_key
        
    def _extract_notion_page_block_id(self, notion_page_url):
        # Extract block id from notion page url
        notion_page_block_id = notion_page_url.split("-")[-1]

        # Insert dashes
        notion_page_block_id = notion_page_block_id[:8] + "-" + notion_page_block_id[8:12] + "-" + notion_page_block_id[12:16] + "-" + notion_page_block_id[16:20] + "-" + notion_page_block_id[20:]

        return notion_page_block_id

    def _get_all_blocks_from_notion_page(self, block_id):
        url = f'https://api.notion.com/v1/blocks/{block_id}/children?page_size=1000'
        headers = {
            'Notion-Version': '2022-06-28',
            'Authorization': f'Bearer {self.notion_api_key}',
        }

        response = requests.get(url, headers=headers)

        notion_blocks = []
        if response.status_code == 200:
            resp_json = response.json()
            for block in resp_json["results"]:
                notion_blocks.append(block)

                if block["has_children"]:
                        children = self._get_all_blocks_from_notion_page(block["id"])
                        notion_blocks.extend(children)

            return notion_blocks
        else:
            log(f"Request failed with status code {response.status_code}: {response.text}", type="error")
            return

    def _filter_blocks_and_extract_text(self, blocks):
        
        text_blocks = []
        for block in blocks:
            # TODO: Do we need other block types?
            if block["type"] in ["paragraph", "bulleted_list_item", "numbered_list_item", "heading_1", "heading_2", "heading_3"]:
                plain = ""
                for rt in block[block["type"]]["rich_text"]:
                    plain += rt["plain_text"]         
                
                prefixes = { "paragraph" : "", "bulleted_list_item" : "- ", "numbered_list_item" : "- ", "heading_1" : "# ", "heading_2" : "## ", "heading_3" : "### " }
                text_blocks.append({"text" : f"{prefixes[block['type']]}{plain}\n", "metadata" : { "type" : block["type"], "block_id" : block["id"] }})
        
        return text_blocks
    
    def _merge_text_blocks_to_markdown(self, text_blocks):

        markdown_string = ""
        for block in text_blocks:

            if block["metadata"]["type"] != "numbered_list_item":
                numbered_list_item = 0

            if block["metadata"]["type"] == "paragraph":
                markdown_string += f"{block['text']}\n"
            elif block["metadata"]["type"] == "bulleted_list_item":
                markdown_string += f"- {block['text']}"
            elif block["metadata"]["type"] == "numbered_list_item":
                if numbered_list_item == 0:
                    numbered_list_item = 1
                else:
                    numbered_list_item += 1
                markdown_string += f"{numbered_list_item}. {block['text']}"
            elif block["metadata"]["type"] == "heading_1":
                markdown_string += f"# {block['text']}"
            elif block["metadata"]["type"] == "heading_2": 
                markdown_string += f"## {block['text']}"
            elif block["metadata"]["type"] == "heading_3":
                markdown_string += f"### {block['text']}"
            else:
                log(f"Unknown block type >{block['metadata']['type']}<", type="error")
                return

        return markdown_string
    
    def _get_notion_page_title_and_last_edit(self, notion_page_block_id):
        url = f'https://api.notion.com/v1/pages/{notion_page_block_id}'

        headers = {
            'Notion-Version': '2022-06-28',
            'Authorization': f'Bearer {self.notion_api_key}',
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            resp_json = response.json()

            last_edited_time = resp_json["last_edited_time"]
            page_title = resp_json["properties"]["title"]["title"][0]["plain_text"]

            return { "last_edited_time" : last_edited_time, "notion_page_title" : page_title }
        else:
            log(f"Request failed with status code {response.status_code}: {response.text}", type="error")
            return {}