from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLineEdit, QLabel, QCheckBox,
                             QSpinBox, QGroupBox, QFileDialog, QMessageBox,
                             QTabWidget, QWidget, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.config import ConfigManager
import os

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        self.setWindowTitle("설정")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_paths_tab()
        self.create_backup_tab()
        self.create_general_tab()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("확인")
        self.ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        self.apply_button = QPushButton("적용")
        self.apply_button.clicked.connect(self.apply_settings)
        buttons_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("기본값으로 초기화")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(self.reset_button)
        
        layout.addLayout(buttons_layout)
    
    def create_paths_tab(self):
        tab = QWidget()
        self.tab_widget.addTab(tab, "경로 설정")
        
        layout = QVBoxLayout(tab)
        
        # Templates directory
        templates_group = QGroupBox("템플릿 디렉토리")
        templates_layout = QFormLayout(templates_group)
        
        templates_dir_layout = QHBoxLayout()
        self.templates_dir_edit = QLineEdit()
        self.templates_dir_edit.setPlaceholderText("템플릿이 저장된 폴더 경로")
        templates_dir_layout.addWidget(self.templates_dir_edit)
        
        browse_templates_btn = QPushButton("찾아보기")
        browse_templates_btn.clicked.connect(self.browse_templates_dir)
        templates_dir_layout.addWidget(browse_templates_btn)
        
        templates_layout.addRow("템플릿 폴더:", templates_dir_layout)
        
        # Add description
        desc_label = QLabel("템플릿 폴더에는 각 서버 타입별 템플릿이 포함되어야 합니다.\n"
                           "예: templates/main/, templates/sub/, templates/lobby/")
        desc_label.setStyleSheet("color: gray; font-size: 11px;")
        desc_label.setWordWrap(True)
        templates_layout.addRow(desc_label)
        
        layout.addWidget(templates_group)
        
        # Output directory
        output_group = QGroupBox("출력 디렉토리")
        output_layout = QFormLayout(output_group)
        
        # Default output directory
        output_dir_layout = QHBoxLayout()
        self.default_output_dir_edit = QLineEdit()
        self.default_output_dir_edit.setPlaceholderText("인스턴스가 생성될 기본 폴더")
        output_dir_layout.addWidget(self.default_output_dir_edit)
        
        browse_output_btn = QPushButton("찾아보기")
        browse_output_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(browse_output_btn)
        
        output_layout.addRow("기본 출력 폴더:", output_dir_layout)
        
        # Instances directory for discovery
        instances_dir_layout = QHBoxLayout()
        self.instances_dir_edit = QLineEdit()
        self.instances_dir_edit.setPlaceholderText("기존 인스턴스를 검색할 폴더")
        instances_dir_layout.addWidget(self.instances_dir_edit)
        
        browse_instances_btn = QPushButton("찾아보기")
        browse_instances_btn.clicked.connect(self.browse_instances_dir)
        instances_dir_layout.addWidget(browse_instances_btn)
        
        output_layout.addRow("인스턴스 검색 폴더:", instances_dir_layout)
        
        layout.addWidget(output_group)
        
        layout.addStretch()
    
    def create_backup_tab(self):
        tab = QWidget()
        self.tab_widget.addTab(tab, "백업 설정")
        
        layout = QVBoxLayout(tab)
        
        backup_group = QGroupBox("백업 옵션")
        backup_layout = QFormLayout(backup_group)
        
        # Auto backup
        self.auto_backup_check = QCheckBox("인스턴스 업데이트 시 자동 백업")
        backup_layout.addRow(self.auto_backup_check)
        
        # Backup directory
        backup_dir_layout = QHBoxLayout()
        self.backup_dir_edit = QLineEdit()
        backup_dir_layout.addWidget(self.backup_dir_edit)
        
        browse_backup_btn = QPushButton("찾아보기")
        browse_backup_btn.clicked.connect(self.browse_backup_dir)
        backup_dir_layout.addWidget(browse_backup_btn)
        
        backup_layout.addRow("백업 폴더:", backup_dir_layout)
        
        # Max backups
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setMinimum(1)
        self.max_backups_spin.setMaximum(50)
        backup_layout.addRow("최대 백업 개수:", self.max_backups_spin)
        
        layout.addWidget(backup_group)
        layout.addStretch()
    
    def create_general_tab(self):
        tab = QWidget()
        self.tab_widget.addTab(tab, "일반 설정")
        
        layout = QVBoxLayout(tab)
        
        # Logging
        logging_group = QGroupBox("로깅 설정")
        logging_layout = QFormLayout(logging_group)
        
        from PyQt5.QtWidgets import QComboBox
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        logging_layout.addRow("로그 레벨:", self.log_level_combo)
        
        layout.addWidget(logging_group)
        
        # About
        about_group = QGroupBox("정보")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setMaximumHeight(100)
        about_text.setText(
            "Dotwork Server Bootstraper v1.0.0\n\n"
            "마인크래프트 서버 인스턴스를 쉽게 생성하고 관리할 수 있는 도구입니다.\n"
            "템플릿 기반으로 서버 설정을 자동화하여 인프라 지식 없이도 "
            "서버를 구성할 수 있습니다."
        )
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        layout.addStretch()
    
    def browse_templates_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "템플릿 디렉토리 선택", 
            self.templates_dir_edit.text() or self.config.templates_dir
        )
        if dir_path:
            self.templates_dir_edit.setText(dir_path)
    
    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "기본 출력 디렉토리 선택",
            self.default_output_dir_edit.text() or self.config.default_output_dir
        )
        if dir_path:
            self.default_output_dir_edit.setText(dir_path)
    
    def browse_instances_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "인스턴스 검색 디렉토리 선택",
            self.instances_dir_edit.text() or self.config.instances_dir
        )
        if dir_path:
            self.instances_dir_edit.setText(dir_path)
    
    def browse_backup_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "백업 디렉토리 선택",
            self.backup_dir_edit.text() or self.config.backup_dir
        )
        if dir_path:
            self.backup_dir_edit.setText(dir_path)
    
    def load_settings(self):
        """Load current settings into UI"""
        self.templates_dir_edit.setText(self.config.templates_dir)
        self.default_output_dir_edit.setText(self.config.default_output_dir)
        self.instances_dir_edit.setText(self.config.instances_dir)
        self.backup_dir_edit.setText(self.config.backup_dir)
        self.auto_backup_check.setChecked(self.config.auto_backup)
        self.max_backups_spin.setValue(self.config.max_backups)
        
        # Set log level
        log_level_index = self.log_level_combo.findText(self.config.log_level)
        if log_level_index >= 0:
            self.log_level_combo.setCurrentIndex(log_level_index)
    
    def apply_settings(self):
        """Apply settings without closing dialog"""
        if self.validate_settings():
            self.save_settings()
            self.settings_changed.emit()
            QMessageBox.information(self, "설정 저장", "설정이 저장되었습니다.")
    
    def validate_settings(self):
        """Validate settings before saving"""
        templates_dir = self.templates_dir_edit.text().strip()
        
        if not templates_dir:
            QMessageBox.warning(self, "설정 오류", "템플릿 디렉토리를 설정해주세요.")
            self.tab_widget.setCurrentIndex(0)  # Switch to paths tab
            self.templates_dir_edit.setFocus()
            return False
        
        if not os.path.exists(templates_dir):
            reply = QMessageBox.question(
                self, "디렉토리 생성",
                f"템플릿 디렉토리가 존재하지 않습니다:\n{templates_dir}\n\n"
                "디렉토리를 생성하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(templates_dir, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "오류", f"디렉토리 생성 실패:\n{str(e)}")
                    return False
            else:
                return False
        
        return True
    
    def save_settings(self):
        """Save settings to config"""
        self.config_manager.update_config(
            templates_dir=self.templates_dir_edit.text().strip(),
            default_output_dir=self.default_output_dir_edit.text().strip(),
            instances_dir=self.instances_dir_edit.text().strip(),
            backup_dir=self.backup_dir_edit.text().strip(),
            auto_backup=self.auto_backup_check.isChecked(),
            max_backups=self.max_backups_spin.value(),
            log_level=self.log_level_combo.currentText()
        )
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self, "설정 초기화",
            "모든 설정을 기본값으로 초기화하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config_manager.reset_to_defaults()
            self.config = self.config_manager.get_config()
            self.load_settings()
            self.settings_changed.emit()
    
    def accept(self):
        """OK button clicked"""
        if self.validate_settings():
            self.save_settings()
            self.settings_changed.emit()
            super().accept()
    
    def reject(self):
        """Cancel button clicked"""
        super().reject()