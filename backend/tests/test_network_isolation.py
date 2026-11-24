"""
Test network isolation: /ask must NEVER make external network calls
during retrieval, thresholding, or validation.
Grounded answers are drawn strictly from local offline corpus.
"""

import socket
import pytest
from unittest.mock import patch

from app.generation.local_llm import LocalGroundedLLM
from app.generation.service import AskService
from app.models.schemas import AnswerStatus


@pytest.mark.asyncio
async def test_ask_makes_no_network_calls_during_retrieval_and_validation():
    """
    Blocks all network socket connections.
    AskService with local grounded LLM must execute 100% offline
    without attempting any network connection.
    """
    def blocked_connect(*args, **kwargs):
        raise RuntimeError("Network call attempted during retrieval/validation: forbidden under Non-Negotiable Rule 2!")

    with patch.object(socket.socket, "connect", side_effect=blocked_connect):
        service = AskService(llm=LocalGroundedLLM())
        
        # Test 1: In-scope constitutional query
        res = await service.answer_question("What is Article 21?")
        assert res.status == AnswerStatus.ANSWERED
        assert res.short_answer is not None
        assert "Article 21" in res.short_answer.simple
        
        # Test 2: In-scope BNSS query
        res_bnss = await service.answer_question("when can police arrest without warrant")
        assert res_bnss.status == AnswerStatus.ANSWERED
        assert res_bnss.short_answer is not None
        
        # Test 3: Out-of-scope query
        res_oos = await service.answer_question("chocolate cake recipe")
        assert res_oos.status == AnswerStatus.OUT_OF_SCOPE
