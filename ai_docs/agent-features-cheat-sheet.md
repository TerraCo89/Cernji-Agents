This cheat sheet explains the distinguishing characteristics and recommended use cases for Skills, Custom Slash Commands, Sub-Agents, and MCP Servers, based on the provided source material.

***

# Agent Feature Cheat Sheet: Skills, Commands, Sub-Agents, and MCP

## 1. Custom Slash Commands (The Primitive)

Custom Slash Commands (often referred to as Prompts) are considered the **primitive** of agentic coding and the fundamental unit of knowledge work. Engineers are strongly advised to prioritize mastery of the prompt.

| When to Use | Distinguishing Characteristics | Example Use Cases |
| :--- | :--- | :--- |
| **Manual Trigger/One-Off Task** | These are reusable prompt shortcuts that you invoke manually. They are explicitly kicked off by the user. | Generalize simple **git commit messages** (simple one-step task). |
| **Simple, Single Task** | Best for jobs that are one-off and do not require scale or complex, automated management. | **Creating a component** (simple one-off task). |
| **Starting Point** | Always recommended as the starting point; keep it simple and build a prompt first. | **Creating a single git work tree** (when you need to see what happened and don't need parallelization). |
| **Composability** | Acts as both a primitive and a composition unit, as they can run skills, MCP servers, and sub-agents. | N/A |

## 2. Agent Skills

Skills are designed for **automatic behavior** and managing a specific problem set with a dedicated, opinionated structure. They represent a higher compositional level.

| When to Use | Distinguishing Characteristics | Example Use Cases |
| :--- | :--- | :--- |
| **Automatic Behavior** | Skills are **triggered by your agents** if given direction, meaning the agent autonomously applies the expertise. | **Automatically extract text and data from PDFs** (if you always want this behavior). |
| **Reoccurring Workflows** | Use to package custom expertise for reoccurring workflows. They scale a solution into a reusable solution. | **Detecting style guide violations** (to encode repeat behavior). |
| **Modularity & Structure** | Offer a dedicated directory structure for building out repeat solutions. Allows for logical composition and grouping of skill elements. | **Managing git work trees** (when one prompt is not enough and you need to manage multiple elements). |
| **Context Efficient** | Skills are context efficient, employing "progressive disclosure" (metadata level, instructions, then resources). | N/A |
| **High Composability** | Skills sit at the top of the composition hierarchy. They can use prompts, other skills, MCP servers, and sub-agents. | Use a skill to **compose many slash commands, sub-agents, or MCPs**. |

## 3. Sub-Agents

Sub-Agents are the solution for running **isolated, specialized tasks** that require parallel execution.

| When to Use | Distinguishing Characteristics | Example Use Cases |
| :--- | :--- | :--- |
| **Parallelization** | This is the defining feature; Sub-Agents are the **only** feature that supports parallel calling. | Whenever you see the keyword "**parallel**," jump to Sub-Agents. |
| **Isolated Context** | Used to delegate work out of your primary agent's context window. They isolate and protect the main context window. | **Fixing and debugging failing tests at scale**. |
| **Transient Context** | The context persistence is lost once the task is complete, which makes them great for isolation, but the user must be okay with losing that context afterward. | **Running a comprehensive security audit** (if it needs to scale and you don't need the context afterward). |

## 4. MCP Servers (Managed Control Plane)

MCP Servers are clearly distinct from skills and other capabilities, focusing entirely on **external integrations**.

| When to Use | Distinguishing Characteristics | Example Use Cases |
| :--- | :--- | :--- |
| **External Integrations** | Built specifically for connecting agents to **external tools and data sources**. | **Connecting to Jira** (an external source). |
| **Third-Party Services** | Ideal for integrating third-party APIs. | **Fetching real-time weather data from APIs**. |
| **Database Queries** | Used for accessing or manipulating data stores. | **Querying your database**. |
| **Context Inefficiency** | Unlike skills, MCP servers are context inefficient and "explode your context window on bootup". | N/A |
| **Bundling Services** | Use to bundle multiple services together and then expose them to your agent. | N/A |

## Quick Decision Tree

```
Need external integration (API, database, third-party service)?
└─> Use MCP Server

Need parallel execution or isolated context?
└─> Use Sub-Agent

Need automatic, reoccurring behavior with structure?
└─> Use Skill

Simple, one-off task that you trigger manually?
└─> Use Custom Slash Command
```

## Key Takeaways

1. **Start Simple**: Always begin with a Custom Slash Command (prompt) before building more complex solutions
2. **Parallelize with Sub-Agents**: If you need to run tasks in parallel, Sub-Agents are your only option
3. **Automate with Skills**: Package reoccurring workflows into Skills for automatic behavior
4. **Integrate with MCP**: Connect to external services and data sources using MCP Servers
5. **Composition Hierarchy**: Skills > Sub-Agents > MCP Servers > Custom Slash Commands (in terms of complexity and composition capability)
