#!/usr/bin/env python3
"""
Resume Agent CLI.

Command-line interface for the Resume Agent.
"""

import sys
from datetime import datetime, timezone
from resume_agent import build_conversation_graph, get_settings, get_provider_info


def main():
    """Main entry point for Resume Agent CLI."""
    # Enable UTF-8 encoding for Windows emoji support
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            # Python < 3.7
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    settings = get_settings()

    print("\n" + "="*60)
    print("🚀 Resume Agent - LangGraph Conversational Agent")
    print("="*60)

    # Show LLM provider configuration
    provider_name, model_name = get_provider_info()
    print(f"\n💡 LLM Provider: {provider_name}")
    print(f"💡 Model: {model_name}")

    print("\nWelcome! I'm your Resume Agent assistant.")
    print("I'm currently in development mode, learning to chat with you.")
    print("\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print("="*60)

    # Validate API key
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            print("\n❌ Error: OPENAI_API_KEY not found in environment")
            print("Please set your API key in .env file")
            sys.exit(1)
    else:
        if not settings.anthropic_api_key:
            print("\n❌ Error: ANTHROPIC_API_KEY not found in environment")
            print("Please set your API key in .env file")
            sys.exit(1)

    try:
        # Build conversation graph
        app = build_conversation_graph()

        # Initialize conversation state
        initial_state = {
            "messages": [],
            "should_continue": True
        }

        # Run conversation loop
        thread_id = f"conversation-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}

        # Start the conversation
        app.invoke(initial_state, config=config)

    except KeyboardInterrupt:
        print("\n\n👋 Conversation interrupted. Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
