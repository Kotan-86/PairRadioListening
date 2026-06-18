# 仕様: docs/spec/framework_amivoice.md#4.2
from __future__ import annotations

import json
import queue
from unittest.mock import MagicMock, patch

import pytest

from framework.amivoice.session_commands import amivoice_start_command
from framework.amivoice.wrp_session import WrpAmiVoiceSession, WrpAmiVoiceSessionFactory
from tests.framework.helpers import amivoice_utterance_payload


@pytest.mark.phase1c
def test_wrp_session_factory_creates_session() -> None:
    factory = WrpAmiVoiceSessionFactory(
        ws_url="wss://example.test/v1/",
        proxy_server_name="user:pass@proxy:8080",
    )
    session = factory.create(api_key="key", lecture_id="lec-1")
    assert session.lecture_id == "lec-1"
    assert session.api_key == "key"


@pytest.mark.phase1c
def test_wrp_session_connect_and_feed_resume() -> None:
    mock_wrp = MagicMock()
    mock_wrp.connect.return_value = True
    mock_wrp.feedDataResume.return_value = True
    mock_wrp.getWaitingResults.return_value = 0
    mock_wrp.feedData.return_value = True
    mock_wrp.feedDataPause.return_value = True

    with patch("framework.amivoice.wrp_session.Wrp.construct", return_value=mock_wrp):
        session = WrpAmiVoiceSession(
            lecture_id="lec-2",
            api_key="test-key",
            ws_url="wss://acp-api.amivoice.com/v1/",
            proxy_server_name="u:p@proxy:8080",
        )
        session.set_message_handler(lambda _raw: None)
        session.send_start_command(amivoice_start_command())
        pcm = b"\x00\x01" * 100
        session.send_audio(pcm)
        session.send_end_command("e")
        session.close()

    mock_wrp.setCodec.assert_called_with("LSB16K")
    mock_wrp.setGrammarFileNames.assert_called_with("-a2-ja-general")
    mock_wrp.setAuthorization.assert_called_with("test-key")
    mock_wrp.setProxyServerName.assert_called_with("u:p@proxy:8080")
    mock_wrp.connect.assert_called_once()
    mock_wrp.feedDataResume.assert_called_once()
    mock_wrp.feedData.assert_called_once_with(pcm, 0, len(pcm))
    mock_wrp.feedDataPause.assert_called_once()
    mock_wrp.disconnect.assert_called_once()


@pytest.mark.phase1c
def test_wrp_session_rejects_unknown_start_command() -> None:
    session = WrpAmiVoiceSession(lecture_id="lec-3", api_key="k", ws_url="wss://x/")
    with pytest.raises(ValueError, match="Unsupported"):
        session.send_start_command("s INVALID")


@pytest.mark.phase1c
def test_wrp_session_connect_failure_raises() -> None:
    mock_wrp = MagicMock()
    mock_wrp.connect.return_value = False
    mock_wrp.getLastMessage.return_value = "ERROR: connect failed"

    with patch("framework.amivoice.wrp_session.Wrp.construct", return_value=mock_wrp):
        session = WrpAmiVoiceSession(lecture_id="lec-4", api_key="k", ws_url="wss://x/")
        with pytest.raises(ConnectionError, match="connect failed"):
            session.send_start_command(amivoice_start_command())


@pytest.mark.phase1c
def test_wrp_session_delivers_finalized_via_worker() -> None:
    payload = amivoice_utterance_payload(text="worker経路", utterance_id="w-1")
    received: list[str] = []
    done = queue.Queue()

    def on_msg(raw: str) -> None:
        received.append(raw)
        done.put(True)

    mock_wrp = MagicMock()
    listener_holder: list = []

    def capture_listener(listener) -> None:
        listener_holder.append(listener)

    mock_wrp.setListener.side_effect = capture_listener

    with patch("framework.amivoice.wrp_session.Wrp.construct", return_value=mock_wrp):
        session = WrpAmiVoiceSession(lecture_id="lec-5", api_key="k", ws_url="wss://x/")
        session.set_message_handler(on_msg)
        assert listener_holder
        listener_holder[0].resultFinalized(json.dumps(payload))

    assert done.get(timeout=2.0)
    assert len(received) == 1
    assert json.loads(received[0])["text"] == "worker経路"
