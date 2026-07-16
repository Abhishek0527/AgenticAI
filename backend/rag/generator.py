import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_reponse(query, context=None):

    if context is None:

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )

        return response.content[0].text

    context_text = "\n\n".join(context)

    prompt = f"""
    Answer the question in maximum 4 sentences.

    Use the provided context to answer the question clearly and directly.
    Prefer the most relevant details from primary context first, then use parent, child, and linked context only when they help.
    If the question asks for multiple items, answer as a short list in plain text.

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








