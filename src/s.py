import os
import requests

API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"
headers = {
    "Authorization": f"Bearer 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",
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

response = query({
    "messages": [
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ],
    "model": "minimaxai/minimax-m1-80k"
})

print(response["choices"][0]["message"])