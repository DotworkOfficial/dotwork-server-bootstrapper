from PyQt5.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QTextEdit, QPushButton,
                             QFormLayout, QSpinBox, QComboBox, QFileDialog,
                             QMessageBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from models.template import Template, TemplateVariable
from core.template_manager import TemplateManager
import os

class InstanceCreationWizard(QWizard):
    def __init__(self, template: Template, template_manager: TemplateManager, parent=None, default_output_dir: str = None):
        super().__init__(parent)
        self.template = template
        self.template_manager = template_manager
        self.default_output_dir = default_output_dir or os.path.join(os.getcwd(), "instances")
        
        self.setWindowTitle(f"인스턴스 생성 - {template.name}")
        self.setFixedSize(600, 500)
        
        # Add pages
        self.addPage(InstanceInfoPage(self.template, self.default_output_dir))
        self.addPage(VariablesPage(self.template))
        self.addPage(SummaryPage(self.template))
        
        # Set button texts
        self.setButtonText(QWizard.NextButton, "다음")
        self.setButtonText(QWizard.BackButton, "이전")
        self.setButtonText(QWizard.FinishButton, "생성")
        self.setButtonText(QWizard.CancelButton, "취소")
    
    def accept(self):
        try:
            # Get data from pages
            instance_name = self.field("instance_name")
            output_dir = self.field("output_dir")
            
            # Collect variables
            variables = {}
            variables_page = self.page(1)
            for var_name, widget in variables_page.variable_widgets.items():
                if isinstance(widget, QLineEdit):
                    variables[var_name] = widget.text()
                elif isinstance(widget, QSpinBox):
                    variables[var_name] = widget.value()
                elif isinstance(widget, QComboBox):
                    variables[var_name] = widget.currentText()
                elif isinstance(widget, QCheckBox):
                    variables[var_name] = widget.isChecked()
            
            # Validate variables
            errors = self.template_manager.validate_variables(self.template, variables)
            if errors:
                QMessageBox.warning(self, "변수 검증 오류", 
                                   "다음 오류를 수정해주세요:\n" + "\n".join(errors))
                return
            
            # Create instance
            instance = self.template_manager.create_instance(
                self.template, instance_name, output_dir, variables
            )
            
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"인스턴스 생성 중 오류가 발생했습니다:\n{str(e)}")

class InstanceInfoPage(QWizardPage):
    def __init__(self, template: Template, default_output_dir: str = None):
        super().__init__()
        self.template = template
        self.default_output_dir = default_output_dir or os.path.join(os.getcwd(), "instances")
        self.init_ui()
    
    def init_ui(self):
        self.setTitle("인스턴스 기본 정보")
        self.setSubTitle(f"'{self.template.name}' 템플릿을 사용하여 새 인스턴스를 생성합니다.")
        
        layout = QFormLayout(self)
        
        # Instance name
        self.instance_name_edit = QLineEdit()
        self.instance_name_edit.setPlaceholderText("예: my-server-001")
        self.registerField("instance_name*", self.instance_name_edit)
        layout.addRow("인스턴스 이름:", self.instance_name_edit)
        
        # Output directory
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(self.default_output_dir)
        self.registerField("output_dir*", self.output_dir_edit)
        dir_layout.addWidget(self.output_dir_edit)
        
        browse_btn = QPushButton("찾아보기")
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)
        
        layout.addRow("생성 위치:", dir_layout)
        
        # Template info
        info_group = QGroupBox("템플릿 정보")
        info_layout = QVBoxLayout(info_group)
        
        info_text = f"이름: {self.template.name}\n"
        info_text += f"설명: {self.template.description}\n"
        info_text += f"버전: {self.template.version}"
        
        info_label = QLabel(info_text)
        info_layout.addWidget(info_label)
        
        layout.addRow(info_group)
    
    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "출력 디렉토리 선택")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

class VariablesPage(QWizardPage):
    def __init__(self, template: Template):
        super().__init__()
        self.template = template
        self.variable_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        self.setTitle("변수 설정")
        self.setSubTitle("템플릿에서 사용할 변수값들을 입력해주세요.")
        
        layout = QFormLayout(self)
        
        if not self.template.variables:
            no_vars_label = QLabel("이 템플릿은 설정할 변수가 없습니다.")
            layout.addWidget(no_vars_label)
            return
        
        for variable in self.template.variables:
            widget = self.create_variable_widget(variable)
            self.variable_widgets[variable.name] = widget
            
            label_text = variable.name
            if variable.required:
                label_text += " *"
            
            desc_label = QLabel(f"{label_text}\n{variable.description}")
            layout.addRow(desc_label, widget)
    
    def create_variable_widget(self, variable: TemplateVariable):
        if variable.type == "string":
            widget = QLineEdit()
            if variable.default_value:
                widget.setText(str(variable.default_value))
            widget.setPlaceholderText(f"예: {variable.default_value or ''}")
            
        elif variable.type == "int" or variable.type == "port":
            widget = QSpinBox()
            widget.setMinimum(1)
            if variable.type == "port":
                widget.setMaximum(65535)
            else:
                widget.setMaximum(999999)
            if variable.default_value:
                widget.setValue(int(variable.default_value))
            
        elif variable.type == "boolean":
            widget = QCheckBox()
            if variable.default_value:
                widget.setChecked(bool(variable.default_value))
                
        elif variable.type == "choice":
            widget = QComboBox()
            # Add choices from validation rule or default choices
            choices = ["option1", "option2", "option3"]  # Could be parsed from validation_rule
            widget.addItems(choices)
            if variable.default_value:
                widget.setCurrentText(str(variable.default_value))
                
        else:
            # Default to string input
            widget = QLineEdit()
            if variable.default_value:
                widget.setText(str(variable.default_value))
        
        return widget

class SummaryPage(QWizardPage):
    def __init__(self, template: Template):
        super().__init__()
        self.template = template
        self.init_ui()
    
    def init_ui(self):
        self.setTitle("생성 확인")
        self.setSubTitle("설정한 내용을 확인하고 인스턴스를 생성합니다.")
        
        layout = QVBoxLayout(self)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)
    
    def initializePage(self):
        summary = "다음 설정으로 인스턴스가 생성됩니다:\n\n"
        summary += f"템플릿: {self.template.name}\n"
        summary += f"인스턴스 이름: {self.field('instance_name')}\n"
        summary += f"생성 위치: {self.field('output_dir')}\n\n"
        
        # Get variables from previous page
        variables_page = self.wizard().page(1)
        if hasattr(variables_page, 'variable_widgets') and variables_page.variable_widgets:
            summary += "변수 설정:\n"
            for var_name, widget in variables_page.variable_widgets.items():
                if isinstance(widget, QLineEdit):
                    value = widget.text()
                elif isinstance(widget, QSpinBox):
                    value = widget.value()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                elif isinstance(widget, QCheckBox):
                    value = "예" if widget.isChecked() else "아니오"
                else:
                    value = "N/A"
                
                summary += f"  {var_name}: {value}\n"
        
        self.summary_text.setText(summary)