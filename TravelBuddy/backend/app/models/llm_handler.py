"""
LLM Handler with proper initialization and error handling
"""

import os
import logging
import time
from typing import Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM, pipeline
import torch

logger = logging.getLogger(_name_)

class LLMHandler:
    """Handler for LLM operations with IBM Granite or HuggingFace models"""
    
    def _init_(self, model_name: Optional[str] = "ibm-granite/granite-3.0-8b-instruct", hf_token: Optional[str] = None):
        """
        Initialize LLM Handler
        
        Args:
            model_name: Name of the model to use
                - "ibm-granite/granite-3.0-8b-instruct" (default)
                - "google/flan-t5-base"
                - Any HuggingFace model path
        """
        self.model_name = model_name
        self.hf_token = hf_token
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # Device selection
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize model
        self._load_model()
    
    def _load_model(self):
        """Load the specified model"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            # If no model name provided, skip heavy model loading and use fallback mode
            if not self.model_name:
                logger.warning("No model name provided — running in fallback mode")
                self.model = None
                self.tokenizer = None
                self.pipeline = None
                return
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_auth_token=self.hf_token or None
            )
            
            # Ensure pad token exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Choose model class based on model type (seq2seq vs causal)
            model_lower = (self.model_name or '').lower()
            is_seq2seq = 't5' in model_lower or 'flan' in model_lower or 'seq2seq' in model_lower

            if is_seq2seq:
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True,
                    use_auth_token=self.hf_token or None
                )
                gen_task = "text2text-generation"
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True,
                    use_auth_token=self.hf_token or None
                )
                gen_task = "text-generation"
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            # Create pipeline (use text2text for seq2seq models like Flan-T5)
            self.pipeline = pipeline(
                gen_task,
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("✅ Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.warning("Falling back to simple response mode")
            self.model = None
            self.tokenizer = None
            self.pipeline = None
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        Generate text response
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
        
        Returns:
            Generated text
        """
        try:
            if self.pipeline is None:
                # Fallback response if model isn't loaded
                return self._fallback_response(prompt)
            
            # Generate
            outputs = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **kwargs
            )
            
            # Extract generated text
            generated_text = outputs[0]['generated_text']
            
            # Remove prompt from output
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return self._fallback_response(prompt)

    def generate_safe(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
        top_p: float = 0.9,
        retries: int = 2,
        timeout: float = 30.0,
        **kwargs
    ) -> str:
        """Generate text with retries, sanitization and length guards.

        This wrapper attempts to call the model and falls back to a safe
        response when the model is unavailable or fails repeatedly.
        """
        prompt = (prompt or "").strip()
        if not prompt:
            return "I'm here to help — what would you like to do today?"

        attempt = 0
        while attempt <= retries:
            try:
                start = time.time()
                text = self.generate(prompt, max_tokens=max_tokens, temperature=temperature, top_p=top_p, **kwargs)
                # basic sanitization
                if not isinstance(text, str):
                    raise ValueError("Non-string response from model")

                text = text.strip()
                # guard: if model echoed the prompt, trim it
                if text.lower().startswith(prompt.lower()[: min(200, len(prompt))]):
                    # don't return the whole prompt; try to extract after the prompt
                    # fallback to safer canned response below if empty
                    candidate = text[len(prompt):].strip()
                    if candidate:
                        text = candidate

                # length guard
                if len(text) > 4000:
                    text = text[:4000].rsplit('.', 1)[0] + '.'

                if text:
                    return text

                # empty response - retry
                attempt += 1
                time.sleep(0.5)
                if time.time() - start > timeout:
                    break

            except Exception as e:
                logger.warning(f"generate_safe attempt {attempt} failed: {e}")
                attempt += 1
                time.sleep(0.5)

        # After retries, return fallback
        return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Provide a simple fallback response when model isn't available"""
        prompt_lower = prompt.lower()
        
        # Greeting detection
        if any(word in prompt_lower for word in ['hi', 'hello', 'hey', 'greetings']):
            return "Hello! Welcome to Kerala Travel Assistant. How can I help plan your trip today?"
        
        # Weather queries
        if 'weather' in prompt_lower:
            return "I can help you check the weather conditions for your destination. Please specify which city in Kerala you're interested in."
        
        # Hotel queries
        if 'hotel' in prompt_lower:
            return "I can help you find hotels in Kerala. Which city would you like to explore?"
        
        # Itinerary queries
        if any(word in prompt_lower for word in ['itinerary', 'plan', 'trip']):
            return "I'd be happy to help you plan your Kerala itinerary. How many days are you planning to visit?"
        
        # Generic response
        return "I'm here to help you plan your Kerala trip. You can ask me about hotels, attractions, weather, or creating an itinerary!"
    
    def chat(
        self,
        messages: list,
        max_tokens: int = 150,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response from chat history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated response
        """
        # Format messages into a single prompt
        prompt = self._format_chat_prompt(messages)
        return self.generate(prompt, max_tokens, temperature, **kwargs)
    
    def _format_chat_prompt(self, messages: list) -> str:
        """Format chat messages into a prompt"""
        formatted = ""
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                formatted += f"System: {content}\n\n"
            elif role == 'user':
                formatted += f"User: {content}\n\n"
            elif role == 'assistant':
                formatted += f"Assistant: {content}\n\n"
        
        formatted += "Assistant: "
        return formatted
    
    def is_available(self) -> bool:
        """Check if model is loaded and available"""
        return self.model is not None and self.pipeline is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_available": self.is_available(),
            "has_cuda": torch.cuda.is_available()
        }
