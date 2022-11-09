import os
import rospy
import rospkg
import csv
from qt_gui.plugin import Plugin
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget, QFileDialog, QListWidgetItem

class MyPlugin(Plugin):

    def __init__(self, context):
        super(MyPlugin, self).__init__(context)
        # Give QObjects reasonable names
        self.setObjectName('MyPlugin')

        # Process standalone plugin command-line arguments
        from argparse import ArgumentParser
        parser = ArgumentParser()
        # Add argument(s) to the parser.
        parser.add_argument("-q", "--quiet", action="store_true",
                      dest="quiet",
                      help="Put plugin in silent mode")
        args, unknowns = parser.parse_known_args(context.argv())
        if not args.quiet:
            print('arguments: ', args)
            print('unknowns: ', unknowns)

        # Create QWidget
        self._widget = QWidget()
        # Get path to UI file which should be in the "resource" folder of this package
        ui_file = os.path.join(rospkg.RosPack().get_path('rqt_autonomous_nav'), 'resource', 'autonomous_nav_gui.ui')
        # Extend the widget with all attributes and children from UI file
        loadUi(ui_file, self._widget)
        # Give QObjects reasonable names
        self._widget.setObjectName('MyPluginUi')
        # Show _widget.windowTitle on left-top of each plugin (when 
        # it's set in _widget). This is useful when you open multiple 
        # plugins at once. Also if you open multiple instances of your 
        # plugin at once, these lines add number to make it easy to 
        # tell from pane to pane.
        if context.serial_number() > 1:
            self._widget.setWindowTitle(self._widget.windowTitle() + (' (%d)' % context.serial_number()))
        # Add widget to the user interface
        context.add_widget(self._widget)

        self.goal_list = []

        # Connect buttons
        self._widget.importListButton.clicked.connect(self.import_list) 
        self._widget.exportListButton.clicked.connect(self.export_list)

    def shutdown_plugin(self):
        # TODO unregister all publishers here
        pass

    def save_settings(self, plugin_settings, instance_settings):
        # TODO save intrinsic configuration, usually using:
        # instance_settings.set_value(k, v)
        pass

    def restore_settings(self, plugin_settings, instance_settings):
        # TODO restore intrinsic configuration, usually using:
        # v = instance_settings.value(k)
        pass

    #def trigger_configuration(self):
        # Comment in to signal that the plugin has a way to configure
        # This will enable a setting button (gear icon) in each dock widget title bar
        # Usually used to open a modal configuration dialog

    def import_list(self):
        response = QFileDialog.getOpenFileName(
            parent = self._widget,
            caption = "Select file",
            directory = os.getcwd(),
            filter = "Goal list file (*.csv)"
        )

        file = response[0]
        print(file)

        self.goal_list = []
        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for i, row in enumerate(csv_reader):
                if (i != 0):
                    self.goal_list.append(row)
        print(self.goal_list)
        self.show_goal_list()

    def show_goal_list(self):
        self._widget.goalListWidget.clear()
        for i, row in enumerate(self.goal_list):
            text = '[' + str(i) + '] ' + ' '.join(row)
            print(text)
            self._widget.goalListWidget.addItem(QListWidgetItem(text))

    def export_list(self):
        response = QFileDialog.getSaveFileName(
            parent = self._widget,
            caption = "Save file",
            directory = os.getcwd(),
            filter = "Goal list file (*.csv)"
        )

        file = response[0]
        if not file.endswith(".csv"):
            file = file + ".csv"
        print(file)

        with open(file, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',')
            csv_writer.writerow(['type', 'latitude', 'longitude'])
            for row in self.goal_list:
                csv_writer.writerow(row)

