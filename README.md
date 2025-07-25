# 🚀 PI Planning Dashboard

A comprehensive Streamlit-based dashboard for Program Increment (PI) Planning that integrates with JIRA and uses AI agents for intelligent automation. This tool streamlines the entire PI planning process from goal validation to dependency analysis.

## ⚡ Quick Setup (3 Commands)

```bash
# 1. Setup Python environment
git clone <repository-url> && cd pi_planning_dashboard
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# 2. Start MCP JIRA Server (replace with your credentials)
docker pull ghcr.io/sooperset/mcp-atlassian:latest
docker run --rm -p 3000:3000 \
  -e JIRA_URL=https://yourcompany.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-jira-api-token \
  ghcr.io/sooperset/mcp-atlassian:latest \
  --transport streamable-http --port 3000

# 3. Run the dashboard
cp .env.example .env  # Edit with your config
streamlit run app/main.py
```

**🎯 Result**: Dashboard running at `http://localhost:8501` with real JIRA integration!

## 🌟 Features

### 📋 Core Functionality
- **JIRA Integration**: Clean and manage JIRA project data
- **Document Processing**: Upload and analyze PI goals from Word/PDF documents
- **AI-Powered Validation**: SMART goals analysis using CrewAI agents
- **Excel Generation**: Automated creation of Epics and Features spreadsheets
- **Story Analysis**: Intelligent backlog analysis for quality improvement
- **Dependency Mapping**: Automated team dependency identification

### 🤖 AI Agents (CrewAI)
- **Goal Validator Agent**: Validates goals against SMART criteria
- **Epic Generator Agent**: Creates Epics and Features from goals
- **Story Analyzer Agent**: Analyzes story quality and completeness
- **Dependency Agent**: Identifies cross-team dependencies

### 🔌 MCP Server Integration
- **Team MCP**: Team ownership rules and keywords
- **JIRA MCP**: Project settings and custom fields
- **Goal MCP**: SMART goal templates and examples

## 🏗️ Project Structure

```
pi_planning_dashboard/
├── app/
│   ├── main.py                 # Main Streamlit application
│   ├── pages/                  # Multi-page application
│   │   ├── 1_🗑️_Wipe_JIRA.py
│   │   ├── 2_📄_Upload_Goals.py
│   │   ├── 3_⚡_Generate_Epics.py
│   │   ├── 4_📊_Review_Push.py
│   │   ├── 5_🔍_Analyze_Backlog.py
│   │   └── 6_🔗_Dependency_Check.py
│   ├── components/             # Reusable UI components
│   │   ├── sidebar.py
│   │   ├── file_uploader.py
│   │   └── mcp_client.py
│   ├── agents/                 # CrewAI agents
│   │   ├── goal_validator.py
│   │   ├── epic_generator.py
│   │   ├── story_analyzer.py
│   │   └── dependency_agent.py
│   └── utils/                  # Utility modules
│       ├── jira_api.py
│       ├── file_handlers.py
│       └── config.py
├── mcp_servers/                # MCP server implementations
│   ├── team_mcp.py
│   ├── jira_mcp.py
│   └── goal_mcp.py
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- JIRA account with API access (optional - demo mode available)
- OpenAI or Anthropic API key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pi_planning_dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   streamlit run app/main.py
   ```

6. **Access the dashboard**
   Open your browser to `http://localhost:8501`

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following:

#### Demo Mode (Recommended for first run)
```env
DEMO_MODE=True
```

#### JIRA Configuration
```env
JIRA_SERVER=https://your-company.atlassian.net
JIRA_USER=your-email@company.com
JIRA_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=PI
```

#### AI Configuration
```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key
DEFAULT_AI_PROVIDER=openai
```

#### JIRA MCP Server Integration (Required for Real JIRA Operations)

This project integrates with the **MCP Atlassian Docker Server** for real JIRA operations. The MCP server acts as a bridge between the dashboard and your JIRA instance.

**🐳 Docker MCP Server Setup (Recommended)**

1. **Prerequisites**
   ```bash
   # Ensure Docker is installed and running
   docker --version
   ```

2. **Pull the MCP Atlassian Docker Image**
   ```bash
   # This is the official MCP Atlassian server image
   docker pull ghcr.io/sooperset/mcp-atlassian:latest
   ```

3. **Get Your JIRA Credentials**
   - **JIRA URL**: Your Atlassian instance (e.g., `https://yourcompany.atlassian.net`)
   - **Username**: Your JIRA email address
   - **API Token**: Generate from [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)

4. **Start the MCP Atlassian Server**
   ```bash
   # Replace with your actual JIRA credentials
   docker run --rm -p 3000:3000 \
     -e JIRA_URL=https://yourcompany.atlassian.net \
     -e JIRA_USERNAME=your-email@company.com \
     -e JIRA_API_TOKEN=your-jira-api-token \
     ghcr.io/sooperset/mcp-atlassian:latest \
     --transport streamable-http --port 3000
   ```

4. **Verify MCP Server is Running**
   ```bash
   # Test the connection
   curl http://localhost:3000/mcp/
   
   # You should see MCP server information
   ```

5. **Configure Dashboard Environment**
   ```env
   # Add to your .env file
   MCP_SERVER_URL=http://localhost:3000/mcp/
   JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
   ```

**🔧 Alternative: Manual MCP Server Setup**

If you prefer to run the MCP server manually:

1. **Clone the MCP Atlassian Repository**
   ```bash
   git clone https://github.com/sooperset/mcp-atlassian.git
   cd mcp-atlassian
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your JIRA credentials
   ```

4. **Start the Server**
   ```bash
   npm start -- --transport streamable-http --port 3000
   ```

**🛠️ Available MCP Tools**

The MCP server provides 31+ JIRA tools including:
- `jira_create_issue`: Creates Epics, Stories, Tasks, and Bugs
- `jira_search`: Search issues using JQL
- `jira_get_project_issues`: Get all issues for a project
- `jira_get_issue`: Get detailed issue information
- `jira_get_transitions`: Get available status transitions
- `jira_get_agile_boards`: Get Agile/Scrum boards
- `jira_get_user_profile`: Get user information
- And many more...

**✅ Testing Your MCP Setup**

1. **Test MCP Connection**
   ```bash
   # From the dashboard directory
   python3 test_new_mcp_client.py
   ```

2. **Expected Output**
   ```
   🚀 Testing New MCP Client Implementation
   ✅ Successfully connected to MCP server!
   🔗 Server URL: http://localhost:3000/mcp/
   🛠️  Available tools: 31
   ✅ Successfully created JIRA issue!
   ```

**🚨 Troubleshooting MCP Setup**

**Connection Refused**
```bash
# Check if Docker container is running
docker ps

# Check if port 3000 is available
lsof -i :3000

# Restart the MCP server
docker stop <container-id>
# Then run the docker command again
```

**Authentication Errors**
```bash
# Verify your JIRA credentials
curl -u "your-email@company.com:your-api-token" \
  "https://yourcompany.atlassian.net/rest/api/2/myself"
```

**MCP Server Not Responding**
```bash
# Check Docker logs
docker logs <container-id>

# Try different port
docker run --rm -p 3001:3000 \
  -e JIRA_URL=... \
  ghcr.io/sooperset/mcp-atlassian:latest \
  --transport streamable-http --port 3000
```

**🎯 Benefits of MCP Integration**
- ✅ **Real-time JIRA Operations**: Create, update, and search JIRA issues instantly
- ✅ **Automatic Authentication**: Secure credential handling through Docker environment
- ✅ **Consistent API Responses**: Standardized MCP protocol for reliable integration
- ✅ **Error Handling**: Built-in retry logic and comprehensive error reporting
- ✅ **31+ JIRA Tools**: Complete JIRA API coverage through MCP tools
- ✅ **Session Management**: Persistent connections for better performance

### JIRA API Token Setup

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the token to your `.env` file

## 📖 Usage Guide

### Step 1: JIRA Cleanup 🗑️
- Connect to your JIRA instance
- Review current project state
- Clean up old data to prepare for new PI

### Step 2: Upload Goals 📄
- Upload PI goals document (Word, PDF, or text)
- AI agent validates goals against SMART criteria
- Review and edit improved goal suggestions

### Step 3: Generate Epics ⚡
- AI generates Epics and Features from validated goals
- Review and customize generated items
- Download Excel file for review

### Step 4: Review & Push 📊
- Upload reviewed Excel file
- Preview items before pushing to JIRA
- Bulk create Epics and Stories in JIRA

### Step 5: Analyze Backlog 🔍
- Analyze existing stories for quality issues
- Get AI recommendations for improvements
- Identify incomplete or poorly written stories

### Step 6: Dependency Check 🔗
- Automated dependency analysis
- Team ownership mapping
- Risk assessment and mitigation suggestions

## 🤖 AI Agents

### Goal Validator Agent
- **Purpose**: Validates PI goals against SMART criteria
- **Input**: Raw goal text from documents
- **Output**: Validated goals with improvement suggestions
- **Model**: GPT-4 (configurable)

### Epic Generator Agent
- **Purpose**: Creates Epics and Features from goals
- **Input**: Validated goals
- **Output**: Structured Epics with Features and acceptance criteria
- **Model**: GPT-4 (configurable)

### Story Analyzer Agent
- **Purpose**: Analyzes user story quality
- **Input**: Existing JIRA stories
- **Output**: Quality scores and improvement recommendations
- **Model**: GPT-3.5-turbo (configurable)

### Dependency Agent
- **Purpose**: Identifies cross-team dependencies
- **Input**: Project data and team ownership rules
- **Output**: Dependency map with risk assessment
- **Model**: GPT-3.5-turbo (configurable)

## 🔌 MCP Servers

### Team MCP Server
```python
# Example team ownership rules
{
    "frontend": ["ui", "react", "angular", "vue"],
    "backend": ["api", "database", "server"],
    "mobile": ["ios", "android", "react-native"],
    "devops": ["deployment", "infrastructure", "ci/cd"]
}
```

### JIRA MCP Server
```python
# Example JIRA configuration
{
    "issue_types": ["Epic", "Story", "Task", "Bug"],
    "custom_fields": {
        "story_points": "customfield_10016",
        "epic_link": "customfield_10014"
    }
}
```

### Goal MCP Server
```python
# Example SMART goal template
{
    "template": "As a [stakeholder], we want to [objective] so that [benefit], measured by [metrics] and completed by [deadline]"
}
```

## 🛠️ Development

### Adding New Pages
1. Create new file in `app/pages/`
2. Follow naming convention: `N_emoji_PageName.py`
3. Import and use shared components from `app/components/`

### Creating New Agents
1. Create agent class in `app/agents/`
2. Inherit from base agent patterns
3. Implement required methods: `execute()`, `validate_input()`, `format_output()`

### Adding MCP Servers
1. Create server implementation in `mcp_servers/`
2. Define tools and resources
3. Update configuration in `.env`

## 🧪 Testing

### Run Tests
```bash
pytest tests/
```

### Test Coverage
```bash
pytest --cov=app tests/
```

### Demo Mode Testing
Set `DEMO_MODE=True` in `.env` to test without real JIRA/AI APIs.

## 📦 Deployment

### Local Development
```bash
streamlit run app/main.py
```

### Docker Deployment
```bash
# Build image
docker build -t pi-planning-dashboard .

# Run container
docker run -p 8501:8501 --env-file .env pi-planning-dashboard
```

### Cloud Deployment
- **Streamlit Cloud**: Connect GitHub repository
- **Heroku**: Use provided `Procfile`
- **AWS/GCP**: Deploy as containerized application

## 🔒 Security Considerations

- Store API keys in environment variables
- Use HTTPS in production
- Implement proper authentication
- Validate all file uploads
- Sanitize user inputs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**JIRA Connection Failed**
- Verify JIRA URL, username, and API token
- Check network connectivity
- Ensure API token has proper permissions

**AI Agent Errors**
- Verify OpenAI/Anthropic API key
- Check API rate limits
- Ensure sufficient credits/quota

**File Upload Issues**
- Check file size limits (default 50MB)
- Verify supported file formats
- Ensure proper file permissions

### Getting Help

- 📧 Email: support@example.com
- 💬 Slack: #pi-planning-support
- 🐛 Issues: GitHub Issues page
- 📖 Documentation: Wiki pages

## 🗺️ Roadmap

### Version 1.1
- [ ] Real-time collaboration features
- [ ] Advanced NLP for better goal extraction
- [ ] Integration with Microsoft Teams
- [ ] Automated story point estimation

### Version 1.2
- [ ] Machine learning for dependency prediction
- [ ] Custom dashboard widgets
- [ ] API for external integrations
- [ ] Mobile-responsive design improvements

### Version 2.0
- [ ] Multi-tenant support
- [ ] Advanced analytics and reporting
- [ ] Integration with other project management tools
- [ ] Workflow automation engine

## 🙏 Acknowledgments

- **Streamlit** for the amazing web framework
- **CrewAI** for agent orchestration capabilities
- **OpenAI/Anthropic** for powerful language models
- **Atlassian** for JIRA API access
- **Community contributors** for feedback and improvements

---

**Happy PI Planning! 🚀**
