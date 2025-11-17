"use client";

import { useQueryState } from "nuqs";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export type AgentType =
  | "career_assistant"
  | "resume_agent_advanced";

export interface Agent {
  id: AgentType;
  name: string;
  description: string;
  icon: string;
}

const AGENTS: Agent[] = [
  {
    id: "career_assistant",
    name: "Career Assistant",
    description: "Chat about careers, analyze jobs, review resumes",
    icon: "💬",
  },
  {
    id: "resume_agent_advanced",
    name: "Resume Agent",
    description: "Advanced resume tailoring with full workflow",
    icon: "📝",
  },
];

export function AgentSelector() {
  const [assistantId, setAssistantId] = useQueryState("assistantId");

  // Get current agent or default to first one
  const currentAgent = AGENTS.find((a) => a.id === assistantId) || AGENTS[0];

  return (
    <div className="flex flex-col gap-3">
      <Label className="text-sm font-medium">Select Agent</Label>
      <div className="grid grid-cols-2 gap-2">
        {AGENTS.map((agent) => (
          <Button
            key={agent.id}
            variant={currentAgent.id === agent.id ? "default" : "outline"}
            className={cn(
              "flex flex-col items-start h-auto py-3 px-4 text-left",
              currentAgent.id === agent.id && "ring-2 ring-primary"
            )}
            onClick={() => setAssistantId(agent.id)}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{agent.icon}</span>
              <span className="font-semibold text-sm">{agent.name}</span>
            </div>
            <span className="text-xs opacity-80 font-normal">
              {agent.description}
            </span>
          </Button>
        ))}
      </div>
    </div>
  );
}
