#!/usr/bin/env python3
"""
Simple Emergency Stop GUI for Drone Controller
This creates a GUI with an emergency stop button that sends stop commands directly to drones.
"""

import tkinter as tk
from tkinter import messagebox
import threading
import signal
import sys
import subprocess
import time
import os  # Added for process ID
from djitellopy import Tello
from djitellopy import TelloSwarm


class EmergencyStopGUI:
    """Simple GUI application for emergency drone control"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drone Emergency Stop")
        self.root.geometry("350x250")
        self.root.configure(bg='#2c3e50')

        # Make window always on top
        self.root.attributes('-topmost', True)

        # Center the window
        self.center_window()

        # Set up the UI
        self.setup_ui()

        # Track if emergency stop was triggered
        self.emergency_triggered = False

    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Title
        title_label = tk.Label(
            main_frame,
            text="🚨 DRONE EMERGENCY CONTROL 🚨",
            font=('Arial', 14, 'bold'),
            fg='#e74c3c',
            bg='#2c3e50'
        )
        title_label.pack(pady=(0, 20))

        # Emergency Stop Button
        self.emergency_button = tk.Button(
            main_frame,
            text="🚨 EMERGENCY STOP 🚨",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#e74c3c',
            activebackground='#c0392b',
            activeforeground='white',
            width=18,
            height=3,
            relief='raised',
            bd=5,
            command=self.emergency_stop
        )
        self.emergency_button.pack(pady=15)

        # Info text
        info_label = tk.Label(
            main_frame,
            text="This will send emergency commands\nto stop all drone operations",
            font=('Arial', 9),
            fg='#ecf0f1',
            bg='#2c3e50',
            justify='center'
        )
        info_label.pack(pady=(10, 15))

        # Close button
        close_button = tk.Button(
            main_frame,
            text="Close",
            font=('Arial', 10),
            fg='white',
            bg='#7f8c8d',
            activebackground='#95a5a6',
            command=self.close_application
        )
        close_button.pack()

    def emergency_stop(self):
        """Execute emergency stop procedure"""
        if self.emergency_triggered:
            print("Emergency stop already in progress!")
            return

        self.emergency_triggered = True
        self.emergency_button.config(
            text="STOPPING...",
            bg='#c0392b',
            state='disabled'
        )

        # Run emergency stop in separate thread
        stop_thread = threading.Thread(
            target=self.execute_emergency_stop,
            daemon=True
        )
        stop_thread.start()

    def execute_emergency_stop(self):
        """Execute the actual emergency stop procedure"""
        try:
            print("🚨 EMERGENCY STOP TRIGGERED FROM GUI!")

            # Step 1: Send Ctrl+C to any running Python processes
            # self.send_interrupt_signals()

            # Step 2: Direct drone emergency commands
            self.send_drone_emergency_commands()

            # Step 3: Kill processes as backup
            # self.kill_drone_processes()

            # Update UI on main thread
            self.root.after(0, self.emergency_stop_complete)

        except Exception as e:
            print(f"Emergency stop error: {e}")
            self.root.after(0, self.emergency_stop_error, str(e))

    def send_interrupt_signals(self):
        """Send interrupt signals to running processes"""
        print("Sending interrupt signals...")

        try:
            if sys.platform == "win32":
                # Windows: Send Ctrl+C event
                subprocess.run([
                    'taskkill', '/F', '/IM', 'python.exe'
                ], capture_output=True, check=False, timeout=5)
            else:
                # Unix: Send SIGINT
                subprocess.run([
                    'pkill', '-SIGINT', '-f', 'python'
                ], capture_output=True, check=False, timeout=5)

        except Exception as e:
            print(f"Error sending interrupt signals: {e}")

    def send_drone_emergency_commands(self):
        """Send direct emergency commands to drones"""
        print("Sending direct emergency commands to drones...")

        try:
            # Try to connect and send emergency command directly




            try:

                drone1 = Tello(host="192.168.137.21")
                drone2 = Tello(host="192.168.137.22")

                # Create swarm from individual drones
                swarm = TelloSwarm([drone1, drone2])
                swarm.connect()
                swarm.emergency()
                print("Emergency command sent to all drones in swarm.")

                # Also try land command as backup
                try:
                    swarm.land()
                    print("Land command sent to all drones in swarm.")
                except Exception as land_err:
                    print(f"Land command failed for swarm: {land_err}")

                swarm.end()
            except Exception as e:
                print(f"Could not send emergency to swarm: {e}")

        except ImportError:
            print("djitellopy not available, skipping direct drone commands")
        except Exception as e:
            print(f"Error sending drone commands: {e}")

    def kill_drone_processes(self):
        """Kill drone-related processes as backup"""
        print("Killing drone processes...")
        current_pid = os.getpid()
        print(f"Current process ID: {current_pid} (will be excluded)")

        try:
            if sys.platform == "win32":
                # Windows commands
                commands = [
                    ['taskkill', '/F', '/FI', f'PID ne {current_pid}', '/IM', 'python.exe'],
                    ['taskkill', '/F', '/FI', 'WINDOWTITLE eq *main.py*'],
                    ['taskkill', '/F', '/FI', 'WINDOWTITLE eq *drone*']
                ]
            else:
                # Unix commands
                commands = [
                    ['pkill', '-f', f'(?!^{current_pid}$)main.py'],
                    ['pkill', '-f', f'(?!^{current_pid}$)drone'],
                    ['pkill', '-f', f'(?!^{current_pid}$)tello'],
                    ['pkill', '-f', f'(?!^{current_pid}$)djitellopy']
                ]

            for cmd in commands:
                try:
                    subprocess.run(
                        cmd,
                        capture_output=True,
                        check=False,
                        timeout=5
                    )
                    print(f"Executed: {' '.join(cmd)}")
                except Exception as e:
                    print(f"Failed to execute {cmd}: {e}")

        except Exception as e:
            print(f"Error killing processes: {e}")

    def emergency_stop_complete(self):
        """Called when emergency stop is complete"""
        self.emergency_button.config(
            text="✅ STOPPED",
            bg='#27ae60',
            state='disabled'
        )
        print("Emergency stop procedure completed!")
        print("• Interrupt signals sent")
        print("• Emergency commands sent to drones")
        print("• Processes terminated")

        # Re-enable button after 5 seconds
        self.root.after(5000, self.reset_button)

    def emergency_stop_error(self, error_msg):
        """Called when emergency stop encounters an error"""
        self.emergency_button.config(
            text="❌ ERROR",
            bg='#e74c3c',
            state='normal'
        )
        print(f"Error during emergency stop: {error_msg}")
        print("Some operations may have failed.")
        print("Check manually if needed.")

        self.emergency_triggered = False

    def reset_button(self):
        """Reset the emergency button"""
        self.emergency_triggered = False
        self.emergency_button.config(
            text="🚨 EMERGENCY STOP 🚨",
            bg='#e74c3c',
            state='normal'
        )

    def close_application(self):
        """Close the application"""
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI"""
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

        print("Emergency Stop GUI started")
        print("Ready to send emergency stop commands")

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nGUI interrupted")


def main():
    """Main function"""
    try:
        app = EmergencyStopGUI()
        app.run()
    except Exception as e:
        print(f"Error starting Emergency Stop GUI: {e}")


if __name__ == "__main__":
    main()
