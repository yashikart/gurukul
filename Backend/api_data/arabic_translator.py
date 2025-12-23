"""
Arabic Translation Utility using Checkpoint Model
Translates English text to Arabic using the local checkpoint model
Falls back to LLM-based translation if checkpoint model is unavailable
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import the local Arabic model service
_local_model = None
_model_available = False

try:
    # Add Base_backend to path
    base_backend_path = Path(__file__).parent.parent / "Base_backend"
    if base_backend_path.exists():
        sys.path.insert(0, str(base_backend_path))
    
    from local_model_service import get_local_model
    _model_available = True
    logger.info("✅ Arabic checkpoint model service available")
except ImportError as e:
    logger.warning(f"⚠️ Arabic checkpoint model service not available: {e}")
    logger.warning("Translation will fallback to LLM-based translation")
    _model_available = False
except Exception as e:
    logger.warning(f"⚠️ Error loading Arabic checkpoint model: {e}")
    _model_available = False


def translate_to_arabic_with_checkpoint(text: str, checkpoint_path: Optional[str] = None) -> Optional[str]:
    """
    Translate English text to Arabic using the checkpoint model
    
    Args:
        text: English text to translate
        checkpoint_path: Optional path to checkpoint directory
        
    Returns:
        Arabic translation or None if translation fails
    """
    if not _model_available:
        logger.debug("Checkpoint model not available, skipping checkpoint translation")
        return None
    
    try:
        global _local_model
        
        # Get or initialize the local model
        if _local_model is None:
            logger.info("Initializing Arabic checkpoint model for translation...")
            _local_model = get_local_model(checkpoint_path)
        
        # Ensure model is loaded
        if not _local_model.is_loaded():
            logger.info("Loading Arabic checkpoint model...")
            _local_model.ensure_loaded()
        
        if not _local_model.is_loaded():
            logger.warning("Failed to load checkpoint model")
            return None
        
        # Create translation prompt
        translation_prompt = f"""Translate the following English text to Arabic. 
Provide only the Arabic translation without any additional text, explanations, or English words.

English text:
{text}

Arabic translation:"""
        
        logger.info(f"Translating text using checkpoint model (length: {len(text)} chars)")
        
        # Generate Arabic translation
        arabic_translation = _local_model.generate(
            prompt=translation_prompt,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9
        )
        
        if not arabic_translation or len(arabic_translation.strip()) == 0:
            logger.warning("Checkpoint model returned empty translation")
            return None
        
        # Clean up the response
        arabic_translation = arabic_translation.strip()
        
        # Remove common prefixes that might be added
        prefixes_to_remove = [
            "Arabic translation:",
            "الترجمة:",
            "Translation:",
            "الترجمة العربية:",
            "Arabic:",
            "عربي:"
        ]
        for prefix in prefixes_to_remove:
            if arabic_translation.startswith(prefix):
                arabic_translation = arabic_translation[len(prefix):].strip()
        
        logger.info(f"✅ Successfully translated using checkpoint model (output length: {len(arabic_translation)} chars)")
        return arabic_translation
        
    except Exception as e:
        logger.error(f"Error translating with checkpoint model: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def translate_to_arabic(text: str, fallback_llm_func=None, checkpoint_path: Optional[str] = None) -> str:
    """
    Translate English text to Arabic using checkpoint model with LLM fallback
    
    Args:
        text: English text to translate
        fallback_llm_func: Optional function to call for LLM-based translation fallback
                          Should accept (prompt: str, llm: str, language: str) -> str
        checkpoint_path: Optional path to checkpoint directory
        
    Returns:
        Arabic translation (from checkpoint or LLM fallback)
    """
    # First, try checkpoint model
    checkpoint_translation = translate_to_arabic_with_checkpoint(text, checkpoint_path)
    
    if checkpoint_translation:
        logger.info("✅ Using checkpoint model translation")
        return checkpoint_translation
    
    # Fallback to LLM-based translation
    if fallback_llm_func:
        logger.info("⚠️ Checkpoint model unavailable, using LLM fallback for translation")
        try:
            translation_prompt = f"""You are a professional translator. Your task is to translate the following English text to Arabic (العربية).

⚠️ CRITICAL REQUIREMENTS:
- You MUST translate the ENTIRE text to Arabic
- Use proper Arabic script (العربية)
- Maintain the exact same structure, sections, and formatting
- Translate ALL text including section headers
- Do NOT leave any English words untranslated
- The output must be 100% in Arabic

English Text to Translate:
{text}

Now provide the complete Arabic translation. Your response must be entirely in Arabic:"""
            
            translated_text = fallback_llm_func(translation_prompt, "grok", "english")
            
            if translated_text and len(translated_text.strip()) > 0:
                logger.info("✅ LLM fallback translation successful")
                return translated_text.strip()
            else:
                logger.warning("⚠️ LLM fallback returned empty translation")
        except Exception as e:
            logger.error(f"❌ LLM fallback translation failed: {e}")
    
    # If all translation methods fail, return original text
    logger.warning("⚠️ All translation methods failed, returning original text")
    return text


def is_checkpoint_available() -> bool:
    """Check if checkpoint model is available"""
    return _model_available


