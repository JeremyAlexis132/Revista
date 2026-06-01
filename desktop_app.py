"""
App de escritorio para procesar revistas RMDE sin usar terminal.
"""

import os
import sys
from typing import List

from PySide6.QtCore import Qt
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


class RevistaApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Procesador RMDE")
        self.resize(900, 600)

        self.bitacora_path = os.path.join(PROJECT_DIR, "bitacora.json")
        self.ids_procesados = leer_bitacora(self.bitacora_path)

        self.folders_list = QListWidget()
        self.folders_list.setSelectionMode(QListWidget.ExtendedSelection)

        self.output_label = QLabel("Salida: (no seleccionada)")
        self.output_dir = ""

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        add_btn = QPushButton("Agregar carpeta")
        remove_btn = QPushButton("Quitar seleccion")
        clear_btn = QPushButton("Limpiar lista")
        output_btn = QPushButton("Elegir salida")
        process_btn = QPushButton("Procesar")

        add_btn.clicked.connect(self.add_folder)
        remove_btn.clicked.connect(self.remove_selected)
        clear_btn.clicked.connect(self.clear_folders)
        output_btn.clicked.connect(self.choose_output_dir)
        process_btn.clicked.connect(self.process_all)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Carpetas seleccionadas:"))
        left_layout.addWidget(self.folders_list)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(add_btn)
        controls_layout.addWidget(remove_btn)
        controls_layout.addWidget(clear_btn)

        left_layout.addLayout(controls_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.output_label)
        right_layout.addWidget(output_btn)
        right_layout.addSpacing(10)
        right_layout.addWidget(QLabel("Bitacora cargada:"))
        right_layout.addWidget(QLabel(", ".join(self.ids_procesados) or "(vacia)"))
        right_layout.addSpacing(10)
        right_layout.addWidget(QLabel("Log:"))
        right_layout.addWidget(self.log_view)
        right_layout.addWidget(process_btn)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 3)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def log(self, message: str) -> None:
        self.log_view.append(message)

    def add_folder(self) -> None:
        folders = self.get_existing_directories("Selecciona una o varias carpetas")
        if not folders:
            return
        for folder in folders:
            self.add_folder_path(folder)

    def get_existing_directories(self, titulo: str) -> List[str]:
        dialog = QFileDialog(self, titulo)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        view = dialog.findChild(QAbstractItemView)
        if view is not None:
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        if dialog.exec() != QFileDialog.Accepted:
            return []
        return dialog.selectedFiles()

    def add_folder_path(self, folder: str) -> None:
        for i in range(self.folders_list.count()):
            if self.folders_list.item(i).data(Qt.UserRole) == folder:
                return
        item = QListWidgetItem(os.path.basename(folder))
        item.setData(Qt.UserRole, folder)
        self.folders_list.addItem(item)

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
        self.output_label.setText(f"Salida: {folder}")

    def validate_folder(self, folder_name: str, folder_path: str) -> List[str]:
        errores = []
        revista_id = extraer_id_de_carpeta(folder_name)
        if revista_id is None:
            errores.append("No se pudo extraer ID del nombre de la carpeta.")
        html_path = encontrar_html_en_carpeta(folder_path)
        if html_path is None:
            errores.append("No se encontro archivo HTML en la carpeta.")
        return errores

    def process_all(self) -> None:
        if self.folders_list.count() == 0:
            QMessageBox.warning(self, "Aviso", "No hay carpetas seleccionadas.")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "Aviso", "Selecciona una carpeta de salida.")
            return

        procesadas = 0
        omitidas = 0
        errores = 0

        for i in range(self.folders_list.count()):
            item = self.folders_list.item(i)
            folder_path = item.data(Qt.UserRole)
            folder_name = os.path.basename(folder_path)

            self.log(f"Procesando: {folder_name}")
            self.log("-" * 40)

            errores_validacion = self.validate_folder(folder_name, folder_path)
            if errores_validacion:
                errores += 1
                for err in errores_validacion:
                    self.log(f"Error: {err}")
                QMessageBox.warning(
                    self,
                    "Formato invalido",
                    f"La carpeta '{folder_name}' no cumple el formato esperado.\n"
                    f"{os.linesep.join(errores_validacion)}",
                )
                continue

            clave_bitacora = construir_clave_bitacora(folder_name)
            revista_id = extraer_id_de_carpeta(folder_name)
            if clave_bitacora is None or revista_id is None:
                errores += 1
                self.log("Error: no se pudo construir clave de bitacora.")
                continue

            procesada_en_bitacora_nueva = clave_bitacora in self.ids_procesados
            procesada_en_bitacora_legacy = (
                revista_id in self.ids_procesados and clave_bitacora.endswith(":art")
            )
            if procesada_en_bitacora_nueva or procesada_en_bitacora_legacy:
                omitidas += 1
                self.log("Omitida: ya procesada segun bitacora.")
                continue

            exito = self.process_folder(folder_name, folder_path)
            if exito:
                registrar_en_bitacora(self.bitacora_path, clave_bitacora)
                self.ids_procesados.append(clave_bitacora)
                procesadas += 1
                self.log("OK: procesada.")
            else:
                errores += 1
                self.log("Error: fallo el procesamiento.")

        self.log("=" * 40)
        self.log(f"Resumen -> Procesadas: {procesadas} | Omitidas: {omitidas} | Errores: {errores}")

    def process_folder(self, folder_name: str, folder_path: str) -> bool:
        html_path = encontrar_html_en_carpeta(folder_path)
        if html_path is None:
            self.log("Error: no se encontro HTML.")
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
    window = RevistaApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
