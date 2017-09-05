# ------------------------------------------------------------------------------
# Name:        driver.py
# Purpose:     Module defining the MultiwfnDriver class
#
# Author:      Brian Skinn
#                bskinn@alum.mit.edu
#
# Created:     30 Aug 2017
# Copyright:   (c) Brian Skinn 2017
# License:     The MIT License; see "LICENSE.txt" for full license terms.
#
#       https://www.github.com/bskinn/mwfn-fu
#
# ------------------------------------------------------------------------------

import attr


def _validate_mwfn_path(md, at, val):
    import os.path as osp

    if not osp.isdir(val):
        raise FileNotFoundError('Invalid path to Multiwfn')

    if not osp.isfile(osp.join(val, MultiwfnDriver.EXECUTABLE)):
        raise FileNotFoundError('Multiwfn.exe not found within indicated directory')


def _validate_data_fname(md, at, val):
    import os.path as osp

    if not osp.isfile(val):
        raise FileNotFoundError('Data file not found')


@attr.s()
class MultiwfnDriver(object):
    """Handles all execution/input/output of a Multiwfn instance."""

    import re

    # Regex for finding the `isilent` settings in `settings.ini`
    p_isilent = re.compile('isilent= ([01])')
    p_nthreads = re.compile('nthreads= (\\d+)')
    p_data_fname = re.compile('^\\s*Loaded (.*) successfully!\\s*$', re.I | re.M)

    # Useful constants
    SETTINGS_FILE = 'settings.ini'
    EXECUTABLE = 'multiwfn.exe'
    WAIT_SHORT = 0.25
    WAIT_MED = 1.0
    WAIT_LONG = 2.5

    # Add attr.ib's
    mwfn_path = attr.ib(convert=str, validator=_validate_mwfn_path)
    data_fname = attr.ib(convert=str, validator=_validate_data_fname)
    suppress_gui = attr.ib(convert=bool, default=True)

    def __attrs_post_init__(self): #, mwfn_path, data_fname, suppress_gui=True):

        from time import sleep

        # Launch Multiwfn; method binds the Feeder and the Pipeline
        self.launch(self.mwfn_path, self.suppress_gui)

        # Store the PID
        self.pid = self.pipeline.commands[0].process.pid

        # Initialize the last- measured length of the output
        self.lastlen = 0

        # Initialize the list of indices for retrieving spans
        #  of output, the list of commands passed, and the
        #  lists of count histories from the await_idle method
        self.mwfn_commands = []
        self.output_spans = []
        self.count_histories = []

        # Load the file and save the filename to use in __repr__
        self.execute(self.data_fname + '\n')
        self.data_fname = self.p_data_fname.search(self.pipeline.stdout.text).group(1)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False


    def shutdown(self, force=False):
        self.pipeline.commands[0].terminate()


    def launch(self, mwfn_path, datafile, suppress_gui=True):

        import os
        import psutil
        import sarge
        from time import sleep

        # Change to mwfn path
        curdir = os.getcwd()
        os.chdir(mwfn_path)

        # Edit settings.ini to suppress output, if indicated
        if suppress_gui:
            # Read the file contents
            with open(self.SETTINGS_FILE, 'r') as f:
                settings_text = f.read()

            # Store the setting
            str_setting = self.p_isilent.search(settings_text).group(0)

            # Coerce the setting to one
            with open(self.SETTINGS_FILE, 'w') as f:
                f.write(settings_text.replace(str_setting, 'isilent= 1'))

        # Execute, binding all needed input/output streams
        self.feeder = sarge.Feeder()
        self.pipeline = sarge.run(self.EXECUTABLE, input=self.feeder, async=True,
                stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))

        # Store the nthreads, nproc, 'idle' CPU level
        # Idle level is 10% of the max CPU level based on (# threads / # CPUs)
        # The value is compared to psutil.cpu_percent(), which reports the value
        #  as the percentage value (0.10 = 10% ==> 10).
        self.nthreads = float(self.p_nthreads.search(settings_text).group(1))
        self.nproc = psutil.cpu_count()
        self.idle_cpu_default = (self.nthreads / self.nproc) / 10 * 100

        # Sleep briefly to ensure settings file read
        sleep(self.WAIT_MED)

        # Restore settings.ini if needed
        if suppress_gui:
            with open(self.SETTINGS_FILE, 'r') as f:
                settings_text = f.read()

            with open(self.SETTINGS_FILE, 'w') as f:
                f.write(settings_text.replace('isilent= 1', str_setting))

        # Restore path
        os.chdir(curdir)


    def await_idle(self, *, idle_cpu=None, print_status=False, poll_time=0.25):
        """Method for waiting until Multiwfn computation is done.

        Waits until CPU activity and target process output both stop.


        Parameters
        ----------
        idle_cpu
            float, optional --
            CPU usage percent below which the system is considered to be
            idle (default 1/10 of the maximum CPU usage as per the Multiwfn
            `nthreads` setting and `psutil.cpu_count()`). Provide the
            actual percentage value: e.g., "two percent" is represented by
            2.0, not 0.02.

        print_status
            bool, optional --
            If True, prints status updates, such as the value of each line_ct
            as it is recalculated. If False (default), prints nothing.

        poll_time
            float, optional --
            Time to wait between each poll of the CPU percentage and the change in
            length of the output. Default is 0.25 seconds.


        Returns
        -------
        ct_history
            length-N list of length-2 lists --
            Full history of the length of the generated output text as seen by
            the function. Presumably little use other than debugging.

        """

        import psutil
        from time import sleep, strftime

        # Function to update the count-history lists
        def ct_update(p, l, h):
            l.pop()                         # Remove last value
            l.insert(0, len(p.stdout.text)) # Insert current count
            h.append(l[:])                  # Add updated value to history

        # Assign default idle CPU level if needed
        if idle_cpu is None:
            idle_cpu = self.idle_cpu_default

        # List for the history of the length tracking
        ct_history = []

        # List for tracking the length of the Multiwfn output
        ct_lengths = [1, 0]

        # Initial, longer wait delay while finding the initial CPU load
        actual_cpu = psutil.Process(pid=self.pid).cpu_percent(interval=4*poll_time) / self.nthreads

        while actual_cpu >= idle_cpu or ct_lengths[0] > ct_lengths[1]:
            # Update the current count length and history
            ct_update(self.pipeline, ct_lengths, ct_history)

            # Store the current CPU value for use in the printing and conditional
            actual_cpu = psutil.Process(pid=self.pid).cpu_percent(interval=poll_time) / self.nthreads

            # Print status info if indicated (PROBABLY CONVERT TO AND/OR AUGMENT WITH
            #  LOGGING, EVENTUALLY?)
            if print_status:
                print('({0}) {1} -- {2}'.format(
                        strftime('%Y-%m-%d %H:%M:%S'), 
                        [actual_cpu, ct_lengths, (actual_cpu >= idle_cpu or ct_lengths[0] > ct_lengths[1])],
                        self.pipeline.stdout.text[-200:].splitlines()[-1]))

        # Return the history (MAY NEED TO IMPROVE THIS?)
        return ct_history


    def execute(self, command, *, idle_cpu=None, print_status=False, poll_time=0.25):
        """Submit a command to the child Multiwfn instance and wait for computation to complete"""

        # Submit the command
        self.feeder.feed(command)

        # Wait for completion
        counts = self.await_idle(idle_cpu=idle_cpu, print_status=print_status, poll_time=poll_time)

        # Store the command passed and the span of indices for later indexing
        self.mwfn_commands.append(command.replace('\n', '!'))
        self.output_spans.append((self.lastlen, len(self.pipeline.stdout.text)))
        self.count_histories.append(counts)

        # Update the marker for the last output string length
        self.lastlen = len(self.pipeline.stdout.text)

    def get_output_block(self, index=None):
        """Return a block of the Multiwfn output."""

        if index is None:
            return self.pipeline.stdout.text
        else:
            return self.pipeline.stdout.text[slice(*self.output_spans[index])]

