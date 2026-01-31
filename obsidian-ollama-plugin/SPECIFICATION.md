# Obsidian Ollama Plugin - Specification & Roadmap

## Project Overview

An Obsidian plugin that integrates with locally-running Ollama to provide AI-powered text manipulation features including rewriting, expanding, and summarizing content.

## Research Summary

### Obsidian Plugin Architecture

Based on research from [Obsidian Developer Documentation](https://docs.obsidian.md/Home) and [obsidian-sample-plugin](https://github.com/obsidianmd/obsidian-sample-plugin):

**Key Components:**
- **Plugin Class**: Extends `Plugin` from obsidian module with `onload()` and `onunload()` lifecycle methods
- **Settings**: Uses `PluginSettingTab` for configuration UI
- **Context Menus**: Register via `workspace.on("editor-menu")` and `workspace.on("file-menu")` events
- **Editor API**: Access selection via `editor.getSelection()` and replace via `editor.replaceSelection()`

**Build System:**
- TypeScript with esbuild bundler
- ESLint with Obsidian-specific rules
- Hot reload during development

### Ollama Integration

Based on [ollama-js library](https://github.com/ollama/ollama-js):

**Key Features:**
- Simple API: `ollama.chat()` and `ollama.generate()`
- Streaming support via AsyncGenerator
- Configurable host (default: `http://127.0.0.1:11434`)
- Browser-compatible via `ollama/browser` import

---

## Feature Specifications

### Feature 1: Paragraph Selection Context Menu

**Trigger:** Right-click on selected text in editor

**Menu Items:**
| Menu Item | Action | Description |
|-----------|--------|-------------|
| Rewrite using Ollama | Replace selection | Rewrite the text with improved clarity and style |
| Rewrite and Expand using Ollama | Replace selection | Rewrite and add more detail/depth |
| Summarize using Ollama | Replace selection | Condense the text to key points |

**Technical Implementation:**
```typescript
this.registerEvent(
  this.app.workspace.on("editor-menu", (menu, editor, view) => {
    const selection = editor.getSelection();
    if (selection && selection.trim().length > 0) {
      // Add menu items
      menu.addItem((item) => {
        item.setTitle("Rewrite using Ollama")
            .setIcon("pencil")
            .onClick(() => this.rewriteSelection(editor, selection));
      });
      // ... additional items
    }
  })
);
```

**Prompts:**
- **Rewrite**: "Rewrite the following text with improved clarity, grammar, and style. Keep the same meaning and approximate length. Return only the rewritten text, no explanations."
- **Rewrite and Expand**: "Rewrite and expand the following text. Add more detail, examples, and depth while maintaining the original meaning. Return only the expanded text, no explanations."
- **Summarize**: "Summarize the following text concisely, capturing the key points. Return only the summary, no explanations."

### Feature 2: File Context Menu

**Trigger:** Right-click on a file in the file explorer

**Menu Items:**
| Menu Item | Action | Description |
|-----------|--------|-------------|
| Summarize and Generate New File | Create new file | Create `[filename]-summary.md` with summary |
| Summarize and Reorganize | Modify file | Reorganize content with summary at top |

**Technical Implementation:**
```typescript
this.registerEvent(
  this.app.workspace.on("file-menu", (menu, file) => {
    if (file instanceof TFile && file.extension === "md") {
      menu.addItem((item) => {
        item.setTitle("Summarize and Generate New File")
            .setIcon("file-plus")
            .onClick(() => this.summarizeToNewFile(file));
      });
      // ... additional items
    }
  })
);
```

**Prompts:**
- **Summarize and Generate**: "Summarize the following document comprehensively. Include main topics, key points, and conclusions. Format with markdown headings."
- **Summarize and Reorganize**: "Analyze and reorganize this document. Add a summary section at the top, then reorganize the content logically with clear headings."

---

## Technical Architecture

### Project Structure

```
obsidian-ollama-plugin/
├── src/
│   ├── main.ts              # Plugin entry point
│   ├── settings.ts          # Settings tab and types
│   ├── ollama-service.ts    # Ollama API wrapper
│   ├── prompts.ts           # Prompt templates
│   └── ui/
│       └── progress-modal.ts # Progress indicator modal
├── styles.css               # Plugin styles
├── manifest.json            # Plugin metadata
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── esbuild.config.mjs       # Build config
├── .eslintrc.js             # Linting rules
├── README.md                # User documentation
└── SPECIFICATION.md         # This file
```

### Plugin Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ollamaHost` | string | `http://127.0.0.1:11434` | Ollama server URL |
| `defaultModel` | string | `llama3.2` | Default model for operations |
| `streamingEnabled` | boolean | `true` | Show streaming output |
| `customPrompts.rewrite` | string | (preset) | Custom rewrite prompt |
| `customPrompts.expand` | string | (preset) | Custom expand prompt |
| `customPrompts.summarize` | string | (preset) | Custom summarize prompt |

### Ollama Service Design

```typescript
interface OllamaService {
  // Test connection to Ollama
  testConnection(): Promise<boolean>;

  // List available models
  listModels(): Promise<string[]>;

  // Generate completion (non-streaming)
  generate(prompt: string, content: string): Promise<string>;

  // Generate completion (streaming)
  generateStream(
    prompt: string,
    content: string,
    onToken: (token: string) => void
  ): Promise<string>;
}
```

### Error Handling

| Error Scenario | User Feedback | Recovery |
|----------------|---------------|----------|
| Ollama not running | Notice: "Cannot connect to Ollama. Please ensure Ollama is running." | Open settings |
| Model not found | Notice: "Model X not found. Please select a different model." | Open settings |
| Empty selection | No menu items shown | N/A |
| API timeout | Notice: "Request timed out. Please try again." | Retry button |
| Generation error | Notice with error message | Log to console |

### Performance Considerations

1. **Lazy Loading**: Only import ollama library when needed
2. **Streaming**: Use streaming for long responses to show progress
3. **Debouncing**: Prevent rapid repeated requests
4. **Caching**: Cache model list (refresh on settings open)
5. **Timeout**: 60-second timeout for API requests

---

## User Experience

### Progress Indication

During processing:
1. Show modal with spinner and "Processing with Ollama..."
2. If streaming enabled, show live token output
3. Allow cancellation via Escape key or Cancel button
4. Show success notice on completion

### Visual Design

- Use Obsidian's native styling
- Icons from Lucide (Obsidian's icon library)
- Consistent with Obsidian's UI patterns

---

## Development Roadmap

### Phase 1: Foundation (Core Setup)
- [ ] Initialize project with obsidian-sample-plugin template
- [ ] Configure TypeScript, ESLint, esbuild
- [ ] Create manifest.json with plugin metadata
- [ ] Implement basic plugin structure with settings tab
- [ ] Add Ollama connection settings UI

### Phase 2: Ollama Integration
- [ ] Implement OllamaService class
- [ ] Add connection testing functionality
- [ ] Implement model listing and selection
- [ ] Add streaming support
- [ ] Create error handling utilities

### Phase 3: Editor Context Menu Features
- [ ] Register editor-menu event
- [ ] Implement "Rewrite using Ollama" feature
- [ ] Implement "Rewrite and Expand using Ollama" feature
- [ ] Implement "Summarize using Ollama" feature
- [ ] Add progress modal for editor operations

### Phase 4: File Context Menu Features
- [ ] Register file-menu event
- [ ] Implement "Summarize and Generate New File" feature
- [ ] Implement "Summarize and Reorganize" feature
- [ ] Handle large files appropriately

### Phase 5: Polish & Release
- [ ] Add custom prompt configuration
- [ ] Write user documentation (README.md)
- [ ] Test across different Obsidian versions
- [ ] Optimize performance
- [ ] Prepare for community plugin submission

---

## API Reference

### Obsidian APIs Used

| API | Purpose | Documentation |
|-----|---------|---------------|
| `Plugin` | Base plugin class | [Plugin API](https://docs.obsidian.md/Reference/TypeScript+API/Plugin) |
| `PluginSettingTab` | Settings UI | [Settings](https://docs.obsidian.md/Plugins/User+interface/Settings) |
| `workspace.on("editor-menu")` | Editor context menu | [Context Menus](https://docs.obsidian.md/Plugins/User+interface/Context+menus) |
| `workspace.on("file-menu")` | File explorer context menu | [Context Menus](https://docs.obsidian.md/Plugins/User+interface/Context+menus) |
| `Editor.getSelection()` | Get selected text | [Editor API](https://docs.obsidian.md/Reference/TypeScript+API/Editor/getSelection) |
| `Editor.replaceSelection()` | Replace selection | [Editor API](https://docs.obsidian.md/Reference/TypeScript+API/Editor) |
| `vault.read()` / `vault.modify()` | File operations | [Vault API](https://docs.obsidian.md/Reference/TypeScript+API/Vault) |
| `Modal` | Progress dialogs | [Modals](https://docs.obsidian.md/Plugins/User+interface/Modals) |
| `Notice` | Toast notifications | [Notice API](https://docs.obsidian.md/Reference/TypeScript+API/Notice) |

### Ollama APIs Used

| API | Purpose | Documentation |
|-----|---------|---------------|
| `ollama.chat()` | Generate completions | [ollama-js](https://github.com/ollama/ollama-js) |
| `ollama.list()` | List available models | [ollama-js](https://github.com/ollama/ollama-js) |
| Streaming | Progressive output | [ollama-js](https://github.com/ollama/ollama-js) |

---

## Dependencies

```json
{
  "dependencies": {
    "ollama": "^0.5.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "builtin-modules": "^3.3.0",
    "esbuild": "^0.20.0",
    "obsidian": "^1.5.0",
    "typescript": "^5.4.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "eslint": "^8.57.0"
  }
}
```

---

## Success Criteria

1. **Functional**: All 5 context menu operations work correctly
2. **Reliable**: Graceful error handling for all edge cases
3. **Performant**: No noticeable lag in UI, streaming works smoothly
4. **User-friendly**: Clear feedback during operations, intuitive settings
5. **Maintainable**: Clean code, well-documented, easy to extend

---

## References

- [Obsidian Developer Documentation](https://docs.obsidian.md/Home)
- [Obsidian Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin)
- [Obsidian API Types](https://github.com/obsidianmd/obsidian-api/blob/master/obsidian.d.ts)
- [Ollama JavaScript Library](https://github.com/ollama/ollama-js)
- [Ollama Documentation](https://docs.ollama.com)
- [Context Menus Guide](https://marcusolsson.github.io/obsidian-plugin-docs/user-interface/context-menus)
