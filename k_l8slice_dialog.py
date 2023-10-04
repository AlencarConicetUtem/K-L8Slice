# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KL8sliceDialog
                                 A QGIS plugin
  Este nombre combina el algoritmo k-means que se utiliza para el agrupamiento (K) con "Landsat 8", que es el tipo específico de imágenes satelitales utilizadas, y "Slicer", que hace referencia al proceso de segmentación o corte de la imagen en diferentes clusters o grupos de uso del suelo.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-08-27
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Keyla Alencar da Silva, Francisca Ruiz-Tagle, Erik Zimmemann y Maria Carolina Parodi. CONICET, UTEM y UNR
        email                : lab.suelos@utem.cl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'k_l8slice_dialog_base.ui'))


class KL8sliceDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(KL8sliceDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)