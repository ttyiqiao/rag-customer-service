'''
知识库
'''
import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

# 检查传入的md5字符串是否已经被处理过了
def check_md5(md5_str: str):
    if not os.path.exists(config.md5_path):
        open(config.md5_path, "w", encoding = "utf-8").close()  # 如果md5文件不存在，则创建一个空文件
        return False # md5未处理过
    else:
        for line in open(config.md5_path, "r", encoding = "utf-8").readlines():
            line = line.strip() # 去掉前后空格和回车
            if line == md5_str:
                return True # md5已处理过
        return False # md5未处理过


# 将传入的md5字符串记录到文件内容中保存
def save_md5(md5_str: str):
    with open(config.md5_path, "a", encoding = "utf-8") as f:
        f.write(md5_str + "\n"  )


# 将传入的字符转换为md5字符串
def get_string_md5(input_str:str, encoding = "utf-8"):
    str_bytes = input_str.encode(encoding = encoding)

    md5_obj = hashlib.md5() # 得到md5对象
    md5_obj.update(str_bytes) # 更新内容，传入即将要转换的字节数组
    md5_hex = md5_obj.hexdigest() # 得到md5的十六进制字符串

    return md5_hex


class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(config.persist_directory, exist_ok = True) # 文件夹不存在则创建，存在则跳过

        self.chroma = Chroma(
            collection_name = config.collection_name, # 放在配置文件里
            embedding_function = DashScopeEmbeddings(model = "text-embedding-v4"),
            persist_directory = config.persist_directory # 数据库本地存储文件夹
        )

        # 文本分割器对象
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size = config.chunk_size, # 分割后文本段最大长度
            chunk_overlap = config.chunk_overlap, # 连续文本段之间的字符重叠数量
            separators = config.separators, # 自然段落划分的符号
            length_function =len # 使用python自带的len函数做长度统计
        )

    # 将传入的字符串进行向量化，存入向量数据库
    def upload_by_str(self, data: str, filename):

        # 得到传入字符串的md5值
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return "[跳过]内容已存在知识库中"
        
        if len(data) > config.max_split_char_number: # 太小的不切分
            knowledge_chunks:list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]


        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "tyq"
        }

        # 内容加载到向量库中
        self.chroma.add_texts(
            # iterable: list, tuple...
            knowledge_chunks,
            metadatas = [metadata for _ in knowledge_chunks]
        )

        save_md5(md5_hex)

        return "[成功]内容已经成功载入向量库"

if __name__ == "__main__":
    service = KnowledgeBaseService()
    r = service.upload_by_str("tyq", "testfile")
    print(r)