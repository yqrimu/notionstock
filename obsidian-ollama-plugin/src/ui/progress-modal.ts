import { App, Modal } from "obsidian";

export class ProgressModal extends Modal {
	private outputContainerEl!: HTMLElement;
	private textEl!: HTMLElement;
	private statusEl!: HTMLElement;
	private cancelButton!: HTMLButtonElement;
	private abortController: AbortController;
	private onCancel: (() => void) | null = null;

	constructor(app: App) {
		super(app);
		this.abortController = new AbortController();
	}

	onOpen(): void {
		const { contentEl } = this;
		contentEl.empty();
		contentEl.addClass("ollama-progress-modal");

		// Header
		const headerEl = contentEl.createEl("div", { cls: "ollama-progress-header" });
		headerEl.createEl("h3", { text: "Processing with Ollama..." });

		// Status
		this.statusEl = contentEl.createEl("div", { cls: "ollama-progress-status" });
		this.statusEl.setText("Connecting to Ollama...");

		// Content area for streaming text
		this.outputContainerEl = contentEl.createEl("div", { cls: "ollama-progress-content" });
		this.textEl = this.outputContainerEl.createEl("div", { cls: "ollama-progress-text" });

		// Cancel button
		const buttonContainer = contentEl.createEl("div", { cls: "ollama-progress-buttons" });
		this.cancelButton = buttonContainer.createEl("button", { text: "Cancel" });
		this.cancelButton.addEventListener("click", () => {
			this.cancel();
		});
	}

	onClose(): void {
		this.abortController.abort();
	}

	setStatus(status: string): void {
		this.statusEl.setText(status);
	}

	appendText(text: string): void {
		this.textEl.appendText(text);
		// Auto-scroll to bottom
		this.outputContainerEl.scrollTop = this.outputContainerEl.scrollHeight;
	}

	setText(text: string): void {
		this.textEl.setText(text);
	}

	clearText(): void {
		this.textEl.empty();
	}

	getAbortSignal(): AbortSignal {
		return this.abortController.signal;
	}

	setOnCancel(callback: () => void): void {
		this.onCancel = callback;
	}

	private cancel(): void {
		this.abortController.abort();
		if (this.onCancel) {
			this.onCancel();
		}
		this.close();
	}

	showSuccess(message: string): void {
		this.statusEl.setText(message);
		this.statusEl.addClass("ollama-success");
		this.cancelButton.setText("Close");
	}

	showError(message: string): void {
		this.statusEl.setText(message);
		this.statusEl.addClass("ollama-error");
		this.cancelButton.setText("Close");
	}
}
