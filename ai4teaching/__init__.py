from ai4teaching.utils.utils import log

from ai4teaching.models.embedding_model import EmbeddingModel
from ai4teaching.models.llm import LargeLanguageModel

from ai4teaching.processing.document_reader import DocumentReader
from ai4teaching.processing.text_reader import TextReader
from ai4teaching.processing.notion_page_reader import NotionPageReader
from ai4teaching.processing.video_reader import VideoReader
from ai4teaching.processing.pdf_reader import PDFReader
from ai4teaching.processing.text_chunker import TextChunker
from ai4teaching.processing.text_embedder import TextEmbedder

from ai4teaching.document_processors.document_processor import DocumentProcessor
from ai4teaching.document_processors.video_processor import VideoProcessor
from ai4teaching.document_processors.notion_processor import NotionProcessor

from ai4teaching.knowledge_base.knowledge_base import KnowledgeBase

from ai4teaching.assistants.assistant import Assistant
from ai4teaching.assistants.video_assistant import VideoAssistant
from ai4teaching.assistants.quiz_assistant import QuizAssistant
from ai4teaching.assistants.openai_assistant import OpenAIAssistant
from ai4teaching.assistants.grading_assistant import GradingAssistant
from ai4teaching.assistants.chatgpt_assistant import ChatGPTAssistant

from ai4teaching.vector_db.vector_db import VectorDB
from ai4teaching.vector_db.chroma_db import ChromaDB



