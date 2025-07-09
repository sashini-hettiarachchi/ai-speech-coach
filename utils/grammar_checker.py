# import openai

# openai.api_key = "YOUR_KEY"

# def correct_grammar(text):
#     prompt = f"Correct the grammar in this spoken text:\n{text}"
#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return response.choices[0].message.content.strip()


import language_tool_python
tool = language_tool_python.LanguageTool('en-US')

def correct_grammar(text):
    return tool.correct(text)
