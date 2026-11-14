# SPDX-License-Identifier: AGPL-3.0-or-later
#
# MantPro - Sistema de Mantenimiento Preventivo
# Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft) <anabasasoft@gmail.com>
# https://github.com/AnabasaSoft/MantPro
#
# Este programa es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General de Affero de GNU tal y
# como la publica la Free Software Foundation, ya sea la versión 3 de la
# Licencia o (a tu elección) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil, pero SIN
# NINGUNA GARANTÍA; ni siquiera la garantía implícita de COMERCIABILIDAD o
# IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la Licencia Pública
# General de Affero de GNU para más detalles.

"""Traducciones de los textos propios de Qt (selector de ficheros y carpetas,
sus ayudas emergentes, botones estándar, menú de cortar/copiar/pegar, selector
de color y de fuente) para los idiomas en los que Qt NO trae un `qtbase_<idioma>.qm`:
euskera y gallego. Se escriben a mano. El resto de idiomas (es, en, ca, pt, fr)
usan los ficheros oficiales de Qt.

La clave es el texto original en inglés de Qt, sin contexto: ninguno de los
textos de abajo significa cosas distintas según el contexto."""

from PyQt6.QtCore import QTranslator

_EU = {
    # Selector de ficheros y carpetas
    "&Choose": "&Hautatu", "&Delete": "&Ezabatu", "&Look in:": "&Begiratu hemen:",
    "&New Folder": "&Karpeta berria", "&Open": "&Ireki", "&Rename": "&Aldatu izena",
    "&Save": "&Gorde", "All Files (*)": "Fitxategi guztiak (*)",
    "Back": "Atzera", "Forward": "Aurrera", "Go back": "Joan atzera",
    "Go forward": "Joan aurrera", "Go to the parent directory": "Joan goiko direktoriora",
    "Parent Directory": "Goiko direktorioa",
    "Change to detail view mode": "Aldatu xehetasun-ikuspegira",
    "Change to list view mode": "Aldatu zerrenda-ikuspegira",
    "Create New Folder": "Sortu karpeta berria", "Create a New Folder": "Sortu karpeta berri bat",
    "New Folder": "Karpeta berria", "Detail View": "Xehetasun-ikuspegia",
    "List View": "Zerrenda-ikuspegia", "Directories": "Direktorioak",
    "Directory:": "Direktorioa:", "File &name:": "Fitxategi-&izena:",
    "Files": "Fitxategiak", "Files of &type:": "Fitxategi-m&ota:",
    "List of places and bookmarks": "Lekuen eta laster-marken zerrenda",
    "Show ": "Erakutsi ", "Show &hidden files": "Erakutsi &ezkutuko fitxategiak",
    "Sidebar": "Alboko barra", "Recent Places": "Azken lekuak",
    "Delete": "Ezabatu", "Rename": "Aldatu izena", "Open": "Ireki", "Save As": "Gorde honela",
    "%1 already exists.\nDo you want to replace it?":
        "%1 badago jada.\nBerridatzi nahi duzu?",
    "%1\nFile not found.\nPlease verify the correct file name was given.":
        "%1\nEz da fitxategia aurkitu.\nEgiaztatu fitxategi-izen zuzena eman dela.",
    "%1\nDirectory not found.\nPlease verify the correct directory name was given.":
        "%1\nEz da direktorioa aurkitu.\nEgiaztatu direktorio-izen zuzena eman dela.",
    "Are you sure you want to delete '%1'?": "Ziur zaude '%1' ezabatu nahi duzula?",
    "Could not delete directory.": "Ezin izan da direktorioa ezabatu.",
    "Drive": "Unitatea", "Folder": "Karpeta", "Unknown": "Ezezaguna",
    "Computer": "Ordenagailua", "Date Modified": "Aldatze-data", "Name": "Izena",
    "Size": "Tamaina", "Type": "Mota",
    "No such file or directory": "Ez dago fitxategi edo direktorio horrik",
    # Botoi estandarrak
    "OK": "Onartu", "Cancel": "Utzi", "&Yes": "&Bai", "&No": "&Ez",
    "Yes to &All": "Bai &denei", "N&o to All": "Ez &denei",
    "Abort": "Abortatu", "Apply": "Aplikatu", "Close": "Itxi", "Discard": "Baztertu",
    "Help": "Laguntza", "Ignore": "Ez ikusi egin", "Reset": "Berrezarri",
    "Restore Defaults": "Berrezarri lehenespenak", "Retry": "Saiatu berriro",
    "Save": "Gorde", "Save All": "Gorde guztiak",
    "Show Details...": "Erakutsi xehetasunak...", "Hide Details...": "Ezkutatu xehetasunak...",
    # Menú contextual de edición
    "&Copy": "&Kopiatu", "&Paste": "&Itsatsi", "&Redo": "&Berregin", "&Undo": "&Desegin",
    "Cu&t": "&Ebaki", "Select All": "Hautatu dena",
    # Selector de color
    "Select Color": "Hautatu kolorea", "&Basic colors": "&Oinarrizko koloreak",
    "&Custom colors": "&Kolore pertsonalizatuak",
    "&Add to Custom Colors": "&Gehitu kolore pertsonalizatuetara",
    "&Pick Screen Color": "&Hautatu pantailako kolorea",
    "Hu&e:": "Ti&nta:", "&Sat:": "&Saz:", "&Val:": "&Balioa:", "&Red:": "&Gorria:",
    "&Green:": "&Berdea:", "Bl&ue:": "&Urdina:", "A&lpha channel:": "A&lfa kanala:",
    "&HTML:": "&HTML:",
    # Selector de fuente
    "Select Font": "Hautatu letra-tipoa", "&Font": "&Letra-tipoa", "Font st&yle": "Letra-&estiloa",
    "&Size": "&Tamaina", "Effects": "Efektuak", "Stri&keout": "Ba&rratua",
    "&Underline": "&Azpimarratua", "Sample": "Lagina", "Wr&iting System": "Idazkera-s&istema",
    "Any": "Edozein", "Italic": "Etzana", "Normal": "Normala", "Oblique": "Zeiharra",
    "Enter a value:": "Sartu balio bat:",
}

_GL = {
    # Selector de ficheiros e cartafoles
    "&Choose": "&Escoller", "&Delete": "&Eliminar", "&Look in:": "&Buscar en:",
    "&New Folder": "&Novo cartafol", "&Open": "&Abrir", "&Rename": "&Renomear",
    "&Save": "&Gardar", "All Files (*)": "Todos os ficheiros (*)",
    "Back": "Atrás", "Forward": "Adiante", "Go back": "Ir atrás",
    "Go forward": "Ir adiante", "Go to the parent directory": "Ir ao directorio superior",
    "Parent Directory": "Directorio superior",
    "Change to detail view mode": "Cambiar á vista de detalle",
    "Change to list view mode": "Cambiar á vista de lista",
    "Create New Folder": "Crear novo cartafol", "Create a New Folder": "Crear un novo cartafol",
    "New Folder": "Novo cartafol", "Detail View": "Vista de detalle",
    "List View": "Vista de lista", "Directories": "Directorios",
    "Directory:": "Directorio:", "File &name:": "&Nome do ficheiro:",
    "Files": "Ficheiros", "Files of &type:": "Ficheiros do &tipo:",
    "List of places and bookmarks": "Lista de lugares e marcadores",
    "Show ": "Amosar ", "Show &hidden files": "Amosar ficheiros &agochados",
    "Sidebar": "Barra lateral", "Recent Places": "Lugares recentes",
    "Delete": "Eliminar", "Rename": "Renomear", "Open": "Abrir", "Save As": "Gardar como",
    "%1 already exists.\nDo you want to replace it?":
        "%1 xa existe.\nQuere substituílo?",
    "%1\nFile not found.\nPlease verify the correct file name was given.":
        "%1\nNon se atopou o ficheiro.\nVerifique que o nome do ficheiro é correcto.",
    "%1\nDirectory not found.\nPlease verify the correct directory name was given.":
        "%1\nNon se atopou o directorio.\nVerifique que o nome do directorio é correcto.",
    "Are you sure you want to delete '%1'?": "Está seguro de que quere eliminar «%1»?",
    "Could not delete directory.": "Non se puido eliminar o directorio.",
    "Drive": "Unidade", "Folder": "Cartafol", "Unknown": "Descoñecido",
    "Computer": "Computador", "Date Modified": "Data de modificación", "Name": "Nome",
    "Size": "Tamaño", "Type": "Tipo",
    "No such file or directory": "Non existe tal ficheiro ou directorio",
    # Botóns estándar
    "OK": "Aceptar", "Cancel": "Cancelar", "&Yes": "&Si", "&No": "&Non",
    "Yes to &All": "Si a &todo", "N&o to All": "N&on a todo",
    "Abort": "Abortar", "Apply": "Aplicar", "Close": "Pechar", "Discard": "Descartar",
    "Help": "Axuda", "Ignore": "Ignorar", "Reset": "Restablecer",
    "Restore Defaults": "Restaurar valores predeterminados", "Retry": "Reintentar",
    "Save": "Gardar", "Save All": "Gardar todo",
    "Show Details...": "Amosar detalles...", "Hide Details...": "Agochar detalles...",
    # Menú contextual de edición
    "&Copy": "&Copiar", "&Paste": "&Pegar", "&Redo": "&Refacer", "&Undo": "&Desfacer",
    "Cu&t": "Cor&tar", "Select All": "Seleccionar todo",
    # Selector de cor
    "Select Color": "Seleccionar cor", "&Basic colors": "Cores &básicas",
    "&Custom colors": "Cores &personalizadas",
    "&Add to Custom Colors": "Eng&adir ás cores personalizadas",
    "&Pick Screen Color": "&Escoller cor da pantalla",
    "Hu&e:": "Ma&tiz:", "&Sat:": "&Sat:", "&Val:": "&Val:", "&Red:": "&Vermello:",
    "&Green:": "V&erde:", "Bl&ue:": "A&zul:", "A&lpha channel:": "Canle a&lfa:",
    "&HTML:": "&HTML:",
    # Selector de tipo de letra
    "Select Font": "Seleccionar tipo de letra", "&Font": "&Tipo de letra",
    "Font st&yle": "&Estilo de letra", "&Size": "Ta&maño", "Effects": "Efectos",
    "Stri&keout": "&Riscado", "&Underline": "&Subliñado", "Sample": "Mostra",
    "Wr&iting System": "Sistema de &escritura",
    "Any": "Calquera", "Italic": "Cursiva", "Normal": "Normal", "Oblique": "Oblicua",
    "Enter a value:": "Introduza un valor:",
}

# Complementos: textos que el qtbase oficial de estos idiomas deja sin traducir
# (el selector de ficheros pide «&Look in:» y «Files of &type:» con ampersand,
# y el .qm solo trae la versión sin él; y las etiquetas de unidad/carpeta).
_COMPLEMENTO_ES = {
    "&Look in:": "&Ver en:", "Files of &type:": "Ficheros de &tipo:",
    "Drive": "Unidad", "Folder": "Carpeta", "Unknown": "Desconocido",
}
_COMPLEMENTO_PT = {
    "&Look in:": "&Procurar em:", "Files of &type:": "Arquivos do &tipo:",
    "Drive": "Unidade",
}
_COMPLEMENTO_FR = {
    "&Look in:": "&Voir dans\u00a0:", "Files of &type:": "Fichiers de &type\u00a0:",
    "Drive": "Lecteur", "Folder": "Dossier", "Unknown": "Inconnu",
}

# Idiomas sin qtbase oficial: traducción completa a mano.
TRADUCCIONES = {"eu": _EU, "gl": _GL}
# Idiomas con qtbase oficial: solo lo que le falta.
COMPLEMENTOS = {"es": _COMPLEMENTO_ES, "pt": _COMPLEMENTO_PT, "fr": _COMPLEMENTO_FR}


# --------------------------------------------------------------------
# Lista de control (la usa herramientas/verificar_idiomas.py y las pruebas)
# --------------------------------------------------------------------

# Idiomas cuyos textos de Qt están cubiertos (oficial + este fichero). Hay que
# añadir aquí el idioma nuevo al darlo de alta, junto con su traducción.
IDIOMAS_QT_CUBIERTOS = ("es", "en", "eu", "ca", "gl", "pt", "fr", "de")

# (contexto, texto original) de los textos de Qt que la app muestra de verdad:
# selector de ficheros y carpetas, botones estándar, menú de edición, selector
# de color y de fuente. Sacados abriendo esos diálogos y registrando lo que Qt
# pide traducir. Si aparece un diálogo nuevo de Qt, añade aquí sus textos.
TEXTOS_QT_USADOS = (
    ('QAbstractFileIconProvider', 'Drive'),
    ('QAbstractFileIconProvider', 'Folder'),
    ('QAbstractFileIconProvider', 'Unknown'),
    ('QColorDialog', '&Add to Custom Colors'),
    ('QColorDialog', '&Basic colors'),
    ('QColorDialog', '&Custom colors'),
    ('QColorDialog', '&Green:'),
    ('QColorDialog', '&HTML:'),
    ('QColorDialog', '&Pick Screen Color'),
    ('QColorDialog', '&Red:'),
    ('QColorDialog', '&Sat:'),
    ('QColorDialog', '&Val:'),
    ('QColorDialog', 'A&lpha channel:'),
    ('QColorDialog', 'Bl&ue:'),
    ('QColorDialog', 'Hu&e:'),
    ('QColorDialog', 'Select Color'),
    ('QFileDialog', '&Choose'),
    ('QFileDialog', '&Delete'),
    ('QFileDialog', '&Look in:'),
    ('QFileDialog', '&New Folder'),
    ('QFileDialog', '&Open'),
    ('QFileDialog', '&Rename'),
    ('QFileDialog', '&Save'),
    ('QFileDialog', 'All Files (*)'),
    ('QFileDialog', 'Back'),
    ('QFileDialog', 'Change to detail view mode'),
    ('QFileDialog', 'Change to list view mode'),
    ('QFileDialog', 'Create New Folder'),
    ('QFileDialog', 'Create a New Folder'),
    ('QFileDialog', 'Detail View'),
    ('QFileDialog', 'Directories'),
    ('QFileDialog', 'Directory:'),
    ('QFileDialog', 'File &name:'),
    ('QFileDialog', 'Files'),
    ('QFileDialog', 'Files of &type:'),
    ('QFileDialog', 'Forward'),
    ('QFileDialog', 'Go back'),
    ('QFileDialog', 'Go forward'),
    ('QFileDialog', 'Go to the parent directory'),
    ('QFileDialog', 'List View'),
    ('QFileDialog', 'List of places and bookmarks'),
    ('QFileDialog', 'Parent Directory'),
    ('QFileDialog', 'Recent Places'),
    ('QFileDialog', 'Save As'),
    ('QFileDialog', 'Show '),
    ('QFileDialog', 'Show &hidden files'),
    ('QFileDialog', 'Sidebar'),
    ('QFileSystemModel', 'Computer'),
    ('QFileSystemModel', 'Date Modified'),
    ('QFileSystemModel', 'Name'),
    ('QFileSystemModel', 'Size'),
    ('QFileSystemModel', 'Type'),
    ('QFontDatabase', 'Any'),
    ('QFontDatabase', 'Italic'),
    ('QFontDatabase', 'Normal'),
    ('QFontDatabase', 'Oblique'),
    ('QFontDialog', '&Font'),
    ('QFontDialog', '&Size'),
    ('QFontDialog', '&Underline'),
    ('QFontDialog', 'Effects'),
    ('QFontDialog', 'Font st&yle'),
    ('QFontDialog', 'Sample'),
    ('QFontDialog', 'Select Font'),
    ('QFontDialog', 'Stri&keout'),
    ('QFontDialog', 'Wr&iting System'),
    ('QIODevice', 'No such file or directory'),
    ('QInputDialog', 'Enter a value:'),
    ('QLineEdit', '&Copy'),
    ('QLineEdit', '&Paste'),
    ('QLineEdit', '&Redo'),
    ('QLineEdit', '&Undo'),
    ('QLineEdit', 'Cu&t'),
    ('QLineEdit', 'Delete'),
    ('QLineEdit', 'Select All'),
    ('QMessageBox', 'Hide Details...'),
    ('QMessageBox', 'Show Details...'),
    ('QPlatformTheme', '&No'),
    ('QPlatformTheme', '&Yes'),
    ('QPlatformTheme', 'Abort'),
    ('QPlatformTheme', 'Apply'),
    ('QPlatformTheme', 'Cancel'),
    ('QPlatformTheme', 'Close'),
    ('QPlatformTheme', 'Discard'),
    ('QPlatformTheme', 'Help'),
    ('QPlatformTheme', 'Ignore'),
    ('QPlatformTheme', 'N&o to All'),
    ('QPlatformTheme', 'OK'),
    ('QPlatformTheme', 'Open'),
    ('QPlatformTheme', 'Reset'),
    ('QPlatformTheme', 'Restore Defaults'),
    ('QPlatformTheme', 'Retry'),
    ('QPlatformTheme', 'Save'),
    ('QPlatformTheme', 'Save All'),
    ('QPlatformTheme', 'Yes to &All'),
    ('QProgressDialog', 'Cancel'),
    ('QWidgetTextControl', '&Copy'),
    ('QWidgetTextControl', '&Paste'),
    ('QWidgetTextControl', '&Redo'),
    ('QWidgetTextControl', '&Undo'),
    ('QWidgetTextControl', 'Cu&t'),
    ('QWidgetTextControl', 'Delete'),
    ('QWidgetTextControl', 'Select All'),
)

# Textos que, en un idioma concreto, son legítimamente iguales al original
# inglés (no cuentan como «sin traducir»). "*" vale para todos los idiomas.
IGUALES_VALIDOS = {
    "*": ("OK", "&HTML:", "Normal"),
    ("es", "&No"): True, ("ca", "&No"): True,
    ("gl", "&Sat:"): True, ("gl", "&Val:"): True,
    ("pt", "&Sat:"): True, ("pt", "&Val:"): True,
    ("fr", "Type"): True, ("fr", "Oblique"): True,
    ("de", "Computer"): True, ("de", "Name"): True,
}


class TraductorQtExtra(QTranslator):
    """Traductor que responde desde un diccionario en memoria (no hay .qm)."""

    def __init__(self, codigo, parent=None):
        super().__init__(parent)
        self._textos = TRADUCCIONES.get(codigo) or COMPLEMENTOS[codigo]

    def isEmpty(self):
        return False

    def translate(self, contexto, texto, desambiguacion=None, n=-1):
        return self._textos.get(texto)  # None = QString nulo: Qt prueba el siguiente traductor
