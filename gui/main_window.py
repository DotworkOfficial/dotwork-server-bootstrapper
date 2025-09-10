from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QTextEdit, 
                             QSplitter, QGroupBox, QMessageBox, QFileDialog,
                             QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from core.template_manager import TemplateManager
from gui.instance_wizard import InstanceCreationWizard
from gui.instance_manager import InstanceManagerWidget
from gui.settings_dialog import SettingsDialog
from models.template import Template
from utils.config import ConfigManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.config.ensure_directories()  # Create directories if they don't exist
        
        self.template_manager = TemplateManager(self.config.templates_dir)
        self.templates = []
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        self.setWindowTitle("Dotwork Server Bootstrapper")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Templates
        left_panel = self.create_templates_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Instance management
        right_panel = self.create_instances_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([400, 800])
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Menu bar
        self.create_menu_bar()
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('파일')
        
        refresh_action = file_menu.addAction('템플릿 새로고침')
        refresh_action.triggered.connect(self.load_templates)
        
        file_menu.addSeparator()
        
        settings_action = file_menu.addAction('설정')
        settings_action.triggered.connect(self.show_settings)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('종료')
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu('도움말')
        about_action = help_menu.addAction('정보')
        about_action.triggered.connect(self.show_about)
    
    def create_templates_panel(self):
        group_box = QGroupBox("템플릿 목록")
        layout = QVBoxLayout(group_box)
        
        # Templates list
        self.templates_list = QListWidget()
        self.templates_list.itemSelectionChanged.connect(self.on_template_selected)
        layout.addWidget(self.templates_list)
        
        # Template info
        self.template_info = QTextEdit()
        self.template_info.setMaximumHeight(150)
        self.template_info.setReadOnly(True)
        layout.addWidget(QLabel("템플릿 정보:"))
        layout.addWidget(self.template_info)
        
        # Buttons
        buttons_layout = QVBoxLayout()
        
        self.create_instance_btn = QPushButton("인스턴스 생성")
        self.create_instance_btn.clicked.connect(self.create_instance)
        self.create_instance_btn.setEnabled(False)
        buttons_layout.addWidget(self.create_instance_btn)
        
        self.refresh_templates_btn = QPushButton("템플릿 새로고침")
        self.refresh_templates_btn.clicked.connect(self.load_templates)
        buttons_layout.addWidget(self.refresh_templates_btn)
        
        layout.addLayout(buttons_layout)
        
        return group_box
    
    def create_instances_panel(self):
        self.instance_manager = InstanceManagerWidget()
        return self.instance_manager
    
    def load_templates(self):
        self.templates_list.clear()
        self.template_info.clear()
        
        try:
            # Update template manager with current config
            self.template_manager = TemplateManager(self.config.templates_dir)
            self.templates = self.template_manager.discover_templates()
            
            for template in self.templates:
                item = QListWidgetItem(template.name)
                item.setData(Qt.UserRole, template)
                self.templates_list.addItem(item)
            
            if not self.templates:
                template_path = self.config.templates_dir
                self.template_info.setText(
                    f"템플릿이 없습니다.\n"
                    f"다음 폴더에 템플릿을 추가하거나 설정에서 템플릿 경로를 변경해주세요:\n"
                    f"{template_path}"
                )
            
            self.statusBar().showMessage(f"{len(self.templates)}개의 템플릿을 찾았습니다. (경로: {self.config.templates_dir})")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"템플릿을 로드하는 중 오류가 발생했습니다:\n{str(e)}")
    
    def on_template_selected(self):
        current_item = self.templates_list.currentItem()
        if current_item:
            template = current_item.data(Qt.UserRole)
            self.show_template_info(template)
            self.create_instance_btn.setEnabled(True)
        else:
            self.template_info.clear()
            self.create_instance_btn.setEnabled(False)
    
    def show_template_info(self, template: Template):
        info_text = f"이름: {template.name}\n"
        info_text += f"설명: {template.description}\n"
        info_text += f"버전: {template.version}\n"
        info_text += f"경로: {template.path}\n\n"
        
        if template.variables:
            info_text += "필요한 변수들:\n"
            for var in template.variables:
                info_text += f"  - {var.name} ({var.type}): {var.description}\n"
                if var.default_value is not None:
                    info_text += f"    기본값: {var.default_value}\n"
                if not var.required:
                    info_text += f"    (선택사항)\n"
        else:
            info_text += "변수가 없습니다."
        
        self.template_info.setText(info_text)
    
    def create_instance(self):
        current_item = self.templates_list.currentItem()
        if not current_item:
            return
        
        template = current_item.data(Qt.UserRole)
        
        # Open instance creation wizard
        wizard = InstanceCreationWizard(template, self.template_manager, self, self.config.default_output_dir)
        if wizard.exec_() == wizard.Accepted:
            # Refresh instance list
            self.instance_manager.refresh_instances()
            self.statusBar().showMessage("인스턴스가 성공적으로 생성되었습니다.")
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec_()
    
    def on_settings_changed(self):
        """Handle settings changes"""
        # Reload config
        self.config = self.config_manager.get_config()
        
        # Reload templates with new path
        self.load_templates()
        
        # Update instance manager
        self.instance_manager.refresh_instances()
        
        self.statusBar().showMessage("설정이 변경되었습니다.")
    
    def show_about(self):
        QMessageBox.about(self, "정보", 
                         "Dotwork Server Bootstrapper v1.0.0\n\n"
                         "마인크래프트 서버 인스턴스를 쉽게 생성하고 관리할 수 있는 도구입니다.")