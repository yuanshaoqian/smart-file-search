; Smart File Search - NSIS 安装脚本
; 用于创建 Windows 安装包

!include "MUI2.nsh"

; 应用程序信息
Name "Smart File Search"
OutFile "SmartFileSearch-Setup.exe"
InstallDir "$PROGRAMFILES\SmartFileSearch"
InstallDirRegKey HKLM "Software\SmartFileSearch" "Install_Dir"
RequestExecutionLevel admin

; 界面设置
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"

; 页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; 安装部分
Section "Smart File Search" SecDummy
  SectionIn RO
  
  ; 设置输出路径
  SetOutPath $INSTDIR
  
  ; 复制文件
  File /r "dist\SmartFileSearch\*.*"
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; 注册表
  WriteRegStr HKLM "Software\SmartFileSearch" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SmartFileSearch" "DisplayName" "Smart File Search"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SmartFileSearch" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SmartFileSearch" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SmartFileSearch" "NoRepair" 1
  
SectionEnd

; 桌面快捷方式
Section "桌面快捷方式" SecDesktop
  CreateShortCut "$DESKTOP\Smart File Search.lnk" "$INSTDIR\SmartFileSearch.exe"
SectionEnd

; 开始菜单
Section "开始菜单" SecStartMenu
  CreateDirectory "$SMPROGRAMS\Smart File Search"
  CreateShortCut "$SMPROGRAMS\Smart File Search\Smart File Search.lnk" "$INSTDIR\SmartFileSearch.exe"
  CreateShortCut "$SMPROGRAMS\Smart File Search\卸载.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

; 卸载部分
Section "Uninstall"
  ; 删除文件
  RMDir /r "$INSTDIR\*.*"
  
  ; 删除桌面快捷方式
  Delete "$DESKTOP\Smart File Search.lnk"
  
  ; 删除开始菜单
  Delete "$SMPROGRAMS\Smart File Search\*.*"
  RMDir "$SMPROGRAMS\Smart File Search"
  
  ; 删除注册表
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SmartFileSearch"
  DeleteRegKey HKLM "Software\SmartFileSearch"
  
  ; 删除安装目录
  RMDir "$INSTDIR"
SectionEnd
