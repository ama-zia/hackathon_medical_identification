from google import genai

client = genai.Client(api_key="AIzaSyD5ZpB42p7w2EYs1R95QgsxJCRrO1ypHWg")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain what Metformin is used for in simple English."
)

print(response.text)