"""
Environment variable manager
Responsible for reading and updating .env document
"""
import os
from typing import Dict, List, Optional
from pathlib import Path


class EnvManager:
    """Environment variable manager"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self._ensure_env_file_exists()

    def _ensure_env_file_exists(self):
        """make sure .env File exists"""
        if not self.env_file.exists():
            self.env_file.touch()

    def read_env(self) -> Dict[str, str]:
        """Read all environment variables"""
        env_vars = {}
        if not self.env_file.exists():
            return env_vars

        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse key-value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        return env_vars

    def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取单个环境变量的值"""
        env_vars = self.read_env()
        return env_vars.get(key, default)

    def update_values(self, updates: Dict[str, str]) -> bool:
        """Update environment variables in batches"""
        try:
            # Read existing configuration
            existing_vars = self.read_env()

            # update value
            existing_vars.update(updates)

            # write back file
            return self._write_env(existing_vars)
        except Exception as e:
            print(f"Failed to update environment variables: {e}")
            return False

    def set_value(self, key: str, value: str) -> bool:
        """Set a single environment variable"""
        return self.update_values({key: value})

    def delete_keys(self, keys: List[str]) -> bool:
        """Delete the specified environment variable"""
        try:
            existing_vars = self.read_env()
            for key in keys:
                existing_vars.pop(key, None)
            return self._write_env(existing_vars)
        except Exception as e:
            print(f"Failed to delete environment variables: {e}")
            return False

    def _write_env(self, env_vars: Dict[str, str]) -> bool:
        """Write environment variables to file"""
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            print(f"write .env File failed: {e}")
            return False


# global instance
env_manager = EnvManager()
