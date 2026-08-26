# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'gis@envirosolutions.pl'
__date__ = '2024-08-28'
__copyright__ = 'Copyright 2024, EnviroSolutions Sp. z o.o.'

import unittest

from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog
from ..utils import QtCompat
from web_service_plugin_dialog import WebServicePluginDialog

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()


class WebServicePluginDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = WebServicePluginDialog(None)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_ok(self):
        """Test we can click OK."""
        ok = QtCompat.getEnum(QDialogButtonBox, 'StandardButton', 'Ok')
        button = self.dialog.button_box.button(ok)
        button.click()
        result = self.dialog.result()
        accepted = QtCompat.getEnum(QDialog, 'DialogCode', 'Accepted')
        self.assertEqual(result, accepted)

    def test_dialog_cancel(self):
        """Test we can click cancel."""
        cancel = QtCompat.getEnum(QDialogButtonBox, 'StandardButton', 'Cancel')
        button = self.dialog.button_box.button(cancel)
        button.click()
        result = self.dialog.result()
        rejected = QtCompat.getEnum(QDialog, 'DialogCode', 'Rejected')
        self.assertEqual(result, rejected)

if __name__ == "__main__":
    suite = unittest.makeSuite(WebServicePluginDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

