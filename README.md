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

## Test Teensy

Untuk mengecek koneksi Jetson ke Teensy dan arah aktuator secara manual:

```bash
source .venv/bin/activate
python scripts/test_teensy_connection.py
```

Default gerak kecil adalah `0.20 m` dan rotasi `20 deg`. Bisa diubah:

```bash
python scripts/test_teensy_connection.py --move 0.10 --turn 10
```

Script ini interaktif dan meminta konfirmasi sebelum setiap gerakan.

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

## Test Vision Alignment

Untuk mengetes deteksi spearhead dan koreksi kiri/kanan saja:

```bash
source .venv/bin/activate
python scripts/test_vision_alignment.py
```

Mode di atas hanya visual. Untuk mengizinkan robot bergerak kiri/kanan:

```bash
python scripts/test_vision_alignment.py --move
```

Untuk Jetson yang lambat atau mode headless/no GUI:

```bash
python scripts/test_vision_alignment.py --move --no-gui --width 320 --height 240 --imgsz 480
```

untuk test lagi

```bash
python scripts/test_vision_alignment.py --move --width 320 --height 240 --imgsz 480 --min-step 0.03 --max-step 0.08 --motion-timeout 12
```

Kamera disetel low-latency dengan buffer kecil dan membuang frame lama sebelum
inferensi agar robot tidak mengejar posisi objek yang sudah basi.

Kontrol keyboard:

```text
space  toggle auto correction
m      satu langkah koreksi
e      emergency stop
q      keluar
```

Script ini tidak menjalankan maju, rotasi, arm, atau gripper.
