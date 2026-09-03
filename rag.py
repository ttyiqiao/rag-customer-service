'''
生成chain
'''
from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from file_history_store import get_history
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda




def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)

    return prompt

class RagService(object):
    def __init__(self):
        self.vector_service = VectorStoreService(
            embedding = DashScopeEmbeddings(model = config.embedding_model_name)
        )

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以已经提供的参考资料为主。"
                 "简洁专业地回答。参考资料{context}。"),
                ("system", "提供如下用户对话的历史记录: "),
                MessagesPlaceholder("history"),
                ("user", "请回答用户的提问: {input}")
            ]
        )

        self.chat_model = ChatTongyi(model = config.chat_model_name, streaming = True)

        self.chain = self.__get_chain()

    def __get_chain(self):
        """ 获取最终的执行链"""
        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"

            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段: {doc.page_content}\n文档元数据: {doc.metadata}\n\n"

            return formatted_str



        # "context": retriever | format_document会报错，写函数排查
        # def temp1(value):
        #     print("---------", value)
        #     return value
        # "context": RunnableLambda(temp1) | retriever | format_document 调用发现打印出来{'input': '我体重120斤，进行尺码推荐', 'history': []}
        # 但是retriever 应该只要"我体重120斤，进行尺码推荐"这个str，因此用函数进行转换
        def format_for_retriever(value:dict) -> str:
            return value["input"]
    




        # 新报错：Expected: ['context', 'history', 'input'] Received: ['input', 'context']
        # 新报错是因为history被扔了，写函数排查
        # def temp2(value):
        #     print("---------", value)
        #     return value
        # "context": RunnableLambda(temp1) | retriever | format_document} | RunnableLambda(temp2) | self.prompt_template | 调用排查
        # 打印出{'input': {'input': '我体重120斤，进行尺码推荐', 'history': []}, 'context': "文档片段: 身高:...
        # 写函数转换
        def format_for_prompt_template(value):
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["context"] = value["context"]
            new_value["history"] = value["input"]["history"]

            return new_value




        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(format_for_retriever) | retriever | format_document
            } | RunnableLambda(format_for_prompt_template) | self.prompt_template | print_prompt| self.chat_model | StrOutputParser()
        )

        # 增强链，附带历史消息
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key = "input", # 用户输入在模板中的占位符
            history_messages_key = "history" # 历史消息在模板中的占位符
        )

        return conversation_chain

if __name__ == '__main__':
    session_config = {
            "configurable": {
                "session_id": "user_002"
            }
        }
    res = RagService().chain.invoke({"input": "我体重120斤，进行尺码推荐"}, session_config) # 记得session_config，以及对于增强链需要传字典（仅仅chain的时候传str）
    print(res)