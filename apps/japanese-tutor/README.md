# 🎮 Japanese Tutor - Screenshot Translation & Learning Agent

An intelligent agent system that helps you learn Japanese through game screenshots with two modes:

1. **Screenshot Watcher** (Existing): Real-time translation of RetroArch screenshots
2. **Learning Agent** (NEW): MCP server with vocabulary tracking and flashcard reviews

Based on the [agentic drop zones pattern](https://github.com/disler/agentic-drop-zones) by disler.

## 🌟 Features

### Screenshot Watcher (Existing)
- **Automatic Detection**: Watches your RetroArch screenshots folder for new images
- **Instant Translation**: Automatically translates Japanese text in screenshots
- **Learning Support**: Provides readings (furigana/romaji), grammar notes, and vocabulary
- **Context Awareness**: Explains what's happening in the game
- **Always-On Assistant**: Runs in the background, ready whenever you take a screenshot

### Learning Agent (NEW - MCP Server)
- **Hybrid OCR**: Claude Vision API + manga-ocr for accurate text extraction
- **Vocabulary Tracking**: Automatic vocabulary database with study status (new/learning/known)
- **Flashcard System**: SM-2 spaced repetition algorithm for optimal learning
- **Learning Statistics**: Track progress, encounter counts, review performance
- **MCP Integration**: Works with Claude Desktop and other MCP clients
- **Offline Capable**: Local OCR and dictionary (manga-ocr + jamdict)

## 📋 Prerequisites

- Python 3.8 or higher
- Anthropic API key
- RetroArch with screenshot functionality enabled

## 🚀 Setup

### 1. Install Python Dependencies

```bash
cd D:\source\Cernji-Agents\apps\japanese-tutor
pip install -r requirements.txt
```

### 2. Set Your Anthropic API Key

**Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="your_api_key_here"
```

To make it permanent, add it to your system environment variables:
1. Search for "Environment Variables" in Windows
2. Add a new system variable: `ANTHROPIC_API_KEY` with your key

### 3. Configure the Screenshot Directory

Edit `config.yaml` and update the `screenshot_dir` path to point to your RetroArch screenshots folder.

**Finding your RetroArch screenshots folder:**
- Default location: `C:\Users\YourUsername\AppData\Roaming\RetroArch\screenshots`
- Or check RetroArch → Settings → Directory → Screenshots

Example config.yaml:
```yaml
screenshot_dir: "C:\\Users\\YourName\\AppData\\Roaming\\RetroArch\\screenshots"
```

### 4. Configure RetroArch Screenshot Hotkey

In RetroArch:
1. Go to Settings → Input → Hotkeys
2. Set a "Screenshot" hotkey (e.g., F8)
3. Make sure screenshots are enabled

## 🎯 Usage

### Mode 1: Screenshot Watcher (Real-time Translation)

#### Start the Watcher

```bash
python screenshot_watcher.py
```

You should see:
```
🎮 Japanese Tutor Screenshot Watcher
Monitoring RetroArch screenshots for Japanese translation...

📁 Monitoring directory: C:\Users\...\RetroArch\screenshots
📝 Using prompt template: prompts/japanese_tutor.md
🤖 Model: claude-sonnet-4-20250514
📋 File patterns: ['*.png', '*.jpg']

Waiting for new screenshots...
```

### Take Screenshots While Playing

1. Play your Japanese retro game (SNES, Game Boy, etc.)
2. When you see Japanese text you want to learn, press your screenshot hotkey (e.g., F8)
3. The agent will automatically detect the new screenshot and provide translation + learning assistance
4. Review Claude's response in the terminal

### Example Output

```
============================================================
📸 New screenshot detected: pokemon_red_001.png
============================================================

🤖 Claude's Response:
------------------------------------------------------------
### 📝 Japanese Text Found:
ポケモンずかんを　かんせい　させることが　わたしの　ゆめなのだ

### 🔤 Readings:
ポケモンずかん (pokemon zukan)
かんせい (kansei)
ゆめ (yume)

### 🌐 Translation:
"Completing the Pokédex is my dream!"

### 📚 Grammar Notes:
- を marks the direct object (Pokédex)
- させる is the causative form ("to make complete")
- のだ adds emphasis/explanation
...
============================================================
```

### Mode 2: Learning Agent (MCP Server)

The Learning Agent extends the screenshot watcher with vocabulary tracking and flashcard reviews.

#### Setup MCP Server

1. **Install dependencies** (includes manga-ocr, jamdict, etc.):
```bash
cd D:\source\Cernji-Agents\apps\japanese-tutor
uv pip install -r requirements.txt
```

2. **Download dictionary data** (required for offline lookups):
```bash
python -c "import jamdict; jamdict.Jamdict()"
```
This downloads ~100MB of JMDict data on first run.

3. **Start the MCP server**:
```bash
uv run japanese_agent.py
```

For HTTP server mode (production):
```bash
uv run japanese_agent.py --transport streamable-http --port 8080
```

4. **Configure Claude Desktop** to connect to the MCP server.

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "japanese-agent": {
      "command": "uv",
      "args": ["run", "D:\\source\\Cernji-Agents\\apps\\japanese-tutor\\japanese_agent.py"],
      "transport": "stdio"
    }
  }
}
```

#### Using MCP Tools in Claude Desktop

Once configured, you can use these tools in Claude Desktop conversations:

**Analyze screenshots:**
```
Please analyze this screenshot: C:\path\to\screenshot.png
```

**List vocabulary by status:**
```
Show me all new vocabulary words
Show me words I'm currently learning
```

**Get learning statistics:**
```
Show my Japanese learning progress
```

**Review flashcards:**
```
Let's review some flashcards
```

**Search vocabulary:**
```
Find the word "ポケモン" in my vocabulary
```

#### Available MCP Tools

- `analyze_screenshot(image_path)` - Extract and analyze Japanese text
- `get_vocabulary(vocab_id)` - Get vocabulary entry
- `list_vocabulary(status_filter, limit)` - List vocabulary by status
- `update_vocab_status(vocab_id, status)` - Update study status
- `search_vocabulary(query)` - Search vocabulary
- `get_vocab_stats()` - Get learning statistics
- `create_flashcard(vocab_id, screenshot_id)` - Create flashcard
- `get_due_flashcards(limit)` - Get due flashcards
- `update_flashcard_review(flashcard_id, rating)` - Record review
- `get_review_stats()` - Get review statistics

#### Slash Commands

You can also use slash commands directly in Claude Code:

- `/japanese:analyze` - Analyze screenshot
- `/japanese:vocab-list` - List vocabulary
- `/japanese:vocab-stats` - Show statistics
- `/japanese:review` - Start flashcard review
- `/japanese:flashcards` - Manage flashcards

## ⚙️ Configuration

### config.yaml Options

```yaml
# Directory to monitor
screenshot_dir: "path/to/screenshots"

# Prompt template
prompt_template: "prompts/japanese_tutor.md"

# Claude model (can use sonnet or opus)
model: "claude-sonnet-4-20250514"

# File patterns to watch
file_patterns:
  - "*.png"
  - "*.jpg"
  - "*.jpeg"
```

### Customizing the Prompt

Edit `prompts/japanese_tutor.md` to customize how Claude responds to your screenshots. You can:
- Adjust the response format
- Focus on specific learning goals
- Change the level of detail
- Add specific vocabulary focus areas

## 💡 Tips for Best Results

1. **Clear Screenshots**: Take screenshots with text clearly visible
2. **Pause the Game**: Pause before taking screenshots to ensure text isn't animated
3. **Good Games for Learning**:
   - RPGs (lots of dialogue): Dragon Quest, Final Fantasy, Pokemon
   - Adventure games: Zelda series
   - Text-heavy games: Visual novels
4. **Review Mode**: Use RetroArch's save states to replay important scenes
5. **Vocabulary Tracking**: Keep a notebook of vocabulary Claude teaches you

## 🔧 Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"
- Make sure you've set your API key as an environment variable
- Restart your terminal after setting it

### "Screenshot directory not found"
- Check the path in config.yaml
- Make sure to use double backslashes in Windows paths: `C:\\Users\\...`
- Verify the directory exists

### Screenshots not being detected
- Make sure RetroArch is saving to the configured directory
- Check that file patterns in config.yaml match your screenshot format
- Try taking a test screenshot and verify it appears in the folder

### No response from Claude
- Check your internet connection
- Verify your API key is valid
- Check the terminal for error messages

## 📚 Learning Resources

Combine this tool with:
- A Japanese dictionary app
- Anki for spaced repetition
- Japanese grammar guides
- RetroArch save states for review

## 🤝 Credits

Based on the [Agentic Drop Zones](https://github.com/disler/agentic-drop-zones) pattern by @disler (IndyDevDan).

Powered by Anthropic's Claude for intelligent Japanese translation and tutoring.

## 📝 License

This tool is for personal educational use. Ensure you own the games you're playing.

---

Happy learning! 🎌🎮
