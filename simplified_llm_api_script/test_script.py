from llm_checker_v2 import review_document
import asyncio

results = asyncio.run(review_document(my_document_dict))
