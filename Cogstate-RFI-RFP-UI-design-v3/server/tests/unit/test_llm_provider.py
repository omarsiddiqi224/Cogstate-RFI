"""
Unit tests for LLM provider functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from rfiprocessor.services.llm_provider import (
    get_gemini_llm,
    get_fast_llm,
    get_reasoning_llm,
    get_advanced_llm
)


class TestLLMProvider:
    """Test cases for LLM provider functions."""

    @patch('rfiprocessor.services.llm_provider.ChatGoogleGenerativeAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_gemini_llm(self, mock_config, mock_gemini_class):
        """Test getting Gemini LLM instance."""
        # Mock config
        mock_config.GEMINI_MODEL_NAME = "gemini-2.0-flash"
        mock_config.GOOGLE_API_KEY = "test-api-key"
        
        # Mock LLM instance
        mock_llm = Mock()
        mock_gemini_class.return_value = mock_llm
        
        result = get_gemini_llm()
        
        # Verify LLM was created with correct parameters
        mock_gemini_class.assert_called_once_with(
            model="gemini-2.0-flash",
            google_api_key="test-api-key",
            temperature=0.1,
            max_retries=2
        )
        assert result == mock_llm

    @patch('rfiprocessor.services.llm_provider.ChatOpenAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_fast_llm(self, mock_config, mock_openai_class):
        """Test getting fast LLM instance."""
        # Mock config
        mock_config.FAST_LLM_MODEL_NAME = "gpt-4-turbo"
        mock_config.OPENAI_API_KEY = "test-openai-key"
        
        # Mock LLM instance
        mock_llm = Mock()
        mock_openai_class.return_value = mock_llm
        
        result = get_fast_llm()
        
        # Verify LLM was created with correct parameters
        mock_openai_class.assert_called_once_with(
            model="gpt-4-turbo",
            temperature=0.1,
            openai_api_key="test-openai-key",
            timeout=10,
            max_retries=2
        )
        assert result == mock_llm

    @patch('rfiprocessor.services.llm_provider.ChatOpenAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_reasoning_llm(self, mock_config, mock_openai_class):
        """Test getting reasoning LLM instance."""
        # Mock config
        mock_config.REASONING_LLM_MODEL_NAME = "gpt-4o"
        mock_config.OPENAI_API_KEY = "test-openai-key"
        
        # Mock LLM instance
        mock_llm = Mock()
        mock_openai_class.return_value = mock_llm
        
        result = get_reasoning_llm()
        
        # Verify LLM was created with correct parameters
        mock_openai_class.assert_called_once_with(
            model="gpt-4o",
            openai_api_key="test-openai-key",
            max_retries=2
        )
        assert result == mock_llm

    @patch('rfiprocessor.services.llm_provider.ChatOpenAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_advanced_llm(self, mock_config, mock_openai_class):
        """Test getting advanced LLM instance."""
        # Mock config
        mock_config.ADVANCED_LLM_MODEL_NAME = "gpt-4o"
        mock_config.OPENAI_API_KEY = "test-openai-key"
        
        # Mock LLM instance
        mock_llm = Mock()
        mock_openai_class.return_value = mock_llm
        
        result = get_advanced_llm()
        
        # Verify LLM was created with correct parameters
        mock_openai_class.assert_called_once_with(
            model="gpt-4o",
            temperature=0.5,
            openai_api_key="test-openai-key",
            max_tokens=None,
            timeout=None,
            max_retries=3
        )
        assert result == mock_llm

    @patch('rfiprocessor.services.llm_provider.ChatGoogleGenerativeAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_gemini_llm_missing_api_key(self, mock_config, mock_gemini_class):
        """Test getting Gemini LLM with missing API key."""
        # Mock config with missing API key
        mock_config.GEMINI_MODEL_NAME = "gemini-2.0-flash"
        mock_config.GOOGLE_API_KEY = ""
        
        # Mock LLM instance
        mock_llm = Mock()
        mock_gemini_class.return_value = mock_llm
        
        result = get_gemini_llm()
        
        # Should still work with empty API key (will be handled by the LLM library)
        mock_gemini_class.assert_called_once_with(
            model="gemini-2.0-flash",
            google_api_key="",
            temperature=0.1,
            max_retries=2
        )
        assert result == mock_llm

    @patch('rfiprocessor.services.llm_provider.ChatOpenAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_fast_llm_missing_api_key(self, mock_config, mock_openai_class):
        """Test getting fast LLM with missing API key."""
        # Mock config with missing API key
        mock_config.FAST_LLM_MODEL_NAME = "gpt-4-turbo"
        mock_config.OPENAI_API_KEY = ""
        
        # Mock LLM instance
        mock_llm = Mock()
        mock_openai_class.return_value = mock_llm
        
        result = get_fast_llm()
        
        # Should still work with empty API key (will be handled by the LLM library)
        mock_openai_class.assert_called_once_with(
            model="gpt-4-turbo",
            temperature=0.1,
            openai_api_key="",
            timeout=10,
            max_retries=2
        )
        assert result == mock_llm

    def test_llm_provider_imports(self):
        """Test that all required imports are available."""
        try:
            from rfiprocessor.services.llm_provider import (
                get_gemini_llm,
                get_fast_llm,
                get_reasoning_llm,
                get_advanced_llm
            )
            assert True  # Imports successful
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    @patch('rfiprocessor.services.llm_provider.ChatGoogleGenerativeAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_gemini_llm_initialization_error(self, mock_config, mock_gemini_class):
        """Test handling of Gemini LLM initialization error."""
        # Mock config
        mock_config.GEMINI_MODEL_NAME = "gemini-2.0-flash"
        mock_config.GOOGLE_API_KEY = "test-api-key"
        
        # Mock initialization error
        mock_gemini_class.side_effect = Exception("API key invalid")
        
        with pytest.raises(Exception) as exc_info:
            get_gemini_llm()
        
        assert "API key invalid" in str(exc_info.value)

    @patch('rfiprocessor.services.llm_provider.ChatOpenAI')
    @patch('rfiprocessor.services.llm_provider.config')
    def test_get_advanced_llm_initialization_error(self, mock_config, mock_openai_class):
        """Test handling of advanced LLM initialization error."""
        # Mock config
        mock_config.ADVANCED_LLM_MODEL_NAME = "gpt-4o"
        mock_config.OPENAI_API_KEY = "test-openai-key"
        
        # Mock initialization error
        mock_openai_class.side_effect = Exception("Model not found")
        
        with pytest.raises(Exception) as exc_info:
            get_advanced_llm()
        
        assert "Model not found" in str(exc_info.value) 