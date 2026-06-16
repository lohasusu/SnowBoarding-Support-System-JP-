"""Main tkinter GUI — Ski / Flight / Schedule / Settings tabs.

All tab inputs mirror the website's search form parameters.
"""
from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from desktop_app.core import config as cfg_mod
from desktop_app.core import output as out_mod
from desktop_app.core import scheduler as sch_mod
from desktop_app.core import scrapers as scr_mod
from desktop_app.core.paths import log_path


# Ski regions (matches web/templates/ski.html)
SKI_REGIONS = ["", "北海道", "長野", "新潟", "山形", "青森", "福島"]

# Airport options (matches web/templates/flight.html origin/destination select)
ORIGINS = [
    ("TPE", "桃園 TPE"),
    ("TSA", "松山 TSA"),
    ("KHH", "高雄 KHH"),
    ("RMQ", "台中 RMQ"),
]
DESTINATIONS = [
    ("CTS", "新千歲 (北海道)"),
    ("HKD", "函館"),
    ("KIJ", "新潟"),
    ("AOJ", "青森"),
    ("FKS", "福島"),
    ("SDJ", "仙台 (含山形)"),
    ("NRT", "成田 (東京)"),
    ("HND", "羽田 (東京)"),
    ("KIX", "關西 (大阪)"),
    ("NGO", "中部 (名古屋)"),
]


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = cfg_mod.load()
        self.root.title("SnowTrip 桌面版 — 雪票 + 機票 爬蟲")
        self.root.geometry("780x620")

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_ski_tab()
        self._build_flight_tab()
        self._build_schedule_tab()
        self._build_settings_tab()
        self._build_log_panel()

        self._refresh_schedule_list()

    # ── Logging panel (shared across tabs) ─────────────────────────────────────
    def _build_log_panel(self):
        frm = ttk.LabelFrame(self.root, text="執行日誌")
        frm.pack(fill="x", padx=10, pady=(0, 10))
        self.log_text = tk.Text(frm, height=8, font=("Consolas", 9))
        self.log_text.pack(fill="x", padx=5, pady=5)
        self.log_text.configure(state="disabled")

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        # Persist
        try:
            with open(log_path(), "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    # ── Ski tab ────────────────────────────────────────────────────────────────
    def _build_ski_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="⛷  雪票查詢")

        ttk.Label(f, text="地區（留空 = 全部）：").grid(row=0, column=0, sticky="w", padx=8, pady=10)
        self.ski_region = tk.StringVar(value=self.cfg.ski.region)
        ttk.Combobox(f, textvariable=self.ski_region, values=SKI_REGIONS, width=20,
                     state="readonly").grid(row=0, column=1, sticky="w", padx=8)

        ttk.Label(f, text="雪場名稱（部分比對，可空）：").grid(row=1, column=0, sticky="w", padx=8, pady=10)
        self.ski_name = tk.StringVar(value=self.cfg.ski.name)
        ttk.Entry(f, textvariable=self.ski_name, width=30).grid(row=1, column=1, sticky="w", padx=8)

        ttk.Button(f, text="▶  立即查詢並輸出 Excel",
                   command=self._run_ski).grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Label(f, text="（查詢後 Excel 會放到「設定」分頁所選的輸出資料夾）",
                  foreground="#666").grid(row=3, column=0, columnspan=2, padx=8)

    def _run_ski(self):
        self._save_current_to_cfg()
        region = self.ski_region.get().strip()
        name = self.ski_name.get().strip()
        self.log(f"⛷ 雪票查詢 region={region or '全部'} name={name or '無'}")

        def worker():
            try:
                items = scr_mod.run_ski(region=region, name=name, progress_cb=self.log)
                out_dir = Path(self.cfg.output_dir)
                fp = out_mod.write_ski(items, out_dir, {"region": region, "name": name})
                self.log(f"✅ 已輸出: {fp}")
                self.root.after(0, lambda: messagebox.showinfo("查詢完成",
                    f"雪票查詢完成 — 共 {len(items)} 筆\n\n輸出: {fp}"))
            except Exception as e:
                self.log(f"❌ 失敗: {e}")
                self.root.after(0, lambda: messagebox.showerror("查詢失敗", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    # ── Flight tab ─────────────────────────────────────────────────────────────
    def _build_flight_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="✈  機票查詢")

        row = 0
        ttk.Label(f, text="出發機場：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.fl_origin = tk.StringVar(value=self.cfg.flight.origin)
        cb_o = ttk.Combobox(f, textvariable=self.fl_origin,
                            values=[f"{c} — {n}" for c, n in ORIGINS],
                            state="readonly", width=24)
        cb_o.grid(row=row, column=1, sticky="w", padx=8)
        # Display→code map
        self._origin_display_to_code = {f"{c} — {n}": c for c, n in ORIGINS}
        for disp, code in self._origin_display_to_code.items():
            if code == self.cfg.flight.origin:
                cb_o.set(disp); break

        row += 1
        ttk.Label(f, text="目的地：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.fl_dest_display = tk.StringVar()
        cb_d = ttk.Combobox(f, textvariable=self.fl_dest_display,
                            values=[f"{c} — {n}" for c, n in DESTINATIONS],
                            state="readonly", width=24)
        cb_d.grid(row=row, column=1, sticky="w", padx=8)
        self._dest_display_to_code = {f"{c} — {n}": (c, n) for c, n in DESTINATIONS}
        for disp, (code, name) in self._dest_display_to_code.items():
            if code == self.cfg.flight.destination:
                cb_d.set(disp); break

        row += 1
        ttk.Label(f, text="去程日期 (YYYY-MM-DD)：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.fl_dep = tk.StringVar(value=self.cfg.flight.departure)
        ttk.Entry(f, textvariable=self.fl_dep, width=15).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        ttk.Label(f, text="回程日期 (留空 = 單程)：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.fl_ret = tk.StringVar(value=self.cfg.flight.ret_date)
        ttk.Entry(f, textvariable=self.fl_ret, width=15).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        ttk.Label(f, text="乘客數：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.fl_adults = tk.IntVar(value=self.cfg.flight.adults)
        ttk.Spinbox(f, textvariable=self.fl_adults, from_=1, to=9,
                    width=8).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        ttk.Button(f, text="▶  立即搜尋並輸出 Excel",
                   command=self._run_flight).grid(row=row, column=0, columnspan=2, pady=20)

        row += 1
        ttk.Label(f, text="（若已在「設定」設定 SerpAPI Key，會優先用 SerpAPI；否則 fast-flights fallback）",
                  foreground="#666", wraplength=560).grid(row=row, column=0, columnspan=2, padx=8)

    def _resolve_flight_inputs(self):
        ori_disp = self.fl_origin.get()
        dst_disp = self.fl_dest_display.get()
        origin = self._origin_display_to_code.get(ori_disp, ori_disp[:3] if ori_disp else "TPE")
        if dst_disp in self._dest_display_to_code:
            destination, dest_name = self._dest_display_to_code[dst_disp]
        else:
            destination, dest_name = self.cfg.flight.destination, self.cfg.flight.dest_name
        return origin, destination, dest_name

    def _run_flight(self):
        self._save_current_to_cfg()
        origin, destination, dest_name = self._resolve_flight_inputs()
        dep = self.fl_dep.get().strip()
        ret = self.fl_ret.get().strip()
        if not dep:
            messagebox.showerror("缺少日期", "請輸入去程日期 (YYYY-MM-DD)")
            return
        adults = int(self.fl_adults.get() or 1)
        self.log(f"✈ 機票 {origin}→{destination} ({dest_name}) {dep}"
                 + (f"/{ret}" if ret else "") + f" adults={adults}")

        def worker():
            try:
                items = scr_mod.run_flight(
                    origin=origin, destination=destination, dest_name=dest_name,
                    departure=dep, ret_date=ret, adults=adults,
                    currency=self.cfg.flight.currency,
                    serpapi_key=self.cfg.serpapi_key,
                    progress_cb=self.log,
                )
                out_dir = Path(self.cfg.output_dir)
                fp = out_mod.write_flight(items, out_dir, {
                    "origin": origin, "destination": destination,
                    "dest_name": dest_name, "departure": dep, "ret_date": ret,
                    "adults": adults,
                })
                self.log(f"✅ 已輸出: {fp}")
                self.root.after(0, lambda: messagebox.showinfo("查詢完成",
                    f"機票查詢完成 — 共 {len(items)} 筆\n\n輸出: {fp}"))
            except Exception as e:
                self.log(f"❌ 失敗: {e}")
                self.root.after(0, lambda: messagebox.showerror("查詢失敗", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    # ── Schedule tab ───────────────────────────────────────────────────────────
    def _build_schedule_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="🕒  排程設定")

        row = 0
        ttk.Label(f, text="任務名稱：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.sch_name = tk.StringVar(value=self.cfg.schedule.task_name)
        ttk.Entry(f, textvariable=self.sch_name, width=30).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        ttk.Label(f, text="任務類型：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.sch_type = tk.StringVar(value=self.cfg.schedule.task_type)
        ttk.Combobox(f, textvariable=self.sch_type, values=["ski", "flight"],
                     state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        ttk.Label(f, text="頻率：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.sch_freq = tk.StringVar(value=self.cfg.schedule.frequency)
        ttk.Combobox(f, textvariable=self.sch_freq, values=["DAILY", "WEEKLY", "ONCE"],
                     state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        ttk.Label(f, text="星期（WEEKLY 用，逗號分隔）：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.sch_days = tk.StringVar(value=self.cfg.schedule.days)
        ttk.Entry(f, textvariable=self.sch_days, width=30).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        ttk.Label(f, text="執行時間 (HH:MM)：").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.sch_time = tk.StringVar(value=self.cfg.schedule.time_hhmm)
        ttk.Entry(f, textvariable=self.sch_time, width=10).grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        btnf = ttk.Frame(f)
        btnf.grid(row=row, column=0, columnspan=2, pady=14)
        ttk.Button(btnf, text="💾  建立 / 更新排程", command=self._create_schedule).pack(side="left", padx=4)
        ttk.Button(btnf, text="🗑  刪除選取排程", command=self._delete_schedule).pack(side="left", padx=4)
        ttk.Button(btnf, text="🔄  重新整理清單", command=self._refresh_schedule_list).pack(side="left", padx=4)

        row += 1
        ttk.Label(f, text="目前已建立的 SnowTrip 排程：", foreground="#1F4E79",
                  font=("", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=(10, 4))

        row += 1
        cols = ("name", "next_run", "status")
        self.sch_tree = ttk.Treeview(f, columns=cols, show="headings", height=6)
        for c, label, w in zip(cols, ("名稱", "下次執行", "狀態"), (240, 200, 100)):
            self.sch_tree.heading(c, text=label)
            self.sch_tree.column(c, width=w)
        self.sch_tree.grid(row=row, column=0, columnspan=2, sticky="ew", padx=8)

        row += 1
        ttk.Label(f,
            text="排程任務透過 Windows 工作排程器執行 — 即使關閉本應用也會準時跑。\n"
                 "首次安裝或變更參數後需重新建立排程，讀取的是最新儲存的設定。",
            foreground="#666", wraplength=720).grid(row=row, column=0, columnspan=2,
                                                    sticky="w", padx=8, pady=(8, 8))

    def _create_schedule(self):
        self._save_current_to_cfg()
        ok, msg = sch_mod.create_task(
            task_name=self.sch_name.get().strip(),
            task_type=self.sch_type.get(),
            frequency=self.sch_freq.get(),
            time_hhmm=self.sch_time.get().strip(),
            days=self.sch_days.get().strip() or "MON,TUE,WED,THU,FRI,SAT,SUN",
        )
        self.log(msg)
        if ok:
            messagebox.showinfo("排程已建立", msg)
        else:
            messagebox.showerror("排程建立失敗", msg)
        self._refresh_schedule_list()

    def _delete_schedule(self):
        sel = self.sch_tree.selection()
        if not sel:
            messagebox.showinfo("請先選取", "請在下方清單選一個排程再刪除")
            return
        name = self.sch_tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("確認刪除", f"確定刪除排程「{name}」？"):
            return
        ok, msg = sch_mod.delete_task(name)
        self.log(msg)
        if ok:
            messagebox.showinfo("已刪除", msg)
        else:
            messagebox.showerror("刪除失敗", msg)
        self._refresh_schedule_list()

    def _refresh_schedule_list(self):
        if not hasattr(self, "sch_tree"):
            return
        for i in self.sch_tree.get_children():
            self.sch_tree.delete(i)
        for t in sch_mod.list_tasks():
            self.sch_tree.insert("", "end", values=(t.name, t.next_run, t.status))

    # ── Settings tab ───────────────────────────────────────────────────────────
    def _build_settings_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="⚙  設定")

        ttk.Label(f, text="輸出資料夾：").grid(row=0, column=0, sticky="w", padx=8, pady=10)
        self.cfg_out = tk.StringVar(value=self.cfg.output_dir)
        ttk.Entry(f, textvariable=self.cfg_out, width=50).grid(row=0, column=1, sticky="w", padx=8)
        ttk.Button(f, text="瀏覽…", command=self._pick_out_dir).grid(row=0, column=2, padx=4)

        ttk.Label(f, text="SerpAPI Key（機票查詢，選填）：").grid(row=1, column=0, sticky="w", padx=8, pady=10)
        self.cfg_key = tk.StringVar(value=self.cfg.serpapi_key)
        ttk.Entry(f, textvariable=self.cfg_key, width=50, show="*").grid(row=1, column=1, sticky="w", padx=8)

        ttk.Button(f, text="💾  儲存設定", command=self._save_settings).grid(row=2, column=0, columnspan=3, pady=20)

        ttk.Label(f, text=f"設定檔位置: {cfg_mod.config_path()}",
                  foreground="#666").grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=4)
        ttk.Label(f, text=f"日誌位置:   {log_path()}",
                  foreground="#666").grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=4)

    def _pick_out_dir(self):
        d = filedialog.askdirectory(initialdir=self.cfg_out.get() or str(Path.home()))
        if d:
            self.cfg_out.set(d)

    def _save_settings(self):
        self._save_current_to_cfg()
        self.log(f"⚙ 設定已儲存 → {cfg_mod.config_path()}")
        messagebox.showinfo("已儲存", "設定已寫入 config.json")

    # ── Persistence helper ────────────────────────────────────────────────────
    def _save_current_to_cfg(self):
        origin, destination, dest_name = self._resolve_flight_inputs()
        self.cfg.output_dir = self.cfg_out.get().strip() or self.cfg.output_dir
        self.cfg.serpapi_key = self.cfg_key.get().strip()
        self.cfg.ski.region = self.ski_region.get().strip()
        self.cfg.ski.name = self.ski_name.get().strip()
        self.cfg.flight.origin = origin
        self.cfg.flight.destination = destination
        self.cfg.flight.dest_name = dest_name
        self.cfg.flight.departure = self.fl_dep.get().strip()
        self.cfg.flight.ret_date = self.fl_ret.get().strip()
        try:
            self.cfg.flight.adults = int(self.fl_adults.get() or 1)
        except Exception:
            self.cfg.flight.adults = 1
        self.cfg.schedule.task_name = self.sch_name.get().strip()
        self.cfg.schedule.task_type = self.sch_type.get()
        self.cfg.schedule.frequency = self.sch_freq.get()
        self.cfg.schedule.days = self.sch_days.get().strip()
        self.cfg.schedule.time_hhmm = self.sch_time.get().strip()
        cfg_mod.save(self.cfg)


def launch():
    root = tk.Tk()
    App(root)
    root.mainloop()
