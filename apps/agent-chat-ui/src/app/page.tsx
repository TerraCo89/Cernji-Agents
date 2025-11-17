"use client";

import { Thread } from "@/components/thread";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { Toaster } from "@/components/ui/sonner";
import { AgentSelector } from "@/components/agent-selector";
import React from "react";

export default function DemoPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading (layout)...</div>}>
      <Toaster />
      <ThreadProvider>
        <StreamProvider>
          <ArtifactProvider>
            <div className="flex flex-col h-screen">
              {/* Agent Selector Header */}
              <div className="border-b p-4 bg-background">
                <div className="max-w-4xl mx-auto">
                  <h1 className="text-2xl font-bold mb-4">Career Application Assistant</h1>
                  <AgentSelector />
                </div>
              </div>

              {/* Thread Component */}
              <div className="flex-1 overflow-hidden">
                <Thread />
              </div>
            </div>
          </ArtifactProvider>
        </StreamProvider>
      </ThreadProvider>
    </React.Suspense>
  );
}
