import sys
import csv
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QFileDialog,
                             QMessageBox, QHeaderView, QMenuBar, QMenu, QSplitter,
                             QTextEdit, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor


class FinancialCalculator:
    """金融计算工具类"""
    
    @staticmethod
    def calculate_total_interest(monthly_interest: float, periods: int) -> float:
        """计算总利息"""
        return monthly_interest * periods
    
    @staticmethod
    def calculate_interest_rate(total_interest: float, principal: float) -> float:
        """计算利息率"""
        if principal <= 0:
            return 0.0
        return (total_interest / principal) * 100
    
    @staticmethod
    def calculate_monthly_payment(principal: float, total_interest: float, periods: int) -> float:
        """计算每期支付金额"""
        if periods <= 0:
            return 0.0
        return (principal + total_interest) / periods
    
    @staticmethod
    def calculate_irr(principal: float, monthly_payment: float, periods: int) -> float:
        """使用牛顿迭代法计算月IRR"""
        if principal <= 0 or monthly_payment <= 0 or periods <= 0:
            return 0.0
            
        def npv(rate: float) -> float:
            """计算净现值"""
            if rate <= -1:
                return float('inf')
            total = -principal
            for i in range(1, periods + 1):
                total += monthly_payment / ((1 + rate) ** i)
            return total
        
        def npv_derivative(rate: float) -> float:
            """计算净现值的导数"""
            if rate <= -1:
                return float('inf')
            total = 0.0
            for i in range(1, periods + 1):
                total -= i * monthly_payment / ((1 + rate) ** (i + 1))
            return total
        
        # 牛顿迭代法
        irr = 0.01  # 初始值1%
        max_iterations = 100
        tolerance = 1e-6
        
        for _ in range(max_iterations):
            current_npv = npv(irr)
            derivative = npv_derivative(irr)
            
            if abs(derivative) < 1e-10:
                break
                
            new_irr = irr - current_npv / derivative
            
            if abs(new_irr - irr) < tolerance:
                break
                
            irr = new_irr
            
            if irr < -0.999:  # 防止发散
                irr = -0.99
        
        return max(0, irr)  # 确保非负
    
    @staticmethod
    def calculate_annual_rate(monthly_irr: float) -> float:
        """计算年化利率"""
        return monthly_irr * 12 * 100


class LoanRecord:
    """贷款记录数据类"""
    
    def __init__(self, name: str = "", principal: float = 0.0, periods: int = 0,
                 monthly_interest: Optional[float] = None, total_interest: Optional[float] = None,
                 timestamp: Optional[str] = None):
        self.name = name
        self.principal = principal
        self.periods = periods
        self.monthly_interest = monthly_interest
        self.total_interest = total_interest
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 自动计算缺失的值
        self._auto_calculate()
    
    def _auto_calculate(self):
        """自动计算缺失的利息数据"""
        if self.monthly_interest is not None and self.total_interest is None:
            self.total_interest = FinancialCalculator.calculate_total_interest(
                self.monthly_interest, self.periods)
        elif self.total_interest is not None and self.monthly_interest is None:
            if self.periods > 0:
                self.monthly_interest = self.total_interest / self.periods
    
    @property
    def interest_rate(self) -> float:
        """利息率"""
        return FinancialCalculator.calculate_interest_rate(
            self.total_interest or 0, self.principal)
    
    @property
    def monthly_payment(self) -> float:
        """每期支付金额"""
        return FinancialCalculator.calculate_monthly_payment(
            self.principal, self.total_interest or 0, self.periods)
    
    @property
    def monthly_irr(self) -> float:
        """月IRR"""
        return FinancialCalculator.calculate_irr(
            self.principal, self.monthly_payment, self.periods)
    
    @property
    def annual_rate(self) -> float:
        """年化利率"""
        return FinancialCalculator.calculate_annual_rate(self.monthly_irr)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'principal': self.principal,
            'periods': self.periods,
            'monthly_interest': self.monthly_interest,
            'total_interest': self.total_interest,
            'interest_rate': self.interest_rate,
            'annual_rate': self.annual_rate,
            'timestamp': self.timestamp
        }


class LoanCalculatorWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.records: List[LoanRecord] = []
        self.current_sort_column = 0
        self.sort_order = Qt.SortOrder.AscendingOrder
        
        self.init_ui()
        self.load_default_data()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('贷款分期金融计算器')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建主部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：输入面板
        left_panel = self.create_input_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：表格显示
        right_panel = self.create_table_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: 1px solid #3d8b40;
                font-weight: bold;
            }
        """)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        save_action = QAction('保存CSV', self)
        save_action.triggered.connect(self.save_to_csv)
        file_menu.addAction(save_action)
        
        load_action = QAction('加载CSV', self)
        load_action.triggered.connect(self.load_from_csv)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def create_input_panel(self) -> QWidget:
        """创建输入面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 输入组
        input_group = QGroupBox("添加新记录")
        input_layout = QFormLayout(input_group)
        
        # 输入字段
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("贷款机构或产品名称")
        
        self.principal_input = QDoubleSpinBox()
        self.principal_input.setRange(0.01, 10000000.0)
        self.principal_input.setDecimals(2)
        self.principal_input.setSuffix(" 元")
        self.principal_input.setSingleStep(1000)
        
        self.periods_input = QSpinBox()
        self.periods_input.setRange(1, 360)
        self.periods_input.setSuffix(" 期")
        
        self.monthly_interest_input = QDoubleSpinBox()
        self.monthly_interest_input.setRange(0.0, 100000.0)
        self.monthly_interest_input.setDecimals(2)
        self.monthly_interest_input.setSuffix(" 元")
        self.monthly_interest_input.setSingleStep(10)
        self.monthly_interest_input.setSpecialValueText("自动计算")
        
        self.total_interest_input = QDoubleSpinBox()
        self.total_interest_input.setRange(0.0, 1000000.0)
        self.total_interest_input.setDecimals(2)
        self.total_interest_input.setSuffix(" 元")
        self.total_interest_input.setSingleStep(100)
        self.total_interest_input.setSpecialValueText("自动计算")
        
        # 添加到表单
        input_layout.addRow("名称/机构:", self.name_input)
        input_layout.addRow("借款金额:", self.principal_input)
        input_layout.addRow("期数:", self.periods_input)
        input_layout.addRow("每期利息:", self.monthly_interest_input)
        input_layout.addRow("总利息:", self.total_interest_input)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("添加记录")
        add_button.clicked.connect(self.add_record)
        
        clear_button = QPushButton("清空输入")
        clear_button.clicked.connect(self.clear_inputs)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(clear_button)
        
        input_layout.addRow(button_layout)
        layout.addWidget(input_group)
        
        # 计算说明
        info_group = QGroupBox("计算说明")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        info_text.setPlainText(
            "计算规则:\n"
            "• 总利息 = 每期利息 × 期数\n"
            "• 利息率 = (总利息 ÷ 本金) × 100%\n"
            "• 年化利率 = 月IRR × 12\n"
            "• 只需填写每期利息或总利息之一，另一个会自动计算"
        )
        
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_table_panel(self) -> QWidget:
        """创建表格面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "名称/机构", "借款金额", "期数", "每期利息", 
            "总利息", "利息率(%)", "年化利率(%)", "添加时间"
        ])
        
        # 设置表格属性
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        # 连接排序信号
        header.sectionClicked.connect(self.sort_table)
        
        layout.addWidget(self.table)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        delete_button = QPushButton("删除选中")
        delete_button.clicked.connect(self.delete_selected)
        
        clear_all_button = QPushButton("清空所有")
        clear_all_button.clicked.connect(self.clear_all_records)
        
        refresh_button = QPushButton("刷新表格")
        refresh_button.clicked.connect(self.refresh_table)
        
        button_layout.addWidget(delete_button)
        button_layout.addWidget(clear_all_button)
        button_layout.addStretch()
        button_layout.addWidget(refresh_button)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def load_default_data(self):
        """加载默认数据"""
        default_records = [
            LoanRecord("银行A", 10000, 12, 50),
            LoanRecord("银行B", 20000, 24, 80),
            LoanRecord("银行C", 5000, 6, 30),
        ]
        self.records = default_records
        self.refresh_table()
    
    def add_record(self):
        """添加新记录"""
        name = self.name_input.text().strip()
        principal = self.principal_input.value()
        periods = self.periods_input.value()
        monthly_interest = self.monthly_interest_input.value()
        total_interest = self.total_interest_input.value()
        
        # 验证输入
        if not name:
            QMessageBox.warning(self, "警告", "请输入贷款机构或产品名称")
            return
            
        if principal <= 0:
            QMessageBox.warning(self, "警告", "借款金额必须大于0")
            return
            
        if periods <= 0:
            QMessageBox.warning(self, "警告", "期数必须大于0")
            return
        
        # 处理利息输入
        if monthly_interest == 0 and total_interest == 0:
            QMessageBox.warning(self, "警告", "请输入每期利息或总利息")
            return
        
        # 创建记录
        record = LoanRecord(
            name=name,
            principal=principal,
            periods=periods,
            monthly_interest=monthly_interest if monthly_interest > 0 else None,
            total_interest=total_interest if total_interest > 0 else None
        )
        
        self.records.append(record)
        self.refresh_table()
        self.clear_inputs()
        
        QMessageBox.information(self, "成功", "记录添加成功！")
    
    def clear_inputs(self):
        """清空输入"""
        self.name_input.clear()
        self.principal_input.setValue(0)
        self.periods_input.setValue(12)
        self.monthly_interest_input.setValue(0)
        self.total_interest_input.setValue(0)
    
    def refresh_table(self):
        """刷新表格显示"""
        self.table.setRowCount(len(self.records))
        
        for row, record in enumerate(self.records):
            items = [
                QTableWidgetItem(record.name),
                QTableWidgetItem(f"{record.principal:.2f}"),
                QTableWidgetItem(str(record.periods)),
                QTableWidgetItem(f"{record.monthly_interest or 0:.2f}"),
                QTableWidgetItem(f"{record.total_interest or 0:.2f}"),
                QTableWidgetItem(f"{record.interest_rate:.2f}"),
                QTableWidgetItem(f"{record.annual_rate:.2f}"),
                QTableWidgetItem(record.timestamp)
            ]
            
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col in [1, 3, 4, 5, 6]:  # 数值列右对齐
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)
    
    def sort_table(self, column: int):
        """排序表格"""
        if column == self.current_sort_column:
            self.sort_order = Qt.SortOrder.DescendingOrder if self.sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            self.current_sort_column = column
            self.sort_order = Qt.SortOrder.AscendingOrder
        
        self.table.sortItems(column, self.sort_order)
    
    def delete_selected(self):
        """删除选中记录"""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.records):
            reply = QMessageBox.question(self, "确认", "确定要删除选中的记录吗？")
            if reply == QMessageBox.StandardButton.Yes:
                del self.records[current_row]
                self.refresh_table()
    
    def clear_all_records(self):
        """清空所有记录"""
        if self.records:
            reply = QMessageBox.question(self, "确认", "确定要清空所有记录吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self.records.clear()
                self.refresh_table()
    
    def save_to_csv(self):
        """保存到CSV文件"""
        if not self.records:
            QMessageBox.warning(self, "警告", "没有数据可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件", "", "CSV文件 (*.csv)")
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        "名称/机构", "借款金额", "期数", "每期利息",
                        "总利息", "利息率(%)", "年化利率(%)", "添加时间"
                    ])
                    
                    for record in self.records:
                        writer.writerow([
                            record.name,
                            f"{record.principal:.2f}",
                            record.periods,
                            f"{record.monthly_interest or 0:.2f}",
                            f"{record.total_interest or 0:.2f}",
                            f"{record.interest_rate:.2f}",
                            f"{record.annual_rate:.2f}",
                            record.timestamp
                        ])
                
                QMessageBox.information(self, "成功", f"数据已保存到:\n{filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件时出错:\n{str(e)}")
    
    def load_from_csv(self):
        """从CSV文件加载"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载CSV文件", "", "CSV文件 (*.csv)")
        
        if filename:
            try:
                new_records = []
                with open(filename, 'r', encoding='utf-8-sig') as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for row in reader:
                        try:
                            record = LoanRecord(
                                name=row.get("名称/机构", ""),
                                principal=float(row.get("借款金额", 0)),
                                periods=int(row.get("期数", 0)),
                                monthly_interest=float(row.get("每期利息", 0)) if float(row.get("每期利息", 0)) > 0 else None,
                                total_interest=float(row.get("总利息", 0)) if float(row.get("总利息", 0)) > 0 else None,
                                timestamp=row.get("添加时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            new_records.append(record)
                        except (ValueError, KeyError) as e:
                            continue  # 跳过格式错误的行
                
                if new_records:
                    self.records = new_records
                    self.refresh_table()
                    QMessageBox.information(self, "成功", f"已加载 {len(new_records)} 条记录")
                else:
                    QMessageBox.warning(self, "警告", "未找到有效数据")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载文件时出错:\n{str(e)}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = LoanCalculatorWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()