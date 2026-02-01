# Ollama Integration for Obsidian

An Obsidian plugin that integrates with locally-running [Ollama](https://ollama.ai) to provide AI-powered text manipulation features including rewriting, expanding, and summarizing content.

## Features

### Text Selection Context Menu

Right-click on selected text to access:

- **Rewrite using Ollama** - Improve clarity, grammar, and style while keeping the same meaning
- **Rewrite and Expand using Ollama** - Add more detail, examples, and depth
- **Summarize using Ollama** - Condense text to key points

### File Context Menu

Right-click on any markdown file in the file explorer to access:

- **Summarize and Generate New File** - Creates a new `filename-summary.md` with a comprehensive summary
- **Summarize and Reorganize** - Reorganizes the file content with a summary section at the top

### Additional Features

- **Streaming output** - See text as it's being generated in real-time
- **Customizable prompts** - Modify the prompts used for each operation
- **Model selection** - Choose from any model available in your Ollama installation
- **Keyboard shortcuts** - Commands available via command palette

## Requirements

- [Ollama](https://ollama.ai) installed and running locally
- At least one model pulled (e.g., `ollama pull llama3.2`)

## Installation

### Manual Installation

1. Download the latest release (`main.js`, `manifest.json`, `styles.css`)
2. Create a folder named `ollama-integration` in your vault's `.obsidian/plugins/` directory
3. Copy the downloaded files into the folder
4. Enable the plugin in Obsidian Settings → Community Plugins

### Building from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/obsidian-ollama-plugin.git
cd obsidian-ollama-plugin

# Install dependencies
npm install

# Build
npm run build

# For development with hot reload
npm run dev
```

## Configuration

Open Settings → Ollama Integration to configure:

### Connection

- **Ollama Host** - URL of your Ollama server (default: `http://127.0.0.1:11434`)
- **Test Connection** - Verify Ollama is running and accessible

### Model

- **Default Model** - Select from available models or enter manually

### Behavior

- **Enable Streaming** - Show text as it's generated (recommended)
- **Request Timeout** - Maximum wait time for responses (10-300 seconds)

### Custom Prompts

Customize the prompts for each operation:
- Rewrite Prompt
- Expand Prompt
- Summarize Prompt
- Summarize File Prompt
- Reorganize Prompt

## Usage

### Text Selection Operations

1. Select text in any markdown file
2. Right-click to open context menu
3. Choose an Ollama operation
4. Watch the progress modal as text is generated
5. Selected text is automatically replaced with the result

### File Operations

1. Right-click on any `.md` file in the file explorer
2. Choose an Ollama operation
3. For "Summarize and Generate New File": A new summary file is created
4. For "Summarize and Reorganize": The file is updated in place

### Keyboard Shortcuts

Access operations via the Command Palette (Ctrl/Cmd + P):
- "Rewrite selection using Ollama"
- "Rewrite and expand selection using Ollama"
- "Summarize selection using Ollama"

## Troubleshooting

### "Cannot connect to Ollama"

1. Ensure Ollama is running: `ollama serve`
2. Check the host URL in settings (default: `http://127.0.0.1:11434`)
3. Test the connection using the "Test" button in settings

### "Model not found"

1. Pull the model first: `ollama pull llama3.2`
2. Check available models: `ollama list`
3. Select a valid model in plugin settings

### Slow responses

- Larger models require more processing time
- Consider using a smaller/faster model like `llama3.2` or `phi3`
- Increase the timeout in settings if needed

## Development

```bash
# Install dependencies
npm install

# Run in development mode (watches for changes)
npm run dev

# Run linter
npm run lint

# Build for production
npm run build
```

## License

MIT License - see LICENSE file for details.

## Credits

- [Obsidian](https://obsidian.md) - The knowledge management app
- [Ollama](https://ollama.ai) - Local LLM runner
- [Obsidian Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin) - Plugin template
