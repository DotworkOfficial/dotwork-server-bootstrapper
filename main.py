#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Dotwork Server Bootstraper")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Dotwork")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()