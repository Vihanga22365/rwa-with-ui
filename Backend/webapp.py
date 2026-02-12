import json
import time
import os
import streamlit as st
from streamlit import expander
# from streamlit_extras.stylable_container import stylable_container

from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_aws import ChatBedrockConverse


# from tools import (
#     get_mzn_token, get_lzm_token
# )
from graph import (
    classify_issue_type,
    call_multi_agents_with_original_check_steps,
    call_multi_agents_with_customized_check_steps,
    generate_final_conclusion
)

os.environ["LANGSMITH_TRACING"]='true'
os.environ["LANGSMITH_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"]=os.getenv('LANGSMITH_API_KEY')
os.environ["LANGSMITH_PROJECT"]="Explainability"

# from prompt import sample_agent_response

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
)

# 

# gemini_2_5_flash = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0,
# )

gemini_2_5_flash = llm

def on_submit_button_clicked():  # 1 usage
    """Callback function for the submit button."""
    with st.spinner("Agents are processing..."):
        # Classify the issue type
        issue_type = classify_issue_type(llm, input_text)
        st.session_state.messages.append({"role": "assistant", "content": f"###### Classified Issue Type: {issue_type}"})
        # Run the Agents
        agent_response = call_multi_agents_with_original_check_steps(llm, issue_type, input_text)
        # agent_response = sample_response
        # Format agent response
        # agent_response = f"##### Classified Issue Type: {issue_type}\n\n" + agent_response
        # Call LLM to generate the final conclusion
        final_conclusion = generate_final_conclusion(gemini_2_5_flash, input_text, agent_response)
        print(final_conclusion)
        # Add expander to show the result
        # expander = st.expander("###### **Final Conclusion**")
        # expander.write(agent_response)
        expander_label = final_conclusion
        st.session_state.messages.append({"role": "assistant", "content": agent_response, "label": expander_label})

# Initialize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize Streamlit app
st.set_page_config(layout="centered", page_title="RWA Model Explainability")
st.sidebar.markdown("# RWA Model Explainability ")

st.markdown("""
<style>
div[data-testid="stMarkdownContainer"] {
    font-size: 16px;
    font-weight: 600;
}
div[data-testid="stMarkdownContainer"] p {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
# Get the input text
input_text = st.sidebar.text_area("Insert Email Subject and Content", height=350)
issue_type = ""
# Make the submit button and call the onclick event
col1, col2 = st.sidebar.columns([2,1])
with col2:
    if input_text:
        st.button("Submit", type="primary", on_click=on_submit_button_clicked, use_container_width=True)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    session_msg = st.chat_message(message["role"])
    # If the message has a label, use it as the expander label
    if "label" in message:
        session_msg.expander(message["label"]).write(message["content"])
    else:
        # Otherwise, just write the content
        session_msg.write(message["content"])

if user_chat_input := st.chat_input("Ask a follow-up question..."):
    st.chat_message("user").write(user_chat_input)
    st.session_state.messages.append({"role": "user", "content": user_chat_input})
    with st.spinner("Agents are processing..."):
        # Call multi agents to get the response.
        agent_response = call_multi_agents_with_customized_check_steps(llm, issue_type, input_text, user_chat_input)
        # agent_response = sample_agent_response
        # agent_response = f"Echo: {user_chat_input}"
        final_conclusion = generate_final_conclusion(gemini_2_5_flash, input_text, agent_response)
        expander_label = final_conclusion
        chat_agent_response = st.chat_message("assistant")
        chat_agent_response.expander(final_conclusion).write(agent_response)
        st.session_state.messages.append({"role": "assistant", "content": agent_response, "label": "final_conclusion"})