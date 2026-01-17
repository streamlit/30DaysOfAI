# 30 Days Of AI with Streamlit 🎈     

Welcome to **#30DaysOfAI** — a comprehensive 30-day challenge to learn, build, and deploy AI-powered applications using [Streamlit](https://streamlit.io) and [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview).

## 🎯 What You'll Build

Master AI app development from chatbots to production-ready RAG systems and intelligent agents.

## 📏 Challenge Rules

1. **Access the daily challenge**
   - 💻 Code: [github.com/streamlit/30daysofai](https://github.com/streamlit/30daysofai)
   - 🕹️ Instructions: [30daysofai.streamlit.app](https://30daysofai.streamlit.app)

2. **Build the app** following daily instructions

3. **Share your progress** on social media with **#30DaysOfAI**

4. **Complete all 30 days** and DM [Chanin Nantasenamat](https://www.linkedin.com/in/chanin-nantasenamat/) or [Jessica Smith](https://www.linkedin.com/in/jessica-s-095a861b3/)

5. **Get recognized** in the Hall of Fame 🏆 (+ possible swags and stickers!)

## 🚀 Getting Started

### Prerequisites

- Python 3.11, 3.12
- [Snowflake free trial](https://signup.snowflake.com/?trial=student&cloud=aws&region=us-west-2&utm_source=streamlit-campaign&utm_campaign=30daysofai) (120 days of credits)
- Basic Python knowledge
- Enthusiasm for AI! 🧠

### Locally

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # or with uv:
   uv pip install -e .
   ```

   `requirements.txt`:
   ```
   streamlit==1.52.0
   snowflake-ml-python==1.20.0
   snowflake-snowpark-python==1.44.0
   ```

3. **Configure Snowflake secrets**
   
   Create `.streamlit/secrets.toml` in your project root:
   ```toml
   [connections.snowflake]
   account = "your_account_identifier"
   user = "your_username"
   password = "your_password"
   role = "ACCOUNTADMIN"
   warehouse = "COMPUTE_WH"
   database = "your_database"
   schema = "your_schema"
   ```
   
   **Important:** Add `.streamlit/secrets.toml` to `.gitignore` — never commit secrets!

4. **Run the app**
   ```bash
   cd app
   streamlit run day1.py
   ```

### In Snowflake

**Recommended for production** — no secrets setup needed!

1. Navigate to Snowsight → Streamlit
2. Create new Streamlit app
3. Copy code from `app/dayX.py`
4. Run in Snowflake

**Benefits:**
- ✅ Automatic authentication
- ✅ Production-ready by default
- ✅ Inherits Snowflake security

## 📁 Repository Structure

```
30days-genai-master/
├── app/               # Streamlit applications (day1.py - day30.py)
├── md/                # Detailed lesson documentation (day1.md - day30.md)
├── toml/              # Configuration files for specific lessons
├── pyproject.toml     # Python dependencies
└── README.md          # This file
```

Each day includes:
- **📱 App file** (`app/dayX.py`) - Complete, runnable code
- **📖 Documentation** (`md/dayX.md`) - Step-by-step explanations
- **💡 Key concepts** - What you'll learn and why it matters


## 🛠️ Technologies

- **[Streamlit](https://streamlit.io)** - Fast, beautiful web apps for ML and data science
- **[Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)** - LLM functions and AI services
- **[Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)** - Semantic search service
- **[Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)** - Natural language to SQL
- **[Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)** - Autonomous AI agents
- **[TruLens](https://www.trulens.org/)** - LLM evaluation and observability

## 📚 Resources

### Official Documentation
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Cheat Sheet](https://docs.streamlit.io/library/cheatsheet)
- [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Cortex Agents Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [TruLens Documentation](https://www.trulens.org/trulens_eval/getting_started/)

### Community
- [Streamlit Gallery](https://streamlit.io/gallery) - Inspiration and templates
- [Streamlit Community Forum](https://discuss.streamlit.io/) - Ask questions
- [Snowflake Community](https://community.snowflake.com/) - Connect with others

## 🤝 Contributing

Found an issue? Contributions are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Submit a pull request

---

# Ready to start?

1. 🔧 **[Set up your connection](md/day1.md)** - Configure Snowflake
2. 🚀 **[Begin Day 1](app/day1.py)** - Build your first app
3. 🎉 **Share your progress** on social with **#30DaysOfAI**

**Have questions?** Open an issue or join the [Streamlit Community Forum](https://discuss.streamlit.io/).
