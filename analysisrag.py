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
FIRST, OUTPUT A CHAIN OF THOUGHT THAT EXPLAINS YOUR ANALYSIS STEP-BY-STEP.

THEN RETURN A COMPREHENSIVE JSON ARRAY where EACH DETECTED ISSUE follows THIS STRUCTURE:
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
   - Number all lines of code for precise referencing.
   - Carefully read the known vulnerabilities context.
   - Comprehend the functionality and purpose of the target Solidity code.

2. BASICS:
   - Identify basic security risks: access control, reentrancy, overflows, gas inefficiencies, visibility issues, and unchecked calls.

3. BREAK DOWN:
   - Divide the code into logical sections (constructors, functions, modifiers, inheritance).
   - Observe how state variables are used and whether external interactions are properly handled.

4. ANALYZE:
   - Inspect each section for known vulnerabilities and suspicious or undocumented patterns.
   - Check if patterns like Checks-Effects-Interactions, proper error handling, and safe math are followed.

5. BUILD:
   - Assemble findings into a clear list of issues using the specified JSON format.

6. EDGE CASES:
   - Consider compiler version quirks, timestamp and block manipulation, and gas griefing attacks.
   - Think about permission escalation or external dependency risks.

7. OUTPUT:
   - Start by explaining how each issue was discovered using a step-by-step thought process (CHAIN OF THOUGHT).
   - Then provide a complete, well-formatted JSON array with no missing fields.

### WHAT NOT TO DO ###
- DO NOT provide vague or incomplete issue descriptions.
- DO NOT ignore low-severity vulnerabilities.
- DO NOT omit migration/fix instructions, even for minor issues.
- DO NOT output free-text paragraphs outside of the JSON structure.
- DO NOT skip the CHAIN OF THOUGHT section before listing issues.
- DO NOT forget to escape quotes in JSON.

### EXAMPLES OF GOOD DETECTIONS ###
[
  {{
    "line": "42",
    "token": "to.call{{value: amount}}(\\"\")",
    "problem": "Reentrancy Vulnerability",
    "severity": "high",
    "explanation": "The contract makes an external call to transfer ETH before updating the internal state (credit[msg.sender]), which can be exploited through reentrancy attacks by malicious contracts.",
    "migration": "Use the Checks-Effects-Interactions pattern by reducing the user's credit balance before making the external call, or use `transfer` instead of `call`."
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

    print(result_text)
    return json_parser.parse_openai_response(result_text)
    (result_text[result_text.find("```json") + len("```json"):result_text.find("```", result_text.find("```json") + len("```json"))])
    return json.loads(result_text[result_text.find("```json") + len("```json"):result_text.find("```", result_text.find("```json") + len("```json"))])
