import pandas as pd
import json
from typing import Annotated
from prompt import (
    PANDAS_AGENT_PROMPT_MART,
    PANDAS_AGENT_PROMPT_MART_EXTN,
    PANDAS_AGENT_PROMPT_TXN_MAP,
    PANDAS_AGENT_PROMPT_DSFT_TXN_RESULT,
    PANDAS_AGENT_PROMPT_DSFT_CONC_RESULT,
    PANDAS_AGENT_PROMPT_DSFT_BASE_SUBASSETCLASS,
    PANDAS_AGENT_SUFFIX
)

# Available sheets names in Excel file with mockup data
sheet_names = [
    "om_cdm_rwa_mtrc",
    "om_cdm_rwa_mtrc_extn",
    "dsft_conc_txn_result",
    "dsft_conc_result_txn_map",
    "dsft_conc_result",
    "dsft_fl_base_subassetclass",
    "dsft_eqty_issuer_con_def",
    "dsft_fl_issuer_trigger",
    "dsft_fl_issue_trigger"
]

def extract_data_from_json(json_data: dict | list, field_to_extract: str) -> str | int | None:
    """
    Extracts specific value for a field from a JSON data input. following the structure of the JSON input.
    {
        "BAL_TYP_CD": xx,
        "Balance Amount": xxxxx,
        "OI_CTL_RNA_MISC": {
            "MESS_AGE_ID": "value",
            "LG_CERTAINTY_FLG": "Y"
        }
    }
    :param field_to_extract: The field to extract from the JSON input.
    :param json_data: JSON input
    :return: The value of the field if found, else None.
    """
    if '.' in field_to_extract:
        field_to_extract = field_to_extract.split('.')[-1]  # Extract the last part after the dot
    if isinstance(json_data, dict):
        if field_to_extract in json_data:
            return json_data[field_to_extract]
        for k, v in json_data.items():
            result = extract_data_from_json(v, field_to_extract)
            if result is not None:
                return result
    elif isinstance(json_data, list):
        for item in json_data:
            result = extract_data_from_json(item, field_to_extract)
            if result is not None:
                return result
    return None

def get_prompt_using_table_name(table_name: str, user_query: str, check_step_for_tool: str) -> str | None:
    """
    Get the prompt dynamically for the given valid dataframe/table name
    Available dataframes are,
    * om_cdm_rwa_mtrc
    * om_cdm_rwa_mtrc_extn
    * dsft_conc_txn_result
    * dsft_conc_result_txn_map
    * dsft_conc_result
    * dsft_fi_base_subassetclass
    * dsft_eqty_issuer_con_def
    * dsft_fl_issuer_trigger
    * dsft_fl_issue_trigger
    :param check_step_for_tool: Check step pass to the tool to process.
    :param table_name: This is the name of the dataframe/table
    :param user_query: User query to filter the dataframe
    :param check_step_for_tool: Checks steps with USER's CHAT INPUT to filter the dataframe
    :return: Prompt string for the given table name
    """
    if table_name in sheet_names:
        if table_name == "om_cdm_rwa_mtrc":
            return PANDAS_AGENT_PROMPT_MART.format(filter_text=user_query, check_step=check_step_for_tool)
        elif table_name == "om_cdm_rwa_mtrc_extn":
            return PANDAS_AGENT_PROMPT_MART_EXTN.format(filter_text=user_query, check_step=check_step_for_tool)
        elif table_name == "dsft_conc_txn_result":
            return PANDAS_AGENT_PROMPT_DSFT_TXN_RESULT.format(filter_text=user_query, check_step=check_step_for_tool)
        elif table_name == "dsft_conc_result_txn_map":
            return PANDAS_AGENT_PROMPT_TXN_MAP.format(filter_text=user_query, check_step=check_step_for_tool)
        elif table_name == "dsft_conc_result":
            return PANDAS_AGENT_PROMPT_DSFT_CONC_RESULT.format(filter_text=user_query, check_step=check_step_for_tool)
        elif table_name == "dsft_fi_base_subassetclass":
            return PANDAS_AGENT_PROMPT_DSFT_BASE_SUBASSETCLASS.format(filter_text=user_query, check_step=check_step_for_tool)
    return None  # Return None if the table name is not valid



# @tool
def get_check_step_to_process(
    step_number: Annotated[str, "Step Number to retrieve from the check steps json"],
    check_steps: Annotated[str, "JSON string with all the Check steps"]) -> str:
    """
    Get the check step to process next based on the step number and check steps provided.
    :param step_number: Step Number to retrieve from the check steps json.
    :param check_steps: Full JSON string with steps.
    :return: Check step to process next
    """
    # Parse check_steps if it's a string
    if isinstance(check_steps, str):
        try:
            check_steps = json.loads(check_steps)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string provided for check_steps")
    check_step_description = check_steps.get(step_number)
    return check_step_description