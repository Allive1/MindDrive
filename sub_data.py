from cortex import Cortex
import json
from numpy import mean
import queue
from tello import Tello
import time
import threading
import datetime

start_time = str(datetime.datetime.now())

def flag_switch(event, flag):
    # event.wait(2.0)
    time.sleep(2.0)
    flag = True


class Subcribe:
    """
    A class to subscribe data stream.
    Attributes
    ----------
    c : Cortex
        Cortex communicate with Emotiv Cortex Service
    Methods
    -------
    start():
        start data subscribing process.
    sub(streams):
        To subscribe to one or more data streams.
    on_new_data_labels(*args, **kwargs):
        To handle data labels of subscribed data
    on_new_eeg_data(*args, **kwargs):
        To handle eeg data emitted from Cortex
    on_new_mot_data(*args, **kwargs):
        To handle motion data emitted from Cortex
    on_new_dev_data(*args, **kwargs):
        To handle device information data emitted from Cortex
    on_new_met_data(*args, **kwargs):
        To handle performance metrics data emitted from Cortex
    on_new_pow_data(*args, **kwargs):
        To handle band power data emitted from Cortex
    """

    def __init__(self, app_client_id, app_client_secret, event, **kwargs):
        """
        Constructs cortex client and bind a function to handle subscribed data streams
        If you do not want to log request and response message , set debug_mode = False. The default is True
        """
        print("Subscribe __init__")
        self.c = Cortex(app_client_id, app_client_secret, debug_mode=True, **kwargs)
        self.c.bind(create_session_done=self.on_create_session_done)
        self.c.bind(new_data_labels=self.on_new_data_labels)
        self.c.bind(new_eeg_data=self.on_new_eeg_data)
        self.c.bind(new_mot_data=self.on_new_mot_data)
        self.c.bind(new_dev_data=self.on_new_dev_data)
        self.c.bind(new_met_data=self.on_new_met_data)
        self.c.bind(new_pow_data=self.on_new_pow_data)
        self.c.bind(inform_error=self.on_inform_error)
        self.event = event

        self.x_queue = queue.Queue(30)
        self.y_queue = queue.Queue(30)
        self.z_queue = queue.Queue(30)
        self.current_x_avg = 0
        self.current_y_avg = 0
        self.current_z_avg = 0

        self.rounded_x_avg = 0
        self.rounded_y_avg = 0
        self.rounded_z_avg = 0

        self.last_command_time = datetime.datetime.now()

        """
        Constructs tello client to connect to drone
        """
        self.drone = Tello()
        self.drone.send_command('command')
        # self.log = self.drone.get_log()
        self.grounded_flag = True
        self.test_flag = True


    def start(self, streams, headsetId=''):
        """
        To start data subscribing process as below workflow
        (1)check access right -> authorize -> connect headset->create session
        (2) subscribe streams data
        'eeg': EEG
        'mot' : Motion
        'dev' : Device information
        'met' : Performance metric
        'pow' : Band power
        'eq' : EEQ Quality
        Parameters
        ----------
        streams : list, required
            list of streams. For example, ['eeg', 'mot']
        headsetId: string , optional
             id of wanted headet which you want to work with it.
             If the headsetId is empty, the first headset in list will be set as wanted headset
        Returns
        -------
        None
        """
        self.streams = streams

        if headsetId != '':
            self.c.set_wanted_headset(headsetId)

        self.c.open()

    def sub(self, streams):
        """
        To subscribe to one or more data streams
        'eeg': EEG
        'mot' : Motion
        'dev' : Device information
        'met' : Performance metric
        'pow' : Band power
        Parameters
        ----------
        streams : list, required
            list of streams. For example, ['eeg', 'mot']
        Returns
        -------
        None
        """
        self.c.sub_request(streams)

    def unsub(self, streams):
        """
        To unsubscribe to one or more data streams
        'eeg': EEG
        'mot' : Motion
        'dev' : Device information
        'met' : Performance metric
        'pow' : Band power
        Parameters
        ----------
        streams : list, required
            list of streams. For example, ['eeg', 'mot']
        Returns
        -------
        None
        """
        self.c.unsub_request(streams)

    def on_new_data_labels(self, *args, **kwargs):
        """
        To handle data labels of subscribed data
        Returns
        -------
        data: list
              array of data labels
        name: stream name
        For example:
            eeg: ["COUNTER","INTERPOLATED", "AF3", "T7", "Pz", "T8", "AF4", "RAW_CQ", "MARKER_HARDWARE"]
            motion: ['COUNTER_MEMS', 'INTERPOLATED_MEMS', 'Q0', 'Q1', 'Q2', 'Q3', 'ACCX', 'ACCY', 'ACCZ', 'MAGX', 'MAGY', 'MAGZ']
            dev: ['AF3', 'T7', 'Pz', 'T8', 'AF4', 'OVERALL']
            met : ['eng.isActive', 'eng', 'exc.isActive', 'exc', 'lex', 'str.isActive', 'str', 'rel.isActive', 'rel', 'int.isActive', 'int', 'foc.isActive', 'foc']
            pow: ['AF3/theta', 'AF3/alpha', 'AF3/betaL', 'AF3/betaH', 'AF3/gamma', 'T7/theta', 'T7/alpha', 'T7/betaL', 'T7/betaH', 'T7/gamma', 'Pz/theta', 'Pz/alpha', 'Pz/betaL', 'Pz/betaH', 'Pz/gamma', 'T8/theta', 'T8/alpha', 'T8/betaL', 'T8/betaH', 'T8/gamma', 'AF4/theta', 'AF4/alpha', 'AF4/betaL', 'AF4/betaH', 'AF4/gamma']
        """
        data = kwargs.get('data')
        stream_name = data['streamName']
        stream_labels = data['labels']
        print('{} labels are : {}'.format(stream_name, stream_labels))

    def on_new_eeg_data(self, *args, **kwargs):
        """
        To handle eeg data emitted from Cortex
        Returns
        -------
        data: dictionary
             The values in the array eeg match the labels in the array labels return at on_new_data_labels
        For example:
           {'eeg': [99, 0, 4291.795, 4371.795, 4078.461, 4036.41, 4231.795, 0.0, 0], 'time': 1627457774.5166}
        """
        data = kwargs.get('data')
        print('eeg data: {}'.format(data))

    def on_new_mot_data(self, *args, **kwargs):
        """
        To handle motion data emitted from Cortex
        Returns
        -------
        data: dictionary
             The values in the array motion match the labels in the array labels return at on_new_data_labels
        For example: {'mot': [33, 0, 0.493859, 0.40625, 0.46875, -0.609375, 0.968765, 0.187503, -0.250004, -76.563667, -19.584995, 38.281834], 'time': 1627457508.2588}
        """

        # read stream data
        data = kwargs.get('data')
        jtopy = json.dumps(data)
        data_json = json.loads(jtopy)
        # print(data_json)

        # parse stream data using X, Y, Z axis of the accelerometer
        if data_json['mot'][0] == 31:
            print('set: {} {} {}'.format(data_json['mot'][6], data_json['mot'][7], data_json['mot'][8]))

        # pop values from queues
        if self.x_queue.full():
            item1 = self.x_queue.get()
        if self.y_queue.full():
            item1 = self.y_queue.get()
        if self.z_queue.full():
            item1 = self.z_queue.get()

        # push through queues
        self.x_queue.put(data_json['mot'][6])
        self.y_queue.put(data_json['mot'][7])
        self.z_queue.put(data_json['mot'][8])

        # calculate
        # global current_x_avg, current_y_avg, current_z_avg, test_flag, event

        y_li = list(self.y_queue.queue)
        self.current_y_avg = mean(y_li)
        self.rounded_y_avg = round(self.current_y_avg, 2)
        # print("The Y average is ", rounded_y_avg)

        x_li = list(self.x_queue.queue)
        self.current_x_avg = mean(x_li)
        self.rounded_x_avg = round(self.current_x_avg, 2)
        # print("The X average is ", rounded_x_avg)

        z_li = list(self.z_queue.queue)
        self.current_z_avg = mean(z_li)
        self.rounded_z_avg = round(self.current_z_avg, 2)
        # print("The Z average is ", rounded_z_avg)

        # if drone is grounded
        if self.grounded_flag:
            # check y average for takeoff
            if self.rounded_y_avg > 0.20:
                self.drone.send_command('takeoff')
                print('takeoff.................')
                time.sleep(2.0)
                self.last_command_time = datetime.datetime.now()
                # pass
                self.grounded_flag = False
        # if drone is airbourne
        elif not self.grounded_flag:
            c = datetime.datetime.now() - self.last_command_time

            # check y average for landing
            if -0.63 > self.rounded_y_avg:
                self.drone.send_command('land')
                print('land.................')
                time.sleep(2.0)
                self.grounded_flag = True
                self.last_command_time = datetime.datetime.now()
                # out = open('log/' + start_time + '.txt', 'w')
                # for stat in self.log:
                #     stat.print_stats()
                #     str = stat.return_stats()
                #     out.write(str)
            elif self.rounded_y_avg > 0.20 and c.seconds > 1.5:
                self.drone.send_command('back 40')
                print('fly back 20.................')
                self.last_command_time = datetime.datetime.now()

            # check x average for left/stop turn
            if self.rounded_z_avg < -0.50 and c.seconds > 1.5:
                self.drone.send_command("left 40")
                print("fly left 20................")
                self.last_command_time = datetime.datetime.now()

            # check x average for right/stop turn
            elif self.rounded_z_avg > 0.50 and c.seconds > 1.5:
                self.drone.send_command("right 40")
                print("fly right 20................")
                self.last_command_time = datetime.datetime.now()
                # pass

            # # check z average for stopping/reversing
            # if -0.50 > self.rounded_y_avg > -0.30:

            # # check z average for starting/thrusting
            if -0.30 > self.rounded_y_avg > -0.63 and c.seconds > 1.5:
                self.drone.send_command("forward 40")
                print("fly forward 20................")
                self.last_command_time = datetime.datetime.now()

        # # if head has been held up for a while
        # if rounded_avg > 0.00:
        #     # if grounded, take off
        #     if self.grounded_flag:
        #         self.drone.send_command('takeoff')
        #         self.grounded_flag = False
        # # if head held down
        # elif rounded_avg < 0.00:
        #     # if airborne, land
        #     if not self.grounded_flag:
        #         self.drone.send_command('land')
        #         self.grounded_flag = True

    def on_new_dev_data(self, *args, **kwargs):
        """
        To handle dev data emitted from Cortex
        Returns
        -------
        data: dictionary
             The values in the array dev match the labels in the array labels return at on_new_data_labels
        For example:  {'signal': 1.0, 'dev': [4, 4, 4, 4, 4, 100], 'batteryPercent': 80, 'time': 1627459265.4463}
        """
        data = kwargs.get('data')
        print('dev data: {}'.format(data))

    def on_new_met_data(self, *args, **kwargs):
        """
        To handle performance metrics data emitted from Cortex
        Returns
        -------
        data: dictionary
             The values in the array met match the labels in the array labels return at on_new_data_labels
        For example: {'met': [True, 0.5, True, 0.5, 0.0, True, 0.5, True, 0.5, True, 0.5, True, 0.5], 'time': 1627459390.4229}
        """
        data = kwargs.get('data')
        print('pm data: {}'.format(data))

    def on_new_pow_data(self, *args, **kwargs):
        """
        To handle band power data emitted from Cortex
        Returns
        -------
        data: dictionary
             The values in the array pow match the labels in the array labels return at on_new_data_labels
        For example: {'pow': [5.251, 4.691, 3.195, 1.193, 0.282, 0.636, 0.929, 0.833, 0.347, 0.337, 7.863, 3.122, 2.243, 0.787, 0.496, 5.723, 2.87, 3.099, 0.91, 0.516, 5.783, 4.818, 2.393, 1.278, 0.213], 'time': 1627459390.1729}
        """
        data = kwargs.get('data')
        print('pow data: {}'.format(data))

    # callbacks functions
    def on_create_session_done(self, *args, **kwargs):
        print('on_create_session_done')

        # subribe data
        self.sub(self.streams)

    def on_inform_error(self, *args, **kwargs):
        error_data = kwargs.get('error_data')
        print(error_data)


# -----------------------------------------------------------
#
# GETTING STARTED
#   - Please reference to https://emotiv.gitbook.io/cortex-api/ first.
#   - Connect your headset with dongle or bluetooth. You can see the headset via Emotiv Launcher
#   - Please make sure the your_app_client_id and your_app_client_secret are set before starting running.
#   - In the case you borrow license from others, you need to add license = "xxx-yyy-zzz" as init parameter
# RESULT
#   - the data labels will be retrieved at on_new_data_labels
#   - the data will be retreived at on_new_[dataStream]_data
#
# -----------------------------------------------------------

def main():
    # Please fill your application clientId and clientSecret before running script
    your_app_client_id = 'lymvMXJlmzSjfmj2JHdkSdtJWIhvWObV9kFY6YaV'
    your_app_client_secret = 'mHRmaSGntxpAAqlvdFHivogOu8PhImyJsj7OSOdJ9np6Ul2a2VT9EcZVd2VO5qJZ77ouHhGogAejx1NaLKU2nJEj9Ri6JPUVhZC5ChZNOshQuBG0kDd8cfBEUitFRxOX'
    event = threading.Event()
    s = Subcribe(your_app_client_id, your_app_client_secret, event)

    # list data streams
    # streams = ['eeg', 'mot', 'met', 'pow']
    streams = ['mot']
    s.start(streams)


if __name__ == '__main__':
    main()

# -----------------------------------------------------------
