# ==========================================
# FILE: core/path_planner.py
# ==========================================

class PathPlanner:
    def __init__(self):
        self.kfs_grid = {"R1": None, "R2": None, "Fake": None}
        print("[INFO] Path Planner siap dalam mode Deterministic Waypoints.")

    def set_kfs_grid(self, kfs_type, row, col):
        """Menyimpan koordinat grid KFS dari dashboard operator."""
        if kfs_type not in self.kfs_grid:
            raise ValueError(f"Jenis KFS tidak dikenal: {kfs_type}")
        self.kfs_grid[kfs_type] = (row, col)
        print(f"[PLANNER] KFS {kfs_type} diset ke grid ({row}, {col})")

    def get_arena_1_target(self):
        """
        Mengembalikan target translasi dari titik Start menuju Rak Spearhead.
        Format return: (forward, left) dalam satuan meter.
        """
        # Contoh: Maju 2.0 meter, Geser Kanan 1.0 meter (Kanan = kiri negatif)
        return 2.0, -1.0  

    def get_arena_2_target(self):
        """Mengembalikan target translasi dari area Rak menuju tepat di depan Forest (Hutan)."""
        # Contoh: Maju 1.5 meter, Geser Kiri 0.0 meter
        return 1.5, 0.0   

    def get_arena_3_target(self):
        """Mengembalikan target translasi akhir menuju tiang scoring Arena 3."""
        # Contoh: Maju 2.0 meter, Geser Kiri 0.0 meter
        return 2.0, 0.0
