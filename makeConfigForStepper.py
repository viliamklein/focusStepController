import configparser

stepConfig = configparser.ConfigParser()

'''
Communications config for baudrate, devname, delays, etc.
'''
stepConfig['Comm'] = {'baudrate': 9600,
                      'devname': '/dev/stepperControl',
                      'pySerialTimeout': 1,
                      'responseDelay': 10}

stepConfig['StepperParams'] = {'MicroStepResolution': 256,
                               'MaxVelocity': 150,
                               'MoveCurrent': 20,
                               'FocusAxis': 3,
                               'DriveMode': 1,}

with open('firstConfig.ini', 'w') as ff:
    stepConfig.write(ff)