import { App, PluginSettingTab, Setting } from "obsidian";
import type OllamaPlugin from "./main";

export interface OllamaPluginSettings {
	ollamaHost: string;
	defaultModel: string;
	streamingEnabled: boolean;
	requestTimeout: number;
	customPrompts: {
		rewrite: string;
		expand: string;
		summarize: string;
		summarizeFile: string;
		reorganize: string;
	};
}

export const DEFAULT_SETTINGS: OllamaPluginSettings = {
	ollamaHost: "http://127.0.0.1:11434",
	defaultModel: "llama3.2",
	streamingEnabled: true,
	requestTimeout: 60000,
	customPrompts: {
		rewrite: "Rewrite the following text with improved clarity, grammar, and style. Keep the same meaning and approximate length. Return only the rewritten text, no explanations:\n\n",
		expand: "Rewrite and expand the following text. Add more detail, examples, and depth while maintaining the original meaning. Return only the expanded text, no explanations:\n\n",
		summarize: "Summarize the following text concisely, capturing the key points. Return only the summary, no explanations:\n\n",
		summarizeFile: "Summarize the following document comprehensively. Include main topics, key points, and conclusions. Format with markdown headings:\n\n",
		reorganize: "Analyze and reorganize this document. Add a brief summary section at the top, then reorganize the content logically with clear markdown headings. Return the complete reorganized document:\n\n",
	},
};

export class OllamaSettingTab extends PluginSettingTab {
	plugin: OllamaPlugin;
	private availableModels: string[] = [];

	constructor(app: App, plugin: OllamaPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	async display(): Promise<void> {
		const { containerEl } = this;
		containerEl.empty();

		containerEl.createEl("h2", { text: "Ollama Integration Settings" });

		// Connection Settings Section
		containerEl.createEl("h3", { text: "Connection" });

		new Setting(containerEl)
			.setName("Ollama Host")
			.setDesc("The URL of your Ollama server (default: http://127.0.0.1:11434)")
			.addText((text) =>
				text
					.setPlaceholder("http://127.0.0.1:11434")
					.setValue(this.plugin.settings.ollamaHost)
					.onChange(async (value) => {
						this.plugin.settings.ollamaHost = value;
						await this.plugin.saveSettings();
					})
			);

		// Test Connection Button
		new Setting(containerEl)
			.setName("Test Connection")
			.setDesc("Verify that Ollama is running and accessible")
			.addButton((button) =>
				button
					.setButtonText("Test")
					.setCta()
					.onClick(async () => {
						button.setButtonText("Testing...");
						button.setDisabled(true);

						const isConnected = await this.plugin.ollamaService.testConnection();

						if (isConnected) {
							button.setButtonText("Connected!");
							// Refresh models list
							await this.refreshModels();
						} else {
							button.setButtonText("Failed - Check host");
						}

						setTimeout(() => {
							button.setButtonText("Test");
							button.setDisabled(false);
						}, 2000);
					})
			);

		// Model Settings Section
		containerEl.createEl("h3", { text: "Model" });

		// Try to load models on display
		await this.refreshModels();

		const modelSetting = new Setting(containerEl)
			.setName("Default Model")
			.setDesc("Select the Ollama model to use for text operations");

		if (this.availableModels.length > 0) {
			modelSetting.addDropdown((dropdown) => {
				// Add current model first if not in list (ensures it shows correctly)
				const currentModel = this.plugin.settings.defaultModel;
				if (currentModel && !this.availableModels.includes(currentModel)) {
					dropdown.addOption(currentModel, `${currentModel} (not found)`);
				}
				this.availableModels.forEach((model) => {
					dropdown.addOption(model, model);
				});
				dropdown.setValue(currentModel);
				dropdown.onChange(async (value) => {
					this.plugin.settings.defaultModel = value;
					await this.plugin.saveSettings();
				});
			});
		} else {
			modelSetting.addText((text) =>
				text
					.setPlaceholder("llama3.2")
					.setValue(this.plugin.settings.defaultModel)
					.onChange(async (value) => {
						this.plugin.settings.defaultModel = value;
						await this.plugin.saveSettings();
					})
			);
			modelSetting.descEl.createEl("br");
			modelSetting.descEl.createEl("span", {
				text: "Could not load models. Enter model name manually or test connection first.",
				cls: "mod-warning",
			});
		}

		// Behavior Settings Section
		containerEl.createEl("h3", { text: "Behavior" });

		new Setting(containerEl)
			.setName("Enable Streaming")
			.setDesc("Show text as it's being generated (recommended)")
			.addToggle((toggle) =>
				toggle
					.setValue(this.plugin.settings.streamingEnabled)
					.onChange(async (value) => {
						this.plugin.settings.streamingEnabled = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Request Timeout")
			.setDesc("Maximum time to wait for a response (in seconds)")
			.addSlider((slider) =>
				slider
					.setLimits(10, 300, 10)
					.setValue(this.plugin.settings.requestTimeout / 1000)
					.setDynamicTooltip()
					.onChange(async (value) => {
						this.plugin.settings.requestTimeout = value * 1000;
						await this.plugin.saveSettings();
					})
			);

		// Custom Prompts Section
		containerEl.createEl("h3", { text: "Custom Prompts" });
		containerEl.createEl("p", {
			text: "Customize the prompts used for each operation. The selected text or file content will be appended to these prompts.",
			cls: "setting-item-description",
		});

		new Setting(containerEl)
			.setName("Rewrite Prompt")
			.setDesc("Prompt for rewriting selected text")
			.addTextArea((text) =>
				text
					.setPlaceholder(DEFAULT_SETTINGS.customPrompts.rewrite)
					.setValue(this.plugin.settings.customPrompts.rewrite)
					.onChange(async (value) => {
						this.plugin.settings.customPrompts.rewrite = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Expand Prompt")
			.setDesc("Prompt for rewriting and expanding selected text")
			.addTextArea((text) =>
				text
					.setPlaceholder(DEFAULT_SETTINGS.customPrompts.expand)
					.setValue(this.plugin.settings.customPrompts.expand)
					.onChange(async (value) => {
						this.plugin.settings.customPrompts.expand = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Summarize Prompt")
			.setDesc("Prompt for summarizing selected text")
			.addTextArea((text) =>
				text
					.setPlaceholder(DEFAULT_SETTINGS.customPrompts.summarize)
					.setValue(this.plugin.settings.customPrompts.summarize)
					.onChange(async (value) => {
						this.plugin.settings.customPrompts.summarize = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Summarize File Prompt")
			.setDesc("Prompt for summarizing an entire file")
			.addTextArea((text) =>
				text
					.setPlaceholder(DEFAULT_SETTINGS.customPrompts.summarizeFile)
					.setValue(this.plugin.settings.customPrompts.summarizeFile)
					.onChange(async (value) => {
						this.plugin.settings.customPrompts.summarizeFile = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Reorganize Prompt")
			.setDesc("Prompt for summarizing and reorganizing a file")
			.addTextArea((text) =>
				text
					.setPlaceholder(DEFAULT_SETTINGS.customPrompts.reorganize)
					.setValue(this.plugin.settings.customPrompts.reorganize)
					.onChange(async (value) => {
						this.plugin.settings.customPrompts.reorganize = value;
						await this.plugin.saveSettings();
					})
			);

		// Reset Prompts Button
		new Setting(containerEl)
			.setName("Reset Prompts")
			.setDesc("Reset all prompts to their default values")
			.addButton((button) =>
				button
					.setButtonText("Reset to Defaults")
					.setWarning()
					.onClick(async () => {
						this.plugin.settings.customPrompts = { ...DEFAULT_SETTINGS.customPrompts };
						await this.plugin.saveSettings();
						this.display(); // Refresh the settings tab
					})
			);
	}

	private async refreshModels(): Promise<void> {
		try {
			this.availableModels = await this.plugin.ollamaService.listModels();
		} catch {
			this.availableModels = [];
		}
	}
}
