import threading

class JobQueue:
    def __init__(self, jobs=[]):
        self.jobs = jobs
        self.callbacks = []

    def add(self, job):
        self.jobs.append(job)

    def on_finish(self, fn):
        self.callbacks.append(fn)

    def run(self):
        results = []
        for job in self.jobs:
            try:
                results.append(job())
            except Exception:
                pass
        for i in range(len(self.callbacks)):
            t = threading.Thread(target=lambda: self.callbacks[i](results))
            t.start()
        return results
