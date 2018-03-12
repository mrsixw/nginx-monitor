#/usr/bin/env python

import os
from proc.core import find_processes
import smtplib
from email.mime.text import MIMEText
from email.parser import Parser
import subprocess
from datetime import datetime, timedelta

if __name__ == '__main__':
    page_size = os.sysconf('SC_PAGE_SIZE')
    physical_pages = os.sysconf('SC_PHYS_PAGES')
    total_mem = page_size * physical_pages
    print ('Page size = {}, pages = {}, total_mem = {} ({:.1f} MB)'.format(page_size,
                                                                    physical_pages,
                                                                    total_mem,
                                                                    total_mem / (1024**2)))


    nginx_processes = [x for x in find_processes() if x.comm == 'nginx' ]

    cumulative_percent = 0

    for x in nginx_processes:
        print ('nginx process pid = {}, parent_pid = {} , rss = {} '.format(x.pid,
                                                                            x.ppid,
                                                                            x.rss))

        process_percent = (x.rss / total_mem) * 100
        cumulative_percent = cumulative_percent + process_percent

    print ('Cumulative nginx memory use = ', cumulative_percent)

    if cumulative_percent > 75:
        # Take action at the 75% mark - we want to schedule an nginx restart
        action_taken = 'Scheduling at for restart'

        # Check if we aleready have a restart pending
        at_query = subprocess.run(['atq','-q','s'],stdout=subprocess.PIPE)
        if at_query.returncode == 0:
            print(at_query.stdout.decode("utf-8"))

            # For now, if the length of the output was anything other than zero, we'll assumne somehting is
            # scheduled
            if len(at_query.stdout.decode("utf-8")) == 0:

                print("Job not scheduled")
                action_taken += "\n Job not scheduled - scheduling"


                today_weekday = datetime.now().weekday()
                if today_weekday > 3:
                    delta_day = 1 + abs(today_weekday - 6)
                else:
                    delta_day = 1
                print (delta_day)
                tomorrow = datetime.now() + timedelta(days=delta_day)

                print (tomorrow.date())

                timespec = "{}{:0>2}{:0>2}0930".format(tomorrow.date().year,
                                               tomorrow.date().month,
                                               tomorrow.date().day)

                sched_proc = subprocess.run(['at',
                                             '-q',
                                             's',
                                             '-f',
                                             './restart_nginx.job',
                                             '-mv',
                                             '-t',
                                             timespec],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)

                print (" ".join(sched_proc.args))
                print (sched_proc.returncode)
                print (sched_proc.stdout.decode("utf-8"))

                if sched_proc.returncode == 0:
                    action_taken += "\n Job scheduled in the at s queue for {}".format(timespec)
                else:
                    action_taken += "\n Job could not be scheduled for {}".format(timespec)
                action_taken += "\n command {}".format(" ".join(sched_proc.args))
                action_taken += "\n return code {}".format(sched_proc.returncode)
                action_taken += "\n output {}".format(sched_proc.stdout.decode("utf-8"))
                action_taken += "\n error {}".format(sched_proc.stderr.decode("utf-8"))



            else:
                print("Job already scheduled")
                action_taken += "\n Job already scheduled in the at s queue - abort"

        else:
            action_taken += "\nReturn code from atq ({}) was {}".format(at_query.args,
                                                                        at_query.returncode)


    else:
        action_taken = 'No action taken'

    # Send ourselves an email - you will need an email template in cwd, but only do this about 66% memory usage,
    # to cut the noise
    if cumulative_percent > 66:
        with open('mail_headers.txt') as fp:
             headers = Parser().parse(fp)
        msg = MIMEText(action_taken)
        msg['To'] = headers['To']
        msg['From'] = headers['From']

        msg['Subject'] = headers['Subject'].format(cumulative_percent)

        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()
