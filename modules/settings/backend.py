"""
Backend logic for application settings
"""
import json
import os


class SettingsManager:
    def _init_(self, config_file='config.json'):
        self.config_file = config_file
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default settings
        return {
            'update_interval': 1,
            'start_with_system': False,
            'minimize_to_tray': False,
            'theme': 'light'
        }
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True, "Settings saved successfully"
        except Exception as e:
            return False, f"Failed to save settings: {e}"
    
    def get_setting(self, key, default=None):
        """Get a specific setting"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """Set a specific setting"""
        self.settings[key] = value
    
    def update_settings(self, new_settings):
        """Update multiple settings at once"""
        self.settings.update(new_settings)
        return self.save_settings()
