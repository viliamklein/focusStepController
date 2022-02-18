from queue import Queue
import queue
from termios import ECHO
import serial
import signal
import traceback
import sys
import time
import configparser
import argparse
import stepControl

def signal_handler(sig, frame):
    # print('You pressed Ctrl+C!')
    sys.exit(0)

def printHKdata(data):

    ss = 'Focus Counts: {:06d}\t'\
         'Switch Status: {:02d}\t'\
         'Velocity: {:05d}'.format(data['FocusAxis'], 
                                   data['FocusSwitches'], 
                                   data['FocusVelocity'])
    print(ss, end='\r')

def main(argv):

    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("configFile", help="pass the name of the config file dummy")
    args = parser.parse_args()

    # parse config file
    stepConfig = configparser.ConfigParser()
    stepConfig.read(args.configFile)

    dataQ = queue.Queue

    st = stepControl.stepController('/dev/stepperControl', stepConfig, dataQ)

    # for xx in range(10):

    #     print(st.readPosition())

    # print(stepConfig.sections())

    while True:

        try: 
            inChoice = input("""
P: Move focus in positive direction
D: Move focus in negative direction
V: Set maximum velocity
R: Read focus position
C: Send command
x: exit
""")
            
            if inChoice == 'x':
                st.stopMotion()
                break

            elif inChoice == 'C' or inChoice == 'c':
                val = input('Write Command to send:')
                val = (val + '\r\n').encode('utf-8')

                st.serialPort.write(val)
                res = st.serialPort.read_until(expected=b'\n')
                print(res)
                # print(type(val))

            elif inChoice == 'I' or inChoice == 'i':
                
                count = 0
                while True:
                    st.serialPort.write(b'/1?43\r\n')
                    res = st.serialPort.read_until(expected=b'\n')
                    
                    indu = res.find(b'\x03')
                    indl = res.find(b'/')
                    res = int(res[indl+3:indu])
                    # res = int(res[ind-2:ind].decode())

                    count += 1

                    # if res != 15:
                    #     print('Found Switch!!', end='\r')
                    # else:
                    # print('count: {:03d}\tres: {:s}'.format(count, res), end='\r')
                    # print('Count: {:d}\t'.format(count), end='')
                    # print(res)
                    print('Count: {:05d}\tres: {:02d}'.format(count, res), end='\r')
                    time.sleep(0.2)

            elif inChoice == 'R' or inChoice == 'r':
                
                pos = st.readPosition()
                print('\nCurr Counts: {:05d}'.format(pos['FocusAxis']))

            elif inChoice == 'P' or inChoice == 'p':
                 
                val = input('Enter number of counts: ')
                val = int(val)
                
                st.movePositiveCounts(val)
                print('\n')
                while True:
                    # pos = st.readPosition()
                    # print('Curr Counts: {:06d}'.format(pos['FocusAxis']), end='\r')
                    hkdata = st.readHouseKeepingData()
                    printHKdata(hkdata)
                    # print(hkdata['FocusAxis'])
                    time.sleep(0.2)
            
            elif inChoice == 'D' or inChoice == 'd':
                 
                val = input('Enter number of counts: ')
                val = int(val)
                
                st.moveNegativeCounts(val)
                print('\n')
                while True:
                    # pos = st.readPosition()
                    # print('Curr Counts: {:05d}'.format(pos['FocusAxis']), end='\r')
                    hkdata = st.readHouseKeepingData()
                    printHKdata(hkdata)
                    # print(hkdata['FocusAxis'])
                    time.sleep(0.2)
            
            elif inChoice == 'V' or inChoice == 'v':
                vel = input('Enter max velocity: ')
                st.setMaxVel(int(vel))
        
        except KeyboardInterrupt:
            st.stopMotion()
            pass

        except Exception as ee:
            st.stopMotion()
            print(ee)
            traceback.print_last()
            break
    
    print('Done')

if __name__ == '__main__':

    main(sys.argv)




# # signal.signal(signal.SIGINT, signal_handler)

# stepControlPort = serial.Serial('/dev/stepperControl', baudrate=9600, timeout=1)

# print(readFirmwareVersion(stepControlPort))

# # stepControlPort.write(b'/1aM3R\r\n')
# # res = str(stepControlPort.read_until('\n'))
# # print(res)

# stepControlPort.write(b'/1j256R\r\n')
# res = str(stepControlPort.read_until('\n'))
# print(res)

# stepControlPort.write(b'/1aM3V150R\r\n')
# res = str(stepControlPort.read_until('\n'))
# print(res)

# stepControlPort.write(b'/1aM3m20R\r\n')
# res = str(stepControlPort.read_until('\n'))
# print(res)

# stepControlPort.write(b'/1aM3N1\r\n')
# res = str(stepControlPort.read_until('\n'))
# print(res)

# input('Ready to move!')

# stepControlPort.write(b'/1aM3P8000R\r\n')
# res = str(stepControlPort.read_until('\n'))
# print(res)

# run = True
# while run:

#     try:
#         stepControlPort.write(b'/1?41\r\n')
#         res = str(stepControlPort.read_until('\n'))
#         res = res.split('\\x03')
#         res = res[0].split('\\xff')[1]
#         chanVals = int(res[-2:]) & 0x0F
#         chan1 = chanVals & 0x01
#         # val = res[1][0:2]
#         print(chan1)
        
#         stepControlPort.write(b'/1?aA\r\n')
#         res = str(stepControlPort.read_until('\n'))
#         print(res)
#         # time.sleep(0.2)
    
#     except KeyboardInterrupt:
#         stepControlPort.write(b'/1T3\r\n')
#         run = False
#         continue


# # stepControlPort.write(b'/1&\r\n')
# # test = stepControlPort.read(size=50)
# # test = stepControlPort.read_until(expected='\n')

# # print(test)

# stepControlPort.close()

# print('Done')