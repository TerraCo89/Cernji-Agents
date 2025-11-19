# Complete Working Examples

## Example 1: Weather Dashboard

### Backend (Python)

```python
# src/weather_agent/graph.py
import uuid
from typing import Annotated, Sequence, TypedDict
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer, push_ui_message
from langgraph.prebuilt import ToolNode


class WeatherState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]


@tool
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    # Mock data - replace with real API
    return {
        "city": city,
        "temperature": 72,
        "conditions": "Sunny",
        "humidity": 65,
        "wind_speed": 10,
        "forecast": [
            {"day": "Mon", "high": 75, "low": 60, "conditions": "Sunny"},
            {"day": "Tue", "high": 73, "low": 58, "conditions": "Cloudy"},
            {"day": "Wed", "high": 70, "low": 55, "conditions": "Rainy"},
        ]
    }


def agent_node(state: WeatherState):
    """Agent decides whether to call weather tool."""
    llm = ChatAnthropic(model="claude-sonnet-4-5")
    llm_with_tools = llm.bind_tools([get_weather])
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def ui_node(state: WeatherState):
    """Emit weather UI component after tool execution."""
    last_message = state["messages"][-1]

    # Check if tool was called
    if not isinstance(last_message, ToolMessage):
        return {}

    if last_message.name != "get_weather":
        return {}

    # Parse weather data
    import json
    weather_data = json.loads(last_message.content)

    # Create AI message
    message = AIMessage(
        id=str(uuid.uuid4()),
        content=f"Here's the weather for {weather_data['city']}"
    )

    # Push weather dashboard component
    push_ui_message(
        "weather_dashboard",
        weather_data,
        message=message
    )

    return {"messages": [message]}


def should_continue(state: WeatherState) -> str:
    """Route to tools or UI."""
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "ui"


# Build graph
tool_node = ToolNode(tools=[get_weather])

workflow = StateGraph(WeatherState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("ui", ui_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")
workflow.add_edge("ui", END)

graph = workflow.compile()
```

### Frontend (React)

```tsx
// ui/WeatherDashboard.tsx
import React from 'react';
import './WeatherDashboard.css';

interface Forecast {
  day: string;
  high: number;
  low: number;
  conditions: string;
}

interface WeatherDashboardProps {
  city: string;
  temperature: number;
  conditions: string;
  humidity: number;
  wind_speed: number;
  forecast: Forecast[];
}

export default function WeatherDashboard({
  city,
  temperature,
  conditions,
  humidity,
  wind_speed,
  forecast
}: WeatherDashboardProps) {
  return (
    <div className="weather-dashboard">
      {/* Current Weather */}
      <div className="current-weather">
        <div className="weather-icon">
          {conditions === 'Sunny' ? '☀️' :
           conditions === 'Cloudy' ? '☁️' :
           conditions === 'Rainy' ? '🌧️' : '🌤️'}
        </div>
        <div className="weather-details">
          <h2>{city}</h2>
          <div className="temperature">{temperature}°F</div>
          <div className="conditions">{conditions}</div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="weather-stats">
        <div className="stat">
          <span className="label">Humidity</span>
          <span className="value">{humidity}%</span>
        </div>
        <div className="stat">
          <span className="label">Wind</span>
          <span className="value">{wind_speed} mph</span>
        </div>
      </div>

      {/* Forecast */}
      <div className="forecast">
        <h3>5-Day Forecast</h3>
        <div className="forecast-grid">
          {forecast.map((day, idx) => (
            <div key={idx} className="forecast-day">
              <div className="day-name">{day.day}</div>
              <div className="day-icon">
                {day.conditions === 'Sunny' ? '☀️' :
                 day.conditions === 'Cloudy' ? '☁️' : '🌧️'}
              </div>
              <div className="day-temps">
                <span className="high">{day.high}°</span>
                <span className="low">{day.low}°</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

```css
/* ui/WeatherDashboard.css */
.weather-dashboard {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 2rem;
  color: white;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  max-width: 500px;
}

.current-weather {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.weather-icon {
  font-size: 5rem;
}

.temperature {
  font-size: 3rem;
  font-weight: bold;
}

.weather-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat {
  background: rgba(255, 255, 255, 0.2);
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
}

.forecast-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.forecast-day {
  background: rgba(255, 255, 255, 0.15);
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
}

.day-temps {
  display: flex;
  justify-content: space-around;
  margin-top: 0.5rem;
}

.high { font-weight: bold; }
.low { opacity: 0.7; }
```

```tsx
// ui/components.tsx
import WeatherDashboard from './WeatherDashboard';

export default {
  weather_dashboard: WeatherDashboard,
};
```

---

## Example 2: Image Gallery with Japanese OCR

### Backend (Python)

```python
# src/japanese_agent/graph.py
import uuid
import base64
from pathlib import Path
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer, push_ui_message


class JapaneseAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    screenshot_paths: list[str]


def encode_image(path: str) -> tuple[str, str]:
    """Encode image to base64."""
    with open(path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    return data, "image/png"


def analyze_screenshots_node(state: JapaneseAgentState):
    """Analyze screenshots and emit gallery component."""

    screenshot_paths = state.get("screenshot_paths", [])
    if not screenshot_paths:
        return {}

    # Process each screenshot
    gallery_items = []
    for path in screenshot_paths:
        # Mock OCR results - replace with real OCR
        ocr_result = {
            "text": "こんにちは",
            "reading": "konnichiwa",
            "translation": "Hello"
        }

        # Encode image
        image_b64, media_type = encode_image(path)

        gallery_items.append({
            "id": str(uuid.uuid4()),
            "image_data": image_b64,
            "media_type": media_type,
            "extracted_text": ocr_result["text"],
            "reading": ocr_result["reading"],
            "translation": ocr_result["translation"]
        })

    message = AIMessage(
        id=str(uuid.uuid4()),
        content=f"Analyzed {len(gallery_items)} screenshots"
    )

    # Push gallery component
    push_ui_message(
        "japanese_gallery",
        {"items": gallery_items},
        message=message
    )

    return {"messages": [message]}


# Build graph
workflow = StateGraph(JapaneseAgentState)
workflow.add_node("analyze", analyze_screenshots_node)
workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", END)

graph = workflow.compile()
```

### Frontend (React)

```tsx
// ui/JapaneseGallery.tsx
import React, { useState } from 'react';
import { useStreamContext } from '@langchain/langgraph-sdk/react-ui';
import './JapaneseGallery.css';

interface GalleryItem {
  id: string;
  image_data: string;
  media_type: string;
  extracted_text: string;
  reading: string;
  translation: string;
}

interface JapaneseGalleryProps {
  items: GalleryItem[];
}

export default function JapaneseGallery({ items }: JapaneseGalleryProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { submit } = useStreamContext();

  const handleWordClick = (word: string) => {
    submit({
      messages: [{
        type: "human",
        content: `Tell me more about: ${word}`
      }]
    });
  };

  return (
    <div className="japanese-gallery">
      <h3>Screenshots ({items.length})</h3>

      <div className="gallery-grid">
        {items.map((item) => (
          <div
            key={item.id}
            className={`gallery-item ${selectedId === item.id ? 'selected' : ''}`}
            onClick={() => setSelectedId(item.id === selectedId ? null : item.id)}
          >
            <img
              src={`data:${item.media_type};base64,${item.image_data}`}
              alt={item.translation}
              loading="lazy"
            />

            <div className="overlay">
              <div className="japanese-text">{item.extracted_text}</div>
              <div className="reading">{item.reading}</div>
              <div className="translation">{item.translation}</div>

              <button
                className="detail-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleWordClick(item.extracted_text);
                }}
              >
                Learn More
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

```css
/* ui/JapaneseGallery.css */
.japanese-gallery {
  padding: 1rem;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.gallery-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}

.gallery-item:hover {
  transform: scale(1.02);
}

.gallery-item.selected {
  box-shadow: 0 0 0 3px #667eea;
}

.gallery-item img {
  width: 100%;
  height: auto;
  display: block;
}

.overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
  padding: 1rem;
  color: white;
}

.japanese-text {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.reading {
  font-size: 0.875rem;
  opacity: 0.9;
  margin-bottom: 0.25rem;
}

.translation {
  font-size: 0.875rem;
  opacity: 0.8;
}

.detail-btn {
  margin-top: 0.5rem;
  padding: 0.25rem 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
}

.detail-btn:hover {
  background: #5568d3;
}
```

---

## Example 3: Interactive Flashcard System

### Backend (Python)

```python
# src/flashcard_agent/graph.py
import uuid
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer, push_ui_message
import json


class FlashcardState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    vocabulary: list[dict]


def generate_flashcards_node(state: FlashcardState):
    """Generate flashcards from vocabulary."""

    vocabulary = state.get("vocabulary", [])
    if not vocabulary:
        # Default vocabulary
        vocabulary = [
            {"word": "こんにちは", "reading": "konnichiwa", "meaning": "Hello"},
            {"word": "ありがとう", "reading": "arigatou", "meaning": "Thank you"},
            {"word": "さようなら", "reading": "sayounara", "meaning": "Goodbye"},
        ]

    message = AIMessage(
        id=str(uuid.uuid4()),
        content=f"Here are {len(vocabulary)} flashcards for review"
    )

    # Push flashcard component
    push_ui_message(
        "flashcard_deck",
        {"cards": vocabulary},
        message=message
    )

    return {"messages": [message]}


def process_rating_node(state: FlashcardState):
    """Process flashcard rating feedback."""

    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage):
        return {}

    try:
        feedback = json.loads(last_message.content)
        if feedback.get("action") != "rate_card":
            return {}

        card_id = feedback["cardId"]
        difficulty = feedback["difficulty"]

        # Store rating (in real app, save to database)
        response = AIMessage(
            id=str(uuid.uuid4()),
            content=f"Recorded rating: {difficulty}"
        )

        return {"messages": [response]}
    except:
        return {}


# Build graph
workflow = StateGraph(FlashcardState)
workflow.add_node("generate", generate_flashcards_node)
workflow.add_node("process_rating", process_rating_node)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", END)

graph = workflow.compile()
```

### Frontend (React)

```tsx
// ui/FlashcardDeck.tsx
import React, { useState } from 'react';
import { useStreamContext } from '@langchain/langgraph-sdk/react-ui';
import './FlashcardDeck.css';

interface Card {
  word: string;
  reading: string;
  meaning: string;
}

interface FlashcardDeckProps {
  cards: Card[];
}

export default function FlashcardDeck({ cards }: FlashcardDeckProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [reviewedCards, setReviewedCards] = useState<Set<number>>(new Set());
  const { submit } = useStreamContext();

  const currentCard = cards[currentIndex];
  const progress = ((reviewedCards.size / cards.length) * 100).toFixed(0);

  const handleFlip = () => setIsFlipped(!isFlipped);

  const handleRating = (difficulty: 'easy' | 'medium' | 'hard') => {
    // Send rating to agent
    submit({
      messages: [{
        type: "human",
        content: JSON.stringify({
          action: "rate_card",
          cardId: currentIndex,
          difficulty
        })
      }]
    });

    // Mark as reviewed
    setReviewedCards(new Set([...reviewedCards, currentIndex]));

    // Move to next card
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  const handleNavigation = (direction: 'prev' | 'next') => {
    if (direction === 'prev' && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
    } else if (direction === 'next' && currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  return (
    <div className="flashcard-deck">
      {/* Progress Bar */}
      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${progress}%` }} />
        <span className="progress-text">
          {reviewedCards.size} / {cards.length} reviewed ({progress}%)
        </span>
      </div>

      {/* Card Counter */}
      <div className="card-counter">
        Card {currentIndex + 1} of {cards.length}
      </div>

      {/* Flashcard */}
      <div className="card-wrapper" onClick={handleFlip}>
        <div className={`flashcard ${isFlipped ? 'flipped' : ''}`}>
          <div className="card-face card-front">
            <div className="card-content">
              <div className="word">{currentCard.word}</div>
              <div className="reading">{currentCard.reading}</div>
            </div>
            <div className="flip-hint">Click to flip</div>
          </div>

          <div className="card-face card-back">
            <div className="card-content">
              <div className="meaning">{currentCard.meaning}</div>
            </div>
            <div className="flip-hint">Click to flip back</div>
          </div>
        </div>
      </div>

      {/* Rating Buttons (shown after flip) */}
      {isFlipped && (
        <div className="rating-buttons">
          <button
            className="rating-btn easy"
            onClick={(e) => {
              e.stopPropagation();
              handleRating('easy');
            }}
          >
            Easy
          </button>
          <button
            className="rating-btn medium"
            onClick={(e) => {
              e.stopPropagation();
              handleRating('medium');
            }}
          >
            Medium
          </button>
          <button
            className="rating-btn hard"
            onClick={(e) => {
              e.stopPropagation();
              handleRating('hard');
            }}
          >
            Hard
          </button>
        </div>
      )}

      {/* Navigation */}
      <div className="navigation-buttons">
        <button
          onClick={() => handleNavigation('prev')}
          disabled={currentIndex === 0}
        >
          ← Previous
        </button>
        <button
          onClick={() => handleNavigation('next')}
          disabled={currentIndex === cards.length - 1}
        >
          Next →
        </button>
      </div>
    </div>
  );
}
```

```css
/* ui/FlashcardDeck.css */
.flashcard-deck {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
}

.progress-container {
  position: relative;
  height: 30px;
  background: #e0e0e0;
  border-radius: 15px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.875rem;
  font-weight: bold;
  color: #333;
}

.card-counter {
  text-align: center;
  font-size: 1rem;
  color: #666;
  margin-bottom: 1rem;
}

.card-wrapper {
  perspective: 1000px;
  height: 350px;
  margin-bottom: 2rem;
  cursor: pointer;
}

.flashcard {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.6s;
  transform-style: preserve-3d;
}

.flashcard.flipped {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.card-front {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.card-back {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  transform: rotateY(180deg);
}

.word {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.reading {
  font-size: 1.5rem;
  opacity: 0.9;
}

.meaning {
  font-size: 2rem;
  text-align: center;
}

.flip-hint {
  position: absolute;
  bottom: 1rem;
  font-size: 0.875rem;
  opacity: 0.7;
}

.rating-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.rating-btn {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.rating-btn:hover {
  transform: translateY(-2px);
}

.rating-btn.easy { background: #4ade80; color: white; }
.rating-btn.medium { background: #fbbf24; color: white; }
.rating-btn.hard { background: #f87171; color: white; }

.navigation-buttons {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.navigation-buttons button {
  flex: 1;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
}

.navigation-buttons button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
```

---

## Running the Examples

### Setup

```bash
# Clone examples
git clone https://github.com/langchain-ai/langgraphjs-gen-ui-examples.git
cd langgraphjs-gen-ui-examples

# Install dependencies
pnpm install

# Set environment variables
cp .env.example .env
# Add your API keys to .env

# Start LangGraph server
pnpm agent
```

### Test Locally

```bash
# Terminal 1: Start LangGraph server
langgraph dev

# Terminal 2: Start Next.js frontend
cd frontend
npm run dev
```

### Deploy

```bash
# Deploy LangGraph agent
langgraph deploy

# Deploy frontend (Vercel)
cd frontend
vercel
```

## Next Steps

- **[07-troubleshooting.md](07-troubleshooting.md)**: Common issues and solutions
- **[README.md](README.md)**: Overview and quick start
