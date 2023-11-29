from ai4teaching import EmbeddingModel

class TextEmbedder:
    def __init__(self, model_name="text-embedding-ada-002"):
        self.model = EmbeddingModel(model_name)

    '''
    Takes a list of documents and embeds them using the OpenAI API. Requires the text to be stored in the "text" key of each document.
    '''
    def embed(self, chunks):

        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.embed(chunk_texts)

        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings.data[i].embedding
        
        return chunks

    