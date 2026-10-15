"""Small CustomTkinter frontend for the GoodbyeDPI executable.

Install the UI dependency with ``python -m pip install customtkinter``.
Place this script beside goodbyedpi.exe and run it as Administrator.
"""

import ctypes
import os
import subprocess
import sys
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox


MODES = {
    "Mode 1: Standard Bypass (-p -r -s -e 1)": ["-p", "-r", "-s", "-e", "1"],
    "Mode 2: Deep Bypass (-p -r -s -e 1 -f 1 -k 1)": [
        "-p", "-r", "-s", "-e", "1", "-f", "1", "-k", "1"
    ],
    "Mode 3: Alternative (-p -r -s -e 2)": ["-p", "-r", "-s", "-e", "2"],
}

BACKGROUND = "#111713"
SURFACE = "#1A241E"
TEXT = "#E8F0EA"
MUTED = "#9AA99D"
GREEN = "#45C47A"
RED = "#F06B68"


class GoodbyeDPIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GoodbyeDPI Control")
        self.geometry("540x430")
        self.resizable(False, False)
        self.configure(fg_color=BACKGROUND)

        # Resolve the executable beside this script, independent of the shell's cwd.
        self.app_directory = Path(__file__).resolve().parent
        self.exe_path = self.app_directory / "goodbyedpi.exe"
        self.process = None
        self.closing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(500, self._poll_process)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=28, pady=(26, 12), sticky="ew")

        ctk.CTkLabel(
            header,
            text="GoodbyeDPI",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="TURKEY PRESETS  /  PROCESS CONTROL",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=MUTED,
        ).pack(anchor="w", pady=(3, 0))

        content = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12)
        content.grid(row=1, column=0, padx=28, pady=10, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content,
            text="Select Mode / Preset",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, padx=22, pady=(22, 8), sticky="w")

        self.mode_menu = ctk.CTkOptionMenu(
            content,
            values=list(MODES),
            height=40,
            fg_color="#29372E",
            button_color="#384B3D",
            button_hover_color="#496451",
            text_color=TEXT,
            dropdown_fg_color=SURFACE,
            dropdown_text_color=TEXT,
            dropdown_hover_color="#34483A",
        )
        self.mode_menu.grid(row=1, column=0, padx=22, sticky="ew")

        self.dns_enabled = ctk.BooleanVar(value=False)
        self.dns_checkbox = ctk.CTkCheckBox(
            content,
            text="Enable Advanced DNS Redirect (--dns-addr 1.1.1.1)",
            variable=self.dns_enabled,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT,
            fg_color=GREEN,
            hover_color="#39A968",
            border_color="#65766A",
            checkmark_color=BACKGROUND,
        )
        self.dns_checkbox.grid(row=2, column=0, padx=22, pady=(22, 24), sticky="w")

        self.toggle_button = ctk.CTkButton(
            content,
            text="ACTIVATE",
            command=self._toggle_service,
            height=48,
            corner_radius=8,
            fg_color=GREEN,
            hover_color="#39A968",
            text_color="#0B1710",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        )
        self.toggle_button.grid(row=3, column=0, padx=22, sticky="ew")

        status_row = ctk.CTkFrame(content, fg_color="transparent")
        status_row.grid(row=4, column=0, padx=22, pady=(20, 18), sticky="w")
        self.status_dot = ctk.CTkLabel(
            status_row, text="●", font=ctk.CTkFont(size=16), text_color=RED
        )
        self.status_dot.pack(side="left", padx=(0, 8))
        self.status_label = ctk.CTkLabel(
            status_row,
            text="Status: Disconnected",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=RED,
        )
        self.status_label.pack(side="left")

        self.executable_label = ctk.CTkLabel(
            self,
            text=f"Executable: {self.exe_path}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=MUTED,
            anchor="w",
        )
        self.executable_label.grid(row=2, column=0, padx=30, pady=(0, 18), sticky="ew")

    def _is_admin(self):
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False

    def _restart_as_admin(self):
        """Offer a UAC relaunch, preserving whether Python or a packaged app is used."""
        if not messagebox.askyesno(
            "Administrator privileges required",
            "GoodbyeDPI needs administrator privileges to load its network driver.\n\n"
            "Restart this application as Administrator?",
            parent=self,
        ):
            return False

        if getattr(sys, "frozen", False):
            executable = sys.executable
            parameters = subprocess.list2cmdline(sys.argv[1:])
        else:
            executable = sys.executable
            parameters = subprocess.list2cmdline(sys.argv)

        try:
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", executable, parameters, str(self.app_directory), 1
            )
        except (AttributeError, OSError) as error:
            messagebox.showerror("Could not elevate", str(error), parent=self)
            return False

        if result <= 32:
            messagebox.showerror(
                "Could not elevate",
                "Windows could not restart the application with administrator privileges.",
                parent=self,
            )
            return False

        self.closing = True
        self.destroy()
        return True

    def _toggle_service(self):
        if self.process is not None and self.process.poll() is None:
            self._stop_process()
        else:
            self._start_process()

    def _start_process(self):
        # Check the adjacent executable explicitly so a missing file is a friendly UI error.
        if not os.path.exists(self.exe_path):
            messagebox.showerror(
                "Executable not found",
                f"goodbyedpi.exe was not found beside this application:\n{self.exe_path}",
                parent=self,
            )
            return

        if not self._is_admin():
            self._restart_as_admin()
            return

        arguments = list(MODES[self.mode_menu.get()])
        if self.dns_enabled.get():
            arguments.extend(["--dns-addr", "1.1.1.1", "--dns-port", "53"])

        try:
            self.process = subprocess.Popen(
                [str(self.exe_path), *arguments],
                cwd=str(self.app_directory),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.SubprocessError) as error:
            self.process = None
            messagebox.showerror(
                "Could not start GoodbyeDPI",
                f"Windows could not start the process.\n\n{error}",
                parent=self,
            )
            return

        self._set_running_ui(True)
        self.after(250, self._poll_process)

    def _stop_process(self):
        process = self.process
        if process is None:
            self._set_running_ui(False)
            return

        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
        except (OSError, subprocess.SubprocessError) as error:
            messagebox.showerror(
                "Could not stop GoodbyeDPI",
                f"The process could not be stopped cleanly.\n\n{error}",
                parent=self,
            )
        finally:
            self.process = None
            self._set_running_ui(False)

    def _set_running_ui(self, running):
        if running:
            self.status_dot.configure(text_color=GREEN)
            self.status_label.configure(text="Status: Connected", text_color=GREEN)
            self.toggle_button.configure(
                text="DEACTIVATE", fg_color=RED, hover_color="#D95552", text_color="#200C0B"
            )
            self.mode_menu.configure(state="disabled")
            self.dns_checkbox.configure(state="disabled")
        else:
            self.status_dot.configure(text_color=RED)
            self.status_label.configure(text="Status: Disconnected", text_color=RED)
            self.toggle_button.configure(
                text="ACTIVATE", fg_color=GREEN, hover_color="#39A968", text_color="#0B1710"
            )
            self.mode_menu.configure(state="normal")
            self.dns_checkbox.configure(state="normal")

    def _poll_process(self):
        if self.closing:
            return
        if self.process is not None and self.process.poll() is not None:
            return_code = self.process.returncode
            self.process = None
            self._set_running_ui(False)
            if return_code != 0:
                messagebox.showwarning(
                    "GoodbyeDPI stopped",
                    f"The process exited with code {return_code}. Check that the WinDivert "
                    "files are present and that no other instance is using the driver.",
                    parent=self,
                )
        self.after(750, self._poll_process)

    def _on_close(self):
        self.closing = True
        self._stop_process()
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    app = GoodbyeDPIApp()
    app.mainloop()