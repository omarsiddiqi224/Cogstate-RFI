# rfiprocessor/core/agents/answer_drafter.py

from typing import Any

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_advanced_llm
from rfiprocessor.services.prompt_loader import load_prompt

logger = get_logger(__name__)

class AnswerDraftingAgent:
    """
    An agent that refines a user-edited draft answer into a polished,
    professional response that is synchronized with the original question.
    """

    def __init__(self):
        """
        Initializes the agent by setting up the LLM, loading the prompt,
        and creating the processing chain.
        """
        try:
            self.llm = get_advanced_llm()
            
            prompt_content = load_prompt("answer_drafter")
            if not prompt_content:
                raise ValueError("Answer drafter prompt could not be loaded.")
            
            prompt_template = PromptTemplate.from_template(prompt_content)
            
            self.chain = prompt_template | self.llm | StrOutputParser()
            logger.info("AnswerDraftingAgent initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize AnswerDraftingAgent: {e}", exc_info=True)
            raise

    def draft_answer(self, question: str, user_draft_answer: str) -> str:
        """
        Takes a question and a user's draft to produce a polished final answer.

        Args:
            question (str): The original question from the RFI.
            user_draft_answer (str): The user-edited text, which may be rough.

        Returns:
            str: The polished, final answer in markdown format.
        """
        logger.info(f"Drafting polished answer for question: '{question[:50]}...'")
        
        try:
            # Invoke the chain with the required inputs
            polished_answer = self.chain.invoke({
                "question": question,
                "user_draft_answer": user_draft_answer
            })
            return polished_answer.strip()
        except Exception as e:
            logger.error(f"Error during answer drafting for question '{question[:50]}...': {e}", exc_info=True)
            return "An error occurred while refining the draft. Please try again."