from bluechat.utils import log
class LargeLanguageModel:

    def __init__(self, model_name = "gpt-3.5-turbo-1106") -> None:
        self.model_name = model_name

    def complete(self, messages):
        from openai import OpenAI
        client = OpenAI()
        log(f"Creating completion with OpenAI API model {self.model_name}", type="debug")
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages
        )
        return response
    
    def summarize(self, text):

        log(f"Summarizing video chunk with OpenAI model {self.model_name}", type="debug")

        messages=[
            {"role": "system", "content": "You are a expert in summarizing texts and you agreed to summarize excerpts from speeches that are handed to."},
            {"role": "user", "content": f"Please summarize the following excerpt from a lecture video in no more than 5-8 sentences. The speakers name is Nicolas: {text}. Please write your summary in German."}
        ]

        summary = self.complete(messages)
        
        return summary.choices[0].message.content
    

    def set_model(self, model_name):
        self.model_name = model_name