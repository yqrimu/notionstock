import { Editor, Notice, Plugin, TFile, TAbstractFile, Menu } from "obsidian";
import { OllamaPluginSettings, DEFAULT_SETTINGS, OllamaSettingTab } from "./settings";
import { OllamaService } from "./ollama-service";
import { ProgressModal } from "./ui/progress-modal";

export default class OllamaPlugin extends Plugin {
	settings!: OllamaPluginSettings;
	ollamaService!: OllamaService;

	async onload(): Promise<void> {
		await this.loadSettings();

		// Initialize Ollama service
		this.ollamaService = new OllamaService(() => this.settings);

		// Add settings tab
		this.addSettingTab(new OllamaSettingTab(this.app, this));

		// Register editor context menu (right-click on selected text)
		this.registerEvent(
			this.app.workspace.on("editor-menu", (menu: Menu, editor: Editor) => {
				const selection = editor.getSelection();
				if (selection && selection.trim().length > 0) {
					this.addEditorMenuItems(menu, editor, selection);
				}
			})
		);

		// Register file context menu (right-click on file in explorer)
		this.registerEvent(
			this.app.workspace.on("file-menu", (menu: Menu, file: TAbstractFile) => {
				if (file instanceof TFile && file.extension === "md") {
					this.addFileMenuItems(menu, file);
				}
			})
		);

		// Add commands for keyboard shortcuts
		this.addCommand({
			id: "ollama-rewrite",
			name: "Rewrite selection using Ollama",
			editorCallback: (editor: Editor) => {
				const selection = editor.getSelection();
				if (selection && selection.trim().length > 0) {
					this.rewriteSelection(editor, selection);
				} else {
					new Notice("Please select some text first");
				}
			},
		});

		this.addCommand({
			id: "ollama-expand",
			name: "Rewrite and expand selection using Ollama",
			editorCallback: (editor: Editor) => {
				const selection = editor.getSelection();
				if (selection && selection.trim().length > 0) {
					this.expandSelection(editor, selection);
				} else {
					new Notice("Please select some text first");
				}
			},
		});

		this.addCommand({
			id: "ollama-summarize",
			name: "Summarize selection using Ollama",
			editorCallback: (editor: Editor) => {
				const selection = editor.getSelection();
				if (selection && selection.trim().length > 0) {
					this.summarizeSelection(editor, selection);
				} else {
					new Notice("Please select some text first");
				}
			},
		});

	}

	onunload(): void {
		// Cleanup handled by Obsidian's plugin system
	}

	async loadSettings(): Promise<void> {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings(): Promise<void> {
		await this.saveData(this.settings);
	}

	/**
	 * Add menu items for editor context menu (text selection)
	 */
	private addEditorMenuItems(menu: Menu, editor: Editor, selection: string): void {
		menu.addSeparator();

		menu.addItem((item) => {
			item.setTitle("Rewrite using Ollama")
				.setIcon("pencil")
				.onClick(() => this.rewriteSelection(editor, selection));
		});

		menu.addItem((item) => {
			item.setTitle("Rewrite and Expand using Ollama")
				.setIcon("unfold-vertical")
				.onClick(() => this.expandSelection(editor, selection));
		});

		menu.addItem((item) => {
			item.setTitle("Summarize using Ollama")
				.setIcon("file-minus")
				.onClick(() => this.summarizeSelection(editor, selection));
		});
	}

	/**
	 * Add menu items for file context menu
	 */
	private addFileMenuItems(menu: Menu, file: TFile): void {
		menu.addSeparator();

		menu.addItem((item) => {
			item.setTitle("Summarize and Generate New File")
				.setIcon("file-plus")
				.onClick(() => this.summarizeToNewFile(file));
		});

		menu.addItem((item) => {
			item.setTitle("Summarize and Reorganize")
				.setIcon("list-ordered")
				.onClick(() => this.summarizeAndReorganize(file));
		});
	}

	/**
	 * Rewrite selected text
	 */
	private async rewriteSelection(editor: Editor, selection: string): Promise<void> {
		await this.processSelection(
			editor,
			selection,
			this.settings.customPrompts.rewrite,
			"Rewriting text..."
		);
	}

	/**
	 * Rewrite and expand selected text
	 */
	private async expandSelection(editor: Editor, selection: string): Promise<void> {
		await this.processSelection(
			editor,
			selection,
			this.settings.customPrompts.expand,
			"Expanding text..."
		);
	}

	/**
	 * Summarize selected text
	 */
	private async summarizeSelection(editor: Editor, selection: string): Promise<void> {
		await this.processSelection(
			editor,
			selection,
			this.settings.customPrompts.summarize,
			"Summarizing text..."
		);
	}

	/**
	 * Process selection with given prompt
	 */
	private async processSelection(
		editor: Editor,
		selection: string,
		prompt: string,
		statusMessage: string
	): Promise<void> {
		const modal = new ProgressModal(this.app);
		modal.open();
		modal.setStatus(statusMessage);

		try {
			let result: string;

			if (this.settings.streamingEnabled) {
				result = await this.ollamaService.generateStream(
					prompt,
					selection,
					(token) => modal.appendText(token),
					modal.getAbortSignal()
				);
			} else {
				modal.setStatus("Processing... (this may take a moment)");
				result = await this.ollamaService.generate(prompt, selection);
				modal.setText(result);
			}

			// Replace selection with result
			editor.replaceSelection(result);
			modal.showSuccess("Complete!");

			// Auto-close after brief delay
			setTimeout(() => modal.close(), 1000);
		} catch (error) {
			const message = error instanceof Error ? error.message : "An error occurred";
			modal.showError(message);
			new Notice(`Ollama error: ${message}`);
		}
	}

	/**
	 * Summarize file and create new summary file
	 */
	private async summarizeToNewFile(file: TFile): Promise<void> {
		const modal = new ProgressModal(this.app);
		modal.open();
		modal.setStatus("Reading file...");

		try {
			// Read file content
			const content = await this.app.vault.read(file);

			if (!content.trim()) {
				modal.showError("File is empty");
				return;
			}

			modal.setStatus("Generating summary...");

			let summary: string;

			if (this.settings.streamingEnabled) {
				summary = await this.ollamaService.generateStream(
					this.settings.customPrompts.summarizeFile,
					content,
					(token) => modal.appendText(token),
					modal.getAbortSignal()
				);
			} else {
				summary = await this.ollamaService.generate(
					this.settings.customPrompts.summarizeFile,
					content
				);
				modal.setText(summary);
			}

			// Create new file with summary
			const baseName = file.basename;
			const newFileName = `${baseName}-summary.md`;
			const newFilePath = file.parent ? `${file.parent.path}/${newFileName}` : newFileName;

			// Check if file already exists
			const existingFile = this.app.vault.getAbstractFileByPath(newFilePath);
			if (existingFile) {
				// Append timestamp to make unique
				const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
				const uniqueFileName = `${baseName}-summary-${timestamp}.md`;
				const uniquePath = file.parent ? `${file.parent.path}/${uniqueFileName}` : uniqueFileName;
				await this.app.vault.create(uniquePath, summary);
				modal.showSuccess(`Created: ${uniqueFileName}`);
			} else {
				await this.app.vault.create(newFilePath, summary);
				modal.showSuccess(`Created: ${newFileName}`);
			}

			setTimeout(() => modal.close(), 2000);
		} catch (error) {
			const message = error instanceof Error ? error.message : "An error occurred";
			modal.showError(message);
			new Notice(`Ollama error: ${message}`);
		}
	}

	/**
	 * Summarize and reorganize file in place
	 */
	private async summarizeAndReorganize(file: TFile): Promise<void> {
		const modal = new ProgressModal(this.app);
		modal.open();
		modal.setStatus("Reading file...");

		try {
			// Read file content
			const content = await this.app.vault.read(file);

			if (!content.trim()) {
				modal.showError("File is empty");
				return;
			}

			modal.setStatus("Reorganizing content...");

			let reorganized: string;

			if (this.settings.streamingEnabled) {
				reorganized = await this.ollamaService.generateStream(
					this.settings.customPrompts.reorganize,
					content,
					(token) => modal.appendText(token),
					modal.getAbortSignal()
				);
			} else {
				reorganized = await this.ollamaService.generate(
					this.settings.customPrompts.reorganize,
					content
				);
				modal.setText(reorganized);
			}

			// Update file with reorganized content
			await this.app.vault.modify(file, reorganized);
			modal.showSuccess("File reorganized!");

			setTimeout(() => modal.close(), 2000);
		} catch (error) {
			const message = error instanceof Error ? error.message : "An error occurred";
			modal.showError(message);
			new Notice(`Ollama error: ${message}`);
		}
	}
}
