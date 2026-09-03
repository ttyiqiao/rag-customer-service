"""
智能客服 RAG 系统 — 主入口
包含：知识库上传（侧边栏）+ 智能客服对话（主界面）
"""
import streamlit as st
import time
import uuid
from rag import RagService
from knowledge_base import KnowledgeBaseService
import config_data as config

# ── 页面配置 ──────────────────────────────────────────────
st.set_page_config(page_title="智能客服 RAG", page_icon="🤖", layout="wide")

# ── 侧边栏：知识库上传 ────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 知识库上传")
    st.markdown("上传文档以扩充知识库（支持 txt / pdf / docx / csv）")

    uploader_file = st.file_uploader(
        "选择文件",
        type=["txt", "pdf", "docx", "csv"],
        accept_multiple_files=False,
        key="kb_uploader",
    )

    if uploader_file is not None:
        file_name = uploader_file.name
        file_type = uploader_file.type
        file_size = uploader_file.size / 1024

        st.markdown(f"**{file_name}**")
        st.caption(f"{file_type} · {file_size:.2f} KB")

        if "kb_service" not in st.session_state:
            st.session_state["kb_service"] = KnowledgeBaseService()

        with st.spinner("正在处理..."):
            try:
                raw_bytes = uploader_file.getvalue()
                if file_name.endswith(".txt"):
                    text = raw_bytes.decode("utf-8")
                else:
                    text = raw_bytes.decode("utf-8", errors="ignore")

                result = st.session_state["kb_service"].upload_by_str(text, file_name)
                st.success(result)
            except Exception as e:
                st.error(f"上传失败：{e}")

    st.divider()
    st.caption("💡 提示：上传后内容会持久化到本地向量库")


# ── 主界面：智能客服对话 ─────────────────────────────────
st.title("🤖 智能客服")
st.divider()

# 初始化会话消息
if "message" not in st.session_state:
    st.session_state["message"] = [
        {"role": "assistant", "content": "你好！有什么可以帮到你？"}
    ]

# 展示历史消息
for msg in st.session_state["message"]:
    st.chat_message(msg["role"]).write(msg["content"])

# 初始化 RAG 服务
if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()

# 每个用户分配唯一 session_id
if "session_id" not in st.session_state:
    st.session_state["session_id"] = f"user_{uuid.uuid4().hex[:6]}"

session_config = {
    "configurable": {
        "session_id": st.session_state["session_id"]
    }
}

# 用户输入
prompt = st.chat_input("请输入你的问题...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    ai_res_list = []
    with st.spinner("AI 思考中..."):
        res_stream = st.session_state["rag"].chain.stream(
            {"input": prompt}, session_config
        )

        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk

        with st.chat_message("assistant"):
            st.write_stream(capture(res_stream, ai_res_list))

    st.session_state["message"].append(
        {"role": "assistant", "content": "".join(ai_res_list)}
    )
