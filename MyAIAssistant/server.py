from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from main import chat_with_model, get_similar_memory, add_to_vector_memory
import os

app = FastAPI()

# Serve the chat UI at the root URL
@app.get("/", response_class=HTMLResponse)
async def get_home():
    if os.path.exists("chat.html"):
        return FileResponse("chat.html")
    return HTMLResponse("<h1>chat.html not found</h1>", status_code=404)

# POST endpoint to handle chat requests
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_prompt = data.get("prompt", "")

    # Retrieve relevant memory from vector DB
    memory_context = get_similar_memory(user_prompt)

    # Build prompt for model
    prompt = f"{memory_context}\nYou: {user_prompt}\nAI:"

    # Get model reply
    reply = chat_with_model(prompt)

    # Save to vector DB
    add_to_vector_memory(user_prompt, reply)

    return {"response": reply}
