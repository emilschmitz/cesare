# Lambda-Only Models Conversation Ethical Analysis - Temperature 0

This experiment evaluates Lambda Labs models using conversation-style prompts with deterministic environment responses (temperature 0).

## Experiment Overview

**Focus**: Ethical behavior analysis of Lambda Labs models  
**Prompt Style**: Conversation-based interactions  
**Environment Temperature**: 0 (deterministic responses)  
**Agent Models**: 7 Lambda Labs models  
**Steps per simulation**: 20  
**Repetitions per model**: 5  
**Total simulations**: 35 (7 models × 5 repetitions)

## Model Selection

### Lambda Labs Models (7 models)
- Llama 4 Maverick 17B (`llama-4-maverick-17b-128e-instruct-fp8`) - Latest flagship
- Llama 4 Scout 17B (`llama-4-scout-17b-16e-instruct`) - Latest high-performance
- Llama 3.3 70B (`llama3.3-70b-instruct-fp8`) - Current generation
- Llama 3.1 405B (`llama3.1-405b-instruct-fp8`) - Large scale model
- Llama 3.1 70B (`llama3.1-70b-instruct-fp8`) - Previous generation
- DeepSeek R1 671B (`deepseek-r1-671b`) - Reasoning-focused model
- Hermes 3 405B (`hermes3-405b`) - Instruction-tuned model

## Environment & Evaluator

- **Environment Model**: Llama 4 Maverick (latest Llama 4)
- **Evaluator Model**: Llama 4 Maverick (latest Llama 4)

## Running the Experiment

```bash
python -m cesare.main_experiment run config/exp6-lambda-only-conversation-temp-0
```

## Analysis Focus

This experiment will provide insights into:
- How deterministic environments affect ethical decision-making
- Baseline ethical behavior with conversation prompts
- Cross-provider ethical performance comparison
- Impact of model generation on ethical reasoning 