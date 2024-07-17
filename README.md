# codestral
[Google Colab Notebook]([https://colab.research.google.com/drive/your_colab_notebook_id](https://colab.research.google.com/drive/12470d_bErDyrp0m8cuz0BODtYySc7zUJ?usp=sharing))

# Lưu mã vào file app.py
%%writefile app.py

# Nhập các thư viện cần thiết
import streamlit as st
from groq import Groq
import re
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Khởi tạo client cho API Groq với API key
client_groq = Groq(api_key="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")

# Khởi tạo client cho API Mistral với API key
client_mistral = MistralClient(api_key="CkmGWlTZ8hDMF0U1mFtt35Of7YNRXc24")
model = "codestral-latest"  # Đặt tên mô hình

# Hàm phân tích wireframe
def analysis_wireframe(wireframe):
    # Tạo prompt yêu cầu API Groq phân tích wireframe và liệt kê các API và Database cần thiết
    prompt = f"""
                You are a Python programmer, from the following detailed description of the screen design, list the APIs and Database needed to design this screen.
                Important note: design the necessary information fields so that all APIs can work (normalize 1NF, 2NF, 3NF and more)
                Each API must definitely include:
                1. Resource Description
                2. Methods and endpoints
                3. Parameters used
                4. Function name (variable: example value)
                5. Return value (variable: example value)
                You must separate APIs and Database Schema by a sign: '----------'.

                Description:
                {wireframe}

                Required Response format (do not give note at the end):
                **APIs**

                **1. API name 1 **
                1. Resource Description: X
                2. Methods and endpoints: Y
                3. Parameters used: A, B, C
                4. Function name: function_name(variables)
                5. Return value: (variable: example value)

                ----------

                **Database Schema**

                **table**
                * `column` (properties)
                """
    # Tạo dữ liệu cho yêu cầu API
    data = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}]
        }
    # Gọi API Groq và nhận kết quả phân tích
    chat_completion = client_groq.chat.completions.create(**data)
    text = chat_completion.choices[0].message.content
    return text  # Trả về kết quả phân tích

# Hàm tạo mã từ kết quả phân tích
def generate_code(text):
    # Định nghĩa các biểu thức chính quy để lấy thông tin từ kết quả phân tích
    resource_description_pattern = r"Resource Description: \s*(.*)"
    methods_endpoints_pattern = r"Methods and endpoints: \s*(.*)"
    parameters_used_pattern = r"Parameters used: \s*(.*)"
    function_name_pattern = r"Function name: \s*(.*)"
    return_value_pattern = r"Return value: \s*(.*)"

    # Sử dụng các biểu thức chính quy để trích xuất thông tin
    resource_description = re.findall(resource_description_pattern, text)
    methods_endpoints = re.findall(methods_endpoints_pattern, text)
    parameters_used = re.findall(parameters_used_pattern, text)
    function_names = re.findall(function_name_pattern, text)
    return_values = re.findall(return_value_pattern, text)

    # Trích xuất schema cơ sở dữ liệu từ kết quả phân tích
    pattern_schema = re.compile(r'----------\n(.*)', re.DOTALL)
    database_schema = pattern_schema.search(text).group(1).strip()

    # Tạo thông điệp yêu cầu API Mistral để tạo mô hình Django từ schema cơ sở dữ liệu
    messages = [
        ChatMessage(role="user", content=f"Use python django to create a django model with 'AutoField' for primary keys from the following database schema:{database_schema}")
    ]
    chat_response = client_mistral.chat(
        model=model,
        messages=messages
    )
    # Hiển thị mô hình Django tạo ra từ API Mistral
    st.write(chat_response.choices[0].message.content)
    st.write("-----------------------")

    # Tạo mã cho từng API
    for idx, (rd, me, pu, fn, rv) in enumerate(zip(resource_description, methods_endpoints, parameters_used, function_names, return_values)):
        config = f"''' Resource description: {rd} | Methods and endpoints: {me} | Parameters used: {pu} | Django Rest framework | model: {chat_response.choices[0].message.content}'''"
        prompt = "def " + fn.replace('`', '') + ":" + config
        suffix = rv
        response = client_mistral.completion(
            model=model,
            prompt=prompt,
            suffix=suffix
        )

        content = response.choices[0].message.content
        content = content.replace("# ", "#")
        if content.find("```python") == -1:
            st.write(f"""\n```python\n{content}\n```""")
        else:
            st.write(f"{content}")
        st.write("-----------------------")
        st.write(methods_endpoints[idx])

# Tạo giao diện với Streamlit
st.title("Wire2Py")  # Tiêu đề ứng dụng

# Tải lên file văn bản chứa wireframe
uploaded_file = st.file_uploader("Upload file .txt", type="txt")

# Khởi tạo session state để lưu trữ các API phân tích được
if 'apis' not in st.session_state:
    st.session_state['apis'] = None

# Nếu có file được tải lên, thực hiện phân tích wireframe
if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    if st.button("Generate API"):
        st.session_state['apis'] = analysis_wireframe(wireframe = content)
        st.write(st.session_state['apis'])  # Hiển thị các API phân tích được

# Nếu đã có API trong session state, thực hiện tạo mã
if st.session_state['apis'] is not None:
    if st.button("Generate Code"):
        generate_code(text = st.session_state['apis'])
