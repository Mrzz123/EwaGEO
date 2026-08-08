import os
import re
import subprocess
import pathlib
import sys
import xml.etree.ElementTree as ET


WINDOWS_TASK_NAME = "EwaGEO"
LEGACY_WINDOWS_TASK_NAME = "liewa"


def get_cli_command():
    """Return a CLI command that works from source and from PyInstaller."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--run-cli"]
    cli_path = pathlib.Path(__file__).resolve().parents[2] / "cli.py"
    return [sys.executable, str(cli_path)]


def _decode_console_output(output):
    if not output:
        return ""
    encoding = "oem" if os.name == "nt" else "utf-8"
    return output.decode(encoding, errors="replace").strip()


def _run_elevated_scheduler_action(action, interval_minutes=None):
    """Run one fixed scheduler action through a scoped Windows UAC prompt."""
    if os.name != "nt":
        return "Administrator elevation is only available on Windows.", False

    import ctypes
    from ctypes import wintypes

    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("fMask", wintypes.ULONG),
            ("hwnd", wintypes.HWND),
            ("lpVerb", wintypes.LPCWSTR),
            ("lpFile", wintypes.LPCWSTR),
            ("lpParameters", wintypes.LPCWSTR),
            ("lpDirectory", wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", wintypes.HINSTANCE),
            ("lpIDList", wintypes.LPVOID),
            ("lpClass", wintypes.LPCWSTR),
            ("hkeyClass", wintypes.HKEY),
            ("dwHotKey", wintypes.DWORD),
            ("hIcon", wintypes.HANDLE),
            ("hProcess", wintypes.HANDLE),
        ]

    if getattr(sys, "frozen", False):
        executable = sys.executable
        arguments = ["--scheduler-action", action]
    else:
        executable = sys.executable
        app_path = pathlib.Path(__file__).resolve().parents[2] / "app.py"
        arguments = [str(app_path), "--scheduler-action", action]
    if action == "create" and interval_minutes is not None:
        arguments.extend(["--scheduler-interval", str(interval_minutes)])

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    shell32.ShellExecuteExW.argtypes = [ctypes.POINTER(ShellExecuteInfo)]
    shell32.ShellExecuteExW.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, wintypes.LPDWORD]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    info = ShellExecuteInfo()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = executable
    info.lpParameters = subprocess.list2cmdline(arguments)
    info.nShow = 0

    if not shell32.ShellExecuteExW(ctypes.byref(info)):
        error_code = ctypes.get_last_error()
        if error_code == 1223:
            return "Administrator permission was cancelled by the user.", False
        return f"Unable to request administrator permission (error {error_code}).", False

    try:
        wait_result = kernel32.WaitForSingleObject(info.hProcess, 60000)
        if wait_result == 0x00000102:  # WAIT_TIMEOUT
            return "The administrator operation did not finish within 60 seconds.", False

        exit_code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(exit_code)):
            return "Unable to read the administrator operation result.", False
        if exit_code.value == 0:
            return "Task Scheduler command completed with administrator permission.", True
        return "Task Scheduler rejected the command even with administrator permission.", False
    finally:
        kernel32.CloseHandle(info.hProcess)


class Systemd:
    def __init__(self):
        self.service_name = "liewa.service"
        self.timer_name = "liewa.timer"

    def update(self):
        timer_cmd = f"systemctl --user status {self.timer_name}"
        service_cmd = f"systemctl --user status {self.service_name}"
        proc = subprocess.Popen(timer_cmd.split(), stdout=subprocess.PIPE)
        timer_output = proc.communicate()[0].decode("utf-8")
        proc = subprocess.Popen(service_cmd.split(), stdout=subprocess.PIPE)
        service_output = proc.communicate()[0].decode("utf-8")
        running = False
        if re.search(r"(?<=Active:\s)\w*", timer_output):
            running = True

        return timer_output+'\n'+service_output,running

    def create_scheduler(self, interval_minutes=10):
        cwd = pathlib.Path(__file__).parent.resolve()
        zwi = os.path.dirname(cwd)

        service = os.path.join(zwi,"liewa.service")
        timer = os.path.join(zwi,"liewa.timer")

        cwd = pathlib.Path(__file__).parent.resolve()
        zwi = os.path.dirname(cwd)
        zwi = os.path.dirname(zwi)
        cli_dir = os.path.join(zwi,"cli.py")

        with open(service, "w") as f:
            f.write(f"""[Unit]
Description=EwaGEO Service
[Service]
Type=simple
ExecStart={os.popen('which python3').read().strip()} {cli_dir}
[Install]
WantedBy=graphical.target""")
        with open(timer, "w") as f:
            f.write(f"""[Unit]
Description=EwaGEO Timer
[Timer]
OnBootSec=1min
OnUnitActiveSec={interval_minutes}min
[Install]
WantedBy=timers.target""")

        os.system(f"cp {service} ~/.config/systemd/user/")
        os.system(f"cp {timer} ~/.config/systemd/user/")

        os.system(f"systemctl --user enable {self.timer_name}")
        self.reload_scheduler()
        os.system(f"systemctl --user start {self.timer_name}")
        subprocess.Popen(f"systemctl --user status {self.timer_name}".split())

        # os.system(f"rm {self.service_name}") #achtubg!!!
        # os.system(f"rm {self.timer_name}")

    def delete_scheduler(self):
        for unit_file in [self.timer_name,self.service_name]:
            os.system(f"systemctl --user stop {unit_file}")
            os.system(f"systemctl --user disable {unit_file}")
            os.system(f"rm ~/.config/systemd/user/{unit_file}")
        self.reload_scheduler()

    def reload_scheduler(self):
        os.system("systemctl --user daemon-reload")


class Launchd:
    def __init__(self):
        cwd = pathlib.Path(__file__).parent.resolve()
        zwi = os.path.dirname(cwd)
        zwi = os.path.dirname(zwi)
        self.plist_path = os.path.join(zwi,"com.liewa.daemon.plist")
        if not os.path.exists(os.path.join(zwi,'stderr.log')) : open(os.path.join(zwi,'stderr.log'), 'a').close()
        if not os.path.exists(os.path.join(zwi,'stdout.log')) : open(os.path.join(zwi,'stdout.log'), 'a').close()
        error_log_path = os.path.join(zwi,"stderr.log")
        out_log_path = os.path.join(zwi,"stdout.log")
        working_dir_path = zwi
        python_interpreter_path = os.popen("which python3").read().strip()
        cli_path = os.path.join(zwi,"cli.py")

        self._write_plist(10)
        self.update()

    def _write_plist(self, interval_minutes):
        cwd = pathlib.Path(__file__).parent.resolve()
        zwi = os.path.dirname(os.path.dirname(cwd))
        error_log_path = os.path.join(zwi, "stderr.log")
        out_log_path = os.path.join(zwi, "stdout.log")
        working_dir_path = zwi
        python_interpreter_path = os.popen('which python3').read().strip()
        cli_path = os.path.join(zwi, "cli.py")
        with open(self.plist_path,"w") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>

    <key>Label</key>
    <string>com.liewa.daemon.plist</string>

    <key>RunAtLoad</key>
    <true/>

    <key>StartInterval</key>
    <integer>{interval_minutes * 60}</integer>

    <key>StandardErrorPath</key>
    <string>{error_log_path}</string>

    <key>StandardOutPath</key>
    <string>{out_log_path}</string>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string><![CDATA[/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin]]></string>
    </dict>

    <key>WorkingDirectory</key>
    <string>{working_dir_path}</string>

    <key>ProgramArguments</key>
    <array>
      <string>{python_interpreter_path}</string>
      <string>{cli_path}</string>
    </array>

  </dict>
</plist>""")

    def get_node(self,tree,name):
        for _,node in tree:
            if node.text == name:
                break
        print(next(tree)[1].text)
        return next(tree)[1]

    def update(self):
        cwd = pathlib.Path(__file__).parent.resolve()
        zwi = os.path.dirname(cwd)
        zwi = os.path.dirname(zwi)
        out = os.path.join(zwi,"stdout.log")
        with open(out,"r+") as f:
            out_lines = f.readlines()
        print(" ".join(out_lines))
        with open(out,"w") as f:
            f.seek(0)
            f.truncate()
        out = os.path.join(zwi,"stderr.log")
        with open(out,"r+") as f:
            err_lines = f.readlines()
        print(" ".join(err_lines))
        with open(out,"w") as f:
            f.seek(0)
            f.truncate()

        if len(" ".join(err_lines)) >= 5:
            return "Error occurred!\n\n"+" ".join(err_lines) + "\n\nError occurred!", True

        if len(" ".join(out_lines)) >= 5:
            return "Success!\n\n"+" ".join(out_lines) + "\n\nSuccess!", True

        return " ".join(err_lines) + " ".join(out_lines), True

    def create_scheduler(self, interval_minutes=10):
        self._write_plist(interval_minutes)
        subprocess.run(f"launchctl load {self.plist_path}",shell=True)

    def delete_scheduler(self):
        subprocess.run(f"launchctl unload {self.plist_path}",shell=True)

    def reload_scheduler(self):
        subprocess.run(f"launchctl start {self.plist_path}",shell=True)



class Schtasks:
    def __init__(self):
        #cwd = pathlib.Path(__file__).parent.resolve()
        #zwi = os.path.dirname(cwd)
        #zwi = os.path.dirname(zwi)
        #filename = os.path.join(zwi,'liewaSchtask.xml')
        #ET.register_namespace("", "http://schemas.microsoft.com/windows/2004/02/mit/task")
        #tree = ET.parse(filename)
        #root = tree.getroot()
        #node = root[4][0][0]            #get the Command Node
        #node.text = os.path.join(zwi,"cli.vbs")
        #author = root[0][1]
        #author.text = str(os.environ['COMPUTERNAME'])+"\\"+ str(os.getlogin())
        #tree.write(os.path.join(zwi,'liewaSchtask.xml'))
        self.update()

    def update(self):
        output, succeeded = self._run("/Query", "/TN", WINDOWS_TASK_NAME)
        if succeeded:
            return output, True
        return self._run("/Query", "/TN", LEGACY_WINDOWS_TASK_NAME)

    def create_scheduler(self, elevate=True, interval_minutes=10):
        try:
            interval_minutes = int(interval_minutes)
        except (TypeError, ValueError):
            return "The update interval must be a whole number of minutes.", False
        if not 5 <= interval_minutes <= 720:
            return "The update interval must be between 5 and 720 minutes.", False
        if elevate:
            return _run_elevated_scheduler_action("create", interval_minutes)
        task_command = subprocess.list2cmdline(get_cli_command())
        output, succeeded = self._run(
            "/Create", "/SC", "MINUTE", "/MO", str(interval_minutes), "/TN", WINDOWS_TASK_NAME,
            "/TR", task_command, "/IT", "/RL", "LIMITED", "/F"
        )
        if succeeded:
            self._run("/Delete", "/TN", LEGACY_WINDOWS_TASK_NAME, "/F")
        return output, succeeded

    def delete_scheduler(self, elevate=True):
        if elevate:
            return _run_elevated_scheduler_action("delete")
        output, succeeded = self._run("/Delete", "/TN", WINDOWS_TASK_NAME, "/F")
        legacy_output, legacy_succeeded = self._run(
            "/Delete", "/TN", LEGACY_WINDOWS_TASK_NAME, "/F"
        )
        if succeeded:
            return output, True
        return legacy_output, legacy_succeeded

    def reload_scheduler(self, elevate=True):
        if elevate:
            return _run_elevated_scheduler_action("run")
        _, current_exists = self._run("/Query", "/TN", WINDOWS_TASK_NAME)
        task_name = WINDOWS_TASK_NAME if current_exists else LEGACY_WINDOWS_TASK_NAME
        return self._run("/Run", "/TN", task_name)

    @staticmethod
    def _run(*arguments):
        try:
            completed = subprocess.run(
                ["schtasks.exe", *arguments],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired:
            return "Windows Task Scheduler did not respond within 15 seconds.", False
        except OSError as exc:
            return f"Unable to start Windows Task Scheduler: {exc}", False

        output = _decode_console_output(completed.stdout)
        if not output:
            output = (
                "Task Scheduler command completed successfully."
                if completed.returncode == 0
                else f"Task Scheduler command failed (exit code {completed.returncode})."
            )
        return output, completed.returncode == 0


if __name__ == "__main__":
    taks = Schtasks()
