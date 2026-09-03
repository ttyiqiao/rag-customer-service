'''
基于Streamlit完成WEB网页上传服务
ps. 页面刷新，重新跑一遍代码
'''
import streamlit as st
from knowledge_base import KnowledgeBaseService
import time

st.title("知识库更新服务")

uploader_file = st.file_uploader(
    "Please upload a file",
    type = ["txt", "pdf", "docx", "csv"],
    accept_multiple_files = False # False表示仅接受一个文件上传
)


# session_state是一个字典
if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()


if uploader_file is not None:
    # 提取文件信息
    file_name = uploader_file.name
    file_type = uploader_file.type
    file_size = uploader_file.size / 1024 # 转换为KB

    st.subheader(f"文件名：{file_name}")
    st.write(f"格式：{file_type} | 大小：{file_size:.2f} KB")

    # get_value -> bytes -> decode("utf-8")
    text = uploader_file.getvalue().decode("utf-8")

    with st.spinner("loading..."): # 转圈动画
        time.sleep(1)
        result = st.session_state["service"].upload_by_str(text, file_name)
        st.write(result)
