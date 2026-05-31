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

## Debug Target Vision

Untuk tuning titik crosshair spearhead tanpa menggerakkan robot:

```bash
source .venv/bin/activate
python scripts/debug_spearhead_target.py
```

Kontrol keyboard:

```text
a/d  geser target kiri/kanan
w/s  geser target atas/bawah
p    print ratio target saat ini
q    keluar
```

Salin nilai ratio yang sudah pas ke `VisionConfig` di `config.py`.
