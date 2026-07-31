from openai import OpenAI

endpoint = ""
deployment_name = "gpt-5.6-terra"
api_key = "<your-api-key>"

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

response = client.responses.create(
    model = deployment_name,
    input="What is the capital of Spain",
)

print(f"Answer: {response.output[0]}")

