from sentence_transformers import CrossEncoder

model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def rerank_documents(
    query: str,
    documents: list[str],
    metadatas: list[dict]
):

    if not documents:

        return [], -1

    pairs = []

    for doc in documents:
        pairs.append([query, doc])

    scores = model.predict(pairs)

    ranked = sorted(
        zip(documents, metadatas, scores),
        key=lambda x: x[2],
        reverse=True
    )

    top_score = ranked[0][2]

    print("Top Score:", top_score)

    top_results = []

    for doc, metadata, score in ranked[:3]:

        top_results.append(
            {
                "document": doc,
                "metadata": metadata,
                "score": float(score)
            }
        )

    return top_results, top_score