from graph_context import get_graph_context

print(
    get_graph_context(
        "Password Reset Design",
        "confluence"
    )
)





# import chromadb

# client = chromadb.PersistentClient(
#     path="./chroma_db"
# )

# collection = client.get_collection(
#     "knowledge_fabric"
# )

# # print(collection.count())

# results = collection.get(
#     where={
#         "source": "SCRUM-7"
#     }
# )

# print(results["metadatas"][0])


# results = collection.get(
#     where={
#         "source_type": "jira"
#     }
# )

# print(len(results["documents"]))