#!/usr/bin/env python3
import math, random, re, tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

PAGE_SIZE = 512
WALLS, SHELVES, BOOKS, PAGES = 6, 8, 16, 64
PAGES_PER_HEX = WALLS * SHELVES * BOOKS * PAGES
M = 95 ** PAGE_SIZE
K = math.ceil((PAGE_SIZE * math.log(95) - math.log(PAGES_PER_HEX)) / math.log(94))
HEX_COUNT = 94 ** K
TOTAL_ADDRESSES = HEX_COUNT * PAGES_PER_HEX
assert TOTAL_ADDRESSES >= M

B95 = "".join(chr(i) for i in range(32, 127))
B94 = B95.replace(" ", "")
VAL95 = {c: i for i, c in enumerate(B95)}
VAL94 = {c: i for i, c in enumerate(B94)}
ZERO95, ZERO94 = B95[0], B94[0]


def to_base(n, alphabet, zero):
    if n == 0:
        return zero
    digits = []
    while n:
        n, r = divmod(n, len(alphabet))
        digits.append(alphabet[r])
    return "".join(reversed(digits))


def from_base(s, valmap, base):
    n = 0
    for c in s:
        n = n * base + valmap[c]
    return n


def to_b95(n): return to_base(n, B95, ZERO95)
def from_b95(s): return from_base(s, VAL95, 95)
def to_b94(n): return to_base(n, B94, ZERO94)
def from_b94(s): return from_base(s, VAL94, 94)


M2 = M - 2
_a = ((M2 * 6180339887498949) // 10**16) | 1
while math.gcd(_a, M2) != 1:
    _a += 2
_b = ((M2 * 3141592653589793) // 10**16) % M2 or 1
_a_inv = pow(_a, -1, M2)


def permute(x):
    return x if x in (0, M - 1) else 1 + (_a * (x - 1) + _b) % M2


def unpermute(y):
    return y if y in (0, M - 1) else 1 + (_a_inv * ((y - 1) - _b)) % M2


def content_from_index(i):
    if not 0 <= i < M:
        raise ValueError(f"index out of range: {i}")
    return to_b95(i).ljust(PAGE_SIZE, ZERO95)


def index_from_content(c):
    if len(c) != PAGE_SIZE or any(x not in VAL95 for x in c):
        raise ValueError("invalid page")
    return from_b95(c)


def make_hex_id(n):
    if not 0 <= n < HEX_COUNT:
        raise ValueError(f"hex_n out of range: {n}")
    return to_b94(n).rjust(K, ZERO94)


def parse_hex_id(s):
    if len(s) != K or any(c not in VAL94 for c in s):
        raise ValueError(f"invalid ID: {s!r}")
    return from_b94(s)


def make_address(h, w, s, b, p):
    if not (1 <= w <= WALLS and 1 <= s <= SHELVES and 1 <= b <= BOOKS and 1 <= p <= PAGES):
        raise ValueError("components out of range")
    return f"{make_hex_id(h)}-w{w}-s{s}-v{b}-p{p}"


def parse_address(addr):
    m = re.fullmatch(r"(.{%d})-w(\d+)-s(\d+)-v(\d+)-p(\d+)" % K, addr.strip())
    if not m:
        raise ValueError(f"invalid address: {addr!r}")
    h, w, s, v, p = m.groups()
    return parse_hex_id(h), int(w), int(s), int(v), int(p)


def page_index(h, w, s, b, p):
    return (h * PAGES_PER_HEX
            + (w - 1) * SHELVES * BOOKS * PAGES
            + (s - 1) * BOOKS * PAGES
            + (b - 1) * PAGES
            + p - 1)


def index_to_address(idx):
    if not 0 <= idx < TOTAL_ADDRESSES:
        raise ValueError(f"idx out of range: {idx}")
    h, r = divmod(idx, PAGES_PER_HEX)
    w, r = divmod(r, SHELVES * BOOKS * PAGES)
    s, r = divmod(r, BOOKS * PAGES)
    b, p = divmod(r, PAGES)
    return make_address(h, w + 1, s + 1, b + 1, p + 1)


def address_to_index(addr):
    return page_index(*parse_address(addr))


def address_to_content(addr):
    idx = address_to_index(addr)
    if idx >= M:
        raise ValueError("address out of navigable range")
    return content_from_index(unpermute(idx))


def content_to_address(content):
    idx = permute(index_from_content(content))
    if idx >= TOTAL_ADDRESSES:
        raise ValueError("permutation out of range")
    return index_to_address(idx)


def search_prefix(text):
    if not text or text[0] == ZERO95 or len(text) > PAGE_SIZE:
        return None
    if any(c not in VAL95 for c in text):
        return None
    return content_to_address(text.ljust(PAGE_SIZE, ZERO95))


class BabelGUI:
    def __init__(self, root):
        self.root = root
        self.current_addr = None
        root.title("Hierarchical Babel")
        root.geometry("1000x760")
        root.minsize(780, 620)
        root.configure(bg="#111827")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(12, 7))
        style.configure("TLabel", background="#111827", foreground="#e5e7eb", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#111827", foreground="#ffffff", font=("Segoe UI", 18, "bold"))
        style.configure("Muted.TLabel", background="#111827", foreground="#9ca3af", font=("Segoe UI", 9))
        style.configure("Mono.TLabel", background="#1f2937", foreground="#93c5fd", font=("Consolas", 8))

        header = tk.Frame(root, bg="#111827")
        header.pack(fill="x", padx=22, pady=(18, 6))
        ttk.Label(header, text="HIERARCHICAL BABEL", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, style="Muted.TLabel",
                  text=f"hex_id = {K} chars · {PAGES_PER_HEX:,} pages/hex · "
                       f"page = {PAGE_SIZE} chars · endpoint-fixing permutation"
                  ).pack(anchor="w")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=22, pady=12)
        self._build_search_tab(notebook)
        self._build_browse_tab(notebook)

    def _build_search_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#111827")
        notebook.add(tab, text="  🔎  Search  ")

        ttk.Label(tab, text="Text to search (must not start with a space):").pack(anchor="w", padx=14, pady=(14, 4))
        self.search_input = tk.Entry(tab, font=("Consolas", 12), bg="#0b1220",
                                     fg="#ffffff", insertbackground="#ffffff", relief="flat")
        self.search_input.pack(fill="x", padx=14, ipady=8)
        self.search_input.bind("<Return>", lambda e: self.do_search())

        row = tk.Frame(tab, bg="#111827")
        row.pack(fill="x", padx=14, pady=10)
        ttk.Button(row, text="🔎  Search", command=self.do_search).pack(side="left")
        ttk.Button(row, text="Clear", command=self.clear_search).pack(side="left", padx=8)
        self.search_status = ttk.Label(row, text="Ready", style="Muted.TLabel")
        self.search_status.pack(side="right")

        ttk.Label(tab, text="Result:").pack(anchor="w", padx=14, pady=(6, 4))
        self.search_output = ScrolledText(tab, wrap="word", font=("Consolas", 10),
                                          bg="#0b1220", fg="#d1d5db", insertbackground="#ffffff",
                                          relief="flat", padx=14, pady=12, state="disabled")
        self.search_output.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        for tag, color in [("ok", "#86efac"), ("addr", "#93c5fd"),
                           ("err", "#fca5a5"), ("muted", "#9ca3af")]:
            self.search_output.tag_configure(tag, foreground=color)

    def _build_browse_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#111827")
        notebook.add(tab, text="  📖  Browse  ")

        ttk.Label(tab, text=f"Address (hex_id of {K} chars + -w -s -v -p):").pack(anchor="w", padx=14, pady=(14, 4))
        self.address_input = tk.Entry(tab, font=("Consolas", 8), bg="#0b1220",
                                      fg="#ffffff", insertbackground="#ffffff", relief="flat")
        self.address_input.pack(fill="x", padx=14, ipady=8)
        self.address_input.bind("<Return>", lambda e: self.do_browse())

        row = tk.Frame(tab, bg="#111827")
        row.pack(fill="x", padx=14, pady=10)
        for label, command in [("📖  Go", self.do_browse),
                               ("← Previous", lambda: self.do_browse(-1)),
                               ("Next →", lambda: self.do_browse(1)),
                               ("🎲 Random", self.do_random),
                               ("⏮ First", self.do_first),
                               ("Last ⏭", self.do_last)]:
            ttk.Button(row, text=label, command=command).pack(side="left", padx=3)
        self.browse_status = ttk.Label(row, text="Ready", style="Muted.TLabel")
        self.browse_status.pack(side="right")

        info = tk.Frame(tab, bg="#1f2937", highlightthickness=1, highlightbackground="#374151")
        info.pack(fill="x", padx=14, pady=(4, 8))
        self.info_label = ttk.Label(info, text="—", style="Mono.TLabel", wraplength=940, justify="left")
        self.info_label.pack(anchor="w", padx=12, pady=8)

        ttk.Label(tab, text="Content (512 characters):").pack(anchor="w", padx=14)
        self.browse_output = ScrolledText(tab, wrap="char", font=("Consolas", 12),
                                          bg="#0b1220", fg="#d1d5db", insertbackground="#ffffff",
                                          relief="flat", padx=14, pady=12, height=12, state="disabled")
        self.browse_output.pack(fill="both", expand=True, padx=14, pady=(4, 14))

    @staticmethod
    def _write(widget, chunks):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        for text, tag in chunks:
            widget.insert("end", text, tag or "")
        widget.configure(state="disabled")

    def do_search(self):
        text = self.search_input.get()
        if not text:
            return
        address = search_prefix(text)
        if address is None:
            self._write(self.search_output, [
                ("NOT FOUND\n\n", "err"),
                (f"Cannot generate a page starting with {text!r}.\n\n", None),
                ("Reasons:\n", "muted"),
                ("  · Starts with a space (system zero)\n", "muted"),
                ("  · Contains characters outside B95\n", "muted"),
                (f"  · Longer than {PAGE_SIZE} characters\n", "muted"),
            ])
            self.search_status.config(text="Not found")
            return
        self._write(self.search_output, [
            ("✓ FOUND\n\n", "ok"),
            ("Searched text:\n", None), (text + "\n\n", None),
            ("Address:\n", None), (address + "\n\n", "addr"),
            ("Page content (512 chars):\n", None),
            (address_to_content(address) + "\n", "muted"),
        ])
        self.search_status.config(text="Found")

    def clear_search(self):
        self.search_input.delete(0, "end")
        self._write(self.search_output, [])
        self.search_status.config(text="Ready")

    def do_browse(self, delta=0):
        address = self.address_input.get().strip()
        if not address:
            return
        try:
            idx = address_to_index(address)
            if delta:
                idx += delta
                if not 0 <= idx < M:
                    raise ValueError("out of navigable pages range")
                address = index_to_address(idx)
            self._show_address(address)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_random(self):
        self._show_address(index_to_address(random.randrange(M)))

    def do_first(self):
        self._show_address(index_to_address(0))

    def do_last(self):
        self._show_address(index_to_address(M - 1))

    def _show_address(self, address):
        content = address_to_content(address)
        self.current_addr = address
        self.address_input.delete(0, "end")
        self.address_input.insert(0, address)
        h, w, s, b, p = parse_address(address)
        self.info_label.config(
            text=f"hex #{h}   ·   wall {w}/{WALLS}   ·   "
                 f"shelf {s}/{SHELVES}   ·   volume {b}/{BOOKS}   ·   "
                 f"page {p}/{PAGES}")
        self._write(self.browse_output, [(content, None)])
        self.browse_status.config(text="OK")


if __name__ == "__main__":
    root = tk.Tk()
    BabelGUI(root)
    root.mainloop()