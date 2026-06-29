import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tuition_data.json")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        students = data.get("_students", data)
        if not isinstance(students, dict):
            students = {}
        migrated = {}
        for sid, rec in students.items():
            if not isinstance(rec, dict):
                continue
            hist = rec.get("history", [])
            new_hist = []
            for item in hist:
                if isinstance(item, dict) and "amount" in item:
                    new_hist.append(round(float(item["amount"]), 2))
                else:
                    new_hist.append(round(float(item), 2))
            migrated[sid] = {
                "total": float(rec.get("total", 0)),
                "count": int(rec.get("count", len(new_hist))),
                "history": new_hist,
            }
        settings = data.get("_settings", {}) if isinstance(data, dict) else {}
        return {
            "_settings": {
                "tuition_cap": float(settings.get("tuition_cap", 0)),
                "first_after_reset_time": settings.get("first_after_reset_time"),
            },
            "_students": migrated,
        }
    return {
        "_settings": {
            "tuition_cap": 0,
            "first_after_reset_time": None,
        },
        "_students": {},
    }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fmt_time(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)


class TuitionApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("720x480")

        self.data = load_data()

        self.cap_var = tk.StringVar(
            value=str(self.data["_settings"].get("tuition_cap", 0))
        )

        pad = {"padx": 8, "pady": 6}

        cap_frame = ttk.LabelFrame(root, text="学费上限设置")
        cap_frame.pack(fill="x", **pad)
        ttk.Label(cap_frame, text="每位学生累计学费上限 (元, 0 表示不限):").grid(
            row=0, column=0, padx=6, pady=8, sticky="e"
        )
        cap_entry = ttk.Entry(cap_frame, textvariable=self.cap_var, width=20)
        cap_entry.grid(row=0, column=1, padx=6, pady=8)
        ttk.Button(cap_frame, text="保存上限", command=self.save_cap).grid(
            row=0, column=2, padx=8, pady=8
        )
        self.cap_label = ttk.Label(cap_frame, text="", foreground="#d9534f")
        self.cap_label.grid(row=0, column=3, padx=10, pady=8, sticky="w")
        cap_entry.bind("<Return>", lambda e: self.save_cap())
        self.update_cap_label()

        form = ttk.LabelFrame(root, text="录入学费")
        form.pack(fill="x", **pad)

        ttk.Label(form, text="学号:").grid(row=0, column=0, padx=6, pady=8, sticky="e")
        self.id_entry = ttk.Entry(form, width=20)
        self.id_entry.grid(row=0, column=1, padx=6, pady=8)

        ttk.Label(form, text="学费 (元):").grid(row=0, column=2, padx=6, pady=8, sticky="e")
        self.amount_entry = ttk.Entry(form, width=20)
        self.amount_entry.grid(row=0, column=3, padx=6, pady=8)

        ttk.Button(form, text="提交缴费", command=self.add_payment).grid(
            row=0, column=4, padx=10, pady=8
        )
        ttk.Button(form, text="清空全部", command=self.clear_all).grid(
            row=0, column=5, padx=6, pady=8
        )

        tree_frame = ttk.LabelFrame(root, text="缴费记录汇总")
        tree_frame.pack(fill="both", expand=True, **pad)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("sid", "total", "count", "history"),
            show="headings",
        )
        self.tree.heading("sid", text="学号")
        self.tree.heading("total", text="累计学费 (元)")
        self.tree.heading("count", text="缴费次数")
        self.tree.heading("history", text="历次金额 (元)")

        self.tree.column("sid", width=120, anchor="center")
        self.tree.column("total", width=140, anchor="e")
        self.tree.column("count", width=100, anchor="center")
        self.tree.column("history", width=360, anchor="w")

        vs = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        self.total_label = ttk.Label(root, text="", font=("Microsoft YaHei", 11, "bold"))
        self.total_label.pack(anchor="w", padx=10, pady=(0, 6))

        self.id_entry.focus_set()
        self.id_entry.bind("<Return>", lambda e: self.amount_entry.focus_set())
        self.amount_entry.bind("<Return>", lambda e: self.add_payment())

        self.refresh_table()

    def update_title(self):
        t = fmt_time(self.data["_settings"].get("first_after_reset_time"))
        if t:
            self.root.title(f"学费统计工具  (首次记录: {t})")
        else:
            self.root.title("学费统计工具")

    def save_cap(self):
        cap_str = self.cap_var.get().strip()
        try:
            cap = float(cap_str) if cap_str else 0.0
        except ValueError:
            messagebox.showerror("错误", "上限必须是数字")
            return
        if cap < 0:
            messagebox.showerror("错误", "上限不能为负数")
            return
        self.data["_settings"]["tuition_cap"] = round(cap, 2)
        self.cap_var.set(f"{cap:.2f}")
        save_data(self.data)
        self.update_cap_label()

    def update_cap_label(self):
        cap = self.data["_settings"].get("tuition_cap", 0)
        if cap and cap > 0:
            self.cap_label.config(text=f"当前上限: {cap:.2f} 元")
        else:
            self.cap_label.config(text="当前: 不限制")

    def add_payment(self):
        sid = self.id_entry.get().strip()
        amt_str = self.amount_entry.get().strip()

        if not sid:
            messagebox.showwarning("提示", "请输入学号")
            return
        if not amt_str:
            messagebox.showwarning("提示", "请输入学费")
            return

        try:
            amt = float(amt_str)
        except ValueError:
            messagebox.showerror("错误", "学费必须是数字")
            return

        if amt < 0:
            messagebox.showerror("错误", "学费不能为负数")
            return

        now_iso = datetime.now().isoformat(timespec="seconds")

        students = self.data["_students"]
        if sid not in students:
            students[sid] = {"total": 0.0, "count": 0, "history": []}

        new_total = students[sid]["total"] + amt
        cap = self.data["_settings"].get("tuition_cap", 0)
        if cap and cap > 0 and new_total > cap:
            if not messagebox.askyesno(
                "超过学费上限",
                f"学号 {sid} 本次缴费后累计将为 {new_total:.2f} 元，"
                f"已超过上限 {cap:.2f} 元！\n\n是否仍要提交？",
            ):
                return

        students[sid]["total"] = new_total
        students[sid]["count"] += 1
        students[sid]["history"].append(round(amt, 2))

        if not self.data["_settings"].get("first_after_reset_time"):
            self.data["_settings"]["first_after_reset_time"] = now_iso

        save_data(self.data)
        self.refresh_table()

        self.id_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.id_entry.focus_set()

    def clear_all(self):
        if not self.data["_students"]:
            return
        if messagebox.askyesno("确认", "确定要清空全部记录吗？此操作不可撤销。"):
            self.data["_students"] = {}
            self.data["_settings"]["first_after_reset_time"] = None
            save_data(self.data)
            self.refresh_table()

    def refresh_table(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        students = self.data["_students"]
        cap = self.data["_settings"].get("tuition_cap", 0)

        grand = 0.0
        for sid in sorted(students.keys()):
            rec = students[sid]
            grand += rec["total"]
            history_str = " + ".join(f"{a:.2f}" for a in rec["history"])
            tag = ""
            if cap and cap > 0 and rec["total"] > cap:
                tag = "overcap"
            self.tree.insert(
                "",
                "end",
                values=(
                    sid,
                    f"{rec['total']:.2f}",
                    rec["count"],
                    history_str,
                ),
                tags=(tag,) if tag else (),
            )

        self.tree.tag_configure("overcap", background="#fde7e7")

        cap_text = f"  (上限 {cap:.2f} 元)" if cap and cap > 0 else ""
        self.total_label.config(
            text=f"学生人数: {len(students)}    全校累计学费总额: {grand:.2f} 元{cap_text}"
        )

        self.update_title()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    TuitionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
