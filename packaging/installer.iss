; Instalador opcional (Inno Setup) para quien prefiera dejar el programa
; instalado permanentemente, en lugar de usar la versión portátil.
;
; IMPORTANTE: la versión portátil sigue siendo la forma principal de
; distribución. Este instalador NO reemplaza ni elimina la carpeta
; portátil; simplemente copia los mismos archivos a Archivos de programa
; (o a una carpeta elegida por el usuario) y crea accesos directos.
;
; Requiere Inno Setup 6 (https://jrsoftware.org/isinfo.php) instalado en la
; máquina de desarrollo (Windows). Compilar con:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
;
; Antes de compilar, debe existir la carpeta portátil ya generada en
; dist\Transcriptor_Notarial_Portable (ver build_portable.ps1).

#define MyAppName "Transcriptor Notarial"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Notaria (personalizar)"
#define MyAppExeName "TranscriptorNotarial.exe"
#define PortableDir "..\dist\Transcriptor_Notarial_Portable"

[Setup]
AppId={{B6E2B6B0-6C57-4C1E-9C7C-TRANSCRIPTOR1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=TranscriptorNotarial_Instalador
Compression=lzma2
SolidCompression=yes
; No se requieren privilegios de administrador salvo que el usuario elija
; instalar en una carpeta protegida; por defecto se instala por usuario.
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=..\resources\iconos\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "{#PortableDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Manual de uso"; Filename: "{app}\Manual_de_Uso.pdf"; Flags: skipifsourcedoesntexist
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; No se eliminan documentos generados por el usuario (viven en
; %USERPROFILE%\Documentos\Transcripciones Notariales, fuera de {app}).
Type: filesandordirs; Name: "{app}"
