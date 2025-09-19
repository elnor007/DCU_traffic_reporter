#!/bin/bash

# Passes down the "kill" command to each of the python and bash processes, allowing for a graceful exit
cleanup() {
    echo -e "\n\n$(date +%Y-%m-%d__%H:%M:%S) : Cleaning up...\n"
    
    for pid in $(jobs -p); do
        kill -SIGINT "$pid" 2>/dev/null
    done

    wait  

    exit 130  
}

trap cleanup SIGINT SIGTERM


# Script names
email_script="email_multiple.py"
upload_script="upload_to_database_historical.py"
reporter_script="ruby_retry.sh"

# Change to project directory
cd /home/$USER/vivacity

docker-compose up -d



# Ensures all containers run before continuing with the script
echo -e "\n\n$(date +%Y-%m-%d__%H:%M:%S) : Waiting for containers to start...\n"
while [ "$(docker-compose ps --services --filter 'status=running' | wc -l)" -lt "$(docker-compose ps --services | wc -l)" ]; do
    sleep 2
done

echo -e "$(date +%Y-%m-%d__%H:%M:%S) : All containers are running, initiating report generation...\n\n"



# Email script runs in the background, waiting for report to be generated
echo -e "$(date +%Y-%m-%d__%H:%M:%S) : Starting email script...\n"
/usr/bin/python3 "$email_script" >> log_files/email_multiple.log 2>&1 &
email_pid=$!



# Most recent traffic data is uploaded to the database from the API
echo -e "$(date +%Y-%m-%d__%H:%M:%S) : Starting upload script...\n"
/usr/bin/python3 "$upload_script" >> log_files/upload_to_database_historical.log 2>&1
upload_exit=$?
echo -e "$(date +%Y-%m-%d__%H:%M:%S) : Upload script finished.\n"
if [[ $upload_exit == 2 ]]; then
    echo "Unresolved error in upload script. Requesting support."
    /usr/bin/python3 request_support.py "$upload_script"    # If any of these scripts cant resolve the errors on their own, 
    cleanup                                                 # an email is sent to the administrator using "request_support.py"
fi



# Delay gives the email script a chance to handle errors (if there are any)
sleep 10

if ! kill -0 "$email_pid" 2>/dev/null; then
    echo "Checking exit status of email script"
    wait "$email_pid"
    email_exit=$?
    echo "Obtained exit status = $email_exit"
    if [[ $email_exit == 2 ]]; then
        /usr/bin/python3 request_support.py "$email_script"
        cleanup
    fi
fi



# Runs the reporter script to generate a report based on the Grafana visualised dashboards
echo -e "$(date +%Y-%m-%d__%H:%M:%S) : Starting reporter script...\n"
./"$reporter_script" \
  "/home/$USER/vivacity/ruby" \
  "/usr/bin/ruby ruby-grafana-reporter \
      -t DCU_grafana_report \
      -o reports/weekly_DCU_sensor_report_\$(date +%Y-%m-%d_%H-%M-%S).pdf \
      -c grafana_reporter.config" \
  5 3 \
  2>&1 | fold -w 80 -s >> /home/$USER/vivacity/log_files/ruby_reporter.log
ruby_exit=${PIPESTATUS[0]}
echo -e "Reporter exit code is $ruby_exit\n"
echo -e "$(date +%Y-%m-%d__%H:%M:%S) : Reporter script finished.\n"
if [[ $ruby_exit == 2 ]]; then
    echo "Unresolved error in ruby script. Requesting support."
    /usr/bin/python3 request_support.py "$reporter_script"
    cleanup
fi

wait

echo -e "$(date +%Y-%m-%d__%H:%M:%S) : Email script finished.\n\n"
