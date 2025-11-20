# 💼 FP&A CFO AI Dashboard

An AI-powered Financial Planning & Analysis dashboard featuring multiple specialized agents for data integration, financial analysis, scenario modeling, and executive reporting.

## 🌟 Features

- **🔗 Data Connector**: Integrates ERP, CRM, and BI data sources
- **📊 FP&A Analyst**: Performs variance analysis and financial forecasting
- **💰 Profit Twin**: Runs what-if simulations for pricing and cost scenarios
- **🎯 CFO Copilot**: Synthesizes insights into executive summaries

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- NVIDIA NGC API key ([Get one here](https://org.ngc.nvidia.com/setup))

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/yourusername/fpna-cfo-dashboard.git
   cd fpna-cfo-dashboard
```

2. **Create virtual environment**
```bash
   python -m venv .venv
```

3. **Activate virtual environment**
   - Windows PowerShell:
```powershell
     .\.venv\Scripts\Activate.ps1
```
   - Windows CMD:
```cmd
     .venv\Scripts\activate.bat
```
   - Linux/Mac:
```bash
     source .venv/bin/activate
```

4. **Install dependencies**
```bash
   pip install -r requirements.txt
```

5. **Configure environment**
```bash
   cp .env.example .env
```
   Edit `.env` and add your NVIDIA NGC API key:
```bash
   NVIDIA_NGC_API_KEY=your-actual-api-key-here
```

6. **Run the application**
```bash
   streamlit run app.py
```

7. **Open browser**
   Navigate to http://localhost:8501

## 🎯 Usage

### Select an Agent
Click one of the four agent buttons at the top:
- **Data Connector**: For data integration questions
- **FP&A Analyst**: For financial analysis and variance reports
- **Profit Twin**: For scenario modeling and what-if analysis
- **CFO Copilot**: For executive summaries and strategic insights

### Ask Questions
Type your query in the chat input. Examples:
- "Provide an executive summary of Q4 financial health"
- "Analyze revenue trends and identify key drivers"
- "Run a scenario with 10% price increase"
- "What are the top 3 risks we should address?"

### Download Reports
Each response includes a download button to save the analysis.

## 📋 Supported Models

The application has been tested with 100+ NVIDIA NGC models. Recommended models:

- **meta/llama-3.1-70b-instruct** (Default - Best balance)
- **meta/llama-3.3-70b-instruct** (Latest version)
- **deepseek-ai/deepseek-r1** (Advanced reasoning)
- **mistralai/mistral-7b-instruct-v0.3** (Fast & efficient)

To switch models, update `NVIDIA_MODEL` in `.env`.

## 🔧 Configuration

### Environment Variables

All configuration is done via `.env` file:
```bash
# Provider
LLM_PROVIDER=nvidia_ngc

# API Configuration
NVIDIA_NGC_API_KEY=your-key-here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.1-70b-instruct

# Model Parameters
NVIDIA_TEMPERATURE=0.7
NVIDIA_MAX_TOKENS=2048
```

### Agent Configuration

Edit `agno_config.py` to customize:
- Agent roles and backstories
- System prompts
- Default workflow tasks

## 🐳 Docker (Optional)
```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8501
```

## 📁 Project Structure
```
fpna-cfo-dashboard/
├── app.py                      # Main Streamlit application
├── agno_config.py              # Agent configurations
├── agno_runner.py              # Agent orchestration
├── llm_client.py               # LLM provider interface
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── outputs/                    # Generated reports
└── README.md                   # This file
```

## 🧪 Testing
```bash
# Test NVIDIA NGC configuration
python test_nvidia_config.py

# Test all available models
python test_all_models.py

# Quick model test
python quick_test_models.py
```

## 🛠️ Troubleshooting

### Issue: "NVIDIA_NGC_API_KEY must be set"
**Solution:** Make sure `.env` file exists and contains your API key.

### Issue: "403 Forbidden"
**Solution:** Accept terms of service for the model at https://build.nvidia.com

### Issue: Port already in use
**Solution:** Use a different port:
```bash
streamlit run app.py --server.port 8502
```

## 📊 Performance

- Supports 100+ NVIDIA NGC models
- Response time: 2-10 seconds (depending on model size)
- Context window: Up to 128K tokens (model-dependent)

## 🔒 Security

- ✅ API keys stored in `.env` (not committed to Git)
- ✅ `.env` file in `.gitignore`
- ✅ Use `.env.example` for sharing configuration templates
- ⚠️ Never commit `.env` file to version control

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [NVIDIA NGC](https://www.nvidia.com/en-us/gpu-cloud/)
- Uses [OpenAI SDK](https://github.com/openai/openai-python) for API interface

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Email: your.email@example.com

---

**Made with ❤️ for Finance Teams**