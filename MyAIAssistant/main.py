import os
import json
import subprocess
import chromadb
import sqlite3

# === SETUP ===

# JSON fallback memory file
MEMORY_FILE = "memory.json"

# ChromaDB vector memory
client = chromadb.Client()
collection = client.get_or_create_collection("conversations")

# SQLite for permanent memory
def init_db():
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            ai_response TEXT
        )
    ''')
    conn.commit()
    return conn

db_conn = init_db()

# === MEMORY ===

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)["conversations"]
    return []

def save_memory(conversations):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"conversations": conversations}, f, indent=2)

def add_to_vector_memory(user_input, ai_reply):
    doc = f"You: {user_input}\nAI: {ai_reply}"
    uid = str(len(collection.get()['ids']) + 1)
    collection.add(documents=[doc], ids=[uid])

def get_similar_memory(prompt):
    try:
        results = collection.query(query_texts=[prompt], n_results=3)
        return "\n".join(results['documents'][0]) if results['documents'] else ""
    except:
        return ""

def save_to_db(conn, user_input, ai_response):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memory (user_input, ai_response) VALUES (?, ?)", (user_input, ai_response))
    conn.commit()

# === CHAT ===

def chat_with_model(prompt):
    process = subprocess.Popen(
        ['ollama', 'run', 'mistral'],  # Or 'llama3', etc.
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output, _ = process.communicate(prompt)
    return output.strip()

# === COMMANDS ===

def execute_command(cmd):
    if "open notepad" in cmd.lower():
        os.system("notepad")
        print("Opening Notepad.")
        return True
    if "open calculator" in cmd.lower():
        os.system("calc")
        print("Opening Calculator.")
        return True
    return False

# === MAIN LOOP (Only when run directly) ===

if __name__ == "__main__":
    conversations = load_memory()

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if execute_command(user_input):
            continue

        memory_context = get_similar_memory(user_input)
        prompt = f"{memory_context}\nYou: {user_input}\nAI:"

        reply = chat_with_model(prompt)
        print("AI:", reply)

        add_to_vector_memory(user_input, reply)
        save_to_db(db_conn, user_input, reply)
        conversations.append({"user": user_input, "ai": reply})
        save_memory(conversations)
