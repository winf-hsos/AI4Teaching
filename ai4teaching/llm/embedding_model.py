class EmbeddingModel:

    def __init__(self, model_name = "text-embedding-ada-002") -> None:
        self.model_name = model_name

    def embed(self, document_list):
        from openai import OpenAI
        client = OpenAI()
        embeddings = client.embeddings.create(input=document_list, model=self.model_name)
        return embeddings

    def get_stats(self):
        return { "model_name" : self.model_name }       