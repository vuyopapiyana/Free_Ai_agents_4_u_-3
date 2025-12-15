import sqlite3
import json
from typing import List
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, ModelRequest, TextPart, UserPromptPart, SystemPromptPart
import os

load_dotenv()

class SQLiteDB:
    def __init__(self, db_name= "conversation.db"):
        """Initialize a SQLiteDB database connection."""
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self) -> None:
        """Creates the table if conversation history does not exist."""
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS conversation_history (
    session_id TEXT PRIMARY KEY,
    message_list TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
 
            ''')

    def add_messages(self, session_id: str, message_list_json: str) -> None:
        """Adds messages to the conversation history table."""
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
        """Get the conversation history of a particular chat."""
        def _parse_messages(data: str)-> List[ModelMessage]:
            json_data = json.loads(data)
            messages: List[ModelMessage] = []

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

    # Generate the response
    result= agent.run_sync(message, message_history=history)
    db.add_messages(session_id, result.all_messages_json())

    return result.output

db = SQLiteDB()
agent = Agent(model='openai:gpt-4o-mini', system_prompt="You are helpful and concise for testing purposes")
session_id = "session_127"

question = ""
while question != 'exit':
    question = input("Enter prompt: ")
    print(chat(session_id, message=question))