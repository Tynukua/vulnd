from langchain_openai.chat_models import ChatOpenAI

from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

class Analyser:
    def __init__(self, model_name, prompt, is_rag=False):
        self.prompt_text = prompt
        self.model = ChatOpenAI(model_name=model_name)
        self.is_rag = is_rag

        if is_rag:
            self.embedding = OpenAIEmbeddings()
            self.prompt = PromptTemplate(template=self.prompt_text, input_variables=['context', 'question'])
            self.vectorstore = FAISS.load_local("vuln_index", self.embedding, allow_dangerous_deserialization=True)
            self.retriever = self.vectorstore.as_retriever(search_type="similarity", k=4)

            self.chain = RetrievalQA.from_chain_type(
                llm=self.model,
                retriever=self.retriever,
                chain_type="stuff",
                chain_type_kwargs={'prompt': self.prompt}
                )
        else:
            self.prompt = PromptTemplate.from_template(self.prompt_text)
            self.chain = self.prompt | self.model

    async def get_vulnerabilities(self, code):
        import json_parser
        
        result_text = await self._get_vulnerabilities_rag(code) if self.is_rag else await self._get_vulnerabilities(code)
        
        return json_parser.parse_openai_response(result_text)
    
    async def _get_vulnerabilities_rag(self, code):
        result = await self.chain.ainvoke({"query": code})
        result_text = result['result']

        return result_text
    
    async def _get_vulnerabilities(self, code):

        result = await self.chain.ainvoke({"code": code})
        result_text = result.content

        return result_text
    
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    analyzer = Analyser(model_name="gpt-4o-mini", prompt='''
    Analyze the following Solidity code and identify potential vulnerabilities, risks, and optimization opportunities. Provide a detailed explanation of each issue found, including its severity and suggested fixes.
    ```
    {code}
    ```
    Return output in JSON format:
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
    ''', is_rag=False)
    
    code = '''
pragma solidity ^0.8.0;

contract VulnerableContract {
        mapping(address => uint) public balances;
        event Deposit(address indexed sender, uint amount);
        event Withdraw(address indexed receiver, uint amount);
                                 
    }
    '''

    import asyncio

    analyser_rag = Analyser(model_name="gpt-4o-mini", prompt='''
    {context}
    Analyze the following Solidity code and identify potential vulnerabilities, risks, and optimization opportunities. Provide a detailed explanation of each issue found, including its severity and suggested fixes.
    ```
    {question}
    ```

    Return output in JSON format:
    [
        {{
        "line": "LINE NUMBER WHERE ISSUE OCCURS",
        "token": "EXACT PROBLEMATIC CODE SNIPPET",
        "problem": "CONCISE NAME OF THE ISSUE",
        "severity": "low | medium | high",
        "explanation": "DETAILED REASON WHY THIS IS A PROBLEM INCLUDING POTENTIAL IMPACT",
        "migration": "CLEAR AND ACTIONABLE INSTRUCTION ON HOW TO FIX OR MITIGATE THIS ISSUE"
        }}
    ]''', is_rag=True)


    async def main():
        results = await asyncio.gather(
            analyzer.get_vulnerabilities(code),
            analyser_rag.get_vulnerabilities(code),
        )
        for result in results:
            print(result)

    asyncio.run(main())
