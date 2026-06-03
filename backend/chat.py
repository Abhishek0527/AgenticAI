from rag.generator import generate_reponse
from rag.retreiver import retrieve_document
def chat():
    query ="What is React?"

    result = retrieve_document(query)

    # print(result)

    answer = generate_reponse(query,result)

    print(answer)

if __name__ == "__main__":
    chat()