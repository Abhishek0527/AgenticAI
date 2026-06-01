from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text):

    splitter= RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=300,
    )
    chunks = splitter.split_text(text)

    return chunks
    