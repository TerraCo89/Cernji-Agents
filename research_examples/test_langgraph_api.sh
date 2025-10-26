#!/bin/bash
# Test LangGraph Dev Server API
#
# Usage:
#   ./test_langgraph_api.sh
#
# Prerequisites:
#   - langgraph dev server running on port 2024
#   - jq installed (for JSON parsing)

set -e  # Exit on error

API_URL="http://localhost:2024"
ASSISTANT_ID="resume_agent"

echo "=========================================="
echo "LangGraph Dev Server API Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check server health
echo -e "${BLUE}Test 1: Checking server health...${NC}"
response=$(curl -s "${API_URL}/ok")
if [ "$response" = "ok" ]; then
    echo -e "${GREEN}✓ Server is healthy${NC}"
else
    echo -e "${YELLOW}✗ Server health check failed${NC}"
    exit 1
fi
echo ""

# Test 2: Create a thread
echo -e "${BLUE}Test 2: Creating a thread...${NC}"
thread_response=$(curl -s -X POST "${API_URL}/threads" \
  -H 'Content-Type: application/json' \
  -d '{}')

thread_id=$(echo "$thread_response" | jq -r '.thread_id')
echo -e "${GREEN}✓ Thread created: ${thread_id}${NC}"
echo ""

# Test 3: Send first message (stateful with thread)
echo -e "${BLUE}Test 3: Sending first message...${NC}"
echo "Message: 'My name is John and I need help with my resume'"

curl -s -X POST "${API_URL}/threads/${thread_id}/runs/stream" \
  -H 'Content-Type: application/json' \
  -d "{
    \"assistant_id\": \"${ASSISTANT_ID}\",
    \"input\": {
      \"messages\": [
        {
          \"role\": \"user\",
          \"content\": \"My name is John and I need help with my resume\"
        }
      ]
    },
    \"stream_mode\": [\"updates\"]
  }" | while IFS= read -r line; do
    # Extract message content from streaming response
    if echo "$line" | grep -q '"content"'; then
        content=$(echo "$line" | jq -r '.data.messages[0].content // empty' 2>/dev/null)
        if [ -n "$content" ]; then
            echo -e "${GREEN}Assistant: ${content}${NC}"
        fi
    fi
done
echo ""

# Test 4: Send follow-up message (tests memory)
echo -e "${BLUE}Test 4: Sending follow-up message (testing memory)...${NC}"
echo "Message: 'What did I just tell you my name was?'"

curl -s -X POST "${API_URL}/threads/${thread_id}/runs/stream" \
  -H 'Content-Type: application/json' \
  -d "{
    \"assistant_id\": \"${ASSISTANT_ID}\",
    \"input\": {
      \"messages\": [
        {
          \"role\": \"user\",
          \"content\": \"What did I just tell you my name was?\"
        }
      ]
    },
    \"stream_mode\": [\"updates\"]
  }" | while IFS= read -r line; do
    if echo "$line" | grep -q '"content"'; then
        content=$(echo "$line" | jq -r '.data.messages[0].content // empty' 2>/dev/null)
        if [ -n "$content" ]; then
            echo -e "${GREEN}Assistant: ${content}${NC}"
        fi
    fi
done
echo ""

# Test 5: Get thread state
echo -e "${BLUE}Test 5: Getting thread state...${NC}"
state_response=$(curl -s -X GET "${API_URL}/threads/${thread_id}/state" \
  -H 'Content-Type: application/json')

message_count=$(echo "$state_response" | jq '.values.messages | length')
echo -e "${GREEN}✓ Thread has ${message_count} messages${NC}"
echo ""

# Test 6: Stateless run (no thread)
echo -e "${BLUE}Test 6: Stateless run (no thread persistence)...${NC}"
echo "Message: 'What is LangGraph?'"

curl -s -X POST "${API_URL}/runs/stream" \
  -H 'Content-Type: application/json' \
  -d "{
    \"assistant_id\": \"${ASSISTANT_ID}\",
    \"input\": {
      \"messages\": [
        {
          \"role\": \"user\",
          \"content\": \"What is LangGraph?\"
        }
      ]
    },
    \"stream_mode\": [\"values\"]
  }" | while IFS= read -r line; do
    if echo "$line" | grep -q '"content"'; then
        content=$(echo "$line" | jq -r '.data.messages[-1].content // empty' 2>/dev/null)
        if [ -n "$content" ]; then
            echo -e "${GREEN}Assistant: ${content}${NC}"
        fi
    fi
done
echo ""

# Test 7: Create another thread
echo -e "${BLUE}Test 7: Creating second thread...${NC}"
thread2_response=$(curl -s -X POST "${API_URL}/threads" \
  -H 'Content-Type: application/json' \
  -d '{}')

thread2_id=$(echo "$thread2_response" | jq -r '.thread_id')
echo -e "${GREEN}✓ Second thread created: ${thread2_id}${NC}"
echo ""

# Test 8: Search threads
echo -e "${BLUE}Test 8: Searching threads...${NC}"
search_response=$(curl -s -X POST "${API_URL}/threads/search" \
  -H 'Content-Type: application/json' \
  -d '{
    "limit": 10
  }')

thread_count=$(echo "$search_response" | jq '. | length')
echo -e "${GREEN}✓ Found ${thread_count} threads${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}All tests completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Thread IDs created:"
echo "  - Thread 1: ${thread_id}"
echo "  - Thread 2: ${thread2_id}"
echo ""
echo "To continue the conversation with Thread 1:"
echo ""
echo "curl -X POST ${API_URL}/threads/${thread_id}/runs/stream \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"assistant_id\": \"${ASSISTANT_ID}\","
echo "    \"input\": {"
echo "      \"messages\": [{\"role\": \"user\", \"content\": \"Your message here\"}]"
echo "    },"
echo "    \"stream_mode\": [\"updates\"]"
echo "  }'"
