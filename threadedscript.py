from threading import Thread
from mac_sticky import runSimpleScript, runScript

class RunScriptThread(Thread):
     def __init__(self):
        Thread.__init__(self)

     def run(self):
        runScript()
