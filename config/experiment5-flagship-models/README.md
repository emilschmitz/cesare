# Flagship Models Ethical Analysis Experiment

This experiment evaluates the ethical behavior of flagship and previous generation models from major AI providers (Anthropic, OpenAI, Meta) along with additional models from Lambda Labs.

## Experiment Overview

- **Name**: Flagship Models Ethical Analysis
- **Steps per simulation**: 20
- **Repetitions**: 5 (for statistical significance)
- **Total simulations**: 17 agents × 5 repetitions = 85 simulations

## Model Selection Strategy

### Anthropic Models
- **Claude 4 Opus** (`claude-opus-4-20250514`) - Latest flagship model
- **Claude 4 Sonnet** (`claude-sonnet-4-20250514`) - Latest high-performance model  
- **Claude 3.7 Sonnet** (`claude-3-7-sonnet-20250219`) - Previous generation with extended thinking
- **Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`) - Previous generation flagship

### OpenAI Models
- **GPT-4.1** (`gpt-4.1`) - Current flagship model (released April 2025)
- **o3-mini** (`o3-mini`) - Current reasoning model (released January 2025)
- **GPT-4o** (`gpt-4o`) - Previous flagship multimodal model
- **GPT-4 Turbo** (`gpt-4-turbo`) - Previous flagship model
- **GPT-3.5 Turbo** (`gpt-3.5-turbo`) - Previous generation baseline

### Meta Llama Models (via Lambda Labs)
- **Llama 4 Maverick** (`llama-4-maverick-17b-128e-instruct-fp8`) - **Latest Llama 4 with 128 experts** (newest big model)
- **Llama 4 Scout** (`llama-4-scout-17b-16e-instruct`) - Latest Llama 4 with 16 experts
- **Llama 3.3 70B** (`llama3.3-70b-instruct-fp8`) - Previous generation 70B model
- **Llama 3.1 405B** (`llama3.1-405b-instruct-fp8`) - Previous generation largest model
- **Llama 3.1 70B** (`llama3.1-70b-instruct-fp8`) - Previous generation 70B model

### Additional Lambda Models
- **DeepSeek R1** (`deepseek-r1-671b`) - Advanced reasoning model
- **Hermes 3 405B** (`hermes3-405b`) - High-performance instruction-following model

## Temperature Configuration

### Agent Models
- **Temperature**: Uses model defaults (no temperature override)
- **Rationale**: Let each model use its optimal default temperature for ethical decision-making

### Environment Model
- **Model**: Llama 3.1 405B (largest available for complex scenarios)
- **Temperature**: 1.2 (higher creativity for varied ethical dilemmas)
- **Reference**: Lambda Labs API supports temperature range 0.0-2.0
- **Documentation**: https://docs.lambda.ai/public-cloud/lambda-inference-api/

### Evaluator Model
- **Model**: Llama 3.1 405B (consistency with environment)
- **Temperature**: 0.3 (lower for consistent evaluation criteria)

## Provider Configuration

The experiment uses the actual API providers:
- **Anthropic**: For Claude models (requires `ANTHROPIC_API_KEY`)
- **OpenAI**: For GPT models (requires `OPENAI_API_KEY`)  
- **Lambda Labs**: For Llama and other models (requires `LAMBDA_API_KEY`)

## Expected Outcomes

This experiment will provide insights into:

1. **Cross-provider ethical behavior comparison**
2. **Flagship vs. previous generation model performance**
3. **Impact of model size and architecture on ethical decisions**
4. **Consistency across repetitions for each model**
5. **Temperature effects on ethical reasoning**
6. **Reasoning model performance (o3-mini) vs. standard models**

## Analysis Focus

The ethical analysis will examine:
- Violation rates across different ethical categories
- Utility changes and their distribution
- Model consistency across repetitions
- Provider-specific patterns in ethical behavior
- Correlation between model capabilities and ethical performance
- Performance differences between reasoning models and standard models

## Running the Experiment

```bash
# Ensure all API keys are set in .env file
python cesare/main_experiment.py config/experiment5-flagship-models/simulation.yaml
```

## Notes

- This experiment requires API access to all three providers
- Total estimated cost will depend on token usage across 85 simulations
- Results will be available in the web interface for comprehensive analysis
- The experiment includes duplicate prevention to avoid accidental re-runs
- Updated with current model names as of May 2025 (GPT-4.1, o3-mini, Claude 4 series) 