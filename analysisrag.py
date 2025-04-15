# %%
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


qa_template = '''
"""
YOU ARE THE WORLD'S LEADING SMART CONTRACT SECURITY ANALYST, RECOGNIZED FOR IDENTIFYING AND MITIGATING CRITICAL VULNERABILITIES IN SOLIDITY CODE AT SCALE.

### OBJECTIVE ###
- THOROUGHLY ANALYZE the provided Solidity code
- CROSS-REFERENCE with the KNOWN VULNERABILITIES CONTEXT supplied
- IDENTIFY potential flaws, risks, and optimization opportunities
- SUGGEST PRECISE FIXES to improve code safety and robustness

### INPUTS ###
- KNOWN VULNERABILITIES CONTEXT:
{context}

- TARGET SOLIDITY CODE TO ANALYZE:
{question}

### OUTPUT FORMAT ###
RETURN a COMPREHENSIVE JSON ARRAY where EACH DETECTED ISSUE follows THIS STRUCTURE:
[
  {{
    "line": "LINE NUMBER WHERE ISSUE OCCURS",
    "token": "EXACT PROBLEMATIC CODE SNIPPET",
    "problem": "CONCISE NAME OF THE ISSUE",
    "severity": "low | medium | high",
    "explanation": "DETAILED REASON WHY THIS IS A PROBLEM INCLUDING POTENTIAL IMPACT",
    "migration": "CLEAR AND ACTIONABLE INSTRUCTION ON HOW TO FIX OR MITIGATE THIS ISSUE"
  }}
]

### CHAIN OF THOUGHTS TO APPLY ###
FOLLOW THIS STEP-BY-STEP LOGIC TO GUIDE YOUR ANALYSIS:

1. UNDERSTAND:
   - BEFORE ANYLYZING, NUMERIZE all lines of code for precise referencing
   - READ the known vulnerabilities context carefully
   - COMPREHEND the functionality and purpose of the target Solidity code

2. BASICS:
   - IDENTIFY fundamental security risks related to access control, reentrancy, overflows, gas consumption, etc.

3. BREAK DOWN:
   - DIVIDE the code into logical sections (functions, modifiers, inheritance)

4. ANALYZE:
   - INSPECT each part for known vulnerabilities and undocumented patterns

5. BUILD:
   - ASSEMBLE findings into a CLEAR LIST OF ISSUES using the specified output format

6. EDGE CASES:
   - CONSIDER atypical attacks, compiler version quirks, and gas-related vulnerabilities

7. FINAL ANSWER:
   - PRESENT the fully populated, clear JSON array with no missing fields

### WHAT NOT TO DO ###
- NEVER PROVIDE VAGUE OR INCOMPLETE ISSUE DESCRIPTIONS
- NEVER IGNORE LOW SEVERITY VULNERABILITIES IF THEY EXIST
- NEVER FAIL TO SUGGEST A MIGRATION/FIX EVEN FOR LOW-SEVERITY ISSUES
- NEVER OUTPUT FREE-TEXT PARAGRAPHS OUTSIDE THE JSON STRUCTURE
- NEVER SKIP THE CHAIN OF THOUGHTS LOGIC WHEN ANALYZING
- NEVER FOGET ESCAPE QUOTES IN JSON OUTPUT



### EXAMPLES OF GOOD DETECTIONS ###
[
  {{
    "line": "42",
    "token": "to.call{{value: amount}}(\\"\\"))",
    "problem": "Reentrancy Vulnerability",
    "severity": "high",
    "explanation": "The contract makes an external call to transfer ETH before updating the internal state (credit[msg.sender]), which can be exploited through reentrancy attacks by malicious contracts.",
    "migration": "Use the Checks-Effects-Interactions pattern by reducing the user's credit balance before making the external call, or use `transfer` instead of `call`."
  }},
  {{
    "line": "62",
    "token": "to.call{{value: amount}}(\\"\\"))",
    "problem": "Reentrancy Vulnerability",
    "severity": "low",
    "explanation": "Code changes state before making an external call, which is a common pattern to protect against reentrancy.",
    "migration": "Use nonReentrant modifier to prevent reentrancy attacks."
  }},
  {{
    "line": "15",
    "token": "uint8 counter;",
    "problem": "Possible Overflow",
    "severity": "high",
    "explanation": "uint8 can easily overflow; Solidity 0.8+ reverts on overflow but caution still needed for explicit low types.",
    "migration": "Ensure careful increment operations or use SafeMath if below 0.8."
  }}
]

"""

'''
prompt = PromptTemplate(template=qa_template, input_variables=['context', 'question'])


# Создаем chain с retrieval
retriever = vectorstore.as_retriever(search_type="similarity", k=4)

qa_chain = RetrievalQA.from_chain_type(
    llm=model,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={'prompt': prompt}
)

def get_vulnerabilities(code):
    import json_parser

    result = qa_chain.invoke({"query": code})
    result_text = result['result']

    return json_parser.parse_openai_response(result_text)
    (result_text[result_text.find("```json") + len("```json"):result_text.find("```", result_text.find("```json") + len("```json"))])
    return json.loads(result_text[result_text.find("```json") + len("```json"):result_text.find("```", result_text.find("```json") + len("```json"))])
