#!/usr/bin/env node

/**
 * @license
 * Copyright 2025 Flashy Project
 * SPDX-License-Identifier: Apache-2.0
 *
 * Qwen Code Free — Standalone CLI launcher
 * Launches qwen-code with free providers pre-configured.
 * No API keys, no tokens, no login required.
 */

import { spawn } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Parse args
const args = process.argv.slice(2);
let authType = 'qwen-free';
let model = '';
const passThroughArgs: string[] = [];

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === '--auth-type' && i + 1 < args.length) {
    authType = args[++i];
  } else if (arg.startsWith('--auth-type=')) {
    authType = arg.split('=')[1];
  } else if (arg === '--model' && i + 1 < args.length) {
    model = args[++i];
  } else if (arg.startsWith('--model=')) {
    model = arg.split('=')[1];
  } else if (arg === '--provider') {
    const provider = args[++i];
    if (provider === 'qwen') {
      authType = 'qwen-free';
    } else if (provider === 'deepinfra') {
      authType = 'deepinfra-free';
    }
  } else if (arg === '--help' || arg === '-h') {
    console.log(`
🆓 Qwen Code Free — AI Coding Agent (No API Key Required!)

Usage:
  qwen-free [options]

Free Provider Options:
  --provider qwen         Use Qwen Free (qwen3.5-plus, qwen3-coder-plus, etc.)
  --provider deepinfra    Use DeepInfra Free (Llama 3, Qwen 2.5, etc.)
  --auth-type <type>      Set auth type directly (qwen-free, deepinfra-free)
  --model <model>         Set the model to use

Examples:
  qwen-free                                # Start with Qwen Free (default)
  qwen-free --provider deepinfra           # Start with DeepInfra Free
  qwen-free --model qwen3-coder-plus       # Use Qwen3 Coder
  qwen-free --model Qwen/Qwen2.5-Coder-32B-Instruct --provider deepinfra

Available Qwen Free Models:
  qwen3.6-plus          Latest Qwen 3.6 Plus
  qwen3.5-plus          Qwen 3.5 Plus (default)
  qwen3.5-flash         Qwen 3.5 Flash (fast)
  qwen3.5-397b-a17b     Qwen 3.5 397B MoE
  qwen3-coder-plus      Qwen 3 Coder (coding specialist)
  qwen-max-latest       Qwen 2.5 Max (legacy)

Available DeepInfra Free Models:
  meta-llama/Meta-Llama-3-8B-Instruct       Llama 3 8B (default)
  meta-llama/Meta-Llama-3-70B-Instruct      Llama 3 70B
  Qwen/Qwen2.5-72B-Instruct                 Qwen 2.5 72B
  Qwen/Qwen2.5-Coder-32B-Instruct           Qwen 2.5 Coder 32B
  microsoft/WizardLM-2-8x22B                WizardLM-2 8x22B
  mistralai/Mistral-7B-Instruct-v0.1        Mistral 7B
`);
    process.exit(0);
  } else {
    passThroughArgs.push(arg);
  }
}

// Set default models per provider
if (!model) {
  if (authType === 'deepinfra-free') {
    model = 'meta-llama/Meta-Llama-3-8B-Instruct';
  } else {
    model = 'qwen3.5-plus';
  }
}

// Build qwen-code command
const qwenArgs = [
  '--auth-type',
  authType,
  '--model',
  model,
  ...passThroughArgs,
];

console.log(`
╔══════════════════════════════════════════════════════════╗
║            🆓  QWEN CODE FREE  🆓                       ║
║                                                          ║
║  Provider: ${authType.padEnd(43)}║
║  Model:    ${model.padEnd(43)}║
║  API Key:  Not required! 🎉                              ║
║                                                          ║
║  Powered by Flashy free providers                        ║
╚══════════════════════════════════════════════════════════╝
`);

// Try to find qwen-code
const qwenCodePath = resolve(__dirname, 'qwen-code');

const child = spawn('npx', ['qwen-code', ...qwenArgs], {
  cwd: qwenCodePath,
  stdio: 'inherit',
  env: {
    ...process.env,
    QWEN_FREE_MODEL: authType === 'qwen-free' ? model : undefined,
    DEEPINFRA_FREE_MODEL: authType === 'deepinfra-free' ? model : undefined,
  },
});

child.on('exit', (code) => {
  process.exit(code ?? 0);
});

child.on('error', (err) => {
  console.error('Failed to start qwen-code:', err.message);
  console.error('\nMake sure you have installed dependencies:');
  console.error('  cd qwen-code && npm install && npm run build && npm run bundle');
  process.exit(1);
});
