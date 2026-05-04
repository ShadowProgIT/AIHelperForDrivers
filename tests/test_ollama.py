# test_ollama.py
import requests
import json

url = "http://localhost:11434/api/generate"

payload = {
    "model": "qwen3.5-driving",
    "prompt": "Можно ли обгонять на пешеходном переходе согласно ПДД РФ? Ответь кратко.",
    "stream": False
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

print("✅ Ответ модели:")
print(result.get("response", "Нет ответа"))