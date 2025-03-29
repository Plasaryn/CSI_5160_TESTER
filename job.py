import time
import urllib.request
import urllib.error
from statistics import stdev
import threading

class JobInstance:
  def __init__(self, image_url: str):
    self.image_url: str = image_url
    self.status = "pending"
    self.start: float = time.process_time()

    try:
      urllib.request.urlretrieve(image_url, "tmp")
      self.status = "complete"
    except urllib.error.HTTPError:
      self.status = "error"


    self.end: float = time.process_time()
    self.time_to_complete: float = self.end - self.start

  def get_results(self) -> dict:
    return {
      "status": self.status,
      "image_url": self.image_url,
      "start_time": self.start,
      "end_time": self.end,
      "time_to_complete": self.time_to_complete
    }


class Job:
  """
Downloads an image multiple times from the same source from a given host.
Evaluates the success rate and timing of each download to get a rounded result.

Keyword Arguments:
host: str - The a descriptive name for the host that will be performing the test.
image_url: str - The complete URL of the image that will be downloaded and measured.
iterations: int = 50 - the number of tests that should be run before the job is complete.
  """
  id: int = 1

  def __init__(self, host: str,  image_url: str, iterations: int = 50) -> None:
    # Test Parameters
    self.host: str = host
    self.image_url: str = image_url
    self.iterations: int = iterations
    self.status: str = "pending"
    self.tests: list[JobInstance] = []

    # Assign ID
    self.id = Job.id
    Job.id += 1

    # Test Success Rate
    self.error_percentage: float = 0.0
    self.completed_tests: int = 0
    self.failed_tests: int = 0

    # Test Metric Rate
    self.minimum_time: float = 0.0
    self.maximum_time: float = 0.0
    self.average_time: float = 0.0
    self.stdev: float = 0.0

    # Once the object is initialized, start the test
    self.thread = threading.Thread(target=self.__conduct_tests, daemon=True)
    self.thread.start()


  def __conduct_tests(self) -> None:
    for _ in range(self.iterations):
      self.tests.append(JobInstance(self.image_url))
    self.__evaluate_test()


  def __evaluate_test(self) -> None:
    successes = []
    failures = []
    times = []

    for test in self.tests:
      if test.status == "complete":
        successes.append(test)
        times.append(test.time_to_complete)
      else:
        failures.append(test)

    # set test success rate
    self.completed_tests = len(successes)
    self.failed_tests = len(failures)
    self.error_percentage = len(failures) / self.iterations

    # set test metrics
    self.minimum_time = min(times)
    self.maximum_time = max(times)
    self.average_time = sum(times) / len(times)
    self.stdev = stdev(times)

    # set status
    partial_success = len(successes) > 0
    partial_failure = len(failures) > 0

    if partial_success and not partial_failure:
      self.status = "completed"
    elif not partial_success and partial_failure:
      self.status = "error"
    else:
      self.status = "partial_error"

  def get_results(self, max_test_count: int = 50) -> dict:
    if self.status == "pending":
      tests: list[JobInstance] = []
    elif max_test_count > self.iterations:
      tests: list[JobInstance] = self.tests[:max_test_count]
    else:
      tests: list[JobInstance] = self.tests
    
    return {
      "id": self.id,
      "host": self.host,
      "image_url": self.image_url,
      "iterations": self.iterations,
      "status": self.status,
      "test_success_evaluation": {
        "completed_tests": self.completed_tests,
        "failed_tests": self.failed_tests,
        "error_percentage": self.error_percentage
      },
      "test_metrics": {
        "minimum_time": self.minimum_time,
        "maximum_time": self.maximum_time,
        "average_time": self.average_time,
        "standard_deviation": self.stdev
      },
      "tests": [x.get_results() for x in tests]
    }
  
  def get_id(self) -> int:
    return self.id


def main() -> None:
  import pprint
  job1 = Job("IcePick", "https://www.google.com/images/branding/googlelogo/1x/googlelogo_light_color_272x92dp.png")

  time.sleep(10)
  print(pprint.pp(job1.get_results()))

if __name__ == "__main__":
  main()    