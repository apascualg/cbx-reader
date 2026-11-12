# CBX Reader 📖✂️

Un lector de cómics y manga moderno, ultraligero y estilizado para Windows (**CBZ**, **CBR**, **ZIP** y **carpetas de imágenes**) diseñado para capturar y copiar viñetas al portapapeles con máxima precisión y resolución nativa.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)
![UI](https://img.shields.io/badge/Theme-Amber%20%26%20Warm%20Dark-F5B900?style=flat)

---

## ✨ Características Principales

- **✂️ Herramienta de Recorte (Crop) Instantánea:**
  - Haz **clic izquierdo directo y arrastra** sobre cualquier viñeta para seleccionarla. El resto de la página se atenúa suavemente de fondo.
  - Pulsa **`Ctrl + C`** para copiar el recorte al portapapeles a su **resolución nativa original** (sin pérdidas de calidad ni distorsión por zoom). La selección se restablece automáticamente.
  - Pulsa **`Ctrl + Z`** o **`Escape`** para cancelar el recorte.

- **⚓ Pan Anclado con Botón Central:**
  - Mantén pulsado el **botón central del ratón (rueda)** para desplazarte por la página libremente.
  - El marco del recorte y la zona iluminada permanecen **100% fijos y anclados a la ilustración** durante el movimiento.

- **📦 Formatos y Fuentes Compatibles:**
  - Archivos comprimidos: `.cbz`, `.zip`, `.cbr`, `.rar`.
  - **Carpetas con imágenes:** Carga directorios enteros con imágenes (`.jpg`, `.png`, `.webp`, `.bmp`, etc.) ordenadas de forma numérica natural.
  - **Imágenes individuales:** Si abres una imagen suelta, detecta su carpeta y carga todas las páginas hermanas automáticamente.

- **🎨 Diseño y Estética:**
  - Paleta personalizada en tonos cálidos oscuros (`#191301`) y ámbar dorado (`#F5B900`).
  - Botones y cajas redondeadas con suavizado anti-aliased y efectos *hover*.
  - Tipografía **Inter** integrada y cargada dinámicamente.

---

## 🚀 Cómo Usarlo

### Opción A: Ejecutable Portátil (`CBX-Reader.exe`)
No requiere tener Python instalado:
1. Descarga o ejecuta **`CBX-Reader.exe`**.
2. Puedes llevarlo en un pendrive o colocarlo en cualquier carpeta.

### Opción B: Instalador de Windows (`Instalar-CBX-Reader.bat`)
Si deseas instalarlo como un programa integrado en tu sistema:
1. Haz doble clic en **`Instalar-CBX-Reader.bat`**.
2. Creará un acceso directo en tu **Escritorio** y en el **Menú Inicio** (podrás buscar `CBX Reader` en Windows).
3. Podrás desinstalarlo limpiamente en cualquier momento desde *Configuración > Aplicaciones instaladas*.

### Opción C: Ejecutar desde el Código Fuente
1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/cbx-reader.git
   cd cbx-reader
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```bash
   python reader.py
   ```

---

## ⌨️ Controles y Atajos de Teclado

| Acción | Método |
|---|---|
| **Abrir archivo** | `Ctrl + O` o botón **📂 Archivo** |
| **Abrir carpeta con imágenes** | `Ctrl + D` / `Ctrl + Shift + O` o botón **📁 Carpeta** |
| **Recortar viñeta (Crop)** | **Clic izquierdo directo + arrastrar** |
| **Copiar recorte al portapapeles** | **`Ctrl + C`** (restablece la selección al instante) |
| **Cancelar / Deshacer recorte** | **`Ctrl + Z`** o **`Escape`** |
| **Mover la página (Pan)** | **Botón central del ratón (rueda) + arrastrar** |
| **Página siguiente** | `→` / `D` / Clic derecho |
| **Página anterior** | `←` / `A` |
| **Zoom in / out** | `+` / `-` o rueda del ratón |
| **Ajustar a ventana** | `F` / `0` o botón **⊡ Ajustar** |

---

## 🔨 Cómo Compilar el Ejecutable tú mismo

Si realizas modificaciones al código y quieres volver a generar el ejecutable `.exe`:
- Simplemente haz doble clic en **`build.bat`**.
- O ejecuta el comando:
  ```bash
  pyinstaller --noconsole --onefile --icon="icon.ico" --add-data="icon.ico;." --add-data="Inter.ttf;." --name="CBX-Reader" reader.py
  ```

---

## 📄 Requisitos para archivos CBR / RAR

Para leer archivos `.cbr` o `.rar`, se requiere tener **WinRAR** instalado en el equipo (el programa detecta automáticamente `UnRAR.exe`). Los archivos `.cbz` y `.zip` funcionan de forma nativa sin ningún software adicional.

---

## 📜 Licencia

Distribuido bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.
