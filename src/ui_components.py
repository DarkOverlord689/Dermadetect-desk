from PyQt6.QtWidgets import (QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QSlider, QTabWidget, QTextEdit, QTableWidget, QWidget,
                             QLineEdit, QFormLayout, QScrollArea)
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt6.QtCore import Qt
from image_viewer import ImageViewer
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression

def create_main_layout(parent):
    main_widget = QTabWidget()
    main_widget.setFont(QFont("Arial", 12))

 

    # Pestaña de Resultados
    results_tab = QWidget()
    results_layout = QHBoxLayout(results_tab)

    # Lado izquierdo (formulario, botones, controles)
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setSpacing(15)

    # Logo y título
    title_label = QLabel('DermaDetect')
    title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
    left_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

    logo_label = QLabel()
    logo_pixmap = QPixmap('ConSlogan/Color.png')
    if not logo_pixmap.isNull():
        logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
    else:
        logo_label.setText("Logo not found")
    left_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

    # Formulario
    form_widget = create_form_widget(parent)
    left_layout.addWidget(form_widget)
    """
    # Preprocesamiento
    preprocess_layout = QHBoxLayout()
    preprocess_label = QLabel("Preprocesamiento:")
    preprocess_label.setFont(QFont("Arial", 12))
    preprocess_layout.addWidget(preprocess_label)
    parent.preprocess_options = QComboBox()
    parent.preprocess_options.addItems(["Reducción de ruido", "Ambos"])
    parent.preprocess_options.setFont(QFont("Arial", 12))
    preprocess_layout.addWidget(parent.preprocess_options)
    left_layout.addLayout(preprocess_layout)
    """
    # Sliders
    for slider_name, label_text in [("zoom_slider", "Zoom:"), ("contrast_slider", "Contraste:"), ("brightness_slider", "Brillo:")]:
        left_layout.addWidget(QLabel(label_text))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(50, 150)
        slider.setValue(100)
        setattr(parent, slider_name, slider)
        left_layout.addWidget(slider)
    # Conectar los sliders con las funciones correspondientes en el parent
    parent.zoom_slider.valueChanged.connect(parent.update_zoom)
    parent.contrast_slider.valueChanged.connect(parent.update_contrast)
    parent.brightness_slider.valueChanged.connect(parent.update_brightness)
    # Botones
    button_style = """
    QPushButton {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        font-size: 16px;
        margin: 4px 2px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:pressed {
        background-color: #3e8e41;
    }
    QPushButton:disabled {
        background-color: #cccccc;
        color: #666666;
    }
    """
    for button_name, button_text, connect_function in [
        ("attach_button", "Cargar Imagen", parent.load_image),
        ("analyze_button", "Analizar Imagen", parent.analyze_image),
        #("history_button", "Ver Historial de Pacientes", parent.load_patient_history)
    ]:
        button = QPushButton(button_text)
        button.setStyleSheet(button_style)
        button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        button.clicked.connect(connect_function)
        setattr(parent, button_name, button)
        left_layout.addWidget(button)

  

    # Lado derecho (visor de imagen y resultados)
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)

    parent.image_viewer = ImageViewer()
    parent.image_viewer.setFixedSize(550, 450)
    right_layout.addWidget(parent.image_viewer)

    parent.result_text = QTextEdit()
    parent.result_text.setReadOnly(True)
    parent.result_text.setFont(QFont("Arial", 12))
    parent.result_text.setStyleSheet("QTextEdit { color: black; background-color: white; }")
    right_layout.addWidget(QLabel("Resultado:"))
    right_layout.addWidget(parent.result_text)

    # Añadir widgets izquierdo y derecho al layout de resultados
    results_layout.addWidget(left_widget, 1)
    results_layout.addWidget(right_widget, 1)

    
    # Añadir la pestaña de Resultados al QTabWidget
    main_widget.addTab(results_tab, "                                                                                                                                                                           ")
   

    return main_widget


def create_form_widget(parent):
    form_widget = QWidget()
    form_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc; border-radius: 5px; padding: 10px;")
    form_layout = QFormLayout(form_widget)
    form_layout.setSpacing(10)
    
    label_font = QFont("Arial", 12)
    
    fields = [
        ("Nombre:", "name_input"),
        ("Identificación:", "id_input"),
        ("Edad:", "age_input"),
        ("Sexo:", "sex_input", ["Masculino", "Femenino"]),
        ("Localización:", "location_input", ["Miembro inferior", "Cabeza/cuello", "Tórax anterior", "Miembro superior", "Espalda", "Palmas/plantas", "lateral torso", "Oral/genital"]),
        ("Observaciones:", "observation_input")
    ]

    for label_text, attr_name, *options in fields:
        label = QLabel(label_text)
        label.setFont(label_font)
        
        if options:
            widget = QComboBox()
            widget.addItems(options[0])
            widget.setFont(label_font)
        elif label_text == "Observaciones:":  # Para el campo de observaciones
            widget = QTextEdit()
            widget.setFont(label_font)
            widget.setPlaceholderText("Escriba sus observaciones aquí...")  # Texto de marcador
        else:
            widget = QLineEdit()
            widget.setFont(label_font)
            
            if label_text == "Edad:":
                # Validator para edad (0-99)
                validator = QIntValidator(0, 99)
                widget.setValidator(validator)
                widget.setPlaceholderText("Ingrese edad de 0 a99 ")  # Texto de ayuda
            elif label_text == "Identificación:":
                # Validator para identificación (números entre 7 y 8 dígitos)
                validator = QRegularExpressionValidator(QRegularExpression("^[0-9]{7,8}$"))
                widget.setValidator(validator)
                widget.setPlaceholderText("Ingrese 7-8 dígitos")  # Texto de ayuda
            elif label_text == "Nombre:":
                # Validator para nombre (solo letras)
                regex = QRegularExpression("^[A-Za-záéíóúñÁÉÍÓÚÑ ]+$")  # Permite letras y espacios
                validator = QRegularExpressionValidator(regex)
                widget.setValidator(validator)
        
        setattr(parent, attr_name, widget)
        form_layout.addRow(label, widget)

    input_style = """
    QLineEdit, QTextEdit, QComboBox {
        color: black;
        background-color: white;
        selection-color: white;
        selection-background-color: #0078d7;
    }
    """
    form_widget.setStyleSheet(input_style)

    return form_widget
