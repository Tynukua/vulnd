from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = DirectoryLoader("vuln_files", glob="**/*.txt", loader_cls=TextLoader)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=50
)
chunks = splitter.split_documents(docs)
for chunk in chunks:
    print(chunk.page_content)
    print("="*50)

embedding = OpenAIEmbeddings()

vectorstore = FAISS.from_documents(docs, embedding)

vectorstore.save_local("vuln_index")

print("✅ Vector base saved to vuln_index")
