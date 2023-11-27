from ai4teaching import Assistant
from ai4teaching import log
from openai import OpenAI

class ChatGPTAssistant(Assistant):

    def __init__(self, config_file, depending_on_assistant=None):
        log("Initializing ChatGPTAssistant", type="debug")
        log(f"ChatGPTAssistant depends on {depending_on_assistant}", type="debug") if depending_on_assistant else None
        super().__init__(config_file, depending_on_assistant)

        self.openai_client = OpenAI()
        self.openai_models = [
            {"display_name" : "GPT-3.5", "model_name" : "gpt-3.5-turbo-1106"},
            {"display_name": "GPT-4", "model_name" : "gpt-4-1106-preview" }
        ]

        self.last_prompt = []
        self.messages = []
        self.system_message = None

    '''
    Returns the complete message history with the assistant's response as
    the last message
    '''
    def chat(self, message, model_display_name="GPT-3.5"):
        # Get model name for display name
        model_name = self._get_model_name_for_display_name(model_display_name)

        # Create new message entry from text and add
        new_message_json = {"role": "user", "content": f"{message}"}

        self.messages.append(new_message_json)

        # Complete the prompt
        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=self.messages
        )
        
        # Get the response and add to messages
        assistant_message_content = response.choices[0].message.content
        assistant_message_json = {"role": "assistant", "content": assistant_message_content}
        self.messages.append(assistant_message_json)

        return self._get_cleaned_messages_copy()
    
    '''
    Returns only the response (last message) of the chat
    '''
    def chat_text(self, message, model_display_name="GPT-3.5"):
        messages = self.chat(message, model_display_name)
        return messages[-1]["content"]

    '''
    Reset the message history
    '''
    def reset(self):
        log("Resetting ChatGPTAssistant", type="debug")
        self.messages = []

        # Add system message if present
        if self.system_message is not None:
            self.messages.append({"role": "system", "content": self.system_message})

        return self._get_cleaned_messages_copy()

    def set_system_message(self, system_message):
        self.system_message = system_message

        # Replace or add system message
        for m in self.messages:
            if m["role"] == "system":
                m["content"] = system_message
                return
        
        # If we are here, there way no system message, add to first position
        self.messages.insert(0, {"role": "system", "content": system_message})

    def get_system_message(self):
        return self.system_message

    def get_model_names(self):
        return [model["display_name"] for model in self.openai_models]        

    def _get_model_name_for_display_name(self, model_display_name):
        for model in self.openai_models:
            if model["display_name"] == model_display_name:
                return model["model_name"]
        return "gpt-3.5-turbo-1106"
    
    def _get_cleaned_messages_copy(self):
        # Remove system message
        messages_copy = self.messages.copy()
        if self.system_message is not None:
            messages_copy.pop(0)
        return messages_copy