"""
Local Arabic Model Service
Loads and manages the Arabic-trained Llama 3.2 3B model with LoRA adapter
"""

import os
import sys
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Ensure stdout is flushed immediately
# Don't wrap stdout here as it may conflict with uvicorn's stream handling
# Instead, use flush() calls where needed
if sys.platform == 'win32':
    import msvcrt
    # Just ensure we can flush, don't wrap stdout
    pass

try:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig
    )
    from peft import PeftModel
    from jinja2 import Template
except ImportError as e:
    logging.error(f"Missing required dependencies: {e}")
    logging.error("Please install: pip install peft bitsandbytes accelerate transformers")
    raise

# Configure logging
logger = logging.getLogger(__name__)


class LocalArabicModel:
    """
    Local Arabic Model Service
    Handles loading and inference for the Arabic-trained Llama 3.2 3B model
    """
    
    def __init__(self, checkpoint_path: Optional[str] = None):
        """
        Initialize the Local Arabic Model service
        
        Args:
            checkpoint_path: Path to checkpoint directory (default: auto-detect)
        """
        self.checkpoint_path = checkpoint_path or self._get_default_checkpoint_path()
        self.model = None
        self.tokenizer = None
        self.chat_template = None
        self.device = self._get_device()
        self._lock = threading.Lock()
        self._is_loaded = False
        self._loading = False
        
        logger.info(f"LocalArabicModel initialized with checkpoint: {self.checkpoint_path}")
        logger.info(f"Device: {self.device}")
    
    def _get_default_checkpoint_path(self) -> str:
        """Get default checkpoint path, downloading from cloud if needed"""
        # First, try environment variable (highest priority)
        env_path = os.getenv('LOCAL_MODEL_CHECKPOINT_PATH')
        if env_path:
            env_path_obj = Path(env_path)
            if env_path_obj.exists() and (env_path_obj / "adapter_model.safetensors").exists():
                logger.info(f"Found checkpoint at environment path: {env_path}")
                return env_path
            # If env path doesn't exist, try to download
            logger.info(f"Checkpoint not found at {env_path}, attempting download...")
            try:
                from download_checkpoint import download_checkpoint
                downloaded_path = download_checkpoint()
                if downloaded_path and Path(downloaded_path).exists():
                    return downloaded_path
            except ImportError:
                logger.debug("download_checkpoint module not available")
            except Exception as e:
                logger.warning(f"Checkpoint download failed: {e}")
        
        # Get the directory where this file is located
        current_dir = Path(__file__).parent
        
        # First, try to find checkpoints directory by searching up from current file
        search_dir = current_dir
        found_paths = []
        
        # Search up to 6 levels to find checkpoints directory
        for level in range(6):
            checkpoint_candidate = search_dir / "checkpoints" / "checkpoint-100000"
            try:
                abs_path = checkpoint_candidate.resolve()
                if abs_path.exists() and (abs_path / "adapter_model.safetensors").exists():
                    logger.info(f"Found checkpoint at: {abs_path}")
                    return str(abs_path)
                found_paths.append(str(abs_path))
            except (OSError, ValueError):
                pass
            
            # Also check parent directories
            if search_dir.parent != search_dir:
                search_dir = search_dir.parent
            else:
                break
        
        # Try specific known paths
        possible_paths = [
            # From Base_backend: Backend/Base_backend -> checkpoints
            current_dir.parent.parent / "checkpoints" / "checkpoint-100000",
            # From Backend: Backend -> checkpoints  
            current_dir.parent.parent.parent / "checkpoints" / "checkpoint-100000",
            # Absolute path fallback
            Path("C:/Users/Microsoft/Documents/Gurukul_new-main/checkpoints/checkpoint-100000"),
        ]
        
        # Try each specific path
        for checkpoint_path in possible_paths:
            try:
                abs_path = checkpoint_path.resolve()
                if abs_path.exists() and (abs_path / "adapter_model.safetensors").exists():
                    logger.info(f"Found checkpoint at: {abs_path}")
                    return str(abs_path)
                found_paths.append(str(abs_path))
            except (OSError, ValueError):
                found_paths.append(str(checkpoint_path))
        
        # Try to download checkpoint if cloud storage is configured
        try:
            from download_checkpoint import download_checkpoint
            downloaded_path = download_checkpoint()
            if downloaded_path and Path(downloaded_path).exists():
                return downloaded_path
        except ImportError:
            logger.debug("download_checkpoint module not available")
        except Exception as e:
            logger.warning(f"Checkpoint download attempt failed: {e}")
        
        # If none found, try one more time to download
        try:
            from download_checkpoint import download_checkpoint
            downloaded_path = download_checkpoint()
            if downloaded_path and Path(downloaded_path).exists():
                return downloaded_path
        except Exception as e:
            logger.debug(f"Final download attempt failed: {e}")
        
        # If still not found, log warning but don't raise error
        # The LLM service will handle missing model gracefully
        logger.warning(
            f"⚠️ Arabic model checkpoint not found. "
            f"The system will use API-based models (Groq/OpenAI) as fallback. "
            f"To enable local Arabic model, set LOCAL_MODEL_CHECKPOINT_PATH or configure cloud storage."
        )
        logger.warning(f"Attempted paths: {', '.join(found_paths[:5])}")
        
        # Return a path that will fail gracefully when model tries to load
        # This allows the service to start but model won't be available
        fallback_path = Path("/tmp/checkpoints/checkpoint-100000")
        fallback_path.mkdir(parents=True, exist_ok=True)
        return str(fallback_path)
        
        # Original error raising (commented out for graceful degradation)
        # raise FileNotFoundError(
        #     f"Checkpoint not found. Attempted paths:\n" + "\n".join(f"  - {p}" for p in found_paths[:10])
        # )
    
    def _get_device(self) -> str:
        """Determine the device to use (cuda, cpu)"""
        try:
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA available. Using GPU: {device_name}")
                print(f"      [INFO] CUDA detected! Using GPU: {device_name}")
                sys.stdout.flush()
                return "cuda"
            else:
                logger.warning("CUDA not available. Using CPU (inference will be slow)")
                print("      [WARN] CUDA not available. Using CPU (inference will be slow)")
                sys.stdout.flush()
                return "cpu"
        except Exception as e:
            logger.warning(f"Error checking CUDA: {e}. Falling back to CPU")
            print(f"      [WARN] Error checking CUDA: {e}. Using CPU")
            sys.stdout.flush()
            return "cpu"
    
    def _load_chat_template(self) -> Optional[Template]:
        """Load and parse the chat template from Jinja file"""
        try:
            template_path = Path(self.checkpoint_path) / "chat_template.jinja"
            if not template_path.exists():
                logger.warning(f"Chat template not found at {template_path}, using default")
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            return Template(template_content)
        except Exception as e:
            logger.error(f"Error loading chat template: {e}")
            return None
    
    def _load_model(self) -> None:
        """Load the base model and LoRA adapter"""
        if self._is_loaded:
            return
        
        if self._loading:
            # Wait for another thread to finish loading
            logger.info("Model is being loaded by another thread, waiting...")
            return
        
        with self._lock:
            if self._is_loaded:
                return
            
            self._loading = True
            
            try:
                logger.info("=" * 60)
                logger.info("Loading Arabic Model...")
                logger.info(f"Checkpoint: {self.checkpoint_path}")
                logger.info(f"Device: {self.device}")
                logger.info("=" * 60)
                
                # Load adapter config to get base model name
                adapter_config_path = Path(self.checkpoint_path) / "adapter_config.json"
                import json
                with open(adapter_config_path, 'r') as f:
                    adapter_config = json.load(f)
                
                base_model_name = adapter_config.get("base_model_name_or_path", 
                                                     "unsloth/llama-3.2-3b-instruct-bnb-4bit")
                
                logger.info(f"Base model: {base_model_name}")
                print(f"      [INFO] Base model: {base_model_name}")
                print(f"      [INFO] Device: {self.device.upper()}")
                sys.stdout.flush()
                
                # Note: Base model name includes "-bnb-4bit" so it's already quantized
                # We don't need to configure quantization_config - the model handles it
                
                # Load base model
                logger.info("Loading base model...")
                print("      [INFO] Downloading/loading base model from HuggingFace...")
                if self.device == "cuda":
                    print("      [INFO] GPU mode: Model is pre-quantized (4-bit), will use GPU")
                else:
                    print("      [INFO] CPU mode: This may take 1-2 minutes (downloading ~2GB)...")
                sys.stdout.flush()
                
                try:
                    if self.device == "cuda":
                        # GPU mode - model is already quantized
                        print("      [INFO] Loading quantized model to GPU...")
                        print("      [INFO] This may take 2-5 minutes (downloading ~2GB if first time)...")
                        print("      [INFO] Please wait - downloading/loading in progress...")
                        sys.stdout.flush()
                        
                        # Enable verbose output for HuggingFace
                        import os
                        import logging
                        logging.getLogger("transformers.modeling_utils").setLevel(logging.INFO)
                        logging.getLogger("transformers.configuration_utils").setLevel(logging.INFO)
                        os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"  # Enable progress bars
                        
                        print("      [INFO] Starting model download/load...")
                        print("      [INFO] If downloading, you should see progress bars below...")
                        sys.stdout.flush()
                        
                        # Wrap in try-except to catch any silent failures
                        print("      [INFO] Calling AutoModelForCausalLM.from_pretrained()...")
                        print("      [INFO] This may take 2-5 minutes - downloading ~2GB if first time")
                        print("      [INFO] Using memory-efficient loading to avoid paging file issues...")
                        sys.stdout.flush()
                        
                        try:
                            # Check bitsandbytes availability
                            try:
                                import bitsandbytes as bnb
                                print("      [INFO] bitsandbytes library available")
                                sys.stdout.flush()
                            except ImportError:
                                print("      [WARN] bitsandbytes not available - model may use more memory")
                                sys.stdout.flush()
                            
                            print("      [INFO] Starting model instantiation...")
                            print("      [INFO] This may take 1-3 minutes - please be patient...")
                            print("      [INFO] If this hangs, it may be a bitsandbytes/Windows compatibility issue")
                            sys.stdout.flush()
                            
                            # Use memory-efficient loading to avoid Windows paging file issues
                            # Note: The model name includes "-bnb-4bit" so it's pre-quantized
                            # We need bitsandbytes to load it properly
                            self.model = AutoModelForCausalLM.from_pretrained(
                                base_model_name,
                                device_map="auto",
                                trust_remote_code=True,
                                dtype=torch.float16,
                                low_cpu_mem_usage=True,  # Reduces memory usage during loading
                                max_memory={0: "10GiB"} if torch.cuda.is_available() else None,  # Limit GPU memory
                            )
                            print("      [INFO] ✅ Model weights loaded successfully!")
                            sys.stdout.flush()
                        except OSError as os_error:
                            if "paging file" in str(os_error).lower() or "1455" in str(os_error):
                                print(f"      [ERROR] Windows paging file (virtual memory) is too small!")
                                print(f"      [SOLUTION] Increase Windows virtual memory:")
                                print(f"        1. Open System Properties > Advanced > Performance Settings")
                                print(f"        2. Advanced tab > Virtual memory > Change")
                                print(f"        3. Set paging file size to at least 16GB (or System managed)")
                                print(f"        4. Restart your computer")
                                print(f"      [INFO] Alternatively, try closing other applications to free RAM")
                                sys.stdout.flush()
                            raise
                        except Exception as load_error:
                            print(f"      [ERROR] Failed during model.from_pretrained(): {type(load_error).__name__}: {load_error}")
                            import traceback
                            print("      [ERROR] Full traceback:")
                            traceback.print_exc()
                            sys.stdout.flush()
                            raise
                    else:
                        # CPU mode - load quantized model to CPU
                        print("      [INFO] Loading quantized model to CPU...")
                        sys.stdout.flush()
                        self.model = AutoModelForCausalLM.from_pretrained(
                            base_model_name,
                            device_map="cpu",
                            trust_remote_code=True,
                            dtype=torch.float32,
                            low_cpu_mem_usage=True,
                        )
                    
                    logger.info("Base model loaded successfully")
                    print("      [OK] Base model loaded!")
                    sys.stdout.flush()
                except MemoryError as e:
                    logger.error(f"Out of memory loading base model: {e}")
                    print(f"      [FAIL] Out of memory! Error: {e}")
                    print("      [INFO] Try closing other applications or use CPU mode")
                    sys.stdout.flush()
                    raise
                except Exception as e:
                    logger.error(f"Error loading base model: {e}")
                    print(f"      [FAIL] Error loading base model: {type(e).__name__}: {e}")
                    print("      [INFO] Full error details:")
                    import traceback
                    traceback.print_exc()
                    sys.stdout.flush()
                    raise
                
                # Load LoRA adapter
                logger.info("Loading LoRA adapter...")
                print("      [INFO] Loading LoRA adapter weights...")
                sys.stdout.flush()
                
                try:
                    self.model = PeftModel.from_pretrained(
                        self.model,
                        self.checkpoint_path,
                        adapter_name="arabic_adapter"
                    )
                    
                    # Merge adapter for faster inference (optional)
                    # self.model = self.model.merge_and_unload()
                    
                    # Set to evaluation mode
                    self.model.eval()
                    
                    logger.info("LoRA adapter loaded successfully")
                    print("      [OK] LoRA adapter loaded!")
                    sys.stdout.flush()
                except Exception as e:
                    logger.error(f"Error loading LoRA adapter: {e}")
                    print(f"      [FAIL] Error loading LoRA adapter: {e}")
                    sys.stdout.flush()
                    raise
                
                # Load tokenizer
                logger.info("Loading tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.checkpoint_path,
                    trust_remote_code=True
                )
                
                # Set pad token if not set
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                logger.info("Tokenizer loaded successfully")
                
                # Load chat template
                self.chat_template = self._load_chat_template()
                if self.chat_template:
                    logger.info("Chat template loaded successfully")
                
                self._is_loaded = True
                logger.info("=" * 60)
                logger.info("✅ Arabic Model loaded successfully!")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"❌ Error loading model: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            finally:
                self._loading = False
    
    def ensure_loaded(self) -> None:
        """Ensure model is loaded (lazy loading)"""
        if not self._is_loaded:
            self._load_model()
    
    def _format_prompt(self, prompt: str, messages: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Format prompt using chat template
        
        Args:
            prompt: User prompt text
            messages: Optional list of message dicts with 'role' and 'content'
        
        Returns:
            Formatted prompt string
        """
        if self.chat_template and messages:
            try:
                # Prepare messages for template
                template_messages = messages.copy() if messages else []
                
                # Add current user message if not in messages
                if not any(msg.get('role') == 'user' and msg.get('content') == prompt for msg in template_messages):
                    template_messages.append({"role": "user", "content": prompt})
                
                # Render template
                formatted = self.chat_template.render(
                    messages=template_messages,
                    add_generation_prompt=True,
                    date_string=datetime.now().strftime("%d %b %Y")
                )
                return formatted
            except Exception as e:
                logger.warning(f"Error formatting with template: {e}, using simple format")
        
        # Fallback: simple format
        return f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>\n\n"
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate response from the model
        
        Args:
            prompt: User input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            messages: Optional conversation history
        
        Returns:
            Generated response text
        """
        # Ensure model is loaded
        self.ensure_loaded()
        
        if not self._is_loaded or self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Cannot generate response.")
        
        try:
            # Format prompt
            formatted_prompt = self._format_prompt(prompt, messages)
            
            # Tokenize
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048  # Limit input length
            ).to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # Decode response
            # Remove input tokens from output
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "loaded": self._is_loaded,
            "checkpoint_path": self.checkpoint_path,
            "device": self.device,
            "has_chat_template": self.chat_template is not None,
            "model_type": "Llama 3.2 3B Instruct (Arabic-trained LoRA)",
        }


# Global instance (lazy loaded)
_local_model_instance: Optional[LocalArabicModel] = None
_instance_lock = threading.Lock()


def get_local_model(checkpoint_path: Optional[str] = None) -> LocalArabicModel:
    """
    Get or create the global LocalArabicModel instance
    
    Args:
        checkpoint_path: Optional checkpoint path (only used on first call)
    
    Returns:
        LocalArabicModel instance
    """
    global _local_model_instance
    
    if _local_model_instance is None:
        with _instance_lock:
            if _local_model_instance is None:
                _local_model_instance = LocalArabicModel(checkpoint_path)
    
    return _local_model_instance

