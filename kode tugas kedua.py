import cv2
import time
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox

# === Resolusi Kamera ===
RESOLUSI = {
    "120p": (160, 120),
    "240p": (320, 240),
    "360p": (480, 360),
    "480p": (640, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080)
}

# === Pilihan Durasi Maksimal (detik) ===
DURASI_LIMIT = {
    "1 menit": 60,
    "5 menit": 300,
    "30 menit": 1800,
    "1 jam": 3600
}


def load_cascade():
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(path)
    if face_cascade.empty():
        raise RuntimeError("Gagal memuat Haar Cascade.")
    return face_cascade


def detect_and_draw(frame, face_cascade, scaleFactor, minNeighbors):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=scaleFactor,
        minNeighbors=minNeighbors,
        minSize=(30, 30)
    )

    # Filter ukuran wajah agar tidak terlalu kecil/besar
    valid_faces = [(x, y, w, h) for (x, y, w, h) in faces if 80 < w < 400]
    for (x, y, w, h) in valid_faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return frame, valid_faces


def pilih_pengaturan_gui():
    """GUI untuk memilih resolusi dan durasi maksimal."""
    root = tk.Tk()
    root.title("Pengaturan Deteksi Wajah")
    root.geometry("320x250")
    root.resizable(False, False)

    tk.Label(root, text="Pilih Resolusi:", font=("Arial", 11)).pack(pady=5)
    selected_res = tk.StringVar(value="720p")
    combo_res = ttk.Combobox(root, textvariable=selected_res,
                             values=list(RESOLUSI.keys()), state="readonly")
    combo_res.pack(pady=5)

    tk.Label(root, text="Durasi Maksimal:", font=("Arial", 11)).pack(pady=5)
    selected_durasi = tk.StringVar(value="5 menit")
    combo_durasi = ttk.Combobox(root, textvariable=selected_durasi,
                                values=list(DURASI_LIMIT.keys()), state="readonly")
    combo_durasi.pack(pady=5)

    start_pressed = tk.BooleanVar(value=False)

    def start():
        start_pressed.set(True)
        root.destroy()

    ttk.Button(root, text="Mulai", command=start).pack(pady=20)
    root.mainloop()

    if start_pressed.get():
        return selected_res.get(), selected_durasi.get()
    else:
        return None, None


def jalankan_deteksi(res_key, durasi_key):
    """Fungsi utama deteksi wajah dengan reset otomatis bila lama tidak terdeteksi."""
    width, height = RESOLUSI[res_key]
    durasi_maksimal = DURASI_LIMIT[durasi_key]
    batas_tidak_terdeteksi = 30  # <<< BATAS TANPA WAJAH 30 DETIK

    scaleFactor = 1.1
    minNeighbors = 8
    cam_index = 0

    face_cascade = load_cascade()
    cap = cv2.VideoCapture(cam_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    print(f"[INFO] Kamera dibuka pada {width}x{height}")
    print(f"[INFO] Durasi maksimal deteksi: {durasi_key}")
    print("[INFO] Tekan 'Q' untuk keluar.")

    frame_count, t0 = 0, time.time()
    total_detected_time = 0.0
    last_detect_time = None
    last_no_detect_time = None
    waktu_tanpa_wajah = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        frame, faces = detect_and_draw(frame, face_cascade, scaleFactor, minNeighbors)
        fps = frame_count / (time.time() - t0)

        # === Jika ada wajah ===
        if len(faces) > 0:
            if last_detect_time is None:
                last_detect_time = time.time()
            else:
                total_detected_time += time.time() - last_detect_time
            last_detect_time = time.time()
            last_no_detect_time = None
            waktu_tanpa_wajah = 0.0  # reset idle timer

        # === Jika tidak ada wajah ===
        else:
            if last_no_detect_time is None:
                last_no_detect_time = time.time()
            waktu_tanpa_wajah = time.time() - last_no_detect_time

            # jika tidak mendeteksi wajah lebih dari batas 30 detik
            if waktu_tanpa_wajah >= batas_tidak_terdeteksi:
                cap.release()
                cv2.destroyAllWindows()
                messagebox.showinfo("Reset Otomatis",
                                    f"Tidak ada wajah terdeteksi selama "
                                    f"{int(waktu_tanpa_wajah)} detik.\n"
                                    "Sistem direset ke menu awal.")
                return "RESET"

            last_detect_time = None

        # === Jika waktu maksimal tercapai ===
        if total_detected_time >= durasi_maksimal:
            print("[PERINGATAN] Waktu maksimal tercapai! Waktunya istirahat demi kesehatan!")
            popup = 255 * np.ones((200, 500, 3), dtype=np.uint8)
            cv2.putText(popup, "WAKTUNYA ISTIRAHAT!", (40, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            cv2.imshow("Peringatan Istirahat", popup)
            cv2.waitKey(5000)
            cv2.destroyWindow("Peringatan Istirahat")

            messagebox.showinfo("Peringatan!", "Waktunya istirahat demi kesehatan!\n"
                                               "Setelah ini sistem kembali ke menu awal.")
            cap.release()
            cv2.destroyAllWindows()
            return "RESET"

        # === Tampilkan info di frame ===
        cv2.putText(frame, f"Wajah: {len(faces)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(frame, f"Durasi: {int(total_detected_time)}s / {durasi_key}",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Tanpa wajah: {int(waktu_tanpa_wajah)}s",
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2)

        cv2.imshow(f"Deteksi Wajah ({res_key})", frame)

        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            cap.release()
            cv2.destroyAllWindows()
            return "KELUAR"


def main():
    while True:
        res_key, durasi_key = pilih_pengaturan_gui()
        if res_key is None or durasi_key is None:
            print("Dibatalkan oleh pengguna.")
            break

        hasil = jalankan_deteksi(res_key, durasi_key)

        if hasil == "RESET":
            continue
        elif hasil == "KELUAR":
            break


if __name__ == "__main__":
    main()
