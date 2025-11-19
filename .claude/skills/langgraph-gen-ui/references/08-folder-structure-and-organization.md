# Component Folder Structure & Organization Patterns

## Overview

This guide covers **production-tested** folder structure patterns for organizing LangGraph Gen-UI components in a clean, maintainable, and scalable way. These patterns are based on real implementations in the Cernji-Agents monorepo (japanese-tutor backend + agent-chat-ui frontend).

## Key Principles

### 1. Separation of Concerns
- **UI Primitives** (`components/ui/`) - Design system components (shadcn/ui)
- **Custom Components** (`components/custom/`) - Agent-specific Gen-UI components
- **Feature Modules** (`components/thread/`, `components/features/`) - Application features
- **Backend** - No React components; only emits UI specifications via `push_ui_message()`

### 2. Component Registry Pattern
- **Centralized registration** in `components/custom/index.ts`
- **Type-safe** component lookup with TypeScript
- **Local-first** rendering with fallback to external loading

### 3. Co-location
- Related files live together (components, hooks, types, utils)
- Feature-based organization over type-based
- Index files for clean imports

## Recommended Folder Structure

### Complete Structure for Next.js + LangGraph

```
apps/your-langgraph-ui/
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── api/
│   │   │   └── [..._path]/route.ts # API passthrough for production
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   │
│   ├── components/
│   │   ├── custom/                 # ⭐ Gen-UI Components (REGISTER HERE)
│   │   │   ├── index.ts           # Component registry
│   │   │   ├── YourCard.tsx       # Custom UI components
│   │   │   ├── Gallery.tsx
│   │   │   └── Dashboard.tsx
│   │   │
│   │   ├── features/              # Feature modules (optional)
│   │   │   └── feature-name/
│   │   │       ├── components/    # Feature components
│   │   │       ├── hooks/         # Feature hooks
│   │   │       ├── index.tsx      # Main export
│   │   │       ├── types.ts       # Feature types
│   │   │       └── utils.ts       # Feature utils
│   │   │
│   │   ├── thread/                # Chat/thread UI
│   │   │   ├── messages/
│   │   │   │   ├── ai.tsx        # AI message with CustomComponent loader
│   │   │   │   ├── human.tsx
│   │   │   │   └── shared.tsx
│   │   │   ├── history/
│   │   │   └── index.tsx
│   │   │
│   │   ├── ui/                    # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   │
│   │   └── icons/                 # SVG icons
│   │
│   ├── providers/                 # React Context providers
│   │   ├── Stream.tsx            # LangGraph streaming
│   │   └── Thread.tsx            # Thread management
│   │
│   ├── hooks/                     # Global hooks
│   │   ├── use-file-upload.tsx
│   │   └── useMediaQuery.tsx
│   │
│   └── lib/                       # Global utilities
│       ├── utils.ts              # cn() helper
│       └── multimodal-utils.ts
│
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

### Backend Structure (Python)

```
apps/your-langgraph-backend/
├── src/
│   └── your_agent/
│       ├── nodes/                # LangGraph nodes
│       │   ├── ui_emission.py   # Node that emits UI
│       │   └── __init__.py
│       ├── state/
│       │   └── schemas.py       # State with ui field
│       ├── tools/
│       └── graph.py             # Main graph
│
├── langgraph.json               # LangGraph server config
└── pyproject.toml
```

## Component Registry Pattern

### 1. Registry File (`components/custom/index.ts`)

```typescript
// Component imports
import HelloCard from './HelloCard';
import ScreenshotCard from './ScreenshotCard';
import WeatherDashboard from './WeatherDashboard';
import FlashcardDeck from './FlashcardDeck';

// Registry map
export const customComponents = {
  hello_card: HelloCard,
  screenshot_card: ScreenshotCard,
  weather_dashboard: WeatherDashboard,
  flashcard_deck: FlashcardDeck,
};

// Type-safe component name
export type CustomComponentName = keyof typeof customComponents;
```

**Benefits:**
- ✅ Single source of truth for all Gen-UI components
- ✅ Type-safe component lookup
- ✅ Easy to add new components (1 import + 1 line)
- ✅ Automatic TypeScript autocomplete

### 2. Loading Pattern (`components/thread/messages/ai.tsx`)

```typescript
import { customComponents } from '@/components/custom';
import { LoadExternalComponent } from '@langchain/langgraph-sdk/react-ui';

function CustomComponent({ message, thread }) {
  const { values } = useStreamContext();

  // Filter UI messages linked to this message
  const uiMessages = values.ui?.filter(
    (ui) => ui.metadata?.message_id === message.id
  );

  return (
    <>
      {uiMessages?.map((uiMessage) => {
        // Check local registry first
        const LocalComponent = customComponents[uiMessage.name];

        if (LocalComponent) {
          // Render pre-loaded component
          return (
            <LocalComponent
              key={uiMessage.id}
              {...uiMessage.props}
            />
          );
        }

        // Fallback to external component loading
        return (
          <LoadExternalComponent
            key={uiMessage.id}
            stream={thread}
            message={uiMessage}
            fallback={<div>Loading...</div>}
          />
        );
      })}
    </>
  );
}
```

**Benefits:**
- ✅ **Local-first**: Faster rendering with pre-loaded components
- ✅ **Fallback support**: Can still load external components dynamically
- ✅ **Type-safe**: TypeScript knows all component names
- ✅ **Performance**: No dynamic imports for registered components

## Feature Module Pattern

### When to Use Feature Modules

Use feature modules when:
- A feature has **multiple components** (3+)
- A feature has **custom hooks**
- A feature has **feature-specific types/utilities**
- You want to **hide implementation details**

### Feature Module Structure

```
components/features/data-visualization/
├── components/               # Internal components (not exported)
│   ├── Chart.tsx
│   ├── Legend.tsx
│   └── Tooltip.tsx
├── hooks/                   # Feature-specific hooks
│   ├── useChartData.tsx
│   └── useChartResize.tsx
├── index.tsx                # Main export (public API)
├── types.ts                 # Feature types
└── utils.ts                 # Feature utilities
```

### Example: index.tsx (Public API)

```typescript
// Only export what consumers need
export { default as DataVisualization } from './DataVisualization';
export type { DataVisualizationProps } from './types';
```

**Benefits:**
- ✅ **Encapsulation**: Internal components hidden
- ✅ **Discoverability**: Everything in one place
- ✅ **Maintainability**: Changes localized
- ✅ **Scalability**: Easy to add features

## Naming Conventions

### Files

| Pattern | Example | Usage |
|---------|---------|-------|
| **PascalCase.tsx** | `ScreenshotCard.tsx` | React components |
| **camelCase.ts** | `utils.ts`, `types.ts` | Utilities, types |
| **kebab-case.tsx** | `markdown-text.tsx` | shadcn/ui primitives |
| **use-*.tsx** | `use-file-upload.tsx` | Custom hooks |

### Directories

| Pattern | Example | Usage |
|---------|---------|-------|
| **kebab-case/** | `agent-inbox/` | Multi-word features |
| **lowercase/** | `hooks/`, `lib/` | Utility directories |

### Components

```typescript
// ✅ Good: PascalCase for component files
ScreenshotCard.tsx
WeatherDashboard.tsx
FlashcardDeck.tsx

// ❌ Bad: Other cases
screenshot-card.tsx
weather_dashboard.tsx
```

### Registry Names

```typescript
// ✅ Good: snake_case for registry keys (matches backend)
export const customComponents = {
  screenshot_card: ScreenshotCard,
  weather_dashboard: WeatherDashboard,
  flashcard_deck: FlashcardDeck,
};

// ❌ Bad: Other cases
export const customComponents = {
  ScreenshotCard: ScreenshotCard,  // Don't use PascalCase
  'weather-dashboard': WeatherDashboard,  // Don't use kebab-case
};
```

## Scalability Patterns

### Small Projects (< 10 Gen-UI components)

**Structure:**
```
components/
├── custom/           # All Gen-UI components here
│   ├── index.ts     # Registry
│   ├── Card1.tsx
│   ├── Card2.tsx
│   └── ...
├── ui/              # shadcn/ui
└── thread/          # Chat UI
```

**When to use:** Prototypes, simple agents, learning projects

### Medium Projects (10-30 Gen-UI components)

**Structure:**
```
components/
├── custom/           # Gen-UI component registry
│   ├── cards/       # Categorize by type
│   │   ├── InfoCard.tsx
│   │   └── StatusCard.tsx
│   ├── forms/
│   │   ├── FeedbackForm.tsx
│   │   └── SettingsForm.tsx
│   ├── charts/
│   │   ├── LineChart.tsx
│   │   └── BarChart.tsx
│   └── index.ts     # Main registry
├── features/        # Complex features
├── ui/
└── thread/
```

**When to use:** Production agents, multiple component types

### Large Projects (30+ Gen-UI components)

**Structure:**
```
components/
├── custom/           # Gen-UI components
│   ├── domain-a/    # Categorize by domain/feature area
│   │   ├── cards/
│   │   ├── forms/
│   │   └── index.ts # Domain registry
│   ├── domain-b/
│   │   ├── charts/
│   │   └── index.ts
│   └── index.ts     # Main registry (re-exports all)
├── features/        # Application features
│   ├── feature-a/
│   ├── feature-b/
│   └── shared/      # Shared feature components
├── ui/
└── thread/
```

**Example main registry:**
```typescript
// components/custom/index.ts
import * as domainA from './domain-a';
import * as domainB from './domain-b';

export const customComponents = {
  ...domainA.customComponents,
  ...domainB.customComponents,
};
```

**When to use:** Enterprise agents, multi-domain applications

## Real Working Examples

### Production Implementation: japanese-tutor + agent-chat-ui

**Location in codebase:**
- Backend: `apps/japanese-tutor/src/japanese_agent/`
- Frontend: `apps/agent-chat-ui/src/`

#### Backend Structure

```
apps/japanese-tutor/src/japanese_agent/
├── nodes/
│   ├── screenshot_ui.py        # Emits "screenshot_card" UI
│   └── save_screenshot_db.py   # Database persistence
├── state/
│   └── schemas.py              # State with ui field
├── tools/
│   └── screenshot_analyzer.py  # OCR tools
├── database/
│   ├── connection.py
│   └── schema.sql
└── graph.py                    # Main graph with UI nodes
```

**Key Pattern:** Backend never has React components, only emits specifications.

#### Frontend Structure

```
apps/agent-chat-ui/src/
├── components/
│   ├── custom/
│   │   ├── index.ts            # ⭐ Registry with 2 components
│   │   ├── HelloCard.tsx       # Test component
│   │   └── ScreenshotCard.tsx  # Production component (OCR display)
│   ├── thread/
│   │   ├── messages/
│   │   │   └── ai.tsx          # CustomComponent loader
│   │   ├── artifact.tsx        # Side panel for rich UI
│   │   └── index.tsx           # Main chat interface
│   └── ui/                     # 15+ shadcn/ui components
├── providers/
│   └── Stream.tsx              # LangGraph SDK integration
└── hooks/
    └── use-file-upload.tsx     # Multimodal file upload
```

**Key Pattern:** Registry-based component loading with local-first approach.

### Component Flow

```
1. User uploads screenshot → agent-chat-ui
2. HumanMessage with base64 image → LangGraph server
3. preprocess_images node → Extracts image, stores in state
4. chatbot node → Decides to use OCR tool
5. tools node → Executes hybrid_screenshot_analysis
6. save_screenshot_to_db node → Persists to SQLite
7. emit_screenshot_ui node → push_ui_message("screenshot_card", {...})
8. SSE stream → onCustomEvent in agent-chat-ui
9. uiMessageReducer → Updates stream.values.ui
10. CustomComponent → Checks registry, renders ScreenshotCard.tsx
```

## Best Practices Summary

### ✅ DO

1. **Use component registry pattern** for type-safety and performance
2. **Separate UI primitives from custom components** (`ui/` vs `custom/`)
3. **Co-locate related files** (components, hooks, types, utils together)
4. **Use feature modules** for complex features with multiple files
5. **Follow naming conventions** (PascalCase components, snake_case registry keys)
6. **Keep backend free of React code** - only emit UI specifications
7. **Use index files** for clean imports and public APIs
8. **Organize by domain** for large projects (30+ components)

### ❌ DON'T

1. **Mix UI primitives with custom components** in the same directory
2. **Use type-based organization** (all components/, all hooks/, all utils/)
3. **Put React components in Python backend** - violates separation of concerns
4. **Forget to register components** in `custom/index.ts`
5. **Use inconsistent naming** (mix PascalCase and kebab-case for components)
6. **Skip TypeScript types** for component props
7. **Create deep nesting** (max 3-4 levels deep)
8. **Duplicate utilities** - extract to shared lib/

## Migration Guide

### From Flat Structure to Feature Modules

**Before:**
```
components/
├── ComponentA.tsx
├── ComponentB.tsx
├── ComponentAHelper.tsx
├── ComponentBHelper.tsx
├── useComponentA.tsx
└── useComponentB.tsx
```

**After:**
```
components/
└── features/
    ├── feature-a/
    │   ├── ComponentA.tsx
    │   ├── ComponentAHelper.tsx
    │   ├── useComponentA.tsx
    │   └── index.tsx
    └── feature-b/
        ├── ComponentB.tsx
        ├── ComponentBHelper.tsx
        ├── useComponentB.tsx
        └── index.tsx
```

### From External to Registry-Based Loading

**Before:**
```typescript
// Always load externally
<LoadExternalComponent stream={thread} message={ui} />
```

**After:**
```typescript
// Check registry first
const LocalComponent = customComponents[uiMessage.name];
if (LocalComponent) {
  return <LocalComponent {...uiMessage.props} />;
}
return <LoadExternalComponent stream={thread} message={ui} />;
```

## Troubleshooting

### Component Not Rendering

**Check:**
1. Is component registered in `components/custom/index.ts`?
2. Does registry key match backend `push_ui_message("key", ...)`?
3. Is `onCustomEvent` handler configured in `useStream`?

### Import Errors

**Check:**
1. Is component exported in `index.ts`?
2. Are you using correct import path (`@/components/custom`)?
3. Does TypeScript `paths` configuration include `@/*`?

### Name Conflicts

**Solution:** Use domain prefixes in registry:
```typescript
export const customComponents = {
  'auth:login_form': AuthLoginForm,
  'analytics:chart': AnalyticsChart,
  // Prevents conflicts between domains
};
```

## Summary

**Key Takeaways:**
1. **Component Registry** = Type-safe, performant Gen-UI component loading
2. **Separation of Concerns** = UI primitives, custom components, features in separate directories
3. **Feature Modules** = Co-locate related code for better maintainability
4. **Scalability** = Organize by domain for large projects
5. **Real Examples** = japanese-tutor + agent-chat-ui demonstrate production patterns

For complete working implementations, refer to:
- `apps/japanese-tutor/` - Backend with UI emission
- `apps/agent-chat-ui/` - Frontend with component registry
