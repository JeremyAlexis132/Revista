"""
App de escritorio para procesar revistas RMDE sin usar terminal.
"""

import os
import sys
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QDropEvent, QDragEnterEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QAbstractItemView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from Modules.css_processor import procesar_css
from Modules.sections import obtener_procesador_por_seccion
from Modules.utils import (
    construir_clave_bitacora,
    crear_estructura_salida,
    copiar_imagenes,
    encontrar_css_en_carpeta,
    encontrar_html_en_carpeta,
    extraer_codigo_seccion,
    extraer_id_de_carpeta,
    leer_bitacora,
    registrar_en_bitacora,
)

# --- ESTILO VISUAL MODERNO (QSS) ---
MODERN_STYLE = """
QMainWindow {
    background-color: #F8F9FA;
}
QPushButton {
    background-color: #0D6EFD;
    color: white;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
    border: none;
}
QPushButton:hover {
    background-color: #0B5ED7;
}
QPushButton:pressed {
    background-color: #0a53be;
}
QPushButton#ProcessBtn {
    background-color: #198754;
    font-size: 15px;
    padding: 12px;
}
QPushButton#ProcessBtn:hover {
    background-color: #157347;
}
QListWidget, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
    color: #212529;
}
QLabel {
    font-size: 14px;
    color: #212529;
    font-weight: bold;
}
QLabel#InfoLabel {
    font-size: 12px;
    color: #6C757D;
    font-weight: normal;
}
"""

# --- LISTA PERSONALIZADA PARA ARRASTRAR Y SOLTAR ---
class DropListWidget(QListWidget):
    def __init__(self, add_callback, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.add_callback = add_callback

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            folder_path = url.toLocalFile()
            if os.path.isdir(folder_path):
                self.add_callback(folder_path)


class RevistaApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Formato Revistas - Procesador RMDE")
        self.resize(950, 650)
        
        # Configurar Ícono de la ventana (Asegúrate de tener un icono.png en tu carpeta)
        icono_path = os.path.join(PROJECT_DIR, "icono.png")
        if os.path.exists(icono_path):
            self.setWindowIcon(QIcon(icono_path))

        self.bitacora_path = os.path.join(PROJECT_DIR, "bitacora.json")
        self.ids_procesados = leer_bitacora(self.bitacora_path)

        # Usar la nueva lista que soporta arrastrar y soltar
        self.folders_list = DropListWidget(self.add_folder_path)

        self.output_label = QLabel("Salida: (Ninguna carpeta seleccionada)")
        self.output_label.setWordWrap(True)
        self.output_dir = ""

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        # Botones
        add_btn = QPushButton("Buscar Carpeta...")
        remove_btn = QPushButton("Quitar Selección")
        clear_btn = QPushButton("Limpiar Todo")
        output_btn = QPushButton("Elegir Carpeta de Salida")
        process_btn = QPushButton("Procesar Archivos")
        process_btn.setObjectName("ProcessBtn") # ID para darle estilo verde especial

        # Conexiones
        add_btn.clicked.connect(self.add_folder)
        remove_btn.clicked.connect(self.remove_selected)
        clear_btn.clicked.connect(self.clear_folders)
        output_btn.clicked.connect(self.choose_output_dir)
        process_btn.clicked.connect(self.process_all)

        # Layout Izquierdo (Entrada)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Carpetas a procesar:"))
        
        info_drag = QLabel("💡 Tip: Puedes seleccionar varias carpetas en tu explorador y arrastrarlas directamente aquí.")
        info_drag.setObjectName("InfoLabel")
        left_layout.addWidget(info_drag)
        
        left_layout.addWidget(self.folders_list)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(add_btn)
        controls_layout.addWidget(remove_btn)
        controls_layout.addWidget(clear_btn)
        left_layout.addLayout(controls_layout)

        # Layout Derecho (Salida y Log)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Destino:"))
        right_layout.addWidget(self.output_label)
        right_layout.addWidget(output_btn)
        
        right_layout.addSpacing(15)
        right_layout.addWidget(QLabel("Registro de Actividad (Log):"))
        right_layout.addWidget(self.log_view)
        right_layout.addSpacing(10)
        right_layout.addWidget(process_btn)

        # Layout Principal
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 4) # Proporción 4
        main_layout.addSpacing(10)
        main_layout.addLayout(right_layout, 5) # Proporción 5

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def log(self, message: str) -> None:
        self.log_view.append(message)
        # Auto-scroll hacia abajo
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_folder(self) -> None:
        # Esto sirve como alternativa manual si el usuario no quiere arrastrar y soltar
        folder = QFileDialog.getExistingDirectory(self, "Selecciona una carpeta")
        if folder:
            self.add_folder_path(folder)

    def add_folder_path(self, folder: str) -> None:
        # Evitar duplicados en la lista
        for i in range(self.folders_list.count()):
            if self.folders_list.item(i).data(Qt.UserRole) == folder:
                return
        
        item = QListWidgetItem(os.path.basename(folder))
        item.setData(Qt.UserRole, folder)
        self.folders_list.addItem(item)
        self.log(f"Agregado a la cola: {os.path.basename(folder)}")

    def remove_selected(self) -> None:
        for item in self.folders_list.selectedItems():
            row = self.folders_list.row(item)
            self.folders_list.takeItem(row)

    def clear_folders(self) -> None:
        self.folders_list.clear()

    def choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Selecciona carpeta de salida")
        if not folder:
            return
        self.output_dir = folder
        self.output_label.setText(f"Salida:\n{folder}")

    def validate_folder(self, folder_name: str, folder_path: str) -> List[str]:
        errores = []
        revista_id = extraer_id_de_carpeta(folder_name)
        if revista_id is None:
            errores.append("No se pudo extraer ID del nombre de la carpeta.")
        html_path = encontrar_html_en_carpeta(folder_path)
        if html_path is None:
            errores.append("No se encontró archivo HTML en la carpeta.")
        return errores

    def process_all(self) -> None:
        if self.folders_list.count() == 0:
            QMessageBox.warning(self, "Aviso", "No hay carpetas en la lista para procesar.")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "Aviso", "Por favor selecciona una carpeta de destino.")
            return

        procesadas = 0
        omitidas = 0
        errores = 0

        self.log("\n🚀 --- INICIANDO PROCESAMIENTO MASIVO ---")

        for i in range(self.folders_list.count()):
            item = self.folders_list.item(i)
            folder_path = item.data(Qt.UserRole)
            folder_name = os.path.basename(folder_path)

            self.log(f"\n📂 Analizando: {folder_name}")

            errores_validacion = self.validate_folder(folder_name, folder_path)
            if errores_validacion:
                errores += 1
                for err in errores_validacion:
                    self.log(f"❌ Error: {err}")
                continue

            clave_bitacora = construir_clave_bitacora(folder_name)
            revista_id = extraer_id_de_carpeta(folder_name)
            if clave_bitacora is None or revista_id is None:
                errores += 1
                self.log("❌ Error: No se pudo construir clave de bitácora.")
                continue

            procesada_en_bitacora_nueva = clave_bitacora in self.ids_procesados
            procesada_en_bitacora_legacy = (
                revista_id in self.ids_procesados and clave_bitacora.endswith(":art")
            )
            if procesada_en_bitacora_nueva or procesada_en_bitacora_legacy:
                omitidas += 1
                self.log("⚠️ Omitida: Ya fue procesada anteriormente según la bitácora.")
                continue

            exito = self.process_folder(folder_name, folder_path)
            if exito:
                registrar_en_bitacora(self.bitacora_path, clave_bitacora)
                self.ids_procesados.append(clave_bitacora)
                procesadas += 1
                self.log("✅ Éxito: Carpeta procesada correctamente.")
            else:
                errores += 1
                self.log("❌ Error: Falló el procesamiento del HTML/CSS.")

        self.log("\n📊 --- RESUMEN FINAL ---")
        self.log(f"Procesadas con éxito: {procesadas}")
        self.log(f"Omitidas (Ya existían): {omitidas}")
        self.log(f"Errores encontrados: {errores}")
        
        QMessageBox.information(self, "Proceso Terminado", f"Se procesaron {procesadas} carpetas.\nHubo {errores} errores.")

    def process_folder(self, folder_name: str, folder_path: str) -> bool:
        html_path = encontrar_html_en_carpeta(folder_path)
        if html_path is None:
            return False

        css_paths = encontrar_css_en_carpeta(folder_path)
        rutas = crear_estructura_salida(self.output_dir, folder_name)

        archivos_css = procesar_css(css_paths, rutas["css"], folder_name)
        copiar_imagenes(folder_path, rutas["images"])

        codigo_seccion = extraer_codigo_seccion(folder_name)
        procesador_html = obtener_procesador_por_seccion(codigo_seccion)

        return procesador_html(
            html_path=html_path,
            archivos_css=archivos_css,
            ruta_salida_html=rutas["html"],
            nombre_revista=folder_name,
        )


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE) # Aplicar el estilo a toda la app
    window = RevistaApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()