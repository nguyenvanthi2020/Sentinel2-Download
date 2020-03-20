# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Sentinel2Download
                                 A QGIS plugin
 Plugin này cho phép tải về ảnh vệ tinh Sentinel-2 theo đơn vị hành chính cấp xã
                              -------------------
        begin                : 2020-03-13
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Nguyễn Văn Thị
        email                : nguyenvanthi@ifee.edu.vn
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction,  QFileDialog, QDateTimeEdit
from qgis.core import QgsProject, Qgis, QgsRasterLayer

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .sentinel2_download_dialog import Sentinel2DownloadDialog
import os.path
import ee

ee.Initialize()
import json
from json import *
from datetime import date
from datetime import time
from datetime import timedelta
from datetime import datetime
from ee_plugin import Map
from itertools import groupby
import pathlib
from pathlib import Path

#from sys import exit
#from IPython import display
import zipfile
import urllib
##
from ee import *
#from ipywidgets import IntProgress

class Sentinel2Download:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
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
            'Sentinel2Download_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Sentinel-2')

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
        return QCoreApplication.translate('Sentinel2Download', message)


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
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/sentinel2_download/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sentinel-2 for Commune Downloader'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&Sentinel-2 Download'),
                action)
            self.iface.removeToolBarIcon(action)
    def layngay(self, chuoingay):
        input_date = chuoingay
        str_Input = [int(''.join(i)) for is_digit, i in groupby(input_date, str.isdigit) if is_digit]
           
        str_Output = date(int(str_Input[1]), int(str_Input[2]), int(str_Input[3]))
        
        self.ketqua = str(str_Output)
        return self.ketqua
        
    def selected(self):
      filename, _filter = QFileDialog.getSaveFileName(
        self.dlg, "Select   output file ","", '*.csv')
      self.dlg.lineEdit.setText(filename)
        
    def run(self):
        """Run method that performs all the real work"""
        #ee.Initialize()
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = Sentinel2DownloadDialog()
        # Add base map
        base_map = QgsProject.instance().mapLayersByName('Google Satellite')
        if len(base_map)== 0:
            urlWithParams = 'type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
            rlayer = QgsRasterLayer(urlWithParams, 'Google Satellite', 'wms')  
            if rlayer.isValid():
                QgsProject.instance().addMapLayer(rlayer)
            else:
                self.iface.messageBar().pushMessage(
                "Không mở được bản đồ nền!",
                level=Qgis.Success, duration=5) 
                
        self.laydanhsachtinh()
        self.dlg.comboTinh.currentIndexChanged.connect(self.laydanhsachhuyen)
        self.dlg.comboHuyen.currentIndexChanged.connect(self.laydanhsachxa)        
        self.tohopmau()
        
        self.dlg.show()

        result = self.dlg.exec_()

        if result:
            #Get date
            batdau=self.dlg.dateBdau.date()
            ketthuc=self.dlg.dateKthuc.date()
            bd_date = str(batdau)
            kt_date = str(ketthuc)
            # Get info
            tinhchon = self.dlg.comboTinh.currentText()
            huyenchon = self.dlg.comboHuyen.currentText()
            xachon = self.dlg.comboXa.currentText()
            mtinh = int(self.laymacode()['tcode'])
            mhuyen = int(self.laymacode()['hcode'])
            mxa = int(self.laymacode()['xcode'])
            
            may = int(self.dlg.inputMay.text())
            khoang = int(self.dlg.inputKhoang.text())
                      
            ngayBatdau = str(self.layngay(bd_date))
            ngayKetthuc = str(self.layngay(kt_date))
                        
            hcxvn = ee.FeatureCollection("users/nguyenvanthi/RGX_WGS84")
            commune = hcxvn.filter(ee.Filter(ee.Filter.eq('MATINH', mtinh))) \
                .filter(ee.Filter(ee.Filter.eq('MAHUYEN', mhuyen))) \
                .filter(ee.Filter(ee.Filter.eq('MAXA', mxa)))
            #Get buffer
       
          
            
            sbuffer = int(self.dlg.inputBuffer.text())
           
            
            
            
            if sbuffer == 0:
                commune_buffered = commune
            else:
                commune_buffered = commune.geometry().buffer(sbuffer)
            
            #Band combinations
            rgbMethod = self.dlg.comboRGB.currentIndex()
            if rgbMethod == 0:
                bands = ['B4', 'B3', 'B2'] # Natural Color
            elif rgbMethod == 1:
                bands = ['B8', 'B4', 'B3'] # Color Infrared
            elif rgbMethod == 2:
                bands = ['B12', 'B8A', 'B4'] # Short-wave Infrared
            elif rgbMethod == 3:
                bands = ['B11', 'B8', 'B2']  # Agriculture  
            elif rgbMethod == 4:
                bands = ['B12', 'B11', 'B2'] # Geology
            else:
                bands = ['B4', 'B3', 'B1'] # Bathymetric
                
            S2_Collection = ee.ImageCollection("COPERNICUS/S2") \
                .filterDate(ngayBatdau, ngayKetthuc).select(bands) \
                .filterBounds(commune_buffered) \
                .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', "less_than", may) \
                .sort('CLOUD_COVERAGE_ASSESSMENT', True)
            #Get the first image in the collection
            S2 = S2_Collection.first();
          
            vizParams = {'bands': bands, 'min': 0, 'max': 2000, 'gamma': 0.8};
            
            image_date1 = ee.Date(S2.get('system:time_start')).format('Y-M-d').getInfo();
            
            soluonganh = S2_Collection.size().getInfo()

            tmp = self.khoangngay(image_date1, khoang)
            
            S22 = ee.ImageCollection("COPERNICUS/S2").filterDate(tmp['bd'], tmp['kt']) \
                .select(bands) \
                .filterBounds(commune_buffered) \
                .median()\
                .clip(commune_buffered)
            Map.centerObject(commune, 14);  
            Map.addLayer(S2.clip(commune_buffered), vizParams, "S2_" + str(xachon) + "_" + image_date1 + " (Ảnh đơn)");
            Map.addLayer(S22, vizParams, "S2_" + str(xachon) + "_" + image_date1 + " (Tập hợp)");
            Map.addLayer(commune_buffered, {'color': 'red'}, "RG_" + str(xachon), False,0.2);  

           ### Save image to Google Drive3
            
                       
            ### Message bar info
            self.iface.messageBar().pushMessage(
                "Mở thành công ảnh Sentiel-2 của " + xachon + " " + huyenchon + " " + tinhchon + "!",
                level=Qgis.Success, duration=10)
            
                  
            pass

    def khoangngay(self, tmp_imagedate, nday):

        str_tmp = tmp_imagedate.split('-')

        imagedate = date(int(str_tmp[0]), int(str_tmp[1]), int(str_tmp[2]))    
        today = date.today()
        dtime = timedelta(days=nday)
     
        hs = today - imagedate
        if hs < dtime:
          sdate = imagedate - hs - dtime
          edate = today
        else:
          sdate = imagedate - dtime
          edate = imagedate + dtime

        self.template_value = {
          'bd': str(sdate),
          'kt': str(edate),
        }    
        return self.template_value
        
    def laydanhsachtinh(self):
        self.dlg.comboTinh.clear()
        tinhs = self.docdstinh()
            
        for tinh in tinhs:
            tname = tinh['TINH']
            tcode = tinh['MATINH']
            self.dlg.comboTinh.addItems([tname])  
            
    def laydanhsachhuyen(self):
        self.dlg.comboHuyen.clear()
        tentinh = self.dlg.comboTinh.currentText()
        listhuyen = self.docdshuyen()
      
        for chon in listhuyen:
            if chon['TINH'] == tentinh:
                hname =  chon['HUYEN']
                hcode = chon['MAHUYEN']
                self.dlg.comboHuyen.addItems([hname])

    def laydanhsachxa(self):
        self.dlg.comboXa.clear()
        tentinh = self.dlg.comboTinh.currentText()
        tenhuyen = self.dlg.comboHuyen.currentText()
        
        listxa = self.docdsxa()
        
        for xachon in listxa:
            if xachon['HUYEN'] == tenhuyen:
                xname = xachon['XA']
                xcode = xachon['MAXA']
                self.dlg.comboXa.addItems([xname])
    def laymacode(self):
        tenxa = self.dlg.comboXa.currentText()
        tentinh = self.dlg.comboTinh.currentText()
        tenhuyen = self.dlg.comboHuyen.currentText()
        listxa = self.docdsxa()
        for xachon in listxa:
            if xachon['XA'] == tenxa:
                if xachon['HUYEN'] == tenhuyen:
                    if xachon['TINH'] == tentinh:
                        xcode = xachon['MAXA']
                        hcode = xachon['MAHUYEN']
                        tcode = xachon['MATINH']
                        macode = {
                        'xcode': xcode,
                        'hcode': hcode,
                        'tcode': tcode
                        }
                        return macode
    
    def tohopmau(self):
        self.dlg.comboRGB.clear()
        listTohop = ['Màu tự nhiên (B4-B3-B2)', 'Màu hồng ngoại (B8-B4-B3)', 'Màu hồng ngoại sóng ngắn (B12-B8A-B4)', 'Nông nghiệp (B11-B8-B2)', 'Địa chất học (B12-B11-B2)', 'Độ sâu (B4-B3-B1)']
        self.dlg.comboRGB.addItems(listTohop)
        
    def docdstinh(self):
        dir1 = str(Path(__file__).parent.absolute()) + '\jsons\provincelist.json'
        with open(dir1) as f1:
            datax1 = json.load(f1)
            return datax1
            
    def docdshuyen(self):
        dir2 = str(Path(__file__).parent.absolute()) + '\jsons\districtlist.json'
        with open(dir2) as f2:
            datax2 = json.load(f2)
            return datax2
            
    def docdsxa(self):
        dir3 = str(Path(__file__).parent.absolute()) + '\jsons\communelist.json'
        with open(dir3) as f3:
            datax3 = json.load(f3)
            return datax3 
    def download_tif(self, image, boundary_geojson, name, folder):
        url = ee.data.makeDownloadUrl(ee.data.getDownloadId({
            'image': image.serialize(),
            'scale': 10,
            'filePerBand': 'false',
            'name': name,
            'region': boundary_geojson,
   
        }))
        local_zip, header = urllib.request.urlretrieve(url)
        with zipfile.ZipFile(local_zip) as local_zipfile:
            return local_zipfile.extract(name + '.tif', folder)
            
    def downloader(self, image,  name): 
        url = ee.data.makeDownloadUrl(
            ee.data.getDownloadId({
                'image': image.serialize(),
                'scale': 10,
                'filePerBand': 'false',
                'name': name,
                
            }))
        return url