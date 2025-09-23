# Setup Guide & Showcase

<br>

## Introduction
### What is the DCU Traffic Reporter?
This is an automated reporting system which downloads traffic data from an API endpoint, which provides the user with data in a weekly report (see image 1) sent to them over email. The api endpoint sources data from the AI traffic camera located outside the DCU Stokes Building main entrance (see image 2). The purpose of this system is to effortlessly and effectively track traffic data, and to analyse both short-term and long-term trends. This reporting system has multiple use-cases such as tracking the College's carbon footprint, using it to adequately adjust resources around the campus e.g. estimating canteen food stock for the day, and much more.

<br><br>


#### *(image 1) A snippet of the weekly traffic report*
<img width="2559" height="1439" alt="image" src="https://github.com/user-attachments/assets/904fe3ff-25c0-40fa-b042-73ba115b6e87" />

<br><br>

This image is an excerpt from the full report, showcasing the data from the footpath countline. This countline measures the total inbound and outbound foot traffic for 6 different classes: busses, cars, cyclists, pedestrians, motorbikes and trucks. Each panel is based on data from the past 28 days and corrolates data in 4 different ways. The top-left panel provides hourly traffic data, the top-right panel gives the average total traffic for each weekday, bottom-left panel illustrates the daily traffic count and finally the bottom-right panel provides average total traffic count for each hour, where each line corresponds to a different day of the week. Every week, this countline along with the two others (inbound and outbound road) are visualised and sent as a report to the listed email recipients.

<br><br><br>

#### *(image 2) The AI traffic camera outside the main entrance of the Stokes (DCU engineering) building*
<img width="921" height="531" alt="image" src="https://github.com/user-attachments/assets/d1acf275-3ca3-482a-b670-f80990b35b7a" />

<br><br><br>


#### *(image 3) A block diagram of the system*
<img width="964" height="552" alt="image" src="https://github.com/user-attachments/assets/cf0e3f01-5b95-4d06-8e1e-4b15a83328b5" />

<br><br>

Here is a step-by-step illustration of the reporting process. The **API endpoint** is accessed by a python script in order to **download** traffic data from the past week. This data is then parsed/formatted, and then directly inserted into the **database**. Any data that's inserted into the database is immediately visualised on the connected **Grafana** dashboards. Once the **Ruby Reporter** is triggered by the System Daemon scheduler, it makes a request to Grafana to generate an image. Grafana uses the **image renderer** to create PNGs out of the dashboards, and then is passed back down to the Ruby Reporter, where they are embedded onto a PDF file. As soon as this PDF report is generated, it is detected by the **emailing script**, and is sent out to the recipients.





<br><br><br>

## Download the Project Directory
Make sure you have the full project directory downloaded to your machine, which
includes all the necessary scripts and config files.

<br><br>

## Install WSL 2 (if not using Linux)
This will be required to run Systemd, which is the scheduler used to automate the
reporter, and ensures that in the event of a server shutdown, any jobs that were missed
will be executed upon booting up. If you are already using Linux, then you can skip this
section.
To begin installation, run windows PowerShell as administrator and run the following
command:
````
wsl --install
````

After installation and setting up the account password and username, you should now
switch out of administrator PowerShell and open normal PowerShell, then run the
command below:
````
wsl -d ubuntu
````

Make sure that after this command, the first line is something like this, and includes
“WSL2”:

<img width="940" height="24" alt="image" src="https://github.com/user-attachments/assets/ab566c85-c415-445e-b649-ca5eb56488b2" />

<br><br>


## Setting up the Systemd Scheduler
Go to the directory in which “vivacity” is saved, then move the project directory in order
to use the Linux file system to avoid any incompatibilities. The below commands move
the project folder into your user directory on the WSL, and changes directory to it:
````
mv vivacity ~
cd ~/vivacity
````

Type in the command below to open and create a systemd service file:
sudo nano /etc/systemd/system/vivacity.service
and copy and paste the below settings:
````
[Unit]
Description=Vivacity Background Service
After=network.target
[Service]
Type=simple
User=USER                                                               #CHANGE USER
WorkingDirectory=/home/USER/vivacity                                    #CHANGE USER 
ExecStart=/home/USER/vivacity/report_gen.sh                             #CHANGE USER
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
# Logs (optional)
StandardOutput=journal
StandardError=journal
# Security (optional)
ProtectSystem=full
PrivateTmp=true
[Install]
WantedBy=multi-user.target
````
**\*\*Make sure to change “USER” to the username you set earlier for your WSL
account\*\***.
Then save the file with ctrl + o, enter, and exit with ctrl + x. Open the timer file with:
````
sudo nano /etc/systemd/system/vivacity.timer
````
and copy and paste the below settings:
````
[Unit]
Description=Run reporter every week
# Time may be in UTC
[Timer]
OnCalendar=Mon *-*-* 08:00             #ADJUST TRIGGER SCHEDULE
Unit=vivacity.service
Persistent=true
AccuracySec=1s
[Install]
WantedBy=timers.target
````
The line to adjust the trigger schedule is pointed out by a comment, and is
currently set to 08:00 every Monday. On some systems this may be interpreted as UTC,
instead of IST, so be sure to check. Note – the database uses UTC.
After you have saved and exited the file, enable the timer file and start it with the
following commands:
````
sudo systemctl enable vivacity.timer
sudo systemctl start vivacity.timer
````
Check the timer’s status with this command and make sure its status is “Active
(waiting)”:
````
systemctl status vivacity.timer
````

<img width="940" height="33" alt="image" src="https://github.com/user-attachments/assets/4348b407-d686-4fab-91cb-541ac99eac35" />

<br><br>

## Installing Dependencies

**\*\*Make sure to cd ~/vivacity\*\***

To install Docker, you can either download the app on windows and connect it to your
WSL, or download docker directly to the WSL, but for compatibility with the reporter we
will do the latter option. The commands below will download docker, give you
permissions to use docker, starts it and sets it to always start on boot. **\*\*It will tell you
to wait 20 seconds before it begins downloading.\*\***

````
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo service docker start
sudo systemctl enable docker
````

Then download Docker Compose to run the .yml file:
````
sudo apt update
sudo apt install docker-compose
````

Make sure to **\*\*close the terminal and open wsl again\*\*** otherwise there may be an
error. Now to test the installed docker files make sure you are in ~/vivacity, and run:
````
docker-compose up
````

This should start downloading all the containerised applications from the dockercompose.yml file. After it pulls all the docker images and finishes downloading, and the
log files start to print for all the running containers, press ctrl + c to shut down the
containers.

When setting this up, grafana doesn’t initially have access to the user-mounted volume,
so permissions must be explicitly given as follows:
````
sudo chown -R 472:472 ./grafana-data
sudo chmod -R u+rwX ./grafana-data
docker-compose restart
````

If an error persists at any point, run the following two commands:
````
docker-compose down
docker-compose up
````

To install Ruby and test it, run the commands below:
````
sudo apt update
sudo apt install ruby-full
sudo gem install ruby-grafana-reporter
ruby --version
gem --version
````

To install Watchdog, run the commands below:
````
sudo apt update
sudo apt install python3-watchdog
````

To install Asyncpg, run the commands below:
````
sudo apt update
sudo apt install python3-asyncpg
````

<br><br>


## Using the Reporter
Now that everything is set up, I will show you how to use the reporter. Make sure to cd
into ~/vivacity before continuing.

**\*\*Before doing anything else\*\*** you must run the following script:
````
python3 upload_to_database_historical.py 4
````
What this does is that it downloads the last 4 weeks of traffic data from the API, allowing
the past 4 weeks of data to be used in the first 3 weeks of using the reporter. If this isn’t
done, then the averages will have limited data to work off during the first 3 weeks.

If you want to add an email address to the mailing list, run the below commands:
````
cd imports
nano email_multiple_helper.py
````

and then add your desired email to the list shown in the red box below:

<img width="602" height="160" alt="image" src="https://github.com/user-attachments/assets/a233a948-7e1f-4899-a2a8-1f43c9cbfab5" />

The "EMAIL_PASSWORD" variable isn't the regular password to an email account. You must create a second password called an app password, which can be created for any google account, as long as it has two factor authentication enabled.

Just make sure that email is inside quotation marks and it is prepended with a comma if
there is another email before it.

If you would like to adjust the report generation schedule, refer to Setting up the
Systemd Scheduler and look for the timer file.

If you would like to generate a report immediately, cd into ~/vivacity and run:
````
./report_gen.sh
````
Which should take approx. 1 minute, depending on your device and network
connection. The report itself will be stored in ~/vivacity/ruby/reports .

If you ever want to terminate the script, just press ctrl + c and it will exit with a cleanup.

<br><br>


## Reporter Setup Complete!
It will now automatically create and send reports in accordance with the schedule
you have given it. Continue reading for important information about the system.

<br><br>

## Important Notes
• The database entries are all timestamped in UTC in order to avoid
confusion/overlap when changing between daylight savings time and UTC. It is
also a standard of time which is universally understood.

• Unless running on a server, there is a good chance your report will not be
generated at the time specified in the system timer file. If WSL is offline during
the scheduled time, then it will only execute upon booting up WSL.

<br><br>

## Accessing the Database
First create an alias name to shorten a long command to a simple name:
````
alias dbconnect='docker run -it --rm --network=vivacity_default -e
PGPASSWORD=elnor007 postgres psql -h timescaledb -U postgres -d
my_database -p 5432'
````

In order to connect to the database with the psql driver, you simply execute the
following:
````
dbconnect
````

After which you will be able to perform any SQL operations on the database. Just to note, this alias is only available for the current session, and resets upon closing. There is also a method available to set the alias permanently.

<br><br>

## Accessing Grafana
After running ./report_gen.sh once, or docker-compose up, the grafana container
should be up and running. In order to view and edit the dashboards, you must type in
**localhost:3000** into a browser, and you should connect. If it prompts you to login, the
username is **admin** and the password is **elnor007**.
