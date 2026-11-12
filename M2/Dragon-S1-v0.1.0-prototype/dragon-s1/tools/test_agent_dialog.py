import sys
from pathlib import Path

# Add agent folder to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

from PyQt5.QtWidgets import QApplication
from ui.request_modal import RequestDialog

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(
        "QWidget{background:#0b0f14;color:#eef4fa;font-family:Segoe UI} "
        "QPushButton{padding:10px;background:#17212c;border:1px solid #263443;"
        "border-radius:7px} "
        "QLineEdit,QTextEdit{background:#111821;border:1px solid #263443;"
        "border-radius:7px;padding:8px}"
    )
    
    print("Launching verification wizard dialog for testing...")
    dialog = RequestDialog("Demo USB Device (SanDisk 64GB)")
    if dialog.exec() == dialog.Accepted:
        print("\n=== Dialog Accepted! ===")
        print("Result Data:")
        for k, v in dialog.result_data().items():
            print(f"  {k}: {v}")
    else:
        print("\n=== Dialog Cancelled! ===")

if __name__ == "__main__":
    main()
