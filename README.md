# GMRT Robot Workspace

Python high-level autonomous stack untuk robot KRAI. Workspace ini menggantikan
struktur `robot_sw/` dan dipakai langsung sebagai `robot_ws/`.

## Struktur

```text
robot_ws/
  main.py
  config.py
  core/
    fsm_master.py
    path_planner.py
  hardware/
    serial_interface.py
  vision/
    visual_servoing.py
    assets/
      best.pt
  ui/
    dashboard.py
  scripts/
    install_dependencies.sh
```

## Setup Jetson

Jalankan dari root workspace:

```bash
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh --system-packages --jetson-torch
source .venv/bin/activate
```

Gunakan `--jetson-torch` jika Torch/CUDA Jetson dipasang dari paket NVIDIA.
Tanpa opsi itu, script akan mencoba memasang `torch` dari `pip`.

## Model Vision

Letakkan model YOLO spearhead di:

```text
vision/assets/best.pt
```

Default class yang dilacak adalah:

```python
("grey spear",)
```

Ubah parameter kamera, class target, debug window, dan jarak blind approach di
`config.py` bagian `VisionConfig`.

## Menjalankan

```bash
source .venv/bin/activate
python main.py
```

Alur utama robot ada di `core/fsm_master.py`. Modul vision dipanggil setelah
robot sampai ke lokasi rak spearhead, lalu hanya melakukan koreksi kanan/kiri.
Setelah target lock, FSM melanjutkan maju buta dan aktuasi arm/gripper.

## Dashboard

`python main.py` menjalankan dashboard Tkinter di main thread dan FSM di
background thread. Dashboard menampilkan odometri, status arena, koneksi serial,
dan tombol `EMERGENCY STOP` yang langsung mengirim command stop ke Teensy.

## Debug Target Vision

Untuk tuning garis target spearhead tanpa menggerakkan robot:

```bash
source .venv/bin/activate
python scripts/debug_spearhead_target.py
```

Kontrol keyboard:

```text
a/d  geser garis target kiri/kanan
p    print ratio target saat ini
q    keluar
```

Vision hanya mengejar supaya centroid objek sejajar dengan garis vertikal target.
Jarak vertikal objek terhadap goal tidak dipakai sebagai syarat lock. Salin nilai
`SPEARHEAD_TARGET_X_RATIO` yang sudah pas ke `VisionConfig` di `config.py`.
