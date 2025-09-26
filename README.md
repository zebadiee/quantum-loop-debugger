
# Quantum Loop Debugger

A self-healing AI development system with real-time monitoring, automated patch generation, and OpenRouter free model rotation.

## 🚀 Features

### Core System
- **Self-Healing Code**: Automatically detects failures and generates patches
- **Real-time Monitoring**: Live dashboard with system health metrics
- **Automated Testing**: Continuous test execution with failure detection
- **Git Integration**: Automated commits, pushes, and pull request creation
- **MCP Architecture**: Modular Component Protocol for service communication

### OpenRouter Free Models Integration
- **Automatic Model Rotation**: Seamlessly switches between free OpenRouter models when quotas are exhausted
- **Usage Tracking**: Monitors hourly and daily usage limits for each model
- **Real-time Dashboard**: Live monitoring of model status, usage, and rotation history
- **Intelligent Failover**: Automatically selects the best available model
- **Cost-Free Operation**: Uses only free-tier models from OpenRouter

## 🔄 OpenRouter Free Models

The system automatically rotates between these free models:

- **Meta Llama 3.2 3B/1B Instruct**: High-performance instruction-following models
- **Microsoft Phi-3 Mini/Medium**: Efficient models optimized for reasoning
- **Google Gemma 2 9B IT**: Instruction-tuned model with strong capabilities
- **Zephyr 7B Beta**: Fine-tuned for helpful, harmless, and honest responses
- **OpenChat 7B**: Optimized for conversational AI tasks
- **MythoMist 7B**: Creative writing and storytelling capabilities

Each model has:
- **200 requests/day limit**
- **20 requests/hour limit**
- **Automatic quota monitoring**
- **Seamless failover when limits reached**

## 📊 Dashboard Features

### System Overview
- Real-time system status and uptime
- Patches applied counter
- Current test execution status
- Recent failure tracking

### OpenRouter Monitoring
- **Current Active Model**: Shows which model is currently being used
- **Model Availability**: Real-time status of all free models
- **Usage Statistics**: Hourly and daily usage for each model
- **Rotation History**: Timeline of model switches with reasons
- **Manual Controls**: Force model rotation and refresh status

### Live Logs
- Real-time system logs with filtering
- Model rotation notifications
- Error tracking and debugging info

## 🛠️ Setup Instructions

### Prerequisites
- Docker and Docker Compose
- OpenRouter API key (free tier)
- GitHub token (optional, for Git operations)

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenRouter Configuration (Required)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# GitHub Integration (Optional)
GITHUB_TOKEN=your_github_token_here

# System Configuration (Optional)
AUTO_COMMIT=true
AUTO_PR=false
MCP_TIMEOUT=30
MCP_RETRY_ATTEMPTS=3
```

### Getting OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for a free account
3. Go to [API Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Copy the key to your `.env` file

**Note**: The free tier provides generous limits for all supported models without requiring payment information.

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/zebadiee/quantum-loop-debugger.git
   cd quantum-loop-debugger
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key
   ```

3. **Start the system**:
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard**:
   - Web Dashboard: http://localhost:5000
   - AI Engineer CLI: `docker exec -it quantum-ai-engineer python -m assistant.core`

### Manual Installation

If you prefer to run without Docker:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create logs directory**:
   ```bash
   mkdir -p logs
   ```

3. **Start services**:
   ```bash
   # Terminal 1: Dashboard
   python tk_dashboard.py

   # Terminal 2: AI Engineer
   python -m assistant.core

   # Terminal 3: Patch Generator
   python tk_patch_generator.py --mcp-mode --port 8081

   # Terminal 4: Auto Retry
   python tk_auto_retry.py --mcp-mode --port 8083
   ```

## 🎯 Usage

### AI Engineer CLI

The AI Engineer provides an interactive command-line interface:

```bash
🤖 AI Engineer > help

Available commands:
  fix <error_description>  - Generate and apply patch
  status                   - Check system status  
  test [path]             - Run tests
  git <operation>         - Git operations
  query <question>        - Ask AI assistant
  health                  - System health check
  openrouter              - OpenRouter status
  rotate                  - Force model rotation
  quit                    - Exit
```

### Example Commands

```bash
# Check OpenRouter status
🤖 AI Engineer > openrouter

# Force model rotation
🤖 AI Engineer > rotate

# Ask the AI a question
🤖 AI Engineer > query How can I optimize this Python function?

# Generate a patch for an error
🤖 AI Engineer > fix TypeError in line 42 of main.py

# Check system health
🤖 AI Engineer > health
```

### Dashboard Usage

1. **Monitor System**: View real-time system status and metrics
2. **Track Models**: See which OpenRouter model is currently active
3. **View Usage**: Monitor quota usage for each free model
4. **Force Rotation**: Manually switch to the next available model
5. **Check History**: Review model rotation timeline and reasons

## 🏗️ Architecture

### Service Components

- **AI Engineer**: Main orchestrator with OpenRouter integration
- **Dashboard MCP**: Web interface with model monitoring
- **Patch MCP**: Automated patch generation service
- **Auto-Retry MCP**: Failure detection and retry logic

### OpenRouter Integration

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Engineer   │───▶│ OpenRouter Free  │───▶│  Free Models    │
│                 │    │     Client       │    │                 │
└─────────────────┘    └──────────────────┘    │ • Llama 3.2     │
         │                       │              │ • Phi-3         │
         │                       │              │ • Gemma 2       │
         ▼                       ▼              │ • Zephyr        │
┌─────────────────┐    ┌──────────────────┐    │ • OpenChat      │
│    Dashboard    │    │  Usage Tracker   │    │ • MythoMist     │
│                 │    │                  │    └─────────────────┘
└─────────────────┘    └──────────────────┘
```

### Data Flow

1. **Request**: AI Engineer receives a query
2. **Model Selection**: OpenRouter client selects available model
3. **API Call**: Request sent to OpenRouter with current model
4. **Usage Tracking**: Request logged for quota monitoring
5. **Response**: Result returned to user
6. **Rotation**: If quota exceeded, automatically switch models

## 📈 Monitoring & Logging

### Usage Tracking

The system maintains detailed usage statistics in `/workspace/logs/openrouter_usage.json`:

```json
{
  "models": {
    "meta-llama/llama-3.2-3b-instruct:free": {
      "requests": ["2024-01-01T10:00:00", "2024-01-01T10:15:00"],
      "total_requests": 2,
      "last_used": "2024-01-01T10:15:00"
    }
  },
  "rotation_history": [
    {
      "timestamp": "2024-01-01T10:30:00",
      "from_model": "meta-llama/llama-3.2-3b-instruct:free",
      "to_model": "microsoft/phi-3-mini-128k-instruct:free",
      "reason": "quota_exhausted"
    }
  ]
}
```

### Log Files

- `logs/ai_engineer.log`: Main system logs
- `logs/openrouter_usage.json`: Model usage tracking
- Dashboard logs: Real-time in web interface

## 🔧 Configuration

### OpenRouter Settings

```python
# In assistant/core.py
config = {
    'openrouter': {
        'api_key': 'your_api_key',
        'app_name': 'Quantum-Loop-Debugger',
        'app_url': 'https://github.com/zebadiee/quantum-loop-debugger'
    }
}
```

### Model Limits

Each free model has built-in limits:
- **Daily Limit**: 200 requests per day
- **Hourly Limit**: 20 requests per hour
- **Context Length**: Varies by model (8K to 131K tokens)

## 🚨 Troubleshooting

### Common Issues

1. **No Available Models**
   - Check if OpenRouter API key is valid
   - Wait for quota reset (hourly/daily)
   - Verify internet connection

2. **Model Rotation Not Working**
   - Check logs for rotation errors
   - Verify usage tracking file permissions
   - Restart the AI Engineer service

3. **Dashboard Not Updating**
   - Check if AI Engineer service is running
   - Verify network connectivity between services
   - Check Docker container logs

### Debug Commands

```bash
# Check service logs
docker logs quantum-ai-engineer
docker logs quantum-dashboard-mcp

# Check OpenRouter status
curl -X POST http://localhost:8080/api/request \
  -H "Content-Type: application/json" \
  -d '{"type": "openrouter_status"}'

# Force model rotation
curl -X POST http://localhost:5000/api/force-rotation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenRouter**: For providing free access to multiple AI models
- **Meta, Microsoft, Google**: For open-sourcing powerful language models
- **Docker**: For containerization support
- **Flask**: For the web dashboard framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/zebadiee/quantum-loop-debugger/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zebadiee/quantum-loop-debugger/discussions)
- **Documentation**: This README and inline code comments

---

**🚀 Ready to experience self-healing AI development with free model rotation? Get started now!**
