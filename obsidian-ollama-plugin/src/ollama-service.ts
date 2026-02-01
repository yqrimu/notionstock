import { requestUrl, RequestUrlResponse } from "obsidian";
import type { OllamaPluginSettings } from "./settings";

export interface OllamaGenerateResponse {
	model: string;
	response: string;
	done: boolean;
}

export interface OllamaModel {
	name: string;
	modified_at: string;
	size: number;
}

export interface OllamaListResponse {
	models: OllamaModel[];
}

export class OllamaService {
	private getSettings: () => OllamaPluginSettings;

	constructor(getSettings: () => OllamaPluginSettings) {
		this.getSettings = getSettings;
	}

	private get host(): string {
		return this.getSettings().ollamaHost.replace(/\/$/, "");
	}

	private get model(): string {
		return this.getSettings().defaultModel;
	}

	/**
	 * Test connection to Ollama server
	 */
	async testConnection(): Promise<boolean> {
		try {
			const response = await requestUrl({
				url: `${this.host}/api/tags`,
				method: "GET",
				throw: false,
			});
			return response.status === 200;
		} catch {
			return false;
		}
	}

	/**
	 * List available models from Ollama
	 */
	async listModels(): Promise<string[]> {
		try {
			const response: RequestUrlResponse = await requestUrl({
				url: `${this.host}/api/tags`,
				method: "GET",
			});

			const data = response.json as OllamaListResponse;
			if (!data.models || !Array.isArray(data.models)) {
				return [];
			}
			return data.models.map((m) => m.name);
		} catch {
			throw new Error("Failed to list models. Is Ollama running?");
		}
	}

	/**
	 * Generate completion without streaming
	 */
	async generate(prompt: string, content: string): Promise<string> {
		const fullPrompt = prompt + content;

		try {
			const response: RequestUrlResponse = await requestUrl({
				url: `${this.host}/api/generate`,
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					model: this.model,
					prompt: fullPrompt,
					stream: false,
				}),
				throw: true,
			});

			const data = response.json as OllamaGenerateResponse;
			return data.response;
		} catch (error) {
			throw this.handleError(error);
		}
	}

	/**
	 * Generate completion with streaming support
	 * Uses fetch API directly for streaming since requestUrl doesn't support it
	 */
	async generateStream(
		prompt: string,
		content: string,
		onToken: (token: string) => void,
		abortSignal?: AbortSignal
	): Promise<string> {
		const fullPrompt = prompt + content;

		try {
			const response = await fetch(`${this.host}/api/generate`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					model: this.model,
					prompt: fullPrompt,
					stream: true,
				}),
				signal: abortSignal,
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Ollama error: ${response.status} - ${errorText}`);
			}

			if (!response.body) {
				throw new Error("Response body is null");
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let fullResponse = "";

			// eslint-disable-next-line no-constant-condition
			while (true) {
				const { done, value } = await reader.read();

				if (done) break;

				const chunk = decoder.decode(value, { stream: true });
				const lines = chunk.split("\n").filter((line) => line.trim());

				for (const line of lines) {
					try {
						const data = JSON.parse(line) as OllamaGenerateResponse;
						if (data.response) {
							fullResponse += data.response;
							onToken(data.response);
						}
					} catch {
						// Skip malformed JSON lines
					}
				}
			}

			return fullResponse;
		} catch (error) {
			if (error instanceof Error && error.name === "AbortError") {
				throw new Error("Request was cancelled");
			}
			throw this.handleError(error);
		}
	}

	/**
	 * Handle and format errors
	 */
	private handleError(error: unknown): Error {
		if (error instanceof Error) {
			if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
				return new Error("Cannot connect to Ollama. Please ensure Ollama is running.");
			}
			if (error.message.includes("404")) {
				return new Error(`Model "${this.model}" not found. Please select a different model in settings.`);
			}
			return error;
		}
		return new Error("An unknown error occurred");
	}
}
