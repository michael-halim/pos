from PyQt6 import QtGui

class POSFonts:
    @staticmethod
    def get_font(size: int = 16):
        font = QtGui.QFont()
        font.setPointSize(size)
        return font