from app.core.llm import AgentsLLM

llm = AgentsLLM()
messages = [
    {"role": "user", "content": "Hello! Who are you?"}
]

full_response = ""
for chunk in llm.stream_invoke(messages):
    print(chunk, end="")
    full_response += chunk
