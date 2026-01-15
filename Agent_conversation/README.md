# agent_conversation

A lightweight Python module for managing AI agent conversations with persistent history using SQLite.  
This module integrates with **pydantic-ai** to store, retrieve, and continue chat sessions across multiple interactions.

## Overview

`agent_conversation` provides a simple way to:

- Persist AI conversations in a SQLite database  
- Restore full conversation context for follow-up messages  
- Maintain structured message history using `pydantic_ai` message types  
- Run interactive chat sessions with minimal setup  

It is ideal for small projects, prototypes, or local AI applications where persistent memory is required without the overhead of a full database system.

---

## Features

- SQLite-based storage of conversation history  
- Automatic retrieval and continuation of past conversations  
- Compatible with `pydantic_ai.Agent`  
- Simple API: just call `chat(session_id, message)`  
- Supports system, user, and model message parts  

---

### Requirements

- Python 3.9+
- `pydantic-ai`
- `python-dotenv`
