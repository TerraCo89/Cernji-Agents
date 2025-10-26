# Changelog

## v0.2.0 - Multi-Provider Support (2025-01-23)

### Added
- **OpenAI Provider Support**: Agent now supports both Claude and OpenAI
- **Configurable LLM Provider**: Switch between providers via `LLM_PROVIDER` env var
- **Cost-Effective Testing**: OpenAI (gpt-4o-mini) is ~20x cheaper than Claude
- **Provider Documentation**: New PROVIDERS.md comparing both options
- **Automatic Provider Detection**: Agent shows which provider/model on startup

### Changed
- Updated `.env` configuration with LLM provider options
- Enhanced `chat_node()` to support both API formats
- Added provider name to "Thinking..." messages
- Updated README with provider configuration examples

### Technical Details
- Added `openai>=1.0.0` to dependencies
- Created unified `call_llm()` function handling both providers
- OpenAI uses system message in messages array
- Claude uses separate system parameter
- Both providers support the same conversation flow

### Files Modified
- `resume_agent_langgraph.py`: Multi-provider support
- `pyproject.toml`: Added openai dependency
- `.env`: Added LLM_PROVIDER configuration
- `README.md`: Updated with provider docs
- `PROVIDERS.md`: New comparison document
- `CHANGELOG.md`: This file

### Testing
```bash
# Test with OpenAI (cheaper)
LLM_PROVIDER=openai uv run test_agent.py

# Test with Claude (higher quality)
LLM_PROVIDER=claude uv run test_agent.py
```

Both providers pass all tests successfully.

---

## v0.1.0 - Initial Release (2025-01-23)

### Added
- **Conversational Agent**: Real-time chat with LangGraph
- **LangGraph Integration**: StateGraph with checkpointing
- **Claude API**: Initial integration with Claude
- **Message History**: Append-only conversation state
- **Exit Handling**: Conditional routing for graceful exit
- **Windows Support**: UTF-8 encoding fix for emoji display

### Files
- `resume_agent_langgraph.py`: Main agent implementation
- `test_agent.py`: Automated testing script
- `README.md`: Documentation
- `CLAUDE.md`: Development guidance
- `pyproject.toml`: Dependencies
- `.env.example`: Configuration template
