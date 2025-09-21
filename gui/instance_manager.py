from typing import List

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QGroupBox,
                             QHeaderView, QMessageBox, QMenu, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent

from gui.result_widget import FileResultWindow
from models.instance import ServerInstance
from core.template_manager import TemplateManager
from models.result import FileResult
from utils.config import ConfigManager
import os
import subprocess
import platform

class InstanceManagerWidget(QGroupBox):
    def __init__(self):
        super().__init__("인스턴스 관리")
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.template_manager = TemplateManager(self.config.templates_dir)
        self.instances = []
        self.init_ui()
        self.refresh_instances()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.refresh_instances)
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.open_folder_btn = QPushButton("폴더 열기")
        self.open_folder_btn.clicked.connect(self.open_instances_folder)
        toolbar_layout.addWidget(self.open_folder_btn)
        
        self.bulk_update_btn = QPushButton("모든 인스턴스 업데이트")
        self.bulk_update_btn.clicked.connect(self.bulk_update_instances)
        self.bulk_update_btn.setEnabled(False)  # Initially disabled
        toolbar_layout.addWidget(self.bulk_update_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Instances table
        self.instances_table = QTableWidget()
        self.instances_table.setColumnCount(5)
        self.instances_table.setHorizontalHeaderLabels([
            "이름", "템플릿", "생성일", "수정일", "경로"
        ])
        
        # Set column widths
        header = self.instances_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        self.instances_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.instances_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.instances_table)
        
        # Info label
        self.info_label = QLabel("인스턴스가 없습니다.")
        layout.addWidget(self.info_label)
    
    def refresh_instances(self):
        # Reload config in case it changed
        self.config = self.config_manager.get_config()
        
        self.instances.clear()
        self.instances_table.setRowCount(0)
        
        # Search for instances in configured locations
        search_paths = [
            self.config.instances_dir,
            self.config.default_output_dir,
            os.path.join(os.getcwd(), "instances"),
            os.path.join(os.getcwd(), "output"),
            os.getcwd()
        ]
        
        # Remove duplicates while preserving order
        unique_paths = []
        for path in search_paths:
            if path and path not in unique_paths:
                unique_paths.append(path)
        
        found_instances = []
        searched_paths = []
        found_paths = set()  # Track unique instance paths to avoid duplicates
        
        for search_path in unique_paths:
            if os.path.exists(search_path):
                instances_in_path = self.find_instances_in_directory(search_path)
                # Filter out duplicates based on normalized instance path
                for instance in instances_in_path:
                    normalized_path = os.path.normpath(os.path.abspath(instance.path))
                    if normalized_path not in found_paths:
                        found_instances.append(instance)
                        found_paths.add(normalized_path)
                searched_paths.append(search_path)
        
        self.instances = found_instances
        self.populate_table()
        
        self.bulk_update_btn.setEnabled(len(self.instances) > 0)
        
        if self.instances:
            self.info_label.setText(
                f"{len(self.instances)}개의 인스턴스를 찾았습니다.\n"
                f"검색 경로: {', '.join(searched_paths)}"
            )
        else:
            self.info_label.setText(
                f"인스턴스가 없습니다. 새 인스턴스를 생성해보세요.\n"
                f"검색 경로: {', '.join(searched_paths)}"
            )
    
    def find_instances_in_directory(self, directory):
        instances = []
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    instance = ServerInstance.load_from_path(item_path)
                    if instance:
                        instances.append(instance)
        except PermissionError:
            pass
        
        return instances
    
    def populate_table(self):
        self.instances_table.setRowCount(len(self.instances))
        
        for row, instance in enumerate(self.instances):
            self.instances_table.setItem(row, 0, QTableWidgetItem(instance.name))
            self.instances_table.setItem(row, 1, QTableWidgetItem(instance.template_name))
            self.instances_table.setItem(row, 2, QTableWidgetItem(
                instance.created_at.strftime("%Y-%m-%d %H:%M")
            ))
            self.instances_table.setItem(row, 3, QTableWidgetItem(
                instance.updated_at.strftime("%Y-%m-%d %H:%M")
            ))
            self.instances_table.setItem(row, 4, QTableWidgetItem(instance.path))
            
            # Store instance object in first column for easy access
            self.instances_table.item(row, 0).setData(Qt.UserRole, instance)
    
    def show_context_menu(self, position):
        if self.instances_table.itemAt(position) is None:
            return
        
        row = self.instances_table.rowAt(position.y())
        if row < 0:
            return
        
        instance = self.instances_table.item(row, 0).data(Qt.UserRole)
        
        menu = QMenu(self)
        
        open_folder_action = menu.addAction("폴더 열기")
        open_folder_action.triggered.connect(lambda: self.open_instance_folder(instance))
        
        menu.addSeparator()
        
        update_action = menu.addAction("템플릿으로 업데이트")
        update_action.triggered.connect(lambda: self.update_instance(instance))

        dry_update_action = menu.addAction("Dry run")
        dry_update_action.triggered.connect(lambda: self.update_instance(instance, dry_run=True))

        menu.addSeparator()
        
        delete_action = menu.addAction("삭제")
        delete_action.triggered.connect(lambda: self.delete_instance(instance))
        
        menu.exec_(self.instances_table.mapToGlobal(position))
    
    def open_instance_folder(self, instance: ServerInstance):
        try:
            if platform.system() == "Windows":
                os.startfile(instance.path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", instance.path])
            else:  # Linux
                subprocess.run(["xdg-open", instance.path])
        except Exception as e:
            QMessageBox.warning(self, "오류", f"폴더를 열 수 없습니다:\n{str(e)}")
    
    def open_instances_folder(self):
        instances_dir = self.config.instances_dir
        if not os.path.exists(instances_dir):
            instances_dir = self.config.default_output_dir
        if not os.path.exists(instances_dir):
            instances_dir = QFileDialog.getExistingDirectory(self, "인스턴스 폴더 선택")
            if not instances_dir:
                return
        
        try:
            if platform.system() == "Windows":
                os.startfile(instances_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", instances_dir])
            else:  # Linux
                subprocess.run(["xdg-open", instances_dir])
        except Exception as e:
            QMessageBox.warning(self, "오류", f"폴더를 열 수 없습니다:\n{str(e)}")
    
    def update_instance(self, instance: ServerInstance, dry_run: bool = False):
        try:
            reply = QMessageBox.question(
                self, "확인",
                f"'{instance.name}' 인스턴스를 '{instance.template_name}' 템플릿으로 업데이트하시겠습니까?\n\n"
                "기존 파일들이 덮어쓰여집니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                result = self.template_manager.update_instance_from_template(instance, dry_run)
                self.refresh_instances()
                FileResultWindow(result.processed_files).exec_()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"인스턴스 업데이트 중 오류가 발생했습니다:\n{str(e)}")
    
    def delete_instance(self, instance: ServerInstance):
        reply = QMessageBox.question(
            self, "확인",
            f"'{instance.name}' 인스턴스를 삭제하시겠습니까?\n\n"
            f"경로: {instance.path}\n\n"
            "이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import shutil
                shutil.rmtree(instance.path)
                self.refresh_instances()
                QMessageBox.information(self, "완료", "인스턴스가 삭제되었습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"인스턴스 삭제 중 오류가 발생했습니다:\n{str(e)}")
    
    def bulk_update_instances(self):
        if not self.instances:
            QMessageBox.information(self, "알림", "업데이트할 인스턴스가 없습니다.")
            return
        
        # Group instances by template name
        template_groups = {}
        for instance in self.instances:
            template_name = instance.template_name
            if template_name not in template_groups:
                template_groups[template_name] = []
            template_groups[template_name].append(instance)
        
        # Show confirmation dialog with details
        message = f"총 {len(self.instances)}개의 인스턴스를 템플릿으로 업데이트하시겠습니까?\n\n"
        message += "템플릿별 인스턴스 개수:\n"
        for template_name, instances in template_groups.items():
            message += f"  • {template_name}: {len(instances)}개\n"
        message += "\n모든 인스턴스의 기존 파일들이 덮어쓰여집니다."
        
        reply = QMessageBox.question(
            self, "일괄 업데이트 확인", message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Perform bulk update
        updated_count = 0
        failed_count = 0
        failed_instances = []
        
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import Qt
        
        # Show progress dialog
        progress = QProgressDialog("인스턴스 업데이트 중...", "취소", 0, len(self.instances), self)
        progress.setWindowTitle("일괄 업데이트")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        file_results: List[FileResult] = []
        for i, instance in enumerate(self.instances):
            if progress.wasCanceled():
                break
                
            progress.setLabelText(f"업데이트 중: {instance.name}")
            progress.setValue(i)
            
            try:
                result = self.template_manager.update_instance_from_template(instance)
                file_results.extend(result.processed_files)
                updated_count += 1
            except Exception as e:
                failed_count += 1
                failed_instances.append(f"{instance.name}: {str(e)}")
            
            # Process events to keep UI responsive
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
        
        progress.setValue(len(self.instances))
        progress.close()
        
        # Refresh instances list
        self.refresh_instances()
        
        # Show results
        if failed_count == 0:
            QMessageBox.information(
                self, "완료", 
                f"모든 인스턴스가 성공적으로 업데이트되었습니다.\n\n"
                f"업데이트된 인스턴스: {updated_count}개"
            )
        else:
            error_details = "\n".join(failed_instances[:5])  # Show first 5 errors
            if len(failed_instances) > 5:
                error_details += f"\n... 및 {len(failed_instances) - 5}개 더"
            
            QMessageBox.warning(
                self, "일부 실패",
                f"일괄 업데이트가 완료되었습니다.\n\n"
                f"성공: {updated_count}개\n"
                f"실패: {failed_count}개\n\n"
                f"실패한 인스턴스:\n{error_details}"
            )

        FileResultWindow(file_results).exec_()