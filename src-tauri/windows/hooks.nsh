; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
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

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillVlaMcpFleetProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  IfFileExists "$INSTDIR\resources\install-mcp-clients.ps1" 0 mcp_hook_done
    DetailPrint "Optional: register vla-mcp in Cursor / Claude Desktop"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-mcp-clients.ps1" -Interactive'
  mcp_hook_done:
!macroend
