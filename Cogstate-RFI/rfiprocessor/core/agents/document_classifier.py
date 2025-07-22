# rfiprocessor/agents/document_classifier.py

import json
from typing import Dict, Any

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_fast_llm
from rfiprocessor.services.prompt_loader import load_prompt

logger = get_logger(__name__)

class DocumentClassifierAgent:
    """
    An agent responsible for classifying documents into predefined categories
    (e.g., RFI/RFP, Supporting Document) and assigning a specific grade.
    """

    def __init__(self):
        """
        Initializes the agent by setting up the LLM, loading the prompt,
        and creating the processing chain.
        """
        try:
            # 1. Initialize the LLM provider
            self.llm = get_fast_llm()
            
            # 2. Load the classification prompt
            prompt_content = load_prompt("document_classifier")
            if not prompt_content:
                raise ValueError("Document classifier prompt could not be loaded.")
            
            self.prompt_template = PromptTemplate.from_template(prompt_content)
            
            # 3. Define the processing chain using LangChain Expression Language (LCEL)
            self.chain = self.prompt_template | self.llm | StrOutputParser()
            
            logger.info("DocumentClassifierAgent initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize DocumentClassifierAgent: {e}", exc_info=True)
            raise

    def classify(self, markdown_content: str) -> Dict[str, Any]:
        """
        Classifies the given markdown content.

        Args:
            markdown_content (str): The markdown content of the document to classify.
                                    To save on tokens, it's recommended to pass only the
                                    first N characters (e.g., 4000).

        Returns:
            Dict[str, Any]: A dictionary containing the 'document_type' and 'document_grade'.
                            Returns a default or error dictionary if classification fails.
        """
        logger.info("Attempting to classify document...")
        
        # To optimize for speed and cost, we only send the first part of the document.
        # The most important classification clues are usually at the beginning.
        truncated_content = markdown_content[:8000]

        try:
            # Invoke the chain with the document content
            response = self.chain.invoke({"markdown_content": truncated_content})
            logger.debug(f"LLM raw response for classification: {response}")

            # The response should be a JSON string, so we parse it.
            classification_result = json.loads(response)

            # Basic validation to ensure the keys we expect are present
            if "document_type" not in classification_result or "document_grade" not in classification_result:
                raise ValueError("LLM response is missing required keys 'document_type' or 'document_grade'.")

            logger.info(f"Document classified successfully as: {classification_result}")
            return classification_result

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from LLM response: {response}")
            # Fallback in case of malformed JSON
            return {"document_type": "Unclassified", "document_grade": "Parsing Error"}
        except Exception as e:
            logger.error(f"An unexpected error occurred during classification: {e}", exc_info=True)
            # General fallback for other errors (e.g., LLM API failure)
            return {"document_type": "Unclassified", "document_grade": "Classification Error"}