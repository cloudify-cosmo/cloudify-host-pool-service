#!/bin/sh -e

### BEGIN INIT INFO
# Provides:          cloudify-hostpool
# Required-Start:    $network $local_fs
# Required-Stop:     $network $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Cloudfy Host-Pool service
### END INIT INFO

# These get replaced during pre-processing
BASE_DIR=${TMPL_BASE_DIR}
VIRT_DIR=${TMPL_VIRT_DIR}
SVC_LOG_LEVEL=${TMPL_SVC_LOG_LEVEL}

SVC_PID_FILE=$BASE_DIR/cloudify-hostpool.pid
SVC_LOG_FILE=$BASE_DIR/gunicorn.log
SVC_PORT=8080
SVC_CONFIG_FILE=$BASE_DIR/config.json
SVC_NAME="Cloudify Host-Pool service"

pid_file_exists() {
    [ -f "$SVC_PID_FILE" ]
}

get_pid() {
    echo "$(cat "$SVC_PID_FILE")"
}

stop_process() {
    PID=$(get_pid)
    echo "Killing process $PID"
    kill $PID
}

is_running() {
    PID=$(get_pid)
    ! [ -z "$(ps aux | awk '{print $2}' | grep "^$PID$")" ]
}

remove_pid_file() {
    echo "Removing pid file"
    rm -f "$SVC_PID_FILE"
}

start_svc() {
    # Access the task's virtualenv
    . $VIRT_DIR/bin/activate
    export HOST_POOL_SERVICE_CONFIG_PATH=$SVC_CONFIG_FILE
    # Start the REST service
    echo "Starting $SVC_NAME..."
    $VIRT_DIR/bin/gunicorn \
            --workers=5 \
            --pid=${SVC_PID_FILE} \
            --log-level=${SVC_LOG_LEVEL} \
            --log-file=${SVC_LOG_FILE} \
            --bind 0.0.0.0:${SVC_PORT} \
            --daemon cloudify_hostpool.rest.service:app
    # Check the REST service start status
    RETVAL=$?
    if [ $RETVAL -ne 0 ]; then
        echo -e Gunicorn error \#$RETVAL
        exit 1
    fi

    # Check the PID file
    sleep 2s
    echo "$SVC_NAME started with pid $(get_pid)"
}

start() {
    if pid_file_exists ; then
        if is_running ; then
            PID=$(get_pid)
            echo "$SVC_NAME already running with pid $PID"
            exit 1
        else
            echo "$SVC_NAME stopped, but pid file exists"
            remove_pid_file
            start_svc
        fi
    else
        start_svc
    fi
}

stop() {
    if pid_file_exists ; then
        if is_running ; then
            echo "Stopping $SVC_NAME..."
            stop_process
            remove_pid_file
            echo "$SVC_NAME stopped"
        else
            echo "Node app already stopped, but pid file exists"
            remove_pid_file
            echo "$SVC_NAME stopped"
        fi
    else
        echo "$SVC_NAME already stopped"
    fi
}

status() {
    if pid_file_exists ; then
        if is_running ; then
            PID=$(get_pid)
            echo "$SVC_NAME running with pid $PID"
        else
            echo "$SVC_NAME stopped, but pid file exists"
        fi
    else
        echo "$SVC_NAME stopped"
    fi
}


case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"

esac
exit $?