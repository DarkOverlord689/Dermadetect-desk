import os
import csv
from datetime import datetime
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QFileDialog, QLabel, QTableWidgetItem, QTableWidget, QApplication, QGridLayout, QTabWidget
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from load_and_predict import predicto, ImagePreprocessor
from ui_components import create_main_layout
from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QHttpMultiPart, QHttpPart
from PyQt6.QtCore import QUrl, QByteArray, QBuffer, QIODevice
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrlQuery
import json
class MelanomaDetector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.models = {
            'DenseNet': 'best_model_DenseNet121.h5',
            'ResNet': 'best_model_ResNet50.h5',
            'Xception': 'best_model_Xception.h5',
            'MobileNet': 'best_model_MobileNet.h5',
            'Inception': 'best_model_InceptionV3.h5',
            'EfficientNet': 'best_model_EfficientNetV2B0.h5'
        }

        self.current_model = None
        self.preprocessor = ImagePreprocessor()
        self.image_history = []
        self.current_image = None
        self.cancer_types = {
            'melanoma': 'Melanoma',
            'basal cell carcinoma': 'Basocelular',
            'squamous cell carcinoma': 'Escamocelular',
        }
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Dermadetect')
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Crear el QTabWidget principal
        self.main_tab_widget = QTabWidget()
        main_layout.addWidget(self.main_tab_widget)

        # Crear las pestañas principales
        self.results_tab = QWidget()
        self.history_tab = QWidget()
        self.comparison_tab = QWidget()

        # Añadir las pestañas al QTabWidget principal
        self.main_tab_widget.addTab(self.results_tab, "Resultados")
        self.main_tab_widget.addTab(self.history_tab, "Historial")
        self.main_tab_widget.addTab(self.comparison_tab, "Comparación")

        # Configurar el contenido de las pestañas
        self.setup_results_tab()
        self.setup_history_tab()
        self.setup_comparison_tab()

    def setup_results_tab(self):
        results_layout = QVBoxLayout(self.results_tab)
        results_content = create_main_layout(self)
        results_layout.addWidget(results_content)

    def setup_history_tab(self):
        history_layout = QVBoxLayout(self.history_tab)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels(['Fecha', 'Nombre', 'Identificación', 'Edad', 'Sexo', 'Localización', 'Imagen', 'Clase Predicha', 'Probabilidades'])
        history_layout.addWidget(self.history_table)

    def setup_comparison_tab(self):
        comparison_layout = QVBoxLayout(self.comparison_tab)
        self.comparison_grid = QGridLayout()
        comparison_widget = QWidget()
        comparison_widget.setLayout(self.comparison_grid)
        comparison_layout.addWidget(comparison_widget)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", "Archivos de Imagen (*.png *.jpg *.bmp)")
        if file_name:
            pixmap = QPixmap(file_name)
            self.image_viewer.set_image(pixmap)
            self.current_image = file_name
            self.image_history.append(file_name)
            self.result_text.clear()
    def analyze_image(self):
        if not self.current_image:
            self.result_text.setText("<p style='color: red;'>Por favor, cargue una imagen primero.</p>")
            return

        patient_data = self.get_patient_data()
        self.send_analysis_request(patient_data)

    def get_patient_data(self):
        return {
            "name": self.name_input.text(),
            "identification": self.id_input.text(),
            "age": self.age_input.text(),
            "sex": self.sex_input.currentText(),
            "localization": self.location_input.currentText()
        }

    def send_analysis_request(self, patient_data):
        # Crear un QNetworkAccessManager
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_analysis_response)

        # Preparar la solicitud
        url = QUrl("http://localhost:8000/predict")
        request = QNetworkRequest(url)

        # Configurar la solicitud para envío multipart
        boundary = b"----WebKitFormBoundary7MA4YWxkTrZu0gW"
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, f"multipart/form-data; boundary={boundary.decode()}")

        # Crear el cuerpo multipart
        body = QByteArray()
        
        # Añadir los campos de texto
        for key, value in patient_data.items():
            body.append(b"--" + boundary + b"\r\n")
            body.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body.append(f"{value}\r\n".encode())

        # Añadir la imagen
        with open(self.current_image, 'rb') as f:
            image_data = f.read()

        body.append(b"--" + boundary + b"\r\n")
        body.append(b'Content-Disposition: form-data; name="file"; filename="image.jpg"\r\n')
        body.append(b"Content-Type: image/jpeg\r\n\r\n")
        body.append(image_data)
        body.append(b"\r\n")

        # Cerrar el cuerpo multipart
        body.append(b"--" + boundary + b"--\r\n")

        # Enviar la solicitud
        reply = self.network_manager.post(request, body)

    def handle_analysis_response(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            result = json.loads(str(reply.readAll(), 'utf-8'))
            patient_data = self.get_patient_data()
            self.display_result(result, patient_data)
        else:
            self.result_text.setText(f"<p style='color: red;'>Error en la solicitud: {reply.errorString()}</p>")

    def display_result(self, result, patient_data):
        full_class_name = self.cancer_types.get(result['predicted_class'], result['predicted_class'])
        result_text = self.format_result_text(result, patient_data, full_class_name)
        self.result_text.setHtml(result_text)

        max_probability = max(result['probabilities'].values())
        #self.save_to_csv(patient_data, max_probability, full_class_name)

        images_and_descriptions = [
            ('interpretation_DenseNet121.jpg', 'Modelo DenseNet21'),
            ('interpretation_EfficientNetV2B0.jpg', 'Modelo EfficientNet'),
            ('interpretation_InceptionV3.jpg', 'Modelo Inception'),
            ('interpretation_MobileNet.jpg', 'Modelo MobileNet'),
            ('interpretation_ResNet50.jpg', 'Modelo ResNet50'),
            ('interpretation_Xception.jpg', 'Modelo Xeption')
        ]
        self.update_comparison_tab(images_and_descriptions)

    def format_result_text(self, result, patient_data, full_class_name):
        result_text = f"""
        <h3>Resultados del Análisis</h3>
        <p><b>Nombre:</b> {patient_data['name']} <br>
        <b>Identificación:</b> {patient_data['identification']} <br>
        <b>Edad:</b> {patient_data['age']} <br>
        <b>Sexo:</b> {patient_data['sex']} <br>
        <b>Localización:</b> {patient_data['localization']}</p>
        <p><b>Clase predicha:</b> {full_class_name}</p>
        <h4>Probabilidades:</h4>
        <ul>
        """

        for class_name, probability in result['probabilities'].items():
            full_name = self.cancer_types.get(class_name, class_name)
            result_text += f"<li><b>{full_name}:</b> {probability:.4f}</li>"

        result_text += "</ul>"

        max_probability = max(result['probabilities'].values())
        if max_probability > 0.5:
            recommendation = "<p style='color: red;'><b>Se recomienda consultar a un dermatólogo.</b></p>"
        else:
            recommendation = "<p style='color: green;'><b>El riesgo parece bajo, pero consulte a un médico si tiene dudas.</b></p>"

        result_text += recommendation
        return result_text

    def update_comparison_tab(self, images_and_descriptions):
        # Limpiar el layout existente
        for i in reversed(range(self.comparison_grid.count())): 
            self.comparison_grid.itemAt(i).widget().setParent(None)

        for index, (image_file, description) in enumerate(images_and_descriptions):
            row = index // 2
            col = index % 2
            
            image_label = QLabel()
            pixmap = QPixmap(image_file)
            if not pixmap.isNull():
                image_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                image_label.setText("Imagen no encontrada")
            self.comparison_grid.addWidget(image_label, row * 2, col, 1, 1, Qt.AlignmentFlag.AlignCenter)
            
            description_label = QLabel(description)
            description_label.setFont(QFont("Arial", 12))
            description_label.setWordWrap(True)
            self.comparison_grid.addWidget(description_label, row * 2 + 1, col, 1, 1, Qt.AlignmentFlag.AlignCenter)

    def save_to_csv(self, patient_data, probabilities, predicted_class):
        csv_file = 'historial_pacientes.csv'
        file_exists = os.path.isfile(csv_file)

        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            fieldnames = ['Fecha', 'Nombre', 'Identificación', 'Edad', 'Sexo', 'Localización', 'Imagen', 'Clase Predicha', 'Probabilidades']
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Nombre': patient_data['Nombre'],
                'Identificación': patient_data['Identificación'],
                'Edad': patient_data['Edad'],
                'Sexo': patient_data['Sexo'],
                'Localización': patient_data['Localización'],
                'Imagen': self.current_image,
                'Clase Predicha': predicted_class,
                'Probabilidades': str(probabilities)
            })

        self.update_patient_history_table()

    def update_patient_history_table(self):
        self.history_table.setRowCount(0)

        csv_file = 'historial_pacientes.csv'
        if os.path.isfile(csv_file):
            with open(csv_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    row_position = self.history_table.rowCount()
                    self.history_table.insertRow(row_position)
                    for i, (key, value) in enumerate(row.items()):
                        self.history_table.setItem(row_position, i, QTableWidgetItem(value))

    def load_patient_history(self):
        self.update_patient_history_table()

    def update_zoom(self, value):
        if hasattr(self, 'image_viewer'):   
            self.image_viewer.update_zoom(value)

    def update_contrast(self, value):
        if hasattr(self, 'image_viewer'):
            self.image_viewer.update_contrast(value)

    def update_brightness(self, value):
        if hasattr(self, 'image_viewer'):
            self.image_viewer.update_brightness(value)

if __name__ == "__main__":
    app = QApplication([])
    window = MelanomaDetector()
    window.show()
    app.exec()