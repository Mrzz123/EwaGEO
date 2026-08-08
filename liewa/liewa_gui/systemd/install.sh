# DIRPATH=$(echo $(pwd))
# PYTHONPATH=$(which python3)

# cat > liewa.service << EOL
# [Unit]
# Description=EwaGEO Service
# [Service]
# Type=simple
# ExecStart=$(which liewa)
# EOL

# cat > liewa.timer << EOL
# [Unit]
# Description=EwaGEO Timer
# [Timer]
# OnBootSec=10
# OnUnitActiveSec=30
# AccuracySec=1ms
# [Install]
# WantedBy=timers.target
# EOL
