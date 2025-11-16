"""Global configuration singleton for application settings."""


class Config:
    """Singleton configuration object to store global application settings."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            # Initialize default values
            cls._instance.input_dir = None
            cls._instance.src = None
            cls._instance.out_dir = None
            cls._instance.group_log = None
            cls._instance.mode = None
        return cls._instance
    
    def initialize(self, input_dir, src, out_dir, group_log, mode):
        """Initialize configuration with provided values."""
        self.input_dir = input_dir
        self.src = src
        self.out_dir = out_dir
        self.group_log = group_log
        self.mode = mode


# Global config instance
config = Config()
