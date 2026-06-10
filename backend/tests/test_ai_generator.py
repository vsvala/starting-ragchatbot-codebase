import pytest
from unittest.mock import MagicMock, patch
from ai_generator import AIGenerator


@pytest.fixture
def mock_client():
    with patch("ai_generator.anthropic.Anthropic") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def generator(mock_client):
    return AIGenerator(api_key="test-key", model="claude-test")


def make_text_response(text="Direct answer"):
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def make_tool_use_response(tool_name="search_course_content", tool_input=None, tool_id="tool_abc"):
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.id = tool_id
    block.input = tool_input or {"query": "test query"}
    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [block]
    return response


def test_direct_text_response(generator, mock_client):
    mock_client.messages.create.return_value = make_text_response("Direct answer")

    result = generator.generate_response("What is AI?")

    assert result == "Direct answer"


def test_tool_use_triggers_tool_execution(generator, mock_client):
    tool_response = make_tool_use_response()
    followup = make_text_response("Final answer after tool")
    mock_client.messages.create.side_effect = [tool_response, followup]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "Search results here"

    result = generator.generate_response("Tell me about RAG", tool_manager=tool_manager)

    tool_manager.execute_tool.assert_called_once()
    assert result == "Final answer after tool"


def test_execute_tool_called_with_correct_name(generator, mock_client):
    tool_response = make_tool_use_response(
        tool_name="search_course_content",
        tool_input={"query": "RAG basics"}
    )
    mock_client.messages.create.side_effect = [tool_response, make_text_response("Answer")]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "results"

    generator.generate_response("query", tool_manager=tool_manager)

    assert tool_manager.execute_tool.call_args[0][0] == "search_course_content"


def test_execute_tool_called_with_correct_kwargs(generator, mock_client):
    tool_input = {"query": "vector stores", "course_name": "RAG Course"}
    mock_client.messages.create.side_effect = [
        make_tool_use_response(tool_input=tool_input),
        make_text_response("Answer")
    ]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "results"

    generator.generate_response("query", tool_manager=tool_manager)

    call_kwargs = tool_manager.execute_tool.call_args[1]
    assert call_kwargs["query"] == "vector stores"
    assert call_kwargs["course_name"] == "RAG Course"


def test_tool_result_in_followup_messages(generator, mock_client):
    mock_client.messages.create.side_effect = [
        make_tool_use_response(),
        make_text_response("Answer")
    ]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "Search results content"

    generator.generate_response("query", tool_manager=tool_manager)

    second_call_messages = mock_client.messages.create.call_args_list[1][1]["messages"]
    tool_result_messages = [
        m for m in second_call_messages
        if isinstance(m.get("content"), list)
        and any(c.get("type") == "tool_result" for c in m["content"])
    ]
    assert len(tool_result_messages) == 1


def test_conversation_history_appended_to_system(generator, mock_client):
    mock_client.messages.create.return_value = make_text_response()

    generator.generate_response("query", conversation_history="User: hi\nAssistant: hello")

    system_used = mock_client.messages.create.call_args[1]["system"]
    assert "Previous conversation:" in system_used
    assert "User: hi" in system_used


def test_no_history_uses_plain_system_prompt(generator, mock_client):
    mock_client.messages.create.return_value = make_text_response()

    generator.generate_response("query")

    system_used = mock_client.messages.create.call_args[1]["system"]
    assert system_used == AIGenerator.SYSTEM_PROMPT


def test_empty_response_returns_empty_string(generator, mock_client):
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = []
    mock_client.messages.create.return_value = response

    result = generator.generate_response("query")

    assert result == ""


def test_tools_absent_when_not_provided(generator, mock_client):
    mock_client.messages.create.return_value = make_text_response()

    generator.generate_response("query")

    call_kwargs = mock_client.messages.create.call_args[1]
    assert "tools" not in call_kwargs
