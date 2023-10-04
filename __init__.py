# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KL8slice
                                 A QGIS plugin
  Este nombre combina el algoritmo k-means que se utiliza para el agrupamiento (K) con "Landsat 8", que es el tipo específico de imágenes satelitales utilizadas, y "Slicer", que hace referencia al proceso de segmentación o corte de la imagen en diferentes clusters o grupos de uso del suelo.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-08-27
        copyright            : (C) 2023 by Keyla Alencar da Silva, Francisca Ruiz-Tagle, Erik Zimmemann y Maria Carolina Parodi. CONICET, UTEM y UNR
        email                : lab.suelos@utem.cl
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load KL8slice class from file KL8slice.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .k_l8slice import KL8slice
    return KL8slice(iface)
