"""
Japanese Tutor Screenshot Watcher
An agentic drop zone that monitors RetroArch screenshots and provides Japanese translations.
Based on the agentic drop zones pattern by disler.
"""

import os
import sys
import time
import base64
from pathlib import Path
from typing import List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import anthropic
import yaml


class ScreenshotHandler(FileSystemEventHandler):
    """Handles new screenshot files and triggers Japanese translation."""
    
    def __init__(self, config: Dict[str, Any], prompt_template: str):
        self.config = config
        self.prompt_template = prompt_template
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.file_patterns = config.get('file_patterns', ['*.png', '*.jpg', '*.jpeg'])
        self.processed_files = set()
        
    def matches_pattern(self, filename: str) -> bool:
        """Check if filename matches any of the configured patterns."""
        for pattern in self.file_patterns:
            if pattern.startswith('*.'):
                extension = pattern[1:]  # Remove the *
                if filename.lower().endswith(extension):
                    return True
        return False
    
    def encode_image(self, image_path: str) -> tuple[str, str]:
        """Encode image to base64 and determine media type."""
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
        
        # Determine media type based on file extension
        ext = Path(image_path).suffix.lower()
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        media_type = media_type_map.get(ext, 'image/png')
        
        return image_data, media_type
    
    def process_screenshot(self, file_path: str):
        """Process a screenshot with Claude for Japanese translation."""
        try:
            print(f"\n{'='*60}")
            print(f"📸 New screenshot detected: {Path(file_path).name}")
            print(f"{'='*60}\n")
            
            # Encode the image
            image_data, media_type = self.encode_image(file_path)
            
            # Prepare the prompt (replace FILE_PATH placeholder)
            prompt = self.prompt_template.replace("{{FILE_PATH}}", file_path)
            
            # Create message with image
            message = self.client.messages.create(
                model=self.config.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            # Print the response
            print("🤖 Claude's Response:")
            print("-" * 60)
            for block in message.content:
                if block.type == "text":
                    print(block.text)
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error processing screenshot: {e}")
            import traceback
            traceback.print_exc()
    
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


def load_prompt_template(prompt_path: str) -> str:
    """Load prompt template from file."""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Main entry point for the screenshot watcher."""
    print("🎮 Japanese Tutor Screenshot Watcher")
    print("Monitoring RetroArch screenshots for Japanese translation...\n")
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set!")
        print("Please set it with: set ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config("config.yaml")
    except FileNotFoundError:
        print("❌ Error: config.yaml not found!")
        print("Please create a config.yaml file with your settings.")
        sys.exit(1)
    
    # Load prompt template
    prompt_path = config.get('prompt_template', 'prompts/japanese_tutor.md')
    try:
        prompt_template = load_prompt_template(prompt_path)
    except FileNotFoundError:
        print(f"❌ Error: Prompt template not found at {prompt_path}")
        sys.exit(1)
    
    # Get the screenshot directory to monitor
    screenshot_dir = config.get('screenshot_dir')
    if not screenshot_dir or not os.path.exists(screenshot_dir):
        print(f"❌ Error: Screenshot directory not found: {screenshot_dir}")
        print("Please set 'screenshot_dir' in config.yaml to your RetroArch screenshots folder")
        sys.exit(1)
    
    print(f"📁 Monitoring directory: {screenshot_dir}")
    print(f"📝 Using prompt template: {prompt_path}")
    print(f"🤖 Model: {config.get('model', 'claude-sonnet-4-20250514')}")
    print(f"📋 File patterns: {config.get('file_patterns', ['*.png', '*.jpg'])}")
    print("\nWaiting for new screenshots...\n")
    
    # Create event handler and observer
    event_handler = ScreenshotHandler(config, prompt_template)
    observer = Observer()
    observer.schedule(event_handler, screenshot_dir, recursive=False)
    
    # Start monitoring
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping screenshot watcher...")
        observer.stop()
    
    observer.join()
    print("👋 Goodbye!")


if __name__ == "__main__":
    main()