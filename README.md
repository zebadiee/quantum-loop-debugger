

# 🔬 Quantum Loop Debugger

A revolutionary self-healing code system that automatically detects failures, generates intelligent patches using AI, and applies fixes in real-time. This system demonstrates advanced automated debugging capabilities with a beautiful web dashboard for monitoring.

## 🌟 Features

- **🤖 AI-Powered Patch Generation**: Intelligent error analysis and automatic patch creation
- **🔄 Self-Healing Loop**: Continuous monitoring and automatic failure recovery
- **📊 Real-Time Dashboard**: Beautiful web interface for system monitoring
- **🎯 Multi-Error Support**: Handles 10+ different types of Python errors
- **⚡ Fast Recovery**: Typically fixes issues within seconds
- **🛡️ Safety Features**: Backup creation and rollback capabilities
- **📈 Metrics Tracking**: Comprehensive logging and performance metrics
- **🧠 AI Engineer Assistant**: Enhanced AI-powered development workflows with MCP integration
- **🔀 Git Integration**: Automated commits, PRs, and branch management
- **💰 Cost-Controlled LLM**: Safe RouteLLM wrapper with whitelisted models and cost limits

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Docker and Docker Compose (for containerized deployment)
- pip package manager
- Git (for version control features)

### Installation Options

#### Option 1: Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/zebadiee/quantum-loop-debugger.git
   cd quantum-loop-debugger
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Access the services**:
   - AI Engineer CLI: `docker exec -it quantum-ai-engineer python -m assistant.core`
   - Web Dashboard: http://localhost:5000
   - AI Engineer API: http://localhost:8080

#### Option 2: Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/zebadiee/quantum-loop-debugger.git
   cd quantum-loop-debugger
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   export ROUTELLM_API_KEY="your_routellm_api_key"
   export GITHUB_TOKEN="your_github_token"
   export WORKSPACE_PATH="$(pwd)"
   ```

4. **Start the dashboard** (optional but recommended):
   ```bash
   python tk_dashboard.py
   ```
   The dashboard will be available at `http://localhost:5000`

5. **Start the AI Engineer**:
   ```bash
   python -m assistant.core
   ```

6. **Run the self-healing system**:
   ```bash
   python tk_auto_retry.py
   ```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Engineer Service                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   RouteLLM      │  │ Git Integration │  │ MCP Client  │ │
│  │   Wrapper       │  │    Manager      │  │   Tools     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
        ┌───────────▼──┐  ┌─────▼─────┐  ┌─▼──────────┐
        │ Patch MCP    │  │Dashboard  │  │Auto-Retry  │
        │ Generator    │  │    MCP    │  │    MCP     │
        └──────────────┘  └───────────┘  └────────────┘
```

### Core Components

1. **AI Engineer Service** (`assistant/core.py`):
   - Main orchestrator for AI-powered development workflows
   - Handles fix/patch requests, status checks, test execution
   - Integrates with existing MCP services
   - Provides interactive CLI interface

2. **RouteLLM Wrapper** (`assistant/route_llm.py`):
   - Safe LLM access with cost controls and model whitelisting
   - Supports multiple models: GPT-4o, Claude-3, Gemini-1.5
   - Hourly and daily cost limits
   - Rate limiting and error handling

3. **Git Integration** (`assistant/git_integration.py`):
   - Automated Git operations (commits, pushes, PRs)
   - Branch management and repository status
   - GitHub API integration for pull requests
   - Configurable auto-commit and auto-PR features

4. **MCP Client Tools** (`assistant/tools/mcp_client.py`):
   - Communication with existing MCP services
   - Standardized JSON-RPC interface
   - Health checks and capability discovery

## 🎯 AI Engineer Usage

### Interactive CLI Commands

```bash
# Start the AI Engineer CLI
python -m assistant.core

# Available commands:
fix <error_description>     # Generate and apply patch
status                      # Check system status  
test [path]                # Run tests
git <operation>            # Git operations
query <question>           # Ask AI assistant
health                     # System health check
quit                       # Exit
```

### Example Workflows

#### 1. Fix a Bug Automatically
```bash
🤖 AI Engineer > fix ImportError: No module named 'requests'
✅ Success!
📝 Generated patch for: requirements.txt
```

#### 2. Check System Status
```bash
🤖 AI Engineer > status
✅ Success!
🏥 System Health: healthy
   patch-mcp: healthy
   dashboard-mcp: healthy
   auto-retry: healthy
```

#### 3. Run Tests
```bash
🤖 AI Engineer > test
✅ Success!
🧪 Tests passed: 15/15
```

#### 4. Git Operations
```bash
🤖 AI Engineer > git status
✅ Success!
🔀 Current branch: ai-engineer-feature
   Modified files: 2
   Untracked files: 1
```

## 🔧 Configuration

### Environment Variables

```bash
# RouteLLM Configuration
ROUTELLM_API_KEY=your_api_key_here
COST_LIMIT_PER_HOUR=10.0
COST_LIMIT_PER_DAY=50.0
DEFAULT_MODEL=gpt-4o-mini
FALLBACK_MODEL=claude-3-haiku

# Git Configuration  
GITHUB_TOKEN=your_github_token
AUTO_COMMIT=true
AUTO_PR=false

# MCP Configuration
MCP_TIMEOUT=30
MCP_RETRY_ATTEMPTS=3

# Workspace
WORKSPACE_PATH=/workspace
```

### Docker Compose Services

- **ai-engineer**: Main AI Engineer service (port 8080)
- **patch-mcp**: Patch generator MCP service (port 8081)
- **dashboard-mcp**: Dashboard MCP service (ports 5000, 8082)
- **auto-retry**: Auto-retry MCP service (port 8083)

## 🛡️ Safety Features

### Cost Controls
- Hourly and daily spending limits for LLM usage
- Whitelisted models only (no access to expensive models without explicit approval)
- Real-time cost tracking and budget enforcement

### Git Safety
- Automatic backups before applying patches
- Branch-based workflow (never commits directly to main)
- Pull request creation for code review
- Rollback capabilities

### Error Handling
- Comprehensive logging and error tracking
- Graceful degradation when services are unavailable
- Health checks for all components
- Timeout protection for long-running operations

## 📊 Monitoring and Logging

### Web Dashboard
Access the web dashboard at `http://localhost:5000` to monitor:
- System health and status
- Recent patch applications
- Error rates and recovery metrics
- Cost tracking and usage statistics

### Log Files
- AI Engineer logs: `/workspace/logs/ai_engineer.log`
- MCP service logs: Individual service containers
- Git operation logs: Included in AI Engineer logs

## 🔄 MCP Integration

The AI Engineer integrates with existing MCP services:

1. **Patch MCP** (`tk_patch_generator.py`):
   - Generates intelligent patches for code failures
   - Supports 10+ error types
   - AI-powered error analysis

2. **Dashboard MCP** (`tk_dashboard.py`):
   - Provides system monitoring and metrics
   - Web interface for status visualization
   - Real-time health checks

3. **Auto-Retry MCP** (`tk_auto_retry.py`):
   - Automatic failure detection and recovery
   - Configurable retry policies
   - Integration with patch generation

## 🚀 Advanced Features

### Custom Model Configuration
```python
# Add custom models to route_llm.py
WHITELISTED_MODELS = {
    'custom-model': {
        'input_cost': 0.001, 
        'output_cost': 0.002, 
        'max_tokens': 50000
    }
}
```

### Git Workflow Customization
```python
# Configure in git_integration.py
git_config = {
    'auto_commit': True,
    'auto_pr': False,
    'default_branch': 'main',
    'commit_message_template': 'AI-Fix: {error_type}'
}
```

### MCP Service Extensions
Add new MCP services by:
1. Creating a new service in `assistant/tools/`
2. Adding the service to `docker-compose.yml`
3. Registering it in `assistant/core.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/zebadiee/quantum-loop-debugger/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zebadiee/quantum-loop-debugger/discussions)
- **Documentation**: [Wiki](https://github.com/zebadiee/quantum-loop-debugger/wiki)

## 🎉 Acknowledgments

- Built with ❤️ for the developer community
- Powered by advanced AI and machine learning technologies
- Inspired by the need for intelligent, self-healing code systems

---

**🔬 Quantum Loop Debugger - Where AI meets intelligent code healing!**

