# 🎮 Japanese Tutor - RetroArch Screenshot Watcher

An intelligent agent that watches your RetroArch screenshots folder and automatically provides Japanese translations and learning assistance using Claude.

Based on the [agentic drop zones pattern](https://github.com/disler/agentic-drop-zones) by disler.

## 🌟 Features

- **Automatic Detection**: Watches your RetroArch screenshots folder for new images
- **Instant Translation**: Automatically translates Japanese text in screenshots
- **Learning Support**: Provides readings (furigana/romaji), grammar notes, and vocabulary
- **Context Awareness**: Explains what's happening in the game
- **Always-On Assistant**: Runs in the background, ready whenever you take a screenshot

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

### Start the Watcher

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
