# pip install google-generativeai

import google.generativeai as genai

genai.configure(api_key="AIzaSyDO8JTTf1jS8IB-wOjhvPox-A51UcUYbnA")

models = list(genai.list_models())

print(f"Total models available: {len(models)}\n")
for model in models:
    print(f"Name:         {model.name}")
    print(f"Display Name: {model.display_name}")
    print(f"Description:  {model.description}")
    print("-" * 50)