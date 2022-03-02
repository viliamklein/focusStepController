import serial
import traceback
import configparser
import time

class stepController:

    def __init__(self, devname, configData, dataQ):
        
        try:
            self.serialPort = serial.Serial(port=devname,
                                            baudrate=configData.getint('Comm', 'baudrate'),
                                            timeout=configData.getint('Comm', 'pyserialtimeout'))

            responseDelayCommand = 'aP{:d}'.format(configData.getint('Comm', 'responsedelay'))
            self.sendCommand(responseDelayCommand)            

            self.focusAxis = configData.get('StepperParams', 'FocusAxis')
            self.MaxVelocity = configData.get('StepperParams', 'MaxVelocity')
            self.MicroStepResolution = configData.get('StepperParams', 'MicroStepResolution')
            self.DriveMode = configData.get('StepperParams', 'DriveMode')
            self.MoveCurrent = configData.get('StepperParams', 'MoveCurrent')

            self.UpperSwitchMask = int(configData.get('StepperParams', 'upperLimitSwitchMask'), 16)
            self.LowerSwitchMask = int(configData.get('StepperParams', 'lowerLimitSwitchMask'), 16)

            setResCmd = 'j' + self.MicroStepResolution
            setMVCmd = 'aM' + self.focusAxis + 'V' + self.MaxVelocity
            setMICmd = 'aM' + self.focusAxis + 'm' + self.MoveCurrent
            setModeCmd = 'aM' + self.focusAxis + 'N' + self.DriveMode

            self.sendCommand(setResCmd)
            self.sendCommand(setMVCmd)
            self.sendCommand(setMICmd)
            self.sendCommand(setModeCmd)

            self.sendCommand('aM3n2')

            self.currCountsConfig = configparser.ConfigParser()
            self.countFname = configData.get('savePos', 'currentCountFile')
            self.currCountsConfig.read(self.countFname)
            self.currCounts = self.currCountsConfig.getint('Position', 'counts')
            self.startCounts = self.currCounts


            responseDelayCommand = 'aP{:d}'.format(configData.getint('Comm', 'responsedelay'))
            self.sendCommand(responseDelayCommand)

            self.dataQ = dataQ

        except Exception:

            traceback.print_last()
    
    def __del__(self):

        self.stopMotion()
        
        val = self.readPosition()
        self.currCountsConfig['Position'] = {'counts': val['FocusAxis']}

        with open(self.countFname, 'w') as ff:
            self.currCountsConfig.write(ff)
        
        self.serialPort.close()

    def readHouseKeepingData(self):

        self.hkData = self.readPosition()
        time.sleep(0.02)
        self.hkData['FocusSwitches'] = self.readFocusSwitchs()
        time.sleep(0.02)
        self.hkData['FocusVelocity'] = self.readCurrVelocity()

        return self.hkData

    def readCurrVelocity(self):
        
        # self.serialPort.write(b'/1?aV\r\n')
        # res = self.serialPort.read_until(expected=b'\n')
        # self.sendCommand('aM3')
        # time.sleep(0.02)
        self.serialPort.write(b'/1aM3R\r\n')
        self.serialPort.read_until(expected=b'\n')
        self.serialPort.write(b'/1?1\r\n')
        res = self.serialPort.read_until(expected=b'\n')

        indStart = res.find(b'\x2F\x30') + 3
        indEnd = res.find(b'\x03')
        
        vel = res[indStart:indEnd].decode('utf-8')
        
        # vel = vel.split(',')
        # vel = [int(xx) for xx in vel]
        # axisVal = int(self.focusAxis)
        
        # vel = vel[axisVal-1]
        return int(vel)

    def readFocusSwitchs(self):
        
        self.serialPort.write(b'/1?43\r\n')
        res = self.serialPort.read_until(expected=b'\n')
        
        indu = res.find(b'\x03')
        indl = res.find(b'/')
        res = int(res[indl+3:indu])

        return res

    def stopMotion(self):
        self.serialPort.write(b'/1T3\r\n')
        self.serialPort.read_until(expected=b'\n')


    def setMaxVel(self, vel):

        setMVCmd = 'aM' + self.focusAxis + 'V{:d}'.format(vel)
        self.sendCommand(setMVCmd)


    def moveNegativeCounts(self, counts):

        movCmd = 'aM' + self.focusAxis + 'D{:d}'.format(abs(counts))
        self.sendCommand(movCmd)

    def movePositiveCounts(self, counts):

        movCmd = 'aM' + self.focusAxis + 'P{:d}'.format(abs(counts))
        self.sendCommand(movCmd)

    def readPosition(self):

        msg = self.addPrefix + b'?aA\r\n'
        self.serialPort.write(msg)
        res = self.serialPort.read_until(expected=b'\n')

        indStart = res.find(b'\x2F\x30') + 3
        indEnd = res.find(b'\x03')

        position = res[indStart:indEnd].decode('utf-8')
        position = position.split(',')
        position = [int(xx) for xx in position]
        axisVal = int(self.focusAxis)

        self.currCounts = position[axisVal-1]
        posData = {'FocusAxis': self.currCounts}

        self.currCountsConfig['Position'] = {'counts': self.currCounts}

        return posData

    def sendCommand(self, cmdString):

        cmd = self.createCommand(cmdString)

        self.serialPort.write(cmd)
        # res = str(self.serialPort.read_until('\n'))
        res = self.serialPort.read_until(expected=b'\n')
        self.parseResult(res)

    def parseResult(self, res):

        ind = res.find(b'\x2F\x30')
        errVal = res[ind+2]

        if (errVal & 0x0F) == 15:
            print('OVERFLOW')
            time.sleep(0.1)
        elif (errVal & 0x0F) != 0:
            raise nonZeroErrorCode(errVal)
    
        
    def createCommand(self, cmdString):

        cmd = self.addPrefix + bytes(cmdString, 'utf-8') + self.postfix
        return cmd
    
    def parseServerCommand(self, command):

        # readInt = lambda ss : int(ss)
        if self.moveCommand in command:

            countsToMove = self.parseNumInCommand(command)
            if countsToMove > 0:
                self.movePositiveCounts(countsToMove)
            elif countsToMove < 0:
                self.moveNegativeCounts(countsToMove)
            else:
                raise ValueError
            
            # self.dataQ.rxQ.put(True)

        elif self.statCommand in command:

            data = self.readHouseKeepingData()
            self.dataQ.rxQ.put(data)

        

    
    def parseNumInCommand(self, ss):

        try:
            ss = ss.split()
            num = int(ss[1])
            return num
        except ValueError:
            print('malformed int')
            pass
        
    
    moveCommand = 'move'
    velCommand = 'velocity'
    statCommand = 'status'

    addPrefix = b'/1'
    postfix = b'R\r\n'
        

class stepError(Exception):
    """ Base class for stepper Errors """
    pass

class nonZeroErrorCode(stepError):
    """ response code shows non zero value """
    def __init__(self, errorValue):
        self.errorValue = errorValue
        super().__init__(self.errorValue)

if __name__ == '__main__':

    import argparse
    import queue

    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("configFile", help="pass the name of the config file dummy")
    args = parser.parse_args()

    # parse config file
    stepConfig = configparser.ConfigParser()
    stepConfig.read(args.configFile)
    
    dataQ = queue.Queue
    st = stepController('/dev/stepperControl', stepConfig, dataQ)
    
    while True:
        try: 
            data = st.readHouseKeepingData()

            ss = 'Focus Counts: {:06d}\t'\
                 'Switch Status: {:02d}\t'\
                 'Velocity: {:05d}'.format(data['FocusAxis'], 
                    data['FocusSwitches'], 
                    data['FocusVelocity'])

            print(ss)
            time.sleep(1)
        
        except KeyboardInterrupt:
            break

    print('Done')