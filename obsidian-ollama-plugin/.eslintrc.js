module.exports = {
	root: true,
	parser: "@typescript-eslint/parser",
	plugins: ["@typescript-eslint"],
	extends: [
		"eslint:recommended",
		"plugin:@typescript-eslint/recommended",
	],
	parserOptions: {
		sourceType: "module",
		ecmaVersion: 2020,
	},
	env: {
		browser: true,
		node: true,
	},
	rules: {
		"no-unused-vars": "off",
		"@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
		"@typescript-eslint/explicit-function-return-type": "off",
		"@typescript-eslint/no-explicit-any": "warn",
		"prefer-const": "error",
		"no-console": "warn",
	},
};
