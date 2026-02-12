import os
import uuid
from threading import Lock
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI

from graph import (
    call_multi_agents_with_customized_check_steps,
    call_multi_agents_with_original_check_steps,
    classify_issue_type,
    generate_final_conclusion,
)

load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', '')
os.environ['LANGSMITH_TRACING'] = 'true'
os.environ['LANGSMITH_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGSMITH_API_KEY'] = os.getenv('LANGSMITH_API_KEY', '')
os.environ['LANGSMITH_PROJECT'] = 'Explainability'

llm = ChatOpenAI(model='gpt-4o', temperature=0)
gemini_2_5_flash = llm


class ApiMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    label: str | None = None


class EmailSubmitRequest(BaseModel):
    input_text: str = Field(min_length=1)
    session_id: str | None = None


class FollowUpRequest(BaseModel):
    input_text: str | None = None
    user_chat_input: str = Field(min_length=1)
    issue_type: str | None = None
    session_id: str | None = None


class AgentResponse(BaseModel):
    session_id: str
    issue_type: str
    messages: list[ApiMessage]


app = FastAPI(title='RWA Explainability API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:4200'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

_session_lock = Lock()
_session_store: dict[str, dict[str, object]] = {}


def _get_or_create_session_id(session_id: str | None) -> str:
    if session_id and session_id.strip():
        return session_id.strip()
    return str(uuid.uuid4())


def _upsert_session(
    session_id: str,
    *,
    input_text: str | None = None,
    issue_type: str | None = None,
    messages: list[ApiMessage] | None = None,
) -> None:
    with _session_lock:
        state = _session_store.get(session_id, {'input_text': '', 'issue_type': '', 'messages': []})

        if input_text is not None:
            state['input_text'] = input_text
        if issue_type is not None:
            state['issue_type'] = issue_type
        if messages:
            existing = state.get('messages', [])
            existing.extend([message.model_dump() for message in messages])
            state['messages'] = existing

        _session_store[session_id] = state


def _get_session_value(session_id: str, key: str) -> str:
    with _session_lock:
        state = _session_store.get(session_id, {})
        value = state.get(key, '')
    return str(value) if value is not None else ''


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/api/rwa/email-submit', response_model=AgentResponse)
def submit_email(payload: EmailSubmitRequest) -> AgentResponse:
    input_text = payload.input_text.strip()
    if not input_text:
        raise HTTPException(status_code=400, detail='input_text is required')

    session_id = _get_or_create_session_id(payload.session_id)

    try:
        issue_type = classify_issue_type(llm, input_text)
        agent_response = call_multi_agents_with_original_check_steps(
            llm,
            issue_type,
            input_text,
        )
        final_conclusion = generate_final_conclusion(
            gemini_2_5_flash,
            input_text,
            agent_response,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Failed to process email submit: {exc}') from exc

    messages = [
        ApiMessage(
            role='assistant',
            content=f'Classified Issue Type: {issue_type}',
        ),
        ApiMessage(
            role='assistant',
            content=agent_response,
            label=final_conclusion,
        ),
    ]

    _upsert_session(
        session_id,
        input_text=input_text,
        issue_type=issue_type,
        messages=messages,
    )

    return AgentResponse(
        session_id=session_id,
        issue_type=issue_type,
        messages=messages,
    )


@app.post('/api/rwa/follow-up', response_model=AgentResponse)
def follow_up(payload: FollowUpRequest) -> AgentResponse:
    user_chat_input = payload.user_chat_input.strip()
    if not user_chat_input:
        raise HTTPException(status_code=400, detail='user_chat_input is required')

    session_id = _get_or_create_session_id(payload.session_id)
    input_text = (payload.input_text or '').strip() or _get_session_value(session_id, 'input_text')
    issue_type = (payload.issue_type or '').strip() or _get_session_value(session_id, 'issue_type')

    if not issue_type:
        if not input_text:
            raise HTTPException(
                status_code=400,
                detail='Provide input_text first through email-submit before follow-up',
            )
        issue_type = classify_issue_type(llm, input_text)

    try:
        agent_response = call_multi_agents_with_customized_check_steps(
            llm,
            issue_type,
            input_text,
            user_chat_input,
        )
        final_conclusion = generate_final_conclusion(
            gemini_2_5_flash,
            input_text,
            agent_response,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Failed to process follow-up: {exc}') from exc

    messages = [
        ApiMessage(role='user', content=user_chat_input),
        ApiMessage(role='assistant', content=agent_response, label=final_conclusion),
    ]

    _upsert_session(
        session_id,
        input_text=input_text,
        issue_type=issue_type,
        messages=messages,
    )

    return AgentResponse(
        session_id=session_id,
        issue_type=issue_type,
        messages=[messages[1]],
    )


if __name__ == '__main__':
    import uvicorn

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8000'))
    uvicorn.run('webapp_api:app', host=host, port=port, reload=True)
