# Historical native copy of the desktop controller

Development takes place in WSL. A technical copy was prepared at
`D:\Tesi-mqt\prototipo-native` to avoid loading DLLs from a UNC path.
It contains `server-desktop.ps1`, `server-desktop-internal.ps1`,
`verify-model.ps1`, `AmdSensors.cs`, `config.json` and only the
`runtime/desktop` and `runtime/pstools` runtimes. The weights stayed at their
existing Windows location; they were not downloaded again.

On another computer, copy these files to a local Windows directory or copy the
whole prototype as explained in the
[installation guide](../../../prototipo/docs/installazione_e_runtime.md).
Start the controller from that directory with a local `ModelPath`. Do not copy
the Qdrant index created on Linux: `app.py prepare` rebuilds it.

The transfer completed during the session recorded here, but the controller
stalled before creating logs or starting the server. PowerShell 5.1 and 7 were
tried; only processes owned by that session were stopped. No real Qwen response
was obtained. The cause remained undiagnosed in that session, so this record
does not attribute the failure to the weights or quantum compilation. It is
a historical observation, not a current health check of the desktop runtime.
