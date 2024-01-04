import time
from typing import List

import pandas as pd
from openai import OpenAI
from utils import decrypt_api_key

api_key = decrypt_api_key("api.txt")

class ChatAssistant:

    def __init__(self, name):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = None
        self.thread_id = None
        self.name = name
    
    """ Get list of all previously created chatbot assistants. """
    def _get_assistant_list(self):
        assistant_list = self.client.beta.assistants.list().data
        assistant_df = pd.DataFrame(
            {
                "name": [asst.name for asst in assistant_list],
                "id": [asst.id for asst in assistant_list],
                "description": [asst.description for asst in assistant_list],
                "instruction": [asst.instructions for asst in assistant_list],
            }
        )
        return assistant_df
    
    """ Create new chatbot assistants with specified person. """
    def _create_assistant(self, instructions, pdf_file, txt_file):
        file_ids = [self._upload_file(pdf_file).id]
        if txt_file:
            file_ids.append(self._upload_file(txt_file).id)

        assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=instructions,
            description=f"Chat Assistant of {self.name}",
            tools=[{"type": "retrieval"}],
            model="gpt-4-1106-preview", # gpt-3.5-turbo-1106
            file_ids=file_ids
        )
        self.assistant_id = assistant.id   

    """Load previosuly created chatbot assistant."""
    def _retrieve_assistant(self, id):
        assistant = self.client.beta.assistants.retrieve(assistant_id=id)
        self.assistant_id = assistant.id
        return assistant

    def _upload_file(self, filename) -> None:
        file = self.client.files.create(
            file=open(filename, "rb"),
            purpose="assistants"
        )
        return file
    
    def _delete_file(self, fileid):
        self.client.files.delete(fileid)

    def _retrieve_file_ids(self):
        files = self.client.beta.assistants.retrieve(self.assistant_id).file_ids
        retrieved_pdf_id = None
        retrieved_txt_id = None
        for file in files:
            retrieved_file = self.client.files.retrieve(file)
            if "pdf" in retrieved_file.filename:
                retrieved_pdf_id = retrieved_file.id
            elif "txt" in retrieved_file.filename:
                retrieved_txt_id = retrieved_file.id
        return retrieved_pdf_id, retrieved_txt_id

    
    """ Initialize chatbot assistant. """
    def set_assistant(self, instructions, pdf_file=None, txt_file=None):
        asst_list = self._get_assistant_list()
        asst_idx = [i for i, name in enumerate(asst_list["name"]) if self.name in name]
        if asst_idx:
            asst_id = asst_list["id"].iloc[asst_idx[0]]
            self._retrieve_assistant(asst_id)

        else:
            self._create_assistant(instructions, pdf_file, txt_file)

    def _create_thread(self):
        """Create or retrieve a persistent thread for the chat."""
        if not self.thread_id:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            # print("new thread created.")

    def get_answers(self, question: str) -> List[str]:
        if self.assistant_id is None:
            raise ValueError("Assistant not created.")
        
        if not self.thread_id:
            self._create_thread()

        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=question,
        )

        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )

        while True:
            run_status = self.client.beta.threads.runs.retrieve(thread_id=self.thread_id, run_id=run.id)
            time.sleep(5)
            if run_status.status == 'completed':
                messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
                break
            else:
                time.sleep(2)
                
        return [message.content[0].text.value for message in messages.data if message.role == "assistant"]
    
    def get_instructions(self):
        return self.client.beta.assistants.retrieve(assistant_id=self.assistant_id).instructions
    
    def revise_instructions(self, new_instruction):
        self.client.beta.assistants.update(
            assistant_id=self.assistant_id,
            instructions=new_instruction
        )

    def change_file(self, pdf_file=None, txt_file=None):
        retrieved_pdf_id, retrieved_txt_id = self._retrieve_file_ids()
        if pdf_file and txt_file:
            self._delete(retrieved_pdf_id)
            self._delete(retrieved_txt_id)
            self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                file_ids=[self._upload_file(pdf_file).id, self._upload_file(txt_file).id]
            )
        elif pdf_file:
            self._delete_file(retrieved_pdf_id)
            self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                file_ids=[retrieved_txt_id, self._upload_file(pdf_file).id]
            )
        elif txt_file:
            if retrieved_txt_id:
                self._delete_file(retrieved_txt_id)
            self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                file_ids=[retrieved_pdf_id, self._upload_file(txt_file).id]
            )