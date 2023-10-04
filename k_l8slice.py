# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KL8slice
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
import re
import processing
import numpy as np
from math import *
from osgeo import gdal 
from shutil import rmtree
from qgis.core import  Qgis
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtMultimedia import QSound
from qgis.PyQt.QtWidgets import QAction
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from PyQt5.QtWidgets import QAction,QFileDialog, QDialog, QLabel, QMessageBox, QSizePolicy, QVBoxLayout

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .k_l8slice_dialog import KL8sliceDialog
import os.path

class Instrucciones(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Instrucciones")
        self.setMinimumSize(300, 200)

        layout = QVBoxLayout(self)

        self.etiqueta = QLabel("Contenido de las instrucciones", self)
        self.etiqueta.setAlignment(Qt.AlignLeft)
        self.etiqueta.setStyleSheet("border: 1px solid black; padding: 25px; font: 75 9pt 'Calibri'; border-radius: 10px 10px 10px 10px;")
        self.etiqueta.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.etiqueta)

class KL8slice:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.dialogo = Instrucciones()
        self.archivo_MTL = []
        self.rutas_bandas = []
        self.rutas_bandas_corr = []
        self.estado_corr = "inactivo"
        
        self.ruta_guardar = []
        self.sound = QSound(os.path.dirname(__file__)+"/exito.wav")

        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'KL8slice_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&K-L8Slice')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('KL8slice', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/k_l8slice/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Calculate K-L8Slice'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&K-L8Slice'),
                action)
            self.iface.removeToolBarIcon(action)

    def inst(self):
        self.dialogo.etiqueta.setText("\tINSTRUCCIONES\n\n1. Asegurarse que las imágenes satelitales que usará sean exclusivamente de Landsat 8.\n2. Determinar si el proceso requiere corrección atmosférica:\n\nEn caso de requerir:\n\t- Dejar desmarcado la opción “Corrección realizada”.\n\t- Pulsar el icono de la opción “Seleccionar imágenes Landsat 8” y seleccionar todas las bandas satelitales de Landsat 8 (debe cerciorarse que estén las bandas 1, 2, 3, 4, 5, 6 y 7).\n\t- Pulsar el icono de la opción “Seleccionar archivo MTL” y escoger el archivo MTL (formato *.txt).\n\nEn caso de no requerir:\n\t- Marcar la opción “Corrección realizada”.\n\t- Pulsar el icono de la opción “Seleccionar imágenes corregidas Landsat 8” y seleccionar todas las bandas satelitales de Landsat 8 (debe cerciorarse que estén las bandas 1, 2, 3, 4, 5, 6 y 7).\n\n3. En la opción “Seleccione método…” seleccionar el método deseado.\n4. Pulsar el icono de la opción “Guardar resultados”, escoger el directorio donde desea guardar y escribir el nombre de la carpeta que contendrá los resultados.\n5. Pulsar el botón “Ejecutar” (es normal que el proceso demore un par de segundos).")
        self.dialogo.exec_()

    def abrirTIF(self,rutas_bandas):
        
        archivo, _ = QFileDialog.getOpenFileNames(self.dlg, 'Abrir archivo', '', 'TIF file .TIF (*.TIF)')
        
        if archivo:
            mensaje = self.dlg.cuadroTIF.setText(archivo[0])
            self.dlg.btn_abrirTIF.setText(mensaje)
        for i in archivo:
            self.rutas_bandas.append(i)

        if len(self.rutas_bandas) > 0:

            #filtro de bandas para mostrar anuncio 
            bandas_necesarias = ["B1", "B2", "B3","B4", "B5", "B6","B7"]
            bandas_faltantes = []

            for banda in bandas_necesarias:
                if not any(banda in ruta for ruta in self.rutas_bandas):
                    bandas_faltantes.append(banda)

            if bandas_faltantes:
                mensaje = f"Las siguientes bandas no están presentes: {', '.join(bandas_faltantes)}"
                QMessageBox.warning(self.dlg, "Aviso", mensaje)
        
            
        return rutas_bandas
    
    def abrirMTL(self,archivo_MTL):
        archivo, _ = QFileDialog.getOpenFileNames(self.dlg, 'Abrir archivo','', 'MTL file .txt (*.txt)')
        if archivo:
            mensaje = self.dlg.cuadroMTL.setText(archivo[0])
            self.dlg.btn_abrirMTL.setText(mensaje)
            self.archivo_MTL.append(archivo[0])

        #Abrir el archivo en modo lectura
            with open(self.archivo_MTL[0], "r") as file:
            # Leer el contenido del archivo y almacenarlo en una variable
                content = file.read()

               # Verificar si la palabra "LC08" está presente en el contenido del archivo
                if "LC08" in content:

                    # Generar la función
                    pass
                else:
                    mensaje = "El MTL ingresado NO corresponde al satélite Landsat 8"
                    QMessageBox.warning(self.dlg, "Aviso", mensaje)
                    self.archivo_MTL.clear()

        return archivo_MTL
    
    def estado(self):
        if self.dlg.btn_correccion.isChecked()==False:
            self.estado_corr = "inactivo"
            self.dlg.cuadroTIF.setEnabled(True)
            self.dlg.btn_abrirTIF.setEnabled(True)
            self.dlg.cuadroMTL.setEnabled(True)
            self.dlg.btn_abrirMTL.setEnabled(True)
            self.dlg.cuadroBandasCorregidas.setEnabled(False)
            self.dlg.btn_abrirCORR.setEnabled(False)
            self.dlg.msj_TIF.setEnabled(True)
            self.dlg.msj_MTL.setEnabled(True)
            self.dlg.msj_CORR.setEnabled(False)
            
        else:
            self.estado_corr = "activo"
            self.dlg.cuadroTIF.setEnabled(False)
            self.dlg.btn_abrirTIF.setEnabled(False)
            self.dlg.cuadroMTL.setEnabled(False)
            self.dlg.btn_abrirMTL.setEnabled(False)
            self.dlg.cuadroBandasCorregidas.setEnabled(True)
            self.dlg.btn_abrirCORR.setEnabled(True)
            self.dlg.msj_TIF.setEnabled(False)
            self.dlg.msj_MTL.setEnabled(False)
            self.dlg.msj_CORR.setEnabled(True)


    def abrirCORR(self,rutas_bandas_corr): 
        archivo, _ = QFileDialog.getOpenFileNames(self.dlg, 'Abrir archivo', '', 'TIF file .TIF (*.TIF)')
        if archivo:
            mensaje = self.dlg.cuadroBandasCorregidas.setText(archivo[0])
            self.dlg.btn_abrirCORR.setText(mensaje)
        for i in archivo:
            self.rutas_bandas_corr.append(i)

        if len(self.rutas_bandas_corr) > 0 and self.estado_corr == 'activo':

            #filtro de bandas para mostrar anuncio 
            bandas_necesarias = ["B1", "B2", "B3","B4", "B5", "B6","B7"]
            bandas_faltantes = []

            for banda in bandas_necesarias:
                if not any(banda in ruta for ruta in self.rutas_bandas_corr):
                    bandas_faltantes.append(banda)

            if bandas_faltantes:
                mensaje = f"Las siguientes bandas no están presentes: {', '.join(bandas_faltantes)}"
                QMessageBox.warning(self.dlg, "Aviso", mensaje)

        return rutas_bandas_corr
    

    def guardar(self, ruta_guardar):

        archivo = QFileDialog.getSaveFileName(self.dlg,'Guardar archivo')
        if archivo:
            mensaje = self.dlg.cuadroGuardar.setText(archivo[0])
            self.dlg.btn_guardar.setText(mensaje)
        self.ruta_guardar.append(archivo[0])
        
        return ruta_guardar
    
    def sonido_termino(self):
        self.sound.play()

    def estado_ejecutar(self):
        if len(self.rutas_bandas) > 0 and self.estado_corr == 'inactivo':

            if len(self.archivo_MTL) > 0 and self.archivo_MTL[0]:
                #Abrir el archivo en modo lectura
                with open(self.archivo_MTL[0], "r") as file:
                # Leer el contenido del archivo y almacenarlo en una variable
                    content = file.read()
                    # Verificar si la palabra "LC08" está presente en el contenido del archivo
                    if "LC08" in content:
        
                        if len(self.ruta_guardar) > 0 and self.ruta_guardar[0]:
                            self.dlg.btn_ejecutar.setEnabled(True)
                            self.dlg.aviso_ejecutar.setVisible(False)
                            self.message_bar = self.iface.messageBar()
                            self.message_bar.pushMessage("ADVERTENCIA:", "El proceso de cálculo y generación de archivos puede demorar varios segundos, por favor esperar sonido y/o mensaje de éxito (IMPORTANTE: NO INTERRUMPA LA EJECUCIÓN)", level=Qgis.Warning, duration=-1)

            elif len(self.archivo_MTL) == 0:
                #filtro de bandas para mostrar anuncio 
                bandas_necesarias = ["B1", "B2", "B3","B4", "B5", "B6","B7"]
                bandas_faltantes = []

                for banda in bandas_necesarias:
                    if not any(banda in ruta for ruta in self.rutas_bandas):
                        bandas_faltantes.append(banda)
                        
        if len(self.rutas_bandas_corr) > 0 and self.estado_corr == 'activo':
            
            if len(self.ruta_guardar) > 0 and self.ruta_guardar[0]: 
                self.dlg.btn_ejecutar.setEnabled(True)
                self.dlg.aviso_ejecutar.setVisible(False)  
                self.message_bar = self.iface.messageBar()
                self.message_bar.pushMessage("ADVERTENCIA:", "El proceso de cálculo y generación de archivos puede demorar varios segundos, por favor esperar sonido y/o mensaje de éxito (IMPORTANTE: NO INTERRUMPA LA EJECUCIÓN)", level=Qgis.Warning, duration=-1)  

    def cerrar(self): 
        self.dlg.close()
        self.limpiar()
        self.dlg.btn_ejecutar.setEnabled(False)
        self.dlg.btn_metodo_0.setChecked(True)

    def limpiar(self):
        self.dlg.cuadroTIF.clear()
        self.dlg.cuadroMTL.clear()
        self.dlg.cuadroBandasCorregidas.clear()
        self.dlg.cuadroGuardar.clear()
        self.archivo_MTL.clear()
        self.rutas_bandas.clear()
        self.rutas_bandas_corr.clear()
        self.ruta_guardar.clear()
        
        

    def guardar_raster(self,dataset,datasetPath,cols,rows,projection,geot):
        rasterSet = gdal.GetDriverByName('GTiff').Create(datasetPath, cols ,rows ,1,gdal.GDT_Float32)
        rasterSet.SetProjection(projection)
        rasterSet.SetGeoTransform(geot)
        rasterSet.GetRasterBand(1).WriteArray(dataset)
        rasterSet.GetRasterBand(1).SetNoDataValue(-999)
        rasterSet = None

    def correccion(self,n,banda,RADIANCE_MULT_BAND,RADIANCE_ADD_BAND,distancia_tierra_sol,cos_elevacion_solar,ESUN):

        B = gdal.Open(banda)
        dn = B.GetRasterBand(1).ReadAsArray().astype(np.float32) 
        RAD = RADIANCE_MULT_BAND * dn + RADIANCE_ADD_BAND
        REFLECTANCIA = (pi*RAD*distancia_tierra_sol**2)/(ESUN * cos_elevacion_solar)
        factor_escala =  55000  # 16000, 100000, ...
        REFLECTANCIA = REFLECTANCIA * factor_escala
        REFLECTANCIA= np.clip(REFLECTANCIA, 1, np.iinfo(np.uint16).max).astype(np.uint16)
        REFLECTANCIA[np.where(dn == 0)] = 0

        cols = B.RasterXSize
        rows = B.RasterYSize
        projection = B.GetProjection()
        geot = B.GetGeoTransform()

        self.guardar_raster(REFLECTANCIA, self.ruta_guardar[0] + f"/correcciones/C_A_B{n}.TIF",cols,rows,projection,geot)
    
                
    def filtro(self,path,archivo):
        
        #BANDAS

        for i in archivo:
            if ("B1.TIF" in i):
                banda_1 = i
            if ("B2.TIF" in i):
                banda_2 = i
            if ("B3.TIF" in i):
                banda_3 = i
            if ("B4.TIF" in i):
                banda_4 = i
            if ("B5.TIF" in i):
                banda_5 = i
            if ("B6.TIF" in i):
                banda_6 = i
            if ("B7.TIF" in i):
                banda_7 = i

        #FILTRO DEL MTL 

        with open (path, 'r') as file:
            archivo = file.read()

        array = []
        array = archivo.split()

        cont = 1
        pos = array.index('RADIANCE_MULT_BAND_1')
        RADIANCE_MULT_BAND = []
        i = 2
        while(cont < 8):
            RADIANCE_MULT_BAND.append(float(array[pos+ i]))
            i = i + 3
            cont = cont + 1

        cont = 1
        pos = array.index('RADIANCE_ADD_BAND_1')
        RADIANCE_ADD_BAND = []
        i = 2
        while(cont < 8):
            RADIANCE_ADD_BAND.append(float(array[pos+ i]))
            i = i + 3
            cont = cont + 1
        
        cont = 1
        pos = array.index('RADIANCE_MAXIMUM_BAND_1')
        RADIANCE_MAXIMUM_BAND = []
        i = 2
        while(cont < 8):
            RADIANCE_MAXIMUM_BAND.append(float(array[pos+ i]))
            i = i + 6
            cont = cont + 1
       
        cont = 1
        pos = array.index('REFLECTANCE_MAXIMUM_BAND_1')
        REFLECTANCE_MAXIMUM_BAND = []
        i = 2
        while(cont < 8):
            REFLECTANCE_MAXIMUM_BAND.append(float(array[pos+ i]))
            i = i + 6
            cont = cont + 1


        pos = array.index('SUN_ELEVATION')
        elevacion_solar = float(array[pos+2])

        pos = array.index('EARTH_SUN_DISTANCE')
        distancia_tierra_sol = float(array[pos+2])

        cos_elevacion_solar=cos((90-(elevacion_solar))*pi/180)

        cont = 1
        i = 0
        ESUN = []
        while(cont < 8):
            ESUN.append((pi*(distancia_tierra_sol)**2) * RADIANCE_MAXIMUM_BAND[i] / REFLECTANCE_MAXIMUM_BAND[i])
            cont = cont + 1
            i = i + 1

        os.mkdir(self.ruta_guardar[0] + '/correcciones')

        self.correccion(1,banda_1,RADIANCE_MULT_BAND[0],RADIANCE_ADD_BAND[0],distancia_tierra_sol,cos_elevacion_solar,ESUN[0])
        self.correccion(2,banda_2,RADIANCE_MULT_BAND[1],RADIANCE_ADD_BAND[1],distancia_tierra_sol,cos_elevacion_solar,ESUN[1])
        self.correccion(3,banda_3,RADIANCE_MULT_BAND[2],RADIANCE_ADD_BAND[2],distancia_tierra_sol,cos_elevacion_solar,ESUN[2])
        self.correccion(4,banda_4,RADIANCE_MULT_BAND[3],RADIANCE_ADD_BAND[3],distancia_tierra_sol,cos_elevacion_solar,ESUN[3])
        self.correccion(5,banda_5,RADIANCE_MULT_BAND[4],RADIANCE_ADD_BAND[4],distancia_tierra_sol,cos_elevacion_solar,ESUN[4])
        self.correccion(6,banda_6,RADIANCE_MULT_BAND[5],RADIANCE_ADD_BAND[5],distancia_tierra_sol,cos_elevacion_solar,ESUN[5])
        self.correccion(7,banda_7,RADIANCE_MULT_BAND[6],RADIANCE_ADD_BAND[6],distancia_tierra_sol,cos_elevacion_solar,ESUN[6])


    def crear_virtual(self, bandas):

        os.mkdir(self.ruta_guardar[0] + '/COMPILACION')

        bandas_iniciales = bandas
        
        # Sufijos de las bandas deseadas
        sufijos_deseados = ["_B1.TIF", "_B2.TIF", "_B3.TIF", "_B4.TIF", "_B5.TIF", "_B6.TIF", "_B7.TIF"]
        
        # Lista de bandas filtrada
        bandas_filtradas = [archivo for archivo in bandas_iniciales if any(archivo.endswith(sufijo) for sufijo in sufijos_deseados)]


        band_files = bandas_filtradas
        
        band_files_string = ' '.join(band_files)
        output_vrt = self.ruta_guardar[0] + '/COMPILACION/RASTER_VIRTUAL.vrt'
        output_tif = self.ruta_guardar[0] + '/COMPILACION/STACK_BANDS.tif'
        
        vrt_options = gdal.BuildVRTOptions(separate=True)
        vrt_ds = gdal.BuildVRT(output_vrt, band_files, options=vrt_options)
        vrt_ds.FlushCache()
        
        translate_options = gdal.TranslateOptions(format='GTiff')
        gdal.Translate(output_tif, vrt_ds, options=translate_options)


    def clasificacion_0(self):

        # Parámetros de entrada
        grids = self.ruta_guardar[0] + '/COMPILACION/STACK_BANDS.tif'  # Reemplaza con la ruta a tu imagen raster
        method = 0  # Método: 0 (Iterative Minimum Distance (Forgy 1965))
        ncluster = 10  # Número de clusters
        maxiter = 10  # Número máximo de iteraciones
        normalise =True  # Normalizar
        oldversion = False  # Versión antigua
        updateview = False  # Actualizar vista

        # Parámetros de salida
        cluster_output = self.ruta_guardar[0] + '/Iterative_Minimum_Distance.tif'  # Ruta de salida para el raster clusterizado
        statistics_output = self.ruta_guardar[0] + '/Iterative_Minimum_Distance.shp'  # Ruta de salida para las estadísticas de los clusters

        # Ejecutar el algoritmo
        processing.run("saga:kmeansclusteringforgrids",
                    {
                        'GRIDS': [grids],
                        'METHOD': method,
                        'NCLUSTER': ncluster,
                        'MAXITER': maxiter,
                        'NORMALISE': normalise,
                        'OLDVERSION': oldversion,
                        'UPDATEVIEW': updateview,
                        'CLUSTER': cluster_output,
                        'STATISTICS': statistics_output
                    })
        
        
    def clasificacion_1(self):

        # Parámetros de entrada
        grids = self.ruta_guardar[0] + '/COMPILACION/STACK_BANDS.tif'  # Reemplaza con la ruta a tu imagen raster
        method = 1  # Método: 1 (Hill-Climbing)
        ncluster = 10  # Número de clusters
        maxiter = 10  # Número máximo de iteraciones
        normalise =True  # Normalizar
        oldversion = False  # Versión antigua
        updateview = False  # Actualizar vista

        # Parámetros de salida
        cluster_output = self.ruta_guardar[0] + '/Hill-Climbing.tif'  # Ruta de salida para el raster clusterizado
        statistics_output = self.ruta_guardar[0] + '/Hill-Climbing.shp'  # Ruta de salida para las estadísticas de los clusters

        # Ejecutar el algoritmo
        processing.run("saga:kmeansclusteringforgrids",
                    {
                        'GRIDS': [grids],
                        'METHOD': method,
                        'NCLUSTER': ncluster,
                        'MAXITER': maxiter,
                        'NORMALISE': normalise,
                        'OLDVERSION': oldversion,
                        'UPDATEVIEW': updateview,
                        'CLUSTER': cluster_output,
                        'STATISTICS': statistics_output
                    })
        

    def clasificacion_2(self):

        # Parámetros de entrada
        grids = self.ruta_guardar[0] + '/COMPILACION/STACK_BANDS.tif'  # Reemplaza con la ruta a tu imagen raster
        method = 2  # Método: 2 (Combined Minimum Distance/Hillclimbing)
        ncluster = 10  # Número de clusters
        maxiter = 10  # Número máximo de iteraciones
        normalise =True  # Normalizar
        oldversion = False  # Versión antigua
        updateview = False  # Actualizar vista

        # Parámetros de salida
        cluster_output = self.ruta_guardar[0] + '/Combined_Minimum_Distance_Hillclimbing.tif'  # Ruta de salida para el raster clusterizado
        statistics_output = self.ruta_guardar[0] + '/Combined_Minimum_Distance_Hillclimbing.shp'  # Ruta de salida para las estadísticas de los clusters

        # Ejecutar el algoritmo
        processing.run("saga:kmeansclusteringforgrids",
                    {
                        'GRIDS': [grids],
                        'METHOD': method,
                        'NCLUSTER': ncluster,
                        'MAXITER': maxiter,
                        'NORMALISE': normalise,
                        'OLDVERSION': oldversion,
                        'UPDATEVIEW': updateview,
                        'CLUSTER': cluster_output,
                        'STATISTICS': statistics_output
                    })

    def ejecutar(self):
        
        os.mkdir(self.ruta_guardar[0])

        if self.estado_corr == "activo":
            bandas = self.rutas_bandas_corr
            bandas_iniciales = bandas
        
            # Sufijos de las bandas deseadas
            sufijos_deseados = ["_B1.TIF", "_B2.TIF", "_B3.TIF", "_B4.TIF", "_B5.TIF", "_B6.TIF", "_B7.TIF"]
            
            # Lista de bandas filtrada
            bandas_filtradas = [archivo for archivo in bandas_iniciales if any(archivo.endswith(sufijo) for sufijo in sufijos_deseados)]

            self.crear_virtual(bandas_filtradas)

            if self.dlg.btn_metodo_0.isChecked()==True:
                self.clasificacion_0()
                self.iface.addRasterLayer(self.ruta_guardar[0] + '/Iterative_Minimum_Distance.sdat', "Iterative Minimum Distance")

            if self.dlg.btn_metodo_1.isChecked()==True:
                self.clasificacion_1()
                self.iface.addRasterLayer(self.ruta_guardar[0] + '/Hill-Climbing.sdat', "Hill-Climbing")

            if self.dlg.btn_metodo_2.isChecked()==True:
                self.clasificacion_2()
                self.iface.addRasterLayer(self.ruta_guardar[0] + '/Combined_Minimum_Distance_Hillclimbing.sdat', "Combined Minimum Distance/Hillclimbing")
            self.limpiar()
            
        if self.estado_corr == "inactivo":
            ruta_MTL = self.archivo_MTL[0]
            bandas = self.rutas_bandas
            
            self.filtro(ruta_MTL,bandas)
        
            self.crear_virtual(bandas)
            rmtree(self.ruta_guardar[0] + '/correcciones')

            if self.dlg.btn_metodo_0.isChecked()==True:
                self.clasificacion_0()
                self.iface.addRasterLayer(self.ruta_guardar[0] + '/Iterative_Minimum_Distance.sdat', "Iterative Minimum Distance")

            if self.dlg.btn_metodo_1.isChecked()==True:
                self.clasificacion_1()
                self.iface.addRasterLayer(self.ruta_guardar[0] + '/Hill-Climbing.sdat', "Hill-Climbing")

            if self.dlg.btn_metodo_2.isChecked()==True:
                self.clasificacion_2()
                self.iface.addRasterLayer(self.ruta_guardar[0] + '/Combined_Minimum_Distance_Hillclimbing.sdat', "Combined Minimum Distance/Hillclimbing")
            self.limpiar()


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = KL8sliceDialog()

            self.dlg.btn_abrirTIF.clicked.connect(self.abrirTIF)
            self.dlg.btn_abrirMTL.clicked.connect(self.abrirMTL)
            self.dlg.btn_ejecutar.clicked.connect(self.ejecutar)
            self.dlg.btn_cerrar.clicked.connect(self.cerrar)
            self.dlg.btn_abrirCORR.clicked.connect(self.abrirCORR)
            self.dlg.btn_guardar.clicked.connect(self.guardar)
            self.dlg.btn_correccion.clicked.connect(self.estado)
            self.dlg.btn_inst.clicked.connect(self.inst)
            self.dlg.btn_ejecutar.clicked.connect(self.sonido_termino)

            self.dlg.cuadroBandasCorregidas.setEnabled(False)
            self.dlg.btn_abrirCORR.setEnabled(False)
            self.dlg.btn_ejecutar.setEnabled(False)
            self.dlg.btn_metodo_0.setChecked(True)

            self.dlg.btn_guardar.clicked.connect(self.estado_ejecutar)
            self.dlg.btn_abrirTIF.clicked.connect(self.estado_ejecutar)
            self.dlg.btn_abrirMTL.clicked.connect(self.estado_ejecutar)
            self.dlg.btn_abrirCORR.clicked.connect(self.estado_ejecutar)
            

            self.dlg.btn_abrirTIF.setToolTip("Seleccione las bandas")
            self.dlg.btn_abrirTIF.setToolTipDuration(3000)
            self.dlg.btn_abrirMTL.setToolTip("Abrir archivo")
            self.dlg.btn_abrirMTL.setToolTipDuration(3000)
            self.dlg.btn_correccion.setToolTip("Corrección atmosférica realizada")
            self.dlg.btn_correccion.setToolTipDuration(3000)
            self.dlg.btn_abrirCORR.setToolTip("Seleccione las bandas corregidas")
            self.dlg.btn_abrirCORR.setToolTipDuration(3000)
            
            self.dlg.btn_ejecutar.setToolTip("Ejecutar")
            self.dlg.btn_ejecutar.setToolTipDuration(3000)
            self.dlg.btn_guardar.setToolTip("Guardar resultados")
            self.dlg.btn_guardar.setToolTipDuration(3000)
            self.dlg.btn_cerrar.setToolTip("Cerrar")
            self.dlg.btn_cerrar.setToolTipDuration(3000)
            self.dlg.btn_inst.setToolTip("Leer instrucciones")
            self.dlg.btn_inst.setToolTipDuration(3000)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
