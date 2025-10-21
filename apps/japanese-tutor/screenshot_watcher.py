#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "claude-code-sdk",
#     "watchdog",
#     "pyyaml",
#     "python-dotenv",
#     "rich",
# ]
# ///

"""
Japanese Tutor Screenshot Watcher
An agentic drop zone that monitors RetroArch screenshots and provides Japanese translations.
Based on the agentic drop zones pattern by disler.
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import yaml

# Initialize Rich console for better output
console = Console()


class ScreenshotHandler(FileSystemEventHandler):
    """Handles new screenshot files and triggers Japanese translation."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.file_patterns = config.get('file_patterns', ['*.png', '*.jpg', '*.jpeg'])
        self.processed_files = set()
        self.slash_command_path = Path(".claude/commands/japanese/analyze.md")
        
    def matches_pattern(self, filename: str) -> bool:
        """Check if filename matches any of the configured patterns."""
        for pattern in self.file_patterns:
            if pattern.startswith('*.'):
                extension = pattern[1:]  # Remove the *
                if filename.lower().endswith(extension):
                    return True
        return False

    def load_slash_command(self, file_path: str) -> str:
        """Load slash command content and replace $ARGUMENTS placeholder."""
        if not self.slash_command_path.exists():
            raise FileNotFoundError(f"Slash command not found: {self.slash_command_path}")

        # Load the slash command content
        prompt_content = self.slash_command_path.read_text(encoding='utf-8')

        # Replace $ARGUMENTS placeholder with the file path
        if "$ARGUMENTS" in prompt_content:
            prompt_content = prompt_content.replace("$ARGUMENTS", file_path)

        return prompt_content

    async def process_screenshot_async(self, file_path: str):
        """Process a screenshot using Claude Code SDK (async)."""
        try:
            console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            console.print(f"[green]📸 New screenshot detected:[/green] {Path(file_path).name}")
            console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

            # Load the slash command content
            console.print(f"[dim]   Loading slash command: {self.slash_command_path}[/dim]")
            full_prompt = self.load_slash_command(file_path)

            # Create SDK client options
            options = ClaudeCodeOptions(
                permission_mode="bypassPermissions",  # Auto-approve tool calls
                model=self.config.get('model', 'sonnet')
            )

            console.print(f"[cyan]ℹ️  Processing with Claude Code SDK...[/cyan]")
            console.print(f"[dim]   Model: {self.config.get('model', 'sonnet')}[/dim]\n")

            # Process with Claude Code SDK
            async with ClaudeSDKClient(options=options) as client:
                await client.query(full_prompt)

                # Stream response
                has_response = False
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        for block in message.content:
                            if hasattr(block, "text") and block.text.strip():
                                has_response = True
                                # Output in styled panel
                                console.print(
                                    Panel(
                                        Text(block.text),
                                        title="[bold cyan]🤖 Claude Code • Japanese Tutor[/bold cyan]",
                                        subtitle=f"[dim]{Path(file_path).name}[/dim]",
                                        border_style="cyan",
                                        expand=False,
                                        padding=(1, 2),
                                    )
                                )

                # If no response received
                if not has_response:
                    console.print(
                        Panel(
                            Text("[yellow]No response received[/yellow]"),
                            title="[bold yellow]🤖 Claude Code • Japanese Tutor[/bold yellow]",
                            subtitle=f"[dim]{Path(file_path).name}[/dim]",
                            border_style="yellow",
                            expand=False,
                            padding=(1, 2),
                        )
                    )

            console.print()

        except Exception as e:
            console.print(f"[bold red]❌ Error processing screenshot: {e}[/bold red]")
            import traceback
            traceback.print_exc()

    def process_screenshot(self, file_path: str):
        """Process a screenshot (sync wrapper for async method)."""
        # Bridge from sync watchdog handler to async SDK call
        asyncio.run(self.process_screenshot_async(file_path))
    
    def on_created(self, event: FileCreatedEvent):
        """Called when a file is created in the monitored directory."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        filename = Path(file_path).name
        
        # Check if file matches our patterns
        if not self.matches_pattern(filename):
            return
        
        # Avoid processing the same file twice
        if file_path in self.processed_files:
            return
        
        self.processed_files.add(file_path)
        
        # Give the file a moment to finish writing
        time.sleep(0.5)
        
        # Process the screenshot
        self.process_screenshot(file_path)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point for the screenshot watcher."""
    # Load environment variables from .env file
    load_dotenv()

    console.print("[bold cyan]🎮 Japanese Tutor Screenshot Watcher[/bold cyan]")
    console.print("Monitoring RetroArch screenshots for Japanese translation...\n")

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[bold red]❌ Error: ANTHROPIC_API_KEY environment variable not set![/bold red]")
        console.print("[yellow]Please set it in .env file or environment:[/yellow]")
        console.print("[dim]  Option 1: Create/update .env file with: ANTHROPIC_API_KEY=your_key_here[/dim]")
        console.print("[dim]  Option 2: Set environment variable: set ANTHROPIC_API_KEY=your_key_here[/dim]")
        sys.exit(1)

    # Load configuration
    try:
        config = load_config("config.yaml")
    except FileNotFoundError:
        console.print("[bold red]❌ Error: config.yaml not found![/bold red]")
        console.print("[yellow]Please create a config.yaml file with your settings.[/yellow]")
        sys.exit(1)

    # Verify slash command exists
    slash_command_path = Path(".claude/commands/japanese/analyze.md")
    if not slash_command_path.exists():
        console.print(f"[bold red]❌ Error: Slash command not found at {slash_command_path}[/bold red]")
        console.print("[yellow]Please ensure the Japanese tutor slash command is installed.[/yellow]")
        sys.exit(1)

    # Get the screenshot directory to monitor
    screenshot_dir = config.get('screenshot_dir')
    if not screenshot_dir or not os.path.exists(screenshot_dir):
        console.print(f"[bold red]❌ Error: Screenshot directory not found: {screenshot_dir}[/bold red]")
        console.print("[yellow]Please set 'screenshot_dir' in config.yaml to your RetroArch screenshots folder[/yellow]")
        sys.exit(1)

    console.print(f"[green]📁 Monitoring directory:[/green] {screenshot_dir}")
    console.print(f"[green]📝 Using slash command:[/green] {slash_command_path}")
    console.print(f"[green]🤖 Model:[/green] {config.get('model', 'sonnet')}")
    console.print(f"[green]📋 File patterns:[/green] {config.get('file_patterns', ['*.png', '*.jpg'])}")
    console.print("\n[cyan]Waiting for new screenshots...[/cyan]\n")

    # Create event handler and observer
    event_handler = ScreenshotHandler(config)
    observer = Observer()
    observer.schedule(event_handler, screenshot_dir, recursive=False)
    
    # Start monitoring
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n\n[bold red]🛑 Stopping screenshot watcher...[/bold red]")
        observer.stop()

    observer.join()
    console.print("[bold cyan]👋 Goodbye![/bold cyan]")


if __name__ == "__main__":
    main()