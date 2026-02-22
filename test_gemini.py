from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain what Metformin is used for in simple English."
)

print(response.text)