# main.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog, simpledialog
from ttkbootstrap.widgets import DateEntry
import threading
from datetime import datetime
import shutil
from pathlib import Path
import os
import sys
import re

from data_manager import DataManager
from automation import take_screenshot

class MainApp(ttk.Window):
    def __init__(self):
        self.data_manager = DataManager()
        config = self.data_manager.load_config()
        super().__init__(themename=config.get("theme", "darkly"))
        self.title("Technical Operations Suite (TOS)")
        self.geometry("1400x800")
        
        self.save_path_var = ttk.StringVar()
        self.auto_zip_var = ttk.BooleanVar()
        self.outlet_name_var = ttk.StringVar()
        self.current_progress = 0.0
        self.dcp_filter_var = ttk.StringVar(value="Tampilkan Semua")
        self.fpkb_filter_var = ttk.StringVar(value="Tampilkan Semua")
        self.fpkb_check_vars = {}

        self.create_widgets()
        self.load_settings_to_ui()
        self.show_disclaimer()

    def create_widgets(self):
        header_frame = ttk.Frame(self); header_frame.pack(fill=X, padx=10, pady=(5, 0))
        app_name_label = ttk.Label(header_frame, text="Technical Operations Suite", font=("-size 12")); app_name_label.pack(side=LEFT)
        version_label = ttk.Label(header_frame, text="v8.1-1", font="-size 10"); version_label.pack(side=RIGHT)
        about_button = ttk.Button(header_frame, text="About", style="info.Outline.TButton", command=self.show_about_dialog); about_button.pack(side=RIGHT, padx=(0, 10))
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        def add_tab(title):
            frame = ttk.Frame(self.notebook, padding=10); self.notebook.add(frame, text=title); return frame
        self.create_lss_tab(add_tab("LSS Screenshot"))
        self.create_dcp_tab(add_tab("DCP Management"))
        self.create_fpkb_tab(add_tab("Manajemen FPKB"))
        self.create_settings_tab(add_tab("Pengaturan"))

    def show_about_dialog(self):
        messagebox.showinfo(title="About Technical Operations Suite", message="Aplikasi ini dikembangkan oleh:\n\nMuhamad Naslim\n\nVersi: 8.1-1")

    def create_lss_tab(self, parent_frame):
        top_frame = ttk.Frame(parent_frame); top_frame.pack(fill=X, pady=5); self.btn_screenshot = ttk.Button(top_frame, text="One Click Screenshot", command=self.start_screenshot_process, style="success.TButton"); self.btn_screenshot.pack(side=LEFT, padx=5); self.progress_bar = ttk.Progressbar(top_frame, orient=HORIZONTAL, length=300, mode='determinate', style='success-striped'); self.progress_bar.pack(side=LEFT, fill=X, expand=True, padx=5); settings_frame = ttk.LabelFrame(parent_frame, text="Opsi Screenshot", padding=15); settings_frame.pack(fill=X, pady=(10,5)); path_frame = ttk.Frame(settings_frame); path_frame.pack(fill=X); ttk.Label(path_frame, text="Folder Penyimpanan:").pack(side=LEFT, padx=(0, 10)); path_entry = ttk.Entry(path_frame, textvariable=self.save_path_var, state="readonly"); path_entry.pack(side=LEFT, fill=X, expand=True); btn_browse = ttk.Button(path_frame, text="Pilih Folder...", command=self.select_save_path); btn_browse.pack(side=LEFT, padx=(10, 0)); btn_open = ttk.Button(path_frame, text="Buka Folder", command=self.open_save_folder, style="info.Outline.TButton"); btn_open.pack(side=LEFT, padx=(5,0)); zip_frame = ttk.Frame(settings_frame); zip_frame.pack(fill=X, pady=(10, 0)); zip_check = ttk.Checkbutton(zip_frame, text="Kompres hasil screenshot ke file ZIP secara otomatis", variable=self.auto_zip_var, command=self.save_settings, style="success.TCheckbutton"); zip_check.pack(side=LEFT); main_paned_window = ttk.PanedWindow(parent_frame, orient=HORIZONTAL); main_paned_window.pack(fill=BOTH, expand=True, pady=10); left_pane = ttk.Frame(main_paned_window, padding=0); console_frame = ttk.LabelFrame(left_pane, text="Real-time Log", padding=10); console_frame.pack(fill=BOTH, expand=True); self.console_log = ttk.Text(console_frame, height=15, state="disabled", wrap="word"); self.console_log.pack(fill=BOTH, expand=True); self.console_log.tag_configure("success", foreground="#28a745"); self.console_log.tag_configure("warning", foreground="#ffc107"); self.console_log.tag_configure("error", foreground="#dc3545"); self.console_log.tag_configure("info", foreground="#17a2b8"); self.console_log.tag_configure("neutral", foreground="gray"); main_paned_window.add(left_pane, weight=2); right_pane = ttk.Frame(main_paned_window, padding=0); self._create_studio_management_ui(right_pane); main_paned_window.add(right_pane, weight=1)
    def _create_studio_management_ui(self, parent_frame):
        studio_frame = ttk.LabelFrame(parent_frame, text="Daftar Studio (Double-click untuk Aktif/Nonaktif)", padding=10); studio_frame.pack(fill=BOTH, expand=True); tree_frame = ttk.Frame(studio_frame); tree_frame.pack(fill=BOTH, expand=True, pady=5); columns = ("nama", "format", "status"); self.studio_tree = ttk.Treeview(tree_frame, columns=columns, show="headings"); self.studio_tree.heading("nama", text="Nama Studio"); self.studio_tree.heading("format", text="Format"); self.studio_tree.heading("status", text="Status"); self.studio_tree.column("nama", width=200); self.studio_tree.column("format", width=100, anchor=CENTER); self.studio_tree.column("status", width=80, anchor=CENTER); self.studio_tree.pack(fill=BOTH, expand=True, side=LEFT); scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.studio_tree.yview); self.studio_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=RIGHT, fill=Y); self.studio_tree.bind("<Double-1>", self.toggle_studio_status); self.studio_tree.tag_configure('disabled', foreground='gray'); button_frame = ttk.Frame(studio_frame, padding=(0, 10)); button_frame.pack(fill=X); btn_add = ttk.Button(button_frame, text="Tambah", command=self.add_studio, style="success.TButton"); btn_add.pack(side=LEFT, padx=2, fill=X, expand=True); btn_edit = ttk.Button(button_frame, text="Edit", command=self.edit_studio, style="info.TButton"); btn_edit.pack(side=LEFT, padx=2, fill=X, expand=True); btn_delete = ttk.Button(button_frame, text="Hapus", command=self.delete_studio, style="danger.TButton"); btn_delete.pack(side=LEFT, padx=2, fill=X, expand=True); self.load_studios_to_treeview()
    def create_dcp_tab(self, parent_frame):
        filter_frame = ttk.Frame(parent_frame); filter_frame.pack(fill=X, pady=(0, 10)); ttk.Label(filter_frame, text="Filter Status:").pack(side=LEFT, padx=(0, 10)); filter_buttons = ["Tampilkan Semua", "Belum Tayang", "Sedang Tayang", "Sudah Tayang"]; style_map = {"Tampilkan Semua": "primary", "Belum Tayang": "secondary", "Sedang Tayang": "warning", "Sudah Tayang": "dark"};
        for text in filter_buttons: btn = ttk.Radiobutton(filter_frame, text=text, variable=self.dcp_filter_var, value=text, command=self.load_dcps_to_treeview, style=f"{style_map[text]}.Outline.Toolbutton"); btn.pack(side=LEFT, padx=2)
        tree_frame = ttk.Frame(parent_frame); tree_frame.pack(fill=BOTH, expand=True, pady=5); columns = ("judul", "file", "uploader", "no_dcp", "lokasi", "status"); self.dcp_tree = ttk.Treeview(tree_frame, columns=columns, show="headings"); self.dcp_tree.heading("judul", text="Judul Film"); self.dcp_tree.heading("file", text="Nama File DCP"); self.dcp_tree.heading("uploader", text="Uploader"); self.dcp_tree.heading("no_dcp", text="Nomor DCP"); self.dcp_tree.heading("lokasi", text="Lokasi Ingest"); self.dcp_tree.heading("status", text="Status Tayang"); self.dcp_tree.column("judul", width=250); self.dcp_tree.column("file", width=300); self.dcp_tree.pack(fill=BOTH, expand=True, side=LEFT); scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.dcp_tree.yview); self.dcp_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=RIGHT, fill=Y); self.dcp_tree.tag_configure('sedang_tayang', background='#4B4B2C'); self.dcp_tree.tag_configure('sudah_tayang', background='#3C3C3C'); self.dcp_tree.bind("<Button-1>", self.on_dcp_status_click); button_frame = ttk.Frame(parent_frame, padding=(0, 10)); button_frame.pack(fill=X); btn_add = ttk.Button(button_frame, text="Tambah DCP", command=self.add_dcp, style="success.TButton"); btn_add.pack(side=LEFT, padx=5); btn_edit = ttk.Button(button_frame, text="Edit DCP", command=self.edit_dcp, style="info.TButton"); btn_edit.pack(side=LEFT, padx=5); btn_delete = ttk.Button(button_frame, text="Hapus DCP", command=self.delete_dcp, style="danger.TButton"); btn_delete.pack(side=LEFT, padx=5); self.load_dcps_to_treeview()
    def create_fpkb_tab(self, parent_frame):
        filter_frame = ttk.Frame(parent_frame); filter_frame.pack(fill=X, pady=(0, 10)); ttk.Label(filter_frame, text="Filter Penerimaan:").pack(side=LEFT, padx=(0, 10)); filter_buttons = ["Tampilkan Semua", "Belum Diterima", "Sudah Diterima"]; style_map = {"Tampilkan Semua": "primary", "Belum Diterima": "warning", "Sudah Diterima": "success"};
        for text in filter_buttons: btn = ttk.Radiobutton(filter_frame, text=text, variable=self.fpkb_filter_var, value=text, command=self.load_fpkb_to_treeview, style=f"{style_map[text]}.Outline.Toolbutton"); btn.pack(side=LEFT, padx=2)
        tree_frame = ttk.Frame(parent_frame); tree_frame.pack(fill=BOTH, expand=True, pady=5); columns = ("check", "tanggal", "barang", "qty", "status_fpkb", "status_penerimaan", "aksi"); self.fpkb_tree = ttk.Treeview(tree_frame, columns=columns, show="headings"); self.fpkb_tree.heading("check", text="Pilih"); self.fpkb_tree.column("check", width=50, anchor=CENTER); self.fpkb_tree.heading("tanggal", text="Tanggal"); self.fpkb_tree.column("tanggal", width=120, anchor=W); self.fpkb_tree.heading("barang", text="Nama Barang"); self.fpkb_tree.column("barang", width=400, anchor=W); self.fpkb_tree.heading("qty", text="Qty"); self.fpkb_tree.column("qty", width=80, anchor=CENTER); self.fpkb_tree.heading("status_fpkb", text="Status FPKB"); self.fpkb_tree.column("status_fpkb", width=150, anchor=W); self.fpkb_tree.heading("status_penerimaan", text="Status Penerimaan"); self.fpkb_tree.column("status_penerimaan", width=300, anchor=W); self.fpkb_tree.heading("aksi", text="Aksi"); self.fpkb_tree.column("aksi", width=150, anchor=CENTER); self.fpkb_tree.pack(fill=BOTH, expand=True, side=LEFT); scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.fpkb_tree.yview); self.fpkb_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=RIGHT, fill=Y);
        self.fpkb_tree.tag_configure('fpkb_belum', foreground='#FF6347'); self.fpkb_tree.tag_configure('fpkb_sudah', foreground='#32CD32'); self.fpkb_tree.tag_configure('diterima_parent', background='#203731'); self.fpkb_tree.tag_configure('diterima_child', background='#203731', foreground='gray'); self.fpkb_tree.tag_configure('clickable', foreground='cyan')
        self.fpkb_tree.bind("<Button-1>", self.on_fpkb_cell_click)
        button_frame = ttk.Frame(parent_frame, padding=(0, 10)); button_frame.pack(fill=X); btn_add = ttk.Button(button_frame, text="Tambah FPKB", command=self.add_fpkb, style="success.TButton"); btn_add.pack(side=LEFT, padx=5);
        self.btn_terima_barang = ttk.Button(button_frame, text="Terima Barang Terpilih", command=self.receive_selected_fpkb, style="info.TButton", state="disabled"); self.btn_terima_barang.pack(side=LEFT, padx=5)
        self.load_fpkb_to_treeview()
    def create_settings_tab(self, parent_frame):
        settings_pane = ttk.PanedWindow(parent_frame, orient=HORIZONTAL); settings_pane.pack(fill=BOTH, expand=True); general_settings_frame = ttk.Frame(settings_pane, padding=0); outlet_frame = ttk.LabelFrame(general_settings_frame, text="Pengaturan Umum", padding=15); outlet_frame.pack(fill=X, pady=10, padx=5); ttk.Label(outlet_frame, text="Nama Outlet (untuk folder):").pack(side=LEFT, padx=(0, 10)); outlet_entry = ttk.Entry(outlet_frame, textvariable=self.outlet_name_var); outlet_entry.pack(side=LEFT, fill=X, expand=True); outlet_entry.bind("<KeyRelease>", lambda event: self.save_settings()); settings_pane.add(general_settings_frame, weight=1); tech_frame_container = ttk.Frame(settings_pane, padding=0); tech_frame = ttk.LabelFrame(tech_frame_container, text="Manajemen Teknisi", padding=15); tech_frame.pack(fill=BOTH, expand=True, pady=10, padx=5); tree_frame = ttk.Frame(tech_frame); tree_frame.pack(fill=BOTH, expand=True, pady=5); self.tech_tree = ttk.Treeview(tree_frame, columns=("nama",), show="headings"); self.tech_tree.heading("nama", text="Nama Teknisi"); self.tech_tree.pack(fill=BOTH, expand=True, side=LEFT); scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tech_tree.yview); self.tech_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=RIGHT, fill=Y); button_frame = ttk.Frame(tech_frame, padding=(0, 10)); button_frame.pack(fill=X, pady=(5,0)); btn_add = ttk.Button(button_frame, text="Tambah Teknisi", command=self.add_technician, style="success.TButton"); btn_add.pack(side=LEFT, padx=5); btn_delete = ttk.Button(button_frame, text="Hapus Teknisi", command=self.delete_technician, style="danger.TButton"); btn_delete.pack(side=LEFT, padx=5); settings_pane.add(tech_frame_container, weight=1); self.load_technicians_to_treeview()
    def load_settings_to_ui(self):
        config = self.data_manager.load_config(); self.save_path_var.set(config.get("save_path", "")); self.auto_zip_var.set(config.get("auto_zip", False)); self.outlet_name_var.set(config.get("outlet_name", "NAMA_OUTLET"))
    def select_save_path(self):
        new_path = filedialog.askdirectory(initialdir=self.save_path_var.get());
        if new_path: self.save_path_var.set(new_path); self.save_settings()
    def open_save_folder(self):
        folder_path = self.save_path_var.get();
        if not os.path.isdir(folder_path): messagebox.showerror("Error", f"Folder tidak ditemukan:\n{folder_path}"); return
        try:
            if sys.platform == "win32": os.startfile(folder_path)
            elif sys.platform == "darwin": os.system(f'open "{folder_path}"')
            else: os.system(f'xdg-open "{folder_path}"')
        except Exception as e: messagebox.showerror("Error", f"Gagal membuka folder:\n{e}")
    def save_settings(self):
        config = self.data_manager.load_config(); config["save_path"] = self.save_path_var.get(); config["auto_zip"] = self.auto_zip_var.get(); config["outlet_name"] = self.outlet_name_var.get(); self.data_manager.save_config(config)
    def log_and_update_progress(self, message, increment):
        timestamp = datetime.now().strftime("%H:%M:%S"); full_message = f"[{timestamp}] {message}\n"; msg_lower = message.lower(); level = "neutral";
        if "error" in msg_lower: level = "error"
        elif "peringatan" in msg_lower or "warning" in msg_lower or "info" in msg_lower: level = "warning"
        elif "berhasil" in msg_lower or "selesai" in msg_lower or "disimpan" in msg_lower: level = "success"
        elif "memproses" in msg_lower or "mencari" in msg_lower or "menunggu" in msg_lower or "memfilter" in msg_lower: level = "info"
        self.console_log.config(state="normal"); self.console_log.insert(END, full_message, level); self.console_log.config(state="disabled"); self.console_log.see(END);
        if increment > 0: self.current_progress += increment; self.progress_bar['value'] = self.current_progress
    def start_screenshot_process(self):
        self.btn_screenshot.config(state="disabled"); self.progress_bar['value'] = 0; self.current_progress = 0.0; self.config(cursor="watch"); self.btn_screenshot.config(text="MEMPROSES...", style="info.TButton"); self.progress_bar.start(10); thread = threading.Thread(target=self.run_automation_logic); thread.daemon = True; thread.start()
    def finalize_process_ui(self, summary_message=None):
        self.progress_bar.stop(); self.config(cursor=""); self.btn_screenshot.config(text="One Click Screenshot", style="success.TButton", state="normal"); self.progress_bar['value'] = 100
        if summary_message: messagebox.showinfo("Proses Selesai", summary_message)
    def run_automation_logic(self):
        config = self.data_manager.load_config(); studios = self.data_manager.load_studios(); active_studios = [s for s in studios if s.get('enabled', True)];
        if not active_studios: self.after(0, self.log_and_update_progress, "PERINGATAN: Tidak ada studio yang aktif.", 0); self.after(100, lambda: self.finalize_process_ui(summary_message="Tidak ada studio aktif untuk diproses.")); return
        stats = {'SUCCESS': 0, 'WARNING': 0, 'ERROR': 0, 'NO_LOGS': 0, 'SKIPPED': 0}; steps_per_studio = 7; total_studios = len(active_studios); progress_increment = (100 / total_studios) / steps_per_studio;
        outlet_name = re.sub(r'[\s/\\:*?"<>|()]', '_', config.get("outlet_name", "NAMA_OUTLET")); today_str = datetime.now().strftime("%Y-%m-%d"); folder_name = f"{outlet_name}_{today_str}"; output_folder_path = Path(config['save_path']) / folder_name; output_folder_path.mkdir(parents=True, exist_ok=True)
        for i, studio in enumerate(active_studios):
            studio_name = studio.get('name', 'UnknownStudio'); studio_url = studio.get('url', '');
            if not studio_url: self.after(0, self.log_and_update_progress, f"PERINGATAN: URL untuk {studio_name} kosong, dilewati.", 0); stats['SKIPPED'] += 1; continue
            def threaded_callback(msg): self.after(0, self.log_and_update_progress, msg, progress_increment)
            status, _ = take_screenshot(studio_url, str(output_folder_path), studio_name, threaded_callback)
            if status in stats: stats[status] += 1
            self.current_progress = (i + 1) * (100 / total_studios); self.progress_bar['value'] = self.current_progress
        self.after(0, self.log_and_update_progress, "PROSES SELESAI!", 0);
        zip_message = "";
        if config.get("auto_zip", False):
            if self.create_zip_archive(): zip_message = "\n\n✔️ File ZIP berhasil dibuat."
        summary_message = f"Proses Selesai!\n\n✅ Berhasil: {stats['SUCCESS']}\n⚠️ Peringatan: {stats['WARNING']}\n❌ Gagal: {stats['ERROR']}\n🔵 Tanpa Log: {stats['NO_LOGS']}\n⚪ Dilewati: {stats['SKIPPED']}{zip_message}"; self.after(100, lambda: self.finalize_process_ui(summary_message))
    def create_zip_archive(self):
        config = self.data_manager.load_config(); today_str = datetime.now().strftime("%Y-%m-%d"); save_path = Path(config['save_path']); outlet_name = re.sub(r'[\s/\\:*?"<>|()]', '_', config.get("outlet_name", "NAMA_OUTLET")); folder_to_zip_name = f"{outlet_name}_{today_str}"; source_folder = save_path / folder_to_zip_name; zip_file_name_base = save_path / folder_to_zip_name
        if not source_folder.is_dir(): self.log_and_update_progress(f"Peringatan: Folder '{source_folder.name}' tidak ditemukan untuk di-ZIP.", 0); return False
        self.log_and_update_progress(f"Info: Membuat file ZIP untuk folder '{source_folder.name}'...", 0);
        try: shutil.make_archive(str(zip_file_name_base), 'zip', str(save_path), folder_to_zip_name); self.log_and_update_progress(f"Berhasil: File '{source_folder.name}.zip' berhasil dibuat.", 0); return True
        except Exception as e: self.log_and_update_progress(f"Error: Gagal membuat file ZIP - {e}", 0); return False
    def toggle_studio_status(self, event):
        selected_item = self.studio_tree.identify_row(event.y);
        if not selected_item: return
        studio_index = int(selected_item); studios = self.data_manager.load_studios()
        if studio_index >= len(studios): return
        studio_to_toggle = studios[studio_index]; current_status = studio_to_toggle.get("enabled", True); studio_to_toggle["enabled"] = not current_status; self.data_manager.save_studios(studios); self.load_studios_to_treeview()
    def load_studios_to_treeview(self):
        focused_item = self.studio_tree.focus();
        for item in self.studio_tree.get_children(): self.studio_tree.delete(item)
        studios = self.data_manager.load_studios()
        for i, studio in enumerate(studios):
            is_enabled = studio.get("enabled", True); status_text = "Aktif" if is_enabled else "Nonaktif"; tags_to_apply = () if is_enabled else ('disabled',)
            values = (studio.get("name"), studio.get("format"), status_text); self.studio_tree.insert("", END, iid=i, values=values, tags=tags_to_apply)
        if focused_item and self.studio_tree.exists(focused_item): self.studio_tree.focus(focused_item); self.studio_tree.selection_set(focused_item)
    def add_studio(self): StudioEditor(self, title="Tambah Studio Baru", callback=self.load_studios_to_treeview)
    def edit_studio(self):
        selected_item = self.studio_tree.focus();
        if not selected_item: messagebox.showwarning("Peringatan", "Pilih studio yang ingin Anda edit terlebih dahulu."); return
        studio_index = int(selected_item); studios = self.data_manager.load_studios(); StudioEditor(self, title="Edit Studio", studio_data=studios[studio_index], studio_index=studio_index, callback=self.load_studios_to_treeview)
    def delete_studio(self):
        selected_item = self.studio_tree.focus();
        if not selected_item: messagebox.showwarning("Peringatan", "Pilih studio yang ingin Anda hapus terlebih dahulu."); return
        if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus studio ini?"):
            studio_index = int(selected_item); studios = self.data_manager.load_studios(); studios.pop(studio_index); self.data_manager.save_studios(studios); self.load_studios_to_treeview()
    def load_technicians_to_treeview(self):
        for item in self.tech_tree.get_children(): self.tech_tree.delete(item)
        technicians = self.data_manager.load_technicians()
        for i, tech in enumerate(technicians): self.tech_tree.insert("", END, iid=i, values=(tech,))
    def add_technician(self):
        name = simpledialog.askstring("Tambah Teknisi", "Masukkan nama teknisi:", parent=self);
        if name: technicians = self.data_manager.load_technicians(); technicians.append(name); self.data_manager.save_technicians(technicians); self.load_technicians_to_treeview()
    def delete_technician(self):
        selected = self.tech_tree.focus();
        if not selected: messagebox.showwarning("Peringatan", "Pilih teknisi yang akan dihapus."); return
        if messagebox.askyesno("Konfirmasi", "Yakin ingin menghapus teknisi ini?"):
            tech_index = int(selected); technicians = self.data_manager.load_technicians(); technicians.pop(tech_index); self.data_manager.save_technicians(technicians); self.load_technicians_to_treeview()
    def load_dcps_to_treeview(self):
        for item in self.dcp_tree.get_children(): self.dcp_tree.delete(item)
        dcp_logs = self.data_manager.load_dcp_logs(); filter_value = self.dcp_filter_var.get()
        for i, dcp in enumerate(dcp_logs):
            status = dcp.get("status", "Belum Tayang")
            if filter_value != "Tampilkan Semua" and status != filter_value: continue
            tag = '';
            if status == "Sedang Tayang": tag = 'sedang_tayang'
            elif status == "Sudah Tayang": tag = 'sudah_tayang'
            values = (dcp.get("judul"), dcp.get("file"), dcp.get("uploader"), dcp.get("no_dcp"), dcp.get("lokasi"), status); self.dcp_tree.insert("", END, iid=i, values=values, tags=(tag,))
    def add_dcp(self): DcpEditor(self, title="Tambah Log DCP Baru", callback=self.load_dcps_to_treeview)
    def edit_dcp(self):
        selected = self.dcp_tree.focus();
        if not selected: messagebox.showwarning("Peringatan", "Pilih data DCP yang akan diedit."); return
        original_index = next((i for i, d in enumerate(self.data_manager.load_dcp_logs()) if d['file'] == self.dcp_tree.item(selected)['values'][1]), None)
        if original_index is None: messagebox.showerror("Error", "Tidak dapat menemukan data asli DCP."); return
        dcp_logs = self.data_manager.load_dcp_logs(); DcpEditor(self, title="Edit Log DCP", dcp_data=dcp_logs[original_index], dcp_index=original_index, callback=self.load_dcps_to_treeview)
    def delete_dcp(self):
        selected = self.dcp_tree.focus();
        if not selected: messagebox.showwarning("Peringatan", "Pilih data DCP yang akan dihapus."); return
        if messagebox.askyesno("Konfirmasi", "Yakin ingin menghapus data DCP ini?"):
            original_index = next((i for i, d in enumerate(self.data_manager.load_dcp_logs()) if d['file'] == self.dcp_tree.item(selected)['values'][1]), None)
            if original_index is None: messagebox.showerror("Error", "Tidak dapat menemukan data asli DCP."); return
            dcp_logs = self.data_manager.load_dcp_logs(); dcp_logs.pop(original_index); self.data_manager.save_dcp_logs(dcp_logs); self.load_dcps_to_treeview()
    def on_dcp_status_click(self, event):
        if self.dcp_tree.identify("region", event.x, event.y) != "cell" or self.dcp_tree.identify_column(event.x) != "#6": return
        selected_item = self.dcp_tree.focus();
        if not selected_item: return
        original_index = next((i for i, d in enumerate(self.data_manager.load_dcp_logs()) if d['file'] == self.dcp_tree.item(selected_item)['values'][1]), None)
        if original_index is None: return
        dcp_logs = self.data_manager.load_dcp_logs(); current_status = dcp_logs[original_index].get("status", "Belum Tayang"); statuses = ["Belum Tayang", "Sedang Tayang", "Sudah Tayang"]
        try: new_status = statuses[(statuses.index(current_status) + 1) % len(statuses)]
        except ValueError: new_status = "Sedang Tayang"
        dcp_logs[original_index]["status"] = new_status; self.data_manager.save_dcp_logs(dcp_logs); self.load_dcps_to_treeview()
    def load_fpkb_to_treeview(self):
        for item in self.fpkb_tree.get_children(): self.fpkb_tree.delete(item)
        fpkb_list = self.data_manager.load_fpkb(); filter_value = self.fpkb_filter_var.get()
        for i, item in enumerate(fpkb_list):
            is_received = "nama_penerima" in item
            if (filter_value == "Belum Diterima" and is_received) or \
               (filter_value == "Sudah Diterima" and not is_received):
                continue
            tags = []; status_fpkb = item.get("status_fpkb", "Belum Dibuat")
            if status_fpkb == "Sudah Dibuat": tags.append('fpkb_sudah')
            else: tags.append('fpkb_belum')
            status_penerimaan_text = "Belum Diterima"
            if is_received:
                tags.append('diterima'); status_penerimaan_text = f"Diterima oleh {item['nama_penerima']} pada {item['tanggal_penerimaan']}"
            items_str = ", ".join([f"{d.get('nama_barang', '')} (Qty: {d.get('quantity', 0)})" for d in item.get("items", [])])
            values = (item.get("tanggal"), items_str, status_fpkb, status_penerimaan_text)
            self.fpkb_tree.insert("", END, iid=i, values=values, tags=tags)
    def on_fpkb_cell_click(self, event):
        if self.fpkb_tree.identify("region", event.x, event.y) != "cell": return
        selected_iid = self.fpkb_tree.focus()
        if not selected_iid: return
        fpkb_index = int(selected_iid)
        column = self.fpkb_tree.identify_column(event.x)
        if column == "#4":
            x, y, width, height = self.fpkb_tree.bbox(selected_iid, column)
            self.show_fpkb_status_menu(fpkb_index, x, y + height)
    def show_fpkb_status_menu(self, fpkb_index, x, y):
        menu = ttk.Menu(self, tearoff=0)
        menu.add_command(label="Belum Dibuat", command=lambda: self.set_fpkb_status(fpkb_index, "Belum Dibuat"))
        menu.add_command(label="Sudah Dibuat", command=lambda: self.set_fpkb_status(fpkb_index, "Sudah Dibuat"))
        menu.post(self.fpkb_tree.winfo_rootx() + x, self.fpkb_tree.winfo_rooty() + y)
    def set_fpkb_status(self, fpkb_index, status):
        fpkb_list = self.data_manager.load_fpkb()
        fpkb_list[fpkb_index]["status_fpkb"] = status
        self.data_manager.save_fpkb(fpkb_list); self.load_fpkb_to_treeview()
    def update_receive_button_state(self, event=None):
        selected_items = self.fpkb_tree.selection()
        if selected_items:
            first_selected = selected_items[0]
            fpkb_list = self.data_manager.load_fpkb()
            if int(first_selected) < len(fpkb_list) and "nama_penerima" not in fpkb_list[int(first_selected)]:
                self.btn_terima_barang.config(state="normal")
                return
        self.btn_terima_barang.config(state="disabled")
    def receive_selected_fpkb(self):
        selected = self.fpkb_tree.selection()
        if not selected: return
        fpkb_index = int(selected[0])
        FpkbReceiptEditor(self, "Form Terima Barang", self.load_fpkb_to_treeview, fpkb_index)
    def add_fpkb(self): FpkbEditor(self, "Tambah FPKB Baru", self.load_fpkb_to_treeview)
    def show_disclaimer(self):
        first_run_file = self.data_manager.config_dir / ".first_run"
        if not first_run_file.exists(): messagebox.showwarning("Disclaimer", "Aplikasi ini menggunakan automasi browser..."); first_run_file.touch()

class StudioEditor(ttk.Toplevel):
    def __init__(self, parent, title, callback, studio_data=None, studio_index=None):
        super().__init__(parent); self.title(title); self.parent = parent; self.callback = callback; self.studio_data = studio_data or {}; self.studio_index = studio_index; self.geometry("500x300"); self.create_form(); self.load_data()
    def create_form(self):
        frame = ttk.Frame(self, padding=20); frame.pack(fill=BOTH, expand=True); ttk.Label(frame, text="Nama Studio:").grid(row=0, column=0, sticky=W, pady=5); self.name_entry = ttk.Entry(frame, width=40); self.name_entry.grid(row=0, column=1, sticky=EW); ttk.Label(frame, text="URL Lengkap:").grid(row=1, column=0, sticky=W, pady=5); self.url_entry = ttk.Entry(frame, width=40); self.url_entry.grid(row=1, column=1, sticky=EW); ttk.Label(frame, text="Format Audio:").grid(row=2, column=0, sticky=W, pady=5); formats = ["Dolby 7.1", "Dolby 5.1", "Atmos", "Lainnya"]; self.format_combo = ttk.Combobox(frame, values=formats, state="readonly"); self.format_combo.grid(row=2, column=1, sticky=EW); self.enabled_var = ttk.BooleanVar(value=True); ttk.Checkbutton(frame, text="Aktifkan studio ini", variable=self.enabled_var, style="success.TCheckbutton").grid(row=3, column=1, sticky=W, pady=10); btn_save = ttk.Button(frame, text="Simpan", command=self.save, style="success.TButton"); btn_save.grid(row=4, column=1, sticky=E, pady=20)
    def load_data(self):
        if self.studio_data: self.name_entry.insert(0, self.studio_data.get("name", "")); self.url_entry.insert(0, self.studio_data.get("url", "")); self.format_combo.set(self.studio_data.get("format", "")); self.enabled_var.set(self.studio_data.get("enabled", True))
    def save(self):
        new_data = {"name": self.name_entry.get(), "url": self.url_entry.get(), "format": self.format_combo.get(), "enabled": self.enabled_var.get()};
        if not new_data["name"] or not new_data["url"]: messagebox.showerror("Error", "Nama Studio dan URL tidak boleh kosong."); return
        studios = self.parent.data_manager.load_studios();
        if self.studio_index is not None: studios[self.studio_index] = new_data
        else: studios.append(new_data)
        self.parent.data_manager.save_studios(studios); self.callback(); self.destroy()

class DcpEditor(ttk.Toplevel):
    def __init__(self, parent, title, callback, dcp_data=None, dcp_index=None):
        super().__init__(parent); self.title(title); self.parent = parent; self.callback = callback; self.dcp_data = dcp_data or {}; self.dcp_index = dcp_index; self.geometry("600x400"); self.create_form(); self.load_data()
    def create_form(self):
        frame = ttk.Frame(self, padding=20); frame.pack(fill=BOTH, expand=True); frame.columnconfigure(1, weight=1); vcmd = (self.register(self.validate_number), '%P')
        ttk.Label(frame, text="Judul Film:").grid(row=0, column=0, sticky=W, pady=5); self.judul_entry = ttk.Entry(frame); self.judul_entry.grid(row=0, column=1, sticky=EW, pady=5)
        ttk.Label(frame, text="Nama File DCP:").grid(row=1, column=0, sticky=W, pady=5); self.file_entry = ttk.Entry(frame); self.file_entry.grid(row=1, column=1, sticky=EW, pady=5)
        ttk.Label(frame, text="Uploader:").grid(row=2, column=0, sticky=W, pady=5); technicians = self.parent.data_manager.load_technicians(); self.uploader_combo = ttk.Combobox(frame, values=technicians, state="readonly"); self.uploader_combo.grid(row=2, column=1, sticky=EW, pady=5)
        ttk.Label(frame, text="Nomor DCP:").grid(row=3, column=0, sticky=W, pady=5); self.no_dcp_entry = ttk.Entry(frame, validate='key', validatecommand=vcmd); self.no_dcp_entry.grid(row=3, column=1, sticky=EW, pady=5)
        ttk.Label(frame, text="Lokasi Ingest:").grid(row=4, column=0, sticky=W, pady=5); locations = ["Server", "LMS"]; self.lokasi_combo = ttk.Combobox(frame, values=locations, state="readonly"); self.lokasi_combo.grid(row=4, column=1, sticky=EW, pady=5)
        btn_save = ttk.Button(frame, text="Simpan", command=self.save, style="success.TButton"); btn_save.grid(row=5, column=1, sticky=E, pady=20)
    def validate_number(self, value_if_allowed): return value_if_allowed.isdigit() or value_if_allowed == ""
    def load_data(self):
        if self.dcp_data: self.judul_entry.insert(0, self.dcp_data.get("judul", "")); self.file_entry.insert(0, self.dcp_data.get("file", "")); self.uploader_combo.set(self.dcp_data.get("uploader", "")); self.no_dcp_entry.insert(0, self.dcp_data.get("no_dcp", "")); self.lokasi_combo.set(self.dcp_data.get("lokasi", ""))
    def save(self):
        new_data = {"judul": self.judul_entry.get(), "file": self.file_entry.get(), "uploader": self.uploader_combo.get(), "no_dcp": self.no_dcp_entry.get(), "lokasi": self.lokasi_combo.get()};
        if not new_data["judul"] or not new_data["file"]: messagebox.showerror("Error", "Judul Film dan Nama File tidak boleh kosong.", parent=self); return
        dcp_logs = self.parent.data_manager.load_dcp_logs()
        if self.dcp_index is not None: new_data["status"] = self.dcp_data.get("status", "Belum Tayang")
        else: new_data["status"] = "Belum Tayang"
        if self.dcp_index is not None: dcp_logs[self.dcp_index] = new_data
        else: dcp_logs.append(new_data)
        self.parent.data_manager.save_dcp_logs(dcp_logs); self.callback(); self.destroy()

class FpkbEditor(ttk.Toplevel):
    def __init__(self, parent, title, callback):
        super().__init__(parent); self.title(title); self.parent = parent; self.callback = callback
        self.geometry("600x400"); self.item_rows = []
        self.create_form()
    def create_form(self):
        main_frame = ttk.Frame(self, padding=20); main_frame.pack(fill=BOTH, expand=True)
        top_frame = ttk.Frame(main_frame); top_frame.pack(fill=X, pady=(0, 15))
        ttk.Label(top_frame, text="Tanggal Permintaan:").pack(side=LEFT, padx=(0, 10))
        self.tanggal_entry = DateEntry(top_frame, bootstyle="primary"); self.tanggal_entry.pack(side=LEFT)
        items_frame = ttk.LabelFrame(main_frame, text="Daftar Item"); items_frame.pack(fill=BOTH, expand=True)
        self.canvas = ttk.Canvas(items_frame); self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(items_frame, orient=VERTICAL, command=self.canvas.yview); scrollbar.pack(side=RIGHT, fill=Y)
        self.scrollable_frame = ttk.Frame(self.canvas); self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw"); self.canvas.configure(yscrollcommand=scrollbar.set)
        button_frame = ttk.Frame(main_frame); button_frame.pack(fill=X, pady=(10, 0))
        btn_add_item = ttk.Button(button_frame, text="+ Tambah Item", command=self.add_item_row, style="success.Outline.TButton"); btn_add_item.pack(side=LEFT)
        btn_save = ttk.Button(button_frame, text="Simpan FPKB", command=self.save, style="success.TButton"); btn_save.pack(side=RIGHT)
        self.add_item_row()
    def add_item_row(self, item_data=None):
        row_frame = ttk.Frame(self.scrollable_frame); row_frame.pack(fill=X, pady=2, padx=5)
        barang_entry = ttk.Entry(row_frame, width=40); barang_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        ttk.Label(row_frame, text="Qty:").pack(side=LEFT); qty_entry = ttk.Entry(row_frame, width=5); qty_entry.pack(side=LEFT, padx=5)
        btn_remove = ttk.Button(row_frame, text="-", command=lambda rf=row_frame: self.remove_item_row(rf), style="danger.TButton", width=2); btn_remove.pack(side=LEFT)
        self.item_rows.append((row_frame, barang_entry, qty_entry))
    def remove_item_row(self, row_frame):
        for i, (frame, _, _) in enumerate(self.item_rows):
            if frame == row_frame: self.item_rows.pop(i); break
        row_frame.destroy()
    def save(self):
        items = []
        for _, barang_entry, qty_entry in self.item_rows:
            barang = barang_entry.get().strip(); qty = qty_entry.get().strip()
            if barang and qty.isdigit() and int(qty) > 0:
                items.append({"nama_barang": barang, "quantity": int(qty)})
        if not items: messagebox.showerror("Error", "Tambahkan setidaknya satu item yang valid.", parent=self); return
        new_data = {"tanggal": self.tanggal_entry.entry.get(), "items": items, "status_fpkb": "Belum Dibuat"}
        fpkb_list = self.parent.data_manager.load_fpkb(); fpkb_list.append(new_data)
        self.parent.data_manager.save_fpkb(fpkb_list); self.callback(); self.destroy()

class FpkbReceiptEditor(ttk.Toplevel):
    def __init__(self, parent, title, callback, fpkb_index):
        super().__init__(parent); self.title(title); self.parent = parent; self.callback = callback; self.fpkb_index = fpkb_index
        self.geometry("450x250"); self.create_form()
    def create_form(self):
        frame = ttk.Frame(self, padding=20); frame.pack(fill=BOTH, expand=True); frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Nama Penerima:").grid(row=0, column=0, sticky=W, pady=5); technicians = self.parent.data_manager.load_technicians(); self.penerima_combo = ttk.Combobox(frame, values=technicians, state="readonly"); self.penerima_combo.grid(row=0, column=1, sticky=EW, pady=5)
        ttk.Label(frame, text="Tanggal Terima:").grid(row=1, column=0, sticky=W, pady=5); self.tanggal_entry = DateEntry(frame, bootstyle="primary"); self.tanggal_entry.grid(row=1, column=1, sticky=EW, pady=5)
        self.sesuai_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Barang sudah sesuai?", variable=self.sesuai_var, style="success.TCheckbutton").grid(row=2, column=1, sticky=W, pady=10)
        btn_save = ttk.Button(frame, text="Simpan Penerimaan", command=self.save, style="success.TButton"); btn_save.grid(row=3, column=1, sticky=E, pady=20)
    def save(self):
        if not self.penerima_combo.get(): messagebox.showerror("Error", "Pilih nama penerima.", parent=self); return
        fpkb_list = self.parent.data_manager.load_fpkb()
        fpkb_list[self.fpkb_index].update({"nama_penerima": self.penerima_combo.get(), "tanggal_penerimaan": self.tanggal_entry.entry.get(), "barang_sesuai": self.sesuai_var.get()})
        self.parent.data_manager.save_fpkb(fpkb_list); self.callback(); self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()