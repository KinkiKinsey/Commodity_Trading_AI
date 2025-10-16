"""
LLM Source Module
=================
This module contains LLM-related functions for the Ringshell AI system.

Functions:
- LLMCallAgent: Agent for calling various LLM APIs (DeepSeek, OpenAI, etc.)
- shared_clients: Shared client management
"""

from .LLM_Call_Agent import LLMCallAgent

__all__ = ['LLMCallAgent']

