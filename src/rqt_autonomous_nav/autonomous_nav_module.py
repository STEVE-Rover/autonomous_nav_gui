import os
import rospy
import rospkg
import csv
from qt_gui.plugin import Plugin
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget, QFileDialog, QListWidgetItem
from std_srvs.srv import Empty
from goal_manager.srv import SetGpsGoal
from goal_manager.msg import GpsGoal
from actionlib_msgs.msg import GoalID
from std_msgs.msg import Int8, Float32

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

        # Variables
        self.navStateLabelStyleSheet = self._widget.navigationStateBadgeLabel.styleSheet().split("\n")
        self.goal_list = []

        # Service clients
        self.set_active_goal_srv = rospy.ServiceProxy('goal_manager/set_active_goal', SetGpsGoal)
        self.start_nav_srv = rospy.ServiceProxy('goal_manager/start_navigation', Empty)

        # Topics
        self.cancel_nav_pub = rospy.Publisher("/move_base/cancel", GoalID, queue_size=1)
        rospy.Subscriber("/led_controller/color", Int8, self.state_cb)
        rospy.Subscriber("goal_manager/distance_to_goal", Float32, self.distance_to_goal_cb)

        # Connect buttons
        self._widget.importListButton.clicked.connect(self.import_list) 
        self._widget.exportListButton.clicked.connect(self.export_list)
        self._widget.removeButton.clicked.connect(self.remove_item)
        self._widget.moveUpButton.clicked.connect(self.move_up_item)
        self._widget.moveDownButton.clicked.connect(self.move_down_item)
        self._widget.addGoalButton.clicked.connect(self.add_goal)
        self._widget.setActiveGoalButton.clicked.connect(self.set_active_goal)
        self._widget.startNavButton.clicked.connect(self.start_nav)
        self._widget.stopNavButton.clicked.connect(self.stop_nav)

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
        self.show_goal_list()

    def show_goal_list(self):
        self._widget.goalListWidget.clear()
        for i, row in enumerate(self.goal_list):
            text = '[' + str(i) + '] ' + ' '.join(row)
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

    def remove_item(self):
        if not len(self.goal_list) == 0:
            row = self._widget.goalListWidget.currentRow()
            self.goal_list.pop(row)
            self.show_goal_list()
            if row >= len(self.goal_list):
                row -= 1
            self._widget.goalListWidget.setCurrentRow(row)

    def move_up_item(self):
        self.move_item(-1)

    def move_down_item(self):
        self.move_item(1)

    def move_item(self, moving_distance):
        row = self._widget.goalListWidget.currentRow()
        new_row = row + moving_distance
        if not (new_row < 0 or new_row >=len(self.goal_list)):
            item = self.goal_list.pop(row)
            self.goal_list.insert(new_row, item)
            self.show_goal_list()
            self._widget.goalListWidget.setCurrentRow(new_row)

    def add_goal(self):
        type = str(self._widget.goalTypeComboBox.currentIndex())
        lat = str(self._widget.latitudeSpinBox.value())
        long = str(self._widget.longitudeSpinBox.value())
        item = [type, lat, long]
        self.goal_list.append(item)
        self.show_goal_list()

    def set_active_goal(self):
        row = self._widget.goalListWidget.currentRow()
        if row >= 0:
            try:
                goal = GpsGoal()
                goal.type = int(self.goal_list[row][0])
                goal.latitude = float(self.goal_list[row][1])
                goal.longitude = float(self.goal_list[row][2])
                self.set_active_goal_srv(goal)

                typeText = "GNSS only"
                if goal.type == 1:
                    typeText = "Post"
                elif goal.type == 2:
                    typeText = "Gate"
                    print(typeText)
                self._widget.goalTypeLabel.setText(typeText)
                self._widget.coordinateLabel.setText("%s, %s" % (goal.latitude, goal.longitude))
                self._widget.goalNumberLabel.setText(str(row))
            except rospy.ServiceException as e:
                print("Service call failed: %s" % e)

    def start_nav(self):
        rospy.loginfo("Starting navigation")
        try:
            self.start_nav_srv()
        except rospy.ServiceException as e:
                print("Service call failed: %s" % e)

    def stop_nav(self):
        rospy.loginfo("Stopping navigation")
        self.cancel_nav_pub.publish(GoalID())

    def state_cb(self, msg):
        if msg.data == 0:
            # Off (grey)
            new_color = "grey"
            self._widget.navigationStateLabel.setText("-")
        elif msg.data == 1:
            # Navigating (red)
            new_color = "rgb(255, 0, 0)"
            self._widget.navigationStateLabel.setText("Navigating")
        elif msg.data == 2:
            # Teleoperating (blue)
            new_color = "rgb(0, 0, 255)"
            self._widget.navigationStateLabel.setText("Teleoperating")
        elif msg.data == 3:
            # Goal reached (green)
            new_color = "rgb(0, 255, 0)"
            self._widget.navigationStateLabel.setText("Goal Reached")
        self.change_backgroung_color(new_color)
        self._widget.navigationStateBadgeLabel.setStyleSheet("\n".join(self.navStateLabelStyleSheet))

    def change_backgroung_color(self, new_color):
        for i, line in enumerate(self.navStateLabelStyleSheet):
            if "background-color" in line:
                self.navStateLabelStyleSheet[i] = "background-color: %s;" % new_color
                break

    def distance_to_goal_cb(self, msg):
        self._widget.distanceToGoalLabel.setText("%.2f m" % msg.data)