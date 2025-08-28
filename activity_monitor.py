#!/usr/bin/env python3
"""
Activity Monitor for automatic display power management.
Monitors user activity and controls HDMI display power via vcgencmd.
"""

import subprocess
from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtGui import QTouchEvent


class DisplayPowerManager:
    """Manages HDMI display power using vcgencmd."""

    def __init__(self):
        self.display_on = True

    def turn_display_on(self):
        """Turn HDMI display on."""
        try:
            result = subprocess.run(
                ["vcgencmd", "display_power", "1"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.display_on = True
                print("Display turned ON")
                return True
            else:
                print(f"Failed to turn display ON: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error turning display ON: {e}")
            return False

    def turn_display_off(self):
        """Turn HDMI display off."""
        try:
            result = subprocess.run(
                ["vcgencmd", "display_power", "0"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.display_on = False
                print("Display turned OFF")
                return True
            else:
                print(f"Failed to turn display OFF: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error turning display OFF: {e}")
            return False

    def is_display_on(self):
        return self.display_on


class ActivityMonitor(QObject):
    """Monitor user activity and manage display power automatically."""

    def __init__(self, timeout_ms=300000):
        super().__init__()
        self.timeout_ms = timeout_ms

        self.display_manager = DisplayPowerManager()

        self.inactivity_timer = QTimer()
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.on_inactivity_timeout)

        self.reset_inactivity_timer()

    def eventFilter(self, obj, event):
        if (
            event.type() == QTouchEvent.TouchBegin
            or event.type() == QTouchEvent.TouchUpdate
        ):
            if not self.display_manager.is_display_on():
                print("Activity detected - display is off. Turning it on...")
                self.display_manager.turn_display_on()
                return True

            self.reset_inactivity_timer()

        return super().eventFilter(obj, event)

    def on_inactivity_timeout(self):
        if self.display_manager.is_display_on():
            print(f"Inactivity timeout ({self.timeout_ms}ms) - turning display OFF")
            self.display_manager.turn_display_off()

    def reset_inactivity_timer(self):
        self.inactivity_timer.stop()
        self.inactivity_timer.start(self.timeout_ms)

    def cleanup(self):
        self.inactivity_timer.stop()
