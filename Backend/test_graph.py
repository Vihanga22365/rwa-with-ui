import os
import json
import pandas as pd

# from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_core.messages.utils import filter_messages
from langchain_experimental.agents import create_pandas_dataframe_agent

from tools import get_prompt_using_table_name, get_check_step_to_process
from prompt import (
    ISSUE_CLASSIFICATION_PROMPT,
    SUPERVISOR_AGENT_PROMPT,
    SUPERVISOR_AGENT_PROMPT_2,
    SUPERVISOR_AGENT_PROMPT_IN_CHAT,
    DATA_EXTRACTION_AGENT_PROMPT,
    FINAL_CONCLUSION_PROMPT,
    DATA_EXTRACTION_AGENT_PROMPT_2
)

# from pretty_print import pretty_print_messages
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def classify_issue_type(llm, input_text):
    """
    Classify the issue type based on the input text.
    :param llm: The language model to use for classification.
    :param input_text: The input text to classify.
    :return: The classified issue type.
    """
    prompt = ISSUE_CLASSIFICATION_PROMPT.format(input_text=input_text)
    print(f"User input: {input_text}")
    try:
        response = llm.invoke(prompt)
        if response.content:
            return response.content
        else:
            raise ValueError("LLM response is empty.")
    except Exception as e:
        print(f"Error invoking LLM: {e}")
        raise ValueError("Failed to classify issue type due to LLM invocation error.")

def generate_final_conclusion(llm, input_text, validation_steps):
    """
    Generate the final conclusion based on the input text and validation steps.
    :param llm: The language model to use for generate the conclusion.
    :param input_text: The input text.
    :param validation_steps: The validation steps.
    :return: Generated final conclusion.
    """
    prompt = FINAL_CONCLUSION_PROMPT
    prompt = prompt.format(input_text=input_text, validation_steps=validation_steps)
    try:
        response = llm.invoke(prompt)
        if response.content:
            return response.content
        else:
            raise ValueError("LLM response is empty.")
    except Exception as e:
        print(f"Error invoking LLM: {e}")
        raise ValueError("Failed to generate the final conclusion due to LLM invocation error.")

def get_check_steps_using_issue_type(issue_type):
    """
    Get the steps
    :param issue_type:
    :return:
    """
    file_path = "C:/Projects/Repos/Scripts/nwa_agentic/input_files/Issue Types and Check Steps.xlsx"
    check_steps_df = pd.read_excel(file_path)
    try:
        filtered_df = check_steps_df[check_steps_df['Issue Type'] == issue_type]['Check Steps'].values[0]
    except IndexError:
        return "No Check Steps Found"
    return filtered_df

def get_input_dataframes():
    """
    Read the input Excel file and return the dataframes.
    :return: A dictionary of dataframes for each sheet in the Excel file.
    """
    file_name = "input_files/data_tables/V Issues Scenarios- Mockup tables.xlsx"
    sheet_names = [
        "om_cdm_rwa_mtrc",
        "om_cdm_rwa_mtrc_extn",
        "dsft_conc_txn_result",
        "dsft_conc_result_txn_map",
        "dsft_conc_result",
        "dsft_fi_base_subassetclass"
    ]
    # Read the Excel file and return the dataframes
    dataframes = pd.read_excel(file_name, sheet_name=sheet_names)
    return dataframes

def init_mart_table_pandas_agent(llm, input_df):
    """
    Initialize a pandas agent for the Mart(OM_CDM_RWA_MTRC) table.
    :param llm: The language model to use for the agent.
    :param input_df: The input dataframe containing the mart table data.
    :return: An agent executor for the mart table.
    """
    om_cdm_rwa_mtrc_prefix_prompt = (
        "You are working with a pandas dataframe in Python. The name of the dataframe is 'df'.\n"
        "Here are the available important columns in the df:\n"
        "  'OBLG_NO' = Integer - The id of the organization.\n"
        "  'SCR_ID' = String - Security Identifier.\n"
        "  'BUY_SELL_IND' = String - Buy or sell indicator\n"
        "  'BAL_TYP_CD' = Integer - Balance type code.\n"
        "  'FDL_FX_AMT' = float\n"
        "  'NETG_AGR_ID' = Integer\n"
        "  'LGL_CERTAINTY_FLG' = String - Legal certainty flag.\n"
        "  'src_txn_id' = String\n"
    )
    # Make suffix prompt with chat transcript
    om_cdm_rwa_mtrc_suffix_prompt = (
        "This is the result of `print(df.head())` :\n"
        "{df_head}"
    )
    # Initialize pandas dataframe agent
    agent_executor = create_pandas_dataframe_agent(
        llm,
        input_df,
        agent_type="tool-calling",
        verbose=True,
        allow_dangerous_code=True,
        return_intermediate_steps=True,
        prefix=om_cdm_rwa_mtrc_prefix_prompt,
        suffix=om_cdm_rwa_mtrc_suffix_prompt,
        number_of_head_rows=1
    )
    # Return agent executor
    return agent_executor

def init_mart_extn_table_pandas_agent(llm, input_df):
    """
    Initialize a pandas agent for the Mart Extn(OM_CDM_RWA_MTRC_EXTN) table.
    :param llm: The language model to use for the agent.
    :param input_df: The input dataframe containing the mart table data.
    :return: An agent executor for the Mart Extn table.
    """
    om_cdm_rwa_mtrc_extn_prefix_prompt = (
        "You are working with a pandas dataframe in Python. The name of the dataframe is 'df'.\n"
        "Here are the available important columns in the df:\n"
        "  'principal_gfcid' = Integer - Principal GFCID(OBLG IO).\n"
        "  'original_lgl_certainty_flg' = String\n"
        "  'org_imm_cancellable' = String\n"
        "  'incorp_cntry_assessment' = String\n"
        "  'trade_type' = String\n"
        "  'stale_prc_flag_2days' = String\n"
        "  'stale_prc_flag_6days' = String\n"
        "  'bal_typ_cd' = String - Balance type code.\n"
        "  'lrm_flg' = String\n"
        "  'IS_DAILY_MARGN' = String\n"
        "  'swwr_flag' = String\n"
        "  'swwr_recovery_rate' = Float\n"
        "  'haircut_eligible_status' = String\n"
    )
    # Make suffix prompt with chat transcript
    om_cdm_rwa_mtrc_extn_suffix_prompt = (
        "This is the result of print(df.head()):\n"
        "{df_head}"
    )
    # Initialize pandas dataframe agent
    agent_executor = create_pandas_dataframe_agent(
        llm,
        input_df,
        agent_type="tool-calling",
        verbose=True,
        allow_dangerous_code=True,
        return_intermediate_steps=True,
        prefix=om_cdm_rwa_mtrc_extn_prefix_prompt,
        suffix=om_cdm_rwa_mtrc_extn_suffix_prompt,
        number_of_head_rows=1
    )
    # Return agent executor
    return agent_executor

def make_multi_agents_graph(llm, input_content):
    """
    Call multiple agents to process the issue type and check steps.
    :param llm: The language model to use for the agents.
    :param issue_check_steps: The issue type and check steps.
    :param user_email_content: The user input.
    :param user_chat_input: Optional: user chat input to include in the check steps.
    :return:
    """
    # Get input dataframes
    input_dfs = get_input_dataframes()
    mart_agent = init_mart_table_pandas_agent(llm, input_dfs["om_cdm_rwa_mtrc"])
    mart_extn_agent = init_mart_extn_table_pandas_agent(llm, input_dfs["om_cdm_rwa_mtrc_extn"])
    # Convert agents as tools
    mart_agent_as_tool = mart_agent.as_tool(
        name="mart_tool",
        description="Tool to extract data from the OM_CDM_RWA_MTRC table."
    )
    mart_extn_agent_as_tool = mart_extn_agent.as_tool(
        name="mart_extn_tool",
        description="Tool to extract data from the OM_CDM_RWA_MTRC_EXTN table."
    )

    # Create the data extraction agent
    data_extraction_agent = create_react_agent(
        model=llm,
        tools=[get_check_step_to_process, get_prompt_using_table_name, mart_agent_as_tool, mart_extn_agent_as_tool],
        prompt=DATA_EXTRACTION_AGENT_PROMPT_2,
        name="data_extraction_agent"
    )

    # Invoke the data extraction agent with the input content
    result = data_extraction_agent.invoke( input = {
        "messages": [
            {
                "role": "user",
                "content": input_content,
            }
        ],
    }, config={"recursion_limit": 100})
    last_message_from_supervisor = ""
    # Return the result of the supervisor agent
    if not result or not result["messages"]:
        return "No messages returned from the supervisor agent."
    ai_messages = filter_messages(result["messages"], include_names=("data_extraction_agent",), exclude_tool_calls=False)
    for ai_message in ai_messages:
        last_message_from_supervisor = last_message_from_supervisor + "\n" + ai_message.content
    print(last_message_from_supervisor)
    return last_message_from_supervisor

#     # Create the data extraction agent
#     data_extraction_agent = create_react_agent(
#         model=llm,
#         tools=[get_prompt_using_table_name, mart_agent_as_tool, mart_extn_agent_as_tool],
#         prompt=DATA_EXTRACTION_AGENT_PROMPT,
#         name="data_extraction_agent"
#     )
#     if user_chat_input:
#         supervisor_agent_prompt = SUPERVISOR_AGENT_PROMPT_IN_CHAT
#         input_content = f"""#filter text: {user_email_content}\n\nUSER'S CHAT INPUT: {user_chat_input}"""
#     else:
#         supervisor_agent_prompt = SUPERVISOR_AGENT_PROMPT
#         input_content = f"""#filter text: {user_email_content}\n\n#Check steps: {issue_check_steps}"""
#     # Create a supervisor agent to manage the data extraction agent
#     supervisor_agent = create_supervisor(
#         model=llm,
#         agents=[data_extraction_agent],
#         prompt=supervisor_agent_prompt,
#         add_handoff_back_messages=True,
#         output_mode="full_history"
#     ).compile()

#     last_message_from_supervisor = ""
#     # Test the data extraction agent
#     # for chunk in supervisor_agent.stream(
#     #     {
#     #         "messages": [
#     #             {
#     #                 "role": "user",
#     #                 "content": input_content,
#     #             }
#     #         ]
#     #     },
#     #     config={"recursion_limit": 100}, stream_mode="updates"
#     # ):
#     #     pretty_print_messages(chunk, last_message=False)
#     #     # Store the last message from the supervisor agent
#     #     if "supervisor" in chunk:
#     #         supervisor_messages = filter_messages(chunk["supervisor"]["messages"], include_names=["supervisor"])
#     #         # If the supervisor agent has made a decision, break the loop
#     #         if "messages" in supervisor_messages:
#     #             last_message_from_supervisor = supervisor_messages["messages"][-1]
#     # Return the result of the supervisor agent
#     result = supervisor_agent.invoke(
#         {
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": input_content,
#                 }
#             ]
#         },
#         config={"recursion_limit": 100}
#     )
#     if not result or not result["messages"]:
#         return "No messages returned from the supervisor agent."
#     ai_messages = filter_messages(result["messages"], include_names=["supervisor"], exclude_tool_calls=True)
#     for ai_message in ai_messages:
#         last_message_from_supervisor = last_message_from_supervisor + "\n" + ai_message.content
#     # Return the last message from supervisor
#     return last_message_from_supervisor

def call_multi_agents_with_original_check_steps(llm, issue_type, email_content):
    """
    Call multiple agents to process the issue type and original check steps.
    :param llm: The language model to use for the agents.
    :param issue_type: The issue type to process.
    :param email_content: Email content.
    :return: A message indicating the next steps or an error message if the issue type is not supported.
    """
    if issue_type == "No Issue Matched":
        return "Please provide a valid issue type."
    elif issue_type == "Collateral Market Value drop observed for Inbound trades":
        return "Issue type is not supported yet."
    # Get the check steps for the issue type
    issue_check_steps = get_check_steps_using_issue_type(issue_type)
    # Convert dictionary to a JSON string
    json_string = json.dumps(issue_check_steps, indent=4)
    # Prepare the input text for the multi agents graph
    input_text = """###Filter text: {user_query}\n###All Check steps: ```json \n{input_dict}```"""
    # Format the input text with user query and check steps
    input_text = input_text.format(user_query=email_content, input_dict=json_string)
    # Call Multi Agents function with the original check steps
    return make_multi_agents_graph(llm, input_text)

def call_multi_agents_with_customized_check_steps(llm, issue_type, email_content, user_customized_check_step):
    """
    Call multiple agents to process the issue type and original check steps, including user customized check step.
    :param llm:
    :param issue_type:
    :param email_content:
    :param user_customized_check_step:
    :return: A message indicating the next steps or an error message if the issue type is not supported.
    """
    issue_type = "Collateral Market Value drop observed for Inbound trades"
    if issue_type == "No Issue Matched":
        return "Please provide a valid issue type."
    elif issue_type == "Collateral Market Value drop observed for Inbound trades":
        return "Issue type is not supported yet."
    # Get the check steps for the issue type
    # issue_check_steps = get_check_steps_using_issue_type(issue_type)
    # Make a JSON using user_customized_check_step
    followup_input = {'1': user_customized_check_step}
    # Convert dictionary to a JSON string
    json_string = json.dumps(followup_input, indent=4)
    # Prepare the input text for the multi agents graph
    input_text = """###Filter text: {user_query}\n###All Check steps: ```json \n{input_dict}```"""
    # Format the input text with user query and check steps
    input_text = input_text.format(user_query=email_content, input_dict=json_string)
    # Call Multi Agents function with the original check steps
    return make_multi_agents_graph(llm, input_text)

# #
# # user_query = """Hi GFICID '1123456918' dropped collateral
# #
# # Can you please check why highlighted security