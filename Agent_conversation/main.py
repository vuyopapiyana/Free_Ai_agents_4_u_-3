import sqlite3
import json
from typing import List
from datetime import datetime
from dotenv import load_dotenv
# core classes from pydantic_ai that represent structured messages
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, ModelRequest, TextPart, UserPromptPart, SystemPromptPart

load_dotenv()

class SQLiteDB:
    def __init__(self, db_name= "conversation.db"):
        """Initialize a SQLiteDB database connection."""
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self) -> None:
        """
        Creates the conversation_history table if it does not already exist.

        The table stores:
        - session_id: unique identifier for a conversation
        - message_list: JSON string of all messages in that conversation
        - timestamp: last updated time
        """
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS conversation_history (
    session_id TEXT PRIMARY KEY,
    message_list TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
 
            ''')

    def add_messages(self, session_id: str, message_list_json: str) -> None:
        """
        Adds messages to the conversation history table.
        
        If the session_id already exists, the existing row is updated.
        If it does not exist, a new row is inserted.

        The actual conversation data is stored as a JSON string.
        """
        self.conn.execute(
            '''
            INSERT INTO conversation_history (session_id, message_list, timestamp)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id)
            DO UPDATE SET
                message_list = excluded.message_list,
                timestamp = CURRENT_TIMESTAMP
            ''',
            (session_id, message_list_json)
        )
        self.conn.commit()

    def get_history(self, session_id: str) -> List[ModelMessage]:
        """
        Get the conversation history of a particular chat.
        
        The messages are stored in the database as JSON but this function converts them back into real pydantic_ai message objects.
        """
        # 
        def _parse_messages(data: str)-> List[ModelMessage]:
            # Helper to converts raw JSON message history back into a list of ModelMessage objects that the Agent can use.
    
            json_data = json.loads(data)
            messages: List[ModelMessage] = [] # Will hold the list of pydantic ModelMessages

            # Loop through each saved message in the JSON list
            for msg in json_data:
                
                parts = []
                for part in msg['parts']:
                    part_kind = part['part_kind']
                    
                    if part_kind == 'system-prompt':
                        parts.append(SystemPromptPart(content=part['content'], dynamic_ref=part.get('dynamic_ref')))
                    elif part_kind == 'user-prompt':
                        parts.append(UserPromptPart(content=part['content'],
                                                    timestamp=datetime.fromisoformat(part['timestamp']),
                                                    part_kind=part['part_kind']))

                    elif part_kind == 'text':
                        parts.append(TextPart(content=part['content'], part_kind=part['part_kind']))
                    else:
                        raise Exception(f'Unknown part kind {part_kind}')

                if msg['kind'] == 'request':
                    messages.append(ModelRequest(parts=parts, kind='request'))
                    
                elif msg['kind'] == 'response':
                    messages.append(ModelResponse(parts=parts,
                                                  model_name=msg.get('model_name'),
                                                  timestamp=datetime.fromisoformat(msg.get('timestamp')),
                                                  kind='response')
                                    )
                else:
                    raise Exception(f'Unknown message kind {msg["kind"]}')
            return messages

        cursor = self.conn.execute(
            "SELECT message_list FROM conversation_history WHERE session_id = ?",
            (session_id,)
        )
        messages = cursor.fetchone()
        
        if messages:
            return _parse_messages(messages[0])
        return []




def chat(session_id: str, message: str) -> ModelMessage:
    """Get the history of a chat and manage the generation and saving of new conversation."""
    # Retrieve previous conversation history
    history = db.get_history(session_id)

    # Generate the response by using the previous history as context
    result= agent.run_sync(message, message_history=history)

    # Save the full updated conversation (including the new message) back to the database
    db.add_messages(session_id, result.all_messages_json())

    return result.output

db = SQLiteDB()
agent = Agent(model='openai:gpt-4o-mini', system_prompt="You are helpful and concise for testing purposes")
session_id = "session_127"

question = ""
while question != 'exit':
    question = input("Enter prompt: ")
    print(chat(session_id, message=question))
