# ==========================================
# ui/dashboard.py
# ==========================================
import tkinter as tk
from tkinter import messagebox
import threading

class RobotDashboard:
    def __init__(self, window, fsm_instance):
        self.window = window
        self.fsm = fsm_instance
        self.window.title("KRAI 2026 - MASTER CONTROL DASHBOARD")
        self.window.geometry("800x480")
        self.window.configure(bg="#222222")

        # Memory lokal GUI untuk memantau tombol mana yang sedang memegang KFS tertentu
        self.kfs_local_coords = {"R1": None, "R2": None, "Fake": None}

        # ==========================================
        # PANEL KIRI: TOMBOL KONTROL UTAMA
        # ==========================================
        left_panel = tk.Frame(window, bg="#2d2d2d", padx=15, pady=15)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_panel, text="COMMAND CONTROL", font=("Arial", 12, "bold"), bg="#2d2d2d", fg="white").pack(pady=10)
        
        # Action Buttons
        tk.Button(left_panel, text="START GLOBAL AUTO", bg="#00aa00", fg="white", font=("Arial", 10, "bold"), width=22, height=2, command=self.gui_start).pack(pady=5)
        tk.Button(left_panel, text="RETRY ARENA 1", bg="#33b5e5", fg="white", width=22, height=1, command=lambda: self.gui_retry(1)).pack(pady=3)
        tk.Button(left_panel, text="RETRY ARENA 2", bg="#33b5e5", fg="white", width=22, height=1, command=lambda: self.gui_retry(2)).pack(pady=3)
        tk.Button(left_panel, text="RETRY ARENA 3", bg="#33b5e5", fg="white", width=22, height=1, command=lambda: self.gui_retry(3)).pack(pady=3)
        
        # Safe Buttons
        tk.Button(left_panel, text="EMERGENCY STOP (S)", bg="#ff4444", fg="white", font=("Arial", 11, "bold"), width=20, height=2, command=self.fsm.trigger_stop).pack(pady=20)
        tk.Button(left_panel, text="RESET SYSTEM (Z)", bg="#aa66cc", fg="white", width=22, command=self.fsm.trigger_reset).pack(pady=3)

        # Monitor State Text
        self.lbl_status = tk.Label(left_panel, text="STATE: STANDBY", font=("Arial", 12, "bold"), bg="#2d2d2d", fg="#ffbb33")
        self.lbl_status.pack(side=tk.BOTTOM, pady=20)

        # ==========================================
        # PANEL KANAN: MATRIKS KFS 3X4
        # ==========================================
        right_panel = tk.Frame(window, bg="#222222", padx=20, pady=15)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_panel, text="KUNG FU SQUARE MATRIX (3x4)", font=("Arial", 13, "bold"), bg="#222222", fg="white").pack(pady=5)

        # Radio Button Selektor Jenis KFS
        self.selected_kfs_type = tk.StringVar(value="R1")
        radio_frame = tk.Frame(right_panel, bg="#222222")
        radio_frame.pack(pady=5)
        
        tk.Radiobutton(radio_frame, text="Set KFS R1", variable=self.selected_kfs_type, value="R1", font=("Arial", 10, "bold"), bg="#222222", fg="#4285F4", selectcolor="#222222").pack(side=tk.LEFT, padx=15)
        tk.Radiobutton(radio_frame, text="Set KFS R2", variable=self.selected_kfs_type, value="R2", font=("Arial", 10, "bold"), bg="#222222", fg="#0F9D58", selectcolor="#222222").pack(side=tk.LEFT, padx=15)
        tk.Radiobutton(radio_frame, text="Set KFS Fake", variable=self.selected_kfs_type, value="Fake", font=("Arial", 10, "bold"), bg="#222222", fg="#DB4437", selectcolor="#222222").pack(side=tk.LEFT, padx=15)

        # Grid Pembentuk Matriks 3x4
        grid_container = tk.Frame(right_panel, bg="#333333", padx=10, pady=10)
        grid_container.pack(pady=10)
        
        self.grid_buttons = {}
        for row in range(3):
            for col in range(4):
                btn_key = f"{row},{col}"
                btn = tk.Button(
                    grid_container, 
                    text=f"Empty\n({row},{col})", 
                    width=10, 
                    height=3, 
                    bg="#555555", 
                    fg="white",
                    font=("Arial", 9),
                    command=lambda r=row, c=col: self.on_grid_click(r, c)
                )
                btn.grid(row=row, column=col, padx=4, pady=4)
                self.grid_buttons[btn_key] = btn

        # Jalankan loop sinkronisasi teks status FSM ke GUI secara periodik
        self.refresh_status_loop()

    def on_grid_click(self, row, col):
        """Mengatur visual warna tombol saat diklik dan melempar koordinat ke Path Planner"""
        kfs_type = self.selected_kfs_type.get()

        # Bersihkan visual tombol lama yang sebelumnya memegang jenis KFS ini
        if self.kfs_local_coords[kfs_type] is not None:
            old_r, old_c = self.kfs_local_coords[kfs_type]
            self.grid_buttons[f"{old_r},{old_c}"].config(text=f"Empty\n({old_r},{old_c})", bg="#555555", fg="white")

        # Daftarkan koordinat baru
        self.kfs_local_coords[kfs_type] = (row, col)
        
        # Berikan warna identitas unik pada tombol matriks
        style_map = {"R1": ("#4285F4", "white"), "R2": ("#0F9D58", "white"), "Fake": ("#DB4437", "white")}
        bg_color, fg_color = style_map[kfs_type]
        self.grid_buttons[f"{row},{col}"].config(text=f"🎯 {kfs_type}\n({row},{col})", bg=bg_color, fg=fg_color)

        # KIRIM DATA LANGSUNG KE OBJECT PATH PLANNER DI DALAM FSM ROBOT
        self.fsm.planner.set_kfs_grid(kfs_type, row, col)

    def gui_start(self):
        # Proteksi pengaman: Lomba tidak boleh start jika koordinat sasaran penting belum ditentukan
        if self.kfs_local_coords["R1"] is None or self.kfs_local_coords["R2"] is None:
            messagebox.showwarning("KFS Kosong", "Tentukan posisi KFS R1 dan KFS R2 terlebih dahulu di matriks!")
            return
        # Panggil FSM menggunakan Thread baru agar GUI tidak lag/macet
        threading.Thread(target=self.fsm.trigger_full_auto, daemon=True).start()

    def gui_retry(self, arena_id):
        threading.Thread(target=self.fsm.trigger_retry_arena, args=(arena_id,), daemon=True).start()

    def refresh_status_loop(self):
        """Loop berkala membaca status terkini dari FSM Robot"""
        self.lbl_status.config(text=f"STATE: {self.fsm.current_arena}")
        self.window.after(100, self.refresh_status_loop)