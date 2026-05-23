import tkinter as tk
from tkinter import messagebox
import os
from datetime import datetime
from waze import fetch
from db import save_alerts, save_jams

SETTINGS_FILE = "settings.txt"


class WazeCollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Urban Traffic Data Collector")
        self.root.geometry("450x450")
        self.root.resizable(False, False)

        self.frame = tk.Frame(root, padx=20, pady=20)
        self.frame.pack(fill="both", expand=True)

        self.show_home()
   
    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def settings_exist(self):
        if not os.path.exists(SETTINGS_FILE):
            return False

        try:
            with open(SETTINGS_FILE, "r") as file:
                settings = file.read().splitlines()

            # Must contain exactly 5 settings
            if len(settings) != 5:
                return False

            top, bottom, left, right, time_value = settings

            # Check empty values
            if not all([
                top.strip(),
                bottom.strip(),
                left.strip(),
                right.strip(),
                time_value.strip()
            ]):
                return False

            # Convert to numbers and check != 0
            values = [
                float(top),
                float(bottom),
                float(left),
                float(right),
                float(time_value)
            ]

            if any(v == 0 for v in values):
                return False

            return True

        except Exception:
            return False

    def load_settings(self):
        if self.settings_exist():
            with open(SETTINGS_FILE, "r") as file:
                return file.read().splitlines()
        return []

    def save_settings(self):
        top = self.top_entry.get()
        bottom = self.bottom_entry.get()
        left = self.left_entry.get()
        right = self.right_entry.get()
        time_value = self.time_entry.get()

        if not all([top, bottom, left, right, time_value]):
            messagebox.showerror(
                "Error",
                "Please fill all fields!"
            )
            return

        with open(SETTINGS_FILE, "w") as file:
            file.write(f"{top}\n")
            file.write(f"{bottom}\n")
            file.write(f"{left}\n")
            file.write(f"{right}\n")
            file.write(f"{time_value}\n")

        messagebox.showinfo(
            "Success",
            "Settings saved successfully!"
        )

        self.show_home()

    def start_collecting(self):
        # Check if settings exist
        if not self.settings_exist():
            messagebox.showwarning(
                "Settings Required",
                "Add settings before starting!"
            )
            return

        # Open collecting interface
        self.show_collection_interface()

    def create_input(self, label, default=""):
        tk.Label(
            self.frame,
            text=label,
            font=("Arial", 10)
        ).pack(anchor="w", pady=(8, 0))

        entry = tk.Entry(self.frame, font=("Arial", 11))
        entry.insert(0, default)
        entry.pack(fill="x", pady=5)

        return entry

    def show_settings(self):
        self.clear_frame()

        settings = self.load_settings()

        tk.Label(
            self.frame,
            text="Settings",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        self.top_entry = self.create_input(
            "Top Coordinate",
            settings[0] if len(settings) > 0 else ""
        )

        self.bottom_entry = self.create_input(
            "Bottom Coordinate",
            settings[1] if len(settings) > 1 else ""
        )

        self.left_entry = self.create_input(
            "Left Coordinate",
            settings[2] if len(settings) > 2 else ""
        )

        self.right_entry = self.create_input(
            "Right Coordinate",
            settings[3] if len(settings) > 3 else ""
        )

        self.time_entry = self.create_input(
            "Time (minutes)",
            settings[4] if len(settings) > 4 else ""
        )

        # Save button
        tk.Button(
            self.frame,
            text="Save Settings",
            bg="green",
            fg="white",
            height=2,
            command=self.save_settings
        ).pack(fill="x", pady=10)

        # Back button
        tk.Button(
            self.frame,
            text="Back to Home",
            bg="gray",
            fg="white",
            height=2,
            command=self.show_home
        ).pack(fill="x")

    def show_home(self):
        self.clear_frame()

        tk.Label(
            self.frame,
            text="Urban Traffic Data Collector",
            font=("Arial", 20, "bold")
        ).pack(pady=30)

        # Start button
        tk.Button(
            self.frame,
            text="Start Collecting",
            bg="blue",
            fg="white",
            height=2,
            command=self.start_collecting
        ).pack(fill="x", pady=10)

        # Settings button
        tk.Button(
            self.frame,
            text="Edit Settings",
            bg="orange",
            fg="white",
            height=2,
            command=self.show_settings
        ).pack(fill="x", pady=10)

    def increment_request(self):
        self.request_count += 1

        self.request_label.config(
            text=f"Requests Done: {self.request_count}"
        )


    def increment_accident(self):
        self.accident_count += 1

        self.accident_label.config(
            text=f"Accidents Found: {self.accident_count}"
        )

    def stop_collection(self):
        self.collection_running = False
        if hasattr(self, "after_id"):
            self.frame.after_cancel(self.after_id)
        self.show_home()
    def run_collection(self, time_value):

        if not self.collection_running:
            return

        try:

            self.status_label.config(
                text="Status: Fetching data...",
                fg="orange"
            )

            # Fetch data
            data = fetch()

            if data:

                # Save to DB
                save_alerts(data)
                save_jams(data)

                # Count requests
                self.request_count += 1

                

                # Update UI
                self.request_label.config(
                    text=f"Requests Done: {self.request_count}"
                )
                self.status_label.config(
                    text="Status: Data saved successfully",
                    fg="green"
                )

            else:
                self.status_label.config(
                    text="Status: No data received",
                    fg="red"
                )

        except Exception as e:

            self.status_label.config(
                text=f"Error: {str(e)}",
                fg="red"
            )

        # Schedule next request
        interval_ms = int(time_value) * 60 * 1000

        self.after_id = self.frame.after(
            interval_ms,
            lambda: self.run_collection(time_value)
        )

    def show_collection_interface(self):

        self.clear_frame()

        # Load settings
        settings = self.load_settings()
        time_value = settings[4]

        # Date info
        today = datetime.now()
        current_date = today.strftime("%d-%m-%Y")
        day_name = today.strftime("%A")

        # Counters
        self.request_count = 0
        self.accident_count = 0
        self.collection_running = True

        # Title
        tk.Label(
            self.frame,
            text="Urban Traffic Data Collection",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        # Date
        tk.Label(
            self.frame,
            text=f"Date: {current_date}",
            font=("Arial", 12)
        ).pack()

        # Day
        tk.Label(
            self.frame,
            text=f"Day: {day_name}",
            font=("Arial", 12)
        ).pack(pady=5)

        # Interval
        tk.Label(
            self.frame,
            text=f"Collection every {time_value} minute(s)",
            font=("Arial", 12)
        ).pack(pady=5)

        # Request counter
        self.request_label = tk.Label(
            self.frame,
            text="Requests Done: 0",
            font=("Arial", 12, "bold")
        )
        self.request_label.pack(pady=10)

        # Last request time
        self.last_request_label = tk.Label(
            self.frame,
            text="Last Request: Not yet",
            font=("Arial", 12, "bold")
        )
        self.last_request_label.pack(pady=10)

        # Status
        self.status_label = tk.Label(
            self.frame,
            text="Status: Waiting...",
            fg="blue",
            font=("Arial", 12, "bold")
        )
        self.status_label.pack(pady=10)

        # Start collection automatically
        self.run_collection(time_value)

        # Back button
        tk.Button(
            self.frame,
            text="Back to Home",
            bg="gray",
            fg="white",
            command=self.stop_collection
        ).pack(fill="x", pady=20)


root = tk.Tk()
app = WazeCollectorApp(root)
root.mainloop()