import streamlit as st
from groq import Groq
import re
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

client_groq = Groq(api_key=st.secrets["groq_key"])
client_mistral = MistralClient(api_key=st.secrets["codestral_key"])
model = "codestral-latest"

def analysis_wireframe(wireframe):
    prompt = f"""
                You are a Python programmer, from the following detailed description of the screen design, list the APIs and Database needed to design this screen.
                Important note: design the necessary information fields so that all APIs can work (normalize 1NF, 2NF, 3NF and more)
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
                You must separate APIs and Database Schema by a sign: '----------'.

                **Database Schema**
                **table**
                * `column` (properties)
                """
    data = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}]
        }
    chat_completion = client_groq.chat.completions.create(**data)
    text = chat_completion.choices[0].message.content
    return text

def generate_code(text):
    resource_description_pattern = r"Resource Description: \s*(.*)"
    methods_endpoints_pattern = r"Methods and endpoints: \s*(.*)"
    parameters_used_pattern = r"Parameters used: \s*(.*)"
    function_name_pattern = r"Function name: \s*(.*)"
    return_value_pattern = r"Return value: \s*(.*)"

    resource_description = re.findall(resource_description_pattern, text)
    methods_endpoints = re.findall(methods_endpoints_pattern, text)
    parameters_used = re.findall(parameters_used_pattern, text)
    function_names = re.findall(function_name_pattern, text)
    return_values = re.findall(return_value_pattern, text)

    pattern_schema = re.compile(r'----------\n(.*)', re.DOTALL)
    database_schema = pattern_schema.search(text).group(1).strip()

    messages = [
        ChatMessage(role="user", content=f"Use python django to create a django model with 'AutoField' for primary keys from the following database schema:{database_schema}")
    ]
    chat_response = client_mistral.chat(
        model=model,
        messages=messages
    )
    st.write(chat_response.choices[0].message.content)
    st.write("-----------------------")

    for idx, (rd, me, pu, fn, rv) in enumerate(zip(resource_description, methods_endpoints, parameters_used, function_names, return_values)):
        st.write("-----------------------")
        st.write(methods_endpoints[idx])
        config = f"''' Resource description: {rd} | Methods and endpoints: {me} | Parameters used: {pu} | Django Rest framework | Api View | model: {chat_response.choices[0].message.content}'''"
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

# Tạo giao diện với Streamlit
st.title("Wire2Py")

uploaded_file = st.file_uploader("Upload file .txt", type="txt")

if 'apis' not in st.session_state:
    st.session_state['apis'] = None

if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    if st.button("Generate API"):
        st.session_state['apis'] = analysis_wireframe(wireframe = content)
        st.write(st.session_state['apis'])

if st.session_state['apis'] is not None:
    if st.button("Generate Code"):
        generate_code(text = st.session_state['apis'])
