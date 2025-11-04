"""
LangGraph Vision-Enabled Browser Automation (Web Voyager Pattern)
==================================================================

ADVANCED APPROACH for complex UIs and visual verification.

This example demonstrates the Web Voyager pattern using annotated screenshots
with bounding boxes. The LLM sees numbered overlays on interactive elements
and decides which to interact with.

Features:
- Vision model analysis (GPT-4V, Claude 3.5 Sonnet)
- Bounding box annotation with numbered overlays
- Resilient to layout changes (no brittle CSS selectors)
- Good for complex, visually-driven interfaces

Installation:
    pip install playwright langgraph langchain-anthropic
    playwright install chromium

Usage:
    python vision_enabled_example.py
"""

import asyncio
import base64
import random
from typing import TypedDict, Annotated, List, Optional
from playwright.async_api import async_playwright, Page
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, add_messages
from langchain_core.tools import tool, InjectedToolArg
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class BBox(TypedDict):
    """Bounding box for an interactive element"""
    x: float  # Center X coordinate
    y: float  # Center Y coordinate
    text: str  # Element text content
    type: str  # Element type (button, link, input, etc.)
    ariaLabel: str  # Accessibility label


class Prediction(TypedDict):
    """Agent's predicted action"""
    action: str  # CLICK, TYPE, SCROLL, WAIT, ANSWER
    args: Optional[List[str]]  # Action arguments


class VisionBrowserState(TypedDict):
    """State for vision-enabled browser agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    page: Page  # Playwright page instance
    task: str  # User's task description
    current_url: str
    screenshot: str  # Base64-encoded annotated screenshot
    bboxes: List[BBox]  # Interactive elements with coordinates
    prediction: Prediction  # Parsed action from LLM
    scratchpad: List[BaseMessage]  # Action history
    observation: str  # Latest tool result
    step_count: int


# ============================================================================
# SCREENSHOT ANNOTATION
# ============================================================================

async def annotate_page(page: Page) -> dict:
    """
    Annotate page with bounding boxes for interactive elements.

    Returns screenshot + bounding box data for LLM analysis.
    """
    # JavaScript to mark interactive elements
    mark_script = """
    () => {
        // Remove any existing overlays first
        document.querySelectorAll('.langgraph-overlay').forEach(el => el.remove());

        const elements = [];
        const interactiveSelectors = 'a, button, input, textarea, select, [role="button"], [onclick]';
        const nodes = document.querySelectorAll(interactiveSelectors);

        nodes.forEach((node, index) => {
            const rect = node.getBoundingClientRect();

            // Filter by visibility and size
            if (rect.width < 20 || rect.height < 20) return;
            if (rect.top < 0 || rect.left < 0) return;

            // Create visual overlay
            const overlay = document.createElement('div');
            overlay.className = 'langgraph-overlay';
            overlay.style.cssText = `
                position: fixed;
                left: ${rect.left}px;
                top: ${rect.top}px;
                width: ${rect.width}px;
                height: ${rect.height}px;
                border: 2px dashed #${Math.floor(Math.random()*16777215).toString(16)};
                pointer-events: none;
                z-index: 999999;
                background: rgba(255, 0, 0, 0.1);
            `;

            // Add numbered label
            const label = document.createElement('div');
            label.textContent = index;
            label.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                background: red;
                color: white;
                padding: 2px 6px;
                font-size: 12px;
                font-weight: bold;
                font-family: Arial;
            `;
            overlay.appendChild(label);
            document.body.appendChild(overlay);

            // Store element data
            elements.push({
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                text: node.textContent?.trim().substring(0, 100) || '',
                type: node.tagName.toLowerCase(),
                ariaLabel: node.getAttribute('aria-label') || ''
            });
        });

        return elements;
    }
    """

    try:
        # Inject annotation script with retry
        for attempt in range(3):
            try:
                bboxes = await page.evaluate(mark_script)
                break
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(0.3)

        # Capture annotated screenshot
        screenshot_bytes = await page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()

        # Get current URL
        current_url = page.url

        return {
            "screenshot": screenshot_b64,
            "bboxes": bboxes,
            "current_url": current_url
        }

    except Exception as e:
        return {
            "screenshot": "",
            "bboxes": [],
            "current_url": "",
            "observation": f"Error annotating page: {str(e)}"
        }


# ============================================================================
# VISION-ENABLED TOOLS
# ============================================================================

@tool
async def click_bbox(
    bbox_id: int,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Click on an element by its bounding box ID (from the annotated screenshot).

    Args:
        bbox_id: The ID number shown on the screenshot overlay
    """
    try:
        page: Page = state["page"]
        bboxes: List[BBox] = state["bboxes"]

        if bbox_id < 0 or bbox_id >= len(bboxes):
            return f"Error: Invalid bbox_id {bbox_id}. Valid range: 0-{len(bboxes)-1}"

        bbox = bboxes[bbox_id]
        x, y = bbox["x"], bbox["y"]

        await page.mouse.click(x, y)

        label = bbox["text"] or bbox["ariaLabel"] or bbox["type"]
        return f"Clicked on element {bbox_id}: {label}"

    except Exception as e:
        return f"Error clicking element {bbox_id}: {str(e)}"


@tool
async def type_into_bbox(
    bbox_id: int,
    text: str,
    submit: bool = False,
    state: Annotated[dict, InjectedToolArg] = None
) -> str:
    """
    Type text into an input field identified by bounding box ID.

    Args:
        bbox_id: The ID number of the input field
        text: Text to type
        submit: Whether to press Enter after typing
    """
    try:
        page: Page = state["page"]
        bboxes: List[BBox] = state["bboxes"]

        if bbox_id < 0 or bbox_id >= len(bboxes):
            return f"Error: Invalid bbox_id {bbox_id}"

        bbox = bboxes[bbox_id]
        x, y = bbox["x"], bbox["y"]

        # Click to focus
        await page.mouse.click(x, y)
        await asyncio.sleep(0.2)

        # Clear existing text
        import platform
        select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
        await page.keyboard.press(select_all)
        await page.keyboard.press("Backspace")

        # Type text with human-like delays
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.12))

        # Optionally submit
        if submit:
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)

        return f"Typed '{text}' into element {bbox_id}{' and submitted' if submit else ''}"

    except Exception as e:
        return f"Error typing into element {bbox_id}: {str(e)}"


@tool
async def scroll_page_vision(
    direction: str,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Scroll the page up or down.

    Args:
        direction: 'up' or 'down'
    """
    try:
        page: Page = state["page"]

        delta_y = -500 if direction.lower() == "up" else 500
        await page.mouse.wheel(0, delta_y)
        await asyncio.sleep(0.5)

        return f"Scrolled {direction}"

    except Exception as e:
        return f"Error scrolling: {str(e)}"


@tool
async def navigate_vision(
    url: str,
    state: Annotated[dict, InjectedToolArg]
) -> str:
    """
    Navigate to a specific URL.

    Args:
        url: URL to navigate to
    """
    try:
        page: Page = state["page"]
        await page.goto(url, wait_until="networkidle")
        return f"Navigated to {url}"
    except Exception as e:
        return f"Error navigating: {str(e)}"


@tool
async def wait_vision(
    seconds: int = 2,
    state: Annotated[dict, InjectedToolArg] = None
) -> str:
    """
    Wait for a specified number of seconds.

    Args:
        seconds: Time to wait
    """
    await asyncio.sleep(seconds)
    return f"Waited {seconds} seconds"


# ============================================================================
# GRAPH NODES
# ============================================================================

async def annotate_node(state: VisionBrowserState) -> dict:
    """Capture and annotate page screenshot"""
    result = await annotate_page(state["page"])
    return result


async def agent_node(state: VisionBrowserState) -> dict:
    """
    Vision-enabled agent that analyzes annotated screenshots.

    Uses Claude 3.5 Sonnet or GPT-4V to understand visual UI.
    """
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    # Build prompt with visual context
    prompt_parts = [
        f"**Task**: {state['task']}",
        f"**Current URL**: {state['current_url']}",
        "",
        "You are viewing an annotated screenshot where interactive elements are marked with red numbered boxes.",
        "",
        "**Available Actions**:",
        "- CLICK <bbox_id>: Click on numbered element",
        "- TYPE <bbox_id> <text>: Type into numbered input field",
        "- SCROLL <up|down>: Scroll page",
        "- NAVIGATE <url>: Go to URL",
        "- WAIT <seconds>: Wait for page to load",
        "- ANSWER <text>: Provide final answer to user",
        "",
        f"**Interactive Elements** ({len(state['bboxes'])} found):",
    ]

    # List interactive elements (limit to first 30)
    for i, bbox in enumerate(state["bboxes"][:30]):
        label = bbox["text"][:50] or bbox["ariaLabel"] or bbox["type"]
        prompt_parts.append(f"  [{i}] {bbox['type']}: {label}")

    if len(state["bboxes"]) > 30:
        prompt_parts.append(f"  ... and {len(state['bboxes']) - 30} more")

    # Add scratchpad (action history)
    if state.get("scratchpad"):
        prompt_parts.append("")
        prompt_parts.append("**Previous Actions**:")
        for msg in state["scratchpad"][-5:]:  # Last 5 observations
            prompt_parts.append(f"  {msg.content}")

    prompt_parts.append("")
    prompt_parts.append("What action should you take next? Respond with ONE action only.")

    prompt_text = "\n".join(prompt_parts)

    # Build message with screenshot
    messages = [
        HumanMessage(content=[
            {"type": "text", "text": prompt_text},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{state['screenshot']}"
                }
            }
        ])
    ]

    # Get LLM response
    response = await llm.ainvoke(messages)

    # Parse action (simplified - production would be more robust)
    action_text = response.content.strip()
    parts = action_text.split(None, 2)

    if not parts:
        prediction = {"action": "WAIT", "args": ["2"]}
    else:
        action = parts[0].upper()
        args = parts[1:] if len(parts) > 1 else []
        prediction = {"action": action, "args": args}

    return {
        "prediction": prediction,
        "messages": [response]
    }


async def execute_action_node(state: VisionBrowserState) -> dict:
    """Execute the predicted action using vision tools"""
    prediction = state["prediction"]
    action = prediction["action"]
    args = prediction.get("args", [])

    observation = ""

    try:
        if action == "CLICK":
            bbox_id = int(args[0])
            observation = await click_bbox.ainvoke({"bbox_id": bbox_id, "state": state})

        elif action == "TYPE":
            bbox_id = int(args[0])
            text = " ".join(args[1:])
            observation = await type_into_bbox.ainvoke({
                "bbox_id": bbox_id,
                "text": text,
                "state": state
            })

        elif action == "SCROLL":
            direction = args[0] if args else "down"
            observation = await scroll_page_vision.ainvoke({"direction": direction, "state": state})

        elif action == "NAVIGATE":
            url = args[0] if args else "https://www.google.com"
            observation = await navigate_vision.ainvoke({"url": url, "state": state})

        elif action == "WAIT":
            seconds = int(args[0]) if args else 2
            observation = await wait_vision.ainvoke({"seconds": seconds, "state": state})

        elif action == "ANSWER":
            observation = " ".join(args)

        else:
            observation = f"Unknown action: {action}"

    except Exception as e:
        observation = f"Error executing {action}: {str(e)}"

    return {"observation": observation}


async def update_scratchpad_node(state: VisionBrowserState) -> dict:
    """Update action history"""
    scratchpad = state.get("scratchpad", [])
    observation = state.get("observation", "")
    step_count = state.get("step_count", 0) + 1

    scratchpad_msg = SystemMessage(content=f"Step {step_count}: {observation}")

    return {
        "scratchpad": scratchpad + [scratchpad_msg],
        "step_count": step_count
    }


# ============================================================================
# ROUTING
# ============================================================================

def should_continue(state: VisionBrowserState) -> str:
    """Determine next node based on action"""
    prediction = state.get("prediction", {})
    action = prediction.get("action", "")
    step_count = state.get("step_count", 0)

    # Check termination
    if action == "ANSWER":
        return "end"
    if step_count >= 15:  # Max steps
        return "end"

    # Continue
    return "annotate"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_vision_browser_agent() -> StateGraph:
    """Build vision-enabled browser automation graph"""
    workflow = StateGraph(VisionBrowserState)

    # Add nodes
    workflow.add_node("annotate", annotate_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("execute", execute_action_node)
    workflow.add_node("update_scratchpad", update_scratchpad_node)

    # Add edges
    workflow.add_edge(START, "annotate")
    workflow.add_edge("annotate", "agent")
    workflow.add_edge("agent", "execute")
    workflow.add_edge("execute", "update_scratchpad")

    # Conditional routing
    workflow.add_conditional_edges(
        "update_scratchpad",
        should_continue,
        {
            "annotate": "annotate",
            "end": END
        }
    )

    # Compile with memory
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# ============================================================================
# EXAMPLES
# ============================================================================

async def example_vision_search():
    """Example: Vision-enabled search automation"""
    print("=== Vision-Enabled Search Example ===\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Watch it work!
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        try:
            # Navigate to starting page
            await page.goto("https://www.google.com")

            # Create graph
            graph = create_vision_browser_agent()

            # Initial state
            initial_state = {
                "page": page,
                "task": "Search for 'LangGraph vision browser' and tell me the first result title",
                "current_url": "https://www.google.com",
                "screenshot": "",
                "bboxes": [],
                "prediction": {"action": "", "args": []},
                "scratchpad": [],
                "observation": "",
                "step_count": 0,
                "messages": []
            }

            # Run graph
            config = {"configurable": {"thread_id": "vision-session-1"}}

            print("Running vision-enabled agent...\n")
            async for event in graph.astream(initial_state, config):
                for node_name, node_output in event.items():
                    if node_name == "update_scratchpad":
                        step = node_output.get("step_count", 0)
                        obs = node_output.get("observation", "")
                        print(f"[Step {step}] {obs}")

                    if node_name == "agent":
                        pred = node_output.get("prediction", {})
                        print(f"  → Action: {pred.get('action')} {pred.get('args', [])}")

            # Get final state
            final_state = await graph.aget_state(config)
            print("\n" + "="*70)
            print("FINAL RESULT:")
            print(final_state.values.get("observation", "No answer"))
            print("="*70)

        finally:
            await browser.close()


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run vision-enabled examples"""
    await example_vision_search()


if __name__ == "__main__":
    asyncio.run(main())
