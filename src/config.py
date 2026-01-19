import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    
    
    # Choose which LLM provider to use
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # Options: "openai", "anthropic", "google"
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Anthropic Configuration (Alternative)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    
    # Google Configuration (Alternative)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-pro")
    
    # ==================== Platform API Configuration ====================
    PLATFORM_API_KEY = os.getenv("PLATFORM_API_KEY")
    
    # ==================== N8N Webhook Configuration ====================
    # Your N8N webhook URL for sending structured data
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
    
    # ==================== Search API Configuration ====================
    # For web research (choose one)
    SEARCH_API_PROVIDER = os.getenv("SEARCH_API_PROVIDER", "serper")  # Options: "serper", "serpapi", "google"
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")  # If using Serper
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")  # If using SerpAPI
    
    # ==================== LangSmith Configuration ====================
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "startup-research-agent")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    
    # ==================== Timeout Configuration ====================
    # How long to wait for API responses (in seconds)
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "60"))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))
    
    # ==================== Graph Execution Configuration ====================
    # Maximum retries for failed operations
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Batch size for concurrent operations
    CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "5"))
    
    # ==================== Research Configuration ====================
    # Number of search results to retrieve
    SEARCH_RESULTS_LIMIT = int(os.getenv("SEARCH_RESULTS_LIMIT", "10"))
    
    # Whether to cache research results
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    
    # ==================== Output Configuration ====================
    # Where to save results
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
    
    # Whether to save thesis as PDF
    SAVE_THESIS_PDF = os.getenv("SAVE_THESIS_PDF", "true").lower() == "true"
    
    # ==================== Logging Configuration ====================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE = os.getenv("LOG_FILE", "./logs/research_agent.log")
    
    # ==================== Database Configuration (Optional) ====================
    # If you want to store results in a database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # ==================== Validation ====================
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration is present
        Call this at startup to catch missing configs early
        """
        required_configs = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY if cls.LLM_PROVIDER == "openai" else None,
            "ANTHROPIC_API_KEY": cls.ANTHROPIC_API_KEY if cls.LLM_PROVIDER == "anthropic" else None,
            "N8N_WEBHOOK_URL": cls.N8N_WEBHOOK_URL,
        }
        
        missing = [key for key, value in required_configs.items() if value is None]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                f"Please check your .env file."
            )
        
        print("✅ Configuration validated successfully!")


# Create output directories if they don't exist
if not os.path.exists(Config.OUTPUT_DIR):
    os.makedirs(Config.OUTPUT_DIR)

if not os.path.exists(os.path.dirname(Config.LOG_FILE)):
    os.makedirs(os.path.dirname(Config.LOG_FILE))