; Fleet Tauri: kill UI + backend before install/uninstall (backend locks resources/*.exe).
; Client registration: mcp-clients.nsh (vendored fleet canonical) registers the
; stdio backend in detected AI tools (Claude/Cursor/Antigravity/OpenCode).
!define MCP_REG_NAME "vla-mcp"
!define MCP_REG_EXE "vla-mcp-backend.exe"
!include "mcp-clients.nsh"

!macro KillVlaMcpFleetProcesses
  DetailPrint "Stopping vla-mcp processes..."
  ExecWait 'taskkill /F /IM vla-mcp-backend.exe /T' $0
  ExecWait 'taskkill /F /IM vla-mcp-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "vla-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "vla-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "vla-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "vla-mcp-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillVlaMcpFleetProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro KillVlaMcpFleetProcesses
  !insertmacro McpClientsRegister
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillVlaMcpFleetProcesses
  !insertmacro McpClientsUnregister
!macroend
