"""Tkinter dashboard for passive robot monitoring and emergency stop."""

import tkinter as tk
from tkinter import ttk


class RobotDashboard:
    REFRESH_MS = 100

    def __init__(self, fsm):
        self.fsm = fsm
        self.robot = fsm.robot

        self.root = tk.Tk()
        self.root.title("GMRT Robot Dashboard")
        self.root.geometry("420x360")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.odom_x_var = tk.StringVar(value="0.000 m")
        self.odom_y_var = tk.StringVar(value="0.000 m")
        self.theta_var = tk.StringVar(value="0.00 deg")
        self.state_var = tk.StringVar(value="STANDBY")
        self.serial_var = tk.StringVar(value="DISCONNECTED")

        self._build_layout()
        self._refresh()

    def _build_layout(self):
        self.root.configure(bg="#101418")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Root.TFrame", background="#101418")
        style.configure("Panel.TFrame", background="#182028", relief="flat")
        style.configure("Title.TLabel", background="#101418", foreground="#f4f7fb", font=("Arial", 16, "bold"))
        style.configure("Label.TLabel", background="#182028", foreground="#aab4c0", font=("Arial", 10))
        style.configure("Value.TLabel", background="#182028", foreground="#f4f7fb", font=("Consolas", 18, "bold"))
        style.configure("State.TLabel", background="#182028", foreground="#f4f7fb", font=("Arial", 13, "bold"))
        style.configure("Stop.TButton", font=("Arial", 18, "bold"))

        root_frame = ttk.Frame(self.root, padding=16, style="Root.TFrame")
        root_frame.pack(fill="both", expand=True)

        title = ttk.Label(root_frame, text="GMRT ROBOT DASHBOARD", style="Title.TLabel")
        title.pack(anchor="w")

        telemetry = ttk.Frame(root_frame, padding=14, style="Panel.TFrame")
        telemetry.pack(fill="x", pady=(14, 10))

        self._add_metric(telemetry, 0, "X (Fwd)", self.odom_x_var)
        self._add_metric(telemetry, 1, "Y (Strf)", self.odom_y_var)
        self._add_metric(telemetry, 2, "Theta", self.theta_var)

        status = ttk.Frame(root_frame, padding=14, style="Panel.TFrame")
        status.pack(fill="x", pady=(0, 12))

        ttk.Label(status, text="FSM State", style="Label.TLabel").grid(row=0, column=0, sticky="w")
        self.state_label = ttk.Label(status, textvariable=self.state_var, style="State.TLabel")
        self.state_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        ttk.Label(status, text="Serial", style="Label.TLabel").grid(row=0, column=1, sticky="w", padx=(32, 0))
        self.serial_label = ttk.Label(status, textvariable=self.serial_var, style="State.TLabel")
        self.serial_label.grid(row=1, column=1, sticky="w", padx=(32, 0), pady=(4, 0))

        stop_btn = tk.Button(
            root_frame,
            text="EMERGENCY STOP",
            command=self._emergency_stop,
            bg="#d71920",
            fg="white",
            activebackground="#a70f14",
            activeforeground="white",
            font=("Arial", 20, "bold"),
            relief="flat",
            height=2,
        )
        stop_btn.pack(fill="x", pady=(4, 0))

    def _add_metric(self, parent, column, label_text, value_var):
        cell = ttk.Frame(parent, style="Panel.TFrame")
        cell.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 12, 0))
        parent.columnconfigure(column, weight=1)

        ttk.Label(cell, text=label_text, style="Label.TLabel").pack(anchor="w")
        ttk.Label(cell, textvariable=value_var, style="Value.TLabel").pack(anchor="w", pady=(4, 0))

    def _refresh(self):
        self.odom_x_var.set(f"{self.robot.odom_x:.3f} m")
        self.odom_y_var.set(f"{self.robot.odom_y:.3f} m")
        self.theta_var.set(f"{self.robot.odom_theta_deg:.2f} deg")

        if self.robot.is_connected:
            self.state_var.set(self.fsm.current_arena)
            self.serial_var.set("CONNECTED")
            self.state_label.configure(foreground="#f4f7fb")
            self.serial_label.configure(foreground="#20d67b")
        else:
            self.state_var.set("DISCONNECTED / KABEL LEPAS!")
            self.serial_var.set("DISCONNECTED")
            self.state_label.configure(foreground="#ff4d4d")
            self.serial_label.configure(foreground="#ff4d4d")

        self.root.after(self.REFRESH_MS, self._refresh)

    def _emergency_stop(self):
        print("[DASHBOARD] Emergency stop clicked.")
        self.fsm.current_arena = "EMERGENCY_STOP"
        self.robot.e_stop()

    def _on_close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def run_dashboard(fsm) -> None:
    RobotDashboard(fsm).run()


Dashboard = RobotDashboard
