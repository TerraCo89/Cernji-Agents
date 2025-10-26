#!/usr/bin/env python3
"""Test message serialization for debugging KeyError: 'role'"""

import json
from langchain_core.messages import AIMessage, HumanMessage

# Test 1: How does LangGraph serialize messages?
human_msg = HumanMessage(content="Hello")
ai_msg = AIMessage(content="Hi there!")

print("="*60)
print("Message Serialization Test")
print("="*60)

print("\n1. HumanMessage object:")
print(f"   Type: {type(human_msg)}")
print(f"   Content: {human_msg.content}")
print(f"   Has 'role' attr: {hasattr(human_msg, 'role')}")
if hasattr(human_msg, 'role'):
    print(f"   Role: {human_msg.role}")

print("\n2. AIMessage object:")
print(f"   Type: {type(ai_msg)}")
print(f"   Content: {ai_msg.content}")
print(f"   Has 'role' attr: {hasattr(ai_msg, 'role')}")
if hasattr(ai_msg, 'role'):
    print(f"   Role: {ai_msg.role}")

print("\n3. Dict representation (model_dump):")
print(f"   HumanMessage: {human_msg.model_dump()}")
print(f"   AIMessage: {ai_msg.model_dump()}")

print("\n4. Dict representation (model_dump with mode='json'):")
print(f"   HumanMessage: {human_msg.model_dump(mode='json')}")
print(f"   AIMessage: {ai_msg.model_dump(mode='json')}")

print("\n5. What keys are in the dict?")
human_dict = human_msg.model_dump()
ai_dict = ai_msg.model_dump()
print(f"   HumanMessage keys: {list(human_dict.keys())}")
print(f"   AIMessage keys: {list(ai_dict.keys())}")

print("\n6. Direct attribute access:")
print(f"   HumanMessage.type: {human_msg.type}")
print(f"   AIMessage.type: {ai_msg.type}")

print("\n")
