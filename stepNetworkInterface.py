import asyncio
# import numpy as np
# import ImageMessages_pb2
import logging

class EchoServerProtocol(asyncio.Protocol):
    
    def __init__(self, qarg, infoLog):
        self.que = qarg
        self.infoLogging = infoLog
        # self.recv_buf = memoryview(bytearray(1048576))
        # self.dataBuf = bytearray()
        # self.asiImgData = ImageMessages_pb2.ASIimage()
        # self.asiImgData = None

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
        # return super().data_received(data)

        print(data)


    # def get_buffer(self, sizehint):
    #     return self.recv_buf
    
    # def buffer_updated(self, nbytes):
    #     self.dataBuf += self.recv_buf[:nbytes]
    #     self.nbytesCounter += nbytes
    #     self.countRecv += 1

    #     if self.frameStart and self.nbytesCounter >= 24:
    #         self.frameStart = False
    #         startBytes = self.recv_buf[0:nbytes]
    #         self.msgLen = int.from_bytes(startBytes[11:15], byteorder='little')
        
    #     if self.nbytesCounter >= self.msgLen and self.msgLen>0:
    #         # print("\nGot frame")
    #         # print('Recv count: {:d}'.format(self.countRecv))
    #         # print('Frame count: {:d}'.format(self.frameCount))

    #         try:
    #             self.asiImgData.ParseFromString(self.dataBuf)
    #             self.que.put(self.asiImgData)

    #             # self.transport.write("got image data")
            
    #         except pb.message.DecodeError:
    #             # print('Parse Error')
    #             self.infoLogging.log(logging.ERROR, "protobuf decode error")
    #             pass

    #         self.frameStart = True
    #         self.frameCount += 1
    #         self.nbytesCounter = 0
    #         self.countRecv = 0
    #         self.msgLen = -1
    #         self.dataBuf = bytearray()

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

def frameDataToArray(data, bits):
    if bits > 8:
        dtImg = np.dtype(np.uint16)
    else:
        dtImg = np.dtype(np.uint8)

    dtImg = dtImg.newbyteorder('<') # LITTLE ENDIAN!!
    imgData = np.frombuffer(data, dtype=dtImg)
    return imgData                                             
