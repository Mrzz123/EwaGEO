# Contributing to EwaGEO

Bug reports, feature proposals, translations and pull requests are welcome at https://github.com/Mrzz123/EwaGEO.

## Before opening a pull request

1. Keep each pull request focused on one change.
2. Explain the user-visible behaviour and any compatibility impact.
3. Preserve upstream and third-party copyright/licence notices.
4. Add or update tests when behaviour changes.
5. Run the local checks below.

```powershell
$env:QT_QPA_PLATFORM='offscreen'
venv\Scripts\python.exe -m compileall -q app.py cli.py liewa tests
venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Development setup

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe app.py
```

## Windows packaging

```powershell
venv\Scripts\pyinstaller.exe --clean --noconfirm app.spec
& 'D:\Inno Setup 6\ISCC.exe' winCompiler.iss
```

Do not commit `venv`, `build`, `dist` or `Output`. Attach `Output\EwaGEO-Setup.exe` to a GitHub Release after testing it on a clean Windows machine.

Contributions are accepted under GPL-3.0-only, the same licence as EwaGEO and its upstream project.
