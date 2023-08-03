import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTabWidget, QFormLayout, QTableWidget, QTableWidgetItem, QComboBox,
    QHBoxLayout, QDialog, QGroupBox, QGridLayout, QDateEdit, QCheckBox, QDialogButtonBox,QFileDialog,
    QHeaderView
)
from PyQt5.QtCore import Qt, QDate
import pandas as pd



# Connect to the SQLite database
conn = sqlite3.connect("library_pc.db")
c = conn.cursor()

# Create the necessary tables if they don't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY,
        name TEXT,
        course TEXT,
        contact TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS computers (
        pc_id TEXT PRIMARY KEY,
        student_id INTEGER,
        status TEXT DEFAULT 'Vacant',
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        student_id INTEGER,
        pc_id TEXT,
        entry_time TEXT,
        exit_time TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (pc_id) REFERENCES computers(pc_id)
    )
''')


class AssignPcWidget(QWidget):
    def __init__(self, pc_management_widget, assignment_history_widget):
        super().__init__()

        self.layout = QVBoxLayout()
        self.pc_management_widget = pc_management_widget
        self.assignment_history_widget = assignment_history_widget

        student_id_input = QLineEdit()
        student_id_input.setPlaceholderText("Enter Student ID")

        self.layout.addWidget(student_id_input)

        assign_button = QPushButton("Assign PC")
        assign_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
                
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        assign_button.clicked.connect(lambda: self.validate_student_and_show_assign_pc_popup(student_id_input))
        self.layout.addWidget(assign_button)

        self.assignment_table = QTableWidget()
        self.assignment_table.setColumnCount(4)
        self.assignment_table.setHorizontalHeaderLabels(["Student ID", "PC ID", "Assign Time", "Unassign"])
        self.assignment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.assignment_table)

        self.setLayout(self.layout)

        # Display assignment history
        self.display_assignment_history()

    def validate_student_and_show_assign_pc_popup(self,student_id_input):
        student_id = student_id_input.text()

        # Check if the student ID exists in the students table
        c.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        student = c.fetchone()

        if student is None:
            QMessageBox.warning(self, "No Match Found", "No matching student found.")
        else:
            self.show_assign_pc_popup(student_id)


    def show_assign_pc_popup(self, student_id):
        popup = AssignPcPopup(student_id, self.get_vacant_pcs(), self.pc_management_widget, self.assignment_history_widget)
        if popup.exec_() == QDialog.Accepted:
            self.display_assignment_history()

    def get_vacant_pcs(self):
        c.execute("SELECT pc_id FROM computers WHERE status = 'Vacant'")
        vacant_pcs = c.fetchall()
        return [pc[0] for pc in vacant_pcs]

    def display_assignment_history(self):
        c.execute(
            "SELECT students.student_id, students.name, computers.pc_id, "
            "reservations.entry_time, reservations.exit_time "
            "FROM students "
            "JOIN reservations ON students.student_id = reservations.student_id "
            "JOIN computers ON computers.pc_id = reservations.pc_id "
            "WHERE computers.status != 'Vacant' AND reservations.exit_time IS NULL "
            "ORDER BY reservations.entry_time ASC"
        )
        assignment_data = c.fetchall()

        self.assignment_table.setRowCount(len(assignment_data))
        for row, assignment in enumerate(assignment_data):
            student_id, name, pc_id, entry_time, exit_time = assignment
            student_item = QTableWidgetItem(str(student_id))
            student_item.setData(Qt.UserRole, name)
            pc_item = QTableWidgetItem(pc_id)
            entry_time_item = QTableWidgetItem(entry_time)
            unassign_button = QPushButton("Unassign")
            unassign_button.clicked.connect(lambda checked, student_id=student_id: self.unassign_pc(student_id))

            self.assignment_table.setItem(row, 0, student_item)
            self.assignment_table.setItem(row, 1, pc_item)
            self.assignment_table.setItem(row, 2, entry_time_item)
            self.assignment_table.setCellWidget(row, 3, unassign_button)

        # self.assignment_table.resizeColumnsToContents()

    def unassign_pc(self, student_id):
        c.execute("UPDATE computers SET student_id = NULL, status = 'Vacant' WHERE student_id = ?", (student_id,))
        c.execute("UPDATE reservations SET exit_time = ? WHERE student_id = ? AND exit_time IS NULL",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), student_id))
        conn.commit()
        self.display_assignment_history()
        self.pc_management_widget.display_pcs()
        self.assignment_history_widget.display_assignment_history() #####################################################


class AssignPcPopup(QDialog):
    def __init__(self, student_id, vacant_pcs, pc_management_widget,assignment_history_widget):
        super().__init__()

        self.setWindowTitle("Assign PC")
        self.student_id = student_id
        self.pc_management_widget = pc_management_widget
        self.assignment_history_widget=assignment_history_widget
        self.layout = QVBoxLayout()

        student_info_group = QGroupBox("Student Information")
        student_info_layout = QVBoxLayout()
        student_info_group.setLayout(student_info_layout)

        # Fetch the student details from the database
        c.execute("SELECT name, course, contact FROM students WHERE student_id = ?", (student_id,))
        student_data = c.fetchone()
        if student_data:
            name, course, contact = student_data

            student_id_label = QLabel(f"Student ID: {student_id}")
            student_info_layout.addWidget(student_id_label)

            name_label = QLabel(f"Name: {name}")
            student_info_layout.addWidget(name_label)

            course_label = QLabel(f"Course: {course}")
            student_info_layout.addWidget(course_label)

            contact_label = QLabel(f"Contact: {contact}")
            student_info_layout.addWidget(contact_label)

        self.layout.addWidget(student_info_group)

        pc_selection_group = QGroupBox("PC Selection")
        pc_selection_layout = QVBoxLayout()
        pc_selection_group.setLayout(pc_selection_layout)

        self.pc_combo = QComboBox()
        pc_selection_layout.addWidget(self.pc_combo)

        self.layout.addWidget(pc_selection_group)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.assign_pc(student_id))
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)

        # Populate the PC options
        self.pc_combo.addItems(vacant_pcs)

    def assign_pc(self,student_id):
        pc_id = self.pc_combo.currentText()

        # Check if the student is already assigned
        c.execute("SELECT student_id FROM computers WHERE student_id = ?", (student_id,))
        assigned_student = c.fetchone()

        if assigned_student is not None:
            QMessageBox.warning(self, "Error", "The Student is already assigned to a PC.")
            return

        # Update the database with the assignment
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO reservations VALUES (?, ?, ?, NULL)", (self.student_id, pc_id, entry_time))
        conn.commit()

        # Update PC status to 'Assigned'
        c.execute("UPDATE computers SET student_id = ?, status = 'Assigned' WHERE pc_id = ?", (self.student_id, pc_id))
        conn.commit()

        QMessageBox.information(self, "PC Assigned", "PC assigned successfully!")
        self.accept()
        
        self.pc_management_widget.display_pcs()
        self.assignment_history_widget.display_assignment_history()
        


class PCManagementWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        pc_input_layout = QHBoxLayout()

        pc_id_input = QLineEdit()
        pc_id_input.setPlaceholderText("Enter PC ID")
        pc_input_layout.addWidget(pc_id_input)

        add_button = QPushButton("Add")
        add_button.clicked.connect(lambda: self.add_pc(pc_id_input.text()))
        pc_input_layout.addWidget(add_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_pc(pc_id_input.text()))
        pc_input_layout.addWidget(delete_button)

        self.layout.addLayout(pc_input_layout)

        self.pc_table = QTableWidget()
        self.pc_table.setColumnCount(2)
        self.pc_table.setHorizontalHeaderLabels(["PC ID", "Status"])
        self.pc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.pc_table)

        self.setLayout(self.layout)

        # Display PC information
        self.display_pcs()

    def display_pcs(self):
        c.execute("SELECT pc_id, status FROM computers")
        pc_data = c.fetchall()
        print("DIsplaying.........")
        self.pc_table.setRowCount(len(pc_data))
        for row, pc in enumerate(pc_data):
            pc_id, status = pc
            pc_item = QTableWidgetItem(pc_id)
            status_item = QTableWidgetItem(status)

            self.pc_table.setItem(row, 0, pc_item)
            self.pc_table.setItem(row, 1, status_item)

        # self.pc_table.resizeColumnsToContents()

    def add_pc(self, pc_id):
        if not pc_id:
            QMessageBox.warning(self, "Error", "Please enter a PC ID.")
            return

        # Check if the PC ID already exists
        c.execute("SELECT pc_id FROM computers WHERE pc_id = ?", (pc_id,))
        existing_pc = c.fetchone()
        if existing_pc:
            QMessageBox.warning(self, "Error", "PC ID already exists.")
            return

        # Insert the new PC into the database
        c.execute("INSERT INTO computers (pc_id) VALUES (?)", (pc_id,))
        conn.commit()

        QMessageBox.information(self, "PC Added", "PC added successfully!")
        self.display_pcs()

    def delete_pc(self, pc_id):
        if not pc_id:
            QMessageBox.warning(self, "Error", "Please enter a PC ID.")
            return

        # Check if the PC ID exists
        c.execute("SELECT pc_id FROM computers WHERE pc_id = ?", (pc_id,))
        existing_pc = c.fetchone()
        if not existing_pc:
            QMessageBox.warning(self, "Error", "PC ID does not exist.")
            return

        # Check if the PC is currently assigned
        c.execute("SELECT student_id FROM computers WHERE pc_id = ?", (pc_id,))
        pc_status = c.fetchone()[0]

        if pc_status is not None:
            QMessageBox.warning(self, "Error", "Cannot delete an assigned PC.")
            return

        # Delete the PC from the database
        c.execute("DELETE FROM computers WHERE pc_id = ?", (pc_id,))
        conn.commit()

        QMessageBox.information(self, "PC Deleted", "PC deleted successfully!")
        self.display_pcs()


class StudentManagementWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.student_id_input = QLineEdit()
        form_layout.addRow("Student ID:", self.student_id_input)

        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)

        self.course_combo = QComboBox()
        self.course_combo.addItem("FYBSC CS")
        self.course_combo.addItem("SYBSC CS")
        self.course_combo.addItem("TYBSC CS")
        self.course_combo.addItem("FYBSC IT")
        self.course_combo.addItem("SYBSC IT")
        self.course_combo.addItem("TYBSC IT")
        form_layout.addRow("Course:", self.course_combo)

        self.contact_input = QLineEdit()
        form_layout.addRow("Contact:", self.contact_input)

        add_student_button = QPushButton("Add Student")
        add_student_button.clicked.connect(self.add_student)
        form_layout.addRow(add_student_button)

        self.layout.addLayout(form_layout)

        self.students_table = QTableWidget()
        self.students_table.setColumnCount(4)
        self.students_table.setHorizontalHeaderLabels(["Student ID", "Name", "Course", "Contact"])
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.students_table)

        self.setLayout(self.layout)

        # Display student data
        self.display_students()

    def display_students(self):
        c.execute("SELECT * FROM students")
        student_data = c.fetchall()

        self.students_table.setRowCount(len(student_data))
        for row, student in enumerate(student_data):
            student_id, name, course, contact = student

            student_id_item = QTableWidgetItem(str(student_id))
            name_item = QTableWidgetItem(name)
            course_item = QTableWidgetItem(course)
            contact_item = QTableWidgetItem(contact)

            self.students_table.setItem(row, 0, student_id_item)
            self.students_table.setItem(row, 1, name_item)
            self.students_table.setItem(row, 2, course_item)
            self.students_table.setItem(row, 3, contact_item)

        # self.students_table.resizeColumnsToContents()

    def add_student(self):
        student_id = self.student_id_input.text()
        name = self.name_input.text()
        course = self.course_combo.currentText()
        contact = self.contact_input.text()

        if not (student_id and name and course and contact):
            QMessageBox.warning(self, "Error", "Please enter all fields.")
            return

        # Check if the student ID already exists
        c.execute("SELECT student_id FROM students WHERE student_id = ?", (student_id,))
        existing_student = c.fetchone()
        if existing_student:
            QMessageBox.warning(self, "Error", "Student ID already exists.")
            return

        # Insert the new student into the database
        c.execute("INSERT INTO students (student_id, name, course, contact) VALUES (?, ?, ?, ?)",
                  (student_id, name, course, contact))
        conn.commit()

        QMessageBox.information(self, "Student Added", "Student added successfully!")

        # Clear the input fields
        self.student_id_input.clear()
        self.name_input.clear()
        self.contact_input.clear()

        # Refresh student data
        self.display_students()


class AssignmentHistoryWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        filter_layout = QGridLayout()
        filter_layout.addWidget(QLabel("Filter Options:"), 0, 0, 1, 2)

        self.filter_date_checkbox = QCheckBox("Filter by Date:")
        self.filter_date_checkbox.stateChanged.connect(self.enable_filter_date)
        filter_layout.addWidget(self.filter_date_checkbox, 1, 0)
        self.filter_date_input = QDateEdit()
        self.filter_date_input.setCalendarPopup(True)
        self.filter_date_input.setDate(QDate.currentDate())
        self.filter_date_input.setEnabled(False)
        filter_layout.addWidget(self.filter_date_input, 1, 1)

        self.filter_student_checkbox = QCheckBox("Filter by Student ID:")
        self.filter_student_checkbox.stateChanged.connect(self.enable_filter_student)
        filter_layout.addWidget(self.filter_student_checkbox, 2, 0)
        self.filter_student_input = QLineEdit()
        self.filter_student_input.setEnabled(False)
        filter_layout.addWidget(self.filter_student_input, 2, 1)

        self.filter_pc_checkbox = QCheckBox("Filter by PC ID:")
        self.filter_pc_checkbox.stateChanged.connect(self.enable_filter_pc)
        filter_layout.addWidget(self.filter_pc_checkbox, 3, 0)
        self.filter_pc_input = QLineEdit()
        self.filter_pc_input.setEnabled(False)
        filter_layout.addWidget(self.filter_pc_input, 3, 1)

        self.filter_button = QPushButton("Apply Filter")
        self.filter_button.clicked.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_button, 4, 0, 1, 2)

        self.layout.addLayout(filter_layout)

        export_button = QPushButton("Export to Excel")
        export_button.clicked.connect(self.export_to_excel)
        self.layout.addWidget(export_button)

        self.assignment_table = QTableWidget()
        self.assignment_table.setColumnCount(6)
        self.assignment_table.setHorizontalHeaderLabels(["Student ID", "Name", "PC ID", "Entry Time", "Exit Time", "Duration"])
        self.assignment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.assignment_table)

        self.setLayout(self.layout)

        # Display assignment history
        self.display_assignment_history()

        self.assignment_data = []

    def enable_filter_date(self, state):
        self.filter_date_input.setEnabled(state == Qt.Checked)

    def enable_filter_student(self, state):
        self.filter_student_input.setEnabled(state == Qt.Checked)

    def enable_filter_pc(self, state):
        self.filter_pc_input.setEnabled(state == Qt.Checked)

    def apply_filter(self):
        filter_date = self.filter_date_input.date().toString(Qt.ISODate)
        filter_student_id = self.filter_student_input.text()
        filter_pc_id = self.filter_pc_input.text()

        query = (
            "SELECT students.student_id, students.name, computers.pc_id, "
            "reservations.entry_time, reservations.exit_time "
            "FROM students "
            "JOIN reservations ON students.student_id = reservations.student_id "
            "JOIN computers ON computers.pc_id = reservations.pc_id "
            "WHERE "
        )

        filters = []

        if self.filter_date_checkbox.isChecked():
            filters.append(f"reservations.entry_time LIKE '{filter_date}%'")

        if self.filter_student_checkbox.isChecked():
            filters.append(f"students.student_id = '{filter_student_id}'")

        if self.filter_pc_checkbox.isChecked():
            filters.append(f"computers.pc_id = '{filter_pc_id}'")

        if filters:
            query += " AND ".join(filters)
        else:
            query = (
                "SELECT students.student_id, students.name, computers.pc_id, "
                "reservations.entry_time, reservations.exit_time "
                "FROM students "
                "JOIN reservations ON students.student_id = reservations.student_id "
                "JOIN computers ON computers.pc_id = reservations.pc_id "
            )

        query += " ORDER BY reservations.entry_time DESC"

        c.execute(query)
        assignment_data = c.fetchall()

        self.assignment_table.setRowCount(len(assignment_data))
        for row, assignment in enumerate(assignment_data):
            student_id, name, pc_id, entry_time, exit_time = assignment
            student_item = QTableWidgetItem(str(student_id))
            student_item.setData(Qt.UserRole, name)
            pc_item = QTableWidgetItem(pc_id)
            entry_time_item = QTableWidgetItem(entry_time)
            exit_time_item = QTableWidgetItem(exit_time if exit_time else "")

            # Calculate the duration if the PC is currently assigned
            duration_item = QTableWidgetItem()
            if exit_time:
                duration = datetime.strptime(exit_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
                duration_item.setText(str(duration))

            self.assignment_table.setItem(row, 0, student_item)
            self.assignment_table.setItem(row, 1, QTableWidgetItem(name))
            self.assignment_table.setItem(row, 2, pc_item)
            self.assignment_table.setItem(row, 3, entry_time_item)
            self.assignment_table.setItem(row, 4, exit_time_item)
            self.assignment_table.setItem(row, 5, duration_item)

    def display_assignment_history(self):
        c.execute(
            "SELECT students.student_id, students.name, computers.pc_id, "
            "reservations.entry_time, reservations.exit_time "
            "FROM students "
            "JOIN reservations ON students.student_id = reservations.student_id "
            "JOIN computers ON computers.pc_id = reservations.pc_id "
            "ORDER BY reservations.entry_time DESC"
        )
        assignment_data = c.fetchall()

        self.assignment_table.setRowCount(len(assignment_data))
        for row, assignment in enumerate(assignment_data):
            student_id, name, pc_id, entry_time, exit_time = assignment
            student_item = QTableWidgetItem(str(student_id))
            student_item.setData(Qt.UserRole, name)
            pc_item = QTableWidgetItem(pc_id)
            entry_time_item = QTableWidgetItem(entry_time)
            exit_time_item = QTableWidgetItem(exit_time if exit_time else "")

            # Calculate the duration if the PC is currently assigned
            duration_item = QTableWidgetItem()
            if exit_time:
                duration = datetime.strptime(exit_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
                duration_item.setText(str(duration))

            self.assignment_table.setItem(row, 0, student_item)
            self.assignment_table.setItem(row, 1, QTableWidgetItem(name))
            self.assignment_table.setItem(row, 2, pc_item)
            self.assignment_table.setItem(row, 3, entry_time_item)
            self.assignment_table.setItem(row, 4, exit_time_item)
            self.assignment_table.setItem(row, 5, duration_item)


    def export_to_excel(self):
        # Retrieve the data from the QTableWidget
        table_data = []
        for row in range(self.assignment_table.rowCount()):
            row_data = []
            for col in range(self.assignment_table.columnCount()):
                item = self.assignment_table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")  # Append an empty string for empty cells
            table_data.append(row_data)

        if not table_data:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return

        # Convert the data to a Pandas DataFrame
        columns = ["Student ID", "Name", "PC ID", "Entry Time", "Exit Time", "Duration"]
        df = pd.DataFrame(table_data, columns=columns)

        # Open a file dialog to choose the export path
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix(".xlsx")
        options = file_dialog.Options()
        options |= file_dialog.DontUseNativeDialog
        file_path, _ = file_dialog.getSaveFileName(self, "Save Assignment Data", "", "Excel Files (*.xlsx);;All Files (*)", options=options)

        if file_path:
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"  # Ensure the file has a .xlsx extension

            try:
                # Export the DataFrame to an Excel file
                df.to_excel(file_path, index=False, engine="xlsxwriter")
                QMessageBox.information(self, "Export Successful", "Assignment data exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"An error occurred while exporting the data: {str(e)}")

class UploadExcelTab(QWidget):
    def __init__(self, studentManagementWidget):
        super().__init__()
        self.studentManagementWidget = studentManagementWidget
        self.layout = QVBoxLayout()

        upload_button = QPushButton("Upload Excel File")
        upload_button.clicked.connect(self.upload_excel_file)
        self.layout.addWidget(upload_button)

        self.uploaded_data_table = QTableWidget()
        self.layout.addWidget(self.uploaded_data_table)
        self.uploaded_data_table.setHorizontalHeaderLabels(["PC ID", "Status"])
        self.uploaded_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setLayout(self.layout)
        
    def upload_excel_file(self):
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix(".xlsx")
        options = file_dialog.Options()
        options |= file_dialog.DontUseNativeDialog
        file_path, _ = file_dialog.getOpenFileName(self, "Upload Excel File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)

        if file_path:
            try:
                # Read the Excel file into a DataFrame
                df = pd.read_excel(file_path)

                # Display the data in the QTableWidget
                self.uploaded_data_table.setRowCount(df.shape[0])
                self.uploaded_data_table.setColumnCount(df.shape[1])
                self.uploaded_data_table.setHorizontalHeaderLabels(df.columns.tolist())

                for row in range(df.shape[0]):
                    for col in range(df.shape[1]):
                        item = QTableWidgetItem(str(df.iat[row, col]))
                        self.uploaded_data_table.setItem(row, col, item)

                # Save the data to the student table in the database
                conn = sqlite3.connect("library_pc.db")
                cursor = conn.cursor()
                for row in df.itertuples(index=False):
                    cursor.execute("INSERT INTO students (student_id, name, course, contact) VALUES (?, ?, ?, ?)", row)
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Upload Successful", "Data uploaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Upload Error", f"An error occurred while uploading the data: {str(e)}")
        self.studentManagementWidget.display_students()


class LibraryPcManagement(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Library PC Management")
        self.setGeometry(200, 200, 800, 600)

        tab_widget = QTabWidget()

        assign_pc_widget = AssignPcWidget(self,self)
        tab_widget.addTab(assign_pc_widget, "Assign PC")

        pc_management_widget = PCManagementWidget()
        tab_widget.addTab(pc_management_widget, "PC Management")

        student_management_widget = StudentManagementWidget()
        tab_widget.addTab(student_management_widget, "Student Management")

        assignment_history_widget = AssignmentHistoryWidget()
        tab_widget.addTab(assignment_history_widget, "Assignment History")

        upload_excel_tab = UploadExcelTab(self)
        tab_widget.addTab(upload_excel_tab, "Upload Excel")

        self.setCentralWidget(tab_widget)

    def display_pcs(self):
        # Retrieve and display PC data
        pc_management_widget = self.findChild(PCManagementWidget)
        if pc_management_widget:
            pc_management_widget.display_pcs()
    
    def display_assignment_history(self):
        # Retrieve and display PC data
        assignment_history_widget = self.findChild(AssignmentHistoryWidget)
        if assignment_history_widget:
            assignment_history_widget.display_assignment_history()

    def display_students(self):
        student_management_widget=self.findChild(StudentManagementWidget)
        if student_management_widget:
            student_management_widget.display_students()

if __name__ == "__main__":
    app = QApplication([])
    window = LibraryPcManagement()
    window.show()
    app.exec_()