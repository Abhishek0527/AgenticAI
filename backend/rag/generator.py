import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_reponse(query,context):

    if context is None:
        return "No relevant information found."

    context_text = "\n\n".join(context)
    
    prompt = f"""
        Answer the question in maximum 3 sentences.

        Use only the provided context.

        If the answer is not in the context, say:
        "I could not find relevant information."

        Context:
        {context_text}

        Question:
        {query}
        """

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.content[0].text

    



    
    
    
    