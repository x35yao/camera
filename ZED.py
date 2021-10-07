import pyzed.camera as zcam
import pyzed.types as tp
import pyzed.core as core
import pyzed.defines as sl
from collections import namedtuple
from time import sleep, time
import cv2
from threading import Thread
from queue import Empty, Queue

class ZEDVideoStream(Thread):
    def __init__(self, ZED, inputQueue, outputQueue):
        self.ZED = ZED
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        Thread.__init__(self)

    def run(self):
        while True:
            album = self.ZED._takePicture(emptyBuffer=False)

            try:
                command = self.inputQueue.get(block=False)
            except Empty:
                command = None

            if command == 1:
                self.outputQueue.put(album)
            elif command == 0:
                break
            elif command == None:
                continue
        return

class ZEDCamera:
    def __init__(self, resolution='720', depth_mode='ultra', depth=True, color=True):
        self.depth = depth
        self.color = color
        self.init = zcam.PyInitParameters()

        resolutions = {'720': sl.PyRESOLUTION.PyRESOLUTION_HD720,
                       '1080':sl.PyRESOLUTION.PyRESOLUTION_HD1080,
                       '2K'  :sl.PyRESOLUTION.PyRESOLUTION_HD2K}

        depthModes = {'perf': sl.PyDEPTH_MODE.PyDEPTH_MODE_PERFORMANCE,
                      'med': sl.PyDEPTH_MODE.PyDEPTH_MODE_MEDIUM,
                      'qual': sl.PyDEPTH_MODE.PyDEPTH_MODE_QUALITY,
                      'ultra': sl.PyDEPTH_MODE.PyDEPTH_MODE_ULTRA,}

        self.init.camera_resolution = resolutions[resolution]
        self.init.depth_mode = depthModes[depth_mode]
        self.cam = zcam.PyZEDCamera()
        self.inQ, self.outQ = Queue(maxsize=1), Queue(maxsize=1)
        return

    def _openCamera(self, totalAttempts=5):
        for attempt in range(totalAttempts):
            print('Opening ZED Camera...')
            status = self.cam.open(self.init)
            if status != tp.PyERROR_CODE.PySUCCESS:
                print('\nTry {} out of {}'.format(attempt+1,totalAttempts))
                print(repr(status))
                if attempt == (totalAttempts-1):
                    print('\n\n'+'-'*80)
                    print('Failed to open ZED')
                    print('Please Unplug the ZED and plug it back in!')
                    return False
            else:
                return True

    def __enter__(self):
        totalAttempts = 5
        for attempt in range(totalAttempts):
            if self._openCamera() == True:
                self.runtime = zcam.PyRuntimeParameters()

                varNames = []
                if self.depth == True:
                    self.mat_depth = core.PyMat()
                    varNames.append('depth')
                if self.color == True:
                    self.mat_color = core.PyMat()
                    varNames.append('color')
                self.Album = namedtuple('Album', varNames)

                self.videoStream = ZEDVideoStream(self, self.inQ, self.outQ)
                self.videoStream.start()
                return self
            else:
                sleep(5)
        raise IOError('Camera could not be opened, please try power cylcing the ZED')

    def __exit__(self, exc_type, exc_value, traceback):
        print('Closing ZED...')
        self.inQ.put(0)
        self.videoStream.join()
        self.cam.close()

    def __del__(self):
        self.inQ.put(0)
        self.videoStream.join()
        self.cam.close()

    def startStream(self):
        self.__enter__()

    def closeStream(self):
        self.__exit__(None, None, None)

    def _takePicture(self, emptyBuffer=False):
        pics = []
        start = time()
        while True:
            status = self.cam.grab(self.runtime)
            if emptyBuffer:
                for i in range(7):
                    status = self.cam.grab(self.runtime)
            if status == tp.PyERROR_CODE.PySUCCESS:
                if self.depth:
                    self.cam.retrieve_image(self.mat_depth, sl.PyVIEW.PyVIEW_DEPTH)
                    depth_image = self.mat_depth.get_data()
                    pics.append(depth_image)

                if self.color:
                    self.cam.retrieve_image(self.mat_color, sl.PyVIEW.PyVIEW_SIDE_BY_SIDE)
                    color_image = self.mat_color.get_data()
                    pics.append(color_image)

                break

            elif (time() - start) > 1:
                raise TimeoutError('The ZED is taking longer than 1 sec')

        return self.Album(*pics)

    def takePicture(self, buffer=False):
        self.inQ.put(1)
        album = self.outQ.get()
        return album

if __name__ == '__main__':
    with ZEDCamera() as cam:
        key = ''
        while key!=113:
            album = cam.takePicture()
            cv2.imshow('ZED Color', album.color)
            cv2.imshow('ZED Depth', album.depth)
            key = cv2.waitKey(5)
        cv2.destroyAllWindows()
