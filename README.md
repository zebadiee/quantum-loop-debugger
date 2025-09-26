
# 🚀 Quantum Loop Debugger - AI Engineer System

A self-healing AI development system with OpenRouter free model rotation, automated patch generation, and comprehensive monitoring.

## 🌟 Features

### 🤖 AI Engineer Core
- **OpenRouter Free Models Integration**: Automatic rotation between 8 free models
- **Smart Failover**: Intelligent quota management and model switching
- **Docker Service Integration**: Containerized microservices architecture
- **CLI Interface**: Interactive command-line interface for development
- **MCP Services Integration**: Patch generation, dashboard, and auto-retry services

### 🔄 OpenRouter Free Models
- **Meta Llama 3.2 3B & 1B Instruct**: High-performance instruction following
- **Microsoft Phi-3 Mini & Medium**: Efficient reasoning models
- **Google Gemma 2 9B IT**: Advanced instruction tuning
- **HuggingFace Zephyr 7B Beta**: Conversational AI capabilities
- **OpenChat 7B**: Optimized chat performance
- **Gryphe MythoMist 7B**: Creative and narrative tasks

### 🛡️ Zero-Cost Guarantee
- **Strict Model Whitelisting**: Only free models are used
- **Usage Tracking**: Persistent monitoring in `usage.json`
- **Quota Management**: Automatic rotation when limits reached
- **Cost Protection**: No paid model fallbacks

### 📊 Observability
- **Real-time Dashboard**: Web-based monitoring interface
- **Usage Analytics**: Detailed model usage statistics
- **Rotation History**: Track model switches and reasons
- **Health Monitoring**: System and service health checks

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenRouter API key (free tier)
- Git repository access

### Environment Setup

1. **Clone the repository**:
```bash
git clone https://github.com/zebadiee/quantum-loop-debugger.git
cd quantum-loop-debugger
```

2. **Set environment variables**:
```bash
# Create .env file
cat > .env << EOF
OPENROUTER_API_KEY=your_openrouter_api_key_here
GITHUB_TOKEN=your_github_token_here
WORKSPACE_PATH=/workspace
EOF
```

3. **Launch the system**:
```bash
docker-compose up -d
```

### 🎯 Access Points

- **AI Engineer CLI**: `docker exec -it quantum-ai-engineer python -m assistant.core`
- **Web Dashboard**: http://localhost:5000
- **API Endpoints**: http://localhost:8080

## 💻 Usage Examples

### CLI Commands

```bash
# Check system status
🤖 AI Engineer > status

# Generate and apply patch
🤖 AI Engineer > fix "ImportError: No module named 'requests'"

# Run tests
🤖 AI Engineer > test

# Query AI assistant
🤖 AI Engineer > query "How do I optimize this code?"

# Check OpenRouter status
🤖 AI Engineer > openrouter

# Force model rotation
🤖 AI Engineer > rotate

# Git operations
🤖 AI Engineer > git status
```

### API Usage

```python
import requests

# Get system status
response = requests.post('http://localhost:8080/api/request', json={
    'type': 'status_check'
})

# Generate patch
response = requests.post('http://localhost:8080/api/request', json={
    'type': 'fix_patch',
    'failure_context': {
        'error': 'ImportError: No module named requests',
        'file': 'main.py'
    },
    'auto_apply': True
})

# Query OpenRouter models
response = requests.post('http://localhost:8080/api/request', json={
    'type': 'llm_query',
    'query': 'Explain this error and suggest a fix'
})
```

## 🏗️ Architecture

### Services Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Engineer   │    │  Patch Generator │    │    Dashboard    │
│   (Port 8080)   │◄──►│   (Port 8081)   │    │   (Port 5000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Auto-Retry    │
                    │   (Port 8083)   │
                    └─────────────────┘
```

### OpenRouter Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenRouter Free Models                   │
├─────────────────────────────────────────────────────────────┤
│ • Meta Llama 3.2 3B/1B Instruct (200 req/day, 20 req/hr)  │
│ • Microsoft Phi-3 Mini/Medium (200 req/day, 20 req/hr)    │
│ • Google Gemma 2 9B IT (200 req/day, 20 req/hr)           │
│ • HuggingFace Zephyr 7B (200 req/day, 20 req/hr)          │
│ • OpenChat 7B (200 req/day, 20 req/hr)                    │
│ • Gryphe MythoMist 7B (200 req/day, 20 req/hr)            │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │ Smart Rotation  │
                    │ & Quota Mgmt    │
                    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `GITHUB_TOKEN` | GitHub access token | Optional |
| `WORKSPACE_PATH` | Working directory | `/workspace` |
| `AUTO_COMMIT` | Auto-commit patches | `true` |
| `AUTO_PR` | Auto-create PRs | `false` |
| `MCP_TIMEOUT` | MCP request timeout | `30` |
| `MCP_RETRY_ATTEMPTS` | MCP retry attempts | `3` |

### Configuration File

Create `config/ai_engineer.json`:

```json
{
  "openrouter": {
    "api_key": "your_key_here",
    "app_name": "Quantum-Loop-Debugger",
    "app_url": "https://github.com/zebadiee/quantum-loop-debugger"
  },
  "git": {
    "auto_commit": true,
    "auto_pr": false
  },
  "mcp": {
    "timeout": 30,
    "retry_attempts": 3
  }
}
```

## 📊 Monitoring & Observability

### Dashboard Features
- **Real-time Status**: System health and active operations
- **Model Usage**: Current model, availability, and usage statistics
- **Rotation History**: Track model switches with timestamps
- **System Logs**: Comprehensive logging with filtering
- **Health Checks**: Service availability monitoring

### Usage Tracking
The system maintains detailed usage statistics in `/workspace/logs/openrouter_usage.json`:

```json
{
  "models": {
    "meta-llama/llama-3.2-3b-instruct:free": {
      "requests": ["2024-01-01T10:00:00Z", "..."],
      "total_requests": 45,
      "last_used": "2024-01-01T15:30:00Z"
    }
  },
  "rotation_history": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "from_model": "meta-llama/llama-3.2-3b-instruct:free",
      "to_model": "microsoft/phi-3-mini-128k-instruct:free",
      "reason": "quota_rotation"
    }
  ]
}
```

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run individual services
python assistant/core.py --mode cli
python tk_dashboard.py --port 5000
python tk_patch_generator.py
python tk_auto_retry.py
```

### Testing

```bash
# Run the test script
python test_script.py

# Test with AI Engineer
🤖 AI Engineer > test test_script.py
```

### Adding New Models

To add new free OpenRouter models, update `assistant/openrouter_client.py`:

```python
FREE_MODELS = {
    'new-model-id:free': {
        'name': 'New Model Name',
        'context_length': 8192,
        'daily_limit': 200,
        'hourly_limit': 20,
        'provider': 'Provider Name',
        'capabilities': ['chat', 'instruct']
    }
}
```

## 🔒 Security & Best Practices

### API Key Management
- Store API keys in environment variables
- Use Docker secrets for production
- Never commit keys to version control

### Model Safety
- Only whitelisted free models are used
- No automatic fallback to paid models
- Usage limits are strictly enforced

### Git Integration
- Automatic commit messages include context
- PR creation requires explicit approval
- Branch protection recommended

## 🚨 Troubleshooting

### Common Issues

**OpenRouter API Key Issues**:
```bash
# Check if key is set
echo $OPENROUTER_API_KEY

# Test API access
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models
```

**Service Connection Issues**:
```bash
# Check service health
docker-compose ps
docker-compose logs ai-engineer
```

**Model Quota Exhausted**:
- Check dashboard for model availability
- Wait for quota reset (hourly/daily)
- Force model rotation if needed

### Logs and Debugging

```bash
# View service logs
docker-compose logs -f ai-engineer
docker-compose logs -f dashboard-mcp

# Access container for debugging
docker exec -it quantum-ai-engineer bash

# Check usage statistics
cat /workspace/logs/openrouter_usage.json
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines
- Follow Python PEP 8 style guide
- Add docstrings to all functions
- Update README for new features
- Test with multiple OpenRouter models

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenRouter for providing free model access
- Meta, Microsoft, Google, and other model providers
- Docker and containerization ecosystem
- Open source AI/ML community

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: This README and inline comments

---

**🚀 Ready to revolutionize your development workflow with AI-powered self-healing code!**
