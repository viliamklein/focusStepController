import asyncio
from curses.ascii import US
from dataclasses import field
import logging

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


class influxClientDataWriter:

    async def writeStepperHKdata(self, hkdata):

        point = Point("Focus") \
                .tag("type", "hangarTesting") \
                .field("FocusCounts", hkdata['FocusAxis'])\
                .field("FocusSwitches", hkdata['FocusSwitches']) \
                .time(hkdata["time"], WritePrecision.US)

        self.write_api.write(self.bucket, self.org, point)

    @classmethod
    async def create(cls, configInfo=None):

        self = influxClientDataWriter()
        token = "FzANVq9O0CVYN4iHQivNgchUsZhM6HbomP0HuXHKuv5Xp11Xcyb5pEIuZbXnpOqSGfqEc03eel_cS9euGBTPxw=="
        self.org = "thaispice"
        self.bucket = "HangarTesting"

        self.client = InfluxDBClient(url="http://10.40.0.32:8086", token=token)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

        return self

def getInfluxClientFC():

    # You can generate a Token from the "Tokens Tab" in the UI
    token = "FzANVq9O0CVYN4iHQivNgchUsZhM6HbomP0HuXHKuv5Xp11Xcyb5pEIuZbXnpOqSGfqEc03eel_cS9euGBTPxw=="
    org = "thaispice"
    bucket = "HangarTesting"

    client = InfluxDBClient(url="http://10.40.0.32:8086", token=token)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    return write_api, bucket, org

def writeStepperHKdata(hkdata, writer, bucket, org):

    point = Point("Focus") \
        .tag("type", "hangarTesting") \
        .field("FocusCounts", hkdata['FocusAxis'])\
        .field("FocusSwitches", hkdata['FocusSwitches']) \
        .time(hkdata["time"], WritePrecision.US)

    writer.write(bucket, org, point)

class EchoServerProtocol(asyncio.Protocol):
    
    def __init__(self, qarg, infoLog):
        self.cmdQue = qarg
        self.infoLogging = infoLog

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        # print('Connection from {}'.format(peername))
        self.infoLogging.log(logging.DEBUG, 'Connection from {}'.format(peername))
        self.transport = transport
        
        self.frameCount = 0
        self.countRecv = 0
        self.nbytesCounter = 0
        self.frameStart = True
        self.headerBytes = []
        self.msgLen = -1
    
    def data_received(self, data: bytes) -> None:
        self.cmdQue.put(data)

    def eof_received(self):
        self.transport.close()
        # print('Close the client socket')
        self.infoLogging.log(logging.DEBUG, 'Close the client socket')
        
        self.countRecv = 0
        self.nbytesList = []
        return False

async def serverRunner(qarg=None, stopEvent=None, infoLog=None, configInfo=None):
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    ipaddress = configInfo.get("NetworkParams", "ipAddr")
    ipport = configInfo.get("NetworkParams", "port")

    server = await loop.create_server(
        lambda: EchoServerProtocol(qarg, infoLog), ipaddress, ipport)

    try:
        async with server:
            # await server.serve_forever()
            await server.start_serving()
            # print('Server running: ', server.is_serving())
            while(True):
                if stopEvent.is_set():
                    break
                await asyncio.sleep(1)
                # print('Server running: ', server.is_serving())

    except KeyboardInterrupt:
        # print("here")
        pass

    except Exception as inst:
        print(type(inst))    # the exception instance
        print(inst.args)     # arguments stored in .args
        print(inst)

    finally:

        # print('Done with server')
        server.close()

def serverThreadRunner(qarg=None, stopEvent=None, infoLog=None, configInfo=None):
    asyncio.run(serverRunner(qarg, stopEvent, infoLog, configInfo))

