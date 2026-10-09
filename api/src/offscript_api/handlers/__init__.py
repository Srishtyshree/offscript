"""Handlers package for route execution."""

from offscript_api.handlers.ai import handle_ai_route
from offscript_api.handlers.human import generate_human_card_content, handle_human_route
from offscript_api.handlers.search import build_search_query, build_search_url, handle_search_route

__all__ = [
    "build_search_query",
    "build_search_url",
    "generate_human_card_content",
    "handle_ai_route",
    "handle_human_route",
    "handle_search_route",
]
