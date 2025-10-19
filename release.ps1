pyinstaller `
    --onefile `
    --windowed `
    --paths "C:\Users\ryu\code\sdxutils\.venv\Lib\site-packages" `
    --hidden-import=PySide6.QtWidgets `
    --hidden-import=PySide6.QtCore `
    --hidden-import=PySide6.QtGui `
    --add-data "C:\Users\ryu\code\sdxutils\.venv\Lib\site-packages\PySide6\plugins;PySide6\plugins" `
    GUI\main.py
