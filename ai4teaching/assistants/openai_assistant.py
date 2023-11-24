from ai4teaching import Assistant
from ai4teaching import log
import time
import os
from openai import OpenAI


class OpenAIAssistant(Assistant):
    def __init__(self, config_file, depending_on_assistant=None):
        log("Initializing OpenAIAssistant", type="debug")
        log(f"OpenAIAssistant depends on {depending_on_assistant}", type="debug") if depending_on_assistant else None
        super().__init__(config_file, depending_on_assistant)

        self.openai_client = OpenAI()
        self.openai_model = "gpt-4-1106-preview"
        #self.openai_model = "gpt-3.5-turbo-1106"

        self.assistant_id = self.config["openai_assistant_id"]
        self.thread = None
        self._setup_client_and_assistant()
        self._create_and_attach_file()

    def _setup_client_and_assistant(self):
        self.openai_client = OpenAI()
        self.openai_assistant = self.openai_client.beta.assistants.retrieve(
            self.assistant_id
        )

    # TODO: Move this to the processor?
    def _create_and_attach_file(self):
        # Add large text file to assistant
        # Get the list of files from the knowledge base
        documents = self.get_list_of_vector_db_documents()

        # Merge all text into one
        text = ""
        for t in documents["documents"]:
            text += t

        # Create a txt with the string as content
        file_name = os.path.join(self.root_path, "assistant_knowledge.txt")
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(text)
        
        # Get the file from the assistant
        #log(f"{self.openai_assistant}")
        file_ids = self.openai_assistant.file_ids

        # Delete the file from the assistant (should be only one file)
        if len(file_ids) > 0:
            try:
                self.openai_client.files.delete(file_id=file_ids[0])
            except:
                log("Could not delete file", type="warning")

        # Create a new file and upload it
        #log(f"Uploading file to OpenAI: {file_name}")
        file = self.openai_client.files.create(file=open(file_name, "rb"), purpose="assistants")
        #log(f"Uploaded file: {file}")
        self.file = file
        
        # Attach the new file to the assistant
        self.openai_client.beta.assistants.update(assistant_id=self.openai_assistant.id, file_ids=[file.id], model=self.openai_model)
        
        # Delete the file
        #os.remove(file_name)

    def get_messages(self):
        messages = self.openai_client.beta.threads.messages.list(
            thread_id=self.thread.id
        )
        return messages

    def send_message(self, message, user_name="Nicolas"):
        # Check if there is already a thread
        if self.thread is None:
            self.thread = self.openai_client.beta.threads.create()

        message = self.openai_client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=f"{message}",
        )

        run = self.openai_client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.openai_assistant.id,
            instructions=f"Bitte spreche den Benutzer mit dem Namen {user_name} an und duze sie oder ihn. Antworte auf Deutsch. Wenn du auf Dokumente zurückgreifst, gib die Quelle an.",
        )

        def check_run(run_id):
            return self.openai_client.beta.threads.runs.retrieve(
                thread_id=self.thread.id, run_id=run_id
            )

        time.sleep(0.1)
        run = check_run(run.id)

        log(f"Run status is {run.status}")

        while run.status != "completed":
            time.sleep(1)
            run = check_run(run.id)
            
            if run.status == "failed":
                log("Run failed", "error")
                break

            if run.status != "in_progress" and run.status != "completed":
                log(f"Run status is {run.status}", "warning")
    
        messages = self.openai_client.beta.threads.messages.list(
            thread_id=self.thread.id
        )

        formatted_messages = self._format_messages(messages)  

        return formatted_messages
    
    def reset(self):
        self.thread = None
        return []

    def _format_messages(self, messages):
        formatted_messages = []
    
        for m in messages.data:
            for c in m.content:
                formatted_messages.append({"role": m.role, "message" : c.text.value })

        # Reverse array
        formatted_messages = formatted_messages[::-1]

        return formatted_messages