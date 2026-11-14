import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class ChatManager:
    def __init__(self, db_path: str = "chat.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_message(self, user: str, content: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (user, content) VALUES (?, ?)', (user, content))
        conn.commit()
        conn.close()
        return True
    
    def get_messages(self, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user, content, timestamp FROM messages ORDER BY id DESC LIMIT ?', (limit,))
        messages = [{"user": row[0], "content": row[1], "timestamp": row[2]} for row in cursor.fetchall()]
        conn.close()
        return messages

if __name__ == "__main__":
    chat = ChatManager()
    chat.save_message("Alice", "Hello world!")
    # Display recent messages
    print("Recent messages:")
    for msg in chat.get_messages(10):
        print(f"[{msg['timestamp']}] {msg['user']}: {msg['content']}")
    
    # Add more sample messages
    chat.save_message("Bob", "Hi Alice!")
    chat.save_message("Alice", "How are you?")
    chat.save_message("Bob", "I'm doing great!")
    
    # Display all messages again
    print("\nAll messages:")
    for msg in chat.get_messages():
        print(f"[{msg['timestamp']}] {msg['user']}: {msg['content']}")