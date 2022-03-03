import threading, queue, argparse, logging, sys, time, datetime
import asyncio
import configparser
import stepControl

import stepNetworkInterface as net
import ImageMessages_pb2 as pbMsgs
from google.protobuf import message


def main(args):
    
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("configFile", help="pass the name of the config file dummy")
    args = parser.parse_args()

    # parse config file
    stepConfig = configparser.ConfigParser()
    stepConfig.read(args.configFile)

    # logging setup
    logpath = stepConfig.get("logging", "logFolder")
    logName = stepConfig.get("logging", "name")
    logNameStr = logpath + "/" + datetime.datetime.now().strftime("%Y%m%d%H%M%S_") + logName + ".log"
    logConfigLevel = stepConfig.get("logging", "level")
    numeric_level = getattr(logging, logConfigLevel.upper(), None)

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level = numeric_level,
                        filemode='a',
                        filename=logNameStr)
    # Networking
    cmdMsgQue = queue.Queue(1)
    loggingDataQue = queue.Queue(10)

    serverStop = threading.Event()
    _threadServer = threading.Thread(target=net.serverThreadRunner, args=(cmdMsgQue, serverStop, logging, stepConfig),)
    _threadServer.start()

    threadList = [_threadServer,]

    ifWriter, ifBucket, ifOrg = net.getInfluxClientFC()

    # Interface to step controller
    st = stepControl.stepController('/dev/stepperControl', stepConfig, loggingDataQue)

    # Stepper loop runner
    loopDelay = float(stepConfig.get('StepperParams', 'loopInterval'))
    while True:

        try:
            time.sleep(loopDelay)

            # read housekeeping data
            hkData = st.readHouseKeepingData()
            hkData['time'] = datetime.datetime.utcnow()

            net.writeStepperHKdata(hkData, ifWriter, ifBucket, ifOrg )
            #check on limit switches
            focusSwitchValue = hkData["FocusSwitches"]

            if (focusSwitchValue & st.UpperSwitchMask) == st.UpperSwitchMask:
                st.stopMotion()
                logging.warning("upper limit hit")

            if (focusSwitchValue & st.LowerSwitchMask) == st.LowerSwitchMask:
                st.stopMotion()
                logging.warning("lower limit hit")
            
            # update position non-volatile file
            st.currCountsConfig['Position'] = {'counts': hkData['FocusAxis']}
            with open(st.countFname, 'w') as ff:
                st.currCountsConfig.write(ff)
            
            # check on cmd msg que
            try:
                cmdMsg = cmdMsgQue.get_nowait()
                cmdBuf = pbMsgs.stepperCtrlMessage()
                cmdBuf.ParseFromString(cmdMsg)
                counts = 0

                if "move" in cmdBuf.cmdString:
                    counts = cmdBuf.counts

                    logging.debug(f"Cmd={cmdBuf.cmdString}, counts={cmdBuf.counts}")

                    if "Positive" in cmdBuf.cmdString:
                        st.movePositiveCounts(counts)
                    elif "Negative" in cmdBuf.cmdString:
                        st.moveNegativeCounts(counts)

                
                elif "velocity" in cmdBuf.cmdString:
                    logging.debug(f"Cmd={cmdBuf.cmdString}, speed={cmdBuf.speed}")
                    st.setMaxVel(cmdBuf.speed)

            except message.DecodeError:
                logging.error("Failed to decode focus command message from GSE")

            except queue.Empty:
                pass

        
        except KeyboardInterrupt:
            break
    
    serverStop.set()
    print('Stopping server')

    for tt in threadList:
        tt.join()

    logging.info("Closing down code")
    print("Done")

if __name__ == "__main__":

    main(sys.argv)
