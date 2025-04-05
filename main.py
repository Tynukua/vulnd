# %%
import os
import dotenv
dotenv.load_dotenv()

# %%
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.globals import set_debug, set_verbose

set_verbose(True)
set_debug(True)

# Загрузка эмбеддингов и векторной БД
embedding = OpenAIEmbeddings()
vectorstore = FAISS.load_local("vuln_index", embedding, allow_dangerous_deserialization=True)

# Инициализация модели
model = ChatOpenAI(model_name="gpt-4o-mini")

# %%
# Кастомный промпт для кода
prompt = PromptTemplate.from_template("""
You are a smart contract security expert.

Here is relevant context from known vulnerabilities:
{context}

Now analyze the following Solidity code:


Return a list of any detected vulnerabilities in this format:
[
  {{
    "line": "line number",
    "token": "problematic code",
    "problem": "short name",
    "severity": "low | medium | high",
    "explanation": "why it's dangerous",
    "migration": "how to fix"
  }}
]
""")

# Создаем chain с retrieval
retriever = vectorstore.as_retriever(search_type="similarity", k=4)

qa_chain = RetrievalQA.from_chain_type(
    llm=model,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt}
)

# %%
# Читаем код из snippets/
snippets_path = "snippets"
files = os.listdir(snippets_path)
code_snippets = []
for file in files:
    with open(os.path.join(snippets_path, file), "r") as f:
        code_snippets.append(f.read())

# %%
# Анализ одного сниппета
code = code_snippets[2]

# %%
# Исправленный вызов chain.invoke() без дублирующихся ключевых аргументов
result = qa_chain.invoke(dict(query="analyze"))

# %%
print(code)
print(result)
