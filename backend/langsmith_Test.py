from dotenv import load_dotenv
from langsmith import traceable
import os

load_dotenv(override=True)

print("Tracing:", os.getenv("LANGSMITH_TRACING"))
print("Project:", os.getenv("LANGSMITH_PROJECT"))
print("Key exists:", bool(os.getenv("LANGSMITH_API_KEY")))

@traceable
def test_langsmith(x):
    return x + 1

print(test_langsmith(10))