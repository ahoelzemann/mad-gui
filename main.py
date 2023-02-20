from mad_gui import start_gui
from mad_gui.plot_tools.labels import BaseRegionLabel

from custom_importer import CustomImporter
from custom_importer import CustomExporter
from mad_gui.config import BaseTheme
from PySide2.QtGui import QColor
from mad_gui.plugins.base import BaseImporter


class MyTheme(BaseTheme):
    # COLOR_DARK = QColor(0, 255, 100)
    # COLOR_LIGHT = QColor(255, 255, 255)
    FAU_PHILFAK_COLORS = {
        "dark": QColor(255, 0, 0),
        "medium": QColor(0, 255, 0),
        "light": QColor(0, 0, 255),
    }


class Self_Recall_Labels(BaseRegionLabel):
    # This label will always be shown at the upper 20% of the plot view
    min_height = 0.6
    max_height = 1
    name = "Activity"
    color = [255, 0, 127, 70]
    descriptions = {
        'walking': None,
        'running': None,
        'cycling': None,
        'car_driving': None,
        'cooking': None,
        'playing_an_instrument': None,
        'horse_riding': None,
        'other': None}


start_gui(plugins=[CustomImporter, CustomExporter], theme=MyTheme, labels=[Self_Recall_Labels])
