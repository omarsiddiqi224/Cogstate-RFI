# rfiprocessor/agents/answer_generator.py

from typing import List, Dict, Any

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_advanced_llm
from rfiprocessor.services.prompt_loader import load_prompt

logger = get_logger(__name__)

class AnswerGeneratorAgent:
    """
    Agent responsible for generating a final answer based on a question
    and retrieved knowledge chunks using a RAG pattern.
    """

    def __init__(self):
        """
        Initializes the agent by setting up the LLM, loading the prompt,
        and creating the processing chain.
        """
        try:
            self.llm = get_advanced_llm()
            
            prompt_content = load_prompt("answer_generator")
            if not prompt_content:
                raise ValueError("Answer generator prompt could not be loaded.")
            
            prompt_template = PromptTemplate.from_template(prompt_content)
            
            self.chain = prompt_template | self.llm | StrOutputParser()
            logger.info("AnswerGeneratorAgent initialized successfully.")

        except Exception as e:
            logger.error(f"Error initializing AnswerGeneratorAgent: {str(e)}", exc_info=True)
            raise

    def generate_answer(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generates a draft answer by synthesizing information from context chunks.

        Args:
            question (str): The user's question from the new RFI.
            context_chunks (List[Dict[str, Any]]): A list of relevant chunks
                                                  retrieved from the vector store.

        Returns:
            str: The AI-generated draft answer.
        """
        logger.info(f"Generating answer for question: '{question[:50]}...'")

        if not context_chunks:
            logger.warning("No context chunks provided to generate answer.")
            return "No relevant information was found in the knowledge base to answer this question."

        # Format the context chunks into a single string for the prompt
        formatted_context = "\n\n---\n\n".join(
            [f"Source: {chunk['metadata'].get('source_filename', 'Unknown')}\n\n{chunk['content']}" for chunk in context_chunks]
        )

        try:
            # Invoke the RAG chain
            response = self.chain.invoke({
                "question": question,
                "context": formatted_context
            })
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            raise