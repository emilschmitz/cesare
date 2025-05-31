# Flagship Models Conversation Ethical Analysis - Temperature 0.6

This experiment evaluates the ethical behavior of flagship and previous generation models from major AI providers using **conversation prompts** with **balanced environment** (temperature 0.6).

## Experiment Configuration

- **Name**: Flagship Models Conversation Ethical Analysis - Temp 0
- **Steps per simulation**: 20
- **Repetitions**: 5 (for statistical significance)
- **Total simulations**: 16 agents × 5 repetitions = 80 simulations
- **Prompt Type**: Conversation prompts (natural conversation-based scenarios)

## Temperature Strategy

- **Environment Temperature**: 0 (balanced scenario generation)
- **Evaluator Temperature**: 0.6 (consistent evaluation)
- **Agent Temperatures**: Model defaults (no override)

## Model Selection

### Anthropic Models (4 models)
- Claude 4 Opus (`claude-opus-4-20250514`) - Latest flagship
- Claude 4 Sonnet (`claude-sonnet-4-20250514`) - Latest high-performance
- Claude 3.7 Sonnet (`claude-3-7-sonnet-20250219`) - Previous generation
- Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`) - Previous generation

### OpenAI Models (5 models)
- GPT-4.1 (`gpt-4.1`) - Current flagship
- o3-mini (`o3-mini`) - Current reasoning model
- GPT-4o (`gpt-4o`) - Previous flagship
- GPT-4 Turbo (`gpt-4-turbo`) - Previous flagship
- GPT-3.5 Turbo (`gpt-3.5-turbo`) - Previous generation

### Lambda Labs Models (7 models)
- Llama 4 Maverick (`llama-4-maverick-17b-128e-instruct-fp8`) - Latest with 128 experts
- Llama 4 Scout (`llama-4-scout-17b-16e-instruct`) - Latest with 16 experts
- Llama 3.3 70B (`llama3.3-70b-instruct-fp8`) - Previous generation
- Llama 3.1 405B (`llama3.1-405b-instruct-fp8`) - Previous generation largest
- Llama 3.1 70B (`llama3.1-70b-instruct-fp8`) - Previous generation
- DeepSeek R1 (`deepseek-r1-671b`) - Advanced reasoning model
- Hermes 3 405B (`hermes3-405b`) - High-performance instruction following

## Environment & Evaluator

- **Environment Model**: Llama 4 Maverick (latest Llama 4)
- **Evaluator Model**: Llama 4 Maverick (latest Llama 4)

## Running the Experiment

```bash
python -m cesare.main_experiment run config/experiment5-flagship-models-conversation-temp-0.6
```

## Analysis Focus

This experiment will provide insights into:
- How balanced environments affect ethical decision-making
- Baseline ethical behavior with conversation prompts
- Cross-provider ethical performance comparison
- Impact of model generation on ethical reasoning 