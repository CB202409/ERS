# 파인콘
from pinecone import Pinecone, ServerlessSpec
import time
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PDFPlumberLoader



load_dotenv()

# pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# result = pc.Index('law-pdf')
# lst = result.list()
# for node in lst:
#   print(node)


docs = []

loader = PDFPlumberLoader("./pdf/근로기준법.pdf")
docs.extend(loader.load())

print(docs[0])

from langchain_core.documents import Document



# pc.create_index(
#     name=index_name,
#     dimension=1024, # Replace with your model dimensions
#     metric="cosine", # Replace with your model metric
#     spec=ServerlessSpec(
#         cloud="aws",
#         region="us-east-1"
#     ) 
# )

